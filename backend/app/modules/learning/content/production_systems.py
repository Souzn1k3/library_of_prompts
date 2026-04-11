from __future__ import annotations

from app.modules.learning.content.common import strengthen_practice_steps, tr

_BASE_TEXT_VALIDATOR = {
    "type": "text",
    "pass_score": 74,
    "min_words": 48,
    "required_markers": ["[GOAL]", "[INPUTS]", "[STAGES]", "[OUTPUT]", "[EVAL]"],
    "bonus_markers": ["fallback", "threshold", "owner", "risk"],
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


def _reflection_submission(min_words: int = 16) -> dict:
    return {
        "type": "text",
        "pass_score": 60,
        "min_words": min_words,
        "required_markers": [],
        "bonus_markers": [],
        "forbidden_phrases": [],
    }


PRODUCTION_SYSTEMS_COURSE = {
    "slug": "production-prompt-systems",
    "title": tr(
        "Production Prompt Systems",
        "Продакшен-системы промптов",
        "Продакшен промпт системалары",
    ),
    "subtitle": tr(
        "Design, evaluate, and ship prompt systems that survive real operations",
        "Проектируйте, оценивайте и внедряйте prompt-системы для реальной работы",
        "Чын операцион эшкә чыдый торган prompt системаларын проектлагыз, бәяләгез һәм кертегез",
    ),
    "description": tr(
        "An advanced builder track: define interfaces, build evaluation rules, control context, and deliver one production-ready workflow.",
        "Продвинутый трек для сборки систем: задайте интерфейсы, постройте правила оценки, управляйте контекстом и сдайте один production-ready workflow.",
        "Система төзү өчен advanced трек: интерфейслар билгеләгез, бәяләү кагыйдәсе төзегез, контекст белән идарә итегез һәм бер production-ready workflow тапшырыгыз.",
    ),
    "difficulty": "advanced",
    "result_headline": tr(
        "Move from writing prompts to designing operating systems for AI work.",
        "Перейдите от написания промптов к проектированию operating system для AI-работы.",
        "Промпт язу дәрәҗәсеннән AI эше өчен operating system проектлау дәрәҗәсенә күчегез.",
    ),
    "deliverable_preview": tr(
        "A production workflow spec with evaluation, guardrails, and owner handoff.",
        "Production workflow spec с evaluation, guardrails и owner handoff.",
        "Evaluation, guardrails һәм owner handoff булган production workflow spec.",
    ),
    "estimated_minutes": 240,
    "is_free": True,
    "course_reward_lmn": 190,
    "lesson_default_reward_lmn": 24,
    "badge_code": "learning.production_prompt_systems",
    "certificate_template": "production-prompt-systems-v1",
    "what_you_will_learn": [
        tr(
            "Write system specs that define inputs, stages, outputs, and evaluation rules",
            "Писать system specs с входами, этапами, результатом и правилами оценки",
            "Керү, этап, нәтиҗә һәм бәяләү кагыйдәсе булган system spec язу",
        ),
        tr(
            "Design prompt workflows with context control, guardrails, and fallback logic",
            "Проектировать prompt-workflow с контролем контекста, guardrails и fallback-логикой",
            "Контекст контроле, guardrails һәм fallback логикасы булган prompt-workflow проектлау",
        ),
        tr(
            "Ship one workflow that another teammate can run and monitor",
            "Сдавать workflow, который сможет запустить и сопровождать другой участник команды",
            "Башка команда әгъзасы эшләтә һәм күзәтә ала торган workflow тапшыру",
        ),
    ],
    "prerequisites": [
        tr(
            "Complete the foundations and workflows tracks or bring equivalent practice.",
            "Пройдите foundations и workflows или уже владейте аналогичной практикой.",
            "Foundations һәм workflows трекларын тәмамлагыз яки шуңа тиң тәҗрибәгез булсын.",
        ),
        tr(
            "Bring one recurring work scenario that needs reliability, not just good wording.",
            "Возьмите один повторяющийся рабочий сценарий, где важна надежность, а не только хорошая формулировка.",
            "Яхшы формулировка гына түгел, ышанычлылык кирәк булган бер кабатлана торган эш сценарие алып килегез.",
        ),
    ],
    "deliverables": [
        tr(
            "A system specification with stage boundaries and interface contracts.",
            "System specification с границами этапов и interface contract.",
            "Этап чиге һәм interface contract булган system specification.",
        ),
        tr(
            "An evaluation harness with pass rules, fail labels, and regression checks.",
            "Evaluation harness с pass rules, fail labels и regression checks.",
            "Pass rules, fail labels һәм regression checks булган evaluation harness.",
        ),
        tr(
            "A final workflow package with context rules, fallback logic, and owner notes.",
            "Итоговый workflow package с правилами контекста, fallback-логикой и заметками для owner.",
            "Контекст кагыйдәсе, fallback логикасы һәм owner язмалары булган финал workflow package.",
        ),
    ],
    "career_outcomes": [
        tr(
            "Turn AI usage into a repeatable operating process instead of a one-off prompt.",
            "Превращать работу с AI в повторяемый процесс, а не в разовый промпт.",
            "AI белән эшне бер тапкырлык промпт түгел, ә кабатлана торган процесска әйләндерү.",
        ),
        tr(
            "Review prompt systems with quality rules, ownership, and failure recovery.",
            "Ревьюить prompt-системы через quality rules, ownership и recovery после сбоя.",
            "Prompt системаларын quality rules, ownership һәм сбойдан соң recovery аша ревьюлау.",
        ),
        tr(
            "Connect prompting to shipping decisions, monitoring, and team handoff.",
            "Связывать prompting с внедрением, мониторингом и передачей в команду.",
            "Promptingны кертү, мониторинг һәм командага тапшыру белән бәйләү.",
        ),
    ],
    "product_action": {
        "label": tr(
            "Open the submit workspace",
            "Открыть форму публикации",
            "Публикация формасын ачу",
        ),
        "href": "/submit",
        "body": tr(
            "Package your final workflow as a prompt asset you can review, refine, and publish inside the product.",
            "Упакуйте финальный workflow как prompt asset, который можно проверить, доработать и отправить внутри продукта.",
            "Финал workflowны продукт эчендә тикшереп, яхшыртып һәм җибәреп була торган prompt asset итеп җыегыз.",
        ),
    },
    "modules": [
        {
            "slug": "production-design",
            "title": tr("Production Design", "Продакшен-дизайн", "Продакшен дизайн"),
            "summary": tr(
                "Define system boundaries, interfaces, and evaluation rules before generation.",
                "Определяйте границы системы, интерфейсы и правила оценки до генерации.",
                "Генерациягә кадәр система чиген, интерфейсларны һәм бәяләү кагыйдәләрен билгеләгез.",
            ),
            "lessons": [
                {
                    "slug": "adv-spec-and-interfaces",
                    "title": tr("System Specs and Interfaces", "System specs и интерфейсы", "System specs һәм интерфейслар"),
                    "summary": tr(
                        "Write the system before you write the prompt text.",
                        "Сначала опишите систему, а потом сам промпт.",
                        "Башта системаны языгыз, аннары гына промпт текстын.",
                    ),
                    "objective": tr(
                        "Design a prompt system specification with explicit inputs, stages, outputs, and evaluation.",
                        "Спроектировать system spec с явными входами, этапами, результатом и оценкой.",
                        "Ачык керү, этап, нәтиҗә һәм бәяләүле system spec проектлау.",
                    ),
                    "deliverable": tr(
                        "A production spec with interface markers and success rules.",
                        "Production spec с interface markers и правилами успеха.",
                        "Interface markers һәм уңыш кагыйдәсе булган production spec.",
                    ),
                    "scenario_title": tr("Case: weekly research memo", "Кейс: еженедельная исследовательская записка", "Кейс: атналык тикшеренү язмасы"),
                    "scenario_body": tr(
                        "An analyst prepares a research memo every week, but results change wildly depending on wording. The system needs stable interfaces before better prose.",
                        "Аналитик каждую неделю готовит research memo, но результат слишком зависит от формулировки. Системе нужны стабильные интерфейсы еще до красивого текста.",
                        "Аналитик һәр атна research memo әзерли, ләкин нәтиҗә сүзләргә артык бәйле. Системага матур текстка кадәр үк тотрыклы интерфейслар кирәк.",
                    ),
                    "debrief": [
                        tr("A prompt system starts with contracts, not copywriting.", "Prompt system copywriting белән түгел, contractтан башлана.", "Prompt system copywriting белән түгел, contractтан башлана."),
                        tr("Inputs and outputs define what the system can be trusted to do.", "Входы и выходы задают границы доверия к системе.", "Керү һәм чыгу системага кайда ышанып була икәнен билгели."),
                        tr("Evaluation belongs in the spec, not only in later QA.", "Оценка должна быть в spec, а не только в финальном QA.", "Бәяләү spec эчендә булырга тиеш, финал QAда гына түгел."),
                    ],
                    "review_rubric": [
                        tr("Inputs are explicit.", "Входы заданы явно.", "Керүләр ачык."),
                        tr("Stages have boundaries.", "Этапы разделены границами.", "Этапларның чиге бар."),
                        tr("Outputs are testable.", "Результат можно проверить.", "Нәтиҗәне тикшереп була."),
                        tr("Success rules are visible.", "Правила успеха видны.", "Уңыш кагыйдәләре күренә."),
                    ],
                    "common_mistakes": [
                        tr("Starting from wording instead of interfaces.", "Начинать с формулировки вместо интерфейсов.", "Интерфейс урынына формулировкадан башлау."),
                        tr("Leaving stages implicit.", "Оставлять этапы подразумеваемыми.", "Этапларны ачык язмый калдыру."),
                        tr("Describing a system with no evaluation rule.", "Описывать систему без правила оценки.", "Системаны бәяләү кагыйдәсенсез тасвирлау."),
                    ],
                    "estimated_minutes": 34,
                    "reward_lmn": 22,
                    "is_final_assessment": False,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "adv-spec-theory",
                            "kind": "theory",
                            "title": tr("Theory", "Теория", "Теория"),
                            "estimated_minutes": 6,
                            "content": [
                                tr("Production prompting starts with system design, not prompt phrasing. The prompt text is only one layer of a larger operating spec.", "Продакшен-промптинг начинается с дизайна системы, а не с формулировки промпта. Сам текст промпта - это только один слой более широкой операционной спецификации.", "Продакшен-промптинг промпт тексты белән түгел, ә система дизайны белән башлана. Промпт үзе зуррак операцион спецификациянең бер катламы гына."),
                                tr("A good spec defines inputs, stages, outputs, and success rules before the model sees anything. That is what makes the system reviewable.", "Хорошая спецификация задает входы, этапы, выходы и правила успеха еще до того, как модель что-то увидит. Именно это делает систему пригодной для ревью, а не личным ремеслом автора.", "Яхшы спецификация модель нәрсә дә булса күргәнче үк керүләрне, этапларны, чыгышларны һәм уңыш кагыйдәләрен билгели. Нәкъ шул системага ревью ясарга мөмкинлек бирә."),
                                tr("Interfaces matter because they separate responsibility. Each stage should know what it receives, what it returns, and what it must not guess.", "Интерфейсы важны потому, что разделяют ответственность. Каждый этап должен понимать, что он получает, что обязан вернуть и что ему запрещено додумывать самому.", "Интерфейслар мөһим, чөнки алар җаваплылыкны аера. Һәр этап нәрсә алуын, нәрсә кайтарырга тиешлеген һәм нәрсәне фаразларга ярамаганын белергә тиеш."),
                                tr("If interfaces stay fuzzy, hidden complexity leaks into the prompt text. The system grows longer, more fragile, and harder to maintain.", "Если интерфейсы остаются размытыми, скрытая сложность протекает прямо в текст промпта. Система становится длиннее, хрупче и дороже в сопровождении.", "Интерфейслар томан булып калса, яшерен катлаулылык турыдан-туры промпт эченә ага. Система озыная, какшый һәм алып бару ягыннан кыйммәтләнә."),
                                tr("A production-ready spec is testable by another teammate. If pass/fail still lives only in the author's head, the system is not ready.", "Production-ready спецификация должна проверяться другим участником команды. Если pass/fail по-прежнему живет только в голове автора, система еще не готова.", "Production-ready спецификацияне башка команда әгъзасы тикшерә алырга тиеш. Әгәр pass/fail әле дә бары тик автор башында гына яшәсә, система әзер түгел."),
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "adv-spec-guided",
                            "kind": "guided_practice",
                            "title": tr("Guided Practice", "Практика с опорой", "Юнәлешле практика"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Convert 'Need a weekly research memo' into a system spec with [GOAL], [INPUTS], [STAGES], [OUTPUT], [EVAL], and one [RISK] trigger.",
                                "Преобразуйте «нужна еженедельная research memo» в system spec с [GOAL], [INPUTS], [STAGES], [OUTPUT], [EVAL] и одним [RISK]-триггером.",
                                "«Атналык research memo кирәк» соравын system specка әйләндерегез: [GOAL], [INPUTS], [STAGES], [OUTPUT], [EVAL] һәм бер [RISK] триггеры булсын.",
                            ),
                            "placeholder": tr(
                                "[GOAL] Deliver a weekly research memo for product leads.\n[INPUTS] Notes, source links, open questions, deadline.\n[STAGES] 1. Gather facts. 2. Compare claims. 3. Draft memo. 4. Score memo.\n[OUTPUT] Memo with summary, evidence table, open risks.\n[EVAL] Pass only if every claim has evidence and one explicit confidence level.",
                                "[GOAL] Подготовить еженедельную research memo для product leads.\n[INPUTS] Заметки, ссылки на источники, открытые вопросы, дедлайн.\n[STAGES] 1. Собрать факты. 2. Сравнить claims. 3. Составить memo. 4. Оценить memo.\n[OUTPUT] Memo с summary, таблицей evidence и открытыми рисками.\n[EVAL] Проход только если у каждого claim есть evidence и явный confidence level.",
                                "[GOAL] Product leads өчен атналык research memo әзерләү.\n[INPUTS] Язмалар, чыганак сылтамалары, ачык сораулар, дедлайн.\n[STAGES] 1. Факт җыю. 2. Claims чагыштыру. 3. Memo язу. 4. Memo бәяләү.\n[OUTPUT] Summary, evidence таблицасы һәм ачык рисклары булган memo.\n[EVAL] Һәр claim өчен evidence һәм ачык confidence level булса гына үтә.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "weak_area_tags": ["system-specs", "interfaces"],
                            },
                        },
                        {
                            "slug": "adv-spec-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr("What makes a prompt system reviewable?", "Что делает prompt-систему пригодной для ревью?", "Prompt-системаны ревью өчен яраклы иткән нәрсә нәрсә?"),
                                a=tr("A long prompt with many style instructions", "Длинный промпт со множеством стилистических указаний", "Күп стилистик күрсәтмәле озын промпт"),
                                b=tr("Explicit inputs, stages, outputs, and success rules", "Явные входы, этапы, выходы и правила успеха", "Ачык керү, этап, нәтиҗә һәм уңыш кагыйдәсе"),
                                c=tr("A model-specific magic phrase", "Модель-специфичная магическая фраза", "Модельгә бәйле тылсымлы фраза"),
                                exp_a=tr("Length does not create a review surface.", "Длина сама по себе не создает поверхность для ревью.", "Озынлык үзе генә ревью өслеге ясамый."),
                                exp_b=tr("Correct: the system is inspectable when the operating parts are explicit.", "Верно: систему можно разобрать, когда ее рабочие части заданы явно.", "Дөрес: система эш өлешләре ачык булганда тикшерелә ала."),
                                exp_c=tr("Magic phrases are fragile and hard to audit.", "Магические фразы хрупки и плохо поддаются аудиту.", "Тылсымлы фразалар какшак һәм аудитка авыр."),
                            ),
                        },
                        {
                            "slug": "adv-spec-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 10,
                            "task": tr(
                                "Write a system spec for one recurring task from your work/study. Keep markers concrete and include owner handoff notes per stage.",
                                "Напишите system spec для одной повторяющейся задачи из работы/учебы. Сохраните маркеры конкретными и добавьте owner-handoff заметки по этапам.",
                                "Эш/укудагы бер кабатлана торган бурыч өчен system spec языгыз. Маркерларны төгәл саклагыз һәм һәр этапка owner-handoff язмалары өстәгез.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 58,
                                "pass_score": 76,
                                "bonus_markers": ["owner", "threshold", "risk"],
                                "weak_area_tags": ["system-transfer"],
                            },
                        },
                        {
                            "slug": "adv-spec-reflection",
                            "kind": "reflection",
                            "title": tr("Reflection", "Рефлексия", "Рефлексия"),
                            "estimated_minutes": 4,
                            "task": tr(
                                "Which part of your current AI workflow is still implicit and should become a written interface?",
                                "Какая часть вашего текущего AI-workflow все еще остается неявной и должна стать явным интерфейсом?",
                                "Хәзерге AI-workflowгызның кайсы өлеше әле дә ачык язылмаган һәм интерфейска әйләнергә тиеш?",
                            ),
                            "submission": _reflection_submission(),
                        },
                    ],
                },
                {
                    "slug": "adv-evaluation-harness",
                    "title": tr("Evaluation Harness", "Evaluation harness", "Evaluation harness"),
                    "summary": tr(
                        "Define pass rules before you trust the output.",
                        "Определяйте pass rules до того, как доверять результату.",
                        "Нәтиҗәгә ышанганчы pass rules билгеләгез.",
                    ),
                    "objective": tr(
                        "Build an evaluation harness with sample cases, fail labels, and a pass rule.",
                        "Построить evaluation harness с sample cases, fail labels и pass rule.",
                        "Sample cases, fail labels һәм pass rule булган evaluation harness төзү.",
                    ),
                    "deliverable": tr(
                        "A small evaluation spec that can detect regressions before rollout.",
                        "Небольшая evaluation-spec, которая ловит regressions до rollout.",
                        "Rolloutка кадәр regressionsны тотучы кыска evaluation spec.",
                    ),
                    "scenario_title": tr("Case: onboarding assistant", "Кейс: onboarding-ассистент", "Кейс: onboarding ассистенты"),
                    "scenario_body": tr(
                        "A team uses AI to answer onboarding questions, but quality drifts after each tweak. You need a harness that shows whether the change improved or broke the system.",
                        "Команда использует AI для ответов на onboarding-вопросы, но качество плавает после каждой правки. Нужен harness, который показывает, улучшила ли правка систему или сломала ее.",
                        "Команда onboarding сорауларына җавап өчен AI куллана, ләкин һәр үзгәрештән соң сыйфат тайпыла. Үзгәреш системаны яхшырттымы яки ваттыммы - шуны күрсәтә торган harness кирәк.",
                    ),
                    "debrief": [
                        tr("Evaluation turns opinion into evidence.", "Evaluation превращает мнение в evidence.", "Evaluation фикерне evidenceка әйләндерә."),
                        tr("Sample cases need failure labels, not just scores.", "Sample cases өчен бәя генә түгел, failure labels та кирәк.", "Sample cases өчен бәя генә түгел, failure labels та кирәк."),
                        tr("A pass rule prevents silent quality drift.", "Pass rule защищает от тихого дрейфа качества.", "Pass rule тыныч кына сыйфат тайпылуын туктата."),
                    ],
                    "review_rubric": [
                        tr("Sample cases are concrete.", "Sample cases конкретны.", "Sample cases конкрет."),
                        tr("Fail labels are explicit.", "Fail labels заданы явно.", "Fail labels ачык."),
                        tr("Pass rule is measurable.", "Pass rule измерим.", "Pass rule үлчәнә."),
                        tr("Report format makes comparison easy.", "Формат отчета удобен для сравнения.", "Хисап форматы чагыштыруны җиңеләйтә."),
                    ],
                    "common_mistakes": [
                        tr("Scoring without example cases.", "Ставить оценки без sample cases.", "Sample casesсыз бәя кую."),
                        tr("Using vague labels like 'bad'.", "Использовать размытые labels вроде 'плохо'.", "«Начар» кебек томан labels куллану."),
                        tr("Reviewing one output with no baseline.", "Проверять один output без baseline.", "Baselineсыз бер output кына тикшерү."),
                    ],
                    "estimated_minutes": 34,
                    "reward_lmn": 24,
                    "is_final_assessment": False,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "adv-eval-theory",
                            "kind": "theory",
                            "title": tr("Theory", "Теория", "Теория"),
                            "estimated_minutes": 6,
                            "content": [
                                tr("An evaluation harness is the memory of quality. It keeps the team from confusing a lucky answer with a reliable system.", "Evaluation harness - это память качества. Он не дает команде перепутать случайно удачный ответ с по-настоящему надежной системой.", "Evaluation harness - сыйфат хәтере. Ул командага очраклы уңышлы җавапны чыннан да ышанычлы система белән бутарга ирек бирми."),
                                tr("Without defined pass/fail, almost every tweak looks like improvement. That is how regressions survive in production.", "Без заранее определенного pass/fail почти любая правка выглядит улучшением. Именно так регрессии и выживают в продакшене.", "Алдан билгеләнгән pass/fail булмаса, һәр төзәтмә диярлек яхшырту кебек күренә. Регрессияләр продакшенда нәкъ шулай яши дә."),
                                tr("Even a small harness needs sample cases, failure labels, thresholds, and a comparable report format.", "Даже небольшой harness должен содержать sample cases, failure labels, thresholds и формат отчета, по которому версии реально можно сравнивать.", "Кечкенә harness та sample cases, failure labels, thresholds һәм версияләрне чынлап чагыштырырлык хисап форматын эченә алырга тиеш."),
                                tr("Failure labels must point to repair decisions, not vague disappointment. 'Inaccurate', 'off-policy', or 'missing evidence' already tells the team what to fix.", "Failure labels должны вести к решению по исправлению, а не к размытому раздражению. Метки вроде inaccurate, off-policy или missing evidence уже подсказывают, куда именно смотреть команде.", "Failure labels томан күңелсезлеккә түгел, ә төзәтү карарына алып барырга тиеш. Inaccurate, off-policy яки missing evidence кебек ярлыклар команданың кая карарга тиешлеген әйтеп тора."),
                                tr("Production quality is trend, not one run. What matters is stability across cases and across iterations.", "Продакшен-качество - это тренд, а не один запуск. Имеет значение устойчивость на серии кейсов и на последовательности итераций.", "Продакшен-сыйфат - ул бер запуск түгел, ә тренд. Төрле кейсларда һәм кабатланган итерацияләрдә тотрыклылык мөһим."),
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "adv-eval-guided",
                            "kind": "guided_practice",
                            "title": tr("Guided Practice", "Практика с опорой", "Юнәлешле практика"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Draft an evaluation harness using [TASK], [SAMPLE_CASES], [FAIL_LABELS], [PASS_RULE], [REPORT] and add one regression guard.",
                                "Соберите evaluation harness с [TASK], [SAMPLE_CASES], [FAIL_LABELS], [PASS_RULE], [REPORT] и добавьте один regression guard.",
                                "[TASK], [SAMPLE_CASES], [FAIL_LABELS], [PASS_RULE], [REPORT] белән evaluation harness төзегез һәм бер regression guard өстәгез.",
                            ),
                            "placeholder": tr(
                                "[TASK] Answer onboarding questions for new team members.\n[SAMPLE_CASES] 3 questions covering policy, tooling, and escalation.\n[FAIL_LABELS] inaccurate | incomplete | unsafe | off-policy.\n[PASS_RULE] Pass only if 3/3 answers avoid unsafe and off-policy labels.\n[REPORT] Return per case: score | fail label | fix recommendation.",
                                "[TASK] Отвечать на onboarding-вопросы новых сотрудников.\n[SAMPLE_CASES] 3 вопроса по policy, tooling и escalation.\n[FAIL_LABELS] inaccurate | incomplete | unsafe | off-policy.\n[PASS_RULE] Проход только если 3/3 ответа без unsafe и off-policy.\n[REPORT] По каждому кейсу: score | fail label | fix recommendation.",
                                "[TASK] Яңа команда әгъзаларының onboarding сорауларына җавап бирү.\n[SAMPLE_CASES] Policy, tooling һәм escalation буенча 3 сорау.\n[FAIL_LABELS] inaccurate | incomplete | unsafe | off-policy.\n[PASS_RULE] 3/3 җавапта unsafe һәм off-policy булмаса гына үтә.\n[REPORT] Һәр кейс өчен: score | fail label | fix recommendation.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "required_markers": ["[TASK]", "[SAMPLE_CASES]", "[FAIL_LABELS]", "[PASS_RULE]", "[REPORT]"],
                                "weak_area_tags": ["evaluation-harness"],
                            },
                        },
                        {
                            "slug": "adv-eval-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr("What makes an evaluation harness useful?", "Что делает evaluation harness полезным?", "Evaluation harness ны файдалы иткән нәрсә нәрсә?"),
                                a=tr("Only a total score", "Только общий score", "Бары тик гомуми score"),
                                b=tr("Cases, failure labels, and a pass threshold", "Кейсы, failure labels и pass threshold", "Кейслар, failure labels һәм pass threshold"),
                                c=tr("A larger prompt", "Более длинный промпт", "Озынрак промпт"),
                                exp_a=tr("A score alone hides the cause of failure.", "Один score скрывает причину провала.", "Бер score хата сәбәбен яшерә."),
                                exp_b=tr("Correct: this creates evidence you can compare over time.", "Верно: так появляется evidence, которое можно сравнивать со временем.", "Дөрес: шулай вакыт буенча чагыштырып була торган evidence барлыкка килә."),
                                exp_c=tr("Prompt length is not evaluation.", "Длина промпта не заменяет evaluation.", "Промпт озынлыгы evaluationны алыштырмый."),
                            ),
                        },
                        {
                            "slug": "adv-eval-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 10,
                            "task": tr(
                                "Create an evaluation harness for a workflow you use (or plan to ship) with baseline vs candidate comparison and release threshold.",
                                "Создайте evaluation harness для workflow, который используете (или планируете внедрить), с сравнением baseline vs candidate и release-threshold.",
                                "Куллана торган (яки кертмәкче булган) workflow өчен evaluation harness төзегез: baseline vs candidate чагыштыруы һәм release-threshold булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "required_markers": ["[TASK]", "[SAMPLE_CASES]", "[FAIL_LABELS]", "[PASS_RULE]", "[REPORT]"],
                                "min_words": 60,
                                "pass_score": 78,
                                "bonus_markers": ["regression", "threshold", "baseline"],
                                "weak_area_tags": ["evaluation-transfer"],
                            },
                        },
                        {
                            "slug": "adv-eval-reflection",
                            "kind": "reflection",
                            "title": tr("Reflection", "Рефлексия", "Рефлексия"),
                            "estimated_minutes": 4,
                            "task": tr(
                                "Where does your current AI workflow rely on opinion instead of evidence?",
                                "Где ваш текущий AI-workflow пока опирается на мнение, а не на evidence?",
                                "Хәзерге AI-workflowгыз кайсы урында әле дә evidence түгел, ә фикергә таяна?",
                            ),
                            "submission": _reflection_submission(),
                        },
                    ],
                },
            ],
        },
        {
            "slug": "operational-reliability",
            "title": tr("Operational Reliability", "Операционная надежность", "Операцион ышанычлылык"),
            "summary": tr(
                "Control context, protect against failure, and package a workflow for real use.",
                "Управляйте контекстом, защищайтесь от сбоев и упаковывайте workflow для реального использования.",
                "Контекст белән идарә итегез, сбойдан сакланыгыз һәм workflowны реаль куллануга җыегыз.",
            ),
            "lessons": [
                {
                    "slug": "adv-context-and-guardrails",
                    "title": tr("Context, Chaining, and Guardrails", "Контекст, chaining и guardrails", "Контекст, chaining һәм guardrails"),
                    "summary": tr(
                        "Control what the system sees, what it ignores, and what it does when quality drops.",
                        "Контролируйте, что система видит, что игнорирует и что делает при падении качества.",
                        "Система нәрсә күрә, нәрсәне санга сукмый һәм сыйфат төшкәндә нәрсә эшли - шуны контрольдә тотыгыз.",
                    ),
                    "objective": tr(
                        "Design context rules, stage handoffs, and fallback logic for a real workflow.",
                        "Спроектировать правила контекста, handoff между этапами и fallback-логику для реального workflow.",
                        "Реаль workflow өчен контекст кагыйдәсе, этап handoffы һәм fallback логикасы проектлау.",
                    ),
                    "deliverable": tr(
                        "A workflow plan with required context, ignored noise, escalation rules, and fallback.",
                        "Workflow-plan с нужным контекстом, игнорируемым шумом, escalation rules и fallback.",
                        "Кирәк контекст, читкә кагыла торган шау, escalation rules һәм fallback булган workflow-plan.",
                    ),
                    "scenario_title": tr("Case: support + documentation workflow", "Кейс: workflow поддержки и документации", "Кейс: support һәм документация workflow"),
                    "scenario_body": tr(
                        "A team uses AI to answer support requests and update docs. The system fails when too much context is dumped in or when no safe fallback exists.",
                        "Команда использует AI для ответов в поддержку и обновления документации. Система ломается, когда в нее сваливают слишком много контекста или не задают безопасный fallback.",
                        "Команда support җаваплары һәм документация яңарту өчен AI куллана. Контекст артык күп өелгәндә яки куркынычсыз fallback булмаганда система ватыла.",
                    ),
                    "debrief": [
                        tr("More context is not automatically better context.", "Больше контекста - не значит лучше контекст.", "Күбрәк контекст - яхшырак контекст дигән сүз түгел."),
                        tr("Every stage needs a clean handoff contract.", "Каждому этапу нужен чистый handoff contract.", "Һәр этапка чиста handoff contract кирәк."),
                        tr("Fallback logic is part of reliability, not a patch for later.", "Fallback-логика - часть надежности, а не заплатка на потом.", "Fallback логикасы ышанычлылыкның өлеше, соңыннан ямау түгел."),
                    ],
                    "review_rubric": [
                        tr("Required context is specific.", "Нужный контекст указан конкретно.", "Кирәк контекст конкрет."),
                        tr("Noise to ignore is named.", "Шум для игнорирования назван.", "Игътибар итмәскә тиешле шау атала."),
                        tr("Fallback path is explicit.", "Fallback path задан явно.", "Fallback path ачык."),
                        tr("Escalation trigger is clear.", "Триггер эскалации понятен.", "Эскалация триггеры ачык."),
                    ],
                    "common_mistakes": [
                        tr("Dumping all available context into one step.", "Сваливать весь контекст в один шаг.", "Бөтен контекстны бер адымга өю."),
                        tr("Using stage chains with no handoff rule.", "Строить stage chain без handoff rule.", "Handoff ruleсыз stage chain төзү."),
                        tr("Assuming the model will recover on its own.", "Надеяться, что модель сама восстановится.", "Модель үзе төзәтер дип өметләнү."),
                    ],
                    "estimated_minutes": 36,
                    "reward_lmn": 24,
                    "is_final_assessment": False,
                    "unlock_after_lessons": ["adv-spec-and-interfaces", "adv-evaluation-harness"],
                    "steps": [
                        {
                            "slug": "adv-context-theory",
                            "kind": "theory",
                            "title": tr("Theory", "Теория", "Теория"),
                            "estimated_minutes": 6,
                            "content": [
                                tr("Context control is not 'more data'; it is selective exposure. The system should see what is necessary, ignore what is noise, and escalate when crucial context is missing.", "Контроль контекста - это не «побольше данных», а селективная подача. Система должна видеть то, что действительно нужно, игнорировать шум и эскалировать ситуацию, если критически важного контекста не хватает.", "Контекст контроле - «күбрәк мәгълүмат» түгел, ә сайлап күрсәтү. Система чынлап кирәклесен күрергә, шауны читкә куярга һәм мөһим контекст җитмәгәндә эскалацияләргә тиеш."),
                                tr("More context often worsens reasoning when it mixes signal with contradiction or stale detail.", "Күбрәк контекст һәрвакыт яхшырту түгел. Әгәр файдалы сигнал искергән детальләр, каршылыклар һәм артык өстәмәләр белән буталса, фикерләү начарлана.", "Күбрәк контекст еш кына фикерне начарайта, әгәр ул файдалы сигналны каршылыклар, искергән детальләр һәм артык өстәмәләр белән бутаса."),
                                tr("Guardrails are operating rules: trigger, default action, and owner of escalation. They are not polite wishes.", "Guardrails - это операционные правила: trigger, действие по умолчанию и владелец эскалации. Это не вежливое пожелание «будь осторожнее», а рабочий механизм.", "Guardrails - операцион кагыйдәләр: trigger, килешенгән гамәл һәм эскалация хуҗасы. Болар әдәпле теләкләр түгел, ә эшли торган механизм."),
                                tr("Handoff contracts between stages protect the chain from hidden assumptions. Each step should know what kind of context may travel forward.", "Handoff-контракты между этапами защищают цепочку от скрытых допущений. Каждый шаг должен заранее понимать, какой именно контекст имеет право проходить дальше.", "Этаплар арасындагы handoff-контрактлар чылбырны яшерен фаразлардан саклый. Һәр адым алга таба нинди контекст күчәргә мөмкин икәнен алдан белергә тиеш."),
                                tr("Mature systems fail safely. When confidence drops or required context is absent, they stop guessing and surface the uncertainty.", "Зрелые системы падают безопасно. Когда confidence падает или обязательный контекст отсутствует, они прекращают угадывать и поднимают наружу саму неопределенность.", "Өлгергән системалар куркынычсыз рәвештә ялгыша. Confidence төшә икән яки мәҗбүри контекст юк икән, алар фаразлаудан туктый һәм билгесезлекне ачык күрсәтә."),
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "adv-context-guided",
                            "kind": "guided_practice",
                            "title": tr("Guided Practice", "Практика с опорой", "Юнәлешле практика"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Write a context-control plan with [TASK], [REQUIRED_CONTEXT], [OPTIONAL_CONTEXT], [IGNORE], [FALLBACK], [OUTPUT], and one [ESCALATE] condition.",
                                "Соберите план управления контекстом с [TASK], [REQUIRED_CONTEXT], [OPTIONAL_CONTEXT], [IGNORE], [FALLBACK], [OUTPUT] и одним условием [ESCALATE].",
                                "Контекст идарәсе планын языгыз: [TASK], [REQUIRED_CONTEXT], [OPTIONAL_CONTEXT], [IGNORE], [FALLBACK], [OUTPUT] һәм бер [ESCALATE] шарты булсын.",
                            ),
                            "placeholder": tr(
                                "[TASK] Answer a support question and suggest a doc update.\n[REQUIRED_CONTEXT] Policy excerpt, product version, user issue.\n[OPTIONAL_CONTEXT] Recent similar cases.\n[IGNORE] Marketing copy, unrelated backlog notes.\n[FALLBACK] If policy is missing or contradictory, escalate instead of guessing.\n[OUTPUT] Return answer + doc update note + escalation flag if needed.",
                                "[TASK] Ответить на вопрос в поддержку и предложить обновление документации.\n[REQUIRED_CONTEXT] Фрагмент policy, версия продукта, проблема пользователя.\n[OPTIONAL_CONTEXT] Похожие кейсы за последнее время.\n[IGNORE] Маркетинговый текст, несвязанные backlog notes.\n[FALLBACK] Если policy нет или она противоречива, эскалировать вместо догадок.\n[OUTPUT] Ответ + заметка для docs + escalation flag при необходимости.",
                                "[TASK] Support соравына җавап бирү һәм документация яңартуын тәкъдим итү.\n[REQUIRED_CONTEXT] Policy өзеге, продукт версиясе, кулланучы проблемасы.\n[OPTIONAL_CONTEXT] Соңгы охшаш кейслар.\n[IGNORE] Маркетинг тексты, бәйсез backlog notes.\n[FALLBACK] Policy юк яки каршылыклы булса, фаразламыйча эскалацияләгез.\n[OUTPUT] Җавап + docs өчен язма + кирәк булса escalation flag.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "required_markers": ["[TASK]", "[REQUIRED_CONTEXT]", "[OPTIONAL_CONTEXT]", "[IGNORE]", "[FALLBACK]", "[OUTPUT]"],
                                "weak_area_tags": ["context-control", "guardrails"],
                            },
                        },
                        {
                            "slug": "adv-context-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr("What is the cleanest use of fallback logic?", "Что является самым чистым применением fallback-логики?", "Fallback логикасын иң чиста куллану нәрсә?"),
                                a=tr("Ask the model to try harder", "Попросить модель стараться лучше", "Модельдән күбрәк тырышуын сорау"),
                                b=tr("Define when to stop guessing and escalate", "Задать момент, когда нужно прекратить догадки и эскалировать", "Кайчан фаразны туктатып эскалацияләргә кирәклеген билгеләү"),
                                c=tr("Paste more context into the prompt", "Вставить в промпт еще больше контекста", "Промптка тагын да күбрәк контекст өстәү"),
                                exp_a=tr("Effort is not a safeguard.", "Стараться сильнее - не safeguard.", "Күбрәк тырышу safeguard түгел."),
                                exp_b=tr("Correct: fallback defines safe behavior under uncertainty.", "Верно: fallback задает безопасное поведение при неопределенности.", "Дөрес: fallback билгесезлек вакытында куркынычсыз тәртипне билгели."),
                                exp_c=tr("More context can increase noise.", "Больше контекста может увеличить шум.", "Күбрәк контекст шауны арттырырга мөмкин."),
                            ),
                        },
                        {
                            "slug": "adv-context-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 10,
                            "task": tr(
                                "Create a context and guardrail plan for a workflow you rely on in real operations, including one safe-fail path and one monitoring metric.",
                                "Соберите план контекста и guardrails для workflow, на который вы опираетесь в реальной работе, включая один safe-fail путь и одну метрику мониторинга.",
                                "Реаль эштә таянган workflow өчен контекст һәм guardrails планы төзегез: бер safe-fail юлы һәм бер мониторинг метрикасы булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "required_markers": ["[TASK]", "[REQUIRED_CONTEXT]", "[OPTIONAL_CONTEXT]", "[IGNORE]", "[FALLBACK]", "[OUTPUT]"],
                                "min_words": 62,
                                "pass_score": 78,
                                "bonus_markers": ["escalate", "risk", "threshold"],
                                "weak_area_tags": ["guardrail-transfer"],
                            },
                        },
                        {
                            "slug": "adv-context-reflection",
                            "kind": "reflection",
                            "title": tr("Reflection", "Рефлексия", "Рефлексия"),
                            "estimated_minutes": 4,
                            "task": tr(
                                "Where does your current workflow still trust the model too early?",
                                "Где ваш текущий workflow все еще слишком рано доверяет модели?",
                                "Хәзерге workflowгыз кайсы урында әле дә модельгә артык иртә ышана?",
                            ),
                            "submission": _reflection_submission(),
                        },
                    ],
                },
                {
                    "slug": "adv-production-capstone",
                    "title": tr("Production Capstone", "Продакшен-капстоун", "Продакшен капстоун"),
                    "summary": tr(
                        "Ship one production-ready workflow with specs, evaluation, and reliability notes.",
                        "Соберите один production-ready workflow со спецификацией, evaluation и notes по надежности.",
                        "Бер production-ready workflowны спецификация, evaluation һәм ышанычлылык язмалары белән тапшырыгыз.",
                    ),
                    "objective": tr(
                        "Package a real workflow another teammate could run, review, and monitor.",
                        "Упаковать реальный workflow так, чтобы другой участник команды мог его запустить, проверить и сопровождать.",
                        "Реаль workflowны башка команда әгъзасы эшләтә, тикшерә һәм күзәтә алырлык итеп җыю.",
                    ),
                    "deliverable": tr(
                        "A final workflow package with spec, eval harness, context rules, and owner note.",
                        "Финальный workflow package со spec, eval harness, правилами контекста и owner note.",
                        "Spec, eval harness, контекст кагыйдәсе һәм owner note булган финал workflow package.",
                    ),
                    "scenario_title": tr("Case: your highest-value recurring AI task", "Кейс: ваша самая ценная повторяющаяся AI-задача", "Кейс: сезнең иң кыйммәтле кабатлана торган AI биремегез"),
                    "scenario_body": tr(
                        "Choose one real recurring task from work or study. Your job is to package it so the workflow can be reviewed, reused, and improved over time.",
                        "Выберите одну реальную повторяющуюся задачу из работы или учебы. Нужно упаковать ее так, чтобы workflow можно было ревьюить, переиспользовать и улучшать со временем.",
                        "Эштән яки укудан бер реаль кабатлана торган бирем сайлагыз. Бурыч - workflowны ревьюлап, кабат кулланып һәм вакыт белән яхшыртып була торган итеп җыю.",
                    ),
                    "debrief": [
                        tr("Production-ready means clear ownership and monitoring, not only a strong prompt.", "Production-ready - это ownership и мониторинг, а не только сильный промпт.", "Production-ready димәк ownership һәм мониторинг, көчле промпт кына түгел."),
                        tr("The workflow package must survive handoff.", "Workflow package должен пережить handoff.", "Workflow package handoff ны узарга тиеш."),
                        tr("A final metric keeps the system anchored to business value.", "Финальная метрика привязывает систему к реальной ценности.", "Финал метрика системаны реаль кыйммәткә бәйли."),
                    ],
                    "review_rubric": [
                        tr("Spec is clear.", "Spec понятен.", "Spec ачык."),
                        tr("Evaluation is measurable.", "Evaluation измерима.", "Evaluation үлчәнә."),
                        tr("Fallback and escalation exist.", "Есть fallback и escalation.", "Fallback һәм escalation бар."),
                        tr("Owner and success metric are explicit.", "Owner и success metric заданы явно.", "Owner һәм success metric ачык."),
                    ],
                    "common_mistakes": [
                        tr("Submitting a nice prompt instead of a system package.", "Сдавать красивый промпт вместо system package.", "System package урынына матур промпт кына тапшыру."),
                        tr("Leaving monitoring out of scope.", "Оставлять мониторинг вне контура.", "Мониторингны контурдан читтә калдыру."),
                        tr("Designing for personal memory instead of team reuse.", "Проектировать под личную память, а не под reuse в команде.", "Команда reuseы урынына шәхси хәтергә генә таянып проектлау."),
                    ],
                    "estimated_minutes": 44,
                    "reward_lmn": 34,
                    "is_final_assessment": True,
                    "unlock_after_lessons": ["adv-evaluation-harness", "adv-context-and-guardrails"],
                    "steps": [
                        {
                            "slug": "adv-capstone-brief",
                            "kind": "theory",
                            "title": tr("Capstone Brief", "Бриф капстоуна", "Капстоун брифы"),
                            "estimated_minutes": 6,
                            "content": [
                                tr("The capstone is about production intent. You are packaging a workflow another person can run, review, and maintain, even when you are not in the room to explain it.", "Капстоун здесь про production-intent. Вы упаковываете workflow так, чтобы другой человек мог его запустить, проверить и сопровождать, даже если вас нет рядом, чтобы все объяснить голосом.", "Капстоун монда production-intent турында. Сез workflowны башка кеше эшләтеп, ревьюлап һәм алып бара алырлык итеп җыясыз, хәтта сез янәшәдә булып барысын да аңлатмасаңыз да."),
                                tr("A good package reads like an operating note: purpose, interfaces, checks, fallback, cadence, owner, and success metric. After one reading, the next person should understand how the system works and where its limits are.", "Хороший пакет читается как операционная памятка: цель, интерфейсы, проверки, fallback, ритм запуска, владелец процесса и метрика успеха. После одного прочтения следующий человек уже должен понимать, как система работает и где проходят ее границы.", "Яхшы пакет operating note кебек укыла: максат, интерфейслар, тикшерүләр, fallback, эшләү ритмы, җаваплы кеше һәм уңыш метрикасы. Бер тапкыр укыгач ук, киләсе кеше системаның ничек эшләвен һәм аның чиген аңларга тиеш."),
                                tr("Do not optimize for elegant wording. Optimize for reliable behavior under normal conditions and under failure, because production value appears when the workflow stays stable under pressure.", "Оптимизировать нужно не изящную формулировку, а надежное поведение в нормальном режиме и в режиме сбоя, потому что production-ценность появляется там, где процесс остается устойчивым под нагрузкой.", "Максат нәфис формулировка түгел, ә гадәти шартларда да, сбой вакытында да ышанычлы тотыш булырга тиеш, чөнки production кыйммәте процесс басым астында да тотрыклы калганда туа."),
                                tr("A complete submission makes quality observable. It shows what signal means 'working', what signal means 'degrading', and what the first response should be. That is what turns a strong prompt into an asset the team can trust.", "Полная работа делает качество наблюдаемым. В ней видно, какой сигнал означает «работает», какой сигнал означает «деградирует» и какой должна быть первая реакция. Именно это превращает сильный промпт в актив, которому команда может доверять.", "Тулы эш сыйфатны күзәтелә торган итә. Анда кайсы сигнал «эшли» дигәнне, кайсысы «начарая» дигәнне һәм беренче реакция нинди булырга тиешлеген күрергә була. Нәкъ менә шул көчле промптны команда ышана алырлык активка әйләндерә."),
                                tr("The final sign of maturity is simple: another teammate can pick up the workflow, run it carefully, notice when it is drifting, and improve it without starting from zero.", "Финальная проверка зрелости очень простая: другой участник команды может взять workflow, аккуратно провести его, заметить деградацию и улучшить систему, не начиная все с нуля.", "Өлгергәнлекнең соңгы билгесе бик гади: башка команда әгъзасы workflowны алып, аны игътибар белән эшләтеп, деградацияне күреп һәм барысын нульдән башламыйча яхшырта ала."),
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "adv-capstone-v1",
                            "kind": "guided_practice",
                            "title": tr("Workflow Package v1", "Workflow package v1", "Workflow package v1"),
                            "estimated_minutes": 9,
                            "task": tr(
                                "Submit v1 using [GOAL], [INPUTS], [STAGES], [GUARDRAILS], [OUTPUT], [EVAL], [OWNER] plus one [CADENCE] note for monitoring frequency.",
                                "Отправьте v1 с [GOAL], [INPUTS], [STAGES], [GUARDRAILS], [OUTPUT], [EVAL], [OWNER] и одной пометкой [CADENCE] о частоте мониторинга.",
                                "v1 җибәрегез: [GOAL], [INPUTS], [STAGES], [GUARDRAILS], [OUTPUT], [EVAL], [OWNER] һәм мониторинг ешлыгы өчен бер [CADENCE] язмасы булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "required_markers": ["[GOAL]", "[INPUTS]", "[STAGES]", "[GUARDRAILS]", "[OUTPUT]", "[EVAL]", "[OWNER]"],
                                "min_words": 70,
                                "pass_score": 80,
                                "bonus_markers": ["fallback", "metric", "threshold"],
                                "weak_area_tags": ["capstone-v1"],
                            },
                        },
                        {
                            "slug": "adv-capstone-quiz",
                            "kind": "quiz",
                            "title": tr("Synthesis Quiz", "Синтез-квиз", "Синтез квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr("What makes the final workflow production-ready?", "Что делает финальный workflow production-ready?", "Финал workflowны production-ready иткән нәрсә нәрсә?"),
                                a=tr("It looks sophisticated", "Он выглядит сложно и умно", "Ул катлаулы һәм акыллы күренә"),
                                b=tr("It has explicit operation rules, checks, and ownership", "В нем явно заданы operation rules, checks и ownership", "Анда operation rules, checks һәм ownership ачык бирелгән"),
                                c=tr("It uses the latest model name", "В нем упомянута новая модель", "Анда иң яңа модель исеме телгә алына"),
                                exp_a=tr("Appearance is not operational quality.", "Внешний вид не равен операционному качеству.", "Тышкы күренеш операцион сыйфат түгел."),
                                exp_b=tr("Correct: clarity of operation is what makes systems reusable.", "Верно: именно операционная ясность делает систему переиспользуемой.", "Дөрес: нәкъ менә операцион ачыклык системаны кабат кулланыла торган итә."),
                                exp_c=tr("Model choice matters, but it is not the system design.", "Выбор модели важен, но не заменяет дизайн системы.", "Модель сайлау мөһим, ләкин система дизайнын алыштырмый."),
                            ),
                        },
                        {
                            "slug": "adv-capstone-v2",
                            "kind": "applied_exercise",
                            "title": tr("Workflow Package v2", "Workflow package v2", "Workflow package v2"),
                            "estimated_minutes": 12,
                            "task": tr(
                                "Submit v2 with one measurable improvement, one fallback change from v1 review, and one explicit rollback trigger.",
                                "Отправьте v2 с одним измеримым улучшением, одной правкой fallback по результатам ревью v1 и одним явным триггером отката.",
                                "v2 җибәрегез: бер үлчәнә торган яхшырту, v1 ревьюсыннан бер fallback төзәтүе һәм бер ачык rollback триггеры булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "required_markers": ["[GOAL]", "[INPUTS]", "[STAGES]", "[GUARDRAILS]", "[OUTPUT]", "[EVAL]", "[OWNER]"],
                                "min_words": 82,
                                "pass_score": 82,
                                "bonus_markers": ["changed", "because", "fallback", "metric"],
                                "weak_area_tags": ["capstone-v2"],
                            },
                        },
                        {
                            "slug": "adv-capstone-final",
                            "kind": "final_checkpoint",
                            "title": tr("Deployment Note", "Заметка по внедрению", "Кертү язмасы"),
                            "estimated_minutes": 7,
                            "task": tr(
                                "Write the rollout note: where this workflow will run, how success is tracked, and what risk is monitored first.",
                                "Напишите rollout note: где будет работать этот workflow, как отслеживается успех и какой риск мониторится первым.",
                                "Rollout note языгыз: workflow кайда эшли, уңыш ничек күзәтелә һәм кайсы риск беренче булып мониторинглана.",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 78,
                                "min_words": 36,
                                "required_markers": ["workflow", "success", "risk"],
                                "bonus_markers": ["owner", "metric", "fallback"],
                                "forbidden_phrases": ["no risks", "works for everything"],
                                "weak_area_tags": ["production-synthesis"],
                            },
                        },
                    ],
                },
            ],
        },
    ],
}

strengthen_practice_steps(
    PRODUCTION_SYSTEMS_COURSE,
    guided_suffix=tr(
        "Think like a system designer. Each marker should reduce ambiguity, separate responsibility, and help another teammate review or run the system without reading your mind.",
        "Думайте как системный дизайнер. Каждый маркер должен уменьшать двусмысленность, разделять ответственность и помогать другому участнику команды ревьюить или запускать систему без чтения ваших мыслей.",
        "Система дизайнеры кебек уйлагыз. Һәр маркер билгесезлекне киметергә, җаваплылыкны аерырга һәм башка команда әгъзасына системаны сезнең уйны укымыйча ревьюларга яки эшләтергә ярдәм итәргә тиеш.",
    ),
    applied_suffix=tr(
        "Make it ship-ready. The spec or harness should survive handoff, monitoring, and failure handling so it feels like an operating asset rather than a clever prompt.",
        "Сделайте это годным к внедрению. Спецификация или harness должны выдерживать handoff, мониторинг и работу со сбоями, чтобы это ощущалось как рабочий актив, а не как просто остроумный промпт.",
        "Моны кертүгә әзер итегез. Спецификация яки harness handoffны, мониторингны һәм сбойлар белән эшне күтәрә алсын, нәтиҗә тапкыр промпт түгел, ә эшли торган актив кебек тоелсын.",
    ),
    reflection_suffix=tr(
        "Be specific about operational risk: identify one hidden assumption, explain how it could fail in the real world, and state the interface or rule that should replace it.",
        "Говорите об операционном риске конкретно: найдите одно скрытое допущение, объясните, как оно может сломаться в реальности, и назовите интерфейс или правило, которое должно его заменить.",
        "Операцион риск турында төгәл языгыз: бер яшерен фаразны табыгыз, аның чын тормышта ничек ватылырга мөмкинлеген аңлатыгыз һәм аны алыштырасы интерфейсны яки кагыйдәне атагыз.",
    ),
    reflection_template=tr(
        "A hidden assumption in my workflow is [...]. It could fail when [...]. I should replace it with [...].",
        "Скрытое допущение в моем workflow - [...]. Оно может сломаться, когда [...]. Его нужно заменить на [...].",
        "Минем workflowдагы яшерен фараз - [...]. Ул [...] булганда ватылырга мөмкин. Аны [...] белән алыштырырга кирәк.",
    ),
)
