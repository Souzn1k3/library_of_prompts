from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, keyboard_button, InlineKeyboardMarkup, InlineKeyboardButton, \
     callback_query, CallbackQuery
from aiogram.filters import Command, CommandStart
from html import escape
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_prompts_by_subcategory, set_user_language, add_or_update_user

router = Router()

# ==============================================================================
# FSM СОСТОЯНИЯ ДЛЯ ПОИСКА
# ==============================================================================
class SearchState(StatesGroup):
    waiting_for_query = State()  # Ожидание поискового запроса


# ==============================================================================
# 1. КОНФИГУРАЦИЯ (Единственный источник правды)
# ==============================================================================

# Уникальные ID для каждой категории. Это ключ к работе кнопок.
CATEGORIES_CALLBACKS_RU = {
    "it": "cat_it_ru",
    "marketing": "cat_marketing_ru",
    "business": "cat_business_ru",
    "education": "cat_edu_ru",
    "arts": "cat_arts_ru",
    "engineering": "cat_eng_ru",
    "finance": "cat_fin_ru",
    "law": "cat_law_ru",
    "agro": "cat_agro_ru",
    "logistics": "cat_log_ru",
    "real_estate": "cat_re_ru",
    "lifestyle": "cat_life_ru",
    "niche": "cat_niche_ru",
}

CATEGORIES_CALLBACKS_TAT = {
    "it": "cat_it_tat",
    "marketing": "cat_marketing_tat",
    "business": "cat_business_tat",
    "education": "cat_edu_tat",
    "arts": "cat_arts_tat",
    "engineering": "cat_eng_tat",
    "finance": "cat_fin_tat",
    "law": "cat_law_tat",
    "agro": "cat_agro_tat",
    "logistics": "cat_log_tat",
    "real_estate": "cat_re_tat",
    "lifestyle": "cat_life_tat",
    "niche": "cat_niche_tat",
}

CATEGORIES_CALLBACKS_ENG = {
    "it": "cat_it_eng",
    "marketing": "cat_marketing_eng",
    "business": "cat_business_eng",
    "education": "cat_edu_eng",
    "arts": "cat_arts_eng",
    "engineering": "cat_eng_eng",
    "finance": "cat_fin_eng",
    "law": "cat_law_eng",
    "agro": "cat_agro_eng",
    "logistics": "cat_log_eng",
    "real_estate": "cat_re_eng",
    "lifestyle": "cat_life_eng",
    "niche": "cat_niche_eng",
}

# Данные подкатегорий IT
IT_SUBCATEGORIES_DATA_RU = [
    ("💻 Написание кода", "sub_it_code_ru"),
    ("⚙️ Рефакторинг и оптимизация", "sub_it_refactor_ru"),
    ("🐞 Отладка (Debugging)", "sub_it_debug_ru"),
    ("🧪 Генерация тестов", "sub_it_tests_ru"),
    ("📄 Документация", "sub_it_docs_ru"),
    ("🛠️ DevOps и Инфраструктура", "sub_it_devops_ru"),
    ("🔒 Кибербезопасность", "sub_it_security_ru"),
    ("🗄️ SQL и Работа с БД", "sub_it_sql_ru"),
    ("🏗️ Архитектура ПО", "sub_it_arch_ru"),
]

IT_SUBCATEGORIES_DATA_TAT = [
    ("💻 Код язу", "sub_it_code_tat"),
    ("⚙️ Рефакторинг һәм оптимизация", "sub_it_refactor_tat"),
    ("🐞 Сызыкны төзәтү", "sub_it_debug_tat"),
    ("🧪 Тестлар генерацияләү", "sub_it_tests_tat"),
    ("📄 Документация", "sub_it_docs_tat"),
    ("🛠️ DevOps һәм Инфраструктура", "sub_it_devops_tat"),
    ("🔒 Киберкуркынычсызлык", "sub_it_security_tat"),
    ("🗄️ SQL һәм Мәгълүмат базалары белән эшләү", "sub_it_sql_tat"),
    ("🏗️ Программаларның архитектурасы", "sub_it_arch_tat"),
]

IT_SUBCATEGORIES_DATA_ENG = [
    ("💻 Code writing", "sub_it_code_eng"),
    ("⚙️ Refactoring and optimization", "sub_it_refactor_eng"),
    ("🐞 Debugging", "sub_it_debug_eng"),
    ("🧪 Test generation", "sub_it_tests_eng"),
    ("📄 Documentation", "sub_it_docs_eng"),
    ("🛠️ DevOps and Infrastructure", "sub_it_devops_eng"),
    ("🔒 Cybersecurity", "sub_it_security_eng"),
    ("🗄️ SQL and Working with Databases", "sub_it_sql_eng"),
    ("🏗️ Software Architecture", "sub_it_arch_eng"),
]

MARKETING_SUBCATEGORIES_DATA_RU = [
    ("📝 Контент-маркетинг", "sub_marketing_content_ru"),
    ("🔍 SEO (Поисковая оптимизация)", "sub_marketing_seo_ru"),
    ("✍️ Копирайтинг", "sub_marketing_copywriting_ru"),
    ("📱 SMM (Социальные медиа)", "sub_marketing_smm_ru"),
    ("📊 Аналитика рынка", "sub_marketing_analytics_ru"),
    ("🎯 Персонализация", "sub_marketing_personalization_ru"),
]

MARKETING_SUBCATEGORIES_DATA_TAT = [
    ("📝 Контент-маркетинг", "sub_marketing_content_tat"),
    ("🔍 SEO (эзләү оптимизациясе)", "sub_marketing_seo_tat"),
    ("✍️ Копирайтинг", "sub_marketing_copywriting_tat"),
    ("📱 SMM (Социаль медиа)", "sub_marketing_smm_tat"),
    ("📊 Базар аналитикасы", "sub_marketing_analytics_tat"),
    ("🎯 Шәхсиләштерү", "sub_marketing_personalization_tat"),
]

MARKETING_SUBCATEGORIES_DATA_ENG = [
    ("📝 Content Marketing", "sub_marketing_content_eng"),
    ("🔍 SEO", "sub_marketing_seo_eng"),
    ("✍️ Copywriting", "sub_marketing_copywriting_eng"),
    ("📱 SMM", "sub_marketing_smm_eng"),
    ("📊 Market Analysis", "sub_marketing_analytics_eng"),
    ("🎯 Personalization", "sub_marketing_personalization_eng"),
]

BUSINESS_SUBCATEGORIES_DATA_RU = [
    ("📊 Стратегическое планирование", "sub_business_planning_ru"),
    ("📋 Управление проектами", "sub_business_projects_ru"),
    ("👥 HR и Рекрутинг", "sub_business_hr_ru"),
    ("💰 Продажи (Sales)", "sub_business_sales_ru"),
    ("📈 Финансы и Бухгалтерия", "sub_business_finance_ru"),
    ("⚖️ Юридическая поддержка (Legal Tech)", "sub_business_legal_ru"),
    ("🎧 Поддержка клиентов (Customer Support)", "sub_business_support_ru"),
]
#C ЭТОГО МОМЕНТА НУЖНО ПРОВЕРЯТЬ ТАТАРСКИЙ!!!!!!!!!!!
BUSINESS_SUBCATEGORIES_DATA_TAT = [
    ("📊 Стратегик планлаштыру", "sub_business_planning_tat"),
    ("📋 Проектларны идарә итү", "sub_business_projects_tat"),
    ("👥 HR һәм Рекрутинг", "sub_business_hr_tat"),
    ("💰 Сату", "sub_business_sales_tat"),
    ("📈 Финанс һәм Бухгалтерия", "sub_business_finance_tat"),
    ("⚖️ Юридик ярдәм", "sub_business_legal_tat"),
    ("🎧 Клиентларга ярдәм", "sub_business_support_tat"),
]

BUSINESS_SUBCATEGORIES_DATA_ENG = [
    ("📊 Strategic Planning", "sub_business_planning_eng"),
    ("📋 Project Management", "sub_business_projects_eng"),
    ("👥 HR & Recruiting", "sub_business_hr_eng"),
    ("💰 Sales", "sub_business_sales_eng"),
    ("📈 Finance & Accounting", "sub_business_finance_eng"),
    ("⚖️ Legal Support", "sub_business_legal_eng"),
    ("🎧 Customer Support", "sub_business_support_eng"),
]

EDUCATION_SUBCATEGORIES_DATA_RU = [
    ("📚 Образовательные программы", "sub_education_programs_ru"),
    ("🎓 Онлайн-курсы и E-Learning", "sub_education_online_ru"),
    ("👨‍🏫 Методика преподавания", "sub_education_teaching_ru"),
    ("📝 Оценка и тестирование", "sub_education_testing_ru"),
    ("🔬 Научные исследования", "sub_education_research_ru"),
    ("📖 Учебные материалы", "sub_education_materials_ru"),
    ("🎯 Профориентация", "sub_education_career_ru"),
]

EDUCATION_SUBCATEGORIES_DATA_TAT = [
    ("📚 Белем бирү программалары", "sub_education_programs_tat"),
    ("🎓 Онлайн-курслар һәм E-Learning", "sub_education_online_tat"),
    ("👨‍🏫 Укыту методикасы", "sub_education_teaching_tat"),
    ("📝 Бәяләү һәм тестлау", "sub_education_testing_tat"),
    ("🔬 Фәнни тикшеренүләр", "sub_education_research_tat"),
    ("📖 Уку материаллары", "sub_education_materials_tat"),
    ("🎯 Профориентация", "sub_education_career_tat"),
]

EDUCATION_SUBCATEGORIES_DATA_ENG = [
    ("📚 Educational Programs", "sub_education_programs_eng"),
    ("🎓 Online Courses & E-Learning", "sub_education_online_eng"),
    ("👨‍🏫 Teaching Methodology", "sub_education_teaching_eng"),
    ("📝 Assessment & Testing", "sub_education_testing_eng"),
    ("🔬 Scientific Research", "sub_education_research_eng"),
    ("📖 Learning Materials", "sub_education_materials_eng"),
    ("🎯 Career Guidance", "sub_education_career_eng"),
]


ARTS_SUBCATEGORIES_DATA_RU = [
    ("📚 Литература", "sub_arts_literature_ru"),
    ("🎨 Дизайн и Визуальное искусство", "sub_arts_design_ru"),
    ("🎵 Музыка и Звук", "sub_arts_music_ru"),
    ("🎮 Геймдев (Game Dev)", "sub_arts_gamedev_ru"),
    ("🎬 Видеопродакшн", "sub_arts_video_ru"),
]

ARTS_SUBCATEGORIES_DATA_TAT = [
    ("📚 Әдәбият", "sub_arts_literature_tat"),
    ("🎨 Дизайн һәм Визуаль сәнгать", "sub_arts_design_tat"),
    ("🎵 Музыка һәм Тавыш", "sub_arts_music_tat"),
    ("🎮 Геймдев (Game Dev)", "sub_arts_gamedev_tat"),
    ("🎬 Видео продюсерлык", "sub_arts_video_tat"),
]

ARTS_SUBCATEGORIES_DATA_ENG = [
    ("📚 Literature", "sub_arts_literature_eng"),
    ("🎨 Design & Visual Arts", "sub_arts_design_eng"),
    ("🎵 Music & Sound", "sub_arts_music_eng"),
    ("🎮 Game Dev", "sub_arts_gamedev_eng"),
    ("🎬 Video Production", "sub_arts_video_eng"),
]


ENGINEERING_SUBCATEGORIES_DATA_RU = [
    ("📐 Проектирование (CAD/CAE)", "sub_engineering_cad_ru"),
    ("🏗️ Строительство", "sub_engineering_construction_ru"),
    ("🏭 Производство", "sub_engineering_manufacturing_ru"),
    ("⚡ Энергетика", "sub_engineering_energy_ru"),
    ("🧪 Химическая промышленность", "sub_engineering_chemical_ru"),
]

ENGINEERING_SUBCATEGORIES_DATA_TAT = [
    ("📐 Проектирование (CAD/CAE)", "sub_engineering_cad_tat"),
    ("🏗️ Төзелеш", "sub_engineering_construction_tat"),
    ("🏭 Җитештерү", "sub_engineering_manufacturing_tat"),
    ("⚡ Энергетика", "sub_engineering_energy_tat"),
    ("🧪 Химия сәнәгате", "sub_engineering_chemical_tat"),
]

ENGINEERING_SUBCATEGORIES_DATA_ENG = [
    ("📐 Engineering Design (CAD/CAE)", "sub_engineering_cad_eng"),
    ("🏗️ Construction", "sub_engineering_construction_eng"),
    ("🏭 Manufacturing", "sub_engineering_manufacturing_eng"),
    ("⚡ Energy", "sub_engineering_energy_eng"),
    ("🧪 Chemical Industry", "sub_engineering_chemical_eng"),
]


FINANCE_SUBCATEGORIES_DATA_RU = [
    ("💹 Инвестиции", "sub_finance_investments_ru"),
    ("🏦 Банковское дело", "sub_finance_banking_ru"),
    ("🛡️ Страхование", "sub_finance_insurance_ru"),
    ("🪙 Криптовалюты и Блокчейн", "sub_finance_crypto_ru"),
]

FINANCE_SUBCATEGORIES_DATA_TAT = [
    ("💹 Инвестицияләр", "sub_finance_investments_tat"),
    ("🏦 Банк эше", "sub_finance_banking_tat"),
    ("🛡️ Страховкалау", "sub_finance_insurance_tat"),
    ("🪙 Криптовалюталар һәм Блокчейн", "sub_finance_crypto_tat"),
]

FINANCE_SUBCATEGORIES_DATA_ENG = [
    ("💹 Investments", "sub_finance_investments_eng"),
    ("🏦 Banking", "sub_finance_banking_eng"),
    ("🛡️ Insurance", "sub_finance_insurance_eng"),
    ("🪙 Cryptocurrency & Blockchain", "sub_finance_crypto_eng"),
]

LAW_SUBCATEGORIES_DATA_RU = [
    ("📜 Законодательная деятельность", "sub_law_legislative_ru"),
    ("🏛️ Госуслуги", "sub_law_public_services_ru"),
    ("⚖️ Судебная система", "sub_law_judicial_ru"),
    ("🏙️ Городское планирование", "sub_law_urban_ru"),
]

LAW_SUBCATEGORIES_DATA_TAT = [
    ("📜 Закон чыгару эшчәнлеге", "sub_law_legislative_tat"),
    ("🏛️ Дәүләт хезмәтләре", "sub_law_public_services_tat"),
    ("⚖️ Суд системасы", "sub_law_judicial_tat"),
    ("🏙️ Шәһәр планлаштыру", "sub_law_urban_tat"),
]

LAW_SUBCATEGORIES_DATA_ENG = [
    ("📜 Legislative Activity", "sub_law_legislative_eng"),
    ("🏛️ Public Services", "sub_law_public_services_eng"),
    ("⚖️ Judicial System", "sub_law_judicial_eng"),
    ("🏙️ Urban Planning", "sub_law_urban_eng"),
]


AGRO_SUBCATEGORIES_DATA_RU = [
    ("🌾 Точное земледелие", "sub_agro_precision_ru"),
    ("🐾 Ветеринария", "sub_agro_veterinary_ru"),
    ("🌍 Экология", "sub_agro_ecology_ru"),
    ("🦋 Биоразнообразие", "sub_agro_biodiversity_ru"),
]

AGRO_SUBCATEGORIES_DATA_TAT = [
    ("🌾 Төгез игенчелек", "sub_agro_precision_tat"),
    ("🐾 Ветеринария", "sub_agro_veterinary_tat"),
    ("🌍 Экология", "sub_agro_ecology_tat"),
    ("🦋 Биотөрлелек", "sub_agro_biodiversity_tat"),
]

AGRO_SUBCATEGORIES_DATA_ENG = [
    ("🌾 Precision Agriculture", "sub_agro_precision_eng"),
    ("🐾 Veterinary", "sub_agro_veterinary_eng"),
    ("🌍 Ecology", "sub_agro_ecology_eng"),
    ("🦋 Biodiversity", "sub_agro_biodiversity_eng"),
]

LOGISTICS_SUBCATEGORIES_DATA_RU = [
    ("🚚 Логистика", "sub_logistics_logistics_ru"),
    ("🚗 Транспорт", "sub_logistics_transport_ru"),
    ("✈️ Туризм и Гостеприимство", "sub_logistics_tourism_ru"),
    ("🚆 Авиация и ЖД", "sub_logistics_aviation_ru"),
]

LOGISTICS_SUBCATEGORIES_DATA_TAT = [
    ("🚚 Логистика", "sub_logistics_logistics_tat"),
    ("🚗 Транспорт", "sub_logistics_transport_tat"),
    ("✈️ Туризм һәм Кунакчыллык", "sub_logistics_tourism_tat"),
    ("🚆 Авиация һәм Тимер юл", "sub_logistics_aviation_tat"),
]

LOGISTICS_SUBCATEGORIES_DATA_ENG = [
    ("🚚 Logistics", "sub_logistics_logistics_eng"),
    ("🚗 Transport", "sub_logistics_transport_eng"),
    ("✈️ Tourism & Hospitality", "sub_logistics_tourism_eng"),
    ("🚆 Aviation & Rail", "sub_logistics_aviation_eng"),
]

REAL_ESTATE_SUBCATEGORIES_DATA_RU = [
    ("🏠 Оценка недвижимости", "sub_real_estate_valuation_ru"),
    ("🔑 Управление объектами", "sub_real_estate_management_ru"),
    ("📢 Маркетинг объектов", "sub_real_estate_marketing_ru"),
]

REAL_ESTATE_SUBCATEGORIES_DATA_TAT = [
    ("🏠 Милекне бәяләү", "sub_real_estate_valuation_tat"),
    ("🔑 Объектларны идарә итү", "sub_real_estate_management_tat"),
    ("📢 Объектлар маркетингы", "sub_real_estate_marketing_tat"),
]

REAL_ESTATE_SUBCATEGORIES_DATA_ENG = [
    ("🏠 Property Valuation", "sub_real_estate_valuation_eng"),
    ("🔑 Property Management", "sub_real_estate_management_eng"),
    ("📢 Property Marketing", "sub_real_estate_marketing_eng"),
]

LIFESTYLE_SUBCATEGORIES_DATA_RU = [
    ("⏰ Планирование времени", "sub_lifestyle_time_ru"),
    ("💪 Здоровье и Фитнес", "sub_lifestyle_health_ru"),
    ("❤️ Отношения и Психология", "sub_lifestyle_relationships_ru"),
    ("🎨 Хобби и Саморазвитие", "sub_lifestyle_hobbies_ru"),
    ("🏠 Быт", "sub_lifestyle_household_ru"),
]

LIFESTYLE_SUBCATEGORIES_DATA_TAT = [
    ("⏰ Вакытны планлаштыру", "sub_lifestyle_time_tat"),
    ("💪 Сәламәтлек һәм Фитнес", "sub_lifestyle_health_tat"),
    ("❤️ Мөнәсәбәтләр һәм Психология", "sub_lifestyle_relationships_tat"),
    ("🎨 Хобби һәм Үз-үзеңне үстерү", "sub_lifestyle_hobbies_tat"),
    ("🏠 Көнкүреш", "sub_lifestyle_household_tat"),
]

LIFESTYLE_SUBCATEGORIES_DATA_ENG = [
    ("⏰ Time Management", "sub_lifestyle_time_eng"),
    ("💪 Health & Fitness", "sub_lifestyle_health_eng"),
    ("❤️ Relationships & Psychology", "sub_lifestyle_relationships_eng"),
    ("🎨 Hobbies & Self-Development", "sub_lifestyle_hobbies_eng"),
    ("🏠 Household & Daily Life", "sub_lifestyle_household_eng"),
]

NICHE_SUBCATEGORIES_DATA_RU = [
    ("🔮 Астрология и Эзотерика", "sub_niche_astrology_ru"),
    ("⚽ Спорт", "sub_niche_sports_ru"),
    ("🤝 Благотворительность и НКО", "sub_niche_charity_ru"),
]

NICHE_SUBCATEGORIES_DATA_TAT = [
    ("🔮 Астрология һәм Эзотерика", "sub_niche_astrology_tat"),
    ("⚽ Спорт", "sub_niche_sports_tat"),
    ("🤝 Хәйрия һәм НКО", "sub_niche_charity_tat"),
]

NICHE_SUBCATEGORIES_DATA_ENG = [
    ("🔮 Astrology & Esoterics", "sub_niche_astrology_eng"),
    ("⚽ Sports", "sub_niche_sports_eng"),
    ("🤝 Charity & NGO", "sub_niche_charity_eng"),
]

# ==============================================================================
# 2. КЛАВИАТУРЫ (Исправленные callback_data)
# ==============================================================================

def get_main_reply_inline():
    """Меню языков"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Русский", callback_data="lang_ru", style = "danger"),
            InlineKeyboardButton(text="Татарча", callback_data="lang_tat", style = "success"),
            InlineKeyboardButton(text="English", callback_data="lang_en", style = "primary"),
        ],
        [InlineKeyboardButton(text=" Профиль", callback_data="menu_profile")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="menu_search")],
    ])


def get_categories_ru():
    """
    Меню категорий RU.
    ВАЖНО: Здесь используются ID из CATEGORIES_CALLBACKS, а не хардкод.
    """
    inline_keyboard = [
        [InlineKeyboardButton(text="💻 Информационные технологии и Разработка ПО",
                              callback_data=CATEGORIES_CALLBACKS_RU["it"])],
        [InlineKeyboardButton(text="📣 Маркетинг, Реклама и PR", callback_data=CATEGORIES_CALLBACKS_RU["marketing"])],
        [InlineKeyboardButton(text="🧑‍💼 Бизнес, Менеджмент и Предпринимательство",
                              callback_data=CATEGORIES_CALLBACKS_RU["business"])],
        [InlineKeyboardButton(text="🧑‍🔬 Образование и Наука", callback_data=CATEGORIES_CALLBACKS_RU["education"])],
        [InlineKeyboardButton(text="🎨 Творчество, Искусство и Медиа", callback_data=CATEGORIES_CALLBACKS_RU["arts"])],
        [InlineKeyboardButton(text="🏗️ Инженерия, Строительство и Производство",
                              callback_data=CATEGORIES_CALLBACKS_RU["engineering"])],
        [InlineKeyboardButton(text="💳 Финансы, Банкинг и Страхование", callback_data=CATEGORIES_CALLBACKS_RU["finance"])],
        [InlineKeyboardButton(text="🏛️ Государственное управление и Право", callback_data=CATEGORIES_CALLBACKS_RU["law"])],
        [InlineKeyboardButton(text="🧑‍🌾 Сельское хозяйство и Экология", callback_data=CATEGORIES_CALLBACKS_RU["agro"])],
        [InlineKeyboardButton(text="🚚 Логистика, Транспорт и Туризм", callback_data=CATEGORIES_CALLBACKS_RU["logistics"])],
        [InlineKeyboardButton(text="🏠 Недвижимость", callback_data=CATEGORIES_CALLBACKS_RU["real_estate"])],
        [InlineKeyboardButton(text="🎯 Персональная эффективность и Lifestyle",
                              callback_data=CATEGORIES_CALLBACKS_RU["lifestyle"])],
        [InlineKeyboardButton(text="👓 Специализированные и Нишевые области",
                              callback_data=CATEGORIES_CALLBACKS_RU["niche"])],
        [InlineKeyboardButton(text="🔙 Назад к языкам", callback_data="back_lang")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_categories_tat():
    """Меню категорий TAT (пока структура аналогична RU для примера)"""
    # В реальном проекте здесь должны быть свои уникальные callback_data, например cat_it_tat
    inline_keyboard = [
        [InlineKeyboardButton(text="💻Мәгълүмат технологияләре һәм программалар төзелеше💻", callback_data=CATEGORIES_CALLBACKS_TAT["it"])],
        [InlineKeyboardButton(text="📣Маркетинг, реклама һәм пиар📣", callback_data=CATEGORIES_CALLBACKS_TAT["marketing"])],
        [InlineKeyboardButton(text="🧑‍💼Бизнес, менеджмендә һәм керәстәнлек🧑‍💼", callback_data=CATEGORIES_CALLBACKS_TAT["business"])],
        [InlineKeyboardButton(text="🧑‍🔬Белем һәм фән🧑‍🔬", callback_data=CATEGORIES_CALLBACKS_TAT["education"])],
        [InlineKeyboardButton(text="🎨Иҗат, сәнгать һәм мәгълүмат чаралары🎨", callback_data=CATEGORIES_CALLBACKS_TAT["arts"])],
        [InlineKeyboardButton(text="🏗️Инженерлык, төзелеш һәм әзерләү🏗️", callback_data=CATEGORIES_CALLBACKS_TAT["engineering"])],
        [InlineKeyboardButton(text="💳Финанслар, банк эшчәнлеге һәм страховкалау💳", callback_data=CATEGORIES_CALLBACKS_TAT["finance"])],
        [InlineKeyboardButton(text="🏛️Дәүләт идарәсе һәм хокук🏛️", callback_data=CATEGORIES_CALLBACKS_TAT["law"])],
        [InlineKeyboardButton(text="🧑‍🌾Ауыл хуҗалыгы һәм экология🧑‍🌾", callback_data=CATEGORIES_CALLBACKS_TAT["agro"])],
        [InlineKeyboardButton(text="🚚Логистика, транспорты һәм туризм🚚", callback_data=CATEGORIES_CALLBACKS_TAT["logistics"])],
        [InlineKeyboardButton(text="🏠Эман-эштәр🏠", callback_data=CATEGORIES_CALLBACKS_TAT["real_estate"])],
        [InlineKeyboardButton(text="🎯Шәхси нәтижәлелек һәм тирә-як тормыш тарзи🎯", callback_data=CATEGORIES_CALLBACKS_TAT["lifestyle"])],
        [InlineKeyboardButton(text="👓Арнайы һәм ниша өлкәләре👓", callback_data=CATEGORIES_CALLBACKS_TAT["niche"])],
        [InlineKeyboardButton(text="🔙 артка 🔙", callback_data="back_lang")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_categories_eng():
    """Меню категорий EN"""
    inline_keyboard = [
        [InlineKeyboardButton(text="💻Information Technology & Software Development💻",
                              callback_data=CATEGORIES_CALLBACKS_ENG["it"])],
        [InlineKeyboardButton(text="📣Marketing, Advertising & PR📣",
                              callback_data=CATEGORIES_CALLBACKS_ENG["marketing"])],
        [InlineKeyboardButton(text="🧑‍💼Business, Management & Entrepreneurship🧑‍💼",
                              callback_data=CATEGORIES_CALLBACKS_ENG["business"])],
        [InlineKeyboardButton(text="🧑‍🔬Education & Science🧑‍🔬", callback_data=CATEGORIES_CALLBACKS_ENG["education"])],
        [InlineKeyboardButton(text="🎨Creative Arts & Media🎨",
                              callback_data=CATEGORIES_CALLBACKS_ENG["arts"])],
        [InlineKeyboardButton(text="🏗️Engineering, Construction & Manufacturing🏗️",
                              callback_data=CATEGORIES_CALLBACKS_ENG["engineering"])],
        [InlineKeyboardButton(text="💳Finance, Banking & Insurance💳",
                              callback_data=CATEGORIES_CALLBACKS_ENG["finance"])],
        [InlineKeyboardButton(text="🏛️Public Administration & Law🏛️", callback_data=CATEGORIES_CALLBACKS_ENG["law"])],
        [InlineKeyboardButton(text="🧑‍🌾Agriculture & Ecology🧑‍🌾", callback_data=CATEGORIES_CALLBACKS_ENG["agro"])],
        [InlineKeyboardButton(text="🚚Logistics, Transport & Tourism🚚",
                              callback_data=CATEGORIES_CALLBACKS_ENG["logistics"])],
        [InlineKeyboardButton(text="🏠Real Estate🏠", callback_data=CATEGORIES_CALLBACKS_ENG["real_estate"])],
        [InlineKeyboardButton(text="🎯Personal Development & Lifestyle🎯",
                              callback_data=CATEGORIES_CALLBACKS_ENG["lifestyle"])],
        [InlineKeyboardButton(text="👓Specialized & Niche Fields👓", callback_data=CATEGORIES_CALLBACKS_ENG["niche"])],
        [InlineKeyboardButton(text="🔙 Back 🔙", callback_data="back_lang")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def get_profile_menu_inline(lang="ru"):
    """Меню профиля"""
    if lang == "tat":
        kb = [
            [InlineKeyboardButton(text="🌐 Теле: Татарча", callback_data="profile_lang_tat")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main_menu")],
        ]
    elif lang == "eng":
        kb = [
            [InlineKeyboardButton(text="🌐 Language: English", callback_data="profile_lang_eng")],
            [InlineKeyboardButton(text="📊 Statistics", callback_data="profile_stats")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back_main_menu")],
        ]
    else:
        kb = [
            [InlineKeyboardButton(text="🌐 Язык: Русский", callback_data="profile_lang_ru")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main_menu")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_main_menu_inline():
    """Главное меню с кнопкой Каталог"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Каталог", callback_data="menu_catalog"),
        InlineKeyboardButton(text="🔍 Поиск", callback_data="menu_search")
         ],
        [InlineKeyboardButton(text="📚 Обучение", callback_data="menu_learning"),
        InlineKeyboardButton(text="💎 Тарифы", callback_data="menu_tariffs")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile")],
    ])

def get_it_subcategories_keyboard_RU():
    """Подкатегории IT"""
    keyboard = []
    for text, callback in IT_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_it_subcategories_keyboard_TAT():
    """Подкатегории IT"""
    keyboard = []
    for text, callback in IT_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_it_subcategories_keyboard_ENG():
    """Подкатегории IT"""
    keyboard = []
    for text, callback in IT_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)




def get_marketing_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in MARKETING_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_marketing_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in MARKETING_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_marketing_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in MARKETING_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_business_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in BUSINESS_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_business_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in BUSINESS_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_business_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in BUSINESS_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_education_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in EDUCATION_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_education_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in EDUCATION_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_education_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in EDUCATION_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_arts_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in ARTS_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_arts_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in ARTS_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_arts_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in ARTS_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_engineering_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in ENGINEERING_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_engineering_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in ENGINEERING_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_engineering_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in ENGINEERING_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_finance_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in FINANCE_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_finance_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in FINANCE_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_finance_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in FINANCE_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_law_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in LAW_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_law_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in LAW_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_law_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in LAW_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_agro_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in AGRO_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_agro_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in AGRO_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_agro_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in AGRO_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_logistics_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in LOGISTICS_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_logistics_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in LOGISTICS_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_logistics_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in LOGISTICS_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_real_estate_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in REAL_ESTATE_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_real_estate_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in REAL_ESTATE_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_real_estate_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in REAL_ESTATE_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_lifestyle_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in LIFESTYLE_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_lifestyle_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in LIFESTYLE_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_lifestyle_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in LIFESTYLE_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_niche_subcategories_keyboard_RU():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in NICHE_SUBCATEGORIES_DATA_RU:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_niche_subcategories_keyboard_TAT():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in NICHE_SUBCATEGORIES_DATA_TAT:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Артка", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_niche_subcategories_keyboard_ENG():
    """Подкатегории маркетинг"""
    keyboard = []
    for text, callback in NICHE_SUBCATEGORIES_DATA_ENG:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_lang")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==============================================================================
# ПОИСК ПО ПОДКАТЕГОРИЯМ
# ==============================================================================
def get_all_subcategories():
    """Возвращает все подкатегории для поиска"""
    all_subs = []
    for text, callback in IT_SUBCATEGORIES_DATA_RU + IT_SUBCATEGORIES_DATA_TAT + IT_SUBCATEGORIES_DATA_ENG:
        all_subs.append((text, callback))
    for text, callback in MARKETING_SUBCATEGORIES_DATA_RU + MARKETING_SUBCATEGORIES_DATA_TAT + MARKETING_SUBCATEGORIES_DATA_ENG:
        all_subs.append((text, callback))
    for text, callback in BUSINESS_SUBCATEGORIES_DATA_RU + BUSINESS_SUBCATEGORIES_DATA_TAT + BUSINESS_SUBCATEGORIES_DATA_ENG:
        all_subs.append((text, callback))
    return all_subs


def search_subcategories(query: str, limit: int = 10):
    """Ищет подкатегории по ключевому слову"""
    all_subs = get_all_subcategories()
    query_lower = query.lower().strip()
    results = []
    for text, callback in all_subs:
        if query_lower in text.lower():
            results.append((text, callback))
            if len(results) >= limit:
                break
    return results


def get_search_results_keyboard(results):
    """Создаёт клавиатуру с результатами поиска"""
    keyboard = []
    for text, callback in results:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад к поиску", callback_data="menu_search")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



# ==============================================================================
# 3. ХЕНДЛЕРЫ (Логика)
# ==============================================================================

# --- ВЫБОР ЯЗЫКА ---

@router.callback_query(F.data == "lang_ru")
async def categories_rus(callback: CallbackQuery):
    await callback.message.edit_text("📂 **Выберите категорию промптов** 📂",
                                     reply_markup=get_categories_ru(),
                                     parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "lang_tat")
async def categories_tat(callback: CallbackQuery):
    await callback.message.edit_text("📂 **Промптлар категориясен сайлагыз** 📂",
                                     reply_markup=get_categories_tat(),
                                     parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "lang_en")
async def categories_eng(callback: CallbackQuery):
    await callback.message.edit_text("📂 **Select prompts category** 📂",
                                     reply_markup=get_categories_eng(),
                                     parse_mode="Markdown")
    await callback.answer()


# --- ВЫБОР КАТЕГОРИИ ---

@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["it"])
async def show_it_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА IT.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_it_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["it"])
async def show_it_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА IT.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_it_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["it"])
async def show_it_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА IT.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_it_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()




@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["marketing"])
async def show_marketing_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_marketing_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["marketing"])
async def show_marketing_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_marketing_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["marketing"])
async def show_marketing_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_marketing_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["business"])
async def show_business_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_business_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["business"])
async def show_business_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_business_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["business"])
async def show_business_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_business_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["education"])
async def show_education_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_education_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["education"])
async def show_education_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_education_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["education"])
async def show_education_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_education_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["arts"])
async def show_arts_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_arts_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["arts"])
async def show_arts_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_arts_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["arts"])
async def show_arts_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_arts_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["engineering"])
async def show_engineering_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_engineering_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["engineering"])
async def show_engineering_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_engineering_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["engineering"])
async def show_engineering_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_engineering_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["finance"])
async def show_finance_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_finance_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["finance"])
async def show_finance_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_finance_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["finance"])
async def show_finance_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_finance_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["law"])
async def show_law_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_law_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["law"])
async def show_law_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_law_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["law"])
async def show_law_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_law_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["agro"])
async def show_agro_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_agro_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["agro"])
async def show_agro_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_agro_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["agro"])
async def show_agro_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_agro_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["logistics"])
async def show_logistics_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_logistics_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["logistics"])
async def show_logistics_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_logistics_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["logistics"])
async def show_logistics_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_logistics_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["real_estate"])
async def show_real_estate_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_real_estate_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["real_estate"])
async def show_real_estate_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_real_estate_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["real_estate"])
async def show_real_estate_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_real_estate_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["lifestyle"])
async def show_lifestyle_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_lifestyle_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["lifestyle"])
async def show_lifestyle_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_lifestyle_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["lifestyle"])
async def show_lifestyle_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_lifestyle_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_RU["niche"])
async def show_niche_subcategories_ru(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Выберите направление**\n\n",
        reply_markup=get_niche_subcategories_keyboard_RU(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_TAT["niche"])
async def show_niche_subcategories_tat(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркентинге .
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Юнәлешне сайлагыз**\n\n",
        reply_markup=get_niche_subcategories_keyboard_TAT(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == CATEGORIES_CALLBACKS_ENG["niche"])
async def show_niche_subcategories_eng(callback: CallbackQuery):
    """
    СРАБАТЫВАЕТ ТОЛЬКО НА маркетинге.
    Теперь callback_data совпадает с тем, что в кнопке.
    """
    await callback.message.edit_text(
        "**Choose a direction**\n\n",
        reply_markup=get_niche_subcategories_keyboard_ENG(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "menu_catalog")
async def menu_catalog(callback: CallbackQuery):
    """Показывает выбор языка для каталога"""
    await callback.message.edit_text(
        "📚 **Каталог промптов**\n\nВыберите язык:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский", callback_data="lang_ru", style = "danger"),
                InlineKeyboardButton(text="Татарча", callback_data="lang_tat", style = "success"),
                InlineKeyboardButton(text="English", callback_data="lang_en", style = "primary"),
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")],
        ])
    )
    await callback.answer()


# --- ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ---
@router.callback_query(F.data == "menu_profile")
async def menu_profile(callback: CallbackQuery):
    """Показывает статистику пользователя"""
    from database import get_user_premium_status, get_user_profile_stats

    user_id = callback.from_user.id

    # Получаем статус премиум
    is_premium = await get_user_premium_status(user_id)

    # Получаем полную статистику
    stats = await get_user_profile_stats(user_id)

    # Формируем текст
    if is_premium:
        status_text = "💎 **Premium**"
        status_emoji = "✅"
    else:
        status_text = "🆓 **Free**"
        status_emoji = "⏳"

    text = (
        f"👤 **Профиль пользователя**\n\n"
        f"ID: `{user_id}`\n"
        f"Статус: {status_text} {status_emoji}\n\n"
        f"📊 **Статистика**:\n"
        f"📝 Предложенных промптов: {stats['prompts_submitted']}\n"
        f"💾 Сохранённых промптов: {stats['prompts_saved']}\n"
        f"📅 ударный режим: {stats['days_in_bot']}\n\n"
    )

    # Клавиатура профиля
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Тарифы", callback_data="tariff_premium")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")],
    ])

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()




# --- ПОДКАТЕГОРИИ IT ---


@router.callback_query(F.data.startswith("sub_it_"))
async def process_it_subcategory(callback: CallbackQuery):
    from database import get_prompts_by_subcategory, set_user_language

    user_id = callback.from_user.id
    callback_data = callback.data

    # 1. Определяем язык
    if callback_data.endswith("_ru"):
        data_dict = dict(IT_SUBCATEGORIES_DATA_RU)
        text_title = "<b>Выбрано:</b>"
        language = "ru"
    elif callback_data.endswith("_tat"):
        data_dict = dict(IT_SUBCATEGORIES_DATA_TAT)
        text_title = "<b>Сайланган:</b>"
        language = "tat"
    else:
        data_dict = dict(IT_SUBCATEGORIES_DATA_ENG)
        text_title = "<b>Selected:</b>"
        language = "eng"

    # 2. Сохраняем язык пользователя в БД
    await set_user_language(user_id, language)

    # 3. Получаем название подкатегории
    subcat_name = escape(data_dict.get(callback_data, callback_data))

    # 4. Запрашиваем промпты из БД
    prompts = await get_prompts_by_subcategory(callback_data, language)

    if not prompts:
        await callback.message.edit_text(
            f"{text_title} {subcat_name}\n\n⚠️ В этом разделе пока нет промптов.",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"{text_title} {subcat_name}\n\n✅ Найдено промптов: {len(prompts)}",
            parse_mode="HTML"
        )
        # Отправляем каждый промпт отдельным сообщением
        for prompt in prompts:
            text = f"📌 <b>{escape(prompt['title'])}</b>\n\n{escape(prompt['content'])}"
            if prompt['is_premium']:
                text += "\n\n🔒 <i>Premium Content</i>"
            await callback.message.answer(text, parse_mode="HTML")

    await callback.answer()


# --- НАВИГАЦИЯ НАЗАД ---

@router.callback_query(F.data == "back_to_categories_ru")
async def back_to_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "📂 **Выберите категорию промптов** 📂",
        reply_markup=get_categories_ru(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_categories_tat")
async def back_to_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "📂 **Выберите категорию промптов** 📂",
        reply_markup=get_categories_tat(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_categories_eng")
async def back_to_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "📂 **Выберите категорию промптов** 📂",
        reply_markup=get_categories_eng(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_lang")
async def back_to_languages(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌐 **Выберите язык / Тел сайлагыз / Select language:** 🌐",
        reply_markup=get_main_reply_inline(),
        parse_mode="Markdown"
    )
    await callback.answer()


# --- МЕНЮ ПОИСКА (ВКЛЮЧАЕТ СОСТОЯНИЕ) ---
@router.callback_query(F.data == "menu_search")
async def menu_search(callback: CallbackQuery, state: FSMContext):
    """Показывает меню поиска и включает режим поиска"""
    await state.set_state(SearchState.waiting_for_query)
    await callback.message.edit_text(
        "🔍 **Поиск по подкатегориям**\n\n"
        "Введите ключевое слово для поиска:\n\n"
        "Примеры:\n"
        "• `код` → Написание кода, Код язу\n"
        "• `SEO` → SEO оптимизация\n"
        "• `дизайн` → Дизайн и визуальное искусство\n\n"
        "⌨️ Просто напишите слово в чат:\n\n"
        "❌ Чтобы отменить поиск, нажмите /cancel",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_lang")]
        ])
    )
    await callback.answer()


# --- ОБРАБОТКА ПОИСКОВОГО ЗАПРОСА (ТОЛЬКО КОГДА АКТИВНО СОСТОЯНИЕ) ---
@router.message(SearchState.waiting_for_query)
async def handle_search_query(message: Message, state: FSMContext):
    """Обрабатывает текстовые сообщения ТОЛЬКО когда активен поиск"""
    query = message.text.strip()

    # Ищем подкатегории
    results = search_subcategories(query, limit=10)

    if not results:
        await message.answer(
            "❌ **Ничего не найдено**\n\n"
            f"По запросу: `{escape(query)}`\n\n"
            "Попробуйте другое ключевое слово.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="menu_search")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="back_lang")],
            ])
        )
    else:
        await message.answer(
            f"✅ **Найдено: {len(results)}**\n\n"
            f"По запросу: `{escape(query)}`\n\n"
            "Выберите подкатегорию:",
            parse_mode="Markdown",
            reply_markup=get_search_results_keyboard(results)
        )

    # ✅ СБРАСЫВАЕМ СОСТОЯНИЕ ПОСЛЕ ПОИСКА
    await state.clear()


# --- ОТМЕНА ПОИСКА ---
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отменяет поиск"""
    await state.clear()
    await message.answer(
        "❌ Поиск отменен",
        reply_markup=get_main_reply_inline()
    )

# --- START ---


@router.message(F.text.lower() == "каталог")
async def hello(message: Message):
   await message.answer(f"Выберете язык", parse_mode="Markdown", reply_markup=get_main_reply_inline())


@router.message(Command("site"))
async def site(message: Message):
   await message.answer("наш сайт:")

@router.message(Command("about"))
async def about(message: Message):
   await message.answer("Копилка промптов - это (@prompts_souz_bot) медиа агрегатор промптов для искуственного интелекта.\n\n"
                        "Основан в 2026 году.\n\n"
                        "Страна: Российская Федерация (Регион: Республика Татарстан)\n\nКопилка промптов  – это  проект, "
                        "распространяющий информацию на платформе Телеграм (Telegram).\n"
                        "Миссия Копилка промптов (КП) состоит в  продвижении информации по промпт инженерии.\n"
                        "Копилка промптов стремится придерживаться самых высоких стандартов в подаче материалов.\n\n"
                        "Команда (КП): Гимадеев Дамир(@Souzn1k3) основатель проекта"
                        "и студент КФУ(ИТИС).\n Лебедев Глеб(@tfmot) помощник в проекте и главный тестировщик.\n\n ПО ВСЕМ ВОПРОСАМ (@Souzn1k3)!")


@router.message(Command("news"))
async def news(message: Message):
   await message.answer("новости сервиса")


@router.message(Command("stickers"))
async def stickers(message: Message):
   await message.answer("https://t.me/addstickers/Souz4_by_fStikBot")

@router.message(Command("report"))
async def site(message: Message):
   await message.answer("собщите об ошибке:")

@router.message(Command("help"))
async def site(message: Message):
    await message.answer("опишите проблему: ")


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Главное меню бота"""
    user_id = message.from_user.id
    full_name = message.from_user.full_name

    # Сохраняем пользователя в БД
    await add_or_update_user(
        user_id=user_id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or ""
    )

    await message.answer(
        f"👋 **Привет, {escape(full_name)}!**\n\n"
        f"Это **Копилка Промптов** - профессиональный каталог\nпромптов и техник:\n"
        f"от zero-shot до chain-of-thought,\n"
        f"организованный для обучения и реальных задач.",
        parse_mode="Markdown",
        reply_markup=get_main_menu_inline()
    )








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