


from aiogram import Bot, Dispatcher
from os import getenv
import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

from routes import router
from database import (
    init_db,
    close_db,
    get_users_for_daily_reminder,
    update_last_notification_time,
    get_user_language
)
from languages import get_text

TOKEN = getenv("BOT_TOKEN")


# ==============================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ==============================================================================

logging.basicConfig(level=logging.INFO)


# ==============================================================================
# ЗАГРУЗКА .ENV
# ==============================================================================


# ==============================================================================
# DISPATCHER
# ==============================================================================

dp = Dispatcher()
dp.include_router(router)


# ==============================================================================
# ЕЖЕДНЕВНЫЙ ПЛАНИРОВЩИК НАПОМИНАНИЙ
# ==============================================================================

async def daily_reminder_scheduler(bot: Bot):
    """
    Планировщик ежедневных напоминаний.

    Запускается в фоновом режиме (asyncio.create_task) и работает бесконечно.
    Раз в 10 минут проверяет в БД пользователей,
    у которых включены ежедневные уведомления (daily_reminder),
    и отправляет им напоминание на их родном языке.

    Аргументы:
        bot (Bot): Экземпляр aiogram Bot для отправки сообщений.

    Работает в цикле:
        1. Спит 600 секунд.
        2. Получает список user_id из БД через get_users_for_daily_reminder().
        3. Для каждого пользователя:
            - получает язык (get_user_language),
            - отправляет сообщение (get_text с ключом 'daily_reminder'),
            - обновляет время последнего уведомления (update_last_notification_time).
        4. При ошибке с одним пользователем — логирует предупреждение и идёт дальше.
        5. При глобальной ошибке — логирует ошибку и спит 30 секунд перед повтором.
    """
    while True:
        try:
            # Проверка раз в 10 минут
            await asyncio.sleep(600)

            users = await get_users_for_daily_reminder()

            for user_id in users:
                try:
                    user_lang = await get_user_language(user_id)

                    await bot.send_message(
                        chat_id=user_id,
                        text=get_text(user_lang, 'daily_reminder'),
                        parse_mode="Markdown"
                    )

                    await update_last_notification_time(user_id)
                    await asyncio.sleep(0.05)

                except Exception as e:
                    logging.warning(f"Не удалось отправить daily reminder пользователю {user_id}: {e}")

        except Exception as e:
            logging.error(f"Ошибка планировщика daily_reminder_scheduler: {e}")
            await asyncio.sleep(30)


# ==============================================================================
# ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА
# ==============================================================================

async def main():
    """
    Главная асинхронная функция запуска бота.

    Последовательность действий:
        1. Проверяет наличие BOT_TOKEN из .env.
        2. Создаёт экземпляр Bot с токеном.
        3. Инициализирует подключение к БД (init_db).
        4. Запускает фоновый планировщик ежедневных напоминаний (daily_reminder_scheduler).
        5. Запускает long-polling через dp.start_polling(bot) для приёма сообщений.
        6. При остановке (CancelledError, Exception, finally):
            - закрывает сессию бота (bot.session.close()),
            - закрывает соединение с БД (close_db()).

    Исключения:
        ValueError: Если BOT_TOKEN не задан.
        CancelledError: При отмене задачи polling.
        Exception: Любая другая ошибка во время polling.
    """
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN не найден в .env")

    bot = Bot(token=TOKEN)

    print("🚀 Start Bot...")

    # Инициализируем БД
    await init_db()

    # Запускаем планировщик уведомлений
    asyncio.create_task(daily_reminder_scheduler(bot))

    try:
        print("✅ Бот запущен! Ожидание сообщений...")
        await dp.start_polling(bot)

    except asyncio.CancelledError:
        print("⚠️ Polling cancelled")

    except Exception as e:
        print(f"❌ Ошибка polling: {e}")

    finally:
        print("🛑 Бот успешно остановлен.")
        await bot.session.close()
        await close_db()


# ==============================================================================
# ТОЧКА ВХОДА
# ==============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Остановка пользователем (Ctrl+C)")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
