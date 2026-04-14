#
# import asyncio
# import asyncpg
# import os
# from dotenv import load_dotenv
# from typing import Optional, List, Dict
# from datetime import date, timedelta
#
# load_dotenv()
#
# # ==============================================================================
# # 1. КОНФИГУРАЦИЯ ПОДКЛЮЧЕНИЯ
# # ==============================================================================
# DB_CONFIG = {
#     'user': os.getenv('DB_USER'),
#     'password': os.getenv('DB_PASSWORD'),
#     'host': os.getenv('DB_HOST'),
#     'port': os.getenv('DB_PORT'),
#     'database': os.getenv('DB_NAME')
# }
#
# # Глобальный пул соединений
# db_pool: asyncpg.Pool = None
#
#
# # ==============================================================================
# # 2. ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# # ==============================================================================
# async def init_db():
#     """Инициализация пула соединений и полная миграция таблиц"""
#     global db_pool
#     try:
#         db_pool = await asyncpg.create_pool(**DB_CONFIG, min_size=5, max_size=20)
#         print("✅ База данных подключена!")
#
#         async with db_pool.acquire() as conn:
#             # ================================================================
#             # ТАБЛИЦА USERS
#             # ================================================================
#             table_exists = await conn.fetchval('''
#                 SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')
#             ''')
#
#             if table_exists:
#                 print("📋 Таблица users существует, проверяем структуру...")
#
#                 user_id_exists = await conn.fetchval('''
#                     SELECT EXISTS (SELECT FROM information_schema.columns
#                     WHERE table_name = 'users' AND column_name = 'user_id')
#                 ''')
#
#                 if not user_id_exists:
#                     print("⚠️ Колонка user_id отсутствует! Пересоздаём таблицу...")
#                     await conn.execute('DROP TABLE IF EXISTS users CASCADE')
#                     await create_users_table(conn)
#                 else:
#                     print("✅ Колонка user_id существует")
#                     # Добавляем недостающие колонки для геймификации
#                     await add_column_if_not_exists(conn, 'users', 'coins', 'INT DEFAULT 0')
#                     await add_column_if_not_exists(conn, 'users', 'streak', 'INT DEFAULT 0')
#                     await add_column_if_not_exists(conn, 'users', 'last_activity_date', 'DATE DEFAULT CURRENT_DATE')
#                     print("✅ Все колонки users проверены")
#             else:
#                 print("📋 Таблица users не существует, создаём...")
#                 await create_users_table(conn)
#
#             # ================================================================
#             # ТАБЛИЦА NOTIFICATIONS (НОВАЯ - ДЛЯ УВЕДОМЛЕНИЙ)
#             # ================================================================
#             await conn.execute('''
#                 CREATE TABLE IF NOT EXISTS notifications (
#                     user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
#                     is_enabled BOOLEAN DEFAULT TRUE,
#                     daily_reminder BOOLEAN DEFAULT TRUE,
#                     news BOOLEAN DEFAULT TRUE,
#                     missions BOOLEAN DEFAULT TRUE,
#                     last_notification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             ''')
#             print("✅ Таблица notifications готова")
#
#             # ================================================================
#             # ТАБЛИЦА PROMPTS
#             # ================================================================
#             await conn.execute('''
#                 CREATE TABLE IF NOT EXISTS prompts (
#                     id SERIAL PRIMARY KEY,
#                     category VARCHAR(50) NOT NULL,
#                     subcategory VARCHAR(50) NOT NULL,
#                     language VARCHAR(10) NOT NULL,
#                     title VARCHAR(255),
#                     content TEXT NOT NULL,
#                     is_premium BOOLEAN DEFAULT FALSE,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             ''')
#             print("✅ Таблица prompts готова")
#
#             # ================================================================
#             # ТАБЛИЦА AI_CHAT_HISTORY
#             # ================================================================
#             await conn.execute('''
#                 CREATE TABLE IF NOT EXISTS ai_chat_history (
#                     id SERIAL PRIMARY KEY,
#                     user_id BIGINT NOT NULL,
#                     model_name VARCHAR(50),
#                     user_message TEXT,
#                     bot_response TEXT,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             ''')
#             print("✅ Таблица ai_chat_history готова")
#
#             # ================================================================
#             # ТАБЛИЦА USER_SAVED_PROMPTS
#             # ================================================================
#             await conn.execute('''
#                 CREATE TABLE IF NOT EXISTS user_saved_prompts (
#                     id SERIAL PRIMARY KEY,
#                     user_id BIGINT NOT NULL,
#                     prompt_id INTEGER,
#                     saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             ''')
#             print("✅ Таблица user_saved_prompts готова")
#
#         print("✅✅✅ ВСЕ ТАБЛИЦЫ ОБНОВЛЕНЫ/СОЗДАНЫ УСПЕШНО!")
#
#     except Exception as e:
#         print(f"❌ Ошибка подключения к БД: {e}")
#         raise
#
#
# async def create_users_table(conn):
#     """Создаёт таблицу users с правильной структурой"""
#     await conn.execute('''
#         CREATE TABLE users (
#             user_id BIGINT PRIMARY KEY,
#             username VARCHAR(255),
#             first_name VARCHAR(255),
#             last_name VARCHAR(255),
#             language VARCHAR(10) DEFAULT 'ru',
#             is_premium BOOLEAN DEFAULT FALSE,
#             is_active BOOLEAN DEFAULT TRUE,
#             coins INT DEFAULT 0,
#             streak INT DEFAULT 0,
#             last_activity_date DATE DEFAULT CURRENT_DATE,
#             joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#     ''')
#     print("✅ Таблица users создана")
#
#
# async def add_column_if_not_exists(conn, table_name, column_name, column_type):
#     """Добавляет колонку если она не существует"""
#     exists = await conn.fetchval(f'''
#         SELECT EXISTS (SELECT FROM information_schema.columns
#         WHERE table_name = '{table_name}' AND column_name = '{column_name}')
#     ''')
#     if not exists:
#         await conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
#         print(f"✅ Колонка {column_name} добавлена")
#     else:
#         print(f"✓ Колонка {column_name} уже существует")
#
#
# # ==============================================================================
# # 3. ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ И ГЕЙМИФИКАЦИИ
# # ==============================================================================
# async def add_or_update_user(user_id: int, username: str, first_name: str, last_name: str, is_premium: bool = False):
#     """Добавляет пользователя и обновляет статистику активности (Стрик)"""
#     async with db_pool.acquire() as conn:
#         try:
#             existing = await conn.fetchrow(
#                 'SELECT last_activity_date, streak FROM users WHERE user_id = $1',
#                 user_id
#             )
#         except Exception as e:
#             print(f"⚠️ Ошибка получения данных пользователя: {e}")
#             existing = None
#
#         today = date.today()
#         new_streak = 1
#
#         if existing and existing['last_activity_date']:
#             last_date = existing['last_activity_date']
#             current_streak = existing['streak'] or 0
#
#             if last_date == today:
#                 new_streak = current_streak
#             elif last_date == today - timedelta(days=1):
#                 new_streak = current_streak + 1
#             else:
#                 new_streak = 1
#
#         await conn.execute('''
#             INSERT INTO users (user_id, username, first_name, last_name, is_premium,
#                              last_active, last_activity_date, streak, coins)
#             VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, $6, $7, 0)
#             ON CONFLICT (user_id) DO UPDATE SET
#                 username = $2,
#                 first_name = $3,
#                 last_name = $4,
#                 is_premium = $5,
#                 last_active = CURRENT_TIMESTAMP,
#                 last_activity_date = $6,
#                 streak = $7
#         ''', user_id, username, first_name, last_name, is_premium, today, new_streak)
#
#         # ✅ Автоматически создаём запись в notifications для нового пользователя
#         await conn.execute('''
#             INSERT INTO notifications (user_id) VALUES ($1)
#             ON CONFLICT (user_id) DO NOTHING
#         ''', user_id)
#
#
# async def get_user_profile_stats(user_id: int) -> dict:
#     """Получает полную статистику профиля (Койны, Стрик, Статус)"""
#     async with db_pool.acquire() as conn:
#         try:
#             row = await conn.fetchrow(
#                 'SELECT coins, streak, is_premium, joined_at FROM users WHERE user_id = $1',
#                 user_id
#             )
#         except:
#             row = None
#
#         if not row:
#             return {'coins': 0, 'streak': 0, 'is_premium': False, 'days_in_bot': 0}
#
#         joined_at = row['joined_at']
#         days_in_bot = 0
#         if joined_at:
#             days_in_bot = (date.today() - joined_at.date()).days + 1
#
#         return {
#             'coins': row['coins'] or 0,
#             'streak': row['streak'] or 0,
#             'is_premium': row['is_premium'] or False,
#             'days_in_bot': days_in_bot
#         }
#
#
# async def update_user_coins(user_id: int, amount: int):
#     """Изменяет баланс койнов (положительно или отрицательно)"""
#     async with db_pool.acquire() as conn:
#         await conn.execute('UPDATE users SET coins = coins + $1 WHERE user_id = $2', amount, user_id)
#
#
# async def save_ai_message(user_id: int, model: str, user_msg: str, bot_msg: str):
#     """Сохраняет историю переписки с ИИ"""
#     async with db_pool.acquire() as conn:
#         await conn.execute('''
#             INSERT INTO ai_chat_history (user_id, model_name, user_message, bot_response)
#             VALUES ($1, $2, $3, $4)
#         ''', user_id, model, user_msg, bot_msg)
#
#
# # ==============================================================================
# # 4. ✅ ФУНКЦИИ ДЛЯ УВЕДОМЛЕНИЙ (НОВЫЕ)
# # ==============================================================================
# async def get_all_active_users() -> List[int]:
#     """Получает список ID всех пользователей, включивших уведомления"""
#     async with db_pool.acquire() as conn:
#         rows = await conn.fetch('''
#             SELECT n.user_id FROM notifications n
#             JOIN users u ON n.user_id = u.user_id
#             WHERE n.is_enabled = TRUE AND u.is_active = TRUE
#         ''')
#         return [row['user_id'] for row in rows]
#
#
# async def get_user_notification_settings(user_id: int) -> dict:
#     """Получает настройки уведомлений пользователя"""
#     async with db_pool.acquire() as conn:
#         row = await conn.fetchrow(
#             'SELECT * FROM notifications WHERE user_id = $1',
#             user_id
#         )
#         if not row:
#             # Создаём настройки по умолчанию, если их нет
#             await conn.execute('''
#                 INSERT INTO notifications (user_id) VALUES ($1)
#                 ON CONFLICT (user_id) DO NOTHING
#             ''', user_id)
#             return {
#                 'is_enabled': True,
#                 'daily_reminder': True,
#                 'news': True,
#                 'missions': True
#             }
#
#         return dict(row)
#
#
# async def update_notification_setting(user_id: int, setting: str, value: bool):
#     """Обновляет конкретную настройку уведомлений"""
#     # Защита от SQL инъекций
#     allowed_settings = ['is_enabled', 'daily_reminder', 'news', 'missions']
#     if setting not in allowed_settings:
#         raise ValueError(f"Недопустимая настройка: {setting}")
#
#     async with db_pool.acquire() as conn:
#         await conn.execute(f'''
#             INSERT INTO notifications (user_id, {setting})
#             VALUES ($1, $2)
#             ON CONFLICT (user_id) DO UPDATE SET {setting} = $2
#         ''', user_id, value)
#
#
# async def update_last_notification_time(user_id: int):
#     """Обновляет время последнего уведомления (для защиты от спама)"""
#     async with db_pool.acquire() as conn:
#         await conn.execute('''
#             UPDATE notifications SET last_notification = CURRENT_TIMESTAMP
#             WHERE user_id = $1
#         ''', user_id)
#
#
# async def get_users_for_daily_reminder() -> List[int]:
#     """Получает пользователей, которым нужно отправить ежедневное напоминание"""
#     async with db_pool.acquire() as conn:
#         rows = await conn.fetch('''
#             SELECT n.user_id FROM notifications n
#             JOIN users u ON n.user_id = u.user_id
#             WHERE n.daily_reminder = TRUE
#             AND n.is_enabled = TRUE
#             AND u.is_active = TRUE
#             AND (n.last_notification IS NULL OR n.last_notification < NOW() - INTERVAL '20 hours')
#         ''')
#         return [row['user_id'] for row in rows]
#
#
# async def get_user_language(user_id: int) -> str:
#     """Получает предпочтительный язык пользователя"""
#     async with db_pool.acquire() as conn:
#         try:
#             result = await conn.fetchval('SELECT language FROM users WHERE user_id = $1', user_id)
#             return result or 'ru'
#         except:
#             return 'ru'
#
#
# async def set_user_language(user_id: int, language: str):
#     """Устанавливает язык пользователя"""
#     async with db_pool.acquire() as conn:
#         await conn.execute('UPDATE users SET language = $1 WHERE user_id = $2', language, user_id)
#
#
# async def get_user_premium_status(user_id: int) -> bool:
#     """Проверяет, является ли пользователь премиум"""
#     async with db_pool.acquire() as conn:
#         try:
#             result = await conn.fetchval('SELECT is_premium FROM users WHERE user_id = $1', user_id)
#             return result or False
#         except:
#             return False
#
#
# async def get_prompts_by_subcategory(subcategory: str, language: str) -> List[Dict]:
#     """Получает промпты для конкретной подкатегории и языка"""
#     async with db_pool.acquire() as conn:
#         try:
#             rows = await conn.fetch(
#                 'SELECT title, content, is_premium FROM prompts WHERE subcategory = $1 AND language = $2',
#                 subcategory, language
#             )
#             return [dict(row) for row in rows]
#         except:
#             return []
#
#
# # ==============================================================================
# # 5. ЗАКРЫТИЕ ПОДКЛЮЧЕНИЯ
# # ==============================================================================
# async def close_db():
#     """Закрытие подключения при остановке бота"""
#     if db_pool:
#         await db_pool.close()
#         print("🛑 База данных отключена")

###


import asyncpg
import os
import random

from dotenv import load_dotenv
from typing import List, Dict
from datetime import date, timedelta

load_dotenv()

# ==============================================================================
# 1. КОНФИГУРАЦИЯ ПОДКЛЮЧЕНИЯ
# ==============================================================================

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
}

db_pool: asyncpg.Pool | None = None

# ==============================================================================
# 2. ПУЛЫ МИССИЙ
# ==============================================================================

DAILY_MISSIONS_POOL = [
    {"code": "daily_open_profile", "title": "Открыть профиль", "target": 1, "reward": 3},
    {"code": "daily_claim_streak", "title": "Продлить ударный режим", "target": 1, "reward": 4},
    {"code": "daily_send_1_ai", "title": "Отправить 1 сообщение ИИ", "target": 1, "reward": 4},
    {"code": "daily_send_3_ai", "title": "Отправить 3 сообщения ИИ", "target": 3, "reward": 8},
    {"code": "daily_use_search", "title": "Использовать поиск моделей", "target": 1, "reward": 3},
]

PERMANENT_MISSIONS_POOL = [
    {"code": "perm_ai_10", "title": "Написать 10 сообщений ИИ", "target": 10, "reward": 20},
    {"code": "perm_ai_25", "title": "Написать 25 сообщений ИИ", "target": 25, "reward": 40},
    {"code": "perm_streak_3", "title": "Продержать ударный режим 3 дня", "target": 3, "reward": 15},
    {"code": "perm_streak_7", "title": "Продержать ударный режим 7 дней", "target": 7, "reward": 35},
    {"code": "perm_buy_freeze_1", "title": "Купить первую заморозку", "target": 1, "reward": 10},
]

# ==============================================================================
# 3. ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ==============================================================================

async def init_db():
    """Инициализация пула соединений и миграция таблиц."""
    global db_pool

    try:
        db_pool = await asyncpg.create_pool(**DB_CONFIG, min_size=3, max_size=15)
        print("✅ База данных подключена!")

        async with db_pool.acquire() as conn:
            # ------------------------------------------------------------------
            # USERS
            # ------------------------------------------------------------------
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'users'
                )
            """)

            if not table_exists:
                print("📋 Таблица users не существует, создаём...")
                await create_users_table(conn)
            else:
                print("📋 Таблица users существует, проверяем структуру...")
                await add_column_if_not_exists(conn, "users", "language", "VARCHAR(10) DEFAULT 'ru'")
                await add_column_if_not_exists(conn, "users", "is_premium", "BOOLEAN DEFAULT FALSE")
                await add_column_if_not_exists(conn, "users", "is_active", "BOOLEAN DEFAULT TRUE")
                await add_column_if_not_exists(conn, "users", "coins", "INT DEFAULT 0")
                await add_column_if_not_exists(conn, "users", "streak", "INT DEFAULT 0")
                await add_column_if_not_exists(conn, "users", "freeze_count", "INT DEFAULT 0")
                await add_column_if_not_exists(conn, "users", "last_activity_date", "DATE DEFAULT CURRENT_DATE")
                await add_column_if_not_exists(conn, "users", "last_streak_claim_date", "DATE")
                await add_column_if_not_exists(conn, "users", "joined_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                await add_column_if_not_exists(conn, "users", "last_active", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                print("✅ Все колонки users проверены")

            # ------------------------------------------------------------------
            # NOTIFICATIONS
            # ------------------------------------------------------------------
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                    is_enabled BOOLEAN DEFAULT TRUE,
                    daily_reminder BOOLEAN DEFAULT TRUE,
                    news BOOLEAN DEFAULT TRUE,
                    missions BOOLEAN DEFAULT TRUE,
                    last_notification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Таблица notifications готова")

            # ------------------------------------------------------------------
            # PROMPTS
            # ------------------------------------------------------------------
            await conn.execute("""
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
            """)
            print("✅ Таблица prompts готова")

            # ------------------------------------------------------------------
            # AI CHAT HISTORY
            # ------------------------------------------------------------------
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_chat_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    model_name VARCHAR(100),
                    user_message TEXT,
                    bot_response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Таблица ai_chat_history готова")

            # ------------------------------------------------------------------
            # USER SAVED PROMPTS
            # ------------------------------------------------------------------
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_saved_prompts (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    prompt_id INTEGER,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Таблица user_saved_prompts готова")

            # ------------------------------------------------------------------
            # USER MISSIONS
            # ------------------------------------------------------------------
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_missions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    mission_code VARCHAR(100) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    mission_type VARCHAR(20) NOT NULL, -- daily / permanent
                    target_value INT DEFAULT 1,
                    progress INT DEFAULT 0,
                    reward INT DEFAULT 0,
                    is_completed BOOLEAN DEFAULT FALSE,
                    assigned_date DATE,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Таблица user_missions готова")

        print("✅ Все таблицы проверены и готовы")

    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        raise


async def create_users_table(conn):
    """Создаёт таблицу users с полной актуальной структурой."""
    await conn.execute("""
        CREATE TABLE users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            language VARCHAR(10) DEFAULT 'ru',
            is_premium BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            coins INT DEFAULT 0,
            streak INT DEFAULT 0,
            freeze_count INT DEFAULT 0,
            last_activity_date DATE DEFAULT CURRENT_DATE,
            last_streak_claim_date DATE,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Таблица users создана")


async def add_column_if_not_exists(conn, table_name: str, column_name: str, column_type: str):
    """Добавляет колонку, если она отсутствует."""
    exists = await conn.fetchval(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = '{table_name}' AND column_name = '{column_name}'
        )
    """)

    if not exists:
        await conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        print(f"✅ Колонка {column_name} добавлена")
    else:
        print(f"✓ Колонка {column_name} уже существует")

# ==============================================================================
# 4. ПОЛЬЗОВАТЕЛИ
# ==============================================================================

async def add_or_update_user(
    user_id: int,
    username: str,
    first_name: str,
    last_name: str,
    is_premium: bool = False
):
    """
    Добавляет нового пользователя или обновляет данные существующего.
    ВАЖНО: стрик здесь НЕ увеличивается автоматически.
    """
    async with db_pool.acquire() as conn:
        today = date.today()

        await conn.execute("""
            INSERT INTO users (
                user_id, username, first_name, last_name, is_premium,
                last_active, last_activity_date
            )
            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, $6)
            ON CONFLICT (user_id) DO UPDATE SET
                username = $2,
                first_name = $3,
                last_name = $4,
                is_premium = $5,
                last_active = CURRENT_TIMESTAMP,
                last_activity_date = $6
        """, user_id, username, first_name, last_name, is_premium, today)

        await conn.execute("""
            INSERT INTO notifications (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id)


async def get_user_profile_stats(user_id: int) -> dict:
    """Получает статистику профиля пользователя."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT coins, streak, is_premium, joined_at
            FROM users
            WHERE user_id = $1
        """, user_id)

        if not row:
            return {
                "coins": 0,
                "streak": 0,
                "is_premium": False,
                "days_in_bot": 0
            }

        joined_at = row["joined_at"]
        days_in_bot = 0
        if joined_at:
            days_in_bot = (date.today() - joined_at.date()).days + 1

        return {
            "coins": row["coins"] or 0,
            "streak": row["streak"] or 0,
            "is_premium": row["is_premium"] or False,
            "days_in_bot": days_in_bot
        }


async def update_user_coins(user_id: int, amount: int):
    """Меняет баланс токенов пользователя."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE users
            SET coins = coins + $1
            WHERE user_id = $2
        """, amount, user_id)


async def save_ai_message(user_id: int, model: str, user_msg: str, bot_msg: str):
    """Сохраняет историю диалога с ИИ."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO ai_chat_history (user_id, model_name, user_message, bot_response)
            VALUES ($1, $2, $3, $4)
        """, user_id, model, user_msg, bot_msg)

# ==============================================================================
# 5. УВЕДОМЛЕНИЯ
# ==============================================================================

async def get_all_active_users() -> List[int]:
    """Список активных пользователей с включёнными уведомлениями."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT n.user_id
            FROM notifications n
            JOIN users u ON n.user_id = u.user_id
            WHERE n.is_enabled = TRUE
              AND u.is_active = TRUE
        """)
        return [row["user_id"] for row in rows]


async def get_user_notification_settings(user_id: int) -> dict:
    """Получает настройки уведомлений пользователя."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM notifications
            WHERE user_id = $1
        """, user_id)

        if not row:
            await conn.execute("""
                INSERT INTO notifications (user_id)
                VALUES ($1)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id)

            return {
                "is_enabled": True,
                "daily_reminder": True,
                "news": True,
                "missions": True
            }

        return dict(row)


async def update_notification_setting(user_id: int, setting: str, value: bool):
    """Обновляет одну настройку уведомлений."""
    allowed_settings = ["is_enabled", "daily_reminder", "news", "missions"]
    if setting not in allowed_settings:
        raise ValueError(f"Недопустимая настройка: {setting}")

    async with db_pool.acquire() as conn:
        await conn.execute(f"""
            INSERT INTO notifications (user_id, {setting})
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET {setting} = $2
        """, user_id, value)


async def update_last_notification_time(user_id: int):
    """Обновляет время последнего уведомления."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE notifications
            SET last_notification = CURRENT_TIMESTAMP
            WHERE user_id = $1
        """, user_id)


async def get_users_for_daily_reminder() -> List[int]:
    """Получает пользователей для ежедневного напоминания."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT n.user_id
            FROM notifications n
            JOIN users u ON n.user_id = u.user_id
            WHERE n.daily_reminder = TRUE
              AND n.is_enabled = TRUE
              AND u.is_active = TRUE
              AND (n.last_notification IS NULL OR n.last_notification < NOW() - INTERVAL '20 hours')
        """)
        return [row["user_id"] for row in rows]

# ==============================================================================
# 6. МУЛЬТИЯЗЫЧНОСТЬ / PREMIUM / ПРОМПТЫ
# ==============================================================================

async def get_user_language(user_id: int) -> str:
    """Получает язык пользователя."""
    async with db_pool.acquire() as conn:
        try:
            result = await conn.fetchval("""
                SELECT language
                FROM users
                WHERE user_id = $1
            """, user_id)
            return result or "ru"
        except Exception:
            return "ru"


async def set_user_language(user_id: int, language: str):
    """Устанавливает язык пользователя."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE users
            SET language = $1
            WHERE user_id = $2
        """, language, user_id)


async def get_user_premium_status(user_id: int) -> bool:
    """Проверяет, есть ли premium у пользователя."""
    async with db_pool.acquire() as conn:
        try:
            result = await conn.fetchval("""
                SELECT is_premium
                FROM users
                WHERE user_id = $1
            """, user_id)
            return result or False
        except Exception:
            return False


async def get_prompts_by_subcategory(subcategory: str, language: str) -> List[Dict]:
    """Получает промпты по подкатегории и языку."""
    async with db_pool.acquire() as conn:
        try:
            rows = await conn.fetch("""
                SELECT title, content, is_premium
                FROM prompts
                WHERE subcategory = $1 AND language = $2
            """, subcategory, language)
            return [dict(row) for row in rows]
        except Exception:
            return []

# ==============================================================================
# 7. ЭКОНОМИКА / МИССИИ / СТРИК
# ==============================================================================

async def ensure_permanent_missions(user_id: int):
    """Создаёт постоянные миссии, если их ещё нет."""
    async with db_pool.acquire() as conn:
        for mission in PERMANENT_MISSIONS_POOL:
            exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1
                    FROM user_missions
                    WHERE user_id = $1
                      AND mission_code = $2
                      AND mission_type = 'permanent'
                )
            """, user_id, mission["code"])

            if not exists:
                await conn.execute("""
                    INSERT INTO user_missions
                    (user_id, mission_code, title, mission_type, target_value, reward, assigned_date)
                    VALUES ($1, $2, $3, 'permanent', $4, $5, CURRENT_DATE)
                """, user_id, mission["code"], mission["title"], mission["target"], mission["reward"])


async def ensure_daily_missions(user_id: int):
    """Каждый день выдаёт пользователю 3 случайные ежедневные миссии."""
    async with db_pool.acquire() as conn:
        count_today = await conn.fetchval("""
            SELECT COUNT(*)
            FROM user_missions
            WHERE user_id = $1
              AND mission_type = 'daily'
              AND assigned_date = CURRENT_DATE
        """, user_id)

        if count_today and count_today >= 3:
            return

        selected = random.sample(DAILY_MISSIONS_POOL, 3)

        for mission in selected:
            exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1
                    FROM user_missions
                    WHERE user_id = $1
                      AND mission_code = $2
                      AND mission_type = 'daily'
                      AND assigned_date = CURRENT_DATE
                )
            """, user_id, mission["code"])

            if not exists:
                await conn.execute("""
                    INSERT INTO user_missions
                    (user_id, mission_code, title, mission_type, target_value, reward, assigned_date)
                    VALUES ($1, $2, $3, 'daily', $4, $5, CURRENT_DATE)
                """, user_id, mission["code"], mission["title"], mission["target"], mission["reward"])


async def get_user_missions(user_id: int) -> dict:
    """Возвращает ежедневные и постоянные миссии пользователя."""
    await ensure_daily_missions(user_id)
    await ensure_permanent_missions(user_id)

    async with db_pool.acquire() as conn:
        daily_rows = await conn.fetch("""
            SELECT *
            FROM user_missions
            WHERE user_id = $1
              AND mission_type = 'daily'
              AND assigned_date = CURRENT_DATE
            ORDER BY id
        """, user_id)

        permanent_rows = await conn.fetch("""
            SELECT *
            FROM user_missions
            WHERE user_id = $1
              AND mission_type = 'permanent'
            ORDER BY id
        """, user_id)

        return {
            "daily": [dict(row) for row in daily_rows],
            "permanent": [dict(row) for row in permanent_rows]
        }


async def update_mission_progress(user_id: int, mission_code: str, amount: int = 1):
    """Обновляет прогресс миссии и начисляет награду при завершении."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT *
            FROM user_missions
            WHERE user_id = $1
              AND mission_code = $2
              AND (
                    (mission_type = 'daily' AND assigned_date = CURRENT_DATE)
                    OR mission_type = 'permanent'
                  )
            ORDER BY id DESC
            LIMIT 1
        """, user_id, mission_code)

        if not row or row["is_completed"]:
            return False

        new_progress = min((row["progress"] or 0) + amount, row["target_value"])
        is_completed = new_progress >= row["target_value"]

        await conn.execute("""
            UPDATE user_missions
            SET progress = $1,
                is_completed = $2,
                completed_at = CASE WHEN $2 = TRUE THEN CURRENT_TIMESTAMP ELSE completed_at END
            WHERE id = $3
        """, new_progress, is_completed, row["id"])

        if is_completed and not row["is_completed"]:
            await conn.execute("""
                UPDATE users
                SET coins = coins + $1
                WHERE user_id = $2
            """, row["reward"], user_id)

            if row["mission_type"] == "daily":
                await grant_daily_bonus_if_all_completed(user_id)

        return is_completed


async def grant_daily_bonus_if_all_completed(user_id: int):
    """Бонус за выполнение всех daily-миссий за день."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT is_completed
            FROM user_missions
            WHERE user_id = $1
              AND mission_type = 'daily'
              AND assigned_date = CURRENT_DATE
        """, user_id)

        if len(rows) < 3:
            return

        if all(row["is_completed"] for row in rows):
            bonus_exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1
                    FROM user_missions
                    WHERE user_id = $1
                      AND mission_code = 'daily_all_completed_bonus'
                      AND mission_type = 'daily'
                      AND assigned_date = CURRENT_DATE
                )
            """, user_id)

            if not bonus_exists:
                await conn.execute("""
                    INSERT INTO user_missions
                    (user_id, mission_code, title, mission_type, target_value, progress, reward, is_completed, assigned_date, completed_at)
                    VALUES ($1, 'daily_all_completed_bonus', 'Выполнить все ежедневные миссии', 'daily', 1, 1, 10, TRUE, CURRENT_DATE, CURRENT_TIMESTAMP)
                """, user_id)

                await conn.execute("""
                    UPDATE users
                    SET coins = coins + 10
                    WHERE user_id = $1
                """, user_id)


async def get_user_economy(user_id: int) -> dict:
    """Возвращает экономику пользователя."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT coins, streak, freeze_count, last_streak_claim_date
            FROM users
            WHERE user_id = $1
        """, user_id)

        if not row:
            return {
                "coins": 0,
                "streak": 0,
                "freeze_count": 0,
                "last_streak_claim_date": None
            }

        return dict(row)


async def claim_daily_streak(user_id: int) -> dict:
    """
    Продлевает ударный режим по кнопке.
    Если день пропущен и есть freeze_count, расходует заморозку.
    """
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT streak, freeze_count, last_streak_claim_date
            FROM users
            WHERE user_id = $1
        """, user_id)

        if not row:
            return {"ok": False, "message": "Пользователь не найден"}

        today = date.today()
        last_claim = row["last_streak_claim_date"]
        streak = row["streak"] or 0
        freeze_count = row["freeze_count"] or 0

        if last_claim == today:
            return {"ok": False, "message": "Сегодня ударный режим уже продлён"}

        used_freeze = False

        if last_claim is None:
            new_streak = 1
        elif last_claim == today - timedelta(days=1):
            new_streak = streak + 1
        else:
            missed_days = (today - last_claim).days - 1
            if missed_days >= 1 and freeze_count > 0:
                freeze_count -= 1
                used_freeze = True
                new_streak = streak + 1
            else:
                new_streak = 1

        reward = 3
        if new_streak % 30 == 0:
            reward = 50
        elif new_streak % 7 == 0:
            reward = 15
        elif new_streak % 3 == 0:
            reward = 5

        await conn.execute("""
            UPDATE users
            SET streak = $1,
                last_streak_claim_date = $2,
                freeze_count = $3,
                coins = coins + $4
            WHERE user_id = $5
        """, new_streak, today, freeze_count, reward, user_id)

        return {
            "ok": True,
            "streak": new_streak,
            "reward": reward,
            "used_freeze": used_freeze,
            "freeze_count": freeze_count
        }


async def buy_freeze(user_id: int, price: int = 30, max_freezes: int = 2) -> dict:
    """Покупает заморозку за токены."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT coins, freeze_count
            FROM users
            WHERE user_id = $1
        """, user_id)

        if not row:
            return {"ok": False, "message": "Пользователь не найден"}

        coins = row["coins"] or 0
        freeze_count = row["freeze_count"] or 0

        if freeze_count >= max_freezes:
            return {"ok": False, "message": "У вас уже максимум заморозок"}

        if coins < price:
            return {"ok": False, "message": f"Недостаточно токенов. Нужно: {price}"}

        await conn.execute("""
            UPDATE users
            SET coins = coins - $1,
                freeze_count = freeze_count + 1
            WHERE user_id = $2
        """, price, user_id)

        return {"ok": True, "message": f"Заморозка куплена за {price} токенов"}

# ==============================================================================
# 8. ТРЕКИНГ ПРОГРЕССА МИССИЙ
# ==============================================================================

async def track_ai_message_sent(user_id: int):
    await update_mission_progress(user_id, "daily_send_1_ai", 1)
    await update_mission_progress(user_id, "daily_send_3_ai", 1)
    await update_mission_progress(user_id, "perm_ai_10", 1)
    await update_mission_progress(user_id, "perm_ai_25", 1)


async def track_profile_open(user_id: int):
    await update_mission_progress(user_id, "daily_open_profile", 1)


async def track_search_used(user_id: int):
    await update_mission_progress(user_id, "daily_use_search", 1)


async def track_streak_claim(user_id: int, streak_value: int):
    await update_mission_progress(user_id, "daily_claim_streak", 1)

    if streak_value >= 3:
        await update_mission_progress(user_id, "perm_streak_3", streak_value)
    if streak_value >= 7:
        await update_mission_progress(user_id, "perm_streak_7", streak_value)


async def track_buy_freeze(user_id: int):
    await update_mission_progress(user_id, "perm_buy_freeze_1", 1)

# ==============================================================================
# 9. ЗАКРЫТИЕ БАЗЫ
# ==============================================================================

async def close_db():
    """Закрывает пул соединений."""
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None
        print("🛑 База данных отключена")


# ==============================================================================
# 9. ЛИДЕРБОРДЫ
# ==============================================================================

def _display_name_sql() -> str:
    return """
        CASE
            WHEN first_name IS NOT NULL AND first_name <> '' THEN first_name
            WHEN username IS NOT NULL AND username <> '' THEN '@' || username
            ELSE 'Игрок #' || user_id::text
        END
    """


async def get_top_users_by_coins(limit: int = 10) -> list[dict]:
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT
                user_id,
                {_display_name_sql()} AS display_name,
                coins
            FROM users
            WHERE is_active = TRUE
            ORDER BY coins DESC, streak DESC, user_id ASC
            LIMIT $1
        """, limit)

        return [dict(row) for row in rows]


async def get_user_rank_by_coins(user_id: int) -> dict:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(f"""
            WITH ranked AS (
                SELECT
                    user_id,
                    {_display_name_sql()} AS display_name,
                    coins,
                    ROW_NUMBER() OVER (ORDER BY coins DESC, streak DESC, user_id ASC) AS rank
                FROM users
                WHERE is_active = TRUE
            )
            SELECT *
            FROM ranked
            WHERE user_id = $1
        """, user_id)

        return dict(row) if row else {"rank": None, "coins": 0, "display_name": "Вы"}


async def get_top_users_by_streak(limit: int = 10) -> list[dict]:
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT
                user_id,
                {_display_name_sql()} AS display_name,
                streak
            FROM users
            WHERE is_active = TRUE
            ORDER BY streak DESC, coins DESC, user_id ASC
            LIMIT $1
        """, limit)

        return [dict(row) for row in rows]


async def get_user_rank_by_streak(user_id: int) -> dict:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(f"""
            WITH ranked AS (
                SELECT
                    user_id,
                    {_display_name_sql()} AS display_name,
                    streak,
                    ROW_NUMBER() OVER (ORDER BY streak DESC, coins DESC, user_id ASC) AS rank
                FROM users
                WHERE is_active = TRUE
            )
            SELECT *
            FROM ranked
            WHERE user_id = $1
        """, user_id)

        return dict(row) if row else {"rank": None, "streak": 0, "display_name": "Вы"}


async def get_top_best_users(limit: int = 10) -> list[dict]:
    """
    Общий рейтинг лучших игроков:
    score = coins + streak * 10 + completed_permanent * 15 + completed_daily * 5
    """
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(f"""
            WITH mission_stats AS (
                SELECT
                    user_id,
                    COALESCE(SUM(CASE WHEN mission_type = 'daily' AND is_completed = TRUE THEN 1 ELSE 0 END), 0) AS completed_daily,
                    COALESCE(SUM(CASE WHEN mission_type = 'permanent' AND is_completed = TRUE THEN 1 ELSE 0 END), 0) AS completed_permanent
                FROM user_missions
                GROUP BY user_id
            )
            SELECT
                u.user_id,
                {_display_name_sql().replace('user_id', 'u.user_id').replace('first_name', 'u.first_name').replace('username', 'u.username')} AS display_name,
                u.coins,
                u.streak,
                COALESCE(ms.completed_daily, 0) AS completed_daily,
                COALESCE(ms.completed_permanent, 0) AS completed_permanent,
                (
                    u.coins
                    + u.streak * 10
                    + COALESCE(ms.completed_permanent, 0) * 15
                    + COALESCE(ms.completed_daily, 0) * 5
                ) AS score
            FROM users u
            LEFT JOIN mission_stats ms ON u.user_id = ms.user_id
            WHERE u.is_active = TRUE
            ORDER BY score DESC, u.coins DESC, u.streak DESC, u.user_id ASC
            LIMIT $1
        """, limit)

        return [dict(row) for row in rows]


async def get_user_rank_best(user_id: int) -> dict:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(f"""
            WITH mission_stats AS (
                SELECT
                    user_id,
                    COALESCE(SUM(CASE WHEN mission_type = 'daily' AND is_completed = TRUE THEN 1 ELSE 0 END), 0) AS completed_daily,
                    COALESCE(SUM(CASE WHEN mission_type = 'permanent' AND is_completed = TRUE THEN 1 ELSE 0 END), 0) AS completed_permanent
                FROM user_missions
                GROUP BY user_id
            ),
            ranked AS (
                SELECT
                    u.user_id,
                    {_display_name_sql().replace('user_id', 'u.user_id').replace('first_name', 'u.first_name').replace('username', 'u.username')} AS display_name,
                    u.coins,
                    u.streak,
                    COALESCE(ms.completed_daily, 0) AS completed_daily,
                    COALESCE(ms.completed_permanent, 0) AS completed_permanent,
                    (
                        u.coins
                        + u.streak * 10
                        + COALESCE(ms.completed_permanent, 0) * 15
                        + COALESCE(ms.completed_daily, 0) * 5
                    ) AS score,
                    ROW_NUMBER() OVER (
                        ORDER BY
                            (
                                u.coins
                                + u.streak * 10
                                + COALESCE(ms.completed_permanent, 0) * 15
                                + COALESCE(ms.completed_daily, 0) * 5
                            ) DESC,
                            u.coins DESC,
                            u.streak DESC,
                            u.user_id ASC
                    ) AS rank
                FROM users u
                LEFT JOIN mission_stats ms ON u.user_id = ms.user_id
                WHERE u.is_active = TRUE
            )
            SELECT *
            FROM ranked
            WHERE user_id = $1
        """, user_id)

        return dict(row) if row else {
            "rank": None,
            "score": 0,
            "coins": 0,
            "streak": 0,
            "completed_daily": 0,
            "completed_permanent": 0,
            "display_name": "Вы"
        }