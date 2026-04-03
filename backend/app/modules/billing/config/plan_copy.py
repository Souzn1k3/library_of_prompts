from app.infrastructure.db.models import PlanTier


BILLING_PLAN_COPY: dict[str, dict[PlanTier, dict[str, object]]] = {
    "en": {
        PlanTier.free: {
            "name": "Free",
            "highlights": [
                "Unlimited free prompts",
                "2 paid prompt unlocks per month",
                "Buy with Lumens or direct checkout",
            ],
            "full_features": [
                "Unlimited access to free prompts",
                "2 permanent paid prompt unlocks every billing window",
                "Save prompts, track submissions, and collect reviews",
                "Buy paid prompts with Lumens or direct checkout",
                "Publish prompts with optional pricing",
            ],
        },
        PlanTier.starter: {
            "name": "Starter",
            "highlights": [
                "15 paid prompt unlocks per month",
                "5% money discount on direct prompt buys",
                "8% Lumen discount on paid prompts",
            ],
            "full_features": [
                "Everything in Free",
                "15 permanent paid prompt unlocks every billing window",
                "5% discount on direct paid prompt purchases",
                "8% discount when buying paid prompts with Lumens",
                "Starter access to premium prompt catalog flow",
                "Low-friction plan for first marketplace conversion",
            ],
        },
        PlanTier.pro: {
            "name": "Pro",
            "highlights": [
                "60 paid prompt unlocks per month",
                "12% money discount on direct prompt buys",
                "15% Lumen discount and Pro learning access",
            ],
            "full_features": [
                "Everything in Starter",
                "60 permanent paid prompt unlocks every billing window",
                "12% discount on direct paid prompt purchases",
                "15% discount on Lumen prompt purchases",
                "Restricted categories and full lesson library",
                "Priority moderation for active contributors",
            ],
        },
        PlanTier.enterprise: {
            "name": "MAX",
            "highlights": [
                "90 paid prompt unlocks per month",
                "15% money discount on direct prompt buys",
                "20% Lumen discount and creator-first value",
            ],
            "full_features": [
                "Everything in Pro",
                "90 permanent paid prompt unlocks every billing window",
                "15% discount on direct paid prompt purchases",
                "20% discount on Lumen prompt purchases",
                "Best plan for heavy buyers and active marketplace sellers",
                "Highest included marketplace value at 1200 RUB",
            ],
        },
    },
    "ru": {
        PlanTier.free: {
            "name": "Free",
            "highlights": [
                "Безлимитные бесплатные промпты",
                "2 платных разблокировки в месяц",
                "Покупка за Lumens или через оплату",
            ],
            "full_features": [
                "Безлимитный доступ к бесплатным промптам",
                "2 постоянные платные разблокировки в каждом расчетном окне",
                "Сохранение промптов, сабмиты и отзывы",
                "Покупка платных промптов за Lumens или через оплату",
                "Публикация промптов с опциональной ценой",
            ],
        },
        PlanTier.starter: {
            "name": "Starter",
            "highlights": [
                "15 платных разблокировок в месяц",
                "Скидка 5% на прямую покупку промптов",
                "Скидка 8% при покупке за Lumens",
            ],
            "full_features": [
                "Все из Free",
                "15 постоянных платных разблокировок в каждом расчетном окне",
                "Скидка 5% на прямые покупки платных промптов",
                "Скидка 8% на покупки платных промптов за Lumens",
                "Комфортный вход в платный маркетплейс",
                "Лучшее соотношение цены и первого апгрейда",
            ],
        },
        PlanTier.pro: {
            "name": "Pro",
            "highlights": [
                "60 платных разблокировок в месяц",
                "Скидка 12% на прямые покупки",
                "Скидка 15% за Lumens и доступ Pro-контента",
            ],
            "full_features": [
                "Все из Starter",
                "60 постоянных платных разблокировок в каждом расчетном окне",
                "Скидка 12% на прямые покупки платных промптов",
                "Скидка 15% на покупки за Lumens",
                "Ограниченные категории и полная библиотека уроков",
                "Приоритетная модерация для активных авторов",
            ],
        },
        PlanTier.enterprise: {
            "name": "MAX",
            "highlights": [
                "90 платных разблокировок в месяц",
                "Скидка 15% на прямые покупки",
                "Скидка 20% за Lumens и максимум ценности",
            ],
            "full_features": [
                "Все из Pro",
                "90 постоянных платных разблокировок в каждом расчетном окне",
                "Скидка 15% на прямые покупки платных промптов",
                "Скидка 20% на покупки за Lumens",
                "Максимальная ценность для постоянных покупателей и авторов",
                "Лучший баланс каталога, обучения и маркетплейса",
            ],
        },
    },
    "tt": {
        PlanTier.free: {
            "name": "Бушлай",
            "highlights": [
                "Бушлай промптларга чиксез керү",
                "Ай саен 2 түләүле ачыш",
                "Lumens яки туры түләү белән алу",
            ],
            "full_features": [
                "Бушлай промптларга чиксез керү",
                "Һәр исәпләү чорында 2 даими түләүле ачыш",
                "Промпт саклау, җибәрү һәм бәяләмәләр",
                "Lumens яки туры түләү белән сатып алу",
                "Бәя кую белән промпт бастыру",
            ],
        },
        PlanTier.starter: {
            "name": "Starter",
            "highlights": [
                "Ай саен 15 түләүле ачыш",
                "Туры сатып алуга 5% ташлама",
                "Lumens белән алганда 8% ташлама",
            ],
            "full_features": [
                "Free планындагы барлык мөмкинлекләр",
                "Һәр исәпләү чорында 15 даими түләүле ачыш",
                "Туры түләүле промпт алуга 5% ташлама",
                "Lumens белән алганда 8% ташлама",
                "Түләүле маркетплейска җиңел керү",
                "Беренче апгрейд өчен иң уңай бәя",
            ],
        },
        PlanTier.pro: {
            "name": "Pro",
            "highlights": [
                "Ай саен 60 түләүле ачыш",
                "Туры сатып алуга 12% ташлама",
                "Lumens белән 15% ташлама һәм Pro керү",
            ],
            "full_features": [
                "Starter мөмкинлекләренең барысы да",
                "Һәр исәпләү чорында 60 даими түләүле ачыш",
                "Туры түләүле промпт алуга 12% ташлама",
                "Lumens белән алганда 15% ташлама",
                "Чикләнгән категорияләр һәм дәресләрнең тулы китапханәсе",
                "Актив авторлар өчен өстен модерация",
            ],
        },
        PlanTier.enterprise: {
            "name": "MAX",
            "highlights": [
                "Ай саен 90 түләүле ачыш",
                "Туры сатып алуга 15% ташлама",
                "Lumens белән 20% ташлама һәм иң зур кыйммәт",
            ],
            "full_features": [
                "Pro мөмкинлекләренең барысы да",
                "Һәр исәпләү чорында 90 даими түләүле ачыш",
                "Туры түләүле промпт алуга 15% ташлама",
                "Lumens белән алганда 20% ташлама",
                "Даими сатып алучылар һәм авторлар өчен иң көчле план",
                "Каталог, уку һәм маркетплейс өчен иң яхшы баланс",
            ],
        },
    },
}
