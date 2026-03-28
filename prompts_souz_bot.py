from aiogram import Bot, Dispatcher, Router
from os  import getenv
import asyncio
from dotenv import load_dotenv
from aiogram.types import Message
import signal
#from prompts_vault.routes import router
from routes import router
import logging
from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError
from database import init_db, close_db, add_or_update_user, get_user_language, set_user_language, get_all_active_users, mark_user_inactive
from routes import get_main_reply_inline, get_categories_ru, get_categories_tat, get_categories_eng


load_dotenv()
TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()

dp.include_router(router)


async def main():
   bot = Bot(token=TOKEN)
   print("start...")

   # ✅ Инициализируем БД ПЕРЕД запуском бота
   await init_db()

   try:
      await dp.start_polling(bot)
   except asyncio.CancelledError:
      pass
   finally:
      print("Бот успешно остановлен.")
      await bot.close()
      await close_db()



if __name__ == "__main__":
   #asyncio.run(main())
   try:
      asyncio.run(main())
   except KeyboardInterrupt:
      # Перехватываем нажатие Ctrl+C
     pass






