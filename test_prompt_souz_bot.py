from aiogram import Bot, Dispatcher
from os import getenv
import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

from test_routes import router
from test_database import (
    init_db,
    close_db,
    get_users_for_daily_reminder,
    update_last_notification_time,
    get_user_language
)
from test_languges import get_text

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
    Проверяет пользователей с включенными daily-уведомлениями
    и отправляет им сообщение на их языке.
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