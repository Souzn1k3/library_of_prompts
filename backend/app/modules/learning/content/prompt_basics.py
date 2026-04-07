from __future__ import annotations

from app.modules.learning.content.common import tr

_BASE_TEXT_VALIDATOR = {
    "type": "text",
    "pass_score": 70,
    "min_words": 35,
    "required_markers": ["[ROLE]", "[CONTEXT]", "[TASK]", "[CONSTRAINTS]", "[OUTPUT]"],
    "bonus_markers": ["[CHECK]", "[EXAMPLE]"],
    "forbidden_phrases": ["any format", "as you wish", "whatever works", "сделай нормально"],
}


def _quiz(
    *,
    question: dict[str, str],
    a: dict[str, str],
    b: dict[str, str],
    c: dict[str, str],
    exp_a: dict[str, str],
    exp_b: dict[str, str],
    exp_c: dict[str, str],
) -> dict:
    return {
        "type": "choice",
        "pass_score": 100,
        "question": question,
        "choices": [
            {"id": "a", "text": a, "explanation": exp_a},
            {"id": "b", "text": b, "explanation": exp_b},
            {"id": "c", "text": c, "explanation": exp_c},
        ],
        "correct_choices": ["b"],
    }


PROMPT_BASICS_COURSE = {
    "slug": "prompt-engineering-foundations",
    "title": tr(
        "Basics of Prompt Engineering",
        "Основы промпт-инжиниринга",
        "Промпт-инжиниринг нигезләре",
    ),
    "subtitle": tr(
        "From vague requests to reliable AI results",
        "От размытых запросов к стабильному результату",
        "Төгәл булмаган сораудан ышанычлы нәтиҗәгә",
    ),
    "description": tr(
        "A practical flagship course: write clear prompts, validate output quality, and build an iteration loop you can use in real tasks.",
        "Флагманский практический курс: научитесь писать ясные промпты, проверять качество ответа и строить итерационный цикл для реальных задач.",
        "Практик флагман курс: ачык промптлар төзергә, җавап сыйфатын тикшерергә һәм реаль эш өчен итерация циклы корырга өйрәнегез.",
    ),
    "difficulty": "beginner",
    "estimated_minutes": 320,
    "is_free": True,
    "course_reward_lmn": 140,
    "lesson_default_reward_lmn": 20,
    "badge_code": "learning.prompt_foundations",
    "certificate_template": "prompt-foundations-v1",
    "what_you_will_learn": [
        tr(
            "Turn ambiguous tasks into structured prompt briefs",
            "Превращать размытую задачу в структурированный бриф для промпта",
            "Билгесез биремне структур промпт-брифка әйләндерү",
        ),
        tr(
            "Use role, context, constraints, and output format intentionally",
            "Осознанно использовать роль, контекст, ограничения и формат ответа",
            "Роль, контекст, чикләү һәм җавап форматын аңлы куллану",
        ),
        tr(
            "Evaluate and improve AI responses with fast quality loops",
            "Оценивать и улучшать ответы ИИ через быстрые циклы качества",
            "ИИ җавапларын тиз сыйфат циклы белән яхшырту",
        ),
    ],
    "modules": [
        {
            "slug": "core-prompt-design",
            "title": tr("Core Prompt Design", "Базовый дизайн промпта", "Промптның төп дизайны"),
            "summary": tr(
                "Build prompt structure that survives different tasks and models.",
                "Соберите структуру промпта, которая работает в разных задачах и моделях.",
                "Төрле бирем һәм модельдә эшли торган промпт структурасын төзегез.",
            ),
            "lessons": [
                {
                    "slug": "pe-foundations",
                    "title": tr(
                        "What Makes a Prompt Work",
                        "Что делает промпт рабочим",
                        "Промптны нәтиҗәле итүче нәрсә",
                    ),
                    "summary": tr(
                        "Define outcome, audience, and minimum quality signal before writing.",
                        "Перед написанием промпта определите результат, аудиторию и минимальный сигнал качества.",
                        "Промпт язганчы нәтиҗә, аудитория һәм минималь сыйфат сигналын билгеләгез.",
                    ),
                    "estimated_minutes": 28,
                    "reward_lmn": 18,
                    "is_final_assessment": False,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "pe-foundations-theory",
                            "kind": "theory",
                            "title": tr("Micro-theory", "Мини-теория", "Мини-теория"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "Strong prompts define the job before the wording.",
                                    "Сильный промпт сначала определяет задачу, а потом формулировку.",
                                    "Көчле промпт башта эшне билгели, аннары формулировканы.",
                                ),
                                tr(
                                    "Use a short brief: target result, user context, constraints, output format.",
                                    "Используйте краткий бриф: результат, контекст, ограничения, формат ответа.",
                                    "Кыска бриф кулланыгыз: нәтиҗә, контекст, чикләү, җавап форматы.",
                                ),
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "pe-foundations-guided",
                            "kind": "guided_practice",
                            "title": tr("Guided Practice", "Практика с опорой", "Юнәлешле практика"),
                            "estimated_minutes": 8,
                            "content": [
                                tr(
                                    "Rewrite this request into a structured prompt: 'Help me study better.'",
                                    "Перепишите запрос в структурированный промпт: «Помоги мне лучше учиться».",
                                    "Бу сорауны структур промптка әйләндерегез: «Укуда яхшырак булыш».",
                                )
                            ],
                            "task": tr(
                                "Your answer must include markers [ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT], [CHECK]. Fill each marker with concrete details, not placeholders.",
                                "В вашем ответе обязательно используйте маркеры [ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT], [CHECK]. Каждый маркер нужно заполнить конкретикой, а не шаблоном.",
                                "Җавапта [ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT], [CHECK] маркерлары мәҗбүри. Һәр маркер эченә конкрет мәгълүмат языгыз.",
                            ),
                            "placeholder": tr(
                                "[ROLE] You are a calm study coach for high-school students.\n[CONTEXT] I prepare for biology twice a week and lose focus after 20 minutes.\n[TASK] Build a 7-day study plan with micro-sessions and one review block.\n[CONSTRAINTS] Keep each day under 30 minutes and include 1 rest day.\n[OUTPUT] Return a table: day | focus | task | time.\n[CHECK] At the end, verify that every day has a clear action and a measurable result.",
                                "[ROLE] Ты спокойный учебный коуч для старшеклассника.\n[CONTEXT] Я готовлюсь к биологии 2 раза в неделю и теряю фокус через 20 минут.\n[TASK] Составь план на 7 дней с микро-сессиями и блоком повторения.\n[CONSTRAINTS] Каждый день до 30 минут, добавь 1 день отдыха.\n[OUTPUT] Верни таблицу: день | фокус | действие | время.\n[CHECK] В конце проверь, что у каждого дня есть конкретное действие и измеримый результат.",
                                "[ROLE] Син югары сыйныф укучысы өчен тыныч уку коучы.\n[CONTEXT] Мин биологиягә атнасына 2 тапкыр әзерләнәм һәм 20 минуттан соң игътибар югала.\n[TASK] 7 көнлек микро-сессияле план төзе.\n[CONSTRAINTS] Һәр көн 30 минуттан артмасын, 1 ял көне булсын.\n[OUTPUT] Таблица: көн | фокус | эш | вакыт.\n[CHECK] Ахырда һәр көн өчен ачык гамәл һәм үлчәнә торган нәтиҗә барлыгын тикшер.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "weak_area_tags": ["structure", "goal-definition"],
                            },
                        },
                        {
                            "slug": "pe-foundations-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 5,
                            "submission": _quiz(
                                question=tr(
                                    "Which version is most likely to produce stable output?",
                                    "Какой вариант с большей вероятностью даст стабильный результат?",
                                    "Кайсы вариант тотрыклырак нәтиҗә бирер?",
                                ),
                                a=tr(
                                    "Write something useful about biology.",
                                    "Напиши что-нибудь полезное про биологию.",
                                    "Биология турында файдалы нәрсә яз.",
                                ),
                                b=tr(
                                    "You are a tutor. Explain one biology topic for grade 8 in 5 bullets and add one mini-quiz.",
                                    "Ты тьютор. Объясни одну тему по биологии для 8 класса в 5 пунктах и добавь мини-квиз.",
                                    "Син тьютор. 8 сыйныф өчен биология темасын 5 пункт белән аңлат һәм мини-квиз өстә.",
                                ),
                                c=tr(
                                    "Give an answer about science.",
                                    "Дай ответ про науку.",
                                    "Фән турында җавап бир.",
                                ),
                                exp_a=tr(
                                    "Too vague: no role, level, or format.",
                                    "Слишком размыто: нет роли, уровня и формата.",
                                    "Артык томан: роль, дәрәҗә, формат юк.",
                                ),
                                exp_b=tr(
                                    "Correct: role, scope, level, and output format are clear.",
                                    "Верно: четко заданы роль, объем, уровень и формат ответа.",
                                    "Дөрес: роль, күләм, дәрәҗә һәм формат ачык.",
                                ),
                                exp_c=tr(
                                    "Still broad and under-specified.",
                                    "Все еще слишком общее и не конкретное.",
                                    "Әле дә артык гомуми һәм төгәл түгел.",
                                ),
                            ),
                        },
                        {
                            "slug": "pe-foundations-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 7,
                            "content": [
                                tr(
                                    "Take a real task from your week and draft a prompt you can run today.",
                                    "Возьмите реальную задачу этой недели и соберите промпт, который можно запустить сегодня.",
                                    "Бу атнадагы реаль эшегезне алыгыз һәм бүген үк кулланып була торган промпт төзегез.",
                                )
                            ],
                            "task": tr(
                                "Write a practical prompt using markers [ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT]. Explain the real task and expected result in concrete words.",
                                "Напишите прикладной промпт с маркерами [ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT]. Опишите реальную задачу и ожидаемый результат конкретно.",
                                "Практик промпт языгыз: [ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT]. Реаль бурычны һәм көтелгән нәтиҗәне төгәл күрсәтегез.",
                            ),
                            "placeholder": tr(
                                "[ROLE] ...\n[CONTEXT] ...\n[TASK] ...\n[CONSTRAINTS] ...\n[OUTPUT] ...",
                                "[ROLE] ...\n[CONTEXT] ...\n[TASK] ...\n[CONSTRAINTS] ...\n[OUTPUT] ...",
                                "[ROLE] ...\n[CONTEXT] ...\n[TASK] ...\n[CONSTRAINTS] ...\n[OUTPUT] ...",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 45,
                                "weak_area_tags": ["transfer", "task-translation"],
                            },
                        },
                        {
                            "slug": "pe-foundations-reflection",
                            "kind": "reflection",
                            "title": tr("Reflection", "Рефлексия", "Рефлексия"),
                            "estimated_minutes": 3,
                            "content": [
                                tr(
                                    "Name one prompt block you still skip and how it affects output quality.",
                                    "Назовите один блок, который вы чаще всего пропускаете, и как это влияет на качество ответа.",
                                    "Еш калдырган бер промпт блогын һәм аның сыйфатка ничек тәэсир итүен языгыз.",
                                )
                            ],
                            "task": tr(
                                "Reflection is needed to identify your weak point before the next lesson. Write one skipped block + one concrete change for your next prompt.",
                                "Рефлексия нужна, чтобы зафиксировать слабое место перед следующим уроком. Напишите: какой блок пропускаете и что конкретно измените в следующем промпте.",
                                "Рефлексия киләсе дәрес алдыннан көчсез урынны табу өчен кирәк. Кайсы блокны калдырасыз һәм киләсе промптта нәрсә үзгәртәчәксез - шуны языгыз.",
                            ),
                            "placeholder": tr(
                                "I often skip [OUTPUT], so my answers become vague. In my next prompt I will add a strict output format with an example.",
                                "Я часто пропускаю [OUTPUT], поэтому ответы получаются размытыми. В следующем промпте добавлю строгий формат ответа и пример.",
                                "Мин еш [OUTPUT] блогын калдырам, шуңа җавап томан була. Киләсе промптта төгәл формат һәм мисал өстим.",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 60,
                                "min_words": 12,
                                "required_markers": [],
                                "bonus_markers": [],
                                "forbidden_phrases": [],
                                "weak_area_tags": ["self-awareness"],
                            },
                        },
                    ],
                },
                {
                    "slug": "pe-structure-pattern",
                    "title": tr(
                        "Role-Context-Task-Output Pattern",
                        "Паттерн Role-Context-Task-Output",
                        "Role-Context-Task-Output паттерны",
                    ),
                    "summary": tr(
                        "Use a repeatable pattern to reduce randomness in model output.",
                        "Используйте повторяемый паттерн, чтобы уменьшить случайность ответа модели.",
                        "Модель җавабындагы очраклылыкны киметү өчен кабатлана торган паттерн кулланыгыз.",
                    ),
                    "estimated_minutes": 30,
                    "reward_lmn": 20,
                    "is_final_assessment": False,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "pe-structure-theory",
                            "kind": "theory",
                            "title": tr("Pattern Logic", "Логика паттерна", "Паттерн логикасы"),
                            "estimated_minutes": 6,
                            "content": [
                                tr(
                                    "Role sets perspective, context sets boundaries, task sets action, output sets shape.",
                                    "Role задает перспективу, context — границы, task — действие, output — форму результата.",
                                    "Role перспектива бирә, context чик куя, task эш билгели, output форма бирә.",
                                )
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "pe-structure-guided",
                            "kind": "guided_practice",
                            "title": tr("Build with the Pattern", "Соберите по паттерну", "Паттерн буенча төзегез"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Create a prompt for planning a one-week study sprint. Use all required markers.",
                                "Соберите промпт для планирования учебного спринта на неделю. Используйте все обязательные маркеры.",
                                "Бер атналык уку спринтын планлау өчен промпт төзегез. Барлык маркерларны кулланыгыз.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "weak_area_tags": ["pattern-usage", "planning"],
                            },
                        },
                        {
                            "slug": "pe-structure-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr(
                                    "What block is missing: '[ROLE] Career coach [TASK] Build a roadmap [OUTPUT] table'?",
                                    "Какой блок отсутствует: '[ROLE] Карьерный коуч [TASK] Построй roadmap [OUTPUT] таблица'?",
                                    "Кайсы блок җитми: '[ROLE] Карьера коучы [TASK] План төзе [OUTPUT] таблица'?",
                                ),
                                a=tr("[CHECK]", "[CHECK]", "[CHECK]"),
                                b=tr("[CONTEXT]", "[CONTEXT]", "[CONTEXT]"),
                                c=tr("[EXAMPLE]", "[EXAMPLE]", "[EXAMPLE]"),
                                exp_a=tr(
                                    "Useful but optional for minimum structure.",
                                    "Полезно, но не обязательно для минимальной структуры.",
                                    "Файдалы, ләкин минималь структура өчен мәҗбүри түгел.",
                                ),
                                exp_b=tr(
                                    "Correct: without context the task scope is unclear.",
                                    "Верно: без контекста неясен масштаб задачи.",
                                    "Дөрес: контекстсыз бирем кысасы ачык түгел.",
                                ),
                                exp_c=tr(
                                    "Examples help, but context is more critical here.",
                                    "Примеры помогают, но здесь важнее контекст.",
                                    "Мисал ярдәм итә, ләкин монда контекст мөһимрәк.",
                                ),
                            ),
                        },
                        {
                            "slug": "pe-structure-applied",
                            "kind": "applied_exercise",
                            "title": tr("Prompt Template Draft", "Черновик шаблона", "Шаблон каралама"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Write a reusable template with placeholders like <topic>, <audience>, <time_limit>.",
                                "Напишите переиспользуемый шаблон с плейсхолдерами <topic>, <audience>, <time_limit>.",
                                "<topic>, <audience>, <time_limit> кебек плейсхолдерлар белән кабат кулланыла торган шаблон языгыз.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 40,
                                "bonus_markers": ["<topic>", "<audience>", "<time_limit>"],
                                "weak_area_tags": ["templating", "reuse"],
                            },
                        },
                        {
                            "slug": "pe-structure-reflection",
                            "kind": "reflection",
                            "title": tr("Quick Synthesis", "Быстрый синтез", "Тиз синтез"),
                            "estimated_minutes": 4,
                            "task": tr(
                                "In one sentence: why is output format not a cosmetic detail?",
                                "Одним предложением: почему формат ответа — это не косметика?",
                                "Бер җөмлә белән: ни өчен җавап форматы вак деталь түгел?",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 60,
                                "min_words": 10,
                                "required_markers": [],
                                "bonus_markers": [],
                                "forbidden_phrases": [],
                                "weak_area_tags": ["concept-linking"],
                            },
                        },
                    ],
                },
                {
                    "slug": "pe-constraints-and-examples",
                    "title": tr(
                        "Constraints and Examples",
                        "Ограничения и примеры",
                        "Чикләүләр һәм мисаллар",
                    ),
                    "summary": tr(
                        "Control quality without over-constraining the model.",
                        "Контролируйте качество, не «ломая» модель чрезмерными ограничениями.",
                        "Модельне артык кысмыйча сыйфатны контрольдә тотыгыз.",
                    ),
                    "estimated_minutes": 34,
                    "reward_lmn": 24,
                    "is_final_assessment": True,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "pe-constraints-theory",
                            "kind": "theory",
                            "title": tr("Theory", "Теория", "Теория"),
                            "estimated_minutes": 6,
                            "content": [
                                tr(
                                    "Constraints should guide output, not suffocate reasoning.",
                                    "Ограничения должны направлять ответ, а не «душить» рассуждение.",
                                    "Чикләү җавапны юнәлтсен, фикер йөртүне томаламасын.",
                                ),
                                tr(
                                    "Examples reduce ambiguity if they represent the target style.",
                                    "Примеры снижают неоднозначность, если отражают целевой стиль.",
                                    "Мисаллар максат стильне чагылдырса, аңлашылмаучылыкны киметә.",
                                ),
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "pe-constraints-guided",
                            "kind": "guided_practice",
                            "title": tr("Constraint Practice", "Практика ограничений", "Чикләү практикасы"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Write a prompt for 'summarize an article' with exactly 4 constraints and one output example.",
                                "Напишите промпт для «суммаризируй статью» с ровно 4 ограничениями и одним примером выхода.",
                                "«Мәкаләне кыскача яз» өчен нәкъ 4 чикләү һәм бер чыгыш мисалы булган промпт төзегез.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 45,
                                "required_markers": [
                                    "[ROLE]",
                                    "[CONTEXT]",
                                    "[TASK]",
                                    "[CONSTRAINTS]",
                                    "[OUTPUT]",
                                    "[EXAMPLE]",
                                ],
                                "weak_area_tags": ["constraints", "example-design"],
                            },
                        },
                        {
                            "slug": "pe-constraints-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 5,
                            "submission": _quiz(
                                question=tr(
                                    "Which constraint improves quality without reducing flexibility too much?",
                                    "Какое ограничение улучшает качество, но не убивает гибкость?",
                                    "Кайсы чикләү сыйфатны арттыра һәм артык кысмый?",
                                ),
                                a=tr(
                                    "Answer only with one word.",
                                    "Отвечай только одним словом.",
                                    "Бер сүз белән генә җавап бир.",
                                ),
                                b=tr(
                                    "Return 5 bullets, each with action + rationale.",
                                    "Верни 5 пунктов, в каждом действие + обоснование.",
                                    "5 пункт кайтар, һәрберсендә эш + нигезләмә булсын.",
                                ),
                                c=tr(
                                    "Use exactly 900 words every time.",
                                    "Всегда используй ровно 900 слов.",
                                    "Һәрвакыт төгәл 900 сүз куллан.",
                                ),
                                exp_a=tr(
                                    "Too restrictive for most tasks.",
                                    "Слишком ограничивает полезность.",
                                    "Файдалы җавапны артык чикли.",
                                ),
                                exp_b=tr(
                                    "Correct: quality criterion is explicit, flexibility remains.",
                                    "Верно: критерий качества задан, но гибкость сохранена.",
                                    "Дөрес: сыйфат критерие ачык, әмма сыгылмалылык саклана.",
                                ),
                                exp_c=tr(
                                    "Word-count rigidity hurts relevance.",
                                    "Жесткий объем часто вредит релевантности.",
                                    "Каты күләм чикләве еш кына релевантлыкны төшерә.",
                                ),
                            ),
                        },
                        {
                            "slug": "pe-constraints-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Scenario", "Прикладной сценарий", "Кулланма сценарий"),
                            "estimated_minutes": 9,
                            "task": tr(
                                "You lead a small team. Draft a prompt to generate a weekly status report format.",
                                "Вы ведете небольшую команду. Соберите промпт для генерации формата еженедельного статуса.",
                                "Сез кечкенә команда алып барасыз. Атналык статус форматы өчен промпт төзегез.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 50,
                                "bonus_markers": ["risk", "next step", "deadline", "[CHECK]"],
                                "weak_area_tags": ["work-transfer", "reporting"],
                            },
                        },
                        {
                            "slug": "pe-constraints-final-checkpoint",
                            "kind": "final_checkpoint",
                            "title": tr("Module Final Checkpoint", "Финальная проверка модуля", "Модульнең финал тикшерүе"),
                            "estimated_minutes": 6,
                            "task": tr(
                                "Produce a polished prompt with all markers and a success metric in [CHECK].",
                                "Соберите финальный промпт со всеми маркерами и метрикой успеха в [CHECK].",
                                "Барлык маркер белән һәм [CHECK] эчендә уңыш метрикасы белән финал промпт әзерләгез.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 55,
                                "required_markers": [
                                    "[ROLE]",
                                    "[CONTEXT]",
                                    "[TASK]",
                                    "[CONSTRAINTS]",
                                    "[OUTPUT]",
                                    "[CHECK]",
                                ],
                                "pass_score": 75,
                                "weak_area_tags": ["module-1-synthesis"],
                            },
                        },
                    ],
                },
            ],
        },
        {
            "slug": "iteration-and-quality",
            "title": tr("Iteration and Quality", "Итерация и качество", "Итерация һәм сыйфат"),
            "summary": tr(
                "Build a loop: draft, test, diagnose, and improve.",
                "Постройте цикл: черновик, тест, диагностика, улучшение.",
                "Цикл төзегез: каралама, тест, диагностика, яхшырту.",
            ),
            "lessons": [
                {
                    "slug": "pe-iteration-loop",
                    "title": tr(
                        "Prompt Iteration Loop",
                        "Итерационный цикл промпта",
                        "Промпт итерация циклы",
                    ),
                    "summary": tr(
                        "Run short iterations instead of rewriting from scratch.",
                        "Используйте короткие итерации вместо полного переписывания.",
                        "Тулы яңадан язу урынына кыска итерация кулланыгыз.",
                    ),
                    "estimated_minutes": 30,
                    "reward_lmn": 20,
                    "is_final_assessment": False,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "pe-iteration-theory",
                            "kind": "theory",
                            "title": tr("Iteration Model", "Модель итерации", "Итерация моделе"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "Use a loop: Run 1 -> identify failure -> edit one block -> run again.",
                                    "Используйте цикл: запуск 1 -> обнаружение сбоя -> правка одного блока -> запуск 2.",
                                    "Цикл кулланыгыз: 1 нче запуск -> проблема -> бер блокны төзәтү -> яңадан запуск.",
                                )
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "pe-iteration-guided",
                            "kind": "guided_practice",
                            "title": tr("Guided Iteration", "Управляемая итерация", "Юнәлешле итерация"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Start from your previous prompt and produce Version A + Version B with one targeted change.",
                                "Возьмите прошлый промпт и сделайте Version A + Version B с одной целевой правкой.",
                                "Алдагы промпттан башлап Version A + Version B ясагыз, бер максатчан үзгәреш белән.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 45,
                                "bonus_markers": ["Version A", "Version B", "changed block"],
                                "weak_area_tags": ["iteration", "diagnostics"],
                            },
                        },
                        {
                            "slug": "pe-iteration-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr(
                                    "What is the best first move after a weak response?",
                                    "Что лучше сделать первым шагом после слабого ответа?",
                                    "Көчсез җаваптан соң беренче иң яхшы адым нинди?",
                                ),
                                a=tr(
                                    "Rewrite the whole prompt immediately.",
                                    "Сразу переписать весь промпт.",
                                    "Шунда ук бөтен промптны яңадан язу.",
                                ),
                                b=tr(
                                    "Identify one failure mode and adjust only one block.",
                                    "Найти один тип ошибки и скорректировать только один блок.",
                                    "Бер хата төрен табып, бер блокны гына төзәтү.",
                                ),
                                c=tr(
                                    "Switch to another model without diagnosis.",
                                    "Сменить модель без диагностики.",
                                    "Диагнозсыз башка модельгә күчү.",
                                ),
                                exp_a=tr(
                                    "Too noisy: you lose causal signal.",
                                    "Слишком шумно: теряется причинная связь.",
                                    "Артык зур үзгәреш: сәбәп сигналын югалтасыз.",
                                ),
                                exp_b=tr(
                                    "Correct: controlled change makes learning measurable.",
                                    "Верно: контролируемое изменение делает обучение измеримым.",
                                    "Дөрес: контрольле үзгәреш өйрәнүне үлчәнә торган итә.",
                                ),
                                exp_c=tr(
                                    "Model switch can help later, not as first step.",
                                    "Смена модели может помочь позже, но не первым шагом.",
                                    "Модельне алыштыру соңрак булыша ала, ләкин беренче адым түгел.",
                                ),
                            ),
                        },
                        {
                            "slug": "pe-iteration-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 9,
                            "task": tr(
                                "Write a mini debug prompt that asks the model to explain why its previous answer failed.",
                                "Сделайте мини debug-промпт, где модель объясняет, почему прошлый ответ был слабым.",
                                "Модельдән алдагы җавап нигә көчсез булганын аңлату өчен mini debug-промпт төзегез.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 42,
                                "weak_area_tags": ["debugging", "meta-prompting"],
                            },
                        },
                        {
                            "slug": "pe-iteration-reflection",
                            "kind": "reflection",
                            "title": tr("Reflection", "Рефлексия", "Рефлексия"),
                            "estimated_minutes": 4,
                            "task": tr(
                                "What block do you change first most often, and why?",
                                "Какой блок вы чаще меняете первым и почему?",
                                "Сез иң элек кайсы блокны үзгәртәсез һәм нигә?",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 60,
                                "min_words": 14,
                                "required_markers": [],
                                "bonus_markers": [],
                                "forbidden_phrases": [],
                                "weak_area_tags": ["reflection-loop"],
                            },
                        },
                    ],
                },
                {
                    "slug": "pe-evaluate-quality",
                    "title": tr("Evaluate Response Quality", "Оценка качества ответа", "Җавап сыйфатын бәяләү"),
                    "summary": tr(
                        "Use fast rubrics to detect weak answers early.",
                        "Используйте быстрые рубрики, чтобы рано замечать слабые ответы.",
                        "Көчсез җавапны иртә табу өчен тиз рубрика кулланыгыз.",
                    ),
                    "estimated_minutes": 30,
                    "reward_lmn": 20,
                    "is_final_assessment": False,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "pe-quality-theory",
                            "kind": "theory",
                            "title": tr("Quality Rubric", "Рубрика качества", "Сыйфат рубрикасы"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "Evaluate by relevance, completeness, factual safety, and actionability.",
                                    "Оценивайте по релевантности, полноте, фактической корректности и применимости.",
                                    "Релевантлык, тулылык, факт куркынычсызлыгы һәм куллану мөмкинлеге буенча бәяләгез.",
                                )
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "pe-quality-guided",
                            "kind": "guided_practice",
                            "title": tr("Rubric Practice", "Практика по рубрике", "Рубрика практикасы"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Write a prompt that forces the model to self-score on 4 criteria at the end.",
                                "Соберите промпт, который заставит модель самооценить ответ по 4 критериям.",
                                "Модель җавап ахырында 4 критерий буенча үзе бәя бирерлек промпт төзегез.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 40,
                                "bonus_markers": ["score", "criterion", "1-5"],
                                "weak_area_tags": ["evaluation", "quality-control"],
                            },
                        },
                        {
                            "slug": "pe-quality-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr(
                                    "Which criterion best captures practical usefulness?",
                                    "Какой критерий лучше отражает практическую полезность?",
                                    "Кайсы критерий практик файданы яхшырак чагылдыра?",
                                ),
                                a=tr("Long answer length", "Большой объем текста", "Озын текст күләме"),
                                b=tr("Actionability", "Применимость (Actionability)", "Кулланыла алу (Actionability)"),
                                c=tr("Poetic style", "Поэтичность", "Поэтик стиль"),
                                exp_a=tr(
                                    "Length alone says little about quality.",
                                    "Объем сам по себе не говорит о качестве.",
                                    "Күләм үзе генә сыйфат турында әйтми.",
                                ),
                                exp_b=tr(
                                    "Correct: can the user act on the output now?",
                                    "Верно: можно ли сразу действовать по результату?",
                                    "Дөрес: нәтиҗә буенча хәзер үк эшләп буламы?",
                                ),
                                exp_c=tr(
                                    "Style can help but does not guarantee utility.",
                                    "Стиль важен, но не гарантирует полезность.",
                                    "Стиль ярдәм итә, ләкин файдалылыкны гарантияләми.",
                                ),
                            ),
                        },
                        {
                            "slug": "pe-quality-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 9,
                            "task": tr(
                                "Create a prompt for feedback on a resume and require a final score + top 3 fixes.",
                                "Сделайте промпт для обратной связи по резюме и потребуйте итоговый score + топ-3 правки.",
                                "Резюме буенча фикер алу өчен промпт төзегез: финал бәя + топ-3 төзәтмә мәҗбүри.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 44,
                                "weak_area_tags": ["assessment-transfer"],
                            },
                        },
                        {
                            "slug": "pe-quality-reflection",
                            "kind": "reflection",
                            "title": tr("Reflection", "Рефлексия", "Рефлексия"),
                            "estimated_minutes": 4,
                            "task": tr(
                                "Which criterion do you tend to ignore when evaluating answers?",
                                "Какой критерий вы чаще всего игнорируете при оценке ответов?",
                                "Җавап бәяләгәндә кайсы критерийны ешрак игътибарсыз калдырасыз?",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 60,
                                "min_words": 12,
                                "required_markers": [],
                                "bonus_markers": [],
                                "forbidden_phrases": [],
                                "weak_area_tags": ["evaluation-awareness"],
                            },
                        },
                    ],
                },
                {
                    "slug": "pe-final-studio",
                    "title": tr("Final Prompt Studio", "Финальная студия промптов", "Финал промпт студиясе"),
                    "summary": tr(
                        "Synthesize everything into one real-world prompt workflow.",
                        "Соберите полный цикл в одном реальном сценарии.",
                        "Бер реаль сценарийда тулы циклны берләштерегез.",
                    ),
                    "estimated_minutes": 36,
                    "reward_lmn": 30,
                    "is_final_assessment": True,
                    "unlock_after_lessons": ["pe-iteration-loop", "pe-evaluate-quality"],
                    "steps": [
                        {
                            "slug": "pe-final-brief",
                            "kind": "theory",
                            "title": tr("Capstone Brief", "Бриф капстоуна", "Капстоун брифы"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "Choose one real task and deliver a prompt workflow: draft -> evaluate -> refine.",
                                    "Выберите реальную задачу и сдайте workflow: черновик -> оценка -> доработка.",
                                    "Бер реаль эш сайлагыз һәм workflow тапшырыгыз: каралама -> бәяләү -> яхшырту.",
                                )
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "pe-final-guided",
                            "kind": "guided_practice",
                            "title": tr("Draft v1", "Черновик v1", "Каралама v1"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Submit Prompt v1 with all required markers plus [CHECK] quality metric.",
                                "Отправьте Prompt v1 со всеми маркерами и метрикой качества в [CHECK].",
                                "Prompt v1 җибәрегез: барлык маркер + [CHECK] эчендә сыйфат метрикасы.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "required_markers": [
                                    "[ROLE]",
                                    "[CONTEXT]",
                                    "[TASK]",
                                    "[CONSTRAINTS]",
                                    "[OUTPUT]",
                                    "[CHECK]",
                                ],
                                "min_words": 55,
                                "pass_score": 75,
                                "weak_area_tags": ["capstone-v1"],
                            },
                        },
                        {
                            "slug": "pe-final-quiz",
                            "kind": "quiz",
                            "title": tr("Synthesis Quiz", "Синтез-квиз", "Синтез квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr(
                                    "What proves learning transfer best?",
                                    "Что лучше всего доказывает перенос навыка?",
                                    "Күнекмә күчешен иң яхшы нәрсә дәлилли?",
                                ),
                                a=tr(
                                    "Only completing many tiny steps.",
                                    "Только прохождение множества мелких шагов.",
                                    "Бик күп вак адымны гына үтәү.",
                                ),
                                b=tr(
                                    "Applying the framework to a new task with measurable quality checks.",
                                    "Применение фреймворка в новой задаче с измеримой проверкой качества.",
                                    "Фреймворкны яңа эштә үлчәнә торган сыйфат тикшерү белән куллану.",
                                ),
                                c=tr(
                                    "Memorizing prompt formulas without use.",
                                    "Запоминание формул без применения.",
                                    "Кулланмыйча формуланы ятлау.",
                                ),
                                exp_a=tr(
                                    "Completion alone can create illusion of learning.",
                                    "Одного завершения шагов недостаточно — это иллюзия прогресса.",
                                    "Адым үтәү генә җитми — бу ялган прогресс булырга мөмкин.",
                                ),
                                exp_b=tr(
                                    "Correct: transfer + measurable quality = real competence.",
                                    "Верно: перенос + измеримость качества = реальная компетенция.",
                                    "Дөрес: күчеш + үлчәнә торган сыйфат = реаль компетенция.",
                                ),
                                exp_c=tr(
                                    "Memorization without application is fragile.",
                                    "Запоминание без применения быстро распадается.",
                                    "Кулланусыз ятлау тиз онытыла.",
                                ),
                            ),
                        },
                        {
                            "slug": "pe-final-applied",
                            "kind": "applied_exercise",
                            "title": tr("Refined v2", "Доработка v2", "Яхшыртылган v2"),
                            "estimated_minutes": 10,
                            "task": tr(
                                "Submit Prompt v2 and explicitly state what you changed and why.",
                                "Отправьте Prompt v2 и явно укажите, что изменили и почему.",
                                "Prompt v2 җибәрегез һәм ниләрне ни өчен үзгәрткәнегезне ачык языгыз.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 60,
                                "bonus_markers": ["changed", "because", "[CHECK]"],
                                "pass_score": 78,
                                "weak_area_tags": ["capstone-v2", "iteration-proof"],
                            },
                        },
                        {
                            "slug": "pe-final-checkpoint",
                            "kind": "final_checkpoint",
                            "title": tr("Course Final Checkpoint", "Финальная проверка курса", "Курсның финал тикшерүе"),
                            "estimated_minutes": 9,
                            "task": tr(
                                "Write a short synthesis: your repeatable prompt workflow in 5 lines + one risk to monitor.",
                                "Напишите синтез: ваш повторяемый prompt-workflow в 5 строках + один риск для контроля.",
                                "Кыска синтез языгыз: 5 юлда кабатлана торган prompt-workflow + бер контроль рискы.",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 75,
                                "min_words": 32,
                                "required_markers": ["workflow", "risk"],
                                "bonus_markers": ["metric", "iteration"],
                                "forbidden_phrases": ["everything is clear", "no risks"],
                                "weak_area_tags": ["course-synthesis"],
                            },
                        },
                    ],
                },
            ],
        },
    ],
}
