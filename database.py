import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from typing import Optional, List, Tuple, Dict

load_dotenv()

# --- Конфигурация подключения ---
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'database': os.getenv('DB_NAME')  # Должно совпадать с .env (prompt_aggregator)
}

# --- Глобальный пул соединений ---
db_pool: asyncpg.Pool = None


async def init_db():
    """Инициализация пула соединений и создание таблиц"""
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(**DB_CONFIG)
        print("✅ База данных подключена!")

        async with db_pool.acquire() as conn:
            # 1. Таблица пользователей
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    language VARCHAR(10) DEFAULT 'ru',
                    is_premium BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 2. Таблица промптов (ОБНОВЛЁННАЯ СТРУКТУРА)
            # Добавлены поля subcategory и is_premium для работы с кнопками и монетизации
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR(50) NOT NULL,
                    subcategory VARCHAR(50) NOT NULL,
                    language VARCHAR(10) NOT NULL,
                    title VARCHAR(255),
                    content TEXT NOT NULL,
                    is_premium BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 3. Таблица конфиденциальных данных
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_secrets (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    secret_type VARCHAR(50),
                    encrypted_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Таблица сохранённых промптов
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_saved_prompts (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    prompt_id INTEGER REFERENCES prompts(id) ON DELETE CASCADE,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        print("✅ Таблицы созданы/проверены")
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        raise


# ==============================================================================
# ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
# ==============================================================================
async def add_or_update_user(user_id: int, username: str, first_name: str, last_name: str, is_premium: bool = False):
    """Добавляет нового пользователя или обновляет данные существующего"""
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, is_premium, last_active)
            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET
                username = $2,
                first_name = $3,
                last_name = $4,
                is_premium = $5,
                last_active = CURRENT_TIMESTAMP
        ''', user_id, username, first_name, last_name, is_premium)


async def get_user_language(user_id: int) -> str:
    """Получает предпочтительный язык пользователя"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval('SELECT language FROM users WHERE user_id = $1', user_id)
        return result or 'ru'


async def set_user_language(user_id: int, language: str):
    """Устанавливает язык пользователя"""
    async with db_pool.acquire() as conn:
        await conn.execute('UPDATE users SET language = $1 WHERE user_id = $2', language, user_id)


async def get_all_active_users() -> List[Dict]:
    """Получить всех активных пользователей для рассылки"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch('SELECT user_id, language, first_name FROM users WHERE is_active = TRUE')
        return [dict(row) for row in rows]


async def mark_user_inactive(user_id: int):
    """Пометить пользователя как неактивного (если заблокировал бота)"""
    async with db_pool.acquire() as conn:
        await conn.execute('UPDATE users SET is_active = FALSE WHERE user_id = $1', user_id)


async def get_user_premium_status(user_id: int) -> bool:
    """Проверяет, является ли пользователь премиум"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval('SELECT is_premium FROM users WHERE user_id = $1', user_id)
        return result or False


# ==============================================================================
# НОВЫЕ ФУНКЦИИ ДЛЯ ПРОФИЛЯ
# ==============================================================================
async def get_user_prompts_count(user_id: int) -> int:
    """Получает количество промптов, предложенных пользователем"""
    async with db_pool.acquire() as conn:
        return await conn.fetchval(
            'SELECT COUNT(*) FROM prompts WHERE created_by = $1',
            user_id
        )


async def get_user_saved_prompts_count(user_id: int) -> int:
    """Получает количество сохранённых промптов пользователя"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval(
            'SELECT COUNT(*) FROM user_saved_prompts WHERE user_id = $1',
            user_id
        )
        return result or 0


async def get_user_profile_stats(user_id: int) -> dict:
    """Получает полную статистику профиля пользователя"""
    async with db_pool.acquire() as conn:
        # Получаем статус премиум
        is_premium = await conn.fetchval(
            'SELECT is_premium FROM users WHERE user_id = $1',
            user_id
        )

        # Получаем дату регистрации
        joined_at = await conn.fetchval(
            'SELECT joined_at FROM users WHERE user_id = $1',
            user_id
        )

        # Считаем дни в боте
        if joined_at:
            days_in_bot = (asyncio.get_event_loop().time() - joined_at.timestamp()) / 86400
            days_in_bot = int(days_in_bot) + 1
        else:
            days_in_bot = 1

        return {
            'is_premium': is_premium or False,
            'joined_at': joined_at,
            'days_in_bot': days_in_bot,
            'prompts_submitted': 0,  # Пока 0, если нет таблицы created_by
            'prompts_saved': 0  # Пока 0, если нет таблицы сохранений
        }
# ==============================================================================
# ФУНКЦИИ ДЛЯ ПРОМПТОВ
# ==============================================================================
async def get_prompts(category: str, language: str) -> List[Tuple]:
    """Получает промпты по категории (старая функция для совместимости)"""
    async with db_pool.acquire() as conn:
        return await conn.fetch(
            'SELECT title, content FROM prompts WHERE category = $1 AND language = $2',
            category, language
        )


# ✅ НОВАЯ ФУНКЦИЯ (Критически важна для работы кнопок подкатегорий)
async def get_prompts_by_subcategory(subcategory: str, language: str) -> List[Dict]:
    """
    Получает промпты для конкретной подкатегории и языка.
    Возвращает список словарей для удобной работы.
    """
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            '''
            SELECT title, content, is_premium 
            FROM prompts 
            WHERE subcategory = $1 AND language = $2
            ''',
            subcategory, language
        )
        return [dict(row) for row in rows]


async def add_prompt(category: str, subcategory: str, language: str, title: str, content: str,
                     is_premium: bool = False):
    """Добавляет новый промпт в базу (обновлённая сигнатура с subcategory)"""
    async with db_pool.acquire() as conn:
        await conn.execute(
            '''
            INSERT INTO prompts (category, subcategory, language, title, content, is_premium) 
            VALUES ($1, $2, $3, $4, $5, $6)
            ''',
            category, subcategory, language, title, content, is_premium
        )


async def get_prompts_count() -> int:
    """Получает общее количество промптов в базе (для статистики)"""
    async with db_pool.acquire() as conn:
        return await conn.fetchval('SELECT COUNT(*) FROM prompts')


# ==============================================================================
# ФУНКЦИИ ДЛЯ КОНФИДЕНЦИАЛЬНЫХ ДАННЫХ
# ==============================================================================
async def save_user_secret(user_id: int, secret_type: str, encrypted_value: str):
    """Сохраняет конфиденциальные данные пользователя (API ключи и т.д.)"""
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO user_secrets (user_id, secret_type, encrypted_value)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, secret_type) DO UPDATE SET encrypted_value = $3
        ''', user_id, secret_type, encrypted_value)


async def get_user_secret(user_id: int, secret_type: str) -> Optional[str]:
    """Получает конфиденциальные данные пользователя"""
    async with db_pool.acquire() as conn:
        return await conn.fetchval(
            'SELECT encrypted_value FROM user_secrets WHERE user_id = $1 AND secret_type = $2',
            user_id, secret_type
        )


# ==============================================================================
# ЗАКРЫТИЕ ПОДКЛЮЧЕНИЯ
# ==============================================================================
async def close_db():
    """Закрытие подключения при остановке бота"""
    if db_pool:
        await db_pool.close()
        print("🛑 База данных отключена")