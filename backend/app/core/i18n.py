from typing import Any, Literal

SupportedLanguage = Literal["en", "ru", "tt"]

DEFAULT_LANGUAGE: SupportedLanguage = "ru"
SUPPORTED_LANGUAGES: tuple[SupportedLanguage, ...] = ("en", "ru", "tt")

_MESSAGES: dict[SupportedLanguage, dict[str, str]] = {
    "en": {
        "errors.validation_failed": "Please check the highlighted fields and try again.",
        "errors.request_failed": "We couldn't complete that action. Please try again.",
        "errors.internal_server_error": "Something went wrong. Please try again or refresh the page.",
        "errors.bad_request": "We couldn't process your details. Please check and try again.",
        "errors.route_not_found": "The requested page was not found.",
        "errors.method_not_allowed": "This action is not available for the requested page.",
        "errors.rate_limited": "Too many requests. Please wait a moment and try again.",
        "errors.service_unavailable": "Service is temporarily unavailable. Please try again soon.",
        "errors.invalid_or_expired_token": "Your session has expired. Please log in again.",
        "errors.user_not_found": "User not found",
        "errors.insufficient_permissions": "You don't have access to this action.",
        "errors.checkout_not_configured": "Checkout is currently unavailable. Please try again later.",
        "errors.billing_not_configured": "Billing is currently unavailable.",
        "errors.plan_not_available": "Selected plan is not available",
        "errors.invalid_plan_for_checkout": "This plan can't be purchased right now.",
        "errors.billing_customer_not_found": "No billing customer found for this account",
        "errors.invalid_webhook_signature": "We couldn't verify the payment update.",
        "errors.invalid_webhook_payload": "We couldn't process the payment update.",
        "errors.onboarding_profile_not_found": "Please complete onboarding first.",
        "errors.email_already_registered": "Email already registered",
        "errors.display_name_already_registered": "Display name is already taken",
        "errors.invalid_display_name": "Display name is required",
        "errors.invalid_credentials": "Invalid email or password",
        "errors.category_create_conflict": "We couldn't create this category. Check the name and parent category.",
        "errors.category_update_conflict": "We couldn't update this category. Check the name and parent category.",
        "errors.category_self_parent": "Category cannot be its own parent",
        "errors.category_has_children": "Remove or move child categories first",
        "errors.category_has_prompts": "Reassign prompts before deleting this category",
        "errors.prompt_not_pending": "This prompt isn't waiting for review.",
        "errors.slug_already_taken": "This link name is already in use.",
        "errors.invalid_use_case": "Some selected use cases are no longer available.",
        "errors.invalid_model_compatibility": "Some selected models are no longer available.",
        "errors.invalid_tag": "Some selected tags are no longer available.",
        "errors.prompt_already_saved": "Prompt already saved",
        "errors.refresh_token_missing": "Your session has ended. Please log in again.",
        "errors.invalid_refresh_token": "Your session has ended. Please log in again.",
        "errors.refresh_token_reused": "Your session has ended. Please log in again.",
        "errors.refresh_token_expired": "Your session has ended. Please log in again.",
        "errors.deprecated_endpoint": "This action is no longer available.",
        "errors.lesson_locked": "Upgrade your plan to open this lesson.",
        "errors.step_locked": "Complete the current step before moving forward.",
        "errors.insufficient_funds": "You need {missing} more LMN to continue.",
        "errors.analytics_ingest_failed": "We couldn't save activity data right now.",
        "errors.moderation_reason_required": "Please add a reason before rejecting this prompt.",
        "errors.submission_rate_limited": "You've reached the submission limit for the last 24 hours.",
        "errors.submission_pending_limit": "You already have too many prompts waiting for review. Please wait for feedback first.",
        "errors.duplicate_submission": "A very similar submission was already sent in the last 24 hours.",
        "errors.submission_too_short": "Please add more detail before submitting.",
        "errors.mission_manual_confirmation_not_allowed": "Mission does not support manual confirmation",
        "errors.streak_recovery_unavailable": "Streak recovery is only available in the same-day recovery window.",
        "errors.store_item_missing": "Purchase item could not be loaded.",
        "errors.store_upgrade_locked": "Upgrade tier is locked until previous tier is owned.",
        "errors.store_item_not_found": "Item is not available right now.",
        "errors.store_item_unavailable": "This item is sold out.",
        "errors.store_item_owned": "You already own this unlock.",
        "errors.wallet_missing": "Wallet could not be loaded.",
        "errors.webhook_processing_failed": "We couldn't complete this payment update.",
        "errors.not_found.default": "The requested item was not found.",
        "errors.not_found.category": "Category not found.",
        "errors.not_found.prompt": "Prompt not found.",
        "errors.not_found.lesson": "Lesson not found.",
        "errors.not_found.user": "Account not found.",
        "errors.not_found.saved_prompt": "Saved prompt not found.",
        "errors.not_found.mission": "Mission not found.",
        "errors.not_found.contributor": "Contributor profile not found.",
    },
    "ru": {
        "errors.validation_failed": "Проверьте заполнение полей и попробуйте снова.",
        "errors.request_failed": "Не удалось выполнить действие. Попробуйте снова.",
        "errors.internal_server_error": "Что-то пошло не так. Попробуйте снова или обновите страницу.",
        "errors.bad_request": "Не удалось обработать данные. Проверьте поля и попробуйте снова.",
        "errors.route_not_found": "Запрошенная страница не найдена.",
        "errors.method_not_allowed": "Это действие недоступно для запрошенной страницы.",
        "errors.rate_limited": "Слишком много запросов. Подождите немного и повторите попытку.",
        "errors.service_unavailable": "Сервис временно недоступен. Попробуйте позже.",
        "errors.invalid_or_expired_token": "Сессия истекла. Войдите снова.",
        "errors.user_not_found": "Пользователь не найден",
        "errors.insufficient_permissions": "Для этого действия недостаточно прав.",
        "errors.checkout_not_configured": "Оплата сейчас недоступна. Попробуйте позже.",
        "errors.billing_not_configured": "Сервис оплаты сейчас недоступен.",
        "errors.plan_not_available": "Выбранный тариф недоступен",
        "errors.invalid_plan_for_checkout": "Этот тариф сейчас нельзя оформить.",
        "errors.billing_customer_not_found": "Для аккаунта не найден биллинговый профиль",
        "errors.invalid_webhook_signature": "Не удалось подтвердить обновление оплаты.",
        "errors.invalid_webhook_payload": "Не удалось обработать обновление оплаты.",
        "errors.onboarding_profile_not_found": "Сначала завершите онбординг.",
        "errors.email_already_registered": "Email уже зарегистрирован",
        "errors.display_name_already_registered": "Это отображаемое имя уже занято",
        "errors.invalid_display_name": "Укажите отображаемое имя",
        "errors.invalid_credentials": "Неверный email или пароль",
        "errors.category_create_conflict": "Не удалось создать категорию. Проверьте название и родительскую категорию.",
        "errors.category_update_conflict": "Не удалось обновить категорию. Проверьте название и родительскую категорию.",
        "errors.category_self_parent": "Категория не может быть родителем самой себя",
        "errors.category_has_children": "Сначала удалите или перенесите дочерние категории",
        "errors.category_has_prompts": "Перед удалением категории переназначьте промпты",
        "errors.prompt_not_pending": "Этот промпт сейчас не ожидает проверки.",
        "errors.slug_already_taken": "Такой адрес уже занят.",
        "errors.invalid_use_case": "Некоторые выбранные сценарии больше недоступны.",
        "errors.invalid_model_compatibility": "Некоторые выбранные модели больше недоступны.",
        "errors.invalid_tag": "Некоторые выбранные теги больше недоступны.",
        "errors.prompt_already_saved": "Промпт уже сохранен",
        "errors.refresh_token_missing": "Сессия истекла. Войдите снова.",
        "errors.invalid_refresh_token": "Сессия истекла. Войдите снова.",
        "errors.refresh_token_reused": "Сессия истекла. Войдите снова.",
        "errors.refresh_token_expired": "Сессия истекла. Войдите снова.",
        "errors.deprecated_endpoint": "Это действие больше недоступно.",
        "errors.lesson_locked": "Откройте более высокий тариф, чтобы получить доступ к уроку.",
        "errors.step_locked": "Сначала завершите текущий шаг, затем переходите дальше.",
        "errors.insufficient_funds": "Не хватает еще {missing} LMN.",
        "errors.analytics_ingest_failed": "Не удалось сохранить данные активности.",
        "errors.moderation_reason_required": "Укажите причину перед отклонением промпта.",
        "errors.submission_rate_limited": "Вы достигли лимита отправок за последние 24 часа.",
        "errors.submission_pending_limit": "У вас уже слишком много промптов на проверке. Дождитесь обратной связи и попробуйте снова.",
        "errors.duplicate_submission": "Очень похожий промпт уже был отправлен за последние 24 часа.",
        "errors.submission_too_short": "Добавьте больше деталей перед отправкой.",
        "errors.mission_manual_confirmation_not_allowed": "Эта миссия не поддерживает ручное подтверждение",
        "errors.streak_recovery_unavailable": "Восстановление серии доступно только в окне восстановления того же дня.",
        "errors.store_item_missing": "Не удалось загрузить товар покупки.",
        "errors.store_upgrade_locked": "Апгрейд уровня доступен только после покупки предыдущего уровня.",
        "errors.store_item_not_found": "Товар сейчас недоступен.",
        "errors.store_item_unavailable": "Этот товар распродан.",
        "errors.store_item_owned": "Этот товар уже куплен.",
        "errors.wallet_missing": "Не удалось загрузить кошелек.",
        "errors.webhook_processing_failed": "Не удалось обработать обновление оплаты.",
        "errors.not_found.default": "Запрошенный объект не найден.",
        "errors.not_found.category": "Категория не найдена.",
        "errors.not_found.prompt": "Промпт не найден.",
        "errors.not_found.lesson": "Урок не найден.",
        "errors.not_found.user": "Аккаунт не найден.",
        "errors.not_found.saved_prompt": "Сохраненный промпт не найден.",
        "errors.not_found.mission": "Миссия не найдена.",
        "errors.not_found.contributor": "Профиль автора не найден.",
    },
    "tt": {
        "errors.validation_failed": "Кырларны тикшереп яңадан җибәрегез.",
        "errors.request_failed": "Бу гамәлне үтәп булмады. Тагын бер кат сынап карагыз.",
        "errors.internal_server_error": "Ниндидер хата килеп чыкты. Яңадан сынап карагыз яки битне яңартыгыз.",
        "errors.bad_request": "Кертелгән мәгълүматны эшкәртеп булмады. Кырларны тикшереп кабатлагыз.",
        "errors.route_not_found": "Соралган бит табылмады.",
        "errors.method_not_allowed": "Бу гамәл соралган бит өчен рөхсәт ителмәгән.",
        "errors.rate_limited": "Сораулар артык күп. Бераз көтеп яңадан сынап карагыз.",
        "errors.service_unavailable": "Сервис вакытлыча эшләми. Соңрак яңадан кереп карагыз.",
        "errors.invalid_or_expired_token": "Сессия вакыты чыкты. Яңадан керегез.",
        "errors.user_not_found": "Кулланучы табылмады",
        "errors.insufficient_permissions": "Бу гамәл өчен хокуклар җитми.",
        "errors.checkout_not_configured": "Түләү хәзер вакытлыча эшләми. Соңрак кабатлап карагыз.",
        "errors.billing_not_configured": "Түләү сервисы вакытлыча эшләми.",
        "errors.plan_not_available": "Сайланган тариф кулланылмый",
        "errors.invalid_plan_for_checkout": "Бу тарифны хәзер рәсмиләштереп булмый.",
        "errors.billing_customer_not_found": "Бу аккаунт өчен биллинг клиенты табылмады",
        "errors.invalid_webhook_signature": "Түләү яңартуын раслап булмады.",
        "errors.invalid_webhook_payload": "Түләү яңартуын эшкәртеп булмады.",
        "errors.onboarding_profile_not_found": "Башта онбордингны тәмамлагыз.",
        "errors.email_already_registered": "Бу email инде теркәлгән",
        "errors.display_name_already_registered": "Бу күрсәтеләчәк исем инде кулланыла",
        "errors.invalid_display_name": "Күрсәтеләчәк исемне кертегез",
        "errors.invalid_credentials": "Email яки серсүз дөрес түгел",
        "errors.category_create_conflict": "Категорияне булдырып булмады. Исемен һәм ата-анасын тикшерегез.",
        "errors.category_update_conflict": "Категорияне яңартып булмады. Исемен һәм ата-анасын тикшерегез.",
        "errors.category_self_parent": "Категория үзенә үзе ата-ана була алмый",
        "errors.category_has_children": "Башта эчке категорияләрне күчерегез яки бетерегез",
        "errors.category_has_prompts": "Категорияне бетергәнче промптларны башка категориягә күчерегез",
        "errors.prompt_not_pending": "Бу промпт хәзер тикшерү көтүендә түгел.",
        "errors.slug_already_taken": "Бу адрес инде кулланыла.",
        "errors.invalid_use_case": "Сайланган кайбер куллану очраклары хәзер юк.",
        "errors.invalid_model_compatibility": "Сайланган кайбер модельләр хәзер юк.",
        "errors.invalid_tag": "Сайланган кайбер теглар хәзер юк.",
        "errors.prompt_already_saved": "Промпт инде сакланган",
        "errors.refresh_token_missing": "Сессия вакыты чыкты. Яңадан керегез.",
        "errors.invalid_refresh_token": "Сессия вакыты чыкты. Яңадан керегез.",
        "errors.refresh_token_reused": "Сессия вакыты чыкты. Яңадан керегез.",
        "errors.refresh_token_expired": "Сессия вакыты чыкты. Яңадан керегез.",
        "errors.deprecated_endpoint": "Бу гамәл инде кулланылмый.",
        "errors.lesson_locked": "Бу дәресне ачу өчен югарырак тариф кирәк.",
        "errors.step_locked": "Алга күчкәнче башта хәзерге адымны тәмамлагыз.",
        "errors.insufficient_funds": "Дәвам итү өчен тагын {missing} LMN кирәк.",
        "errors.analytics_ingest_failed": "Активлык мәгълүматын саклап булмады.",
        "errors.moderation_reason_required": "Промптны кире какканчы сәбәбен языгыз.",
        "errors.submission_rate_limited": "Соңгы 24 сәгать өчен җибәрү лимитына җиттегез.",
        "errors.submission_pending_limit": "Сезнең караудагы промптлар артык күп. Башта фикерне көтегез.",
        "errors.duplicate_submission": "Соңгы 24 сәгатьтә бик охшаш промпт инде җибәрелгән.",
        "errors.submission_too_short": "Җибәргәнче күбрәк деталь өстәгез.",
        "errors.mission_manual_confirmation_not_allowed": "Бу миссия кул белән раслауны хупламый",
        "errors.streak_recovery_unavailable": "Серияне торгызу шул ук көндәге торгызу тәрәзәсендә генә мөмкин.",
        "errors.store_item_missing": "Сатып алу товары йөкләнмәде.",
        "errors.store_upgrade_locked": "Яңа дәрәҗә элекке дәрәҗә сатып алынгач кына ачыла.",
        "errors.store_item_not_found": "Товар хәзер вакытлыча юк.",
        "errors.store_item_unavailable": "Бу товар сатылып беткән.",
        "errors.store_item_owned": "Бу товар сездә инде бар.",
        "errors.wallet_missing": "Капчыкны йөкләп булмады.",
        "errors.webhook_processing_failed": "Түләү яңартуын эшкәртеп булмады.",
        "errors.not_found.default": "Соралган объект табылмады.",
        "errors.not_found.category": "Категория табылмады.",
        "errors.not_found.prompt": "Промпт табылмады.",
        "errors.not_found.lesson": "Дәрес табылмады.",
        "errors.not_found.user": "Аккаунт табылмады.",
        "errors.not_found.saved_prompt": "Сакланган промпт табылмады.",
        "errors.not_found.mission": "Миссия табылмады.",
        "errors.not_found.contributor": "Автор профиле табылмады.",
    },
}


def _detect_language(value: str | None) -> SupportedLanguage | None:
    if not value:
        return None
    normalized = value.strip().lower().replace("_", "-")
    if normalized == "ru" or normalized.startswith("ru-"):
        return "ru"
    if normalized == "tt" or normalized.startswith("tt-"):
        return "tt"
    if normalized == "en" or normalized.startswith("en-"):
        return "en"
    return None


def normalize_language(value: str | None) -> SupportedLanguage:
    return _detect_language(value) or DEFAULT_LANGUAGE


def resolve_language_from_header(header_value: str | None) -> SupportedLanguage:
    if not header_value:
        return DEFAULT_LANGUAGE
    for part in header_value.split(","):
        token = part.strip()
        if not token:
            continue
        lang = _detect_language(token.split(";")[0].strip())
        if lang and lang in SUPPORTED_LANGUAGES:
            return lang
    return DEFAULT_LANGUAGE


def translate(message_key: str, language: SupportedLanguage, params: dict[str, Any] | None = None) -> str | None:
    template = _MESSAGES.get(language, {}).get(message_key)
    if template is None:
        template = _MESSAGES[DEFAULT_LANGUAGE].get(message_key)
    if template is None:
        return None
    if not params:
        return template
    try:
        return template.format(**params)
    except Exception:
        return template
