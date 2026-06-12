# import asyncio
# from aiogram import Router, F
# from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
# from aiogram.filters import Command, CommandStart
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
# from html import escape
# import os
# import aiohttp
# from database import (
#     add_or_update_user, get_user_profile_stats,
#     get_user_notification_settings, update_notification_setting,
#     get_all_active_users, save_ai_message,
#     get_user_language, set_user_language,
#     get_user_missions, get_user_economy,
#     claim_daily_streak, buy_freeze,
#     ensure_daily_missions, ensure_permanent_missions,
#     track_ai_message_sent, track_profile_open,
#     track_search_used, track_streak_claim, track_buy_freeze
# )
# from languages import get_text, LANGUAGES
#
# router = Router()
#
# # ==============================================================================
# # 1. КОНФИГУРАЦИЯ API
# # ==============================================================================
# MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
# MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
#
# # ✅ QWEN API через OPENROUTER
# QWEN_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
# QWEN_API_URL = "https://openrouter.ai/api/v1/chat/completions"
#
# print("=" * 50)
# print("🔑 ПРОВЕРКА API КЛЮЧЕЙ:")
# print(f"MISTRAL_API_KEY: {'✅ Загружен' if MISTRAL_API_KEY else '❌ ПУСТОЙ'}")
# print(f"OPENROUTER_API_KEY: {'✅ Загружен' if QWEN_API_KEY else '❌ ПУСТОЙ'}")
# if QWEN_API_KEY:
#     print(f"QWEN_KEY начало: {QWEN_API_KEY[:15]}...")
# print("=" * 50)
# # ==============================================================================
# # 2. СОСТОЯНИЯ FSM
# # ==============================================================================
# class AIChatState(StatesGroup):
#     waiting_for_message = State()
#     current_model = State()
#
#
# class SearchState(StatesGroup):
#     waiting_for_query = State()
#
#
# # ==============================================================================
# # 3. БАЗА МОДЕЛЕЙ
# # ==============================================================================
# AI_MODELS_DB = [
#     {"id": "mistral", "name": " Mistral AI", "description": "Быстрая и эффективная модель от Mistral"},
#     {"id": "qwen", "name": " Qwen AI", "description": "Умная модель от Alibaba с глубоким пониманием контекста"},
#     {"id": "nemotron", "name": "Nemotron AI", "description": "Мощная бизнес-модель от NVIDIA для сложных задач"},
#     {"id": "gemini", "name": " Gemini Pro", "description": "Мультимодальная модель от Google"},
#     {"id": "gpt4", "name": " GPT-4", "description": "Продвинутая модель от OpenAI"},
#     {"id": "claude", "name": " Claude 3", "description": "Безопасная и мощная модель от Anthropic"},
#     {"id": "llama", "name": " Llama 3", "description": "Открытая модель от Meta"},
# ]
#
#
# # ==============================================================================
# # 4. КЛАВИАТУРЫ (С МУЛЬТИЯЗЫЧНОСТЬЮ)
# # ==============================================================================
# def get_main_menu_inline(lang: str = 'ru'):
#     """Главное меню бота"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text=get_text(lang, 'catalog_ai_btn'), callback_data="menu_catalog_ai")],
#         [InlineKeyboardButton(text=get_text(lang, 'search_btn'), callback_data="menu_search"),
#          InlineKeyboardButton(text=get_text(lang, 'tariffs_btn'), callback_data="menu_tariffs")],
#         [InlineKeyboardButton(text=get_text(lang, 'missions_btn'), callback_data="menu_missions"),
#          InlineKeyboardButton(text=get_text(lang, 'games_btn'), callback_data="menu_games")],
#         [InlineKeyboardButton(text=get_text(lang, 'profile_btn'), callback_data="menu_profile")],
#     ])
#
#
# def get_catalog_ai_inline(lang: str = 'ru'):
#     """Меню выбора модели ИИ"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text=get_text(lang, 'mistral_btn'), callback_data="ai_model_mistral")],
#         [InlineKeyboardButton(text=get_text(lang, 'qwen_btn'), callback_data="ai_model_qwen")],
#         [InlineKeyboardButton(text=get_text(lang, 'nemotron_btn'), callback_data="ai_model_nemotron")],
#         [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="back_main_menu")]
#     ])
#
#
# def get_exit_ai_inline(lang: str = 'ru'):
#     """Кнопка выхода из режима чата с ИИ"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text=get_text(lang, 'complete_session'), callback_data="exit_ai_chat")]
#     ])
#
#
# def get_profile_menu_inline(lang: str = 'ru'):
#     """Меню профиля"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text=get_text(lang, 'update'), callback_data="menu_profile")],
#         [InlineKeyboardButton(text=get_text(lang, 'language_settings'), callback_data="menu_language")],
#         [InlineKeyboardButton(text=get_text(lang, 'notifications_settings'), callback_data="menu_notifications")],
#         [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="back_main_menu")],
#     ])
#
#
# def get_search_results_inline(results: list, lang: str = 'ru'):
#     """Клавиатура с результатами поиска"""
#     keyboard = []
#     for model in results:
#         keyboard.append([InlineKeyboardButton(
#             text=model["name"],
#             callback_data=f"search_select_{model['id']}"
#         )])
#     keyboard.append([InlineKeyboardButton(text=get_text(lang, 'back_to_menu'), callback_data="back_main_menu")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_model_detail_inline(model_id: str, lang: str = 'ru'):
#     """Клавиатура для выбранной модели"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text=get_text(lang, 'launch_model'), callback_data=f"launch_model_{model_id}")],
#         [InlineKeyboardButton(text=get_text(lang, 'back_to_search'), callback_data="menu_search")],
#         [InlineKeyboardButton(text=get_text(lang, 'back_to_menu'), callback_data="back_main_menu")],
#     ])
#
#
# def get_language_inline(lang: str = 'ru'):
#     """Клавиатура выбора языка"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
#         [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
#         [InlineKeyboardButton(text="🇹🇹 Татарча", callback_data="lang_tt")],
#         [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="menu_profile")],
#     ])
#
#
# def get_notifications_inline(settings: dict, lang: str = 'ru'):
#     """Клавиатура настроек уведомлений"""
#     status = "✅ ВКЛ" if settings['is_enabled'] else "❌ ВЫКЛ"
#     daily = "🔔" if settings['daily_reminder'] else "🔕"
#     news = "📰" if settings['news'] else "📰❌"
#     missions = "🎯" if settings['missions'] else "🎯❌"
#
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(
#             text="🔘 Общие: " + ("ВКЛ ✅" if settings['is_enabled'] else "ВЫКЛ ❌"),
#             callback_data="notif_toggle_main"
#         )],
#         [InlineKeyboardButton(text=daily + " Ежедневные", callback_data="notif_toggle_daily"),
#          InlineKeyboardButton(text=news + " Новости", callback_data="notif_toggle_news")],
#         [InlineKeyboardButton(text=missions + " Миссии", callback_data="notif_toggle_missions")],
#         [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="menu_profile")],
#     ])
#
#
# # ==============================================================================
# # 5. ХЕНДЛЕРЫ НАВИГАЦИИ
# # ==============================================================================
# @router.message(CommandStart())
# async def cmd_start(message: Message):
#     """Главное меню бота при запуске"""
#     user_id = message.from_user.id
#     full_name = message.from_user.full_name
#
#     # 1. Регистрируем пользователя
#     await add_or_update_user(
#         user_id=user_id,
#         username=message.from_user.username or "",
#         first_name=message.from_user.first_name or "",
#         last_name=message.from_user.last_name or ""
#     )
#
#     # 2. Получаем язык пользователя
#     user_lang = await get_user_language(user_id)
#
#     # 3. Отправляем приветствие на языке пользователя
#     await message.answer(
#         get_text(user_lang, 'welcome', name=escape(full_name)),
#         parse_mode="Markdown",
#         reply_markup=get_main_menu_inline(user_lang)
#     )
#
#
# @router.callback_query(F.data == "back_main_menu")
# async def back_to_main(callback: CallbackQuery, state: FSMContext):
#     """Возврат в главное меню из любого раздела"""
#     await state.clear()
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await callback.message.edit_text(
#         get_text(user_lang, 'main_menu'),
#         reply_markup=get_main_menu_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # --- КАТАЛОГ ИИ ---
# @router.callback_query(F.data == "menu_catalog_ai")
# async def show_catalog_ai(callback: CallbackQuery):
#     """Показывает доступные модели ИИ"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await callback.message.edit_text(
#         get_text(user_lang, 'catalog_ai'),
#         reply_markup=get_catalog_ai_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # ==============================================================================
# # 6. НАСТРОЙКИ УВЕДОМЛЕНИЙ
# # ==============================================================================
# @router.callback_query(F.data == "menu_notifications")
# async def show_notifications_settings(callback: CallbackQuery):
#     """Показывает настройки уведомлений"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#     settings = await get_user_notification_settings(user_id)
#
#     status = "✅ ВКЛ" if settings['is_enabled'] else "❌ ВЫКЛ"
#     daily = "🔔" if settings['daily_reminder'] else "🔕"
#     news = "📰" if settings['news'] else "📰❌"
#     missions = "🎯" if settings['missions'] else "🎯❌"
#
#     text = get_text(
#         user_lang, 'notifications',
#         status=status,
#         daily=daily,
#         news=news,
#         missions=missions
#     )
#
#     await callback.message.edit_text(
#         text,
#         reply_markup=get_notifications_inline(settings, user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == "notif_toggle_main")
# async def toggle_main_notif(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     settings = await get_user_notification_settings(user_id)
#     new_value = not settings['is_enabled']
#     await update_notification_setting(user_id, 'is_enabled', new_value)
#     await show_notifications_settings(callback)
#     await callback.answer()
#
#
# @router.callback_query(F.data == "notif_toggle_daily")
# async def toggle_daily_notif(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     settings = await get_user_notification_settings(user_id)
#     new_value = not settings['daily_reminder']
#     await update_notification_setting(user_id, 'daily_reminder', new_value)
#     await show_notifications_settings(callback)
#     await callback.answer()
#
#
# @router.callback_query(F.data == "notif_toggle_news")
# async def toggle_news_notif(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     settings = await get_user_notification_settings(user_id)
#     new_value = not settings['news']
#     await update_notification_setting(user_id, 'news', new_value)
#     await show_notifications_settings(callback)
#     await callback.answer()
#
#
# @router.callback_query(F.data == "notif_toggle_missions")
# async def toggle_missions_notif(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     settings = await get_user_notification_settings(user_id)
#     new_value = not settings['missions']
#     await update_notification_setting(user_id, 'missions', new_value)
#     await show_notifications_settings(callback)
#     await callback.answer()
#
#
# # ==============================================================================
# # 7. АДМИНКА: РАССЫЛКА
# # ==============================================================================
# @router.message(Command("broadcast"))
# async def broadcast_command(message: Message):
#     """Команда для рассылки сообщений всем пользователям (ТОЛЬКО ДЛЯ АДМИНА)"""
#     ADMIN_ID = 1755580726  # ⚠️ ЗАМЕНИ НА СВОЙ TELEGRAM ID
#     if message.from_user.id != ADMIN_ID:
#         return
#
#     if not message.reply_to_message:
#         await message.answer("❌ Используйте как ответ на сообщение для рассылки")
#         return
#
#     users = await get_all_active_users()
#     success = 0
#     blocked = 0
#
#     await message.answer(f"🚀 Начинаю рассылку для {len(users)} пользователей...")
#
#     for user_id in users:
#         try:
#             await message.reply_to_message.copy(chat_id=user_id)
#             success += 1
#             await asyncio.sleep(0.05)
#         except Exception:
#             blocked += 1
#
#     await message.answer(f"✅ Готово!\nУспешно: {success}\nЗаблокировано: {blocked}")
#
#
# # ==============================================================================
# # 8. ПОИСК ПО AI МОДЕЛЯМ
# # ==============================================================================
# @router.callback_query(F.data == "menu_search")
# async def menu_search(callback: CallbackQuery, state: FSMContext):
#     """Показывает меню поиска и включает режим поиска"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await state.set_state(SearchState.waiting_for_query)
#     await callback.message.edit_text(
#         get_text(user_lang, 'search_prompt'),
#         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text=get_text(user_lang, 'back_to_menu'), callback_data="back_main_menu")]
#         ]),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.message(SearchState.waiting_for_query)
# async def process_search_query(message: Message, state: FSMContext):
#     """Обрабатывает поисковый запрос и показывает результаты"""
#     user_id = message.from_user.id
#     user_lang = await get_user_language(user_id)
#     query = message.text.lower().strip()
#
#     results = [
#         model for model in AI_MODELS_DB
#         if query in model["id"].lower() or query in model["name"].lower() or query in model["description"].lower()
#     ]
#
#     if not results:
#         await message.answer(
#             get_text(user_lang, 'search_no_results', query=escape(query)),
#             parse_mode="Markdown",
#             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                 [InlineKeyboardButton(text=get_text(user_lang, 'back_to_search'), callback_data="menu_search")],
#                 [InlineKeyboardButton(text=get_text(user_lang, 'back_to_menu'), callback_data="back_main_menu")],
#             ])
#         )
#     else:
#         results_text = "\n".join([f"• {m['name']} — {m['description']}" for m in results])
#         await message.answer(
#             get_text(user_lang, 'search_results', count=len(results), results=results_text),
#             parse_mode="Markdown",
#             reply_markup=get_search_results_inline(results, user_lang)
#         )
#
#     await state.clear()
#
#
# @router.callback_query(F.data.startswith("search_select_"))
# async def select_model_from_search(callback: CallbackQuery, state: FSMContext):
#     """Показывает детали выбранной модели"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#     model_id = callback.data.replace("search_select_", "")
#     model = next((m for m in AI_MODELS_DB if m["id"] == model_id), None)
#
#     if model:
#         await callback.message.edit_text(
#             get_text(
#                 user_lang, 'model_detail',
#                 model_name=model['name'],
#                 description=model['description'],
#                 model_id=model_id
#             ),
#             reply_markup=get_model_detail_inline(model_id, user_lang),
#             parse_mode="Markdown"
#         )
#     else:
#         await callback.message.edit_text(
#             "❌ **Модель не найдена**",
#             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                 [InlineKeyboardButton(text=get_text(user_lang, 'back_to_search'), callback_data="menu_search")],
#                 [InlineKeyboardButton(text=get_text(user_lang, 'back_to_menu'), callback_data="back_main_menu")],
#             ]),
#             parse_mode="Markdown"
#         )
#
#     await callback.answer()
#
#
# @router.callback_query(F.data.startswith("launch_model_"))
# async def launch_model_from_search(callback: CallbackQuery, state: FSMContext):
#     """Запускает чат с выбранной моделью"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#     model_id = callback.data.replace("launch_model_", "")
#     model = next((m for m in AI_MODELS_DB if m["id"] == model_id), None)
#
#     if model:
#         if model_id in ["mistral", "qwen", "nemotron"]:
#             await state.set_state(AIChatState.waiting_for_message)
#             await state.update_data(current_model=model_id)
#             await callback.message.edit_text(
#                 f"{model['name']} " + get_text(user_lang, 'ai_activated'),
#                 reply_markup=get_exit_ai_inline(user_lang),
#                 parse_mode="Markdown"
#             )
#         else:
#             await callback.message.edit_text(
#                 f"🚧 **{model['name']}**\n\n"
#                 f"Эта модель скоро будет доступна!\n"
#                 f"Попробуйте Mistral AI или Qwen AI для тестирования.\n\n"
#                 f"{model['description']}",
#                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                     [InlineKeyboardButton(text=get_text(user_lang, 'back_to_search'), callback_data="menu_search")],
#                     [InlineKeyboardButton(text=get_text(user_lang, 'back_to_menu'), callback_data="back_main_menu")],
#                 ]),
#                 parse_mode="Markdown"
#             )
#     else:
#         await callback.message.edit_text(
#             "❌ **Ошибка запуска модели**",
#             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                 [InlineKeyboardButton(text=get_text(user_lang, 'back_to_search'), callback_data="menu_search")],
#             ]),
#             parse_mode="Markdown"
#         )
#
#     await callback.answer()
#
#
# # ==============================================================================
# # 9. ЗАПУСК МОДЕЛЕЙ (MISTRAL + QWEN)
# # ==============================================================================
# @router.callback_query(F.data == "ai_model_mistral")
# async def start_mistral_chat(callback: CallbackQuery, state: FSMContext):
#     """Активирует режим диалога с Mistral"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await state.set_state(AIChatState.waiting_for_message)
#     await state.update_data(current_model="mistral")
#     await callback.message.edit_text(
#         "Mistral AI " + get_text(user_lang, 'ai_activated'),
#         reply_markup=get_exit_ai_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == "ai_model_qwen")
# async def start_qwen_chat(callback: CallbackQuery, state: FSMContext):
#     """Активирует режим диалога с Qwen"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await state.set_state(AIChatState.waiting_for_message)
#     await state.update_data(current_model="qwen")
#     await callback.message.edit_text(
#         "Qwen AI " + get_text(user_lang, 'ai_activated'),
#         reply_markup=get_exit_ai_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == "ai_model_nemotron")
# async def start_nemotron_chat(callback: CallbackQuery, state: FSMContext):
#     """Активирует режим диалога с Nemotron"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await state.set_state(AIChatState.waiting_for_message)
#     await state.update_data(current_model="nemotron")
#     await callback.message.edit_text(
#         "Nemotron AI " + get_text(user_lang, 'ai_activated'),
#         reply_markup=get_exit_ai_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == "exit_ai_chat")
# async def exit_ai_chat(callback: CallbackQuery, state: FSMContext):
#     """Выход из режима диалога"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await state.clear()
#     await callback.message.edit_text(
#         get_text(user_lang, 'session_ended'),
#         reply_markup=get_main_menu_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # ==============================================================================
# # 10. ОБРАБОТКА СООБЩЕНИЙ ДЛЯ ИИ (FSM)
# # ==============================================================================
# @router.message(AIChatState.waiting_for_message)
# async def handle_ai_message(message: Message, state: FSMContext):
#     """Обрабатывает текст пользователя и отправляет в AI"""
#     user_text = message.text
#     user_id = message.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     # Получаем текущую модель из состояния
#     state_data = await state.get_data()
#     current_model = state_data.get("current_model", "mistral")
#
#     thinking_msg = await message.answer(
#         get_text(user_lang, 'thinking'),
#         parse_mode="Markdown"
#     )
#
#     try:
#         bot_response = ""
#         model_name = ""
#
#         # ✅ MISTRAL AI
#         if current_model == "mistral":
#             model_name = "mistral-small"
#             if MISTRAL_API_KEY:
#                 async with aiohttp.ClientSession() as session:
#                     headers = {
#                         "Authorization": f"Bearer {MISTRAL_API_KEY}",
#                         "Content-Type": "application/json"
#                     }
#                     payload = {
#                         "model": "mistral-small",
#                         "messages": [{"role": "user", "content": user_text}]
#                     }
#                     async with session.post(MISTRAL_API_URL, json=payload, headers=headers) as resp:
#                         if resp.status == 200:
#                             data = await resp.json()
#                             bot_response = data['choices'][0]['message']['content']
#                         else:
#                             error_text = await resp.text()
#                             bot_response = f"⚠️ Ошибка API Mistral: {resp.status}"
#                             print(f"❌ Mistral Error: {error_text}")
#             else:
#                 await asyncio.sleep(1)
#                 bot_response = f"(Демо-режим Mistral) Вы написали: '{user_text}'"
#
#         # ✅ QWEN AI через OPENROUTER
#         elif current_model == "qwen":
#             model_name = "qwen/qwen-2.5-7b-instruct"
#             if QWEN_API_KEY:
#                 async with aiohttp.ClientSession() as session:
#                     headers = {
#                         "Authorization": f"Bearer {QWEN_API_KEY}",
#                         "Content-Type": "application/json",
#                         "HTTP-Referer": "https://your-bot.com",
#                         "X-Title": "AI Hub Bot"
#                     }
#                     payload = {
#                         "model": "qwen/qwen-2.5-7b-instruct",
#                         "messages": [{"role": "user", "content": user_text}]
#                     }
#                     async with session.post(QWEN_API_URL, json=payload, headers=headers) as resp:
#                         if resp.status == 200:
#                             data = await resp.json()
#                             try:
#                                 bot_response = data['choices'][0]['message']['content']
#                             except KeyError as e:
#                                 print(f"❌ KeyError: {e}")
#                                 print(f"📦 Data keys: {data.keys()}")
#                                 bot_response = f"⚠️ Ошибка формата ответа: {str(e)}"
#                         else:
#                             error_text = await resp.text()
#                             bot_response = f"⚠️ Ошибка API Qwen: {resp.status}\n{error_text}"
#                             print(f"❌ Qwen Error: {error_text}")
#             else:
#                 await asyncio.sleep(1)
#                 bot_response = f"(Демо-режим Qwen) Вы написали: '{user_text}'\nДобавьте OPENROUTER_API_KEY в .env"
#
#
#         # ✅ NEMOTRON AI через OPENROUTER
#         elif current_model == "nemotron":
#             model_name = "nvidia/nemotron-3-super-120b-a12b:free"
#             if QWEN_API_KEY:  # ✅ Используем тот же ключ OpenRouter
#                 async with aiohttp.ClientSession() as session:
#                     headers = {
#                         "Authorization": f"Bearer {QWEN_API_KEY}",
#                         "Content-Type": "application/json",
#                         "HTTP-Referer": "https://your-bot.com",
#                         "X-Title": "AI Hub Bot"
#                     }
#                     payload = {
#                         "model": "nvidia/nemotron-3-super-120b-a12b:free",  # ✅ Модель Nemotron
#                         "messages": [{"role": "user", "content": user_text}]
#                     }
#                     async with session.post(QWEN_API_URL, json=payload, headers=headers) as resp:
#                         if resp.status == 200:
#                             data = await resp.json()
#                             try:
#                                 bot_response = data['choices'][0]['message']['content']
#                             except KeyError as e:
#                                 print(f"❌ KeyError: {e}")
#                                 print(f"📦 Data keys: {data.keys()}")
#                                 bot_response = f"⚠️ Ошибка формата ответа: {str(e)}"
#                         else:
#                             error_text = await resp.text()
#                             bot_response = f"⚠️ Ошибка API Nemotron: {resp.status}\n{error_text}"
#                             print(f"❌ Nemotron Error: {error_text}")
#             else:
#                 await asyncio.sleep(1)
#                 bot_response = f"(Демо-режим Nemotron) Вы написали: '{user_text}'\nДобавьте OPENROUTER_API_KEY в .env"
#
#         await thinking_msg.delete()
#
#         # Определяем эмодзи модели для ответа
#         model_emoji = "🌪️" if current_model == "mistral" else "🤖"
#
#         await message.answer(
#             f"{model_emoji} **{current_model.capitalize()}:**\n\n{escape(bot_response)}",
#             parse_mode="Markdown",
#             reply_markup=get_exit_ai_inline(user_lang)
#         )
#
#         await save_ai_message(user_id, model_name, user_text, bot_response)
#
#     except Exception as e:
#         await thinking_msg.delete()
#         print(f"❌ Критическая ошибка: {e}")
#         await message.answer(f"❌ Произошла ошибка: {str(e)}", reply_markup=get_exit_ai_inline(user_lang))
#
#
# # ==============================================================================
# # 11. ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# # ==============================================================================
# @router.callback_query(F.data == "menu_profile")
# async def show_profile(callback: CallbackQuery):
#     """Показывает статистику пользователя"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#     stats = await get_user_profile_stats(user_id)
#
#     streak_emoji = "🔥" if stats['streak'] > 0 else "💤"
#     premium_badge = "💎 Premium" if stats['is_premium'] else "🆓 Free"
#
#     text = get_text(
#         user_lang, 'profile',
#         user_id=user_id,
#         premium_badge=premium_badge,
#         coins=stats['coins'],
#         streak_emoji=streak_emoji,
#         streak=stats['streak'],
#         days=stats['days_in_bot']
#     )
#
#     await callback.message.edit_text(
#         text,
#         reply_markup=get_profile_menu_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # ==============================================================================
# # 12. НАСТРОЙКИ ЯЗЫКА
# # ==============================================================================
# @router.callback_query(F.data == "menu_language")
# async def show_language_menu(callback: CallbackQuery):
#     """Показывает меню выбора языка"""
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await callback.message.edit_text(
#         get_text(user_lang, 'language_menu'),
#         reply_markup=get_language_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data.startswith("lang_"))
# async def change_language(callback: CallbackQuery):
#     """Изменяет язык пользователя"""
#     user_id = callback.from_user.id
#     new_lang = callback.data.replace("lang_", "")
#
#     if new_lang in ['ru', 'en', 'tt']:
#         await set_user_language(user_id, new_lang)
#
#         await callback.message.edit_text(
#             get_text(new_lang, 'language_changed', lang=LANGUAGES[new_lang]),
#             reply_markup=get_main_menu_inline(new_lang),
#             parse_mode="Markdown"
#         )
#
#     await callback.answer()
#
#
# # ==============================================================================
# # 13. ЗАГЛУШКИ ДЛЯ ОСТАЛЬНЫХ РАЗДЕЛОВ
# # ==============================================================================
# @router.callback_query(F.data == "menu_tariffs")
# async def show_tariffs_stub(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await callback.message.edit_text(
#         get_text(user_lang, 'tariffs', current='free'),
#         reply_markup=get_main_menu_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == "menu_missions")
# async def show_missions_stub(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await callback.message.edit_text(
#         get_text(user_lang, 'missions_stub'),
#         reply_markup=get_main_menu_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == "menu_games")
# async def show_games_stub(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await callback.message.edit_text(
#         get_text(user_lang, 'games_stub'),
#         reply_markup=get_main_menu_inline(user_lang),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # ==============================================================================
# # 14. ОТМЕНА ПОИСКА (COMMAND /cancel)
# # ==============================================================================
# @router.message(Command("cancel"))
# async def cancel_search(message: Message, state: FSMContext):
#     """Отменяет текущее состояние (поиск, чат с ИИ)"""
#     user_id = message.from_user.id
#     user_lang = await get_user_language(user_id)
#
#     await state.clear()
#     await message.answer(
#         get_text(user_lang, 'cancel'),
#         reply_markup=get_main_menu_inline(user_lang),
#         parse_mode="Markdown"
#     )
#
#
# # ==============================================================================
# # 15. ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ
# # ==============================================================================
# @router.message(Command("news"))
# async def news(message: Message):
#     await message.answer("📰 Новости сервиса")
#
#
# @router.message(Command("stickers"))
# async def stickers(message: Message):
#     await message.answer("https://t.me/addstickers/Souz4_by_fStikBot")
#
#
# @router.message(Command("report"))
# async def report(message: Message):
#     await message.answer("📝 Сообщите об ошибке:")
#
#
# @router.message(Command("ai"))
# async def ai_leaderboard(message: Message):
#     await message.answer("🏆 Лидеры ИИ: https://arena.ai/leaderboard")
#
#
# @router.message(Command("sub"))
# async def sub_info(message: Message):
#     user_id = message.from_user.id
#     user_lang = await get_user_language(user_id)
#     await message.answer(get_text(user_lang, 'tariffs', current='free'), parse_mode="Markdown")
#
#
# @router.message(F.text.lower() == "привет")
# async def cmd_hello(message: Message):
#     user_id = message.from_user.id
#     full_name = message.from_user.full_name
#     user_lang = await get_user_language(user_id)
#
#     await add_or_update_user(
#         user_id=user_id,
#         username=message.from_user.username or "",
#         first_name=message.from_user.first_name or "",
#         last_name=message.from_user.last_name or ""
#     )
#
#     await message.answer(
#         get_text(user_lang, 'welcome', name=escape(full_name)),
#         parse_mode="Markdown",
#         reply_markup=get_main_menu_inline(user_lang)
#     )
# @router.message(Command("site"))
# async def site(message: Message):
#    await message.answer("наш сайт:")
#
#
# @router.message(Command("about"))
# async def about(message: Message):
#    await message.answer("Копилка промптов - это (@prompts_souz_bot) ии агрегатор для тестирования промптов.\n\n"
#                         "Основан в 2026 году.\n\n"
#                         "Страна: Российская Федерация (Регион: Республика Татарстан)\n\n"
#                         "Миссия Копилка промптов (КП) состоит в  продвижении информации по промпт инженерии.\n"
#                         "Копилка промптов стремится придерживаться самых высоких стандартов в подаче материалов.\n\n"
#                         "Команда (КП): Гимадеев Дамир(@Souzn1k3)."
#                         "и студент КФУ(ИТИС).\n Лебедев Глеб(@tfmot).\n\n ПО ВСЕМ ВОПРОСАМ (@Souzn1k3)!")


import asyncio
import aiohttp

from datetime import datetime, timezone
from html import escape
import json
import re
import secrets
import subprocess
import wave

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot_plans import (
    PAID_PLAN_ORDER,
    SUBSCRIPTION_PERIOD_SECONDS,
    build_subscription_payload,
    format_expiry,
    get_plan_badge,
    get_plan_config,
    get_plan_title,
    has_same_or_higher_plan,
    normalize_plan_tier,
    parse_subscription_payload,
)
from database import (
    add_or_update_user,
    count_ai_messages_today,
    get_user_plan,
    get_user_profile_stats,
    get_user_notification_settings,
    update_notification_setting,
    get_all_active_users,
    save_ai_message,
    get_user_language,
    set_user_language,

    # Новое: миссии / экономика / стрик
    get_user_missions,
    get_user_economy,
    ensure_daily_missions,
    ensure_permanent_missions,
    track_ai_message_sent,
    track_profile_open,
    track_search_used,
    track_streak_claim,
    track_buy_freeze,
    claim_daily_streak,
    buy_freeze,
    get_top_users_by_coins,
    get_user_rank_by_coins,
    get_top_users_by_streak,
    get_user_rank_by_streak,
    get_top_best_users,
    get_user_rank_best,
    grant_game_reward,
    update_user_plan,
    update_user_coins,
)

from languages import get_text, LANGUAGES
from website_api import (
    activate_stars_subscription as website_activate_stars_subscription,
    get_moderation_prompt as website_get_moderation_prompt,
    get_moderation_queue as website_get_moderation_queue,
    get_subscription_status as website_get_subscription_status,
    moderate_prompt as website_moderate_prompt,
    upsert_user as website_upsert_user,
)
import os
import aiofiles


def _parse_admin_telegram_ids() -> tuple[int, ...]:
    values: list[int] = []
    primary = (os.getenv("ADMIN_TELEGRAM_ID", "1755580726") or "").strip()
    if primary:
        try:
            values.append(int(primary))
        except ValueError:
            pass

    raw = (os.getenv("ADMIN_TELEGRAM_IDS", "") or "").strip()
    if raw:
        for token in raw.split(","):
            candidate = token.strip()
            if not candidate:
                continue
            try:
                values.append(int(candidate))
            except ValueError:
                continue

    deduped: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        deduped.append(value)

    if not deduped:
        deduped.append(1755580726)
    return tuple(deduped)


ADMIN_TELEGRAM_IDS = _parse_admin_telegram_ids()
ADMIN_TELEGRAM_ID = ADMIN_TELEGRAM_IDS[0]


router = Router()

# ==============================================================================
# 1. КОНФИГУРАЦИЯ API
# ==============================================================================

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

QWEN_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
QWEN_API_URL = "https://openrouter.ai/api/v1/chat/completions"

VOSK_MODEL_PATH = os.getenv(
    "VOSK_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "models", "vosk-model-small-ru-0.22"),
)
_vosk_model = None


# ==============================================================================
# 2. СОСТОЯНИЯ FSM
# ==============================================================================

class AIChatState(StatesGroup):
    waiting_for_message = State()
    current_model = State()


class SearchState(StatesGroup):
    waiting_for_query = State()

class GamesState(StatesGroup):
    in_ai_quiz = State()
    in_prompt_puzzle = State()

class PromptReviewState(StatesGroup):
    waiting_for_prompt = State()


class ModerationCommentState(StatesGroup):
    waiting_for_comment = State()


# ==============================================================================
# 3. БАЗА МОДЕЛЕЙ
# ==============================================================================

AI_MODELS_DB = [
    {"id": "mistral", "name": "Mistral AI 🇫🇷", "description": "Быстрая и эффективная модель от Mistral"},
    {"id": "qwen", "name": "Qwen AI 🇨🇳", "description": "Умная модель от Alibaba с глубоким пониманием контекста"},
    {"id": "zai", "name": "Z AI 🇨🇳", "description": "Легкая модель GLM от Z.ai через OpenRouter для быстрых диалогов и повседневных задач"},
    {"id": "nemotron", "name": "NVIDIA Nemotron 3 Super 🇺🇸", "description": "Гибридная модель от NVIDIA для сложных задач, программирования и анализа"},
    {"id": "gemini", "name": "Gemini Pro 🇺🇸", "description": "Мультимодальная модель от Google"},
    {"id": "gptoss", "name": "OpenAI gpt-oss-120b 🇺🇸", "description": "Сильная open-weight модель для логики, кода и сложных рассуждений"},
    {"id": "claude", "name": "Claude 3 🇺🇸", "description": "Безопасная и мощная модель от Anthropic"},
    {"id": "llama", "name": "Llama 3 🇺🇸", "description": "Открытая модель от Meta"},
]

AI_QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": {
            "ru": "Какой промпт лучше для получения структурированного ответа от ИИ?",
            "en": "Which prompt is better for getting a structured AI response?",
            "tt": "ИИдан структуралы җавап алу өчен кайсы промпт яхшырак?"
        },
        "option_a": {
            "ru": "Напиши что-нибудь про бизнес",
            "en": "Write something about business",
            "tt": "Бизнес турында нәрсә дә булса яз"
        },
        "option_b": {
            "ru": "Составь бизнес-план для Telegram-бота. Формат: 1) идея 2) ЦА 3) монетизация 4) риски",
            "en": "Create a business plan for a Telegram bot. Format: 1) idea 2) target audience 3) monetization 4) risks",
            "tt": "Telegram-бот өчен бизнес-план төзе. Формат: 1) идея 2) аудитория 3) монетизация 4) куркынычлар"
        },
        "correct": "b",
        "reward": 5,
        "explanation": {
            "ru": "Правильный ответ: B. Хороший промпт задаёт задачу, контекст и формат ответа.",
            "en": "Correct answer: B. A strong prompt gives the task, context, and response format.",
            "tt": "Дөрес җавап: B. Яхшы промпт бурычны, контекстны һәм җавап форматын бирә."
        }
    },
    {
        "id": 2,
        "question": {
            "ru": "Какой промпт лучше для полезного ответа по Python?",
            "en": "Which prompt is better for a useful Python answer?",
            "tt": "Python буенча файдалы җавап алу өчен кайсы промпт яхшырак?"
        },
        "option_a": {
            "ru": "Объясни Python",
            "en": "Explain Python",
            "tt": "Python-ны аңлат"
        },
        "option_b": {
            "ru": "Объясни циклы for в Python простыми словами и покажи 3 коротких примера для новичка",
            "en": "Explain Python for-loops in simple words and show 3 short examples for a beginner",
            "tt": "Python-дагы for циклларын гади итеп аңлат һәм башлаучы өчен 3 кыска мисал күрсәт"
        },
        "correct": "b",
        "reward": 5,
        "explanation": {
            "ru": "Правильный ответ: B. Чем конкретнее запрос, тем выше шанс получить полезный результат.",
            "en": "Correct answer: B. The more specific the prompt, the more useful the result.",
            "tt": "Дөрес җавап: B. Промпт никадәр төгәлрәк булса, нәтиҗә шулкадәр файдалырак була."
        }
    }
]

PROMPT_PUZZLES = [
    {
        "id": 1,
        "reward": 6,
        "pieces": {
            "ru": ["[expert]", "[marketing]", "[act as]"],
            "en": ["[expert]", "[marketing]", "[act as]"],
            "tt": ["[expert]", "[marketing]", "[act as]"],
        },
        "correct_order": [2, 0, 1],
        "explanation": {
            "ru": "Правильная сборка: [act as] → [expert] → [marketing]. Сначала роль, потом уровень, потом тема.",
            "en": "Correct order: [act as] → [expert] → [marketing]. First role, then level, then topic.",
            "tt": "Дөрес тәртип: [act as] → [expert] → [marketing]. Башта роль, аннары дәрәҗә, аннары тема."
        }
    },
    {
        "id": 2,
        "reward": 6,
        "pieces": {
            "ru": ["[for beginner]", "[explain Python loops]", "[with 3 examples]"],
            "en": ["[for beginner]", "[explain Python loops]", "[with 3 examples]"],
            "tt": ["[for beginner]", "[explain Python loops]", "[with 3 examples]"],
        },
        "correct_order": [1, 0, 2],
        "explanation": {
            "ru": "Правильная сборка: [explain Python loops] → [for beginner] → [with 3 examples]. Сначала задача, потом аудитория, потом формат.",
            "en": "Correct order: [explain Python loops] → [for beginner] → [with 3 examples]. First task, then audience, then format.",
            "tt": "Дөрес тәртип: [explain Python loops] → [for beginner] → [with 3 examples]. Башта бурыч, аннары аудитория, аннары формат."
        }
    }
]
# ==============================================================================
# 4. ЛОКАЛЬНЫЕ ТЕКСТЫ ДЛЯ МИССИЙ / СТРИКА
#    (чтобы не ломать languages.py и не требовать ручных изменений)
# ==============================================================================

LOCAL_TEXTS = {
    "ru": {
        "missions_title": "🎯 **Миссии**",
        "daily_missions": "**Ежедневные миссии:**",
        "permanent_missions": "**Постоянные миссии:**",
        "no_missions": "Нет миссий",
        "streak_title": "🔥 **Ударный режим**",
        "streak_desc": (
            "Нажимай кнопку каждый день, чтобы продлевать ударный режим.\n"
            "Если пропустишь день, заморозка сохранит серию."
        ),
        "economy_line": "🪙 Токены: **{coins}**\n🔥 Стрик: **{streak}**\n🧊 Заморозки: **{freeze_count}**",
        "claim_streak_btn": "🔥 Продлить ударный режим",
        "buy_freeze_btn": "🧊 Купить заморозку (30)",
        "streak_btn": "🔥 Стрик",
        "missions_btn_new": "🎯 Миссии 🎯",
        "streak_claimed": (
            "🔥 **Ударный режим продлён!**\n\n"
            "Текущий стрик: **{streak}**\n"
            "Награда: **+{reward}** токенов\n"
            "🧊 Заморозок осталось: **{freeze_count}**"
        ),
        "freeze_used": "\n\n🧊 Заморозка была использована автоматически.",
        "back_to_profile": "👤 Назад в профиль",
        "mission_done_alert": "✅ Прогресс обновлён",
        "freeze_bought_alert": "🧊 Заморозка куплена!",
        "menu_profile_extra": "\n\n🧊 Заморозки: **{freeze_count}**",
        "all_daily_completed_bonus": "🎁 Бонус за все миссии дня уже учтён в токенах.",
        "leaderboard_btn": "🏆 Лидерборд",
        "leaderboard_title": "🏆 **Лидерборд**",
        "leaderboard_best_btn": "👑 Лучшие игроки",
        "leaderboard_coins_btn": "🪙 Топ по токенам",
        "leaderboard_streak_btn": "🔥 Топ по стрику",
        "leaderboard_best_title": "👑 **Лучшие игроки**",
        "leaderboard_coins_title": "🪙 **Топ по токенам**",
        "leaderboard_streak_title": "🔥 **Топ по стрику**",
        "your_place": "📍 Ваше место: **{rank}**",
        "your_coins": "🪙 Ваш баланс: **{value}**",
        "your_streak": "🔥 Ваш стрик: **{value}**",
        "your_score": "⭐ Ваш рейтинг: **{value}**",
        "games_menu_title": "🎮 **Каталог игр**\n\nВыберите игру:",
        "ai_quiz_btn": "🧠 AI-квиз",
        "ai_quiz_title": "🧠 **AI-квиз**\n\nВыбери лучший промпт.",
        "quiz_option_a": "A",
        "quiz_option_b": "B",
        "quiz_correct": "✅ Верно! Вы получили **+{reward}** токенов.\n\n{explanation}",
        "quiz_wrong": "❌ Неверно.\n\n{explanation}",
        "next_question_btn": "➡️ Следующий вопрос",
        "back_to_games_btn": "🎮 К играм",
        "prompt_puzzle_btn": "🧩 Собери промпт",
        "prompt_puzzle_title": "🧩 **Собери промпт**\n\nНажимай части в правильном порядке.",
        "prompt_puzzle_current": "Текущая сборка:",
        "prompt_puzzle_empty": "пока пусто",
        "prompt_puzzle_ready_btn": "✅ Проверить",
        "prompt_puzzle_reset_btn": "♻️ Сбросить",
        "prompt_puzzle_correct": "✅ Правильно! Вы получили **+{reward}** токенов.\n\n{explanation}",
        "prompt_puzzle_wrong": "❌ Пока неправильно.\n\n{explanation}",
        "next_puzzle_btn": "➡️ Следующий пазл",
        "prompt_review_start": "📝 Пришлите ваш промпт одним сообщением.",
        "prompt_review_sent": "✅ Ваш промпт отправлен на редакцию.",
        "prompt_review_empty": "❌ Пожалуйста, отправьте текстовый промпт.",
    },
    "en": {
        "missions_title": "🎯 **Missions**",
        "daily_missions": "**Daily missions:**",
        "permanent_missions": "**Permanent missions:**",
        "no_missions": "No missions",
        "streak_title": "🔥 **Streak**",
        "streak_desc": (
            "Press the button every day to extend your streak.\n"
            "If you miss a day, a freeze will save it."
        ),
        "economy_line": "🪙 Tokens: **{coins}**\n🔥 Streak: **{streak}**\n🧊 Freezes: **{freeze_count}**",
        "claim_streak_btn": "🔥 Extend streak",
        "buy_freeze_btn": "🧊 Buy freeze (30)",
        "streak_btn": "🔥 Streak",
        "missions_btn_new": "🎯 Missions 🎯",
        "streak_claimed": (
            "🔥 **Streak extended!**\n\n"
            "Current streak: **{streak}**\n"
            "Reward: **+{reward}** tokens\n"
            "🧊 Freezes left: **{freeze_count}**"
        ),
        "freeze_used": "\n\n🧊 A freeze was used automatically.",
        "back_to_profile": "👤 Back to profile",
        "mission_done_alert": "✅ Progress updated",
        "freeze_bought_alert": "🧊 Freeze purchased!",
        "menu_profile_extra": "\n\n🧊 Freezes: **{freeze_count}**",
        "all_daily_completed_bonus": "🎁 Bonus for all daily missions is already included.",
        "leaderboard_btn": "🏆 Leaderboard",
        "leaderboard_title": "🏆 **Leaderboard**",
        "leaderboard_best_btn": "👑 Best players",
        "leaderboard_coins_btn": "🪙 Top by tokens",
        "leaderboard_streak_btn": "🔥 Top by streak",
        "leaderboard_best_title": "👑 **Best players**",
        "leaderboard_coins_title": "🪙 **Top by tokens**",
        "leaderboard_streak_title": "🔥 **Top by streak**",
        "your_place": "📍 Your place: **{rank}**",
        "your_coins": "🪙 Your balance: **{value}**",
        "your_streak": "🔥 Your streak: **{value}**",
        "your_score": "⭐ Your rating: **{value}**",
        "games_menu_title": "🎮 **Games Catalog**\n\nChoose a game:",
        "ai_quiz_btn": "🧠 AI Quiz",
        "ai_quiz_title": "🧠 **AI Quiz**\n\nChoose the better prompt.",
        "quiz_option_a": "A",
        "quiz_option_b": "B",
        "quiz_correct": "✅ Correct! You earned **+{reward}** tokens.\n\n{explanation}",
        "quiz_wrong": "❌ Wrong.\n\n{explanation}",
        "next_question_btn": "➡️ Next question",
        "back_to_games_btn": "🎮 Back to games",
        "prompt_puzzle_btn": "🧩 Build prompt",
        "prompt_puzzle_title": "🧩 **Build the prompt**\n\nTap the parts in the correct order.",
        "prompt_puzzle_current": "Current build:",
        "prompt_puzzle_empty": "empty",
        "prompt_puzzle_ready_btn": "✅ Check",
        "prompt_puzzle_reset_btn": "♻️ Reset",
        "prompt_puzzle_correct": "✅ Correct! You earned **+{reward}** tokens.\n\n{explanation}",
        "prompt_puzzle_wrong": "❌ Not correct yet.\n\n{explanation}",
        "next_puzzle_btn": "➡️ Next puzzle",
        "prompt_review_start": "📝 Send your prompt in one message.",
        "prompt_review_sent": "✅ Your prompt has been sent for review.",
        "prompt_review_empty": "❌ Please send a text prompt.",
    },
    "tt": {
        "missions_title": "🎯 **Миссияләр**",
        "daily_missions": "**Көндәлек миссияләр:**",
        "permanent_missions": "**Даими миссияләр:**",
        "no_missions": "Миссияләр юк",
        "streak_title": "🔥 **Удар режимы**",
        "streak_desc": (
            "Удар режимын дәвам итү өчен көн саен төймәгә бас.\n"
            "Бер көнне калдырсаң, заморозка серияне саклап калачак."
        ),
        "economy_line": "🪙 Токеннар: **{coins}**\n🔥 Стрик: **{streak}**\n🧊 Заморозкалар: **{freeze_count}**",
        "claim_streak_btn": "🔥 Удар режимын дәвам итү",
        "buy_freeze_btn": "🧊 Заморозка алу (30)",
        "streak_btn": "🔥 Стрик",
        "missions_btn_new": "🎯 Миссияләр 🎯",
        "streak_claimed": (
            "🔥 **Удар режимы дәвам ителде!**\n\n"
            "Хәзерге стрик: **{streak}**\n"
            "Бүләк: **+{reward}** токен\n"
            "🧊 Калган заморозкалар: **{freeze_count}**"
        ),

        "leaderboard_btn": "🏆 Лидерборд",
        "leaderboard_title": "🏆 **Лидерборд**",
        "leaderboard_best_btn": "👑 **Иң яхшы уенчылар**",
        "leaderboard_coins_btn": "🪙 **Топ токеннар буенча**",
        "leaderboard_streak_btn": "🔥 **Топ стрик буенча**",
        "leaderboard_best_title": "👑 **Иң яхшы уенчылар**",
        "leaderboard_coins_title": "🪙 **Топ токеннар буенча**",
        "leaderboard_streak_title": "🔥 **Топ стрик буенча**",
        "your_place": "📍 Сезнең урын: **{rank}**",
        "your_coins": "🪙 Сезнең баланс: **{value}**",
        "your_streak": "🔥 Сезнең стрик: **{value}**",
        "your_score": "⭐️ Сезнең рейтинг: **{value}**",
        "games_menu_title": "🎮 **Уеннар каталоги**\n\nУен сайлагыз:",
        "ai_quiz_btn": "🧠 AI-квиз",
        "ai_quiz_title": "🧠 **AI-квиз**\n\nИң яхшы промптны сайла.",
        "quiz_option_a": "A",
        "quiz_option_b": "B",
        "quiz_correct": "✅ Дөрес! Сез **+{reward}** токен алдыгыз.\n\n{explanation}",
        "quiz_wrong": "❌ Дөрес түгел.\n\n{explanation}",
        "next_question_btn": "➡️ Киләсе сорау",
        "back_to_games_btn": "🎮 Уеннарга",
        "prompt_puzzle_btn": "🧩 Промпт җый",
        "prompt_puzzle_title": "🧩 **Промпт җый**\n\nӨлешләргә дөрес тәртиптә бас.",
        "prompt_puzzle_current": "Хәзерге җыю:",
        "prompt_puzzle_empty": "әлегә буш",
        "prompt_puzzle_ready_btn": "✅ Тикшерү",
        "prompt_puzzle_reset_btn": "♻️ Яңадан",
        "prompt_puzzle_correct": "✅ Дөрес! Сез **+{reward}** токен алдыгыз.\n\n{explanation}",
        "prompt_puzzle_wrong": "❌ Әлегә дөрес түгел.\n\n{explanation}",
        "next_puzzle_btn": "➡️ Киләсе пазл",
        "prompt_review_start": "📝 Промптыгызны бер хәбәр белән җибәрегез.",
        "prompt_review_sent": "✅ Сезнең промпт редакциягә җибәрелде.",
        "prompt_review_empty": "❌ Зинһар, текстлы промпт җибәрегез.",

}

}


def lt(lang: str, key: str, **kwargs) -> str:
    data = LOCAL_TEXTS.get(lang, LOCAL_TEXTS["ru"])
    text = data.get(key, LOCAL_TEXTS["ru"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text


SUBSCRIPTION_TEXTS = {
    "ru": {
        "title": "💎 **Подписка**",
        "current_plan": "Ваш тариф",
        "renews_until": "Активна до",
        "shared_sync": "Подписка действует и на сайте, и в Telegram-боте. После оплаты доступ и все преимущества синхронизируются автоматически.",
        "price": "Цена",
        "choose": "Выберите тариф для оформления подписки через Telegram Stars:",
        "ai_daily_limit": "AI-диалоги в день",
        "freeze_limit": "Лимит заморозок",
        "game_bonus": "Бонус в играх",
        "premium_prompts": "Premium-промпты",
        "restricted_categories": "Restricted-категории",
        "yes": "Да",
        "no": "Нет",
        "unlimited": "без лимита",
        "included": "уже входит",
        "active": "текущий",
        "pay": "Оплатить {stars} ⭐️",
        "checkout_ready": "Ссылка на оплату готова. После успешного платежа подписка автоматически синхронизируется с сайтом.",
        "payment_success": "✅ Подписка активирована: {badge} **{plan}**",
        "payment_success_expires": "✅ Подписка активирована: {badge} **{plan}**\nАктивна до: **{expires}**",
        "payment_failed_sync": "⚠️ Оплата прошла, но сайт не подтвердил синхронизацию. Я уже отправил уведомление админу.",
        "same_or_higher": "У вас уже этот тариф или выше.",
        "limit_reached": "⛔ Дневной лимит AI-диалогов исчерпан: **{used}/{limit}**.",
        "limit_hint": "Перейдите на более высокий тариф в разделе «Тарифы», чтобы увеличить лимит.",
        "limit_status": "Лимит сегодня: **{used}/{limit}**",
        "limit_status_unlimited": "Лимит сегодня: **без ограничений**",
        "game_bonus_line": "🎁 Бонус подписки: **+{bonus}** токенов ({pct}%)",
        "profile_plan": "\n\n💎 План: {badge} **{plan}**",
        "profile_expires": "\n⏳ Активна до: **{expires}**",
        "profile_ai_limit": "\n🤖 AI в день: **{limit}**",
        "profile_game_bonus": "\n🎮 Бонус игр: **+{bonus}%**",
        "streak_limit": "\n📦 Лимит заморозок по плану: **{limit}**",
        "noop_included": "Этот уровень уже входит в ваш доступ.",
    },
    "en": {
        "title": "💎 **Shared Subscription**",
        "current_plan": "Current plan",
        "renews_until": "Active until",
        "shared_sync": "The same subscription works on both the website and the Telegram bot.",
        "price": "Price",
        "choose": "Choose a plan to purchase with Telegram Stars:",
        "ai_daily_limit": "AI chats per day",
        "freeze_limit": "Freeze limit",
        "game_bonus": "Game bonus",
        "premium_prompts": "Premium prompts",
        "restricted_categories": "Restricted categories",
        "yes": "Yes",
        "no": "No",
        "unlimited": "unlimited",
        "included": "already included",
        "active": "current",
        "pay": "Pay {stars} ⭐️",
        "checkout_ready": "Your payment link is ready. After a successful payment, the subscription will sync with the website automatically.",
        "payment_success": "✅ Subscription activated: {badge} **{plan}**",
        "payment_success_expires": "✅ Subscription activated: {badge} **{plan}**\nActive until: **{expires}**",
        "payment_failed_sync": "⚠️ Payment succeeded, but the website did not confirm the sync yet. I have already notified the admin.",
        "same_or_higher": "You already have this plan or a higher one.",
        "limit_reached": "⛔ Your daily AI limit is used up: **{used}/{limit}**.",
        "limit_hint": "Open the Plans section to upgrade and increase the limit.",
        "limit_status": "Today: **{used}/{limit}**",
        "limit_status_unlimited": "Today: **unlimited**",
        "game_bonus_line": "🎁 Subscription bonus: **+{bonus}** tokens ({pct}%)",
        "profile_plan": "\n\n💎 Plan: {badge} **{plan}**",
        "profile_expires": "\n⏳ Active until: **{expires}**",
        "profile_ai_limit": "\n🤖 AI per day: **{limit}**",
        "profile_game_bonus": "\n🎮 Game bonus: **+{bonus}%**",
        "streak_limit": "\n📦 Freeze limit by plan: **{limit}**",
        "noop_included": "This level is already included in your access.",
    },
    "tt": {
        "title": "💎 **Уртак язылу**",
        "current_plan": "Хәзерге план",
        "renews_until": "Актив вакыты",
        "shared_sync": "Бер үк язылу сайтта да, Telegram-ботта да эшли.",
        "price": "Бәя",
        "choose": "Telegram Stars аша сатып алу өчен план сайлагыз:",
        "ai_daily_limit": "Көненә AI-диалоглар",
        "freeze_limit": "Туңдыру лимиты",
        "game_bonus": "Уен бонусы",
        "premium_prompts": "Premium-промптлар",
        "restricted_categories": "Restricted-категорияләр",
        "yes": "Әйе",
        "no": "Юк",
        "unlimited": "чиксез",
        "included": "инде кергән",
        "active": "хәзерге",
        "pay": "{stars} ⭐️ түләү",
        "checkout_ready": "Түләү сылтамасы әзер. Уңышлы түләүдән соң язылу сайт белән автоматик синхронлашачак.",
        "payment_success": "✅ Язылу активлаштырылды: {badge} **{plan}**",
        "payment_success_expires": "✅ Язылу активлаштырылды: {badge} **{plan}**\nАктив вакыты: **{expires}**",
        "payment_failed_sync": "⚠️ Түләү узды, ләкин сайт синхронлаштыруны әле расламады. Админга хәбәр җибәрелде.",
        "same_or_higher": "Сездә инде бу план яки аннан югарысы бар.",
        "limit_reached": "⛔ Көндәлек AI лимиты бетте: **{used}/{limit}**.",
        "limit_hint": "Лимитны арттыру өчен «Тарифлар» бүлегендә планны яңартыгыз.",
        "limit_status": "Бүген: **{used}/{limit}**",
        "limit_status_unlimited": "Бүген: **чиксез**",
        "game_bonus_line": "🎁 Язылу бонусы: **+{bonus}** токен ({pct}%)",
        "profile_plan": "\n\n💎 План: {badge} **{plan}**",
        "profile_expires": "\n⏳ Актив вакыты: **{expires}**",
        "profile_ai_limit": "\n🤖 Көненә AI: **{limit}**",
        "profile_game_bonus": "\n🎮 Уен бонусы: **+{bonus}%**",
        "streak_limit": "\n📦 План буенча туңдыру лимиты: **{limit}**",
        "noop_included": "Бу дәрәҗә инде сезнең мөмкинлекләргә керә.",
    },
}


def st(lang: str, key: str, **kwargs) -> str:
    data = SUBSCRIPTION_TEXTS.get(lang, SUBSCRIPTION_TEXTS["ru"])
    text = data.get(key, SUBSCRIPTION_TEXTS["ru"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text


def _bool_text(lang: str, value: bool) -> str:
    return st(lang, "yes" if value else "no")


def _limit_text(lang: str, value: int) -> str:
    return st(lang, "unlimited") if int(value) == 0 else str(value)


def _stars_text(stars: int) -> str:
    return f"{int(stars)} ⭐️"


def _plan_price_text(tier: str) -> str:
    plan = get_plan_config(tier)
    stars = int(plan["stars_price_month"])
    return "Free" if stars == 0 else f"{_stars_text(stars)} / 30d"


def _plan_feature_lines(lang: str, tier: str) -> list[str]:
    plan = get_plan_config(tier)
    return [
        f"{st(lang, 'price')}: **{_plan_price_text(tier)}**",
        f"{st(lang, 'ai_daily_limit')}: **{_limit_text(lang, int(plan['ai_daily_limit']))}**",
        f"{st(lang, 'freeze_limit')}: **{_limit_text(lang, int(plan['max_freezes']))}**",
        f"{st(lang, 'game_bonus')}: **+{int(plan['coin_bonus_percent'])}%**",
        f"{st(lang, 'premium_prompts')}: **{_bool_text(lang, bool(plan['premium_prompts']))}**",
        f"{st(lang, 'restricted_categories')}: **{_bool_text(lang, bool(plan['restricted_categories']))}**",
    ]


def build_tariffs_text(lang: str, current_plan: dict) -> str:
    current_tier = normalize_plan_tier(current_plan.get("plan_tier"))
    current_title = get_plan_title(current_tier, lang)
    current_badge = get_plan_badge(current_tier)
    lines = [
        st(lang, "title"),
        "",
        f"{st(lang, 'current_plan')}: {current_badge} **{current_title}**",
    ]

    current_expiry = format_expiry(current_plan.get("plan_expires_at"), lang)
    if current_expiry:
        lines.append(f"{st(lang, 'renews_until')}: **{current_expiry}**")

    lines.extend(["", st(lang, "shared_sync"), "", st(lang, "choose")])

    for tier in ("free", *PAID_PLAN_ORDER):
        lines.append("")
        lines.append(f"{get_plan_badge(tier)} **{get_plan_title(tier, lang)}**")
        lines.extend(f"• {line}" for line in _plan_feature_lines(lang, tier))

    return "\n".join(lines)


def get_tariffs_menu_inline(lang: str, current_tier: str) -> InlineKeyboardMarkup:
    rows = []
    for tier in PAID_PLAN_ORDER:
        label = f"{get_plan_badge(tier)} {get_plan_title(tier, lang)} · {_stars_text(get_plan_config(tier)['stars_price_month'])}"
        callback = f"tariff_buy:{tier}"
        if has_same_or_higher_plan(current_tier, tier):
            label = f"{get_plan_badge(tier)} {get_plan_title(tier, lang)} · {st(lang, 'included')}"
            callback = "tariff_noop"
        rows.append([InlineKeyboardButton(text=label, callback_data=callback)])
    rows.append([InlineKeyboardButton(text=get_text(lang, "back"), callback_data="back_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_tariff_checkout_inline(lang: str, pay_url: str, stars: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=st(lang, "pay", stars=stars), url=pay_url)],
            [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="menu_tariffs")],
        ]
    )


async def apply_subscription_snapshot(user_id: int, snapshot: dict | None) -> dict:
    if not snapshot:
        return await get_user_plan(user_id)
    return await update_user_plan(
        user_id,
        plan_tier=snapshot.get("plan_tier", "free"),
        plan_expires_at=snapshot.get("current_period_end"),
        benefits=snapshot.get("benefits") or {},
    )


async def sync_subscription_cache(
    user_id: int,
    *,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    language: str = "ru",
) -> dict:
    await website_upsert_user(
        telegram_user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language=language,
    )
    snapshot = await website_get_subscription_status(user_id)
    return await apply_subscription_snapshot(user_id, snapshot if isinstance(snapshot, dict) else None)


def build_profile_plan_block(lang: str, plan: dict) -> str:
    tier = normalize_plan_tier(plan.get("plan_tier"))
    block = st(lang, "profile_plan", badge=get_plan_badge(tier), plan=get_plan_title(tier, lang))
    expires = format_expiry(plan.get("plan_expires_at"), lang)
    if expires:
        block += st(lang, "profile_expires", expires=expires)
    block += st(lang, "profile_ai_limit", limit=_limit_text(lang, int(plan.get("plan_ai_limit", 0))))
    block += st(lang, "profile_game_bonus", bonus=int(plan.get("plan_coin_bonus_pct", 0)))
    return block


def build_ai_limit_status(lang: str, used: int, limit: int) -> str:
    if int(limit) == 0:
        return st(lang, "limit_status_unlimited")
    return st(lang, "limit_status", used=used, limit=limit)


def build_ai_activation_text(lang: str, model_title: str, plan: dict, used_today: int) -> str:
    return f"{model_title} {get_text(lang, 'ai_activated')}\n\n{build_ai_limit_status(lang, used_today, int(plan.get('plan_ai_limit', 0)))}"


async def start_ai_session(
    callback: CallbackQuery,
    state: FSMContext,
    *,
    model_key: str,
    model_title: str,
) -> None:
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    plan = await sync_subscription_cache(user_id, language=user_lang)
    used_today = await count_ai_messages_today(user_id)

    await state.set_state(AIChatState.waiting_for_message)
    await state.update_data(current_model=model_key)
    await callback.message.edit_text(
        build_ai_activation_text(user_lang, model_title, plan, used_today),
        reply_markup=get_exit_ai_inline(user_lang),
        parse_mode="Markdown",
    )
    await callback.answer()


# ==============================================================================
# 4. ПАНЕЛЬ МОДЕРАЦИИ
# ==============================================================================

MODERATION_PANEL_TEXTS = {
    "ru": {
        "queue_title": "🛠 Модерация промптов",
        "queue_empty": "Сейчас нет промптов, ожидающих модерацию.",
        "queue_hint": "Выберите промпт из списка ниже.",
        "open_prompt": "Открыть промпт",
        "open_queue": "Открыть очередь",
        "approve": "✅ Одобрить",
        "approve_comment": "💬 Одобрить с комментарием",
        "reject": "❌ Отклонить",
        "reject_comment": "📝 Отклонить с комментарием",
        "comment_prompt_approve": "💬 Отправьте комментарий для одобрения одним сообщением.",
        "comment_prompt_reject": "📝 Отправьте причину отклонения одним сообщением.",
        "comment_saved": "✅ Решение сохранено.",
        "no_access": "⛔ У вас нет доступа к модерации.",
        "load_failed": "❌ Не удалось загрузить данные модерации.",
        "decision_failed": "❌ Не удалось применить решение. Возможно, промпт уже обработан.",
        "reason_more_detail": "Нужно больше деталей и конкретики.",
        "reason_structure": "Нужно улучшить структуру и формат ответа.",
        "reason_duplicate": "Похоже на дубликат или слишком близкую версию существующего промпта.",
        "reason_policy": "Нужно привести промпт в соответствие с правилами площадки.",
        "back_queue": "⬅️ К очереди",
        "back_prompt": "⬅️ К карточке",
        "prev_page": "⬅️ Назад",
        "next_page": "Вперед ➡️",
        "card_header": "📌 Карточка промпта",
        "card_author": "Автор",
        "card_slug": "Slug",
        "card_status": "Статус",
        "card_summary": "Кратко",
        "card_category": "Категория",
        "card_technique": "Техника",
        "card_tags": "Теги",
        "card_use_cases": "Use cases",
        "card_models": "Модели",
        "card_body": "Промпт",
        "status_done": "Готово: {state}",
    },
    "en": {
        "queue_title": "🛠 Prompt moderation",
        "queue_empty": "There are no prompts waiting for moderation right now.",
        "queue_hint": "Choose a prompt from the list below.",
        "open_prompt": "Open prompt",
        "open_queue": "Open queue",
        "approve": "✅ Approve",
        "approve_comment": "💬 Approve with comment",
        "reject": "❌ Reject",
        "reject_comment": "📝 Reject with comment",
        "comment_prompt_approve": "💬 Send one comment message for approval.",
        "comment_prompt_reject": "📝 Send one rejection reason message.",
        "comment_saved": "✅ Decision saved.",
        "no_access": "⛔ You do not have moderation access.",
        "load_failed": "❌ Failed to load moderation data.",
        "decision_failed": "❌ Failed to apply the decision. The prompt may already be processed.",
        "reason_more_detail": "Please add more detail and specificity.",
        "reason_structure": "Please improve the structure and output format.",
        "reason_duplicate": "This looks like a duplicate or too close to an existing prompt.",
        "reason_policy": "Please align the prompt with marketplace rules.",
        "back_queue": "⬅️ Back to queue",
        "back_prompt": "⬅️ Back to prompt",
        "prev_page": "⬅️ Prev",
        "next_page": "Next ➡️",
        "card_header": "📌 Prompt card",
        "card_author": "Author",
        "card_slug": "Slug",
        "card_status": "Status",
        "card_summary": "Summary",
        "card_category": "Category",
        "card_technique": "Technique",
        "card_tags": "Tags",
        "card_use_cases": "Use cases",
        "card_models": "Models",
        "card_body": "Prompt",
        "status_done": "Done: {state}",
    },
    "tt": {
        "queue_title": "🛠 Промпт модерациясе",
        "queue_empty": "Хәзер модерация көткән промптлар юк.",
        "queue_hint": "Түбәндәге исемлектән промпт сайлагыз.",
        "open_prompt": "Промптны ачу",
        "open_queue": "Чиратны ачу",
        "approve": "✅ Раслау",
        "approve_comment": "💬 Комментарий белән раслау",
        "reject": "❌ Кире кагу",
        "reject_comment": "📝 Комментарий белән кире кагу",
        "comment_prompt_approve": "💬 Раслау өчен комментарийны бер хәбәр белән җибәрегез.",
        "comment_prompt_reject": "📝 Кире кагу сәбәбен бер хәбәр белән җибәрегез.",
        "comment_saved": "✅ Карар сакланды.",
        "no_access": "⛔ Сездә модерациягә керү мөмкинлеге юк.",
        "load_failed": "❌ Модерация мәгълүматларын йөкләп булмады.",
        "decision_failed": "❌ Карарны кулланып булмады. Бәлки промпт инде эшкәртелгәндер.",
        "reason_more_detail": "Күбрәк деталь һәм төгәллек кирәк.",
        "reason_structure": "Структураны һәм җавап форматын яхшыртырга кирәк.",
        "reason_duplicate": "Бу дубликатка яки булган промптка артык якын версиягә охшаган.",
        "reason_policy": "Промптны мәйданчык кагыйдәләренә туры китерергә кирәк.",
        "back_queue": "⬅️ Чиратка",
        "back_prompt": "⬅️ Карточкага",
        "prev_page": "⬅️ Артка",
        "next_page": "Алга ➡️",
        "card_header": "📌 Промпт карточкасы",
        "card_author": "Автор",
        "card_slug": "Slug",
        "card_status": "Статус",
        "card_summary": "Кыскача",
        "card_category": "Категория",
        "card_technique": "Техника",
        "card_tags": "Теглар",
        "card_use_cases": "Use cases",
        "card_models": "Модельләр",
        "card_body": "Промпт",
        "status_done": "Әзер: {state}",
    },
}

MODERATION_REASON_PRESETS = {
    "detail": "reason_more_detail",
    "structure": "reason_structure",
    "duplicate": "reason_duplicate",
    "policy": "reason_policy",
}
MODERATION_PAGE_SIZE = 8


def is_admin_user(user_id: int) -> bool:
    return user_id in ADMIN_TELEGRAM_IDS


def mt(lang: str, key: str, **kwargs) -> str:
    data = MODERATION_PANEL_TEXTS.get(lang, MODERATION_PANEL_TEXTS["ru"])
    text = data.get(key, MODERATION_PANEL_TEXTS["ru"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def moderation_reason_text(reason_code: str, lang: str) -> str:
    key = MODERATION_REASON_PRESETS.get(reason_code, "reason_more_detail")
    return mt(lang, key)


def trim_message_text(value: str | None, limit: int = 2800) -> str:
    text = (value or "").strip()
    if not text:
        return "—"
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}…"


async def notify_admins(bot, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
    for admin_id in ADMIN_TELEGRAM_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=text, reply_markup=reply_markup)
        except Exception:
            continue


def build_moderation_queue_text(lang: str, items: list[dict], *, offset: int) -> str:
    if not items:
        return f"{mt(lang, 'queue_title')}\n\n{mt(lang, 'queue_empty')}"

    lines = [mt(lang, "queue_title"), "", mt(lang, "queue_hint"), ""]
    for idx, item in enumerate(items, start=offset + 1):
        author = item.get("author_display_name") or "—"
        lines.append(f"{idx}. {item.get('title', 'Untitled')}")
        lines.append(f"   {author} · {item.get('slug', '—')}")
    return "\n".join(lines)


def get_moderation_queue_inline(items: list[dict], *, offset: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=item.get("title", "Untitled")[:60], callback_data=f"mod:open:{item['id']}")]
        for item in items
    ]
    nav: list[InlineKeyboardButton] = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"mod:queue:{max(offset - MODERATION_PAGE_SIZE, 0)}"))
    if len(items) == MODERATION_PAGE_SIZE:
        nav.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"mod:queue:{offset + MODERATION_PAGE_SIZE}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="back_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_moderation_card_text(lang: str, prompt: dict) -> str:
    author = prompt.get("author_display_name") or "—"
    username = prompt.get("author_username") or "—"
    summary = trim_message_text(prompt.get("summary"), limit=500)
    body = trim_message_text(prompt.get("body"), limit=2200)
    tags = ", ".join(prompt.get("tags") or []) or "—"
    use_cases = ", ".join(prompt.get("use_cases") or []) or "—"
    models = ", ".join(prompt.get("model_compatibility") or []) or "—"
    lines = [
        mt(lang, "card_header"),
        "",
        f"{mt(lang, 'card_author')}: {author}",
        f"Username: {username}",
        f"{mt(lang, 'card_slug')}: {prompt.get('slug', '—')}",
        f"{mt(lang, 'card_status')}: {prompt.get('moderation_state', 'pending')} / {prompt.get('status', 'draft')}",
        f"{mt(lang, 'card_summary')}: {summary}",
        f"{mt(lang, 'card_category')}: {prompt.get('category_name') or '—'}",
        f"{mt(lang, 'card_technique')}: {prompt.get('technique') or '—'}",
        f"{mt(lang, 'card_tags')}: {tags}",
        f"{mt(lang, 'card_use_cases')}: {use_cases}",
        f"{mt(lang, 'card_models')}: {models}",
        "",
        f"{mt(lang, 'card_body')}:",
        body,
    ]
    notes = (prompt.get("moderation_notes") or "").strip()
    if notes:
        lines.extend(["", f"Комментарий: {notes}"])
    return "\n".join(lines)


def get_moderation_card_inline(prompt_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"mod:approve:{prompt_id}"),
                InlineKeyboardButton(text="💬 Одобрить + коммент", callback_data=f"mod:approvec:{prompt_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod:reject:{prompt_id}"),
                InlineKeyboardButton(text="📝 Отклонить + коммент", callback_data=f"mod:rejectc:{prompt_id}"),
            ],
            [InlineKeyboardButton(text="⬅️ К очереди", callback_data="mod:queue:0")],
        ]
    )


def get_reject_reason_inline(prompt_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мало деталей", callback_data=f"mod:reason:{prompt_id}:detail")],
            [InlineKeyboardButton(text="Нужна структура", callback_data=f"mod:reason:{prompt_id}:structure")],
            [InlineKeyboardButton(text="Дубликат", callback_data=f"mod:reason:{prompt_id}:duplicate")],
            [InlineKeyboardButton(text="Нарушает правила", callback_data=f"mod:reason:{prompt_id}:policy")],
            [InlineKeyboardButton(text="📝 Свой комментарий", callback_data=f"mod:rejectc:{prompt_id}")],
            [InlineKeyboardButton(text="⬅️ К карточке", callback_data=f"mod:open:{prompt_id}")],
        ]
    )


def get_moderation_done_inline(prompt_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть карточку", callback_data=f"mod:open:{prompt_id}")],
            [InlineKeyboardButton(text="⬅️ К очереди", callback_data="mod:queue:0")],
        ]
    )


async def load_moderation_queue(admin_telegram_user_id: int, *, offset: int = 0) -> list[dict]:
    return await website_get_moderation_queue(
        acting_telegram_user_id=admin_telegram_user_id,
        skip=offset,
        limit=MODERATION_PAGE_SIZE,
    )

# ==============================================================================
# 5. КЛАВИАТУРЫ
# ==============================================================================

def get_main_menu_inline(lang: str = 'ru'):
    """Главное меню бота"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, 'catalog_ai_btn'), callback_data="menu_catalog_ai")],
        [InlineKeyboardButton(text=get_text(lang, 'search_btn'), callback_data="menu_search"),
         InlineKeyboardButton(text=get_text(lang, 'tariffs_btn'), callback_data="menu_tariffs")],
        [InlineKeyboardButton(text=lt(lang, 'missions_btn_new'), callback_data="menu_missions"),
         InlineKeyboardButton(text=get_text(lang, 'games_btn'), callback_data="menu_games")],
        [InlineKeyboardButton(text=lt(lang, 'leaderboard_btn'), callback_data="menu_leaderboard"),
         InlineKeyboardButton(text=get_text(lang, 'profile_btn'), callback_data="menu_profile")],
    ])

def get_leaderboard_menu_inline(lang: str = 'ru'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lt(lang, 'leaderboard_best_btn'), callback_data="leaderboard_best")],
        [InlineKeyboardButton(text=lt(lang, 'leaderboard_coins_btn'), callback_data="leaderboard_coins")],
        [InlineKeyboardButton(text=lt(lang, 'leaderboard_streak_btn'), callback_data="leaderboard_streak")],
        [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="back_main_menu")],
    ])


def get_leaderboard_back_inline(lang: str = 'ru'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lt(lang, 'leaderboard_best_btn'), callback_data="leaderboard_best"),
         InlineKeyboardButton(text=lt(lang, 'leaderboard_coins_btn'), callback_data="leaderboard_coins")],
        [InlineKeyboardButton(text=lt(lang, 'leaderboard_streak_btn'), callback_data="leaderboard_streak")],
        [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="menu_leaderboard")],
    ])


def get_catalog_ai_inline(lang: str = 'ru'):
    """Меню выбора модели ИИ"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, 'mistral_btn'), callback_data="ai_model_mistral")],
        [InlineKeyboardButton(text=get_text(lang, 'qwen_btn'), callback_data="ai_model_qwen")],
        [InlineKeyboardButton(text=get_text(lang, 'z_ai_btn'), callback_data="ai_model_zai")],
        [InlineKeyboardButton(text=get_text(lang, 'nemotron_btn'), callback_data="ai_model_nemotron")],
        [InlineKeyboardButton(text=get_text(lang, 'gpt_oss_btn'), callback_data="ai_model_gptoss")],
        [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="back_main_menu")]
    ])


def get_exit_ai_inline(lang: str = 'ru'):
    """Кнопка выхода из режима чата с ИИ"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, 'complete_session'), callback_data="exit_ai_chat")]
    ])


def get_profile_menu_inline(lang: str = 'ru'):
    """Меню профиля"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, 'update'), callback_data="menu_profile")],
        [InlineKeyboardButton(text=lt(lang, 'streak_btn'), callback_data="menu_streak"),
         InlineKeyboardButton(text=lt(lang, 'missions_btn_new'), callback_data="menu_missions")],
        [InlineKeyboardButton(text=get_text(lang, 'language_settings'), callback_data="menu_language")],
        [InlineKeyboardButton(text=get_text(lang, 'notifications_settings'), callback_data="menu_notifications")],
        [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="back_main_menu")],
    ])


def get_search_results_inline(results: list, lang: str = 'ru'):
    """Клавиатура с результатами поиска"""
    keyboard = []
    for model in results:
        keyboard.append([
            InlineKeyboardButton(
                text=model["name"],
                callback_data=f"search_select_{model['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text=get_text(lang, 'back_to_menu'), callback_data="back_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_model_detail_inline(model_id: str, lang: str = 'ru'):
    """Клавиатура для выбранной модели"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, 'launch_model'), callback_data=f"launch_model_{model_id}")],
        [InlineKeyboardButton(text=get_text(lang, 'back_to_search'), callback_data="menu_search")],
        [InlineKeyboardButton(text=get_text(lang, 'back_to_menu'), callback_data="back_main_menu")],
    ])


def get_language_inline(lang: str = 'ru'):
    """Клавиатура выбора языка с отметкой выбранного языка"""
    ru_text = "✅ Русский" if lang == "ru" else " Русский"
    en_text = "✅ English" if lang == "en" else " English"
    tt_text = "✅ Татарча" if lang == "tt" else " Татарча"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ru_text, callback_data="lang_ru")],
        [InlineKeyboardButton(text=en_text, callback_data="lang_en")],
        [InlineKeyboardButton(text=tt_text, callback_data="lang_tt")],
        [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="menu_profile")],
    ])


def get_notifications_inline(settings: dict, lang: str = 'ru'):
    """Клавиатура настроек уведомлений"""
    daily = "🔔" if settings['daily_reminder'] else "🔕"
    news = "📰" if settings['news'] else "📰❌"
    missions = "🎯" if settings['missions'] else "🎯❌"

    if lang == "en":
        main_text = "ON ✅" if settings['is_enabled'] else "OFF ❌"
        daily_text = "Daily"
        news_text = "News"
        missions_text = "Missions"
    elif lang == "tt":
        main_text = "КАБ ✅" if settings['is_enabled'] else "СҮН ❌"
        daily_text = "Көндәлек"
        news_text = "Яңалыклар"
        missions_text = "Миссияләр"
    else:
        main_text = "ВКЛ ✅" if settings['is_enabled'] else "ВЫКЛ ❌"
        daily_text = "Ежедневные"
        news_text = "Новости"
        missions_text = "Миссии"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=("🔘 " + main_text),
            callback_data="notif_toggle_main"
        )],
        [InlineKeyboardButton(text=f"{daily} {daily_text}", callback_data="notif_toggle_daily"),
         InlineKeyboardButton(text=f"{news} {news_text}", callback_data="notif_toggle_news")],
        [InlineKeyboardButton(text=f"{missions} {missions_text}", callback_data="notif_toggle_missions")],
        [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="menu_profile")],
    ])


def get_streak_menu_inline(lang: str = 'ru'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lt(lang, 'claim_streak_btn'), callback_data="claim_streak")],
        [InlineKeyboardButton(text=lt(lang, 'buy_freeze_btn'), callback_data="buy_freeze")],
        [InlineKeyboardButton(text=lt(lang, 'missions_btn_new'), callback_data="menu_missions")],
        [InlineKeyboardButton(text=lt(lang, 'back_to_profile'), callback_data="menu_profile")],
    ])


def get_missions_menu_inline(lang: str = 'ru'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lt(lang, 'streak_btn'), callback_data="menu_streak")],
        [InlineKeyboardButton(text=lt(lang, 'back_to_profile'), callback_data="menu_profile")],
    ])

def get_games_menu_inline(lang: str = 'ru'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lt(lang, 'ai_quiz_btn'), callback_data="game_ai_quiz")],
        [InlineKeyboardButton(text=lt(lang, 'prompt_puzzle_btn'), callback_data="game_prompt_puzzle")],
        [InlineKeyboardButton(text=get_text(lang, 'back'), callback_data="back_main_menu")],
    ])


def get_ai_quiz_options_inline(question_id: int, lang: str = 'ru'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"🅰️ {lt(lang, 'quiz_option_a')}", callback_data=f"quiz_answer:{question_id}:a"),
            InlineKeyboardButton(text=f"🅱️ {lt(lang, 'quiz_option_b')}", callback_data=f"quiz_answer:{question_id}:b"),
        ],
        [InlineKeyboardButton(text=lt(lang, 'back_to_games_btn'), callback_data="menu_games")],
    ])

def get_prompt_puzzle_inline(puzzle_id: int, pieces: list[str], lang: str = 'ru'):
    keyboard = []

    for idx, piece in enumerate(pieces):
        keyboard.append([
            InlineKeyboardButton(
                text=piece,
                callback_data=f"puzzle_pick:{puzzle_id}:{idx}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text=lt(lang, 'prompt_puzzle_ready_btn'), callback_data=f"puzzle_check:{puzzle_id}")
    ])
    keyboard.append([
        InlineKeyboardButton(text=lt(lang, 'prompt_puzzle_reset_btn'), callback_data=f"puzzle_reset:{puzzle_id}")
    ])
    keyboard.append([
        InlineKeyboardButton(text=lt(lang, 'back_to_games_btn'), callback_data="menu_games")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ai_quiz_result_inline(next_index: int, total_questions: int, lang: str = 'ru'):
    buttons = []
    if next_index < total_questions:
        buttons.append([InlineKeyboardButton(text=lt(lang, 'next_question_btn'), callback_data=f"quiz_next:{next_index}")])

    buttons.append([InlineKeyboardButton(text=lt(lang, 'back_to_games_btn'), callback_data="menu_games")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==============================================================================
# 6. СЛУЖЕБНЫЕ ФУНКЦИИ ОТОБРАЖЕНИЯ
# ==============================================================================

def build_missions_text(lang: str, economy: dict, missions: dict) -> str:
    daily_lines = []
    for m in missions["daily"]:
        status = "✅" if m["is_completed"] else "⬜"
        daily_lines.append(
            f"{status} {m['title']} — {m['progress']}/{m['target_value']} (+{m['reward']})"
        )

    permanent_lines = []
    for m in missions["permanent"]:
        status = "✅" if m["is_completed"] else "⬜"
        permanent_lines.append(
            f"{status} {m['title']} — {m['progress']}/{m['target_value']} (+{m['reward']})"
        )

    text = (
        f"{lt(lang, 'missions_title')}\n\n"
        f"{lt(lang, 'economy_line', coins=economy['coins'], streak=economy['streak'], freeze_count=economy['freeze_count'])}\n\n"
        f"{lt(lang, 'daily_missions')}\n"
        f"{chr(10).join(daily_lines) if daily_lines else lt(lang, 'no_missions')}\n\n"
        f"{lt(lang, 'permanent_missions')}\n"
        f"{chr(10).join(permanent_lines) if permanent_lines else lt(lang, 'no_missions')}"
    )

    return text

async def render_ai_quiz_question(message_obj, question_index: int, user_lang: str):
    question = AI_QUIZ_QUESTIONS[question_index]

    text = (
        f"{lt(user_lang, 'ai_quiz_title')}\n\n"
        f"❓ {question['question'][user_lang]}\n\n"
        f"🅰️ {question['option_a'][user_lang]}\n\n"
        f"🅱️ {question['option_b'][user_lang]}"
    )

    await message_obj.edit_text(
        text,
        reply_markup=get_ai_quiz_options_inline(question["id"], user_lang),
        parse_mode="Markdown"
    )

async def render_prompt_puzzle(message_obj, puzzle_index: int, user_lang: str, selected_order: list[int] | None = None):
    puzzle = PROMPT_PUZZLES[puzzle_index]
    selected_order = selected_order or []

    pieces = puzzle["pieces"][user_lang]
    current_build = " → ".join(pieces[i] for i in selected_order) if selected_order else lt(user_lang, "prompt_puzzle_empty")

    text = (
        f"{lt(user_lang, 'prompt_puzzle_title')}\n\n"
        f"📦 {', '.join(pieces)}\n\n"
        f"🛠 {lt(user_lang, 'prompt_puzzle_current')}\n"
        f"`{current_build}`"
    )

    await message_obj.edit_text(
        text,
        reply_markup=get_prompt_puzzle_inline(puzzle["id"], pieces, user_lang),
        parse_mode="Markdown"
    )


def format_leaderboard_lines(items: list[dict], metric_key: str) -> str:
    medals = ["🥇", "🥈", "🥉"]
    lines = []

    for idx, item in enumerate(items, start=1):
        prefix = medals[idx - 1] if idx <= 3 else f"{idx}."
        lines.append(f"{prefix} {item['display_name']} — {item[metric_key]}")

    return "\n".join(lines) if lines else "Пока пусто"


def format_best_leaderboard_lines(items: list[dict]) -> str:
    medals = ["🥇", "🥈", "🥉"]
    lines = []

    for idx, item in enumerate(items, start=1):
        prefix = medals[idx - 1] if idx <= 3 else f"{idx}."
        lines.append(
            f"{prefix} {item['display_name']} — {item['score']} "
            f"(🪙 {item['coins']} | 🔥 {item['streak']})"
        )

    return "\n".join(lines) if lines else "Пока пусто"


def split_text_into_chunks(text: str, chunk_size: int = 3500) -> list[str]:
    chunks = []

    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break

        split_pos = text.rfind("\n", 0, chunk_size)
        if split_pos == -1:
            split_pos = text.rfind(" ", 0, chunk_size)
        if split_pos == -1:
            split_pos = chunk_size

        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip()

    return chunks


async def safe_send_long_message(message: Message, text: str, reply_markup=None):
    chunks = split_text_into_chunks(text)

    for i, chunk in enumerate(chunks):
        if i == len(chunks) - 1:
            await message.answer(chunk, reply_markup=reply_markup)
        else:
            await message.answer(chunk)


async def call_openrouter_model(api_url: str, api_key: str, model: str, user_text: str) -> str:
    timeout = aiohttp.ClientTimeout(total=180, connect=20, sock_connect=20, sock_read=180)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-bot.com",
        "X-Title": "AI Hub Bot"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_text}]
    }

    last_error = None

    for attempt in range(3):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(api_url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]

                    error_text = await resp.text()
                    last_error = Exception(f"Ошибка API {model}: {resp.status}\n{error_text}")

            await asyncio.sleep(2 * (attempt + 1))

        except asyncio.TimeoutError as e:
            last_error = e
            await asyncio.sleep(2 * (attempt + 1))

        except aiohttp.ClientError as e:
            last_error = e
            await asyncio.sleep(2 * (attempt + 1))

    raise last_error if last_error else Exception("Неизвестная ошибка OpenRouter")


def _get_vosk_model():
    """Ленивая загрузка локальной STT-модели, чтобы бот стартовал даже без Vosk."""
    global _vosk_model
    if _vosk_model is not None:
        return _vosk_model

    if not os.path.isdir(VOSK_MODEL_PATH):
        raise RuntimeError(f"Vosk model not found: {VOSK_MODEL_PATH}")

    try:
        from vosk import KaldiRecognizer, Model
    except ImportError as exc:
        raise RuntimeError("Python package 'vosk' is not installed") from exc

    _vosk_model = (Model(VOSK_MODEL_PATH), KaldiRecognizer)
    return _vosk_model


async def _transcribe_voice_with_vosk(file_path: str) -> str:
    wav_path = os.path.splitext(file_path)[0] + ".wav"
    model, recognizer_cls = _get_vosk_model()

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", file_path,
                "-ar", "16000",
                "-ac", "1",
                "-f", "wav",
                wav_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        with wave.open(wav_path, "rb") as wf:
            if wf.getnchannels() != 1 or wf.getframerate() != 16000:
                raise RuntimeError("Vosk requires mono WAV 16kHz")

            recognizer = recognizer_cls(model, wf.getframerate())
            recognizer.SetWords(True)
            final_text_parts = []

            while True:
                data = wf.readframes(4000)
                if not data:
                    break

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if result.get("text"):
                        final_text_parts.append(result["text"])

            final_result = json.loads(recognizer.FinalResult())
            if final_result.get("text"):
                final_text_parts.append(final_result["text"])

        return " ".join(final_text_parts).strip()
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


async def _transcribe_voice_with_openai(file_path: str) -> str:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    headers = {"Authorization": f"Bearer {openai_api_key}"}
    data = aiohttp.FormData()
    data.add_field("model", "gpt-4o-mini-transcribe")

    with open(file_path, "rb") as audio_file:
        data.add_field("file", audio_file)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                data=data,
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("text", "")

                error = await resp.text()
                raise RuntimeError(f"STT API error: {error}")


async def transcribe_voice_to_text(file_path: str) -> str:
    """
    Распознает голос локально через Vosk, а при недоступности Vosk падает обратно на OpenAI STT.
    """
    try:
        return await _transcribe_voice_with_vosk(file_path)
    except Exception as vosk_error:
        try:
            return await _transcribe_voice_with_openai(file_path)
        except Exception as openai_error:
            raise RuntimeError(
                f"Vosk STT failed: {vosk_error}; OpenAI STT failed: {openai_error}"
            ) from openai_error
# ==============================================================================
# 7. ХЕНДЛЕРЫ НАВИГАЦИИ
# ==============================================================================

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Главное меню бота при запуске"""
    user_id = message.from_user.id
    full_name = message.from_user.full_name

    await add_or_update_user(
        user_id=user_id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or ""
    )

    user_lang = await get_user_language(user_id)
    await sync_subscription_cache(
        user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language=user_lang,
    )

    # создаём миссии при первом/очередном входе
    await ensure_daily_missions(user_id)
    await ensure_permanent_missions(user_id)

    await message.answer(
        get_text(user_lang, 'welcome', name=escape(full_name)),
        parse_mode="Markdown",
        reply_markup=get_main_menu_inline(user_lang)
    )


@router.callback_query(F.data == "back_main_menu")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню из любого раздела"""
    await state.clear()
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await callback.message.edit_text(
        get_text(user_lang, 'main_menu'),
        reply_markup=get_main_menu_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


# --- КАТАЛОГ ИИ ---

@router.callback_query(F.data == "menu_catalog_ai")
async def show_catalog_ai(callback: CallbackQuery):
    """Показывает доступные модели ИИ"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    await sync_subscription_cache(user_id, language=user_lang)

    await callback.message.edit_text(
        get_text(user_lang, 'catalog_ai'),
        reply_markup=get_catalog_ai_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "game_ai_quiz")
async def start_ai_quiz(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    await sync_subscription_cache(user_id, language=user_lang)

    await state.set_state(GamesState.in_ai_quiz)
    await state.update_data(ai_quiz_index=0)

    await render_ai_quiz_question(callback.message, 0, user_lang)
    await callback.answer()


@router.callback_query(F.data.startswith("quiz_answer:"))
async def process_ai_quiz_answer(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    parts = callback.data.split(":")
    question_id = int(parts[1])
    user_answer = parts[2]

    question = next((q for q in AI_QUIZ_QUESTIONS if q["id"] == question_id), None)
    if not question:
        await callback.answer("Вопрос не найден", show_alert=True)
        return

    state_data = await state.get_data()
    current_index = state_data.get("ai_quiz_index", 0)

    if user_answer == question["correct"]:
        reward_info = await grant_game_reward(user_id, question["reward"])
        text = lt(
            user_lang,
            "quiz_correct",
            reward=reward_info["total_reward"],
            explanation=question["explanation"][user_lang]
        )
        if reward_info["bonus_reward"] > 0:
            text += "\n\n" + st(
                user_lang,
                "game_bonus_line",
                bonus=reward_info["bonus_reward"],
                pct=reward_info["bonus_pct"],
            )
    else:
        text = lt(
            user_lang,
            "quiz_wrong",
            explanation=question["explanation"][user_lang]
        )

    await callback.message.edit_text(
        text,
        reply_markup=get_ai_quiz_result_inline(current_index + 1, len(AI_QUIZ_QUESTIONS), user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("quiz_next:"))
async def next_ai_quiz_question(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    next_index = int(callback.data.split(":")[1])

    await state.set_state(GamesState.in_ai_quiz)
    await state.update_data(ai_quiz_index=next_index)

    await render_ai_quiz_question(callback.message, next_index, user_lang)
    await callback.answer()

@router.callback_query(F.data == "game_prompt_puzzle")
async def start_prompt_puzzle(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    await sync_subscription_cache(user_id, language=user_lang)

    await state.set_state(GamesState.in_prompt_puzzle)
    await state.update_data(puzzle_index=0, puzzle_selected_order=[])

    await render_prompt_puzzle(callback.message, 0, user_lang, [])
    await callback.answer()

@router.callback_query(F.data.startswith("puzzle_pick:"))
async def process_prompt_puzzle_pick(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    _, puzzle_id_str, piece_idx_str = callback.data.split(":")
    puzzle_id = int(puzzle_id_str)
    piece_idx = int(piece_idx_str)

    state_data = await state.get_data()
    puzzle_index = state_data.get("puzzle_index", 0)
    selected_order = state_data.get("puzzle_selected_order", [])

    puzzle = PROMPT_PUZZLES[puzzle_index]
    if puzzle["id"] != puzzle_id:
        await callback.answer("Пазл не найден", show_alert=True)
        return

    if piece_idx not in selected_order:
        selected_order.append(piece_idx)

    await state.update_data(puzzle_selected_order=selected_order)
    await render_prompt_puzzle(callback.message, puzzle_index, user_lang, selected_order)
    await callback.answer()

@router.callback_query(F.data.startswith("puzzle_reset:"))
async def process_prompt_puzzle_reset(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    state_data = await state.get_data()
    puzzle_index = state_data.get("puzzle_index", 0)

    await state.update_data(puzzle_selected_order=[])
    await render_prompt_puzzle(callback.message, puzzle_index, user_lang, [])
    await callback.answer()

@router.callback_query(F.data.startswith("puzzle_check:"))
async def process_prompt_puzzle_check(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    state_data = await state.get_data()
    puzzle_index = state_data.get("puzzle_index", 0)
    selected_order = state_data.get("puzzle_selected_order", [])

    puzzle = PROMPT_PUZZLES[puzzle_index]
    is_correct = selected_order == puzzle["correct_order"]

    if is_correct:
        reward_info = await grant_game_reward(user_id, puzzle["reward"])
        text = lt(
            user_lang,
            "prompt_puzzle_correct",
            reward=reward_info["total_reward"],
            explanation=puzzle["explanation"][user_lang]
        )
        if reward_info["bonus_reward"] > 0:
            text += "\n\n" + st(
                user_lang,
                "game_bonus_line",
                bonus=reward_info["bonus_reward"],
                pct=reward_info["bonus_pct"],
            )

        buttons = []
        if puzzle_index + 1 < len(PROMPT_PUZZLES):
            buttons.append([
                InlineKeyboardButton(
                    text=lt(user_lang, "next_puzzle_btn"),
                    callback_data=f"puzzle_next:{puzzle_index + 1}"
                )
            ])
        buttons.append([
            InlineKeyboardButton(text=lt(user_lang, "back_to_games_btn"), callback_data="menu_games")
        ])

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="Markdown"
        )
    else:
        text = lt(
            user_lang,
            "prompt_puzzle_wrong",
            explanation=puzzle["explanation"][user_lang]
        )

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=lt(user_lang, 'prompt_puzzle_reset_btn'), callback_data=f"puzzle_reset:{puzzle['id']}")],
                [InlineKeyboardButton(text=lt(user_lang, 'back_to_games_btn'), callback_data="menu_games")]
            ]),
            parse_mode="Markdown"
        )

    await callback.answer()
# ==============================================================================
# 8. НАСТРОЙКИ УВЕДОМЛЕНИЙ
# ==============================================================================

@router.callback_query(F.data == "menu_notifications")
async def show_notifications_settings(callback: CallbackQuery):
    """Показывает настройки уведомлений"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    settings = await get_user_notification_settings(user_id)

    if user_lang == "en":
        status = "✅ ON" if settings['is_enabled'] else "❌ OFF"
    elif user_lang == "tt":
        status = "✅ КАБ" if settings['is_enabled'] else "❌ СҮН"
    else:
        status = "✅ ВКЛ" if settings['is_enabled'] else "❌ ВЫКЛ"

    daily = "🔔" if settings['daily_reminder'] else "🔕"
    news = "📰" if settings['news'] else "📰❌"
    missions = "🎯" if settings['missions'] else "🎯❌"

    text = get_text(
        user_lang, 'notifications',
        status=status,
        daily=daily,
        news=news,
        missions=missions
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_notifications_inline(settings, user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "notif_toggle_main")
async def toggle_main_notif(callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = await get_user_notification_settings(user_id)
    new_value = not settings['is_enabled']
    await update_notification_setting(user_id, 'is_enabled', new_value)
    await show_notifications_settings(callback)
    await callback.answer()


@router.callback_query(F.data == "notif_toggle_daily")
async def toggle_daily_notif(callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = await get_user_notification_settings(user_id)
    new_value = not settings['daily_reminder']
    await update_notification_setting(user_id, 'daily_reminder', new_value)
    await show_notifications_settings(callback)
    await callback.answer()


@router.callback_query(F.data == "notif_toggle_news")
async def toggle_news_notif(callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = await get_user_notification_settings(user_id)
    new_value = not settings['news']
    await update_notification_setting(user_id, 'news', new_value)
    await show_notifications_settings(callback)
    await callback.answer()


@router.callback_query(F.data == "notif_toggle_missions")
async def toggle_missions_notif(callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = await get_user_notification_settings(user_id)
    new_value = not settings['missions']
    await update_notification_setting(user_id, 'missions', new_value)
    await show_notifications_settings(callback)
    await callback.answer()


# ==============================================================================
# 9. АДМИНКА: РАССЫЛКА
# ==============================================================================

@router.message(Command("broadcast"))
async def broadcast_command(message: Message):
    """Команда для рассылки сообщений всем пользователям (ТОЛЬКО ДЛЯ АДМИНА)"""
    if not is_admin_user(message.from_user.id):
        return

    if not message.reply_to_message:
        await message.answer("❌ Используйте как ответ на сообщение для рассылки")
        return

    users = await get_all_active_users()
    success = 0
    blocked = 0

    await message.answer(f"🚀 Начинаю рассылку для {len(users)} пользователей...")

    for user_id in users:
        try:
            await message.reply_to_message.copy(chat_id=user_id)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            blocked += 1

    await message.answer(f"✅ Готово!\nУспешно: {success}\nЗаблокировано: {blocked}")


# ==============================================================================
# 10. ПОИСК ПО AI МОДЕЛЯМ
# ==============================================================================

@router.callback_query(F.data == "menu_search")
async def menu_search(callback: CallbackQuery, state: FSMContext):
    """Показывает меню поиска и включает режим поиска"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await track_search_used(user_id)

    await state.set_state(SearchState.waiting_for_query)
    await callback.message.edit_text(
        get_text(user_lang, 'search_prompt'),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_lang, 'back_to_menu'), callback_data="back_main_menu")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(SearchState.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext):
    """Обрабатывает поисковый запрос и показывает результаты"""
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)
    query = (message.text or "").lower().strip()

    results = [
        model for model in AI_MODELS_DB
        if query in model["id"].lower() or query in model["name"].lower() or query in model["description"].lower()
    ]

    if not results:
        await message.answer(
            get_text(user_lang, 'search_no_results', query=escape(query)),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_text(user_lang, 'back_to_search'), callback_data="menu_search")],
                [InlineKeyboardButton(text=get_text(user_lang, 'back_to_menu'), callback_data="back_main_menu")],
            ])
        )
    else:
        results_text = "\n".join([f"• {m['name']} — {m['description']}" for m in results])
        await message.answer(
            get_text(user_lang, 'search_results', count=len(results), results=results_text),
            parse_mode="Markdown",
            reply_markup=get_search_results_inline(results, user_lang)
        )

    await state.clear()


@router.callback_query(F.data.startswith("search_select_"))
async def select_model_from_search(callback: CallbackQuery, state: FSMContext):
    """Показывает детали выбранной модели"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    model_id = callback.data.replace("search_select_", "")
    model = next((m for m in AI_MODELS_DB if m["id"] == model_id), None)

    if model:
        await callback.message.edit_text(
            get_text(
                user_lang, 'model_detail',
                model_name=model['name'],
                description=model['description'],
                model_id=model_id
            ),
            reply_markup=get_model_detail_inline(model_id, user_lang),
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "❌ **Модель не найдена**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_text(user_lang, 'back_to_search'), callback_data="menu_search")],
                [InlineKeyboardButton(text=get_text(user_lang, 'back_to_menu'), callback_data="back_main_menu")],
            ]),
            parse_mode="Markdown"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("launch_model_"))
async def launch_model_from_search(callback: CallbackQuery, state: FSMContext):
    """Запускает чат с выбранной моделью"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    model_id = callback.data.replace("launch_model_", "")
    model = next((m for m in AI_MODELS_DB if m["id"] == model_id), None)

    if model:
        if model_id in ["mistral", "qwen", "zai", "nemotron", "gptoss"]:
            await start_ai_session(
                callback,
                state,
                model_key=model_id,
                model_title=model["name"],
            )
            return
        else:
            if user_lang == "en":
                soon_text = (
                    f"🚧 **{model['name']}**\n\n"
                    f"This model will be available soon!\n"
                    f"Try Mistral AI or Qwen AI for testing.\n\n"
                    f"{model['description']}"
                )
            elif user_lang == "tt":
                soon_text = (
                    f"🚧 **{model['name']}**\n\n"
                    f"Бу модель тиздән кулланыла алачак!\n"
                    f"Тест өчен Mistral AI яки Qwen AI кулланып карагыз.\n\n"
                    f"{model['description']}"
                )
            else:
                soon_text = (
                    f"🚧 **{model['name']}**\n\n"
                    f"Эта модель скоро будет доступна!\n"
                    f"Попробуйте Mistral AI или Qwen AI для тестирования.\n\n"
                    f"{model['description']}"
                )

            await callback.message.edit_text(
                soon_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=get_text(user_lang, 'back_to_search'), callback_data="menu_search")],
                    [InlineKeyboardButton(text=get_text(user_lang, 'back_to_menu'), callback_data="back_main_menu")],
                ]),
                parse_mode="Markdown"
            )
    else:
        await callback.message.edit_text(
            "❌ **Ошибка запуска модели**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_text(user_lang, 'back_to_search'), callback_data="menu_search")],
            ]),
            parse_mode="Markdown"
        )

    await callback.answer()


# ==============================================================================
# 11. ЗАПУСК МОДЕЛЕЙ (MISTRAL + QWEN)
# ==============================================================================

@router.callback_query(F.data == "ai_model_mistral")
async def start_mistral_chat(callback: CallbackQuery, state: FSMContext):
    """Активирует режим диалога с Mistral"""
    await start_ai_session(callback, state, model_key="mistral", model_title="🌪️ Mistral AI")


@router.callback_query(F.data == "ai_model_qwen")
async def start_qwen_chat(callback: CallbackQuery, state: FSMContext):
    """Активирует режим диалога с Qwen"""
    await start_ai_session(callback, state, model_key="qwen", model_title="🤖 Qwen AI")

@router.callback_query(F.data == "ai_model_zai")
async def start_zai_chat(callback: CallbackQuery, state: FSMContext):
    """Активирует режим диалога с Z AI"""
    await start_ai_session(callback, state, model_key="zai", model_title="🤖 Z AI")

@router.callback_query(F.data == "ai_model_nemotron")
async def start_nemotron_chat(callback: CallbackQuery, state: FSMContext):
    """Активирует режим диалога с Nemotron"""
    await start_ai_session(callback, state, model_key="nemotron", model_title="🟢 NVIDIA Nemotron")

@router.callback_query(F.data == "ai_model_gptoss")
async def start_gptoss_chat(callback: CallbackQuery, state: FSMContext):
    await start_ai_session(callback, state, model_key="gptoss", model_title="🧠 OpenAI gpt-oss")

@router.callback_query(F.data == "exit_ai_chat")
async def exit_ai_chat(callback: CallbackQuery, state: FSMContext):
    """Выход из режима диалога"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await state.clear()
    await callback.message.edit_text(
        get_text(user_lang, 'session_ended'),
        reply_markup=get_main_menu_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


# ==============================================================================
# 12. ОБРАБОТКА СООБЩЕНИЙ ДЛЯ ИИ (FSM)
# ==============================================================================

def clean_markdown(text: str) -> str:
    """Убирает Markdown-символы из AI-ответа перед отправкой в обычном text mode."""
    return re.sub(r'([#_*~`])', '', text)


@router.message(AIChatState.waiting_for_message)
async def handle_ai_message(message: Message, state: FSMContext):
    """Обрабатывает текст пользователя и отправляет в AI"""
    user_text = message.text or ""
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)
    plan = await get_user_plan(user_id)
    limit = int(plan.get("plan_ai_limit", 20))
    used_today = await count_ai_messages_today(user_id)

    if limit > 0 and used_today >= limit:
        await message.answer(
            f"{st(user_lang, 'limit_reached', used=used_today, limit=limit)}\n{st(user_lang, 'limit_hint')}",
            reply_markup=get_main_menu_inline(user_lang),
            parse_mode="Markdown",
        )
        return

    state_data = await state.get_data()
    current_model = state_data.get("current_model", "mistral")

    thinking_msg = await message.answer(
        get_text(user_lang, 'thinking'),
        parse_mode="Markdown"
    )

    try:
        bot_response = ""
        model_name = ""

        if current_model == "mistral":
            model_name = "mistral-small"
            if MISTRAL_API_KEY:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {MISTRAL_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "mistral-small",
                        "messages": [{"role": "user", "content": user_text}]
                    }

                    async with session.post(MISTRAL_API_URL, json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            bot_response = data['choices'][0]['message']['content']
                        else:
                            error_text = await resp.text()
                            bot_response = f"⚠️ Ошибка API Mistral: {resp.status}"
                            print(f"❌ Mistral Error: {error_text}")
            else:
                await asyncio.sleep(1)
                if user_lang == "en":
                    bot_response = f"(Mistral demo mode) You wrote: '{user_text}'"
                elif user_lang == "tt":
                    bot_response = f"(Mistral демо режимы) Сез яздыгыз: '{user_text}'"
                else:
                    bot_response = f"(Демо-режим Mistral) Вы написали: '{user_text}'"

        elif current_model == "qwen":
            model_name = "qwen/qwen-2.5-7b-instruct"

            if QWEN_API_KEY:
                bot_response = await call_openrouter_model(
                    api_url=QWEN_API_URL,
                    api_key=QWEN_API_KEY,
                    model="qwen/qwen-2.5-7b-instruct",
                    user_text=user_text
                )
            else:
                await asyncio.sleep(1)
                if user_lang == "en":
                    bot_response = f"(Qwen demo mode) You wrote: '{user_text}'\nAdd OPENROUTER_API_KEY to .env"
                elif user_lang == "tt":
                    bot_response = f"(Qwen демо режимы) Сез яздыгыз: '{user_text}'\nOPENROUTER_API_KEY ны .env ка өстәгез"
                else:
                    bot_response = f"(Демо-режим Qwen) Вы написали: '{user_text}'\nДобавьте OPENROUTER_API_KEY в .env"

        elif current_model == "zai":
            model_name = "z-ai/glm-4.5-air:free"

            if QWEN_API_KEY:
                bot_response = await call_openrouter_model(
                    api_url=QWEN_API_URL,
                    api_key=QWEN_API_KEY,
                    model="z-ai/glm-4.5-air:free",
                    user_text=user_text
                )
            else:
                await asyncio.sleep(1)
                if user_lang == "en":
                    bot_response = f"(Z AI demo mode) You wrote: '{user_text}'\nAdd OPENROUTER_API_KEY to .env"
                elif user_lang == "tt":
                    bot_response = f"(Z AI демо режимы) Сез яздыгыз: '{user_text}'\nOPENROUTER_API_KEY ны .env ка өстәгез"
                else:
                    bot_response = f"(Демо-режим Z AI) Вы написали: '{user_text}'\nДобавьте OPENROUTER_API_KEY в .env"


        elif current_model == "nemotron":
            model_name = "nvidia/nemotron-3-super-120b-a12b:free"

            if QWEN_API_KEY:
                bot_response = await call_openrouter_model(
                    api_url=QWEN_API_URL,
                    api_key=QWEN_API_KEY,
                    model="nvidia/nemotron-3-super-120b-a12b:free",
                    user_text=user_text
                )
            else:
                await asyncio.sleep(1)
                if user_lang == "en":
                    bot_response = f"(Nemotron demo mode) You wrote: '{user_text}'\nAdd OPENROUTER_API_KEY to .env"
                elif user_lang == "tt":
                    bot_response = f"(Nemotron демо режимы) Сез яздыгыз: '{user_text}'\nOPENROUTER_API_KEY ны .env ка өстәгез"
                else:
                    bot_response = f"(Демо-режим Nemotron) Вы написали: '{user_text}'\nДобавьте OPENROUTER_API_KEY в .env"



        elif current_model == "gptoss":
            model_name = "openai/gpt-oss-120b:free"

            if QWEN_API_KEY:
                bot_response = await call_openrouter_model(
                    api_url=QWEN_API_URL,
                    api_key=QWEN_API_KEY,
                    model="openai/gpt-oss-120b:free",
                    user_text=user_text
                )
            else:
                await asyncio.sleep(1)
                if user_lang == "en":
                    bot_response = f"(gpt-oss demo mode) You wrote: '{user_text}'\nAdd OPENROUTER_API_KEY to .env"
                elif user_lang == "tt":
                    bot_response = f"(gpt-oss демо режимы) Сез яздыгыз: '{user_text}'\nOPENROUTER_API_KEY ны .env ка өстәгез"
                else:
                    bot_response = f"(Демо-режим gpt-oss) Вы написали: '{user_text}'\nДобавьте OPENROUTER_API_KEY в .env"

        if bot_response:
            bot_response = clean_markdown(bot_response)

        await thinking_msg.delete()

        if current_model == "mistral":
            model_emoji = "🌪️"
        elif current_model == "qwen":
            model_emoji = "🤖"
        elif current_model == "zai":
            model_emoji = "🤖"
        elif current_model == "nemotron":
            model_emoji = "🟢"
        elif current_model == "gptoss":
            model_emoji = "🧠"
        else:
            model_emoji = "🤖"

        display_name = {
            "mistral": "Mistral",
            "qwen": "Qwen",
            "zai": "Z AI",
            "nemotron": "Nemotron",
            "gptoss": "gpt-oss",
        }.get(current_model, current_model.capitalize())

        full_text = f"{model_emoji} {display_name}:\n\n{bot_response}"

        await safe_send_long_message(
            message,
            full_text,
            reply_markup=get_exit_ai_inline(user_lang)
        )

        await save_ai_message(user_id, model_name, user_text, bot_response)
        await track_ai_message_sent(user_id)

    except asyncio.TimeoutError:
        try:
            await thinking_msg.delete()
        except Exception:
            pass

        if user_lang == "en":
            error_text = "⏳ The model took too long to respond. Try again or shorten the prompt."
        elif user_lang == "tt":
            error_text = "⏳ Модель җавап бирү өчен артык озак вакыт алды. Кабатлап карагыз яки промптны кыскартыгыз."
        else:
            error_text = "⏳ Модель слишком долго отвечает. Попробуйте ещё раз или сократите промпт."

        await message.answer(error_text, reply_markup=get_exit_ai_inline(user_lang))

    except aiohttp.ClientError as e:
        try:
            await thinking_msg.delete()
        except Exception:
            pass

        if user_lang == "en":
            error_text = f"🌐 Connection error with AI service: {str(e)}"
        elif user_lang == "tt":
            error_text = f"🌐 AI сервисы белән тоташу хатасы: {str(e)}"
        else:
            error_text = f"🌐 Ошибка соединения с AI сервисом: {str(e)}"

        await message.answer(error_text, reply_markup=get_exit_ai_inline(user_lang))

# ==============================================================================
# 13. ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# ==============================================================================

@router.callback_query(F.data == "menu_profile")
async def show_profile(callback: CallbackQuery):
    """Показывает статистику пользователя"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    plan = await sync_subscription_cache(
        user_id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        language=user_lang,
    )

    await ensure_daily_missions(user_id)
    await ensure_permanent_missions(user_id)
    await track_profile_open(user_id)

    stats = await get_user_profile_stats(user_id)
    economy = await get_user_economy(user_id)

    streak_emoji = "🔥" if stats['streak'] > 0 else "💤"
    premium_badge = f"{get_plan_badge(plan.get('plan_tier'))} {get_plan_title(plan.get('plan_tier'), user_lang)}"

    text = get_text(
        user_lang, 'profile',
        user_id=user_id,
        premium_badge=premium_badge,
        coins=economy['coins'],
        streak_emoji=streak_emoji,
        streak=economy['streak'],
        days=stats['days_in_bot']
    )

    text += lt(user_lang, "menu_profile_extra", freeze_count=economy['freeze_count'])
    text += build_profile_plan_block(user_lang, plan)

    await callback.message.edit_text(
        text,
        reply_markup=get_profile_menu_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


# ==============================================================================
# 14. МИССИИ
# ==============================================================================

@router.callback_query(F.data == "menu_missions")
async def show_missions(callback: CallbackQuery):
    """Показывает миссии пользователя"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await ensure_daily_missions(user_id)
    await ensure_permanent_missions(user_id)

    missions = await get_user_missions(user_id)
    economy = await get_user_economy(user_id)

    text = build_missions_text(user_lang, economy, missions)

    await callback.message.edit_text(
        text,
        reply_markup=get_missions_menu_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


# ==============================================================================
# 15. СТРИК И ЗАМОРОЗКА
# ==============================================================================

@router.callback_query(F.data == "menu_streak")
async def show_streak_menu(callback: CallbackQuery):
    """Меню ударного режима"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    plan = await sync_subscription_cache(user_id, language=user_lang)
    economy = await get_user_economy(user_id)

    text = (
        f"{lt(user_lang, 'streak_title')}\n\n"
        f"{lt(user_lang, 'economy_line', coins=economy['coins'], streak=economy['streak'], freeze_count=economy['freeze_count'])}\n\n"
        f"{lt(user_lang, 'streak_desc')}"
    )
    text += st(user_lang, "streak_limit", limit=_limit_text(user_lang, int(plan.get("plan_max_freezes", 2))))

    await callback.message.edit_text(
        text,
        reply_markup=get_streak_menu_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "claim_streak")
async def claim_streak_handler(callback: CallbackQuery):
    """Продлевает ударный режим пользователя"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    result = await claim_daily_streak(user_id)

    if not result["ok"]:
        await callback.answer(result["message"], show_alert=True)
        return

    await track_streak_claim(user_id, result["streak"])

    text = lt(
        user_lang,
        "streak_claimed",
        streak=result["streak"],
        reward=result["reward"],
        freeze_count=result["freeze_count"]
    )

    if result.get("used_freeze"):
        text += lt(user_lang, "freeze_used")

    await callback.message.edit_text(
        text,
        reply_markup=get_streak_menu_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "buy_freeze")
async def buy_freeze_handler(callback: CallbackQuery):
    """Покупка заморозки"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    plan = await sync_subscription_cache(user_id, language=user_lang)

    result = await buy_freeze(user_id, price=30, max_freezes=int(plan.get("plan_max_freezes", 2)))

    if not result["ok"]:
        await callback.answer(result["message"], show_alert=True)
        return

    await track_buy_freeze(user_id)
    await callback.answer(lt(user_lang, "freeze_bought_alert"), show_alert=True)
    await show_streak_menu(callback)

@router.callback_query(F.data == "menu_leaderboard")
async def show_leaderboard_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await callback.message.edit_text(
        lt(user_lang, "leaderboard_title"),
        reply_markup=get_leaderboard_menu_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "leaderboard_coins")
async def show_leaderboard_coins(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    top_users = await get_top_users_by_coins(limit=10)
    my_rank = await get_user_rank_by_coins(user_id)

    text = (
        f"{lt(user_lang, 'leaderboard_coins_title')}\n\n"
        f"{format_leaderboard_lines(top_users, 'coins')}\n\n"
        f"{lt(user_lang, 'your_place', rank=my_rank['rank'] or '—')}\n"
        f"{lt(user_lang, 'your_coins', value=my_rank.get('coins', 0))}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_leaderboard_back_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "leaderboard_streak")
async def show_leaderboard_streak(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    top_users = await get_top_users_by_streak(limit=10)
    my_rank = await get_user_rank_by_streak(user_id)

    text = (
        f"{lt(user_lang, 'leaderboard_streak_title')}\n\n"
        f"{format_leaderboard_lines(top_users, 'streak')}\n\n"
        f"{lt(user_lang, 'your_place', rank=my_rank['rank'] or '—')}\n"
        f"{lt(user_lang, 'your_streak', value=my_rank.get('streak', 0))}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_leaderboard_back_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "leaderboard_best")
async def show_leaderboard_best(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    top_users = await get_top_best_users(limit=10)
    my_rank = await get_user_rank_best(user_id)

    text = (
        f"{lt(user_lang, 'leaderboard_best_title')}\n\n"
        f"{format_best_leaderboard_lines(top_users)}\n\n"
        f"{lt(user_lang, 'your_place', rank=my_rank['rank'] or '—')}\n"
        f"{lt(user_lang, 'your_score', value=my_rank.get('score', 0))}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_leaderboard_back_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()
# ==============================================================================
# 16. НАСТРОЙКИ ЯЗЫКА
# ==============================================================================

async def render_language_menu(callback: CallbackQuery, lang: str):
    """Перерисовывает меню выбора языка с текущей отметкой."""
    await callback.message.edit_text(
        get_text(lang, 'language_menu'),
        reply_markup=get_language_inline(lang),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "menu_language")
async def show_language_menu(callback: CallbackQuery):
    """Показывает меню выбора языка"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await render_language_menu(callback, user_lang)
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery):
    """Изменяет язык и сразу обновляет текущее меню выбора языка."""
    user_id = callback.from_user.id
    new_lang = callback.data.replace("lang_", "")

    if new_lang in ['ru', 'en', 'tt']:
        await set_user_language(user_id, new_lang)
        await render_language_menu(callback, new_lang)

    await callback.answer()


# ==============================================================================
# 17. ЗАГЛУШКИ / ОСТАЛЬНЫЕ РАЗДЕЛЫ
# ==============================================================================

@router.callback_query(F.data == "menu_tariffs")
async def show_tariffs_stub(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    plan = await sync_subscription_cache(
        user_id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        language=user_lang,
    )

    await callback.message.edit_text(
        build_tariffs_text(user_lang, plan),
        reply_markup=get_tariffs_menu_inline(user_lang, normalize_plan_tier(plan.get("plan_tier"))),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "tariff_noop")
async def tariff_noop(callback: CallbackQuery):
    user_lang = await get_user_language(callback.from_user.id)
    await callback.answer(st(user_lang, "noop_included"), show_alert=True)


@router.callback_query(F.data.startswith("tariff_buy:"))
async def tariff_buy(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    tier = normalize_plan_tier(callback.data.split(":", 1)[1])
    current_plan = await sync_subscription_cache(
        user_id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        language=user_lang,
    )

    if has_same_or_higher_plan(current_plan.get("plan_tier"), tier):
        await callback.answer(st(user_lang, "same_or_higher"), show_alert=True)
        return

    plan = get_plan_config(tier)
    stars_price = int(plan["stars_price_month"])
    invoice_payload = build_subscription_payload(user_id, tier, secrets.token_hex(6))
    invoice_link = await callback.bot.create_invoice_link(
        title=f"{get_plan_badge(tier)} {get_plan_title(tier, user_lang)}",
        description="Shared subscription for Prompt Vault website and Telegram bot",
        payload=invoice_payload,
        currency="XTR",
        prices=[LabeledPrice(label=get_plan_title(tier, user_lang), amount=stars_price)],
        subscription_period=SUBSCRIPTION_PERIOD_SECONDS,
    )

    text = (
        f"{get_plan_badge(tier)} **{get_plan_title(tier, user_lang)}**\n\n"
        f"{st(user_lang, 'checkout_ready')}\n\n"
        + "\n".join(f"• {line}" for line in _plan_feature_lines(user_lang, tier))
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_tariff_checkout_inline(user_lang, invoice_link, stars_price),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout_query(query: PreCheckoutQuery):
    payload = parse_subscription_payload(query.invoice_payload)
    is_valid = bool(payload and payload["user_id"] == query.from_user.id)
    if not is_valid:
        await query.answer(ok=False, error_message="Invalid subscription payload.")
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    payment = message.successful_payment
    if payment is None:
        return

    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)
    payload = parse_subscription_payload(payment.invoice_payload)
    if not payload or payload["user_id"] != user_id:
        return

    period_end = None
    if payment.subscription_expiration_date:
        period_end = datetime.fromtimestamp(payment.subscription_expiration_date, tz=timezone.utc).isoformat()

    occurred_at = datetime.now(timezone.utc).isoformat()
    snapshot = await website_activate_stars_subscription(
        telegram_user_id=user_id,
        tier=payload["tier"],
        provider_subscription_id=payload["provider_subscription_id"],
        invoice_payload=payment.invoice_payload,
        telegram_payment_charge_id=payment.telegram_payment_charge_id,
        provider_payment_charge_id=payment.provider_payment_charge_id,
        currency=payment.currency,
        total_amount=payment.total_amount,
        current_period_end=period_end,
        occurred_at=occurred_at,
        is_recurring=bool(payment.is_recurring),
        is_first_recurring=bool(payment.is_first_recurring),
    )

    if snapshot:
        plan = await apply_subscription_snapshot(user_id, snapshot)
        tier = normalize_plan_tier(plan.get("plan_tier"))
        expires = format_expiry(plan.get("plan_expires_at"), user_lang)
        success_text = (
            st(user_lang, "payment_success_expires", badge=get_plan_badge(tier), plan=get_plan_title(tier, user_lang), expires=expires)
            if expires
            else st(user_lang, "payment_success", badge=get_plan_badge(tier), plan=get_plan_title(tier, user_lang))
        )
        await message.answer(success_text, parse_mode="Markdown", reply_markup=get_main_menu_inline(user_lang))
        return

    await notify_admins(
        message.bot,
        (
            "⚠️ Не удалось синхронизировать подписку после оплаты.\n"
            f"User ID: {user_id}\n"
            f"Tier: {payload['tier']}\n"
            f"Invoice payload: {payment.invoice_payload}\n"
            f"Telegram charge: {payment.telegram_payment_charge_id}\n"
            f"Provider charge: {payment.provider_payment_charge_id}"
        ),
    )
    await message.answer(st(user_lang, "payment_failed_sync"), reply_markup=get_main_menu_inline(user_lang))


@router.callback_query(F.data == "menu_games")
async def show_games_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    await sync_subscription_cache(user_id, language=user_lang)

    await state.clear()

    await callback.message.edit_text(
        lt(user_lang, 'games_menu_title'),
        reply_markup=get_games_menu_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


# ==============================================================================
# 18. ОТМЕНА СОСТОЯНИЙ
# ==============================================================================

@router.message(Command("cancel"))
async def cancel_search(message: Message, state: FSMContext):
    """Отменяет текущее состояние (поиск, чат с ИИ)"""
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)

    await state.clear()
    await message.answer(
        get_text(user_lang, 'cancel'),
        reply_markup=get_main_menu_inline(user_lang),
        parse_mode="Markdown"
    )


# ==============================================================================
# 19. ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ
# ==============================================================================

@router.message(Command("help"))
async def help_command(message: Message):
    """Показывает краткую помощь по основным сценариям бота."""
    user_lang = await get_user_language(message.from_user.id)
    await message.answer(
        get_text(user_lang, "help_text"),
        parse_mode="Markdown",
    )


@router.message(Command("news"))
async def news(message: Message):
    await message.answer("📰 Новости сервиса")


@router.message(Command("stickers"))
async def stickers(message: Message):
    await message.answer("https://t.me/addstickers/Souz4_by_fStikBot")


@router.message(Command("report"))
async def report(message: Message):
    await message.answer("📝 Сообщите об ошибке:")


@router.message(Command("ai"))
async def ai_leaderboard(message: Message):
    await message.answer("🏆 Лидеры ИИ: https://arena.ai/leaderboard")


@router.message(Command("sub"))
async def sub_info(message: Message):
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)
    plan = await sync_subscription_cache(
        user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language=user_lang,
    )
    await message.answer(
        build_tariffs_text(user_lang, plan),
        parse_mode="Markdown",
        reply_markup=get_tariffs_menu_inline(user_lang, normalize_plan_tier(plan.get("plan_tier"))),
    )


@router.message(F.text.lower() == "привет")
async def cmd_hello(message: Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    user_lang = await get_user_language(user_id)

    await add_or_update_user(
        user_id=user_id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or ""
    )
    await sync_subscription_cache(
        user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language=user_lang,
    )

    await ensure_daily_missions(user_id)
    await ensure_permanent_missions(user_id)

    await message.answer(
        get_text(user_lang, 'welcome', name=escape(full_name)),
        parse_mode="Markdown",
        reply_markup=get_main_menu_inline(user_lang)
    )


@router.message(Command("site"))
async def site(message: Message):
    await message.answer("наш сайт: https://prompts-vault.ru")


@router.message(Command("about"))
async def about(message: Message):
    await message.answer(
        "Копилка промптов - это (@prompts_souz_bot) ии агрегатор для тестирования промптов.\n\n"
        "Основан в 2026 году.\n\n"
        "Страна: Российская Федерация (Регион: Республика Татарстан)\n\n"
        "Миссия Копилка промптов (КП) состоит в  продвижении информации по промпт инженерии.\n"
        "Копилка промптов стремится придерживаться самых высоких стандартов в подаче материалов.\n\n"
        "Команда (КП): Гимадеев Дамир(@Souzn1k3)."
        "и студент КФУ(ИТИС).\n Лебедев Глеб(@tfmot).\n\n ПО ВСЕМ ВОПРОСАМ (@Souzn1k3)!"
    )


@router.message(Command("moderation"))
async def moderation_panel(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)
    if not is_admin_user(user_id):
        await message.answer(mt(user_lang, "no_access"))
        return

    await state.clear()
    items = await load_moderation_queue(user_id, offset=0)
    await message.answer(
        build_moderation_queue_text(user_lang, items, offset=0),
        reply_markup=get_moderation_queue_inline(items, offset=0),
    )


@router.callback_query(F.data.startswith("mod:queue"))
async def moderation_queue_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    if not is_admin_user(user_id):
        await callback.answer(mt(user_lang, "no_access"), show_alert=True)
        return

    await state.clear()
    parts = (callback.data or "").split(":")
    offset = 0
    if len(parts) >= 3:
        try:
            offset = max(int(parts[2]), 0)
        except ValueError:
            offset = 0

    items = await load_moderation_queue(user_id, offset=offset)
    await callback.message.edit_text(
        build_moderation_queue_text(user_lang, items, offset=offset),
        reply_markup=get_moderation_queue_inline(items, offset=offset),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mod:open:"))
async def moderation_open_prompt(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    if not is_admin_user(user_id):
        await callback.answer(mt(user_lang, "no_access"), show_alert=True)
        return

    await state.clear()
    prompt_id = (callback.data or "").split(":", 2)[2]
    prompt = await website_get_moderation_prompt(
        prompt_id,
        acting_telegram_user_id=user_id,
    )
    if not prompt:
        await callback.answer(mt(user_lang, "load_failed"), show_alert=True)
        return

    reply_markup = (
        get_moderation_card_inline(prompt_id)
        if prompt.get("moderation_state") == "pending"
        else get_moderation_done_inline(prompt_id)
    )
    await callback.message.edit_text(
        build_moderation_card_text(user_lang, prompt),
        reply_markup=reply_markup,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mod:approve:"))
async def moderation_approve(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    if not is_admin_user(user_id):
        await callback.answer(mt(user_lang, "no_access"), show_alert=True)
        return

    await state.clear()
    prompt_id = (callback.data or "").split(":", 2)[2]
    decision = await website_moderate_prompt(
        prompt_id,
        acting_telegram_user_id=user_id,
        action="approve",
    )
    if not decision:
        await callback.answer(mt(user_lang, "decision_failed"), show_alert=True)
        return

    prompt = await website_get_moderation_prompt(prompt_id, acting_telegram_user_id=user_id)
    if prompt:
        await callback.message.edit_text(
            build_moderation_card_text(user_lang, prompt),
            reply_markup=get_moderation_done_inline(prompt_id),
        )
    await callback.answer(mt(user_lang, "comment_saved"))


@router.callback_query(F.data.startswith("mod:approvec:"))
async def moderation_approve_comment(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    if not is_admin_user(user_id):
        await callback.answer(mt(user_lang, "no_access"), show_alert=True)
        return

    prompt_id = (callback.data or "").split(":", 2)[2]
    await state.set_state(ModerationCommentState.waiting_for_comment)
    await state.update_data(moderation_prompt_id=prompt_id, moderation_action="approve")
    await callback.message.answer(mt(user_lang, "comment_prompt_approve"))
    await callback.answer()


@router.callback_query(F.data.startswith("mod:reject:"))
async def moderation_reject_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    if not is_admin_user(user_id):
        await callback.answer(mt(user_lang, "no_access"), show_alert=True)
        return

    await state.clear()
    prompt_id = (callback.data or "").split(":", 2)[2]
    prompt = await website_get_moderation_prompt(prompt_id, acting_telegram_user_id=user_id)
    if not prompt:
        await callback.answer(mt(user_lang, "load_failed"), show_alert=True)
        return

    await callback.message.edit_text(
        build_moderation_card_text(user_lang, prompt),
        reply_markup=get_reject_reason_inline(prompt_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mod:reason:"))
async def moderation_reject_reason(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    if not is_admin_user(user_id):
        await callback.answer(mt(user_lang, "no_access"), show_alert=True)
        return

    await state.clear()
    _, _, prompt_id, reason_code = (callback.data or "").split(":", 3)
    decision = await website_moderate_prompt(
        prompt_id,
        acting_telegram_user_id=user_id,
        action="reject",
        reason=moderation_reason_text(reason_code, user_lang),
    )
    if not decision:
        await callback.answer(mt(user_lang, "decision_failed"), show_alert=True)
        return

    prompt = await website_get_moderation_prompt(prompt_id, acting_telegram_user_id=user_id)
    if prompt:
        await callback.message.edit_text(
            build_moderation_card_text(user_lang, prompt),
            reply_markup=get_moderation_done_inline(prompt_id),
        )
    await callback.answer(mt(user_lang, "comment_saved"))


@router.callback_query(F.data.startswith("mod:rejectc:"))
async def moderation_reject_comment(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)
    if not is_admin_user(user_id):
        await callback.answer(mt(user_lang, "no_access"), show_alert=True)
        return

    prompt_id = (callback.data or "").split(":", 2)[2]
    await state.set_state(ModerationCommentState.waiting_for_comment)
    await state.update_data(moderation_prompt_id=prompt_id, moderation_action="reject")
    await callback.message.answer(mt(user_lang, "comment_prompt_reject"))
    await callback.answer()


@router.message(ModerationCommentState.waiting_for_comment, F.text)
async def moderation_comment_input(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)
    if not is_admin_user(user_id):
        await state.clear()
        await message.answer(mt(user_lang, "no_access"))
        return

    comment = (message.text or "").strip()
    if not comment:
        await message.answer(mt(user_lang, "decision_failed"))
        return

    data = await state.get_data()
    prompt_id = data.get("moderation_prompt_id")
    action = data.get("moderation_action")
    if not prompt_id or action not in {"approve", "reject"}:
        await state.clear()
        await message.answer(mt(user_lang, "decision_failed"))
        return

    decision = await website_moderate_prompt(
        str(prompt_id),
        acting_telegram_user_id=user_id,
        action=action,
        reason=comment,
    )
    if not decision:
        await message.answer(mt(user_lang, "decision_failed"))
        return

    await state.clear()
    prompt = await website_get_moderation_prompt(str(prompt_id), acting_telegram_user_id=user_id)
    if not prompt:
        await message.answer(mt(user_lang, "comment_saved"))
        return

    await message.answer(
        build_moderation_card_text(user_lang, prompt),
        reply_markup=get_moderation_done_inline(str(prompt_id)),
    )


@router.message(Command("prompt"))
async def prompt_review_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)

    await state.set_state(PromptReviewState.waiting_for_prompt)
    await message.answer(get_text(user_lang, "prompt_review_start"))


@router.message(PromptReviewState.waiting_for_prompt, F.text)
async def process_prompt_review_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)

    if not message.text or not message.text.strip():
        await message.answer(get_text(user_lang, "prompt_review_empty"))
        return

    username = f"@{message.from_user.username}" if message.from_user.username else "без username"
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()

    admin_text = (
        "📩 Новый промпт на редакцию\n\n"
        f"👤 Пользователь: {full_name}\n"
        f"🆔 ID: {user_id}\n"
        f"🔗 Username: {username}\n"
        f"📝 Источник: текст\n\n"
        f"📝 Промпт:\n{message.text}"
    )

    try:
        await notify_admins(message.bot, admin_text)
        await message.answer(get_text(user_lang, "prompt_review_sent"))
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить промпт на редакцию: {e}")


@router.message(PromptReviewState.waiting_for_prompt, F.voice)
async def process_prompt_review_voice(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)
    file_path = f"temp_voice_{user_id}.ogg"

    if message.voice.duration > 180:
        await message.answer(get_text(user_lang, "prompt_review_voice_too_long"))
        return

    await message.answer(get_text(user_lang, "prompt_review_voice_processing"))

    try:
        file = await message.bot.get_file(message.voice.file_id)
        await message.bot.download_file(file.file_path, destination=file_path)
        text = await transcribe_voice_to_text(file_path)

        if not text.strip():
            await message.answer(get_text(user_lang, "prompt_review_voice_failed"))
            return

        username = f"@{message.from_user.username}" if message.from_user.username else "без username"
        full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        admin_text = (
            "📩 Новый промпт на редакцию\n\n"
            f"👤 Пользователь: {full_name}\n"
            f"🆔 ID: {user_id}\n"
            f"🔗 Username: {username}\n"
            f"🎙 Источник: голос\n\n"
            f"📝 Распознанный текст:\n{text}"
        )

        await notify_admins(message.bot, admin_text)
        await message.answer(f"{get_text(user_lang, 'prompt_review_sent')}\n\n📝 {text}")
        await state.clear()
    except Exception as e:
        await message.answer(f"{get_text(user_lang, 'prompt_review_voice_failed')}\n\n{e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    # Пока просто заглушка под speech-to-text
    # Здесь следующим шагом мы добавим:
    # 1. скачивание voice
    # 2. распознавание в текст
    # 3. отправку тебе как обычного промпта
#
# # ==============================================================================
# # 1. КОНФИГУРАЦИЯ И СОСТОЯНИЯ
# # ==============================================================================
#
# # Ключ API для Mistral (Получить на https://console.mistral.ai/)
# # Если ключа нет, бот будет работать в демо-режиме (отвечать заглушками)
# MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
# MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
#
# # ✅ QWEN API (НОВОЕ!)
# QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
# QWEN_API_URL = "https://openrouter.ai/api/v1/chat/completions"
#
# class AIChatState(StatesGroup):
#     waiting_for_message = State()  # Состояние активного диалога с ИИ
#     current_model = State()
# # ✅ НОВОЕ: Состояния для ПОИСКА
# class SearchState(StatesGroup):
#     waiting_for_query = State()
#
# # ==============================================================================
# # 2. КЛАВИАТУРЫ (Новая структура меню)
# # ==============================================================================
#
# def get_main_menu_inline():
#     """Главное меню бота (6 кнопок)"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="🤖 Каталог ИИ", callback_data="menu_catalog_ai")],
#         [InlineKeyboardButton(text="🔍 Поиск", callback_data="menu_search"),
#          InlineKeyboardButton(text="💎 Тарифы", callback_data="menu_tariffs")],
#         [InlineKeyboardButton(text="🎯 Миссии", callback_data="menu_missions"),
#          InlineKeyboardButton(text="🎮 Игры", callback_data="menu_games")],
#         [InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile")],
#     ])
#
#
# AI_MODELS_DB = [
#     {"id": "mistral", "name": "🌪️ Mistral AI", "description": "Быстрая и эффективная модель от Mistral"},
#     {"id": "qwen", "name": "🤖 Qwen AI", "description": "Умная модель от Alibaba с глубоким пониманием контекста"},
#     {"id": "gemini", "name": "💎 Gemini Pro", "description": "Мультимодальная модель от Google"},
#     {"id": "gpt4", "name": "🧠 GPT-4", "description": "Продвинутая модель от OpenAI"},
#     {"id": "claude", "name": "🤖 Claude 3", "description": "Безопасная и мощная модель от Anthropic"},
#     {"id": "llama", "name": "🦙 Llama 3", "description": "Открытая модель от Meta"},
#     {"id": "cohere", "name": "📊 Cohere", "description": "Модель для работы с текстом"},
#     {"id": "palm", "name": "🔮 PaLM 2", "description": "Языковая модель от Google"},
#     {"id": "stable", "name": "🎨 Stable Diffusion", "description": "Генерация изображений"},
# ]
#
#
#
# def get_catalog_ai_inline():
#     """Меню выбора модели ИИ"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text=" Mistral AI", callback_data="ai_model_mistral")],
#         [InlineKeyboardButton(text="🤖 Qwen AI", callback_data="ai_model_qwen")],
#         [InlineKeyboardButton(text=" Gemini Pro", callback_data="ai_model_gemini_pro")],
#         [InlineKeyboardButton(text=" Gigachat", callback_data="ai_model_gigachat")],
#         [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_main_menu")]
#     ])
#
#
# def get_exit_ai_inline():
#     """Кнопка выхода из режима чата с ИИ"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="🔙 Завершить сессию", callback_data="exit_ai_chat")]
#     ])
#
#
# def get_profile_menu_inline():
#     """Меню профиля"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="🔄 Обновить", callback_data="menu_profile")],
#         [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main_menu")],
#     ])
#
# # ✅ НОВАЯ: Клавиатура с результатами поиска
# def get_search_results_inline(results: list):
#     """Создаёт инлайн-кнопки с результатами поиска"""
#     keyboard = []
#     for model in results:
#         keyboard.append([InlineKeyboardButton(
#             text=model["name"],
#             callback_data=f"search_select_{model['id']}"
#         )])
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_main_menu")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# # ✅ НОВАЯ: Клавиатура для конкретной модели
# def get_model_detail_inline(model_id: str):
#     """Клавиатура для выбранной модели"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="🚀 Запустить модель", callback_data=f"launch_model_{model_id}")],
#         [InlineKeyboardButton(text="🔙 Назад к поиску", callback_data="menu_search")],
#         [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_main_menu")],
#     ])
#
#
# # ==============================================================================
# # 3. ХЕНДЛЕРЫ НАВИГАЦИИ
# # ==============================================================================
#
# @router.message(CommandStart())
# async def cmd_start(message: Message):
#     """Главное меню бота при запуске"""
#     user_id = message.from_user.id
#     full_name = message.from_user.full_name
#
#     # 1. Регистрируем пользователя и обновляем стрик в БД
#     await add_or_update_user(
#         user_id=user_id,
#         username=message.from_user.username or "",
#         first_name=message.from_user.first_name or "",
#         last_name=message.from_user.last_name or ""
#     )
#
#     # 2. Очищаем состояние FSM (на случай если застрял в поиске или чате)
#     await message.bot.delete_my_commands()  # Опционально
#
#     # 3. Отправляем приветствие
#     await message.answer(
#          f"👋 **Привет, {escape(full_name)}!**\n\n"
#          f"Это **Копилка Промптов** - профессиональный каталог\nпромптов и техник:\n"
#          f"от zero-shot до chain-of-thought,\n"
#          f"организованный для обучения и реальных задач.",
#          parse_mode="Markdown",
#          reply_markup=get_main_menu_inline()
#      )
#
#
# @router.callback_query(F.data == "back_main_menu")
# async def back_to_main(callback: CallbackQuery, state: FSMContext):
#     """Возврат в главное меню из любого раздела"""
#     await state.clear()  # Сбрасываем любые активные состояния (чат, поиск)
#     await callback.message.edit_text(
#         "🏠 **Главное меню**",
#         reply_markup=get_main_menu_inline(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # --- КАТАЛОГ ИИ ---
# @router.callback_query(F.data == "menu_catalog_ai")
# async def show_catalog_ai(callback: CallbackQuery):
#     """Показывает доступные модели ИИ"""
#     await callback.message.edit_text(
#         "🤖 **Каталог Искусственного Интеллекта**\n\n"
#         "Выберите модель для начала работы:",
#         reply_markup=get_catalog_ai_inline(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # ==============================================================================
# # НОВЫЕ ХЕНДЛЕРЫ: НАСТРОЙКИ УВЕДОМЛЕНИЙ
# # ==============================================================================
#
# @router.callback_query(F.data == "menu_notifications")
# async def show_notifications_settings(callback: CallbackQuery):
#     """Показывает настройки уведомлений"""
#     user_id = callback.from_user.id
#     settings = await get_user_notification_settings(user_id)
#
#     # Формируем текст с эмодзи статуса
#     status = "✅ ВКЛ" if settings['is_enabled'] else "❌ ВЫКЛ"
#     daily = "🔔" if settings['daily_reminder'] else "🔕"
#     news = "📰" if settings['news'] else "📰❌"
#     missions = "🎯" if settings['missions'] else "🎯❌"
#
#     text = (
#         f"🔔 **Настройки уведомлений**\n\n"
#         f"Общий статус: **{status}**\n\n"
#         f"Параметры:\n"
#         f"{daily} Ежедневные напоминания\n"
#         f"{news} Новости сервиса\n"
#         f"{missions} Миссии и задания\n\n"
#         f"Управляйте нажатием на кнопки:"
#     )
#
#     await callback.message.edit_text(
#         text,
#         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(
#                 text="🔘 Общие: " + ("ВКЛ ✅" if settings['is_enabled'] else "ВЫКЛ ❌"),
#                 callback_data="notif_toggle_main"
#             )],
#             [InlineKeyboardButton(
#                 text=daily + " Ежедневные",
#                 callback_data="notif_toggle_daily"
#             ),
#                 InlineKeyboardButton(
#                     text=news + " Новости",
#                     callback_data="notif_toggle_news"
#                 )],
#             [InlineKeyboardButton(
#                 text=missions + " Миссии",
#                 callback_data="notif_toggle_missions"
#             )],
#             [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_profile")],
#         ]),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # Обработчики переключения настроек
# @router.callback_query(F.data == "notif_toggle_main")
# async def toggle_main_notif(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     settings = await get_user_notification_settings(user_id)
#     new_value = not settings['is_enabled']
#     await update_notification_setting(user_id, 'is_enabled', new_value)
#     await show_notifications_settings(callback)
#     await callback.answer(f"Уведомления {'включены' if new_value else 'выключены'}")
#
#
# @router.callback_query(F.data == "notif_toggle_daily")
# async def toggle_daily_notif(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     settings = await get_user_notification_settings(user_id)
#     new_value = not settings['daily_reminder']
#     await update_notification_setting(user_id, 'daily_reminder', new_value)
#     await show_notifications_settings(callback)
#     await callback.answer()
#
#
# @router.callback_query(F.data == "notif_toggle_news")
# async def toggle_news_notif(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     settings = await get_user_notification_settings(user_id)
#     new_value = not settings['news']
#     await update_notification_setting(user_id, 'news', new_value)
#     await show_notifications_settings(callback)
#     await callback.answer()
#
#
# @router.callback_query(F.data == "notif_toggle_missions")
# async def toggle_missions_notif(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     settings = await get_user_notification_settings(user_id)
#     new_value = not settings['missions']
#     await update_notification_setting(user_id, 'missions', new_value)
#     await show_notifications_settings(callback)
#     await callback.answer()
#
#
# # Добавь кнопку в профиль
# # В функции show_profile добавь в клавиатуру:
# # [InlineKeyboardButton(text="🔔 Уведомления", callback_data="menu_notifications")]
#
# # ==============================================================================
# # АДМИНКА: РАССЫЛКА
# # ==============================================================================
#
# @router.message(Command("broadcast"))
# async def broadcast_command(message: Message, bot):
#     """Команда для рассылки сообщений всем пользователям (ТОЛЬКО ДЛЯ АДМИНА)"""
#     ADMIN_ID = 123456789  # ⚠️ ЗАМЕНИ НА СВОЙ TELEGRAM ID
#
#     if message.from_user.id != ADMIN_ID:
#         return
#
#     if not message.reply_to_message:
#         await message.answer("❌ Используйте как ответ на сообщение для рассылки")
#         return
#
#     users = await get_all_active_users()
#     success = 0
#     blocked = 0
#
#     await message.answer(f"🚀 Начинаю рассылку для {len(users)} пользователей...")
#
#     for user_id in users:
#         try:
#             await message.reply_to_message.copy(chat_id=user_id)
#             success += 1
#             await asyncio.sleep(0.05)  # Защита от лимитов
#         except Exception:
#             blocked += 1
#
#     await message.answer(f"✅ Готово!\nУспешно: {success}\nЗаблокировано: {blocked}")
#
#
# # ==============================================================================
# # 5. ✅ ПОИСК ПО AI МОДЕЛЯМ (НОВАЯ ФУНКЦИОНАЛЬНОСТЬ)
# # ==============================================================================
# @router.callback_query(F.data == "menu_search")
# async def menu_search(callback: CallbackQuery, state: FSMContext):
#     """Показывает меню поиска и включает режим поиска"""
#     await state.set_state(SearchState.waiting_for_query)
#     await callback.message.edit_text(
#         "🔍 **Поиск AI моделей**\n\n"
#         "Введите название модели для поиска:\n\n"
#         "Примеры:\n"
#         "• `mistral` → Mistral AI\n"
#         "• `gemini` → Gemini Pro\n"
#         "• `gpt` → GPT-4\n"
#         "• `claude` → Claude 3\n"
#         "• `llama` → Llama 3\n\n"
#         "⌨️ Просто напишите слово в чат:\n\n"
#         "❌ Чтобы отменить поиск, нажмите /cancel",
#         parse_mode="Markdown",
#         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_main_menu")]
#         ])
#     )
#     await callback.answer()
#
#
# @router.message(SearchState.waiting_for_query)
# async def process_search_query(message: Message, state: FSMContext):
#     """Обрабатывает поисковый запрос и показывает результаты"""
#     query = message.text.lower().strip()
#
#     # ✅ Ищем совпадения в базе моделей
#     results = [
#         model for model in AI_MODELS_DB
#         if query in model["id"].lower() or query in model["name"].lower() or query in model["description"].lower()
#     ]
#
#     if not results:
#         # Ничего не найдено
#         await message.answer(
#             f"❌ **Ничего не найдено по запросу \"{escape(query)}\"**\n\n"
#             "Попробуйте другой запрос:\n"
#             "• mistral\n"
#             "• gemini\n"
#             "• gpt\n"
#             "• claude\n"
#             "• llama",
#             parse_mode="Markdown",
#             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                 [InlineKeyboardButton(text="🔙 Повторить поиск", callback_data="menu_search")],
#                 [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_main_menu")],
#             ])
#         )
#     else:
#         # Найдены результаты
#         results_text = "\n".join([f"• {m['name']} — {m['description']}" for m in results])
#         await message.answer(
#             f"✅ **Найдено моделей: {len(results)}**\n\n"
#             f"{results_text}\n\n"
#             "Выберите модель из списка ниже 👇",
#             parse_mode="Markdown",
#             reply_markup=get_search_results_inline(results)
#         )
#
#     # ✅ Сбрасываем состояние поиска
#     await state.clear()
#
#
# # ✅ НОВАЯ: Обработка выбора модели из поиска
# @router.callback_query(F.data.startswith("search_select_"))
# async def select_model_from_search(callback: CallbackQuery, state: FSMContext):
#     """Показывает детали выбранной модели"""
#     model_id = callback.data.replace("search_select_", "")
#     model = next((m for m in AI_MODELS_DB if m["id"] == model_id), None)
#
#     if model:
#         await callback.message.edit_text(
#             f"🤖 **{model['name']}**\n\n"
#             f"{model['description']}\n\n"
#             f"**ID модели:** `{model_id}`\n\n"
#             "Готовы запустить эту модель?",
#             parse_mode="Markdown",
#             reply_markup=get_model_detail_inline(model_id)
#         )
#     else:
#         await callback.message.edit_text(
#             "❌ **Модель не найдена**",
#             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                 [InlineKeyboardButton(text="🔙 Назад к поиску", callback_data="menu_search")],
#                 [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_main_menu")],
#             ]),
#             parse_mode="Markdown"
#         )
#
#     await callback.answer()
#
#
# # ✅ НОВАЯ: Запуск выбранной модели
# @router.callback_query(F.data.startswith("launch_model_"))
# async def launch_model_from_search(callback: CallbackQuery, state: FSMContext):
#     model_id = callback.data.replace("launch_model_", "")
#     model = next((m for m in AI_MODELS_DB if m["id"] == model_id), None)
#
#     if model:
#         if model_id in ["mistral", "qwen"]:  # ✅ Теперь работают обе модели!
#             await state.set_state(AIChatState.waiting_for_message)
#             await state.update_data(current_model=model_id)
#             await callback.message.edit_text(
#                 f"{model['name']} **Активирован**\n\n"
#                 f"Теперь я слушаю вас. Напишите любой запрос, и нейросеть ответит.\n"
#                 f"💰 *Стоимость сообщения: 1 коин*",
#                 reply_markup=get_exit_ai_inline(),
#                 parse_mode="Markdown"
#             )
#         else:
#             await callback.message.edit_text(
#                 f"🚧 **{model['name']}**\n\n"
#                 f"Эта модель скоро будет доступна!\n"
#                 f"Попробуйте Mistral AI или Qwen AI для тестирования.\n\n"
#                 f"{model['description']}",
#                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                     [InlineKeyboardButton(text="🔙 Назад к поиску", callback_data="menu_search")],
#                     [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_main_menu")],
#                 ]),
#                 parse_mode="Markdown"
#             )
#     else:
#         await callback.message.edit_text(
#             "❌ **Ошибка запуска модели**",
#             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                 [InlineKeyboardButton(text="🔙 Назад к поиску", callback_data="menu_search")],
#             ]),
#             parse_mode="Markdown"
#         )
#     await callback.answer()
#
#
#
# # --- ЗАПУСК MISTRAL AI ---
# @router.callback_query(F.data == "ai_model_mistral")
# async def start_mistral_chat(callback: CallbackQuery, state: FSMContext):
#     """Активирует режим диалога с Mistral"""
#     await state.set_state(AIChatState.waiting_for_message)
#     await state.update_data(current_model="mistral")
#     await callback.message.edit_text(
#         "🌪️ **Mistral AI Активирован**\n\n"
#         "Теперь я слушаю вас. Напишите любой запрос, и нейросеть ответит.\n"
#         "💰 *Стоимость сообщения: 1 коин*",
#         reply_markup=get_exit_ai_inline(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# # ✅ НОВОЕ: Запуск Qwen AI
# @router.callback_query(F.data == "ai_model_qwen")
# async def start_qwen_chat(callback: CallbackQuery, state: FSMContext):
#     await state.set_state(AIChatState.waiting_for_message)
#     await state.update_data(current_model="qwen")
#     await callback.message.edit_text(
#         "🤖 **Qwen AI Активирован**\n\n"
#         "Теперь я слушаю вас. Напишите любой запрос, и нейросеть ответит.\n"
#         "💰 *Стоимость сообщения: 1 коин*",
#         reply_markup=get_exit_ai_inline(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # --- ВЫХОД ИЗ ЧАТА С ИИ ---
# @router.callback_query(F.data == "exit_ai_chat")
# async def exit_mistral_chat(callback: CallbackQuery, state: FSMContext):
#     """Выход из режима диалога"""
#     await state.clear()
#     await callback.message.edit_text(
#         "🛑 **Сессия завершена**\n\nВы вернулись в главное меню.",
#         reply_markup=get_main_menu_inline(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # --- ОБРАБОТКА СООБЩЕНИЙ ДЛЯ ИИ (FSM) ---
# @router.message(AIChatState.waiting_for_message)
# async def handle_ai_message(message: Message, state: FSMContext):
#     user_text = message.text
#     user_id = message.from_user.id
#
#     # Получаем текущую модель из состояния
#     state_data = await state.get_data()
#     current_model = state_data.get("current_model", "mistral")
#
#     thinking_msg = await message.answer("🤔 *Нейросеть думает...*...", parse_mode="Markdown")
#
#     try:
#         bot_response = ""
#         model_name = ""
#
#         # ✅ MISTRAL AI
#         if current_model == "mistral":
#             model_name = "mistral-small"
#             if MISTRAL_API_KEY:
#                 async with aiohttp.ClientSession() as session:
#                     headers = {
#                         "Authorization": f"Bearer {MISTRAL_API_KEY}",
#                         "Content-Type": "application/json"
#                     }
#                     payload = {
#                         "model": "mistral-small",
#                         "messages": [{"role": "user", "content": user_text}]
#                     }
#                     async with session.post(MISTRAL_API_URL, json=payload, headers=headers) as resp:
#                         if resp.status == 200:
#                             data = await resp.json()
#                             bot_response = data['choices'][0]['message']['content']
#                         else:
#                             bot_response = "⚠️ Ошибка API Mistral. Попробуйте позже."
#             else:
#                 await asyncio.sleep(1)
#                 bot_response = f"(Демо-режим Mistral) Вы написали: '{user_text}'"
#
#
#         # ✅ QWEN AI через OPENROUTER (ИСПРАВЛЕНО!)
#         elif current_model == "qwen":
#             model_name = "qwen/qwen-2.5-7b-instruct"  # ✅ Формат OpenRouter
#             if QWEN_API_KEY:
#                 async with aiohttp.ClientSession() as session:
#                     headers = {
#                         "Authorization": f"Bearer {QWEN_API_KEY}",
#                         "Content-Type": "application/json",
#                         "HTTP-Referer": "https://your-bot.com",  # ✅ Требуется OpenRouter
#                         "X-Title": "AI Hub Bot"  # ✅ Требуется OpenRouter
#                     }
#                     payload = {
#                         "model": "qwen/qwen-2.5-7b-instruct",  # ✅ Формат OpenRouter
#                         "messages": [{"role": "user", "content": user_text}]
#                     }
#                     async with session.post(QWEN_API_URL, json=payload, headers=headers) as resp:
#                         # ✅ Логирование ответа для отладки
#                         print(f"📡 OpenRouter Status: {resp.status}")
#
#                         if resp.status == 200:
#                             data = await resp.json()
#                             print(f"📦 OpenRouter Response: {data}")  # ✅ Смотрим структуру
#
#                             # ✅ Безопасное получение ответа
#                             try:
#                                 bot_response = data['choices'][0]['message']['content']
#                             except KeyError as e:
#                                 print(f"❌ KeyError: {e}")
#                                 print(f"📦 Data keys: {data.keys()}")
#                                 bot_response = f"⚠️ Ошибка формата ответа: {str(e)}"
#                         else:
#                             error_text = await resp.text()
#                             bot_response = f"⚠️ Ошибка API Qwen: {resp.status}\n{error_text}"
#                             print(f"❌ Qwen Error: {error_text}")
#             else:
#                 await asyncio.sleep(1)
#                 bot_response = f"(Демо-режим Qwen) Вы написали: '{user_text}'\nДобавьте OPENROUTER_API_KEY в .env"
#
#         await thinking_msg.delete()
#
#         # Определяем эмодзи модели для ответа
#         model_emoji = "🌪️" if current_model == "mistral" else "🤖"
#
#         await message.answer(
#             f"{model_emoji} **{current_model.capitalize()}:**\n\n{escape(bot_response)}",
#             parse_mode="Markdown",
#             reply_markup=get_exit_ai_inline()
#         )
#
#         await save_ai_message(user_id, model_name, user_text, bot_response)
#
#     except Exception as e:
#         await thinking_msg.delete()
#         await message.answer(f"❌ Произошла ошибка: {str(e)}", reply_markup=get_exit_ai_inline())
#
#
# # --- ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ---
# @router.callback_query(F.data == "menu_profile")
# async def show_profile(callback: CallbackQuery):
#     """Показывает статистику пользователя"""
#     user_id = callback.from_user.id
#     stats = await get_user_profile_stats(user_id)
#
#     # Эмодзи для стрика
#     streak_emoji = "🔥" if stats['streak'] > 0 else "💤"
#     premium_badge = "💎 Premium" if stats['is_premium'] else "🆓 Free"
#
#     text = (
#         f"👤 **Профиль пользователя**\n\n"
#         f"ID: `{user_id}`\n"
#         f"Статус: {premium_badge}\n\n"
#         f"📊 **Ваши достижения**:\n"
#         f"🪙 Баланс: **{stats['coins']}** койнов\n"
#         f"{streak_emoji} Ударный режим: **{stats['streak']}** дн.\n"
#         f"📅 В боте: **{stats['days_in_bot']}** дн.\n\n"
#         f"Выполняйте миссии и общайтесь с ИИ, чтобы зарабатывать!"
#     )
#
#     await callback.message.edit_text(
#         text,
#         reply_markup=get_profile_menu_inline(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # --- ЗАГЛУШКИ ДЛЯ ОСТАЛЬНЫХ РАЗДЕЛОВ ---
# @router.callback_query(F.data == "menu_search")
# async def show_search_stub(callback: CallbackQuery):
#     await callback.message.edit_text("🔍 **Поиск**\n\nФункционал в разработке...", reply_markup=get_main_menu_inline(),
#                                      parse_mode="Markdown")
#     await callback.answer()
#
#
# @router.callback_query(F.data == "menu_tariffs")
# async def show_tariffs_stub(callback: CallbackQuery):
#     await callback.message.edit_text("💎 **Подписки**\n\nуровни подписки: Ваш на данный момент: free\n\n\nfree: 0 руб/мес\nstarter: 200 руб/мес\npro: 500 руб/мес\nMAX 600 руб/мес",
#                                      reply_markup=get_main_menu_inline(), parse_mode="Markdown")
#     await callback.answer()
#
#
# @router.callback_query(F.data == "menu_missions")
# async def show_missions_stub(callback: CallbackQuery):
#     await callback.message.edit_text("🎯 **Миссии**\n\nЕжедневные задания появятся здесь.",
#                                      reply_markup=get_main_menu_inline(), parse_mode="Markdown")
#     await callback.answer()
#
#
# @router.callback_query(F.data == "menu_games")
# async def show_games_stub(callback: CallbackQuery):
#     await callback.message.edit_text("🎮 **Игры**\n\nМини-игры для заработка койнов в разработке.",
#                                      reply_markup=get_main_menu_inline(), parse_mode="Markdown")
#     await callback.answer()
#
#
# # ==============================================================================
# # 6. ✅ ОТМЕНА ПОИСКА (COMMAND /cancel)
# # ==============================================================================
# @router.message(Command("cancel"))
# async def cancel_search(message: Message, state: FSMContext):
#     """Отменяет текущее состояние (поиск, чат с ИИ)"""
#     await state.clear()
#     await message.answer(
#         "❌ **Поиск отменён**\n\nВы вернулись в главное меню.",
#         reply_markup=get_main_menu_inline(),
#         parse_mode="Markdown"
#     )
#
#
#
# @router.message(Command("news"))
# async def news(message: Message):
#     await message.answer("новости сервиса")
#
#
# @router.message(Command("stickers"))
# async def stickers(message: Message):
#     await message.answer("https://t.me/addstickers/Souz4_by_fStikBot")
#
# @router.message(Command("report"))
# async def site(message: Message):
#     await message.answer("собщите об ошибке:")
#
# @router.message(Command("help"))
# async def site(message: Message):
#      await message.answer("опишите проблему: ")
#
# @router.message(Command("ai"))
# async def site(message: Message):
#      await message.answer("лидеры: https://arena.ai/leaderboard ")
#
# @router.message(Command("sub"))
# async def site(message: Message):
#      await message.answer("уровни подписки: Ваш на данный момент: free\n\n\nfree: 0 руб/мес\nstarter: 200 руб/мес\npro: 500 руб/мес\nMAX 600 руб/мес ")
#
# @router.message(F.text.lower() == "привет")
# async def cmd_start(message: Message):
#     """Главное меню бота при запуске"""
#     user_id = message.from_user.id
#     full_name = message.from_user.full_name
#
#     # 1. Регистрируем пользователя и обновляем стрик в БД
#     await add_or_update_user(
#         user_id=user_id,
#         username=message.from_user.username or "",
#         first_name=message.from_user.first_name or "",
#         last_name=message.from_user.last_name or ""
#     )
#
#     # 2. Очищаем состояние FSM (на случай если застрял в поиске или чате)
#     await message.bot.delete_my_commands()  # Опционально
#
#     # 3. Отправляем приветствие
#     await message.answer(
#          f"👋 **Привет, {escape(full_name)}!**\n\n"
#          f"Это **Копилка Промптов** - профессиональный каталог\nпромптов и техник:\n"
#          f"от zero-shot до chain-of-thought,\n"
#          f"организованный для обучения и реальных задач.",
#          parse_mode="Markdown",
#          reply_markup=get_main_menu_inline()
#      )



# router = Router()
#
# # ==============================================================================
# # FSM СОСТОЯНИЯ ДЛЯ ПОИСКА
# # ==============================================================================
# class SearchState(StatesGroup):
#     waiting_for_query = State()  # Ожидание поискового запроса
#
#
# # ==============================================================================
# # 1. КОНФИГУРАЦИЯ (Единственный источник правды)
# # ==============================================================================
#
# # Уникальные ID для каждой категории. Это ключ к работе кнопок.
# CATEGORIES_CALLBACKS_RU = {
#     "it": "cat_it_ru",
#     "marketing": "cat_marketing_ru",
#     "business": "cat_business_ru",
#     "education": "cat_edu_ru",
#     "arts": "cat_arts_ru",
#     "engineering": "cat_eng_ru",
#     "finance": "cat_fin_ru",
#     "law": "cat_law_ru",
#     "agro": "cat_agro_ru",
#     "logistics": "cat_log_ru",
#     "real_estate": "cat_re_ru",
#     "lifestyle": "cat_life_ru",
#     "niche": "cat_niche_ru",
# }
#
# CATEGORIES_CALLBACKS_TAT = {
#     "it": "cat_it_tat",
#     "marketing": "cat_marketing_tat",
#     "business": "cat_business_tat",
#     "education": "cat_edu_tat",
#     "arts": "cat_arts_tat",
#     "engineering": "cat_eng_tat",
#     "finance": "cat_fin_tat",
#     "law": "cat_law_tat",
#     "agro": "cat_agro_tat",
#     "logistics": "cat_log_tat",
#     "real_estate": "cat_re_tat",
#     "lifestyle": "cat_life_tat",
#     "niche": "cat_niche_tat",
# }
#
# CATEGORIES_CALLBACKS_ENG = {
#     "it": "cat_it_eng",
#     "marketing": "cat_marketing_eng",
#     "business": "cat_business_eng",
#     "education": "cat_edu_eng",
#     "arts": "cat_arts_eng",
#     "engineering": "cat_eng_eng",
#     "finance": "cat_fin_eng",
#     "law": "cat_law_eng",
#     "agro": "cat_agro_eng",
#     "logistics": "cat_log_eng",
#     "real_estate": "cat_re_eng",
#     "lifestyle": "cat_life_eng",
#     "niche": "cat_niche_eng",
# }
#
# # Данные подкатегорий IT
# IT_SUBCATEGORIES_DATA_RU = [
#     ("💻 Написание кода", "sub_it_code_ru"),
#     ("⚙️ Рефакторинг и оптимизация", "sub_it_refactor_ru"),
#     ("🐞 Отладка (Debugging)", "sub_it_debug_ru"),
#     ("🧪 Генерация тестов", "sub_it_tests_ru"),
#     ("📄 Документация", "sub_it_docs_ru"),
#     ("🛠️ DevOps и Инфраструктура", "sub_it_devops_ru"),
#     ("🔒 Кибербезопасность", "sub_it_security_ru"),
#     ("🗄️ SQL и Работа с БД", "sub_it_sql_ru"),
#     ("🏗️ Архитектура ПО", "sub_it_arch_ru"),
# ]
#
# IT_SUBCATEGORIES_DATA_TAT = [
#     ("💻 Код язу", "sub_it_code_tat"),
#     ("⚙️ Рефакторинг һәм оптимизация", "sub_it_refactor_tat"),
#     ("🐞 Сызыкны төзәтү", "sub_it_debug_tat"),
#     ("🧪 Тестлар генерацияләү", "sub_it_tests_tat"),
#     ("📄 Документация", "sub_it_docs_tat"),
#     ("🛠️ DevOps һәм Инфраструктура", "sub_it_devops_tat"),
#     ("🔒 Киберкуркынычсызлык", "sub_it_security_tat"),
#     ("🗄️ SQL һәм Мәгълүмат базалары белән эшләү", "sub_it_sql_tat"),
#     ("🏗️ Программаларның архитектурасы", "sub_it_arch_tat"),
# ]
#
# IT_SUBCATEGORIES_DATA_ENG = [
#     ("💻 Code writing", "sub_it_code_eng"),
#     ("⚙️ Refactoring and optimization", "sub_it_refactor_eng"),
#     ("🐞 Debugging", "sub_it_debug_eng"),
#     ("🧪 Test generation", "sub_it_tests_eng"),
#     ("📄 Documentation", "sub_it_docs_eng"),
#     ("🛠️ DevOps and Infrastructure", "sub_it_devops_eng"),
#     ("🔒 Cybersecurity", "sub_it_security_eng"),
#     ("🗄️ SQL and Working with Databases", "sub_it_sql_eng"),
#     ("🏗️ Software Architecture", "sub_it_arch_eng"),
# ]
#
# MARKETING_SUBCATEGORIES_DATA_RU = [
#     ("📝 Контент-маркетинг", "sub_marketing_content_ru"),
#     ("🔍 SEO (Поисковая оптимизация)", "sub_marketing_seo_ru"),
#     ("✍️ Копирайтинг", "sub_marketing_copywriting_ru"),
#     ("📱 SMM (Социальные медиа)", "sub_marketing_smm_ru"),
#     ("📊 Аналитика рынка", "sub_marketing_analytics_ru"),
#     ("🎯 Персонализация", "sub_marketing_personalization_ru"),
# ]
#
# MARKETING_SUBCATEGORIES_DATA_TAT = [
#     ("📝 Контент-маркетинг", "sub_marketing_content_tat"),
#     ("🔍 SEO (эзләү оптимизациясе)", "sub_marketing_seo_tat"),
#     ("✍️ Копирайтинг", "sub_marketing_copywriting_tat"),
#     ("📱 SMM (Социаль медиа)", "sub_marketing_smm_tat"),
#     ("📊 Базар аналитикасы", "sub_marketing_analytics_tat"),
#     ("🎯 Шәхсиләштерү", "sub_marketing_personalization_tat"),
# ]
#
# MARKETING_SUBCATEGORIES_DATA_ENG = [
#     ("📝 Content Marketing", "sub_marketing_content_eng"),
#     ("🔍 SEO", "sub_marketing_seo_eng"),
#     ("✍️ Copywriting", "sub_marketing_copywriting_eng"),
#     ("📱 SMM", "sub_marketing_smm_eng"),
#     ("📊 Market Analysis", "sub_marketing_analytics_eng"),
#     ("🎯 Personalization", "sub_marketing_personalization_eng"),
# ]
#
# BUSINESS_SUBCATEGORIES_DATA_RU = [
#     ("📊 Стратегическое планирование", "sub_business_planning_ru"),
#     ("📋 Управление проектами", "sub_business_projects_ru"),
#     ("👥 HR и Рекрутинг", "sub_business_hr_ru"),
#     ("💰 Продажи (Sales)", "sub_business_sales_ru"),
#     ("📈 Финансы и Бухгалтерия", "sub_business_finance_ru"),
#     ("⚖️ Юридическая поддержка (Legal Tech)", "sub_business_legal_ru"),
#     ("🎧 Поддержка клиентов (Customer Support)", "sub_business_support_ru"),
# ]
# #C ЭТОГО МОМЕНТА НУЖНО ПРОВЕРЯТЬ ТАТАРСКИЙ!!!!!!!!!!!
# BUSINESS_SUBCATEGORIES_DATA_TAT = [
#     ("📊 Стратегик планлаштыру", "sub_business_planning_tat"),
#     ("📋 Проектларны идарә итү", "sub_business_projects_tat"),
#     ("👥 HR һәм Рекрутинг", "sub_business_hr_tat"),
#     ("💰 Сату", "sub_business_sales_tat"),
#     ("📈 Финанс һәм Бухгалтерия", "sub_business_finance_tat"),
#     ("⚖️ Юридик ярдәм", "sub_business_legal_tat"),
#     ("🎧 Клиентларга ярдәм", "sub_business_support_tat"),
# ]
#
# BUSINESS_SUBCATEGORIES_DATA_ENG = [
#     ("📊 Strategic Planning", "sub_business_planning_eng"),
#     ("📋 Project Management", "sub_business_projects_eng"),
#     ("👥 HR & Recruiting", "sub_business_hr_eng"),
#     ("💰 Sales", "sub_business_sales_eng"),
#     ("📈 Finance & Accounting", "sub_business_finance_eng"),
#     ("⚖️ Legal Support", "sub_business_legal_eng"),
#     ("🎧 Customer Support", "sub_business_support_eng"),
# ]
#
# EDUCATION_SUBCATEGORIES_DATA_RU = [
#     ("📚 Образовательные программы", "sub_education_programs_ru"),
#     ("🎓 Онлайн-курсы и E-Learning", "sub_education_online_ru"),
#     ("👨‍🏫 Методика преподавания", "sub_education_teaching_ru"),
#     ("📝 Оценка и тестирование", "sub_education_testing_ru"),
#     ("🔬 Научные исследования", "sub_education_research_ru"),
#     ("📖 Учебные материалы", "sub_education_materials_ru"),
#     ("🎯 Профориентация", "sub_education_career_ru"),
# ]
#
# EDUCATION_SUBCATEGORIES_DATA_TAT = [
#     ("📚 Белем бирү программалары", "sub_education_programs_tat"),
#     ("🎓 Онлайн-курслар һәм E-Learning", "sub_education_online_tat"),
#     ("👨‍🏫 Укыту методикасы", "sub_education_teaching_tat"),
#     ("📝 Бәяләү һәм тестлау", "sub_education_testing_tat"),
#     ("🔬 Фәнни тикшеренүләр", "sub_education_research_tat"),
#     ("📖 Уку материаллары", "sub_education_materials_tat"),
#     ("🎯 Профориентация", "sub_education_career_tat"),
# ]
#
# EDUCATION_SUBCATEGORIES_DATA_ENG = [
#     ("📚 Educational Programs", "sub_education_programs_eng"),
#     ("🎓 Online Courses & E-Learning", "sub_education_online_eng"),
#     ("👨‍🏫 Teaching Methodology", "sub_education_teaching_eng"),
#     ("📝 Assessment & Testing", "sub_education_testing_eng"),
#     ("🔬 Scientific Research", "sub_education_research_eng"),
#     ("📖 Learning Materials", "sub_education_materials_eng"),
#     ("🎯 Career Guidance", "sub_education_career_eng"),
# ]
#
#
# ARTS_SUBCATEGORIES_DATA_RU = [
#     ("📚 Литература", "sub_arts_literature_ru"),
#     ("🎨 Дизайн и Визуальное искусство", "sub_arts_design_ru"),
#     ("🎵 Музыка и Звук", "sub_arts_music_ru"),
#     ("🎮 Геймдев (Game Dev)", "sub_arts_gamedev_ru"),
#     ("🎬 Видеопродакшн", "sub_arts_video_ru"),
# ]
#
# ARTS_SUBCATEGORIES_DATA_TAT = [
#     ("📚 Әдәбият", "sub_arts_literature_tat"),
#     ("🎨 Дизайн һәм Визуаль сәнгать", "sub_arts_design_tat"),
#     ("🎵 Музыка һәм Тавыш", "sub_arts_music_tat"),
#     ("🎮 Геймдев (Game Dev)", "sub_arts_gamedev_tat"),
#     ("🎬 Видео продюсерлык", "sub_arts_video_tat"),
# ]
#
# ARTS_SUBCATEGORIES_DATA_ENG = [
#     ("📚 Literature", "sub_arts_literature_eng"),
#     ("🎨 Design & Visual Arts", "sub_arts_design_eng"),
#     ("🎵 Music & Sound", "sub_arts_music_eng"),
#     ("🎮 Game Dev", "sub_arts_gamedev_eng"),
#     ("🎬 Video Production", "sub_arts_video_eng"),
# ]
#
#
# ENGINEERING_SUBCATEGORIES_DATA_RU = [
#     ("📐 Проектирование (CAD/CAE)", "sub_engineering_cad_ru"),
#     ("🏗️ Строительство", "sub_engineering_construction_ru"),
#     ("🏭 Производство", "sub_engineering_manufacturing_ru"),
#     ("⚡ Энергетика", "sub_engineering_energy_ru"),
#     ("🧪 Химическая промышленность", "sub_engineering_chemical_ru"),
# ]
#
# ENGINEERING_SUBCATEGORIES_DATA_TAT = [
#     ("📐 Проектирование (CAD/CAE)", "sub_engineering_cad_tat"),
#     ("🏗️ Төзелеш", "sub_engineering_construction_tat"),
#     ("🏭 Җитештерү", "sub_engineering_manufacturing_tat"),
#     ("⚡ Энергетика", "sub_engineering_energy_tat"),
#     ("🧪 Химия сәнәгате", "sub_engineering_chemical_tat"),
# ]
#
# ENGINEERING_SUBCATEGORIES_DATA_ENG = [
#     ("📐 Engineering Design (CAD/CAE)", "sub_engineering_cad_eng"),
#     ("🏗️ Construction", "sub_engineering_construction_eng"),
#     ("🏭 Manufacturing", "sub_engineering_manufacturing_eng"),
#     ("⚡ Energy", "sub_engineering_energy_eng"),
#     ("🧪 Chemical Industry", "sub_engineering_chemical_eng"),
# ]
#
#
# FINANCE_SUBCATEGORIES_DATA_RU = [
#     ("💹 Инвестиции", "sub_finance_investments_ru"),
#     ("🏦 Банковское дело", "sub_finance_banking_ru"),
#     ("🛡️ Страхование", "sub_finance_insurance_ru"),
#     ("🪙 Криптовалюты и Блокчейн", "sub_finance_crypto_ru"),
# ]
#
# FINANCE_SUBCATEGORIES_DATA_TAT = [
#     ("💹 Инвестицияләр", "sub_finance_investments_tat"),
#     ("🏦 Банк эше", "sub_finance_banking_tat"),
#     ("🛡️ Страховкалау", "sub_finance_insurance_tat"),
#     ("🪙 Криптовалюталар һәм Блокчейн", "sub_finance_crypto_tat"),
# ]
#
# FINANCE_SUBCATEGORIES_DATA_ENG = [
#     ("💹 Investments", "sub_finance_investments_eng"),
#     ("🏦 Banking", "sub_finance_banking_eng"),
#     ("🛡️ Insurance", "sub_finance_insurance_eng"),
#     ("🪙 Cryptocurrency & Blockchain", "sub_finance_crypto_eng"),
# ]
#
# LAW_SUBCATEGORIES_DATA_RU = [
#     ("📜 Законодательная деятельность", "sub_law_legislative_ru"),
#     ("🏛️ Госуслуги", "sub_law_public_services_ru"),
#     ("⚖️ Судебная система", "sub_law_judicial_ru"),
#     ("🏙️ Городское планирование", "sub_law_urban_ru"),
# ]
#
# LAW_SUBCATEGORIES_DATA_TAT = [
#     ("📜 Закон чыгару эшчәнлеге", "sub_law_legislative_tat"),
#     ("🏛️ Дәүләт хезмәтләре", "sub_law_public_services_tat"),
#     ("⚖️ Суд системасы", "sub_law_judicial_tat"),
#     ("🏙️ Шәһәр планлаштыру", "sub_law_urban_tat"),
# ]
#
# LAW_SUBCATEGORIES_DATA_ENG = [
#     ("📜 Legislative Activity", "sub_law_legislative_eng"),
#     ("🏛️ Public Services", "sub_law_public_services_eng"),
#     ("⚖️ Judicial System", "sub_law_judicial_eng"),
#     ("🏙️ Urban Planning", "sub_law_urban_eng"),
# ]
#
#
# AGRO_SUBCATEGORIES_DATA_RU = [
#     ("🌾 Точное земледелие", "sub_agro_precision_ru"),
#     ("🐾 Ветеринария", "sub_agro_veterinary_ru"),
#     ("🌍 Экология", "sub_agro_ecology_ru"),
#     ("🦋 Биоразнообразие", "sub_agro_biodiversity_ru"),
# ]
#
# AGRO_SUBCATEGORIES_DATA_TAT = [
#     ("🌾 Төгез игенчелек", "sub_agro_precision_tat"),
#     ("🐾 Ветеринария", "sub_agro_veterinary_tat"),
#     ("🌍 Экология", "sub_agro_ecology_tat"),
#     ("🦋 Биотөрлелек", "sub_agro_biodiversity_tat"),
# ]
#
# AGRO_SUBCATEGORIES_DATA_ENG = [
#     ("🌾 Precision Agriculture", "sub_agro_precision_eng"),
#     ("🐾 Veterinary", "sub_agro_veterinary_eng"),
#     ("🌍 Ecology", "sub_agro_ecology_eng"),
#     ("🦋 Biodiversity", "sub_agro_biodiversity_eng"),
# ]
#
# LOGISTICS_SUBCATEGORIES_DATA_RU = [
#     ("🚚 Логистика", "sub_logistics_logistics_ru"),
#     ("🚗 Транспорт", "sub_logistics_transport_ru"),
#     ("✈️ Туризм и Гостеприимство", "sub_logistics_tourism_ru"),
#     ("🚆 Авиация и ЖД", "sub_logistics_aviation_ru"),
# ]
#
# LOGISTICS_SUBCATEGORIES_DATA_TAT = [
#     ("🚚 Логистика", "sub_logistics_logistics_tat"),
#     ("🚗 Транспорт", "sub_logistics_transport_tat"),
#     ("✈️ Туризм һәм Кунакчыллык", "sub_logistics_tourism_tat"),
#     ("🚆 Авиация һәм Тимер юл", "sub_logistics_aviation_tat"),
# ]
#
# LOGISTICS_SUBCATEGORIES_DATA_ENG = [
#     ("🚚 Logistics", "sub_logistics_logistics_eng"),
#     ("🚗 Transport", "sub_logistics_transport_eng"),
#     ("✈️ Tourism & Hospitality", "sub_logistics_tourism_eng"),
#     ("🚆 Aviation & Rail", "sub_logistics_aviation_eng"),
# ]
#
# REAL_ESTATE_SUBCATEGORIES_DATA_RU = [
#     ("🏠 Оценка недвижимости", "sub_real_estate_valuation_ru"),
#     ("🔑 Управление объектами", "sub_real_estate_management_ru"),
#     ("📢 Маркетинг объектов", "sub_real_estate_marketing_ru"),
# ]
#
# REAL_ESTATE_SUBCATEGORIES_DATA_TAT = [
#     ("🏠 Милекне бәяләү", "sub_real_estate_valuation_tat"),
#     ("🔑 Объектларны идарә итү", "sub_real_estate_management_tat"),
#     ("📢 Объектлар маркетингы", "sub_real_estate_marketing_tat"),
# ]
#
# REAL_ESTATE_SUBCATEGORIES_DATA_ENG = [
#     ("🏠 Property Valuation", "sub_real_estate_valuation_eng"),
#     ("🔑 Property Management", "sub_real_estate_management_eng"),
#     ("📢 Property Marketing", "sub_real_estate_marketing_eng"),
# ]
#
# LIFESTYLE_SUBCATEGORIES_DATA_RU = [
#     ("⏰ Планирование времени", "sub_lifestyle_time_ru"),
#     ("💪 Здоровье и Фитнес", "sub_lifestyle_health_ru"),
#     ("❤️ Отношения и Психология", "sub_lifestyle_relationships_ru"),
#     ("🎨 Хобби и Саморазвитие", "sub_lifestyle_hobbies_ru"),
#     ("🏠 Быт", "sub_lifestyle_household_ru"),
# ]
#
# LIFESTYLE_SUBCATEGORIES_DATA_TAT = [
#     ("⏰ Вакытны планлаштыру", "sub_lifestyle_time_tat"),
#     ("💪 Сәламәтлек һәм Фитнес", "sub_lifestyle_health_tat"),
#     ("❤️ Мөнәсәбәтләр һәм Психология", "sub_lifestyle_relationships_tat"),
#     ("🎨 Хобби һәм Үз-үзеңне үстерү", "sub_lifestyle_hobbies_tat"),
#     ("🏠 Көнкүреш", "sub_lifestyle_household_tat"),
# ]
#
# LIFESTYLE_SUBCATEGORIES_DATA_ENG = [
#     ("⏰ Time Management", "sub_lifestyle_time_eng"),
#     ("💪 Health & Fitness", "sub_lifestyle_health_eng"),
#     ("❤️ Relationships & Psychology", "sub_lifestyle_relationships_eng"),
#     ("🎨 Hobbies & Self-Development", "sub_lifestyle_hobbies_eng"),
#     ("🏠 Household & Daily Life", "sub_lifestyle_household_eng"),
# ]
#
# NICHE_SUBCATEGORIES_DATA_RU = [
#     ("🔮 Астрология и Эзотерика", "sub_niche_astrology_ru"),
#     ("⚽ Спорт", "sub_niche_sports_ru"),
#     ("🤝 Благотворительность и НКО", "sub_niche_charity_ru"),
# ]
#
# NICHE_SUBCATEGORIES_DATA_TAT = [
#     ("🔮 Астрология һәм Эзотерика", "sub_niche_astrology_tat"),
#     ("⚽ Спорт", "sub_niche_sports_tat"),
#     ("🤝 Хәйрия һәм НКО", "sub_niche_charity_tat"),
# ]
#
# NICHE_SUBCATEGORIES_DATA_ENG = [
#     ("🔮 Astrology & Esoterics", "sub_niche_astrology_eng"),
#     ("⚽ Sports", "sub_niche_sports_eng"),
#     ("🤝 Charity & NGO", "sub_niche_charity_eng"),
# ]
#
# # ==============================================================================
# # 2. КЛАВИАТУРЫ (Исправленные callback_data)
# # ==============================================================================
#
# def get_main_reply_inline():
#     """Меню языков"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(text="Русский", callback_data="lang_ru", style = "danger"),
#             InlineKeyboardButton(text="Татарча", callback_data="lang_tat", style = "success"),
#             InlineKeyboardButton(text="English", callback_data="lang_en", style = "primary"),
#         ],
#         [InlineKeyboardButton(text=" Профиль", callback_data="menu_profile")],
#         [InlineKeyboardButton(text="🔍 Поиск", callback_data="menu_search")],
#     ])
#
#
# def get_categories_ru():
#     """
#     Меню категорий RU.
#     ВАЖНО: Здесь используются ID из CATEGORIES_CALLBACKS, а не хардкод.
#     """
#     inline_keyboard = [
#         [InlineKeyboardButton(text="💻 Информационные технологии и Разработка ПО",
#                               callback_data=CATEGORIES_CALLBACKS_RU["it"])],
#         [InlineKeyboardButton(text="📣 Маркетинг, Реклама и PR", callback_data=CATEGORIES_CALLBACKS_RU["marketing"])],
#         [InlineKeyboardButton(text="🧑‍💼 Бизнес, Менеджмент и Предпринимательство",
#                               callback_data=CATEGORIES_CALLBACKS_RU["business"])],
#         [InlineKeyboardButton(text="🧑‍🔬 Образование и Наука", callback_data=CATEGORIES_CALLBACKS_RU["education"])],
#         [InlineKeyboardButton(text="🎨 Творчество, Искусство и Медиа", callback_data=CATEGORIES_CALLBACKS_RU["arts"])],
#         [InlineKeyboardButton(text="🏗️ Инженерия, Строительство и Производство",
#                               callback_data=CATEGORIES_CALLBACKS_RU["engineering"])],
#         [InlineKeyboardButton(text="💳 Финансы, Банкинг и Страхование", callback_data=CATEGORIES_CALLBACKS_RU["finance"])],
#         [InlineKeyboardButton(text="🏛️ Государственное управление и Право", callback_data=CATEGORIES_CALLBACKS_RU["law"])],
#         [InlineKeyboardButton(text="🧑‍🌾 Сельское хозяйство и Экология", callback_data=CATEGORIES_CALLBACKS_RU["agro"])],
#         [InlineKeyboardButton(text="🚚 Логистика, Транспорт и Туризм", callback_data=CATEGORIES_CALLBACKS_RU["logistics"])],
#         [InlineKeyboardButton(text="🏠 Недвижимость", callback_data=CATEGORIES_CALLBACKS_RU["real_estate"])],
#         [InlineKeyboardButton(text="🎯 Персональная эффективность и Lifestyle",
#                               callback_data=CATEGORIES_CALLBACKS_RU["lifestyle"])],
#         [InlineKeyboardButton(text="👓 Специализированные и Нишевые области",
#                               callback_data=CATEGORIES_CALLBACKS_RU["niche"])],
#         [InlineKeyboardButton(text="🔙 Назад к языкам", callback_data="back_lang")]
#     ]
#     return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
#
#
# def get_categories_tat():
#     """Меню категорий TAT (пока структура аналогична RU для примера)"""
#     # В реальном проекте здесь должны быть свои уникальные callback_data, например cat_it_tat
#     inline_keyboard = [
#         [InlineKeyboardButton(text="💻Мәгълүмат технологияләре һәм программалар төзелеше💻", callback_data=CATEGORIES_CALLBACKS_TAT["it"])],
#         [InlineKeyboardButton(text="📣Маркетинг, реклама һәм пиар📣", callback_data=CATEGORIES_CALLBACKS_TAT["marketing"])],
#         [InlineKeyboardButton(text="🧑‍💼Бизнес, менеджмендә һәм керәстәнлек🧑‍💼", callback_data=CATEGORIES_CALLBACKS_TAT["business"])],
#         [InlineKeyboardButton(text="🧑‍🔬Белем һәм фән🧑‍🔬", callback_data=CATEGORIES_CALLBACKS_TAT["education"])],
#         [InlineKeyboardButton(text="🎨Иҗат, сәнгать һәм мәгълүмат чаралары🎨", callback_data=CATEGORIES_CALLBACKS_TAT["arts"])],
#         [InlineKeyboardButton(text="🏗️Инженерлык, төзелеш һәм әзерләү🏗️", callback_data=CATEGORIES_CALLBACKS_TAT["engineering"])],
#         [InlineKeyboardButton(text="💳Финанслар, банк эшчәнлеге һәм страховкалау💳", callback_data=CATEGORIES_CALLBACKS_TAT["finance"])],
#         [InlineKeyboardButton(text="🏛️Дәүләт идарәсе һәм хокук🏛️", callback_data=CATEGORIES_CALLBACKS_TAT["law"])],
#         [InlineKeyboardButton(text="🧑‍🌾Ауыл хуҗалыгы һәм экология🧑‍🌾", callback_data=CATEGORIES_CALLBACKS_TAT["agro"])],
#         [InlineKeyboardButton(text="🚚Логистика, транспорты һәм туризм🚚", callback_data=CATEGORIES_CALLBACKS_TAT["logistics"])],
#         [InlineKeyboardButton(text="🏠Эман-эштәр🏠", callback_data=CATEGORIES_CALLBACKS_TAT["real_estate"])],
#         [InlineKeyboardButton(text="🎯Шәхси нәтижәлелек һәм тирә-як тормыш тарзи🎯", callback_data=CATEGORIES_CALLBACKS_TAT["lifestyle"])],
#         [InlineKeyboardButton(text="👓Арнайы һәм ниша өлкәләре👓", callback_data=CATEGORIES_CALLBACKS_TAT["niche"])],
#         [InlineKeyboardButton(text="🔙 артка 🔙", callback_data="back_lang")]
#     ]
#     return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
#
#
# def get_categories_eng():
#     """Меню категорий EN"""
#     inline_keyboard = [
#         [InlineKeyboardButton(text="💻Information Technology & Software Development💻",
#                               callback_data=CATEGORIES_CALLBACKS_ENG["it"])],
#         [InlineKeyboardButton(text="📣Marketing, Advertising & PR📣",
#                               callback_data=CATEGORIES_CALLBACKS_ENG["marketing"])],
#         [InlineKeyboardButton(text="🧑‍💼Business, Management & Entrepreneurship🧑‍💼",
#                               callback_data=CATEGORIES_CALLBACKS_ENG["business"])],
#         [InlineKeyboardButton(text="🧑‍🔬Education & Science🧑‍🔬", callback_data=CATEGORIES_CALLBACKS_ENG["education"])],
#         [InlineKeyboardButton(text="🎨Creative Arts & Media🎨",
#                               callback_data=CATEGORIES_CALLBACKS_ENG["arts"])],
#         [InlineKeyboardButton(text="🏗️Engineering, Construction & Manufacturing🏗️",
#                               callback_data=CATEGORIES_CALLBACKS_ENG["engineering"])],
#         [InlineKeyboardButton(text="💳Finance, Banking & Insurance💳",
#                               callback_data=CATEGORIES_CALLBACKS_ENG["finance"])],
#         [InlineKeyboardButton(text="🏛️Public Administration & Law🏛️", callback_data=CATEGORIES_CALLBACKS_ENG["law"])],
#         [InlineKeyboardButton(text="🧑‍🌾Agriculture & Ecology🧑‍🌾", callback_data=CATEGORIES_CALLBACKS_ENG["agro"])],
#         [InlineKeyboardButton(text="🚚Logistics, Transport & Tourism🚚",
#                               callback_data=CATEGORIES_CALLBACKS_ENG["logistics"])],
#         [InlineKeyboardButton(text="🏠Real Estate🏠", callback_data=CATEGORIES_CALLBACKS_ENG["real_estate"])],
#         [InlineKeyboardButton(text="🎯Personal Development & Lifestyle🎯",
#                               callback_data=CATEGORIES_CALLBACKS_ENG["lifestyle"])],
#         [InlineKeyboardButton(text="👓Specialized & Niche Fields👓", callback_data=CATEGORIES_CALLBACKS_ENG["niche"])],
#         [InlineKeyboardButton(text="🔙 Back 🔙", callback_data="back_lang")]
#     ]
#     return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
#
#
# def get_profile_menu_inline(lang="ru"):
#     """Меню профиля"""
#     if lang == "tat":
#         kb = [
#             [InlineKeyboardButton(text="🌐 Теле: Татарча", callback_data="profile_lang_tat")],
#             [InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats")],
#             [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main_menu")],
#         ]
#     elif lang == "eng":
#         kb = [
#             [InlineKeyboardButton(text="🌐 Language: English", callback_data="profile_lang_eng")],
#             [InlineKeyboardButton(text="📊 Statistics", callback_data="profile_stats")],
#             [InlineKeyboardButton(text="🔙 Back", callback_data="back_main_menu")],
#         ]
#     else:
#         kb = [
#             [InlineKeyboardButton(text="🌐 Язык: Русский", callback_data="profile_lang_ru")],
#             [InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats")],
#             [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main_menu")],
#         ]
#     return InlineKeyboardMarkup(inline_keyboard=kb)
#
# def get_main_menu_inline():
#     """Главное меню с кнопкой Каталог"""
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="📚 Каталог", callback_data="menu_catalog"),
#         InlineKeyboardButton(text="🔍 Поиск", callback_data="menu_search")
#          ],
#         [InlineKeyboardButton(text="📚 Обучение", callback_data="menu_learning"),
#         InlineKeyboardButton(text="💎 Тарифы", callback_data="menu_tariffs")],
#         [InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile")],
#     ])
#
# def get_it_subcategories_keyboard_RU():
#     """Подкатегории IT"""
#     keyboard = []
#     for text, callback in IT_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_it_subcategories_keyboard_TAT():
#     """Подкатегории IT"""
#     keyboard = []
#     for text, callback in IT_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_it_subcategories_keyboard_ENG():
#     """Подкатегории IT"""
#     keyboard = []
#     for text, callback in IT_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
#
#
# def get_marketing_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in MARKETING_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_marketing_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in MARKETING_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_marketing_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in MARKETING_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_business_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in BUSINESS_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_business_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in BUSINESS_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_business_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in BUSINESS_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_education_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in EDUCATION_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_education_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in EDUCATION_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_education_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in EDUCATION_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_arts_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in ARTS_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_arts_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in ARTS_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_arts_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in ARTS_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_engineering_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in ENGINEERING_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_engineering_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in ENGINEERING_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_engineering_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in ENGINEERING_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_finance_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in FINANCE_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_finance_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in FINANCE_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_finance_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in FINANCE_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_law_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in LAW_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_law_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in LAW_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_law_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in LAW_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_agro_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in AGRO_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_agro_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in AGRO_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_agro_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in AGRO_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_logistics_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in LOGISTICS_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_logistics_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in LOGISTICS_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_logistics_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in LOGISTICS_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_real_estate_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in REAL_ESTATE_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_real_estate_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in REAL_ESTATE_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_real_estate_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in REAL_ESTATE_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_lifestyle_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in LIFESTYLE_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_lifestyle_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in LIFESTYLE_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_lifestyle_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in LIFESTYLE_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_niche_subcategories_keyboard_RU():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in NICHE_SUBCATEGORIES_DATA_RU:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
# def get_niche_subcategories_keyboard_TAT():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in NICHE_SUBCATEGORIES_DATA_TAT:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# def get_niche_subcategories_keyboard_ENG():
#     """Подкатегории маркетинг"""
#     keyboard = []
#     for text, callback in NICHE_SUBCATEGORIES_DATA_ENG:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#
#     keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# # ==============================================================================
# # ПОИСК ПО ПОДКАТЕГОРИЯМ
# # ==============================================================================
# def get_all_subcategories():
#     """Возвращает все подкатегории для поиска"""
#     all_subs = []
#     for text, callback in IT_SUBCATEGORIES_DATA_RU + IT_SUBCATEGORIES_DATA_TAT + IT_SUBCATEGORIES_DATA_ENG:
#         all_subs.append((text, callback))
#     for text, callback in MARKETING_SUBCATEGORIES_DATA_RU + MARKETING_SUBCATEGORIES_DATA_TAT + MARKETING_SUBCATEGORIES_DATA_ENG:
#         all_subs.append((text, callback))
#     for text, callback in BUSINESS_SUBCATEGORIES_DATA_RU + BUSINESS_SUBCATEGORIES_DATA_TAT + BUSINESS_SUBCATEGORIES_DATA_ENG:
#         all_subs.append((text, callback))
#     return all_subs
#
#
# def search_subcategories(query: str, limit: int = 10):
#     """Ищет подкатегории по ключевому слову"""
#     all_subs = get_all_subcategories()
#     query_lower = query.lower().strip()
#     results = []
#     for text, callback in all_subs:
#         if query_lower in text.lower():
#             results.append((text, callback))
#             if len(results) >= limit:
#                 break
#     return results
#
#
# def get_search_results_keyboard(results):
#     """Создаёт клавиатуру с результатами поиска"""
#     keyboard = []
#     for text, callback in results:
#         keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
#     keyboard.append([InlineKeyboardButton(text="🔙 Назад к поиску", callback_data="menu_search")])
#     return InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
#
# # ==============================================================================
# # 3. ХЕНДЛЕРЫ (Логика)
# # ==============================================================================
#
# # --- ВЫБОР ЯЗЫКА ---
#
# @router.callback_query(F.data == "lang_ru")
# async def categories_rus(callback: CallbackQuery):
#     await callback.message.edit_text("📂 **Выберите категорию промптов** 📂",
#                                      reply_markup=get_categories_ru(),
#                                      parse_mode="Markdown")
#     await callback.answer()
#
#
# @router.callback_query(F.data == "lang_tat")
# async def categories_tat(callback: CallbackQuery):
#     await callback.message.edit_text("📂 **Промптлар категориясен сайлагыз** 📂",
#                                      reply_markup=get_categories_tat(),
#                                      parse_mode="Markdown")
#     await callback.answer()
#
#
# @router.callback_query(F.data == "lang_en")
# async def categories_eng(callback: CallbackQuery):
#     await callback.message.edit_text("📂 **Select prompts category** 📂",
#                                      reply_markup=get_categories_eng(),
#                                      parse_mode="Markdown")
#     await callback.answer()
#
#
# # --- ВЫБОР КАТЕГОРИИ ---
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["it"])
# async def show_it_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА IT.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_it_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["it"])
# async def show_it_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА IT.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_it_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["it"])
# async def show_it_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА IT.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_it_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
#
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["marketing"])
# async def show_marketing_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_marketing_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["marketing"])
# async def show_marketing_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_marketing_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["marketing"])
# async def show_marketing_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_marketing_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["business"])
# async def show_business_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_business_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["business"])
# async def show_business_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_business_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["business"])
# async def show_business_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_business_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["education"])
# async def show_education_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_education_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["education"])
# async def show_education_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_education_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["education"])
# async def show_education_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_education_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["arts"])
# async def show_arts_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_arts_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["arts"])
# async def show_arts_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_arts_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["arts"])
# async def show_arts_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_arts_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["engineering"])
# async def show_engineering_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_engineering_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["engineering"])
# async def show_engineering_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_engineering_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["engineering"])
# async def show_engineering_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_engineering_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["finance"])
# async def show_finance_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_finance_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["finance"])
# async def show_finance_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_finance_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["finance"])
# async def show_finance_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_finance_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["law"])
# async def show_law_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_law_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["law"])
# async def show_law_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_law_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["law"])
# async def show_law_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_law_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["agro"])
# async def show_agro_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_agro_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["agro"])
# async def show_agro_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_agro_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["agro"])
# async def show_agro_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_agro_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["logistics"])
# async def show_logistics_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_logistics_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["logistics"])
# async def show_logistics_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_logistics_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["logistics"])
# async def show_logistics_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_logistics_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["real_estate"])
# async def show_real_estate_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_real_estate_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["real_estate"])
# async def show_real_estate_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_real_estate_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["real_estate"])
# async def show_real_estate_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_real_estate_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["lifestyle"])
# async def show_lifestyle_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_lifestyle_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["lifestyle"])
# async def show_lifestyle_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_lifestyle_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["lifestyle"])
# async def show_lifestyle_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_lifestyle_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["niche"])
# async def show_niche_subcategories_ru(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Выберите направление**\n\n",
#         reply_markup=get_niche_subcategories_keyboard_RU(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["niche"])
# async def show_niche_subcategories_tat(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Юнәлешне сайлагыз**\n\n",
#         reply_markup=get_niche_subcategories_keyboard_TAT(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["niche"])
# async def show_niche_subcategories_eng(callback: CallbackQuery):
#     """
#     СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
#     Теперь callback_data совпадает с тем, что в кнопке.
#     """
#     await callback.message.edit_text(
#         "**Choose a direction**\n\n",
#         reply_markup=get_niche_subcategories_keyboard_ENG(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == "menu_catalog")
# async def menu_catalog(callback: CallbackQuery):
#     """Показывает выбор языка для каталога"""
#     await callback.message.edit_text(
#         "📚 **Каталог промптов**\n\nВыберите язык:",
#         parse_mode="Markdown",
#         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#             [
#                 InlineKeyboardButton(text="Русский", callback_data="lang_ru", style = "danger"),
#                 InlineKeyboardButton(text="Татарча", callback_data="lang_tat", style = "success"),
#                 InlineKeyboardButton(text="English", callback_data="lang_en", style = "primary"),
#             ],
#             [InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")],
#         ])
#     )
#     await callback.answer()
#
#
# # --- ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ---
# @router.callback_query(F.data == "menu_profile")
# async def menu_profile(callback: CallbackQuery):
#     """Показывает статистику пользователя"""
#     from database import get_user_premium_status, get_user_profile_stats
#
#     user_id = callback.from_user.id
#
#     # Получаем статус премиум
#     is_premium = await get_user_premium_status(user_id)
#
#     # Получаем полную статистику
#     stats = await get_user_profile_stats(user_id)
#
#     # Формируем текст
#     if is_premium:
#         status_text = "💎 **Premium**"
#         status_emoji = "✅"
#     else:
#         status_text = "🆓 **Free**"
#         status_emoji = "⏳"
#
#     text = (
#         f"👤 **Профиль пользователя**\n\n"
#         f"ID: `{user_id}`\n"
#         f"Статус: {status_text} {status_emoji}\n\n"
#         f"📊 **Статистика**:\n"
#         f"📝 Предложенных промптов: {stats['prompts_submitted']}\n"
#         f"💾 Сохранённых промптов: {stats['prompts_saved']}\n"
#         f"📅 ударный режим: {stats['days_in_bot']}\n\n"
#     )
#
#     # Клавиатура профиля
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="💎 Тарифы", callback_data="tariff_premium")],
#         [InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")],
#     ])
#
#     await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
#     await callback.answer()
#
#
#
#
# # --- ПОДКАТЕГОРИИ IT ---
#
#
# @router.callback_query(F.data.startswith("sub_it_"))
# async def process_it_subcategory(callback: CallbackQuery):
#     from database import get_prompts_by_subcategory, set_user_language
#
#     user_id = callback.from_user.id
#     callback_data = callback.data
#
#     # 1. Определяем язык
#     if callback_data.endswith("_ru"):
#         data_dict = dict(IT_SUBCATEGORIES_DATA_RU)
#         text_title = "<b>Выбрано:</b>"
#         language = "ru"
#     elif callback_data.endswith("_tat"):
#         data_dict = dict(IT_SUBCATEGORIES_DATA_TAT)
#         text_title = "<b>Сайланган:</b>"
#         language = "tat"
#     else:
#         data_dict = dict(IT_SUBCATEGORIES_DATA_ENG)
#         text_title = "<b>Selected:</b>"
#         language = "eng"
#
#     # 2. Сохраняем язык пользователя в БД
#     await set_user_language(user_id, language)
#
#     # 3. Получаем название подкатегории
#     subcat_name = escape(data_dict.get(callback_data, callback_data))
#
#     # 4. Запрашиваем промпты из БД
#     prompts = await get_prompts_by_subcategory(callback_data, language)
#
#     if not prompts:
#         await callback.message.edit_text(
#             f"{text_title} {subcat_name}\n\n⚠️ В этом разделе пока нет промптов.",
#             parse_mode="HTML"
#         )
#     else:
#         await callback.message.edit_text(
#             f"{text_title} {subcat_name}\n\n✅ Найдено промптов: {len(prompts)}",
#             parse_mode="HTML"
#         )
#         # Отправляем каждый промпт отдельным сообщением
#         for prompt in prompts:
#             text = f"📌 <b>{escape(prompt['title'])}</b>\n\n{escape(prompt['content'])}"
#             if prompt['is_premium']:
#                 text += "\n\n🔒 <i>Premium Content</i>"
#             await callback.message.answer(text, parse_mode="HTML")
#
#     await callback.answer()
#
#
# # --- НАВИГАЦИЯ НАЗАД ---
#
# @router.callback_query(F.data == "back_to_categories_ru")
# async def back_to_categories(callback: CallbackQuery):
#     await callback.message.edit_text(
#         "📂 **Выберите категорию промптов** 📂",
#         reply_markup=get_categories_ru(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == "back_to_categories_tat")
# async def back_to_categories(callback: CallbackQuery):
#     await callback.message.edit_text(
#         "📂 **Выберите категорию промптов** 📂",
#         reply_markup=get_categories_tat(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
# @router.callback_query(F.data == "back_to_categories_eng")
# async def back_to_categories(callback: CallbackQuery):
#     await callback.message.edit_text(
#         "📂 **Выберите категорию промптов** 📂",
#         reply_markup=get_categories_eng(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# @router.callback_query(F.data == "back_lang")
# async def back_to_languages(callback: CallbackQuery):
#     await callback.message.edit_text(
#         "🌐 **Выберите язык / Тел сайлагыз / Select language:** 🌐",
#         reply_markup=get_main_reply_inline(),
#         parse_mode="Markdown"
#     )
#     await callback.answer()
#
#
# # --- МЕНЮ ПОИСКА (ВКЛЮЧАЕТ СОСТОЯНИЕ) ---
# @router.callback_query(F.data == "menu_search")
# async def menu_search(callback: CallbackQuery, state: FSMContext):
#     """Показывает меню поиска и включает режим поиска"""
#     await state.set_state(SearchState.waiting_for_query)
#     await callback.message.edit_text(
#         "🔍 **Поиск по подкатегориям**\n\n"
#         "Введите ключевое слово для поиска:\n\n"
#         "Примеры:\n"
#         "• `код` → Написание кода, Код язу\n"
#         "• `SEO` → SEO оптимизация\n"
#         "• `дизайн` → Дизайн и визуальное искусство\n\n"
#         "⌨️ Просто напишите слово в чат:\n\n"
#         "❌ Чтобы отменить поиск, нажмите /cancel",
#         parse_mode="Markdown",
#         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")]
#         ])
#     )
#     await callback.answer()
#
#
# # --- ОБРАБОТКА ПОИСКОВОГО ЗАПРОСА (ТОЛЬКО КОГДА АКТИВНО СОСТОЯНИЕ) ---
# @router.message(SearchState.waiting_for_query)
# async def handle_search_query(message: Message, state: FSMContext):
#     """Обрабатывает текстовые сообщения ТОЛЬКО когда активен поиск"""
#     query = message.text.strip()
#
#     # Ищем подкатегории
#     results = search_subcategories(query, limit=10)
#
#     if not results:
#         await message.answer(
#             "❌ **Ничего не найдено**\n\n"
#             f"По запросу: `{escape(query)}`\n\n"
#             "Попробуйте другое ключевое слово.",
#             parse_mode="Markdown",
#             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                 [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="menu_search")],
#                 [InlineKeyboardButton(text="❌ Отменить", callback_data="back_lang")],
#             ])
#         )
#     else:
#         await message.answer(
#             f"✅ **Найдено: {len(results)}**\n\n"
#             f"По запросу: `{escape(query)}`\n\n"
#             "Выберите подкатегорию:",
#             parse_mode="Markdown",
#             reply_markup=get_search_results_keyboard(results)
#         )
#
#     # ✅ СБРАСЫВАЕМ СОСТОЯНИЕ ПОСЛЕ ПОИСКА
#     await state.clear()
#
#

#     )
#



###

# Стратегическое планирование: Разработка бизнес-планов, дорожных карт (roadmaps), анализ рисков.
# Управление проектами: Декомпозиция задач, создание планов спринтов (Agile/Scrum), генерация отчетов о статусе проектов.
# HR и Рекрутинг: Написание вакансий, скрининг резюме, генерация вопросов для собеседований, планы онбординга сотрудников.
# Продажи (Sales): Скрипты для холодных звонков, обработка возражений, подготовка коммерческих предложений (КП), анализ сделок.
# Финансы и Бухгалтерия: Анализ финансовых отчетов, прогнозирование денежных потоков, объяснение налоговых изменений, генерация шаблонов счетов.
# Юридическая поддержка (Legal Tech): Анализ контрактов, поиск правовых прецедентов, составление типовых договоров, проверка на соответствие законодательству (GDPR, локальные законы).
# Поддержка клиентов (Customer Support): Создание базы знаний, генерация ответов на частые вопросы (FAQ), анализ тональности обращений, симуляция диалогов для обучения операторов.

###

# Разработка учебных программ: Создание планов уроков, syllabus курсов, тестов и экзаменационных билетов.
# Репетиторство и менторство: Объяснение сложных тем простым языком, генерация пошаговых решений задач, адаптация материала под уровень ученика.
# Научные исследования: Обзор литературы (Literature Review), формулирование гипотез, помощь в написании академических статей, рецензирование черновиков.
# Языковое обучение: Генерация диалогов, упражнений на грамматику, проверка эссе, симуляция носителя языка.
# Визуализация данных: Идеи для графиков, объяснение статистических методов, интерпретация результатов экспериментов.

###

# Литература: Написание сюжетов, развитие персонажей, диалоги, поэзия, сценарии для кино и театра.
# Дизайн и Визуальное искусство: Промпты для генерации изображений (Midjourney, DALL-E, Stable Diffusion), идеи для логотипов, цветовые палитры, описание стилей.
# Музыка и Звук: Генерация текстов песен, идей для мелодий, описание звукового дизайна, подкаст-сценарии.
# Геймдев (Game Dev): Создание лора мира, квестов, диалогов NPC, балансировка игровых механик, генерация ассетов (описания для 3D-моделеров).
# Видеопродакшн: Раскадровки (storyboards), сценарии, планы съемок, идеи для монтажа.

###

# Проектирование (CAD/CAE): Генерация спецификаций, проверка норм, идеи для оптимизации конструкций.
# Строительство: Составление смет, календарных планов работ, проверка соответствия СНиП/ГОСТ.
# Производство: Оптимизация цепочек поставок, предиктивное обслуживание оборудования (анализ данных датчиков), контроль качества (анализ дефектов).
# Энергетика: Моделирование нагрузок, оптимизация потребления, анализ возобновляемых источников энергии.
# Химическая промышленность: Синтез новых материалов, безопасность процессов.

###

# Инвестиции: Анализ рынков, генерация инвестиционных тезисов, суммаризация отчетов компаний (10-K, 10-Q).
# Банковское дело: Оценка кредитоспособности (анализ данных заемщика), обнаружение мошенничества (паттерны транзакций).
# Страхование: Оценка рисков, автоматизация обработкиClaims (страховых случаев), расчет премий.
# Криптовалюты и Блокчейн: Анализ смарт-контрактов на уязвимости, отслеживание транзакций, генерация токеномики.

###

# Законодательная деятельность: Анализ законопроектов, поиск противоречий в законах, сравнение международного права.
# Госуслуги: Чат-боты для граждан, упрощение бюрократического языка, анализ обращений граждан.
# Судебная система: Подготовка проектов судебных решений (на основе прецедентов), анализ доказательств.
# Городское планирование: Анализ транспортных потоков, оптимизация маршрутов общественного транспорта, урбанистика.

###

# Точное земледелие: Анализ данных с дронов/спутников, рекомендации по поливу и удобрениям, прогноз урожая.
# Ветеринария: Диагностика заболеваний животных, рекомендации по кормлению.
# Экология: Мониторинг загрязнения, анализ климатических данных, стратегии устойчивого развития (ESG).
# Биоразнообразие: Идентификация видов по фото/звуку, мониторинг миграции животных.

###

# Логистика: Оптимизация маршрутов доставки, управление складскими запасами, прогнозирование спроса.
# Транспорт: Планирование расписаний, анализ трафика, автономное вождение (сценарии поведения).
# Туризм и Гостеприимство: Составление индивидуальных itineraries (маршрутов), бронирование, рекомендации отелей/ресторанов, перевод для туристов.
# Авиация и ЖД: Управление экипажами, техобслуживание, динамическое ценообразование.

###

# Оценка недвижимости: Анализ рыночных тенденций, автоматическая оценка стоимости (AVM).
# Управление объектами: Обработка заявок арендаторов, планирование ремонтов.
# Маркетинг объектов: Генерация описаний квартир/домов, виртуальные туры (сценарии).

###

# Планирование времени: Составление распорядка дня, техники тайм-менеджмента (Pomodoro, GTD).
# Здоровье и Фитнес: Планы тренировок, рецепты питания, трекеры привычек.
# Отношения и Психология: Советы по коммуникации, идеи для свиданий, разрешение конфликтов.
# Хобби и Саморазвитие: Изучение новых навыков, идеи для подарков, планирование путешествий.
# Быт: Идеи для уборки, организация пространства, советы по ремонту своими руками.

###

# Астрология и Эзотерика: Генерация гороскопов, толкование карт Таро (как развлекательный контент).
# Спорт: Анализ матчей, тактические схемы, тренировочные программы для профессионалов.
# Благотворительность и НКО: Написание грантовых заявок, стратегии фандрайзинга, отчетность.
