# from aiogram import Bot, Dispatcher, Router
# from os  import getenv
# import asyncio
# from dotenv import load_dotenv
# from aiogram.types import Message
# import signal
# #from prompts_vault.routes import router
# from routes import router
# import logging
# from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError
# from database import init_db, close_db, add_or_update_user, get_users_for_daily_reminder, update_last_notification_time
# import aiohttp
#
#
# # Настройка логирования
# logging.basicConfig(level=logging.INFO)
#
# load_dotenv()
# TOKEN = getenv("BOT_TOKEN")
#
# dp = Dispatcher()
# dp.include_router(router)
#
#
# # ==============================================================================
# # ЗАДАЧА ПЛАНИРОВЩИКА
# # ==============================================================================
# async def daily_reminder_scheduler(bot: Bot):
#    """Ежедневная рассылка напоминаний (каждые 24 часа)"""
#    while True:
#       try:
#          await asyncio.sleep(86400)  # 24 часа86400
#
#          users = await get_users_for_daily_reminder()
#
#          for user_id in users:
#             try:
#                await bot.send_message(
#                   chat_id=user_id,
#                   text="🔔 **Напоминание из AI Hub!**\n\n"
#                        "Не забудь зайти сегодня, чтобы не прервать ударный режим! 🔥\n"
#                        "Выполняй миссии и зарабатывай койны.",
#                   parse_mode="Markdown"
#                )
#                await update_last_notification_time(user_id)
#                await asyncio.sleep(0.05)
#             except Exception:
#                pass  # Пользователь заблокировал бота
#
#       except Exception as e:
#          logging.error(f"Ошибка планировщика: {e}")
#
# async def main():
#    # ✅ Создаём бота БЕЗ ручной настройки сессии (aiogram 3.x сам управляет)
#    bot = Bot(token=TOKEN)
#
#    print("🚀 Start Bot...")
#
#    # ✅ Инициализируем БД ПЕРЕД запуском бота
#    await init_db()
#    asyncio.create_task(daily_reminder_scheduler(bot))
#    try:
#       print("✅ Бот запущен! Ожидание сообщений...")
#       await dp.start_polling(bot)
#    except asyncio.CancelledError:
#       print("⚠️ Polling cancelled")
#    except Exception as e:
#       print(f"❌ Ошибка polling: {e}")
#    finally:
#       print("🛑 Бот успешно остановлен.")
#       await bot.close()
#       await close_db()
#
#
# if __name__ == "__main__":
#    try:
#       asyncio.run(main())
#    except KeyboardInterrupt:
#       print("\n⚠️ Остановка пользователем (Ctrl+C)")
#    except Exception as e:
#       print(f"❌ Критическая ошибка: {e}")











# from aiogram import Bot, Dispatcher
# from os import getenv
# import asyncio
# from dotenv import load_dotenv
# from routes import router
# import logging
# from database import init_db, close_db, get_users_for_daily_reminder, update_last_notification_time
# from languages import get_text
#
# # Настройка логирования
# logging.basicConfig(level=logging.INFO)
#
# load_dotenv()
# TOKEN = getenv("BOT_TOKEN")
#
# dp = Dispatcher()
# dp.include_router(router)
#
#
# # ==============================================================================
# # ЗАДАЧА ПЛАНИРОВЩИКА
# # ==============================================================================
# async def daily_reminder_scheduler(bot: Bot):
#    """Ежедневная рассылка напоминаний (каждые 24 часа)"""
#    while True:
#       try:
#          await asyncio.sleep(10)  # 24 часа
#
#          users = await get_users_for_daily_reminder()
#
#          for user_id in users:
#             try:
#                # Получаем язык пользователя для персонализированного уведомления
#                user_lang = await get_user_language_from_db(user_id)
#
#                await bot.send_message(
#                   chat_id=user_id,
#                   text=get_text(user_lang, 'daily_reminder'),
#                   parse_mode="Markdown"
#                )
#                await update_last_notification_time(user_id)
#                await asyncio.sleep(0.05)
#             except Exception:
#                pass  # Пользователь заблокировал бота
#
#       except Exception as e:
#          logging.error(f"Ошибка планировщика: {e}")
#
#
# async def get_user_language_from_db(user_id: int) -> str:
#    """Вспомогательная функция для получения языка (для планировщика)"""
#    from database import db_pool
#    async with db_pool.acquire() as conn:
#       try:
#          result = await conn.fetchval('SELECT language FROM users WHERE user_id = $1', user_id)
#          return result or 'ru'
#       except:
#          return 'ru'
#
#
# async def main():
#    # ✅ Создаём бота
#    bot = Bot(token=TOKEN)
#    print("🚀 Start Bot...")
#
#    # ✅ Инициализируем БД ПЕРЕД запуском бота
#    await init_db()
#
#    # ✅ Запускаем планировщик уведомлений
#    asyncio.create_task(daily_reminder_scheduler(bot))
#
#    try:
#       print("✅ Бот запущен! Ожидание сообщений...")
#       await dp.start_polling(bot)
#    except asyncio.CancelledError:
#       print("⚠️ Polling cancelled")
#    except Exception as e:
#       print(f"❌ Ошибка polling: {e}")
#    finally:
#       print("🛑 Бот успешно остановлен.")
#       await bot.close()
#       await close_db()
#
#
# if __name__ == "__main__":
#    try:
#       asyncio.run(main())
#    except KeyboardInterrupt:
#       print("\n⚠️ Остановка пользователем (Ctrl+C)")
#    except Exception as e:
#       print(f"❌ Критическая ошибка: {e}")


from aiogram import Bot, Dispatcher
from os import getenv
import asyncio
import logging

from dotenv import load_dotenv

from routes import router
from database import (
    init_db,
    close_db,
    get_users_for_daily_reminder,
    update_last_notification_time,
    get_user_language
)
from languages import get_text


# ==============================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ==============================================================================

logging.basicConfig(level=logging.INFO)


# ==============================================================================
# ЗАГРУЗКА .ENV
# ==============================================================================

load_dotenv()
TOKEN = getenv("BOT_TOKEN")


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