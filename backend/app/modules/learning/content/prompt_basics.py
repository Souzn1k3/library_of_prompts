from __future__ import annotations

from app.modules.learning.content.common import tr

_BASE_TEXT_VALIDATOR = {
    "type": "text",
    "pass_score": 70,
    "min_words": 35,
    "required_markers": ["[ROLE]", "[CONTEXT]", "[TASK]", "[CONSTRAINTS]", "[OUTPUT]"],
    "bonus_markers": ["[CHECK]", "[EXAMPLE]"],
    "forbidden_phrases": [
        "any format",
        "as you wish",
        "whatever works",
        "just make it good",
        "в любом формате",
        "как хотите",
        "как угодно",
        "сделай нормально",
        "теләсә нинди форматта",
        "үзеңчә",
        "ничек булса да ярый",
        "нормаль итеп эшлә",
    ],
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
                                    "Prompt engineering starts from a contract: goal, audience, constraints, and definition of done.",
                                    "Промпт-инжиниринг начинается с контракта: цель, аудитория, ограничения и определение «готово».",
                                    "Промпт-инжиниринг контракттан башлана: максат, аудитория, чикләүләр һәм «әзер» билгеләмәсе.",
                                ),
                                tr(
                                    "A stable prompt usually has five layers: role, context, task, constraints, and output format.",
                                    "Стабильный промпт обычно состоит из пяти слоев: роль, контекст, задача, ограничения и формат результата.",
                                    "Тотрыклы промпт гадәттә биш катламнан тора: роль, контекст, бурыч, чикләүләр һәм нәтиҗә форматы.",
                                ),
                                tr(
                                    "Small wording changes can strongly shift output quality when one of these layers is missing.",
                                    "Даже небольшая смена формулировки резко меняет качество, если один из этих слоев отсутствует.",
                                    "Бу катламнарның берсе юк икән, кечкенә генә формулировка үзгәреше дә сыйфатны нык үзгәртә.",
                                ),
                                tr(
                                    "Most beginner failures are predictable: vague verbs, no target level, and no concrete output shape.",
                                    "Большинство ошибок новичка предсказуемы: размытые глаголы, нет уровня аудитории и нет формы результата.",
                                    "Башлангыч хаталар еш бер үк: томан фигыльләр, аудитория дәрәҗәсе юк, нәтиҗә формасы юк.",
                                ),
                                tr(
                                    "Quick self-check: if a classmate can run your prompt and get a similar structure, your prompt is likely well-specified.",
                                    "Быстрая самопроверка: если одноклассник может запустить ваш промпт и получить похожую структуру, значит спецификация сильная.",
                                    "Тиз үз-үзеңне тикшерү: сыйныфташыгыз сезнең промптны эшләтеп охшаш структура алса, спецификация яхшы.",
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
                                    "Rewrite this request into a structured prompt: 'Help me study better.' Use a real school context and measurable result.",
                                    "Перепишите запрос в структурированный промпт: «Помоги мне лучше учиться». Используйте реальный школьный контекст и измеримый результат.",
                                    "«Укуда яхшырак булыш» соравын структур промптка әйләндерегез: чын мәктәп контексты һәм үлчәнә торган нәтиҗә булсын.",
                                )
                            ],
                            "task": tr(
                                "Include [ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT], [CHECK]. In [CHECK] set two measurable signals: completion rate and review quality.",
                                "Используйте [ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT], [CHECK]. В [CHECK] задайте два измеримых сигнала: процент выполнения и качество повторения.",
                                "[ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT], [CHECK] кулланыгыз. [CHECK] эчендә ике үлчәнә торган сигнал куегыз: үтәү проценты һәм кабатлау сыйфаты.",
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
                                "Write a real prompt with [ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT], [CHECK]. The task must be executable today and include one failure-risk in [CHECK].",
                                "Напишите реальный промпт с [ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT], [CHECK]. Задачу нужно выполнить сегодня и указать один риск провала в [CHECK].",
                                "[ROLE], [CONTEXT], [TASK], [CONSTRAINTS], [OUTPUT], [CHECK] белән реаль промпт языгыз. Бирем бүген үк үтәлә торган булсын һәм [CHECK] эчендә бер хата рискы булсын.",
                            ),
                            "placeholder": tr(
                                "[ROLE] ...\n[CONTEXT] ...\n[TASK] ...\n[CONSTRAINTS] ...\n[OUTPUT] ...",
                                "[ROLE] ...\n[CONTEXT] ...\n[TASK] ...\n[CONSTRAINTS] ...\n[OUTPUT] ...",
                                "[ROLE] ...\n[CONTEXT] ...\n[TASK] ...\n[CONSTRAINTS] ...\n[OUTPUT] ...",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "required_markers": ["[ROLE]", "[CONTEXT]", "[TASK]", "[CONSTRAINTS]", "[OUTPUT]", "[CHECK]"],
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
                                "Reflection is needed to lock in improvement before the next lesson: name one skipped block, one consequence, and one concrete fix in your next prompt.",
                                "Рефлексия нужна, чтобы закрепить улучшение перед следующим уроком: назовите один пропускаемый блок, одно последствие и одну конкретную правку в следующем промпте.",
                                "Рефлексия киләсе дәрес алдыннан үсешне ныгыту өчен кирәк: еш калдырылган бер блокны, бер нәтиҗәсен һәм киләсе промпттагы бер төгәл төзәтмәне языгыз.",
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
                                    "Role-Context-Task-Output is not decoration; it is a control system for model behavior.",
                                    "Role-Context-Task-Output - это не украшение, а система управления поведением модели.",
                                    "Role-Context-Task-Output бизәк түгел, ә модель тәртибен идарә итү системасы.",
                                ),
                                tr(
                                    "Role defines viewpoint, context defines boundaries, task defines action, output defines how quality can be inspected.",
                                    "Role задает позицию, context задает границы, task задает действие, output задает форму проверяемого результата.",
                                    "Role карашны, context чикләрне, task эшне, output тикшерелә торган нәтиҗә формасын билгели.",
                                ),
                                tr(
                                    "If you skip context, the model invents assumptions. If you skip output shape, you cannot compare answers.",
                                    "Если пропустить context, модель додумает предположения. Если пропустить output-форму, ответы нельзя сравнивать.",
                                    "Context юк икән, модель үзе фаразлый. Output формасы юк икән, җавапларны чагыштырып булмый.",
                                ),
                                tr(
                                    "For beginners, this pattern reduces anxiety: you always know which block to improve instead of rewriting everything.",
                                    "Для начинающих этот паттерн снижает тревогу: вы всегда понимаете, какой блок улучшать, не переписывая всё.",
                                    "Башлангыч дәрәҗә өчен бу паттерн борчылуны киметә: барысын яңадан язмыйча, кайсы блокны яхшыртырга икәнен күрәсез.",
                                ),
                                tr(
                                    "A useful habit: keep each block short and concrete, then test one block change at a time.",
                                    "Полезная привычка: делайте каждый блок коротким и конкретным, затем тестируйте изменения по одному блоку.",
                                    "Файдалы гадәт: һәр блокны кыска һәм төгәл языгыз, аннары үзгәрешне бер блок буенча гына тикшерегез.",
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
                                "Create a prompt for a one-week study sprint. Include [CHECK] with day-by-day completion criteria and one escalation rule if the student falls behind.",
                                "Соберите промпт для недельного учебного спринта. Добавьте [CHECK] с критериями по дням и одно правило эскалации, если ученик отстает.",
                                "Бер атналык уку спринты өчен промпт төзегез. [CHECK] эчендә көнлек критерийлар һәм укучы артта калса бер эскалация кагыйдәсе булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "required_markers": ["[ROLE]", "[CONTEXT]", "[TASK]", "[CONSTRAINTS]", "[OUTPUT]", "[CHECK]"],
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
                                    "Какой блок отсутствует: '[ROLE] Карьерный коуч [TASK] Построй дорожную карту [OUTPUT] таблица'?",
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
                                "Write a reusable template with placeholders like <topic>, <audience>, <time_limit>, <difficulty>. Add one quality gate in [CHECK] so the template does not produce generic output.",
                                "Напишите переиспользуемый шаблон с плейсхолдерами <тема>, <аудитория>, <лимит_времени>, <сложность>. Добавьте один quality gate в [CHECK], чтобы шаблон не выдавал шаблонную «воду».",
                                "<тема>, <аудитория>, <вакыт_лимиты>, <катлаулылык> кебек плейсхолдерлы шаблон языгыз. [CHECK] эченә бер quality gate өстәгез, шаблон гомуми «су» бирмәсен.",
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
                                    "Constraints are quality rails: they narrow bad outputs while preserving useful reasoning.",
                                    "Ограничения - это рельсы качества: они сужают плохие ответы, но сохраняют полезное рассуждение.",
                                    "Чикләүләр - сыйфат рельслары: алар начар җавапны кыса, әмма файдалы фикерне саклый.",
                                ),
                                tr(
                                    "Use hard constraints for non-negotiables (format, safety) and soft constraints for style and depth.",
                                    "Жесткие ограничения задавайте для обязательного (формат, безопасность), мягкие - для стиля и глубины.",
                                    "Каты чикләүне мәҗбүри өлешкә бирегез (формат, куркынычсызлык), йомшак чикләүне стиль һәм тирәнлеккә кулланыгыз.",
                                ),
                                tr(
                                    "Examples work when they show target structure, not when they are copied blindly.",
                                    "Примеры работают, когда показывают целевую структуру, а не когда их бездумно копируют.",
                                    "Мисаллар максат структураны күрсәтсә генә файдалы, уйламыйча күчереп алганда түгел.",
                                ),
                                tr(
                                    "Common failure: too many rigid rules create brittle prompts that fail on slightly new tasks.",
                                    "Типичный сбой: слишком много жестких правил делает промпт хрупким и неустойчивым к новым задачам.",
                                    "Еш очрый торган хата: артык күп каты кагыйдә промптны какшата һәм яңа бурычта ватылуга китерә.",
                                ),
                                tr(
                                    "Your goal is controllable flexibility: enough structure to verify quality, enough freedom to solve the task.",
                                    "Ваша цель - управляемая гибкость: структуры достаточно для проверки качества, свободы достаточно для решения задачи.",
                                    "Максат - идарә ителә торган сыгылмалылык: сыйфатны тикшерергә җитәрлек структура һәм бурычны чишәргә җитәрлек ирек.",
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
                                "Write a prompt for 'summarize an article' with exactly 4 constraints: 2 hard + 2 soft, plus one [EXAMPLE] and one [CHECK] rule.",
                                "Напишите промпт для «суммаризируй статью» с ровно 4 ограничениями: 2 жестких + 2 мягких, плюс один [EXAMPLE] и одно правило [CHECK].",
                                "«Мәкаләне кыскача яз» өчен нәкъ 4 чикләү куегыз: 2 каты + 2 йомшак, өстәп бер [EXAMPLE] һәм бер [CHECK] кагыйдәсе.",
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
                                    "[CHECK]",
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
                                "You lead a small team. Draft a weekly status prompt that forces evidence-based updates, explicit risks, and next actions with deadlines.",
                                "Вы ведете небольшую команду. Соберите weekly status промпт, который требует обновления на основе фактов, явные риски и следующие действия с дедлайнами.",
                                "Сез кечкенә команда алып барасыз. Фактка нигезләнгән яңарту, ачык рисклар һәм дедлайнлы киләсе адымнар таләп иткән weekly status промпт төзегез.",
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
                                    "Professional prompting is iterative engineering: baseline output, diagnose failure, patch one block, retest.",
                                    "Профессиональный промптинг - это итерационная инженерия: базовый выход, диагноз сбоя, правка одного блока, повторный тест.",
                                    "Профессиональ промптинг итерацион инженерия ул: базовый нәтиҗә, хата диагнозы, бер блокны төзәтү, кабат тест.",
                                ),
                                tr(
                                    "Changing one block at a time gives causal clarity: you can see what actually improved quality.",
                                    "Изменение одного блока за раз дает причинную ясность: видно, что реально улучшило качество.",
                                    "Бер блокны гына үзгәртү сәбәпне ача: кайсы үзгәрешнең чынлап яхшыртканын күрәсез.",
                                ),
                                tr(
                                    "Keep a micro-log: version, change, observed effect, next hypothesis.",
                                    "Ведите микро-лог: версия, правка, наблюдаемый эффект, следующая гипотеза.",
                                    "Микро-лог алып барыгыз: версия, төзәтмә, күзәтелгән эффект, киләсе гипотеза.",
                                ),
                                tr(
                                    "Most teams stall because they rewrite everything and lose learning signal.",
                                    "Многие команды застревают, потому что переписывают всё и теряют сигнал обучения.",
                                    "Күп командалар тыгыла, чөнки барысын яңадан яза һәм өйрәнү сигналын югалта.",
                                ),
                                tr(
                                    "Iteration becomes a skill when each loop ends with a specific decision: keep, modify, or rollback.",
                                    "Итерация становится навыком, когда каждый цикл заканчивается конкретным решением: оставить, изменить или откатить.",
                                    "Һәр цикл ачык карар белән тәмамланса, итерация чын күнекмәгә әйләнә: калдырыргамы, үзгәртергәме, кире кайтарыргамы.",
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
                                "Start from your previous prompt and produce Version A + Version B with one targeted change. Add a short diff note: what changed, why, and what metric should improve.",
                                "Возьмите прошлый промпт и сделайте Версию A и Версию B с одной целевой правкой. Добавьте короткий diff-комментарий: что изменили, зачем и какая метрика должна вырасти.",
                                "Алдагы промпттан Version A һәм Version B ясагыз, бер максатчан үзгәреш белән. Кыска diff-язма өстәгез: нәрсә үзгәрде, ни өчен һәм кайсы метрика үсәргә тиеш.",
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
                                "Write a mini debug prompt that labels failure mode, identifies root cause, and proposes one focused revision. Require a before/after expectation.",
                                "Сделайте мини debug-промпт, где модель маркирует тип сбоя, находит корень проблемы и предлагает одну точечную правку. Потребуйте ожидание «до/после».",
                                "Мини debug-промпт языгыз: хата төрен тамгалагыз, төп сәбәбен табыгыз һәм бер төгәл төзәтмә тәкъдим итегез. «До/после» көтелгән нәтиҗәсен мәҗбүри итегез.",
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
                                    "A quality rubric turns 'looks good' into measurable judgment.",
                                    "Рубрика качества превращает «выглядит нормально» в измеримую оценку.",
                                    "Сыйфат рубрикасы «ярый кебек» бәясен үлчәнә торган бәяләүгә әйләндерә.",
                                ),
                                tr(
                                    "Use four baseline criteria: relevance, completeness, factual safety, and actionability.",
                                    "Используйте четыре базовых критерия: релевантность, полнота, фактическая корректность и применимость.",
                                    "Дүрт төп критерий кулланыгыз: релевантлык, тулылык, факт дөреслеге һәм куллану мөмкинлеге.",
                                ),
                                tr(
                                    "Score each criterion separately before writing a final score; this prevents halo bias.",
                                    "Оценивайте каждый критерий отдельно до итогового балла; это снижает эффект ореола.",
                                    "Финал балл куйганчы һәр критерийны аерым бәяләгез; бу ореол хатасын киметә.",
                                ),
                                tr(
                                    "A rubric is useful only if it triggers action: revise prompt, add context, or tighten output format.",
                                    "Рубрика полезна только если запускает действие: правка промпта, добавление контекста или ужесточение формата.",
                                    "Рубрика гамәл тудырса гына файдалы: промпт төзәтү, контекст өстәү яки форматны катыландыру.",
                                ),
                                tr(
                                    "For school-level learners, this creates confidence: quality is checked by rules, not by guessing.",
                                    "Для школьника это снижает хаос: качество проверяется по правилам, а не по догадкам.",
                                    "Укучы өчен бу ышаныч бирә: сыйфат фараз белән түгел, кагыйдә белән тикшерелә.",
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
                                "Write a prompt that forces the model to self-score on 4 criteria at the end and justify each score with one sentence and one evidence quote.",
                                "Соберите промпт, который заставит модель оценить себя по 4 критериям и обосновать каждый балл одной фразой и одной ссылкой на фрагмент ответа.",
                                "Модельне ахырда 4 критерий буенча үз-үзен бәяләргә мәҗбүр итүче промпт языгыз: һәр баллга бер җөмлә нигез һәм җаваптан бер дәлил китерелсен.",
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
                                "Create a prompt for resume feedback with scorecard output: criterion scores, top 3 fixes, and a rewrite plan for the weakest section.",
                                "Сделайте промпт для обратной связи по резюме с форматом scorecard: баллы по критериям, топ-3 правки и план переписывания самого слабого блока.",
                                "Резюме өчен scorecard форматлы фикер промпты төзегез: критерий баллары, топ-3 төзәтмә һәм иң көчсез бүлекне яңадан язу планы.",
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
                                    "Capstone proves transfer: you must apply the framework to a new real task, not repeat lesson examples.",
                                    "Капстоун проверяет перенос навыка: нужно применить фреймворк к новой реальной задаче, а не повторить пример из урока.",
                                    "Капстоун күнекмә күчешен тикшерә: фреймворкны дәрестәге мисалга түгел, яңа реаль бурычка кулланырга кирәк.",
                                ),
                                tr(
                                    "Your workflow must show the full loop: brief, prompt v1, quality check, revision logic, and prompt v2.",
                                    "Ваш workflow должен показать полный цикл: бриф, промпт v1, проверка качества, логика правки и промпт v2.",
                                    "Workflow тулы циклны күрсәтергә тиеш: бриф, промпт v1, сыйфат тикшерүе, төзәтү логикасы һәм промпт v2.",
                                ),
                                tr(
                                    "Use measurable checks so another person can review your result without guessing your intent.",
                                    "Используйте измеримые проверки, чтобы другой человек мог ревьюить работу без угадывания ваших намерений.",
                                    "Үлчәнә торган тикшерүләр кулланыгыз, башка кеше сезнең ниятне чамаламыйча ревью ясый алсын.",
                                ),
                                tr(
                                    "A strong final submission explains not only what changed, but why that change should improve output.",
                                    "Сильная финальная работа объясняет не только что изменилось, но и почему это улучшает результат.",
                                    "Көчле финал эштә нәрсә үзгәргән генә түгел, ә бу үзгәрешнең ни өчен сыйфатны арттыруы да аңлатыла.",
                                )
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "pe-final-guided",
                            "kind": "guided_practice",
                            "title": tr("Draft v1", "Черновик версии 1", "1 нче версия караламасы"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Submit Prompt v1 with all required markers plus [CHECK] quality metrics and one explicit risk you still expect.",
                                "Отправьте Промпт v1 со всеми маркерами, метриками качества в [CHECK] и одним явным риском, который пока остается.",
                                "Промпт v1 җибәрегез: барлык маркерлар, [CHECK] эчендә сыйфат метрикалары һәм әле дә калган бер ачык риск булсын.",
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
                            "title": tr("Refined v2", "Доработка версии 2", "2 нче версияне яхшырту"),
                            "estimated_minutes": 10,
                            "task": tr(
                                "Submit Prompt v2 and explicitly state what changed, why it should improve quality, and which metric moved from v1.",
                                "Отправьте Промпт v2 и явно укажите: что изменили, почему это улучшает качество и какая метрика изменилась относительно v1.",
                                "Промпт v2 җибәрегез һәм ачык языгыз: нәрсә үзгәрде, ни өчен сыйфат яхшырырга тиеш, һәм v1 белән чагыштырганда кайсы метрика үзгәрде.",
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
