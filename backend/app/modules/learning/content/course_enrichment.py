from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.modules.learning.content.common import tr


COURSE_ENRICHMENTS: dict[str, dict[str, Any]] = {
    "prompt-engineering-foundations": {
        "result_headline": tr(
            "Build prompts that turn vague requests into usable outputs with predictable quality.",
            "Собирайте промпты, которые превращают размытые запросы в полезный результат с предсказуемым качеством.",
            "Билгесез сорауны тотрыклы сыйфатлы файдалы нәтиҗәгә әйләндерә торган промптлар төзегез.",
        ),
        "deliverable_preview": tr(
            "Reusable prompt brief plus an iteration loop for real tasks.",
            "Переиспользуемый prompt-brief и цикл доработки для реальных задач.",
            "Реаль биремнәр өчен кабат кулланыла торган prompt-brief һәм яхшырту циклы.",
        ),
        "prerequisites": [
            tr(
                "No prior prompt-engineering background is required.",
                "Предыдущий опыт в prompt engineering не требуется.",
                "Prompt engineering буенча элекке тәҗрибә кирәк түгел.",
            ),
            tr(
                "Bring one real task from study, work, or personal projects.",
                "Возьмите одну реальную задачу из учебы, работы или личного проекта.",
                "Укудан, эштән яки шәхси проекттан бер реаль бирем алып килегез.",
            ),
            tr(
                "Be ready to revise your first draft instead of treating the first output as final.",
                "Будьте готовы дорабатывать первый черновик, а не считать первый ответ финальным.",
                "Беренче җавапны финал дип түгел, ә каралама дип карарга әзер булыгыз.",
            ),
        ],
        "deliverables": [
            tr(
                "A structured prompt brief with role, context, task, constraints, output, and check.",
                "Структурированный prompt-brief: роль, контекст, задача, ограничения, формат и проверка.",
                "Структур prompt-brief: роль, контекст, бурыч, чикләү, формат һәм тикшерү.",
            ),
            tr(
                "A repeatable revision loop for weak AI outputs.",
                "Повторяемый цикл доработки для слабых AI-ответов.",
                "Көчсез AI җаваплары өчен кабатлана торган яхшырту циклы.",
            ),
            tr(
                "A quality rubric you can apply before trusting or shipping the result.",
                "Рубрика качества, которую можно применять перед использованием результата.",
                "Нәтиҗәне кулланганчы тикшерә торган сыйфат рубрикасы.",
            ),
        ],
        "career_outcomes": [
            tr(
                "Write clearer prompts for study plans, summaries, and research tasks.",
                "Писать более точные промпты для учебных планов, саммари и исследовательских задач.",
                "Уку планнары, саммари һәм тикшеренү биремнәре өчен төгәлрәк промптлар язу.",
            ),
            tr(
                "Spot weak requests before they waste model calls or time.",
                "Замечать слабые запросы до того, как они потратят время и запросы к модели.",
                "Вакытны һәм модель чакыруларын әрәм иткәнче үк көчсез сорауларны күрү.",
            ),
            tr(
                "Explain why a prompt works instead of copying formulas blindly.",
                "Понимать, почему промпт работает, а не копировать формулы вслепую.",
                "Промпт нигә эшләгәнен аңлау, формуланы сукыр күчермәү.",
            ),
        ],
        "product_action": {
            "label": tr("Open the AI workbench", "Открыть AI-воркбенч", "AI-workbench ачу"),
            "href": "/#home-workbench",
            "body": tr(
                "Use the home workbench to run the prompt pattern from this course on a real task right away.",
                "Запустите паттерн из курса на реальной задаче прямо в домашнем AI-воркбенче.",
                "Курстагы паттернны реаль биремдә шунда ук home workbench эчендә кулланыгыз.",
            ),
        },
        "lessons": {
            "pe-foundations": {
                "objective": tr(
                    "Translate a vague ask into a prompt brief that can actually be executed.",
                    "Перевести размытый запрос в prompt-brief, который можно реально выполнить.",
                    "Билгесез сорауны чынлап башкарып була торган prompt-briefка әйләндерү.",
                ),
                "deliverable": tr(
                    "A first-pass brief with goal, audience, constraints, output format, and quality check.",
                    "Первичный brief с целью, аудиторией, ограничениями, форматом ответа и quality check.",
                    "Максат, аудитория, чикләү, җавап форматы һәм quality check булган беренче brief.",
                ),
                "scenario_title": tr("Case: exam sprint planning", "Кейс: план подготовки к экзамену", "Кейс: имтиханга әзерлек планы"),
                "scenario_body": tr(
                    "A student says 'help me study better'. Your job is to convert that into a task the model can execute today, under real time limits.",
                    "Студент пишет: «помоги мне лучше учиться». Ваша задача - превратить это в запрос, который модель сможет выполнить сегодня с учетом реальных ограничений по времени.",
                    "Студент: «яхшырак укырга булыш». Сезнең бурыч - моны бүген үк, чын вакыт чикләве белән, модель башкара ала торган сорауга әйләндерү.",
                ),
                "debrief": [
                    tr("The original ask hides the user, the success signal, and the practical limit.", "Исходный запрос скрывает пользователя, критерий успеха и практическое ограничение.", "Башлангыч сорауда кулланучы, уңыш сигналы һәм практик чикләү юк."),
                    tr("Better prompting starts with decisions about the job, not with clever wording.", "Хороший промпт начинается с решений о задаче, а не с красивой формулировки.", "Яхшы промпт матур сүздән түгел, бирем турында карардан башлана."),
                    tr("If the result cannot be used today, the prompt is still underspecified.", "Если результат нельзя использовать сегодня, промпт все еще недоопределен.", "Нәтиҗәне бүген кулланып булмый икән, промпт әле дә җитәрлек төгәл түгел."),
                ],
                "review_rubric": [
                    tr("Defines who the output is for.", "Показывает, для кого результат.", "Нәтиҗә кем өчен икәнен күрсәтә."),
                    tr("Names the exact task to perform.", "Называет точное действие.", "Төгәл эшне атый."),
                    tr("Locks a realistic limit or boundary.", "Фиксирует реальное ограничение.", "Реаль чикләүне билгели."),
                    tr("Specifies how output quality will be checked.", "Задает способ проверки качества.", "Сыйфат ничек тикшереләчәген күрсәтә."),
                ],
                "common_mistakes": [
                    tr("Using a generic role with no audience.", "Использовать роль без аудитории.", "Аудиториясез роль куллану."),
                    tr("Leaving success undefined.", "Не определять успешный результат.", "Уңыш нәтиҗәсен билгеләмәү."),
                    tr("Asking for help instead of a concrete deliverable.", "Просить помощь вместо deliverable.", "Deliverable урынына гомуми ярдәм сорау."),
                ],
            },
            "pe-structure-pattern": {
                "objective": tr(
                    "Use role, context, task, and output as control surfaces instead of decoration.",
                    "Использовать role, context, task и output как рычаги управления, а не украшения.",
                    "Role, context, task һәм output-ны бизәк итеп түгел, идарә рычагы итеп куллану.",
                ),
                "deliverable": tr(
                    "A reusable prompt pattern with explicit structure and placeholders.",
                    "Переиспользуемый prompt-pattern с явной структурой и плейсхолдерами.",
                    "Ачык структуралы һәм placeholderлы кабат кулланыла торган prompt-pattern.",
                ),
                "scenario_title": tr("Case: weekly operations update", "Кейс: еженедельное операционное обновление", "Кейс: атналык операцион яңарту"),
                "scenario_body": tr(
                    "A team lead wants a weekly update from messy notes. The prompt needs enough structure to produce a stable summary every Friday.",
                    "Тимлиду нужен еженедельный апдейт из хаотичных заметок. Промпт должен быть настолько структурирован, чтобы выдавать стабильное резюме каждую пятницу.",
                    "Команда лидына буталчык язмалардан атналык апдейт кирәк. Промпт һәр җомгада тотрыклы нәтиҗә бирерлек дәрәҗәдә структуралы булырга тиеш.",
                ),
                "debrief": [
                    tr("Role controls perspective, but context controls relevance.", "Роль задает перспективу, но релевантность задает контекст.", "Роль карашны бирә, ләкин релевантлыкны контекст билгели."),
                    tr("The output block is part of the task, not an afterthought.", "Блок output - это часть задачи, а не добавка в конце.", "Output блогы - соңыннан кушылган әйбер түгел, ә биремнең өлеше."),
                    tr("A template is reusable only if its placeholders encode real decisions.", "Шаблон переиспользуем только тогда, когда плейсхолдеры отражают реальные решения.", "Шаблон placeholderлар реаль карарларны саклаганда гына кабат кулланыла."),
                ],
                "review_rubric": [
                    tr("Role is tied to the task.", "Роль связана с задачей.", "Роль бурычка бәйләнгән."),
                    tr("Context narrows the situation.", "Контекст сужает ситуацию.", "Контекст ситуацияне төгәлли."),
                    tr("Output format is explicit.", "Формат ответа задан явно.", "Җавап форматы ачык."),
                    tr("Placeholders are reusable in new tasks.", "Плейсхолдеры можно перенести в другую задачу.", "Placeholderларны башка биремдә кулланып була."),
                ],
                "common_mistakes": [
                    tr("Adding role without task scope.", "Добавлять роль без рамки задачи.", "Рольне бурыч рамкасыннан башка өстәү."),
                    tr("Writing a template with empty labels only.", "Писать шаблон из одних пустых ярлыков.", "Шаблонны буш ярлыклардан гына язу."),
                    tr("Forgetting the output contract.", "Забывать про контракт ответа.", "Җавап контракты турында оныту."),
                ],
            },
            "pe-constraints-and-examples": {
                "objective": tr(
                    "Reduce ambiguity with constraints and examples without overloading the prompt.",
                    "Снижать неоднозначность через ограничения и примеры, не перегружая промпт.",
                    "Промптны артык катлауландырмыйча, чикләү һәм мисал белән билгесезлекне киметү.",
                ),
                "deliverable": tr(
                    "A constrained prompt that uses one useful example and one quality check.",
                    "Промпт с ограничениями, одним полезным примером и одной quality check.",
                    "Чикләү, бер файдалы мисал һәм бер quality check булган промпт.",
                ),
                "scenario_title": tr("Case: outbound email without brand drift", "Кейс: исходящее письмо без ухода от тона бренда", "Кейс: бренд тавышын югалтмыйча чыгу хаты"),
                "scenario_body": tr(
                    "A founder wants an email draft, but the model keeps sounding generic. You need constraints and a compact example that shape tone without copying.",
                    "Основателю нужен черновик письма, но модель пишет слишком общо. Вам нужны ограничения и короткий пример, которые направляют тон без копирования.",
                    "Фаундерга хат караламасы кирәк, ләкин модель артык гомуми яза. Күчермичә генә тонны бирү өчен чикләү һәм кыска мисал кирәк.",
                ),
                "debrief": [
                    tr("Constraints define where the model must not drift.", "Ограничения задают границы, куда модель не должна уходить.", "Чикләүләр модель кайда тайпылмаска тиешлеген билгели."),
                    tr("Examples are steering signals, not text to be copied.", "Примеры - это сигналы направления, а не текст для копирования.", "Мисаллар - юнәлеш сигналы, күчерү тексты түгел."),
                    tr("One strong example beats several noisy examples.", "Один сильный пример лучше нескольких шумных.", "Бер көчле мисал берничә шау мисалдан яхшырак."),
                ],
                "review_rubric": [
                    tr("Constraint list is concrete.", "Список ограничений конкретный.", "Чикләүләр конкрет."),
                    tr("Example shows tone or structure clearly.", "Пример ясно показывает тон или структуру.", "Мисал тонны яки структураны ачык күрсәтә."),
                    tr("Prompt does not become bloated.", "Промпт не разрастается без пользы.", "Промпт файдасыз рәвештә озаймый."),
                    tr("Check block protects against drift.", "Блок проверки страхует от дрейфа.", "Тикшерү блогы дрейфтан саклый."),
                ],
                "common_mistakes": [
                    tr("Stacking too many rules.", "Наслаивать слишком много правил.", "Артык күп кагыйдә өстәү."),
                    tr("Using an example that should be copied verbatim.", "Использовать пример, который хочется скопировать дословно.", "Сүзгә-сүз күчерәсе килгән мисал куллану."),
                    tr("Treating tone as implied.", "Считать тон подразумеваемым.", "Тон үзе аңлашыла дип уйлау."),
                ],
            },
            "pe-iteration-loop": {
                "objective": tr(
                    "Improve weak outputs through controlled revisions instead of random rewrites.",
                    "Улучшать слабые ответы через контролируемые правки, а не случайные переписывания.",
                    "Көчсез җавапны очраклы яңадан язу белән түгел, контрольле үзгәртү белән яхшырту.",
                ),
                "deliverable": tr(
                    "A versioned prompt pair plus a revision note that explains what changed and why.",
                    "Пара версий промпта и revision note с объяснением, что и зачем изменено.",
                    "Ике версияле промпт һәм нәрсә ни өчен үзгәргәнен аңлаткан revision note.",
                ),
                "scenario_title": tr("Case: generic resume feedback", "Кейс: слишком общее резюме-фидбек", "Кейс: артык гомуми резюме фидбегы"),
                "scenario_body": tr(
                    "The first answer sounds polished but useless. The learner must identify which prompt block to adjust first and prove the effect in v2.",
                    "Первый ответ звучит гладко, но бесполезно. Нужно понять, какой блок менять первым, и доказать эффект во второй версии.",
                    "Беренче җавап матур, ләкин файдасыз. Башта кайсы блокны үзгәртергә кирәклеген табып, икенче версиядә нәтиҗәсен күрсәтергә кирәк.",
                ),
                "debrief": [
                    tr("Iteration without a hypothesis becomes guesswork.", "Итерация без гипотезы быстро превращается в гадание.", "Гипотезасыз итерация тиз генә фаразга әйләнә."),
                    tr("Change one meaningful variable before changing everything.", "Сначала меняйте один значимый параметр, а не все сразу.", "Башта барысын түгел, ә бер әһәмиятле үзгәреш кертегез."),
                    tr("The revision note is evidence that the learner understands causality.", "Revision note - доказательство того, что ученик понимает причинность.", "Revision note укучының сәбәп бәйләнешен аңлавын күрсәтә."),
                ],
                "review_rubric": [
                    tr("Names the failure clearly.", "Четко называет сбой.", "Хатаны ачык атый."),
                    tr("Changes one high-impact block first.", "Сначала меняет один важный блок.", "Башта бер көчле тәэсирле блокны үзгәртә."),
                    tr("Explains why the change should help.", "Объясняет, почему правка должна помочь.", "Үзгәреш ни өчен ярдәм итәргә тиешлеген аңлата."),
                    tr("Compares v1 and v2 explicitly.", "Явно сравнивает v1 и v2.", "v1 белән v2 не ачык чагыштыра."),
                ],
                "common_mistakes": [
                    tr("Changing everything at once.", "Менять все сразу.", "Барысын берьюлы үзгәртү."),
                    tr("Explaining output problems without naming the prompt cause.", "Описывать слабый ответ без причины в промпте.", "Җавап проблемасын әйтеп, промпт сәбәбен атамый калу."),
                    tr("Treating iteration as cosmetic editing.", "Считать итерацию косметикой.", "Итерацияне косметик төзәтү дип санау."),
                ],
            },
            "pe-evaluate-quality": {
                "objective": tr(
                    "Judge outputs with a rubric before accepting them as useful.",
                    "Оценивать ответы по рубрике до того, как считать их полезными.",
                    "Җавапны файдалы дип санаганчы рубрика буенча бәяләү.",
                ),
                "deliverable": tr(
                    "A scoring prompt that returns criteria, total score, and top fixes.",
                    "Оценивающий промпт с критериями, итоговым score и топ-исправлениями.",
                    "Критерий, гомуми score һәм төп төзәтмәләрне чыгара торган бәяләү промпты.",
                ),
                "scenario_title": tr("Case: research summary for a decision", "Кейс: исследовательское summary для решения", "Кейс: карар өчен тикшеренү summary"),
                "scenario_body": tr(
                    "You receive a summary that sounds complete, but the decision still feels risky. The job is to score relevance, completeness, factual safety, and actionability before trust.",
                    "Вы получаете summary, которое звучит полно, но решение все еще рискованно. Нужно оценить релевантность, полноту, фактическую корректность и применимость до доверия.",
                    "Summary тулы кебек яңгырый, ләкин карар әле дә куркыныч. Ышану алдыннан релевантлык, тулылык, факт төгәллеге һәм кулланышлылыкны бәяләргә кирәк.",
                ),
                "debrief": [
                    tr("A polished answer can still fail actionability.", "Даже аккуратный ответ может провалить практическую применимость.", "Матур җавап та кулланышлылык буенча төшәргә мөмкин."),
                    tr("Scoring creates a pause between generation and trust.", "Оценка создает паузу между генерацией и доверием.", "Бәяләү генерация белән ышану арасында пауза ясый."),
                    tr("Top fixes matter more than vague praise.", "Топ-исправления полезнее, чем общая похвала.", "Төп төзәтмәләр гомуми мактаудан файдалырак."),
                ],
                "review_rubric": [
                    tr("Uses explicit criteria.", "Использует явные критерии.", "Ачык критерий куллана."),
                    tr("Separates score from explanation.", "Разделяет оценку и объяснение.", "Бәяне һәм аңлатманы аера."),
                    tr("Includes actionable fixes.", "Добавляет применимые исправления.", "Кулланып була торган төзәтмәләр кертә."),
                    tr("Makes uncertainty visible.", "Делает неопределенность видимой.", "Билгесезлекне күренерлек итә."),
                ],
                "common_mistakes": [
                    tr("Scoring length instead of usefulness.", "Оценивать длину вместо пользы.", "Файда урынына озынлыкны бәяләү."),
                    tr("Using criteria that cannot change a decision.", "Использовать критерии, которые не влияют на решение.", "Карарга тәэсир итми торган критерий куллану."),
                    tr("Giving a score without top fixes.", "Давать оценку без главных правок.", "Төп төзәтмәсез бәя бирү."),
                ],
            },
            "pe-final-studio": {
                "objective": tr(
                    "Package the entire prompt loop into one repeatable workflow for a real task.",
                    "Упаковать весь prompt-loop в один повторяемый workflow для реальной задачи.",
                    "Бөтен prompt-loopны реаль бирем өчен бер кабатлана торган workflowга җыю.",
                ),
                "deliverable": tr(
                    "A production-ready prompt brief, quality check, and revision pass for one real scenario.",
                    "Production-ready prompt-brief, quality check и revision pass для одного реального сценария.",
                    "Бер реаль сценарий өчен production-ready prompt-brief, quality check һәм revision pass.",
                ),
                "scenario_title": tr("Case: this week's high-value task", "Кейс: главная задача этой недели", "Кейс: бу атнаның төп биреме"),
                "scenario_body": tr(
                    "The learner must choose one meaningful task from real work or study, build v1, score it, and submit a stronger v2 that could be reused next week.",
                    "Ученик выбирает одну значимую реальную задачу, строит v1, оценивает ее и сдает усиленную v2, которую можно переиспользовать на следующей неделе.",
                    "Укучы реаль эштән яки укудан бер әһәмиятле бирем сайлый, v1 ясый, бәяли һәм киләсе атнада кабат кулланып була торган көчлерәк v2 тапшыра.",
                ),
                "debrief": [
                    tr("The capstone proves transfer only if the task is real.", "Капстоун доказывает перенос навыка только если задача реальна.", "Капстоун күнекмәнең күчешен бирем реаль булганда гына күрсәтә."),
                    tr("Quality checks are part of the workflow, not a separate afterthought.", "Проверка качества - часть процесса, а не отдельный хвост.", "Сыйфат тикшерүе - аерым койрык түгел, ә процессның өлеше."),
                    tr("A good final workflow can be reused by the learner tomorrow.", "Хороший финальный workflow можно повторить уже завтра.", "Яхшы финал workflowны иртәгә үк яңадан кулланып була."),
                ],
                "review_rubric": [
                    tr("Targets a real task.", "Ориентирован на реальную задачу.", "Реаль биремгә юнәлгән."),
                    tr("Includes prompt plus evaluation logic.", "Содержит и промпт, и логику оценки.", "Промптны да, бәяләү логикасын да үз эченә ала."),
                    tr("Shows what changed between versions.", "Показывает, что изменилось между версиями.", "Версияләр арасында нәрсә үзгәргәнен күрсәтә."),
                    tr("Can be reused with minor edits.", "Можно переиспользовать с небольшими правками.", "Кечкенә үзгәреш белән кабат кулланып була."),
                ],
                "common_mistakes": [
                    tr("Choosing a toy task.", "Выбирать игрушечную задачу.", "Уенчык бирем сайлау."),
                    tr("Submitting v2 without evidence of improvement.", "Сдавать v2 без доказательства улучшения.", "Яхшырту дәлиленсез v2 тапшыру."),
                    tr("Forgetting the final risk to monitor.", "Забывать про риск, который нужно отслеживать.", "Күзәтергә кирәк булган риск турында оныту."),
                ],
            },
        },
    },
    "prompt-workflows-study-and-work": {
        "result_headline": tr(
            "Turn single prompts into multi-stage workflows for research, writing, analysis, and debugging.",
            "Превращайте одиночные промпты в многошаговые workflow для исследований, письма, анализа и отладки.",
            "Бер промптны тикшеренү, язу, анализ һәм төзәтү өчен күп адымлы workflowга әйләндерегез.",
        ),
        "deliverable_preview": tr(
            "A reusable workflow with stages, checks, and fallback logic.",
            "Переиспользуемый workflow со стадиями, проверками и fallback-логикой.",
            "Этап, тикшерү һәм fallback логикасы булган кабат кулланыла торган workflow.",
        ),
        "prerequisites": [
            tr("Complete the foundations course or bring an equivalent prompting habit.", "Завершите базовый курс или уже работайте с промптами осознанно.", "База курсын тәмамлагыз яки промпт белән аңлы эшләү гадәте булсын."),
            tr("Bring one recurring task that needs more than a single model call.", "Возьмите повторяющуюся задачу, для которой мало одного запроса к модели.", "Бер модель чакыруы гына җитми торган кабатлана торган бирем алып килегез."),
            tr("Be ready to compare versions, evidence, and failure modes.", "Будьте готовы сравнивать версии, доказательства и failure modes.", "Версия, дәлил һәм failure mode-ларны чагыштырырга әзер булыгыз."),
        ],
        "deliverables": [
            tr("A workflow brief with stage boundaries and acceptance criteria.", "Workflow-brief с границами этапов и критериями приемки.", "Этап чиге һәм кабул итү критерийлары булган workflow-brief."),
            tr("Reusable patterns for research, writing, decision support, and debugging.", "Переиспользуемые паттерны для research, writing, decision support и debugging.", "Research, writing, decision support һәм debugging өчен кабат кулланыла торган паттерннар."),
            tr("A capstone workflow another teammate can run tomorrow.", "Капстоун-workflow, который другой участник команды сможет запустить завтра.", "Иртәгә башка команда әгъзасы эшләтеп җибәрә ала торган капстоун-workflow."),
        ],
        "career_outcomes": [
            tr("Split complex work into reliable prompt stages instead of one overloaded prompt.", "Разбивать сложную работу на надежные стадии вместо одного перегруженного промпта.", "Катлаулы эшне бер артык авыр промптка түгел, ә ышанычлы этапларга бүлү."),
            tr("Create workflows that are easier to debug, review, and hand off.", "Собирать workflow, которые легче отлаживать, ревьюить и передавать другим.", "Төзәтү, ревью һәм тапшыру җиңел булган workflow төзү."),
            tr("Connect prompting to real outputs like briefs, decision memos, and writing systems.", "Связывать prompting с реальными результатами: brief, decision memo и writing system.", "Promptingны brief, decision memo һәм writing system кебек реаль нәтиҗә белән бәйләү."),
        ],
        "product_action": {
            "label": tr("Open the prompt catalog", "Открыть каталог промптов", "Промпт каталогын ачу"),
            "href": "/catalog",
            "body": tr(
                "Use the catalog to find prompts you can turn into reusable workflows after each lesson.",
                "После урока откройте каталог и найдите промпты, которые можно превратить в переиспользуемый workflow.",
                "Һәр дәрестән соң каталогны ачып, workflowга әйләндерә ала торган промптлар табыгыз.",
            ),
        },
        "lessons": {
            "wf-task-briefing": {
                "objective": tr("Convert a messy request into an execution brief with a clear done-state.", "Преобразовать нечеткий запрос в исполнительный brief с ясным done-state.", "Буталчык сорауны ачык done-state булган үтәү briefына әйләндерү."),
                "deliverable": tr("Workflow brief with goal, stakeholders, constraints, and acceptance criteria.", "Workflow-brief с целью, ролями, ограничениями и критериями приемки.", "Максат, рольләр, чикләү һәм кабул итү критерийлары булган workflow-brief."),
                "scenario_title": tr("Case: project plan before Friday", "Кейс: план проекта до пятницы", "Кейс: җомгага кадәр проект планы"),
                "scenario_body": tr(
                    "A PM says 'we need a better project plan'. The workflow must transform that into a brief another teammate can execute without guessing.",
                    "PM пишет: «нужен план проекта получше». Workflow должен превратить это в brief, который другой участник команды сможет выполнить без догадок.",
                    "PM: «проект планы яхшырак кирәк». Workflow моны башка команда әгъзасы фаразламыйча ук башкара ала торган briefка әйләндерергә тиеш.",
                ),
                "debrief": [
                    tr("A workflow fails early when 'done' is undefined.", "Workflow ломается рано, если не определено состояние «готово».", "Workflow «әзер» билгесез булганда башта ук өзелә."),
                    tr("Stakeholders matter because they change acceptance criteria.", "Стейкхолдеры важны, потому что меняют критерии приемки.", "Stakeholderлар мөһим, чөнки кабул итү критерийларын үзгәртә."),
                    tr("A good brief reduces rework before generation starts.", "Хороший brief сокращает переделки еще до генерации.", "Яхшы brief генерация башланганчы ук кабат эшне киметә."),
                ],
                "review_rubric": [
                    tr("Goal is concrete.", "Цель конкретна.", "Максат конкрет."),
                    tr("Stakeholders are visible.", "Стейкхолдеры указаны.", "Stakeholderлар күрсәтелгән."),
                    tr("Acceptance criteria are testable.", "Критерии приемки можно проверить.", "Кабул итү критерийларын тикшереп була."),
                    tr("Constraint list is realistic.", "Ограничения реалистичны.", "Чикләүләр реалистик."),
                ],
                "common_mistakes": [
                    tr("Jumping straight into generation.", "Сразу переходить к генерации.", "Шунда ук генерациягә күчү."),
                    tr("Confusing objective with output format.", "Путать цель с форматом.", "Максатны формат белән бутау."),
                    tr("Ignoring who will use the result.", "Игнорировать будущего пользователя результата.", "Нәтиҗәне кем кулланачагын оныту."),
                ],
            },
            "wf-research-and-synthesis": {
                "objective": tr("Design a workflow that compares evidence and keeps uncertainty visible.", "Спроектировать workflow, который сравнивает доказательства и держит неопределенность видимой.", "Дәлилләрне чагыштыра һәм билгесезлекне күренерлек тота торган workflow проектлау."),
                "deliverable": tr("A claims table with evidence, confidence, and open questions.", "Claims table с evidence, confidence и open questions.", "Evidence, confidence һәм open questions булган claims table."),
                "scenario_title": tr("Case: choosing between two learning plans", "Кейс: выбор между двумя учебными планами", "Кейс: ике уку планы арасыннан сайлау"),
                "scenario_body": tr(
                    "You need to compare two plans without collapsing uncertainty into fake certainty. The workflow must surface evidence gaps before a decision.",
                    "Нужно сравнить два плана, не превращая неопределенность в ложную уверенность. Workflow должен показать пробелы в evidence до решения.",
                    "Ике планны билгесезлекне ялган ышанычка әйләндермичә чагыштырырга кирәк. Workflow карар алдыннан evidence бушлыкларын күрсәтергә тиеш.",
                ),
                "debrief": [
                    tr("Research quality depends on separation of claims and evidence.", "Качество research зависит от разделения claims и evidence.", "Research сыйфаты claims белән evidence аерым булуга бәйле."),
                    tr("Confidence without evidence is theatre.", "Уверенность без evidence - это театр.", "Evidenceсыз ышаныч - театр гына."),
                    tr("Open questions are a useful output, not a failure.", "Открытые вопросы - это полезный выход, а не провал.", "Ачык сораулар - файдалы нәтиҗә, уңышсызлык түгел."),
                ],
                "review_rubric": [
                    tr("Sources or evidence are explicit.", "Источники или evidence указаны явно.", "Чыганаклар яки evidence ачык күрсәтелгән."),
                    tr("Confidence is visible per claim.", "Уверенность показана по каждому claim.", "Һәр claim буенча ышаныч күрсәтелгән."),
                    tr("Unknowns remain visible.", "Неизвестное остается видимым.", "Билгесез нәрсә яшерелми."),
                    tr("Synthesis does not overstate certainty.", "Синтез не завышает уверенность.", "Синтез ышанычны арттырып күрсәтми."),
                ],
                "common_mistakes": [
                    tr("Jumping to conclusion too early.", "Слишком рано идти к выводу.", "Бик иртә нәтиҗәгә сикерү."),
                    tr("Merging sources without comparison.", "Склеивать источники без сравнения.", "Чыганакларны чагыштырмыйча кушу."),
                    tr("Hiding uncertainty in prose.", "Прятать неопределенность в тексте.", "Билгесезлекне текст эченә яшерү."),
                ],
            },
            "wf-writing-workflow": {
                "objective": tr("Chain outline, draft, and edit so writing quality survives handoff and revision.", "Связать outline, draft и edit так, чтобы качество текста сохранялось при передаче и доработке.", "Outline, draft һәм editны шулай бәйләү: текст сыйфаты тапшыру һәм доработка вакытында саклансын."),
                "deliverable": tr("A writing workflow that returns outline, draft, and editor checklist.", "Writing-workflow, который возвращает outline, draft и editor checklist.", "Outline, draft һәм editor checklist чыгара торган writing-workflow."),
                "scenario_title": tr("Case: publish an internal update", "Кейс: опубликовать внутреннее обновление", "Кейс: эчке яңарту бастыру"),
                "scenario_body": tr(
                    "A team needs a high-quality internal update, but raw drafts keep missing structure and clarity. The workflow should create a reliable writing pipeline.",
                    "Команде нужен качественный внутренний апдейт, но черновики постоянно теряют структуру и ясность. Workflow должен собрать надежный writing pipeline.",
                    "Командага сыйфатлы эчке апдейт кирәк, ләкин караламалар структура һәм ачыклыкны югалта. Workflow ышанычлы writing pipeline бирергә тиеш.",
                ),
                "debrief": [
                    tr("Writing improves when roles are separated by stage.", "Письмо ул этаплар буенча рольләр бүленгәндә яхшыра.", "Язу этаплар буенча рольләр бүленгәндә яхшыра."),
                    tr("Editing is not the same as drafting.", "Редактура - не то же самое, что черновик.", "Редактура каралама белән бер үк түгел."),
                    tr("Checklists stabilize writing quality across repeats.", "Чек-листы стабилизируют качество текста при повторении.", "Чек-листлар кабатлаганда текст сыйфатын тотрыклыландыра."),
                ],
                "review_rubric": [
                    tr("Outline is usable.", "План пригоден к работе.", "План кулланып була торган."),
                    tr("Draft follows the plan.", "Черновик следует плану.", "Каралама планга иярә."),
                    tr("Edit checklist catches quality gaps.", "Редакторский чек-лист ловит пробелы качества.", "Редактор чек-листы сыйфат бушлыкларын тота."),
                    tr("Stages can be rerun independently.", "Этапы можно запускать отдельно.", "Этапларны аерым эшләтеп була."),
                ],
                "common_mistakes": [
                    tr("Asking for perfect prose in one pass.", "Просить идеальный текст за один проход.", "Бер узуда ук камил текст сорау."),
                    tr("Skipping the editor stage.", "Пропускать редакторский этап.", "Редактор этабын калдырып китү."),
                    tr("Letting the draft invent missing facts.", "Позволять черновику додумывать факты.", "Караламага җитмәгән фактны уйлап табарга рөхсәт итү."),
                ],
            },
            "wf-analysis-workflow": {
                "objective": tr("Turn analysis into a decision-ready artifact instead of a generic summary.", "Превратить анализ в decision-ready артефакт, а не в общее summary.", "Анализны гомуми summary түгел, ә decision-ready артефактка әйләндерү."),
                "deliverable": tr("A decision memo with options, criteria, recommendation, and confidence.", "Decision memo с вариантами, критериями, рекомендацией и уверенностью.", "Вариант, критерий, рекомендация һәм ышаныч булган decision memo."),
                "scenario_title": tr("Case: one team, two priorities", "Кейс: одна команда, два приоритета", "Кейс: бер команда, ике приоритет"),
                "scenario_body": tr(
                    "The team only has capacity for one major priority this week. The workflow must force trade-offs and make confidence explicit.",
                    "У команды есть ресурс только на один крупный приоритет этой недели. Workflow должен заставить сравнить компромиссы и явно показать уверенность.",
                    "Команданың бу атнада бер генә зур приоритетка ресурсы бар. Workflow компромиссны мәҗбүр итеп чагыштырырга һәм ышанычны ачык күрсәтергә тиеш.",
                ),
                "debrief": [
                    tr("Analysis is useful only if it supports a choice.", "Анализ полезен только если помогает выбрать.", "Анализ сайлауга ярдәм иткәндә генә файдалы."),
                    tr("Options without criteria become opinion theater.", "Варианты без критериев превращаются в театр мнений.", "Критерийсыз вариантлар фикер театрына әйләнә."),
                    tr("Confidence reveals where follow-up work is still needed.", "Уверенность показывает, где еще нужен follow-up.", "Ышаныч кайда әле дә follow-up кирәклеген күрсәтә."),
                ],
                "review_rubric": [
                    tr("Options are comparable.", "Варианты сравнимы.", "Вариантлар чагыштырыла."),
                    tr("Criteria are explicit.", "Критерии указаны явно.", "Критерийлар ачык."),
                    tr("Recommendation is justified.", "Рекомендация обоснована.", "Рекомендация нигезле."),
                    tr("Confidence is attached to the recommendation.", "К рекомендации привязана уверенность.", "Рекомендациягә ышаныч бәйләнгән."),
                ],
                "common_mistakes": [
                    tr("Giving one answer with no alternatives.", "Давать один ответ без альтернатив.", "Альтернативасыз бер җавап кына бирү."),
                    tr("Listing pros and cons with no decision frame.", "Перечислять плюсы и минусы без рамки решения.", "Плюс-минусны карар рамкасыннан башка гына язу."),
                    tr("Confusing verbosity with rigor.", "Путать объем с rigor.", "Озынлыкны rigor белән бутау."),
                ],
            },
            "wf-prompt-debugging": {
                "objective": tr("Diagnose failure patterns and recover quality with a repeatable debug loop.", "Диагностировать failure patterns и восстанавливать качество через repeatable debug loop.", "Failure patternнарны диагностикалап, repeatable debug loop белән сыйфатны кире кайтару."),
                "deliverable": tr("A debug workflow with failure label, targeted fix, and fallback path.", "Debug-workflow с failure label, точечной правкой и fallback path.", "Failure label, төгәл төзәтү һәм fallback path булган debug-workflow."),
                "scenario_title": tr("Case: policy-sensitive support reply", "Кейс: ответ поддержки с учетом политики", "Кейс: кагыйдәгә бәйле support җавабы"),
                "scenario_body": tr(
                    "A support prompt keeps missing policy exceptions. The learner must classify the failure, isolate the cause, and design a recovery step.",
                    "Support-промпт постоянно пропускает policy exceptions. Нужно классифицировать сбой, выделить причину и собрать шаг восстановления.",
                    "Support-промпт policy exceptionsны һаман калдыра. Хатаны классификацияләп, сәбәбен аерып, кире кайтару адымын җыярга кирәк.",
                ),
                "debrief": [
                    tr("A failure label makes debugging faster.", "Failure label ускоряет отладку.", "Failure label төзәтүне тизләтә."),
                    tr("Controlled comparison is better than random retries.", "Контролируемое сравнение лучше случайных повторов.", "Контрольле чагыштыру очраклы кабатлаудан яхшырак."),
                    tr("Fallback logic keeps the workflow useful even when output drops.", "Fallback-логика сохраняет пользу workflow при просадке качества.", "Сыйфат төшсә дә fallback логика workflowны файдалы итә."),
                ],
                "review_rubric": [
                    tr("Failure is named precisely.", "Сбой назван точно.", "Хата төгәл атала."),
                    tr("Cause is linked to a prompt block.", "Причина связана с блоком промпта.", "Сәбәп промпт блогына бәйләнгән."),
                    tr("Fix is targeted, not generic.", "Правка точечная, а не общая.", "Төзәтү төгәл, гомуми түгел."),
                    tr("Fallback keeps the task moving.", "Fallback позволяет не останавливать задачу.", "Fallback биремне туктатмый."),
                ],
                "common_mistakes": [
                    tr("Retrying with no diagnosis.", "Повторять без диагноза.", "Диагнозсыз кабатлау."),
                    tr("Blaming the model instead of the prompt setup.", "Винить модель вместо prompt setup.", "Prompt setup урынына модельне гаепләү."),
                    tr("Fixing symptoms but not the cause.", "Чинить симптом, а не причину.", "Сәбәпне түгел, симптомны төзәтү."),
                ],
            },
            "wf-capstone": {
                "objective": tr("Ship one end-to-end workflow that another teammate can execute tomorrow.", "Собрать один end-to-end workflow, который завтра сможет выполнить другой участник команды.", "Иртәгә башка команда әгъзасы башкара ала торган бер end-to-end workflow тапшыру."),
                "deliverable": tr("A production-style workflow with stages, checks, fallback, owner, and success metric.", "Workflow в production-стиле: этапы, проверки, fallback, owner и success metric.", "Production-style workflow: этаплар, тикшерүләр, fallback, owner һәм success metric."),
                "scenario_title": tr("Case: operationalize a recurring AI task", "Кейс: операционализировать повторяющуюся AI-задачу", "Кейс: кабатлана торган AI биремен операцион формага кертү"),
                "scenario_body": tr(
                    "Take one recurring task from your real week and convert it into a workflow with stage boundaries, quality checks, fallback logic, and rollout notes.",
                    "Возьмите одну повторяющуюся задачу из реальной недели и превратите ее в workflow с границами этапов, quality checks, fallback-логикой и заметкой по внедрению.",
                    "Реаль атнагыздан бер кабатлана торган бирем алыгыз һәм аны этап чиге, quality checks, fallback логикасы һәм кертү язмасы булган workflowга әйләндерегез.",
                ),
                "debrief": [
                    tr("A workflow becomes production-ready when someone else can run it.", "Workflow становится production-ready, когда его может выполнить другой человек.", "Workflow аны башка кеше дә эшләтә алса production-ready була."),
                    tr("Checks and ownership are part of the design, not documentation fluff.", "Проверки и ownership - часть дизайна, а не лишняя документация.", "Тикшерү һәм ownership - дизайн өлеше, артык документ түгел."),
                    tr("Fallback keeps the system safe under degraded output quality.", "Fallback удерживает систему в безопасном режиме при просадке качества.", "Сыйфат төшкәндә fallback системаны куркынычсыз тота."),
                ],
                "review_rubric": [
                    tr("Stages are explicit.", "Этапы заданы явно.", "Этаплар ачык."),
                    tr("Checks are measurable.", "Проверки измеримы.", "Тикшерүләр үлчәнә."),
                    tr("Owner and cadence are visible.", "Owner и cadence указаны.", "Owner һәм cadence күрсәтелгән."),
                    tr("Fallback path is realistic.", "Fallback path реалистичен.", "Fallback path реалистик."),
                ],
                "common_mistakes": [
                    tr("Designing for yourself only.", "Проектировать только под себя.", "Үзегез өчен генә проектлау."),
                    tr("Ignoring rollout and monitoring.", "Игнорировать rollout и мониторинг.", "Rollout һәм мониторингны оныту."),
                    tr("Writing a pretty flow with no operating detail.", "Писать красивый flow без операционных деталей.", "Операцион детальсез матур flow гына язу."),
                ],
            },
        },
    },
}


def apply_course_enrichment(course: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(course)
    enrichment = COURSE_ENRICHMENTS.get(str(course.get("slug") or ""))
    if not enrichment:
        return out

    lesson_map = dict(enrichment.get("lessons", {}))
    for key, value in enrichment.items():
        if key == "lessons":
            continue
        out[key] = deepcopy(value)

    for module in out.get("modules", []):
        for lesson in module.get("lessons", []):
            lesson_enrichment = lesson_map.get(lesson.get("slug"))
            if not lesson_enrichment:
                continue
            for key, value in lesson_enrichment.items():
                lesson[key] = deepcopy(value)

    return out
