import asyncio
import aiohttp

from html import escape
import re
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from test_database import (
    add_or_update_user,
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
    update_user_coins,
    get_user_language,
)

from test_languges import get_text, LANGUAGES
import os
import aiofiles
import json
import wave
import subprocess
from vosk import Model, KaldiRecognizer


router = Router()

# ==============================================================================
# 1. КОНФИГУРАЦИЯ API
# ==============================================================================

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

QWEN_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
QWEN_API_URL = "https://openrouter.ai/api/v1/chat/completions"


VOSK_MODEL_PATH = "models/vosk-model-small-ru-0.22"
vosk_model = Model(VOSK_MODEL_PATH)

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

class GamesState(StatesGroup):
    in_ai_quiz = State()
    in_prompt_puzzle = State()

class PromptReviewState(StatesGroup):
    waiting_for_prompt = State()


# ==============================================================================
# 3. БАЗА МОДЕЛЕЙ
# ==============================================================================

AI_MODELS_DB = [
    {"id": "mistral", "name": "Mistral AI", "description": "Быстрая и эффективная модель от Mistral"},
    {"id": "qwen", "name": "Qwen AI", "description": "Умная модель от Alibaba с глубоким пониманием контекста"},
    {"id": "nemotron", "name": "NVIDIA Nemotron 3 Super", "description": "Гибридная модель от NVIDIA для сложных задач, программирования и анализа"},
    {"id": "gemini", "name": "Gemini Pro", "description": "Мультимодальная модель от Google"},
    {"id": "gptoss", "name": "OpenAI gpt-oss-120b", "description": "Сильная open-weight модель для логики, кода и сложных рассуждений"},
    {"id": "claude", "name": "Claude 3", "description": "Безопасная и мощная модель от Anthropic"},
    {"id": "llama", "name": "Llama 3", "description": "Открытая модель от Meta"},
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
        "missions_title": "🎯 **Миссии** 🎯",
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
        "missions_btn_new": "🎯 Миссии",
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
        "missions_btn_new": "🎯 Missions",
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
        "missions_btn_new": "🎯 Миссияләр",
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


def get_language_inline(current_lang: str = 'ru'):
    """Клавиатура выбора языка с отметкой выбранного языка"""
    ru_text = "✅ Русский" if current_lang == "ru" else " Русский"
    en_text = "✅ English" if current_lang == "en" else " English"
    tt_text = "✅ Татарча" if current_lang == "tt" else " Татарча"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ru_text, callback_data="lang_ru")],
        [InlineKeyboardButton(text=en_text, callback_data="lang_en")],
        [InlineKeyboardButton(text=tt_text, callback_data="lang_tt")],
        [InlineKeyboardButton(text=get_text(current_lang, 'back'), callback_data="menu_profile")],
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

async def transcribe_voice_to_text(file_path: str) -> str:
    """
    Распознаёт голосовое сообщение через Vosk.
    Telegram voice (.ogg) сначала конвертируется в mono wav 16kHz.
    """

    wav_path = file_path.replace(".ogg", ".wav")

    try:
        # Конвертируем .ogg -> .wav (mono, 16kHz)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", file_path,
                "-ar", "16000",
                "-ac", "1",
                "-f", "wav",
                wav_path
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        wf = wave.open(wav_path, "rb")

        if wf.getnchannels() != 1 or wf.getframerate() != 16000:
            raise Exception("Vosk требует WAV mono 16kHz")

        rec = KaldiRecognizer(vosk_model, wf.getframerate())
        rec.SetWords(True)

        final_text_parts = []

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get("text"):
                    final_text_parts.append(result["text"])

        final_result = json.loads(rec.FinalResult())
        if final_result.get("text"):
            final_text_parts.append(final_result["text"])

        wf.close()

        text = " ".join(final_text_parts).strip()
        return text

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
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

    # создаём миссии при первом/очередном входе
    await ensure_daily_missions(user_id)
    await ensure_permanent_missions(user_id)

    user_lang = await get_user_language(user_id)

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
        await update_user_coins(user_id, question["reward"])
        text = lt(
            user_lang,
            "quiz_correct",
            reward=question["reward"],
            explanation=question["explanation"][user_lang]
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
        await update_user_coins(user_id, puzzle["reward"])
        text = lt(
            user_lang,
            "prompt_puzzle_correct",
            reward=puzzle["reward"],
            explanation=puzzle["explanation"][user_lang]
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
    ADMIN_ID = 1755580726  # ⚠️ замени на свой Telegram ID

    if message.from_user.id != ADMIN_ID:
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
        if model_id in ["mistral", "qwen", "nemotron", "gptoss"]:
            await state.set_state(AIChatState.waiting_for_message)
            await state.update_data(current_model=model_id)
            await callback.message.edit_text(
                f"{model['name']} {get_text(user_lang, 'ai_activated')}",
                reply_markup=get_exit_ai_inline(user_lang),
                parse_mode="Markdown"
            )
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
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await state.set_state(AIChatState.waiting_for_message)
    await state.update_data(current_model="mistral")
    await callback.message.edit_text(
        f"🌪️ Mistral AI {get_text(user_lang, 'ai_activated')}",
        reply_markup=get_exit_ai_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "ai_model_qwen")
async def start_qwen_chat(callback: CallbackQuery, state: FSMContext):
    """Активирует режим диалога с Qwen"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await state.set_state(AIChatState.waiting_for_message)
    await state.update_data(current_model="qwen")
    await callback.message.edit_text(
        f"🤖 Qwen AI {get_text(user_lang, 'ai_activated')}",
        reply_markup=get_exit_ai_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "ai_model_nemotron")
async def start_nemotron_chat(callback: CallbackQuery, state: FSMContext):
    """Активирует режим диалога с Nemotron"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await state.set_state(AIChatState.waiting_for_message)
    await state.update_data(current_model="nemotron")
    await callback.message.edit_text(
        f"🟢 NVIDIA Nemotron {get_text(user_lang, 'ai_activated')}",
        reply_markup=get_exit_ai_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "ai_model_gptoss")
async def start_gptoss_chat(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await state.set_state(AIChatState.waiting_for_message)
    await state.update_data(current_model="gptoss")
    await callback.message.edit_text(
        f" OpenAI gpt-oss {get_text(user_lang, 'ai_activated')}",
        reply_markup=get_exit_ai_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()

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
    """
    Убирает Markdown-разметку из текста (звездочки, решетки и т.д.)
    """
    # Убираем символы Markdown, такие как *, _, #, ~
    text = re.sub(r'([#_*~`])', '', text)

    return text



@router.message(AIChatState.waiting_for_message)
async def handle_ai_message(message: Message, state: FSMContext):
    """Обрабатывает текст пользователя и отправляет в AI"""
    user_text = message.text or ""
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)

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
                            bot_response = clean_markdown(bot_response)
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
                bot_response = clean_markdown(bot_response)
            else:
                await asyncio.sleep(1)
                if user_lang == "en":
                    bot_response = f"(Qwen demo mode) You wrote: '{user_text}'\nAdd OPENROUTER_API_KEY to .env"
                elif user_lang == "tt":
                    bot_response = f"(Qwen демо режимы) Сез яздыгыз: '{user_text}'\nOPENROUTER_API_KEY ны .env ка өстәгез"
                else:
                    bot_response = f"(Демо-режим Qwen) Вы написали: '{user_text}'\nДобавьте OPENROUTER_API_KEY в .env"


        elif current_model == "nemotron":
            model_name = "nvidia/nemotron-3-super-120b-a12b:free"

            if QWEN_API_KEY:
                bot_response = await call_openrouter_model(
                    api_url=QWEN_API_URL,
                    api_key=QWEN_API_KEY,
                    model="nvidia/nemotron-3-super-120b-a12b:free",
                    user_text=user_text
                )
                bot_response = clean_markdown(bot_response)
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
                bot_response = clean_markdown(bot_response)
            else:
                await asyncio.sleep(1)
                if user_lang == "en":
                    bot_response = f"(gpt-oss demo mode) You wrote: '{user_text}'\nAdd OPENROUTER_API_KEY to .env"
                elif user_lang == "tt":
                    bot_response = f"(gpt-oss демо режимы) Сез яздыгыз: '{user_text}'\nOPENROUTER_API_KEY ны .env ка өстәгез"
                else:
                    bot_response = f"(Демо-режим gpt-oss) Вы написали: '{user_text}'\nДобавьте OPENROUTER_API_KEY в .env"

        await thinking_msg.delete()

        if current_model == "mistral":
            model_emoji = "🌪️"
        elif current_model == "qwen":
            model_emoji = "🤖"
        elif current_model == "nemotron":
            model_emoji = "🟢"
        elif current_model == "gptoss":
            model_emoji = "🧠"
        else:
            model_emoji = "🤖"

        full_text = f"{model_emoji} {current_model.capitalize()}:\n\n{bot_response}"

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



@router.callback_query(F.data == "menu_missions")
async def show_missions(callback: CallbackQuery):
    """Показывает миссии пользователя"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    # Показываем ежедневные миссии

    missions = await get_user_missions(user_id)
    economy = await get_user_economy(user_id)

    text = build_missions_text(user_lang, economy, missions)

    await callback.message.edit_text(
        text,
        reply_markup=get_missions_menu_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()



@router.callback_query(F.data == "menu_profile")
async def show_profile(callback: CallbackQuery):
    """Показывает статистику пользователя"""
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

    await ensure_daily_missions(user_id)
    await ensure_permanent_missions(user_id)
    await track_profile_open(user_id)

    stats = await get_user_profile_stats(user_id)
    economy = await get_user_economy(user_id)

    streak_emoji = "🔥" if stats['streak'] > 0 else "💤"
    premium_badge = "💎 Premium" if stats['is_premium'] else "🆓 Free"

    first_name = callback.from_user.first_name or ""
    last_name = callback.from_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()

    text = get_text(
        user_lang, 'profile',
        user_id=user_id,
        premium_badge=premium_badge,
        coins=economy['coins'],
        streak_emoji=streak_emoji,
        streak=economy['streak'],
        days=stats['days_in_bot']
    )

    if full_name:
        text = text.replace(
            "👤 **Профиль пользователя**",
            f"👤 **Профиль пользователя — {full_name}**"
        ).replace(
            "👤 **User Profile**",
            f"👤 **User Profile — {full_name}**"
        ).replace(
            "👤 **Кулланучы профиле**",
            f"👤 **Кулланучы профиле — {full_name}**"
        )

    text += lt(user_lang, "menu_profile_extra", freeze_count=economy['freeze_count'])

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
    economy = await get_user_economy(user_id)

    text = (
        f"{lt(user_lang, 'streak_title')}\n\n"
        f"{lt(user_lang, 'economy_line', coins=economy['coins'], streak=economy['streak'], freeze_count=economy['freeze_count'])}\n\n"
        f"{lt(user_lang, 'streak_desc')}"
    )

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

    result = await buy_freeze(user_id, price=30, max_freezes=2)

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
    """Перерисовывает меню выбора языка"""
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
    """Изменяет язык и сразу обновляет текущее меню выбора языка"""
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

    await callback.message.edit_text(
        get_text(user_lang, 'tariffs', current='free'),
        reply_markup=get_main_menu_inline(user_lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "menu_games")
async def show_games_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_lang = await get_user_language(user_id)

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
    await message.answer(get_text(user_lang, 'tariffs', current='free'), parse_mode="Markdown")


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
@router.message(Command("prompt"))
async def prompt_review_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)

    await state.set_state(PromptReviewState.waiting_for_prompt)

    await message.answer(
        lt(user_lang, "prompt_review_start")
    )

@router.message(Command("prompt"))
async def prompt_review_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_language(user_id)

    await state.set_state(PromptReviewState.waiting_for_prompt)

    await message.answer(
        get_text(user_lang, "prompt_review_start")
    )


@router.message(PromptReviewState.waiting_for_prompt, F.text)
async def process_prompt_review_text(message: Message, state: FSMContext):
    ADMIN_ID = 1755580726  # твой Telegram ID

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
        await message.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text
        )

        await message.answer(get_text(user_lang, "prompt_review_sent"))
        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Не удалось отправить промпт на редакцию: {e}")

    @router.message(PromptReviewState.waiting_for_prompt, F.voice)
    async def process_prompt_review_voice(message: Message, state: FSMContext):
        ADMIN_ID = 1755580726

        user_id = message.from_user.id
        user_lang = await get_user_language(user_id)

        # 1. Ограничение длины
        if message.voice.duration > 180:
            await message.answer(get_text(user_lang, "prompt_review_voice_too_long"))
            return

        await message.answer(
            get_text(user_lang, "prompt_review_voice_processing")
        )

        try:
            # 2. Получаем файл
            file = await message.bot.get_file(message.voice.file_id)

            file_path = f"temp_voice_{user_id}.ogg"

            # 3. Скачиваем
            await message.bot.download_file(file.file_path, destination=file_path)

            # 4. Распознаем
            text = await transcribe_voice_to_text(file_path)

            if not text.strip():
                await message.answer(get_text(user_lang, "prompt_review_voice_failed"))
                return

            # 5. Формируем сообщение админу
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

            # 6. Отправляем админу
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text
            )

            # 7. Ответ пользователю
            await message.answer(
                f"{get_text(user_lang, 'prompt_review_sent')}\n\n📝 {text}"
            )

            # 8. Удаляем файл
            if os.path.exists(file_path):
                os.remove(file_path)

            await state.clear()

        except Exception as e:
            await message.answer(
                f"{get_text(user_lang, 'prompt_review_voice_failed')}\n\n{e}"
            )


