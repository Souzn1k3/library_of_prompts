from __future__ import annotations

from app.modules.learning.content.common import strengthen_practice_steps, tr

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
                            "title": tr("Theory", "Теория", "Теория"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "A good prompt starts before the first sentence. First define the task, who will use the result, what constraints matter, and what 'done' should look like. If those things are blurry, the model has to guess.",
                                    "Хороший промпт начинается не с красивой формулировки, а с понятной договоренности с моделью. До того как писать запрос, нужно ответить на четыре вопроса: какую задачу мы решаем, для кого делаем результат, какие есть ограничения и по какому признаку поймем, что ответ уже можно использовать.",
                                    "Яхшы промпт беренче җөмләдән дә алда башлана. Башта бурычны, нәтиҗәне кем кулланачагын, нинди чикләүләр мөһим икәнен һәм «әзер» дигәннең нәрсә икәнен билгеләргә кирәк. Болар томан булса, модель үзе фаразлый башлый.",
                                ),
                                tr(
                                    "A reliable beginner structure is simple: role, context, task, constraints, and output format. Each block removes a different kind of ambiguity, so the model spends less effort guessing and more effort solving.",
                                    "Сильный промпт лучше работает, когда инструкция ясная, конкретная и не заставляет модель догадываться о контексте. Запрос «помоги подготовиться к экзамену» слишком широкий, а запрос «составь план подготовки к экзамену по биологии на 5 дней для ученика 10 класса, по 40 минут в день, в виде таблицы» уже задает рабочие рамки.",
                                    "Ышанычлы башлангыч структура бик гади: роль, контекст, бурыч, чикләүләр һәм нәтиҗә форматы. Һәр блок билгесезлекнең үз өлешен ябып куя, шуңа модель фаразлауга түгел, ә чишүгә күбрәк көч сарыф итә.",
                                ),
                                tr(
                                    "For example, 'help me study biology' is too open. 'Create a 5-day biology study plan for a grade-10 student, 40 minutes a day, in table form' already tells the model who the plan is for, how long it should take, and what shape the answer must have.",
                                    "Самый надежный каркас для новичка выглядит так: роль, контекст, задача, ограничения и формат ответа. Роль помогает выбрать точку зрения, контекст объясняет ситуацию, задача говорит, что именно делать, ограничения не дают расползтись, а формат ответа заранее показывает, как будет выглядеть полезный результат.",
                                    "Мәсәлән, «биологияне яхшырак укырга булыш» дигән сорау артык киң. Ә «10 нчы сыйныф укучысы өчен 5 көнлек биология әзерлек планы төзе, көненә 40 минут, таблица формасында» дигән сорау инде кем өчен эшләнүен, күпме вакытка исәпләнүен һәм нәтиҗәнең нинди булырга тиешлеген күрсәтә.",
                                ),
                                tr(
                                    "Most weak answers come from missing detail, not from a 'bad model'. If you skip audience level, number of items, time limit, or format, the answer may sound confident and still be unusable.",
                                    "Большинство слабых ответов появляются не потому, что модель «плохая», а потому что в запросе оставили пустоты. Если не указан уровень аудитории, модель выберет его сама; если не сказано, сколько пунктов нужно, она решит это на свое усмотрение; если не описан формат, вы получите текст, который трудно проверить и сравнить.",
                                    "Күпчелек зәгыйфь җаваплар «начар модель» аркасында түгел, ә җитмәгән конкретика аркасында барлыкка килә. Әгәр аудитория дәрәҗәсе, пунктлар саны, вакыт лимиты яки формат күрсәтелмәсә, җавап ышанычлы яңгырый ала, ләкин кулланырга яраксыз булырга мөмкин.",
                                ),
                                tr(
                                    "A fast self-check is this: could another student run your prompt and get a similarly structured result? If yes, the prompt is probably specified well enough. If no, the task still lives too much in your head.",
                                    "Быстрая проверка очень простая: представьте, что ваш промпт запускает другой человек, который не сидел у вас в голове. Если по вашему запросу он сможет получить примерно такую же структуру ответа и поймет, что считать хорошим результатом, значит основа уже сильная. Если нет, промпт еще не объясняет задачу достаточно ясно.",
                                    "Тиз үз-үзеңне тикшерү ысулы болай: башка укучы сезнең промптны эшләтеп, якынча шул ук структурадагы нәтиҗә ала алыр идеме? Әгәр ала алса, промпт җитәрлек дәрәҗәдә төгәл язылган. Әгәр юк икән, бурыч әле дә артык күп дәрәҗәдә сезнең башыгызда гына яши.",
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
                                    "Role-Context-Task-Output is not decoration. It is a practical control system that lets you improve a prompt block by block instead of rewriting the whole request every time something goes wrong.",
                                    "Паттерн Role-Context-Task-Output нужен не для красоты и не для модного вида промпта. Это способ разложить запрос на понятные блоки, чтобы вы управляли качеством по частям, а не переписывали весь текст каждый раз, когда ответ не понравился.",
                                    "Role-Context-Task-Output бизәк өчен түгел. Ул промптны блоклап идарә итү ысулы: нәрсәдер эшләмәсә, бөтен сорауны яңадан язмыйча, нәкъ кайсы өлешне төзәтергә кирәклеген күрсәтә.",
                                ),
                                tr(
                                    "Each block has one job. Role sets viewpoint, Context explains the situation, Task tells the model what action to take, and Output defines the form of the result so quality is easy to inspect.",
                                    "У каждого блока своя работа. Role отвечает на вопрос «кто говорит и с какой позиции», Context объясняет, что важно знать про ситуацию, Task задает действие, а Output заранее фиксирует форму результата, чтобы ответ можно было быстро проверить и использовать.",
                                    "Һәр блокның үз вазифасы бар. Role караш ноктасын билгели, Context хәлнең мөһим өлешләрен аңлата, Task нинди гамәл кирәклеген әйтә, ә Output нәтиҗәнең формасын алдан ук күрсәтә, шуңа сыйфатны тиз тикшереп була.",
                                ),
                                tr(
                                    "If one block is missing, the model compensates by guessing. No Context usually creates invented assumptions, no Task creates wandering answers, and no Output creates text that sounds smart but is hard to compare or use.",
                                    "Если убрать хотя бы один блок, начинаются типичные проблемы. Без Context модель додумывает детали, без Task начинает рассуждать слишком широко, без Output вы получаете вроде бы умный текст, но не тот формат, который нужен в учебе или работе.",
                                    "Бер блок төшеп калса, модель буш урынны үзе тутыра башлый. Context булмаса, ул детальләрне үзе уйлап чыгара; Task зәгыйфь булса, җавап таралып китә; Output булмаса, текст акыллы кебек яңгырый, ләкин аны куллану яки чагыштыру авыр була.",
                                ),
                                tr(
                                    "In practice, a short structured prompt often beats a longer messy one. A clear role, a compact context block, one concrete task, and a visible output format usually produce a more reliable answer than a vague paragraph.",
                                    "На практике это выглядит так. Вместо запроса «сделай еженедельный апдейт» лучше написать: «Ты project coordinator. Ниже сырые заметки команды за неделю. Сверни их в апдейт для руководителя: 3 главных результата, 2 риска, 3 следующих шага. Формат — короткие блоки, без воды». Здесь уже видно, кто говорит, с чем работает и как должен выглядеть ответ.",
                                    "Практикада кыска, ләкин структуралы промпт еш кына озын һәм буталчык сораудан яхшырак эшли. Ачык роль, кыска контекст, бер конкрет бурыч һәм күренеп торган нәтиҗә форматы, гадәттә, томан абзацка караганда ышанычлырак җавап бирә.",
                                ),
                                tr(
                                    "This pattern also lowers anxiety for beginners. When the result is weak, you can ask which block failed and improve only that part instead of starting from zero.",
                                    "Главный плюс паттерна в том, что его легко улучшать. Если ответ слишком общий, сначала усиливайте Context. Если результат полезный, но в неверной форме, правьте Output. Так вы не гадаете, что «не так со всем промптом», а спокойно находите конкретный слабый блок.",
                                    "Бу паттерн башлангыч дәрәҗәдәге кешенең борчылуын да киметә. Нәтиҗә зәгыйфь булса, «бөтен промпт начар» дип түгел, ә «кайсы блок эшләмәде?» дип карыйсыз. Шуннан соң нәкъ шул өлешне генә яхшыртасыз.",
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
                                    "Constraints are not there to make a prompt sound strict. They are there to narrow the space of bad answers before the model even starts working.",
                                    "Ограничения нужны не для того, чтобы сделать промпт строгим ради строгости. Они нужны, чтобы заранее сузить пространство плохих ответов: не уходить в лишнюю длину, не менять тон, не придумывать факты и не отдавать результат в неудобной форме.",
                                    "Чикләүләр промптны ясалма рәвештә кырысландыру өчен түгел. Алар модель эшли башлаганчы ук начар җаваплар киңлеген тарайта: артык озынлыкны, тонның тайпылуын, уйлап чыгарылган фактларны һәм уңайсыз форматны киметә.",
                                ),
                                tr(
                                    "Use hard constraints for non-negotiables such as safety, format, required fields, or length. Use soft constraints for tone, depth, and style so the model still has room to adapt to the task.",
                                    "Полезно разделять ограничения на жесткие и мягкие. Жесткие — это то, что нельзя нарушать: формат ответа, запрет на выдуманные данные, лимит по длине, обязательные поля. Мягкие — это пожелания к стилю и глубине: например, писать дружелюбно, кратко и на уровне новичка.",
                                    "Чикләүләрне каты һәм йомшак төргә бүлү бик файдалы. Каты чикләүләр иминлек, формат, мәҗбүри бүлекләр яки күләм кебек бозарга ярамаган өлешләр өчен кирәк. Йомшак чикләүләр исә тон, тирәнлек һәм стиль өчен кулланыла, шуңа модель реаль бурычка яраклаша ала.",
                                ),
                                tr(
                                    "Examples work best when they show target structure, not when they invite copying. A short relevant example teaches the shape of a good answer; a long irrelevant one teaches the wrong pattern.",
                                    "Примеры работают не как образец для бездумного копирования, а как маяк. Они помогают тогда, когда действительно похожи на вашу задачу и показывают нужную структуру ответа. Если пример нерелевантный, модель копирует шум, а не логику.",
                                    "Мисаллар максат структураны күрсәткәндә генә көчле эшли. Кыска һәм туры килгән мисал яхшы җавапның формасын күрсәтә, ә озын һәм чит мисал модельгә ялгыш үрнәк бирә.",
                                ),
                                tr(
                                    "A common beginner mistake is stacking too many rigid rules. Then the prompt becomes brittle: it works on one narrow case and breaks as soon as the task changes a little.",
                                    "Хороший пример обычно маленький и целевой. Если вам нужно письмо без ухода от тона бренда, лучше дать один короткий ориентир вроде «тон спокойный, без пафоса, сначала суть, потом следующий шаг», чем вставлять длинный образец на полстраницы, который модель начнет повторять почти дословно.",
                                    "Башлангычларда еш очрый торган хата - артык күп каты кагыйдә өю. Шунда промпт какшакка әйләнә: тар гына бер очракта эшли, ә бурыч бераз гына үзгәрсә дә ватыла башлый.",
                                ),
                                tr(
                                    "The real goal is controllable flexibility: enough structure that you can verify quality, and enough freedom that the model can still solve a real task.",
                                    "Главная цель здесь — управляемая гибкость. Промпт должен быть достаточно собранным, чтобы ответ можно было проверить, и достаточно свободным, чтобы модель адаптировалась под реальный кейс. Если после добавления ограничений ответ стал деревянным и ломается на любом новом вводе, значит вы перетянули контроль.",
                                    "Төп максат - идарә ителә торган сыгылмалылык. Сыйфатны тикшерерлек структура җитәрлек булырга тиеш, ләкин модель реаль бурычны хәл итә алырлык ирек тә калырга тиеш. Әгәр чикләүләрдән соң җавап агачтай катса, димәк контроль артык нык тартылган.",
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
                                    "Strong prompts are rarely born on the first try. Good work usually comes from short loops: make version 1, inspect the failure, change one clear thing, and test again.",
                                    "Хороший промпт почти никогда не рождается с первой попытки. В реальной работе сильный результат появляется через маленькие итерации: сделали версию 1, посмотрели, где она сломалась, внесли одну понятную правку и снова проверили результат.",
                                    "Көчле промпт беренче омтылыштан сирәк туа. Яхшы нәтиҗә, гадәттә, кыска цикллардан җыела: 1 нче версияне ясадың, хатаны күрдең, бер аңлаешлы үзгәреш керттең һәм яңадан тикшердең.",
                                ),
                                tr(
                                    "The biggest beginner mistake is changing everything at once. If you rewrite role, context, format, and examples in one pass, you lose the cause-and-effect signal and learn nothing from the result.",
                                    "Самая частая ошибка новичка — менять все сразу. Переписали роль, добавили новый контекст, поменяли формат, навалили примеров, и в итоге непонятно, что именно сработало. Намного полезнее менять один блок за раз: так вы видите причинно-следственную связь, а не просто надеетесь на удачу.",
                                    "Иң киң таралган хата - барысын да берьюлы үзгәртү. Рольне, контекстны, форматны һәм мисалларны бер үк вакытта алыштырсаң, кайсы үзгәрешнең чынлап ярдәм иткәнен аңлап булмый. Бер блокны гына үзгәртү сәбәп-тәэсир бәйләнешен күрсәтә.",
                                ),
                                tr(
                                    "A practical loop is simple: save the baseline answer, name the problem, write one hypothesis, patch one block, and compare before versus after. For example: 'too broad -> maybe format is weak -> add required sections and a length limit.'",
                                    "Удобный цикл выглядит так: сначала зафиксируйте базовый ответ, потом подпишите, какая у него проблема, затем сформулируйте гипотезу и исправьте только один элемент. Например: «ответ слишком общий; гипотеза — не хватает ограничений по формату; правка — добавить обязательные разделы и лимит длины». После этого сравните до и после.",
                                    "Уңайлы цикл бик гади: базовый җавапны сакла, проблеманы ата, бер гипотеза яз, бер блокны төзәт һәм аннары «элек/соңыннан» чагыштыр. Мәсәлән: «җавап артык гомуми; гипотеза - формат зәгыйфь; төзәтмә - мәҗбүри бүлекләр һәм күләм лимиты өстәү».",
                                ),
                                tr(
                                    "A tiny version log helps a lot. Keep four notes: version, what changed, what effect you saw, and what you will try next.",
                                    "Очень помогает простой журнал итераций. Достаточно четырех строк: версия, что изменили, какой эффект увидели, что попробуете следующим. Такой микро-лог быстро превращает хаос в обучение, потому что вы начинаете замечать повторяющиеся паттерны своих ошибок.",
                                    "Кыска версия журналы бик ярдәм итә. Дүрт кенә язма җитә: версия, нәрсә үзгәрде, нинди нәтиҗә күренде һәм киләсе адымда нәрсә сыналырга тиеш. Шушы микро-лог буталчыкны өйрәнүгә әйләндерә.",
                                ),
                                tr(
                                    "Iteration becomes a real skill when every loop ends with a decision: keep the change, modify it, or roll it back. Then prompting stops being guesswork and starts behaving like engineering.",
                                    "Сильная итерация всегда заканчивается решением, а не ощущением. После каждого круга должно быть понятно: эту правку оставляем, откатываем или усиливаем. Тогда промпт развивается как инженерная система, а не как набор случайных переписываний.",
                                    "Һәр цикл ачык карар белән тәмамланганда гына итерация чын күнекмәгә әйләнә: үзгәрешне калдырыргамы, көчәйтергәме, әллә кире кайтарыргамы. Шул чакта промптинг очраклы фаразлаудан инженериягә күчә.",
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
                                    "A rubric replaces 'looks good' with visible judgment. Without criteria, confident writing can trick you into thinking the answer is useful even when it misses the task.",
                                    "Рубрика качества нужна для одной простой вещи: заменить расплывчатое «ну вроде нормально» на проверяемый разбор ответа. Пока вы оцениваете только общим впечатлением, промпт легко кажется хорошим просто потому, что текст звучит уверенно.",
                                    "Рубрика «ярый кебек» дигән хисне күренеп торган бәяләүгә алыштыра. Критерийлар булмаса, ышанычлы язылган текст сезне җавап файдалы дип алдарга мөмкин, хәтта ул бурычны япмаса да.",
                                ),
                                tr(
                                    "A strong beginner rubric can start with four criteria: relevance, completeness, factual safety, and actionability. These four questions already catch most weak outputs.",
                                    "Для начала достаточно четырех критериев. Релевантность отвечает на вопрос «ответил ли текст именно на задачу», полнота — «закрыл ли он все обязательные части», фактическая надежность — «нет ли выдумок и опасных допущений», применимость — «можно ли взять этот результат и использовать без долгой переделки».",
                                    "Башлангыч дәрәҗә өчен дүрт критерий җитә: релевантлык, тулылык, факт иминлеге һәм куллану мөмкинлеге. Шушы дүрт сорау ук күпчелек зәгыйфь җавапларны тотып ала.",
                                ),
                                tr(
                                    "Score each criterion separately before you write an overall score. This protects you from halo bias, where one polished paragraph hides missing detail or risky assumptions.",
                                    "Важно оценивать критерии отдельно. Сначала поставьте небольшую оценку каждому пункту и коротко запишите причину, а уже потом смотрите на общую картину. Такой подход защищает от эффекта ореола, когда один красивый абзац заставляет нас простить серьезные пробелы в логике или фактах.",
                                    "Һәр критерийны гомуми баллга кадәр аерым бәяләгез. Бу ореол хатасын киметә: матур бер абзац сезне җитди бушлыкларны яки куркыныч фаразларны күрми калырга мәҗбүр итмәсен.",
                                ),
                                tr(
                                    "A rubric is only useful if it leads to action. Low relevance means fix the task, low completeness means clarify output sections, and low factual safety means limit data sources or add an uncertainty rule.",
                                    "Хорошая рубрика всегда ведет к следующему действию. Если провал по релевантности — нужно уточнять Task. Если провал по полноте — укреплять Output. Если модель придумывает лишнее — стоит ограничить источник данных или добавить явное правило «если не знаешь, так и скажи».",
                                    "Рубрика гамәлгә китергәндә генә файдалы. Релевантлык түбән булса - Taskны төгәллә, тулылык җитмәсә - Outputны ныгыт, факт иминлеге начар булса - чыганакларны кыс яисә билгесезлек кагыйдәсе өстә.",
                                ),
                                tr(
                                    "This makes the work calmer and clearer. You stop guessing whether the answer is good and start checking it with rules you can reuse in the next task.",
                                    "На практике рубрика делает работу спокойнее. Вы уже не угадываете, хороший ли ответ получился, а проверяете его по понятным правилам. А значит, можете вернуться к теории, увидеть слабое место и править не вслепую, а осознанно.",
                                    "Бу эшне тынычрак һәм аңлаешлырак итә. Сез җавап яхшымы дип фаразламыйсыз, ә аны яңадан кулланып була торган кагыйдәләр аша тикшерәсез. Шуңа зәгыйфь урынны күрү һәм төзәтү җиңеләя.",
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
                                    "The capstone measures transfer, not memory. You are expected to apply the framework to a real task of your own, not repeat an example from the lesson.",
                                    "Финальный проект проверяет не память, а перенос навыка. Здесь уже недостаточно повторить пример из урока: нужно взять свою реальную задачу и показать, что вы умеете собрать под нее полный рабочий промпт, а не просто красивый текст.",
                                    "Капстоун хәтерне түгел, күнекмәнең күчүен тикшерә. Сездән дәрестәге мисалны кабатлау түгел, ә үзегезнең реаль бурычка шул ук каркасны куллану көтелә.",
                                ),
                                tr(
                                    "A strong final submission shows the full loop: brief, prompt v1, quality check, revision logic, and prompt v2. The value is not only in the final text, but in the path that got you there.",
                                    "Сильная финальная работа показывает весь цикл целиком. Сначала вы формулируете brief: кто пользователь, что нужно получить, какие есть ограничения и что считается хорошим результатом. Затем делаете первую версию промпта, проверяете ее по рубрике качества, находите слабое место и выпускаете улучшенную вторую версию.",
                                    "Көчле финал эш тулы циклны күрсәтә: brief, prompt v1, сыйфат тикшерүе, төзәтү логикасы һәм prompt v2. Кыйммәт финал текстта гына түгел, ә шушы нәтиҗәгә ничек килгәнегездә дә.",
                                ),
                                tr(
                                    "Your work should be reviewable by another person. A teammate should be able to see the task, the expected output, the quality criteria, and the weak point you chose to improve.",
                                    "Очень важно, чтобы ваш результат мог проверить другой человек. Если однокурсник или коллега открывает ваш шаблон и не понимает, как вы собирались оценивать ответ, значит критерии еще слишком расплывчатые. В хорошей работе ясно видно и саму задачу, и форму ответа, и правила проверки.",
                                    "Сезнең эшне башка кеше карый алырлык булырга тиеш. Командадагы кеше бурычны, көтелгән нәтиҗәне, сыйфат критерийларын һәм сез ныгыткан зәгыйфь урынны ачык күрә белергә тиеш.",
                                ),
                                tr(
                                    "Version 2 should not be 'better' only by claim. You need to explain what changed, why you changed it, and what quality signal should improve because of that change.",
                                    "Финальный плюс сильной работы — объяснение изменений. Недостаточно написать «версия 2 лучше». Нужно по-человечески показать, что именно вы изменили и почему это должно было улучшить результат: добавили контекст, сузили формат, убрали лишний пример или усилили проверку. Тогда видно не только итог, но и ваше мышление.",
                                    "2 нче версия «яхшырак» дип кенә аталырга тиеш түгел. Нәрсә үзгәргәнен, ни өчен үзгәрткәнегезне һәм бу үзгәрештән соң кайсы сыйфат сигналы үсәргә тиешлеген ачык аңлату кирәк.",
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

strengthen_practice_steps(
    PROMPT_BASICS_COURSE,
    guided_suffix=tr(
        "Ground it in one believable situation, name who will use the result, and make every marker concrete enough that another learner could run it without follow-up questions.",
        "Опирайтесь на одну правдоподобную ситуацию, назовите, кто будет использовать результат, и заполните каждый маркер так конкретно, чтобы другой ученик смог запустить это без уточняющих вопросов.",
        "Бер ышанычлы хәлгә таяныгыз, нәтиҗәне кем кулланачагын әйтегез һәм һәр маркерны шулкадәр төгәл тутырыгыз ки, башка укучы аны өстәмә сораусыз ук эшләтә алсын.",
    ),
    applied_suffix=tr(
        "Build something worth keeping after the lesson: the result should feel ready to run today, refine tomorrow, and reuse later instead of starting from zero again.",
        "Собирайте не учебную формальность, а заготовку, которую захочется оставить после урока: ее должно быть реально запустить сегодня, доработать завтра и потом переиспользовать, а не писать с нуля.",
        "Дәрестән соң саклап калырлык әйбер төзегез: нәтиҗәне бүген үк эшләтеп була торган, иртәгә яхшыртып һәм соңрак яңадан куллана торган булсын, яңадан нульдән башлыйсы килмәсен.",
    ),
    reflection_suffix=tr(
        "Skip generic self-talk. Point to one exact miss, show how it weakened the answer, and name the next concrete change you will make.",
        "Избегайте общих слов о себе. Укажите один точный промах, покажите, как он ослабил ответ, и назовите следующую конкретную правку.",
        "Гомуми сүзләр белән чикләнмәгез. Бер төгәл хатага күрсәтегез, аның җавапны ничек какшатканын аңлатыгыз һәм киләсе конкрет төзәтмәне атагыз.",
    ),
    reflection_template=tr(
        "I missed [...], so the answer became [...]. In the next prompt I will add/change [...].",
        "Я упустил [...], из-за этого ответ стал [...]. В следующем промпте я добавлю/изменю [...].",
        "Мин [...] өлешен төшереп калдырдым, шуңа җавап [...] булып чыкты. Киләсе промптта мин [...] өстим/үзгәртәм.",
    ),
)
