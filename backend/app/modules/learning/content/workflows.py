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


WORKFLOWS_COURSE = {
    "slug": "prompt-workflows-study-and-work",
    "title": tr(
        "Prompt Workflows for Study and Work",
        "Промпт-воркфлоу для учебы и работы",
        "Уку һәм эш өчен промпт-workflow",
    ),
    "subtitle": tr(
        "Apply prompting to real outcomes, not toy examples",
        "Применяйте промптинг к реальным результатам, а не к игрушечным примерам",
        "Промптингны уен мисалларына түгел, чын нәтиҗәгә кулланыгыз",
    ),
    "description": tr(
        "A practical continuation course: build reusable workflows for research, writing, analysis, and daily execution with AI.",
        "Продолжение базового курса: соберите переиспользуемые workflow для исследований, письма, анализа и повседневной работы с ИИ.",
        "База курсын дәвам итү: тикшеренү, язу, анализ һәм көндәлек эш өчен ЯИ эш агымы төзегез.",
    ),
    "difficulty": "intermediate",
    "estimated_minutes": 330,
    "is_free": True,
    "course_reward_lmn": 160,
    "lesson_default_reward_lmn": 22,
    "badge_code": "learning.prompt_workflows",
    "certificate_template": "prompt-workflows-v1",
    "what_you_will_learn": [
        tr(
            "Design prompt workflows that survive context switching",
            "Проектировать промпт-workflow, устойчивые к переключению контекста",
            "Контекст алышынганда да тотрыклы промпт-workflow проектлау",
        ),
        tr(
            "Combine prompting with checklists, rubrics, and deliverable formats",
            "Комбинировать промпты с чек-листами, рубриками и форматами deliverable",
            "Промптны чек-лист, рубрика һәм deliverable форматы белән берләштерү",
        ),
        tr(
            "Diagnose weak outputs and recover quality fast",
            "Быстро диагностировать слабые ответы и восстанавливать качество",
            "Көчсез җавапны тиз диагностикалау һәм сыйфатны кире кайтару",
        ),
    ],
    "modules": [
        {
            "slug": "workflow-foundations",
            "title": tr("Workflow Foundations", "Основы workflow", "Workflow нигезләре"),
            "summary": tr(
                "Build repeatable prompt pipelines for study and planning.",
                "Соберите повторяемые цепочки промптов для учебы и планирования.",
                "Уку һәм планлау өчен кабатлана торган промпт чылбыры төзегез.",
            ),
            "lessons": [
                {
                    "slug": "wf-task-briefing",
                    "title": tr("Task Briefing Workflow", "Workflow постановки задачи", "Бирем брифинг workflow"),
                    "summary": tr(
                        "Convert a messy request into a clean execution brief.",
                        "Преобразуйте нечеткий запрос в чистый исполнительный бриф.",
                        "Буталчык сорауны төгәл үтәү брифына әйләндерегез.",
                    ),
                    "estimated_minutes": 30,
                    "reward_lmn": 20,
                    "is_final_assessment": False,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "wf-brief-theory",
                            "kind": "theory",
                            "title": tr("Theory", "Теория", "Теория"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "Workflow quality is decided before generation. The prompt is not the first artifact here; the brief is. If the brief is vague, the model will optimize for fluency instead of usefulness.",
                                    "Качество процесса решается еще до генерации. Промпт здесь не первый артефакт, а последний метр перед запуском. Если бриф размытый, модель почти неизбежно начнет оптимизировать ответ под гладкость, а не под полезность.",
                                    "Workflow сыйфаты генерациягә кадәр хәл ителә. Монда промпт беренче артефакт түгел, ә соңгы метр гына. Әгәр бриф томан булса, модель җавапны файдага түгел, ә шома яңгырашка көйләп җибәрә.",
                                ),
                                tr(
                                    "A strong brief fixes objective, audience, constraints, inputs, and acceptance criteria. In other words, it aligns people before it instructs the model.",
                                    "Сильный бриф фиксирует цель, аудиторию, ограничения, входные материалы и критерии приемки. Иначе говоря, он сначала выравнивает людей по задаче, а уже потом дает инструкцию модели.",
                                    "Көчле бриф максатны, аудиторияне, чикләүләрне, керү материалларын һәм кабул итү критерийларын терки. Димәк, ул башта кешеләрне бер үк аңлашуга китерә, аннары гына модельгә күрсәтмә бирә.",
                                ),
                                tr(
                                    "If acceptance criteria are missing, teams start confusing output volume with output quality. A long answer may still be operationally empty if it contains no deadlines, risks, or next actions.",
                                    "Если критерии приемки не заданы, команда начинает путать объем ответа с качеством. Длинный текст может выглядеть солидно, но оставаться операционно пустым: без сроков, рисков и следующих действий.",
                                    "Кабул итү критерийлары булмаса, команда җавап күләмен сыйфат белән бутый башлый. Озын текст җитди кебек күренергә мөмкин, ләкин операцион яктан буш кала: срокларсыз, рискларсыз һәм киләсе адымнарсыз.",
                                ),
                                tr(
                                    "A good brief also surfaces hidden assumptions early. That is much cheaper than discovering them after the team already received a polished but wrong result.",
                                    "Хороший бриф еще и рано вытаскивает скрытые допущения. Это гораздо дешевле, чем обнаружить их после того, как команда уже получила аккуратный, но неверный результат.",
                                    "Яхшы бриф яшерен фаразларны да иртә чыгара. Бу команда инде пөхтә, ләкин ялгыш нәтиҗә алганнан соң аңлауга караганда күпкә арзанрак.",
                                ),
                                tr(
                                    "The real test of a brief is handoff. If another teammate cannot run it without extra questions, the brief is still under-specified.",
                                    "Настоящая проверка брифа - handoff. Если другой участник команды не может взять его в работу без дополнительных вопросов, бриф еще недоспецифицирован.",
                                    "Брифның чын тикшерүе - handoff. Әгәр башка команда әгъзасы аны өстәмә сорауларсыз эшкә ала алмаса, бриф әле җитәрлек дәрәҗәдә төгәл түгел.",
                                ),
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "wf-brief-guided",
                            "kind": "guided_practice",
                            "title": tr("Guided Practice", "Практика с опорой", "Юнәлешле практика"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Transform this request into a workflow brief: 'Need a better project plan.' Require scope, deadline, owner, and acceptance criteria in [CHECK].",
                                "Преобразуйте запрос в workflow-бриф: «Нужен план проекта получше». Обязательно задайте scope, дедлайн, owner и критерии приемки в [CHECK].",
                                "«Проект планы яхшырак кирәк» соравын workflow-брифка әйләндерегез. [CHECK] эчендә scope, дедлайн, owner һәм кабул итү критерийларын мәҗбүри куегыз.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "weak_area_tags": ["briefing", "scope-definition"],
                            },
                        },
                        {
                            "slug": "wf-brief-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 5,
                            "submission": _quiz(
                                question=tr(
                                    "What prevents most workflow failures at the start?",
                                    "Что чаще всего предотвращает сбои workflow на старте?",
                                    "Workflow башында өзелүне иң яхшы нәрсә кисәтә?",
                                ),
                                a=tr(
                                    "Using longer prompts immediately.",
                                    "Сразу писать максимально длинный промпт.",
                                    "Шунда ук бик озын промпт язу.",
                                ),
                                b=tr(
                                    "Defining acceptance criteria before generation.",
                                    "Задать критерии приемки до генерации.",
                                    "Генерация алдыннан кабул итү критерийларын билгеләү.",
                                ),
                                c=tr(
                                    "Switching tools every time.",
                                    "Постоянно менять инструменты.",
                                    "Инструментны һәрвакыт алыштыру.",
                                ),
                                exp_a=tr(
                                    "Length is not a substitute for clarity.",
                                    "Длина не заменяет ясность.",
                                    "Озынлык ачыклыкны алыштырмый.",
                                ),
                                exp_b=tr(
                                    "Correct: criteria create a clear done-state.",
                                    "Верно: критерии задают четкое состояние «сделано».",
                                    "Дөрес: критерий «тәмам» халәтен ачык итә.",
                                ),
                                exp_c=tr(
                                    "Tool switching adds noise, not structure.",
                                    "Смена инструментов добавляет шум, а не структуру.",
                                    "Инструмент алыштыру структура түгел, шау өсти.",
                                ),
                            ),
                        },
                        {
                            "slug": "wf-brief-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Create a brief for a real task (exam prep, sprint planning, or client response) and include one risk trigger plus fallback action.",
                                "Соберите бриф для реальной задачи (экзамен, спринт или ответ клиенту) и добавьте один risk trigger и fallback-действие.",
                                "Реаль бурыч өчен бриф төзегез (имтихан, спринт яки клиент җавабы) һәм бер risk trigger белән fallback гамәлен кертегез.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 42,
                                "weak_area_tags": ["transfer", "execution-brief"],
                            },
                        },
                        {
                            "slug": "wf-brief-reflection",
                            "kind": "reflection",
                            "title": tr("Reflection", "Рефлексия", "Рефлексия"),
                            "estimated_minutes": 4,
                            "task": tr(
                                "What part of task briefing saves you the most rework?",
                                "Какая часть брифинга экономит вам больше всего переделок?",
                                "Бирем брифингының кайсы өлеше иң күп кабат эшне киметә?",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 60,
                                "min_words": 12,
                                "required_markers": [],
                                "bonus_markers": [],
                                "forbidden_phrases": [],
                                "weak_area_tags": ["reflection-briefing"],
                            },
                        },
                    ],
                },
                {
                    "slug": "wf-research-and-synthesis",
                    "title": tr("Research and Synthesis Workflow", "Workflow исследования и синтеза", "Тикшеренү һәм синтез workflow"),
                    "summary": tr(
                        "Gather, compare, and synthesize information without hallucination drift.",
                        "Собирайте, сравнивайте и синтезируйте данные без дрейфа в галлюцинации.",
                        "Мәгълүматны галлюцинациягә китмичә җыегыз, чагыштырыгыз һәм синтезлагыз.",
                    ),
                    "estimated_minutes": 32,
                    "reward_lmn": 22,
                    "is_final_assessment": False,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "wf-research-theory",
                            "kind": "theory",
                            "title": tr("Theory", "Теория", "Теория"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "Research workflows exist to slow the jump from question to certainty. The main risk is not slow work; it is fast confidence built on weak evidence.",
                                    "Исследовательский процесс нужен, чтобы замедлить прыжок от вопроса к уверенности. Главный риск здесь не медленная работа, а слишком быстрая уверенность, построенная на слабых данных.",
                                    "Research-workflow сораудан әзер ышанычка сикерүне акрынайту өчен кирәк. Төп куркыныч акрын эш түгел, ә зәгыйфь дәлилгә корылган артык тиз ышаныч.",
                                ),
                                tr(
                                    "A reliable sequence is simple: collect evidence, compare claims, mark uncertainty, then synthesize. When synthesis comes first, evidence becomes decoration instead of support.",
                                    "Надежная последовательность здесь простая: собрать evidence, сравнить claims, отдельно пометить неопределенность и только потом синтезировать вывод. Если синтез возникает первым, evidence превращается в декорацию, а не в опору.",
                                    "Ышанычлы эзлеклелек гади: evidence җый, claims чагыштыр, билгесезлекне билгелә һәм аннары гына синтез яса. Әгәр синтез алдан туса, evidence терәк түгел, ә бизәк кенә булып кала.",
                                ),
                                tr(
                                    "Every key statement should be traceable to either a confirmed fact, a marked assumption, or an open question. Without that split, the reader cannot judge what to trust.",
                                    "Каждый важный тезис должен быть привязан либо к подтвержденному факту, либо к помеченному предположению, либо к открытому вопросу. Без такого разделения читатель не понимает, чему можно доверять.",
                                    "Һәр мөһим фикер я расланган фактка, я билгеләнгән фаразга, я ачык сорауга бәйләнгән булырга тиеш. Мондый аеру булмаса, укучы нәрсәгә ышанырга икәнен аңламый.",
                                ),
                                tr(
                                    "A useful research output is not just a summary; it is a map of confidence. It shows what is known, what is likely, and what still blocks a decision.",
                                    "Полезный исследовательский выход - это не просто summary, а карта уверенности. Она показывает, что уже известно, что пока лишь вероятно и что еще мешает принять решение.",
                                    "Файдалы тикшеренү чыгышы summary гына түгел, ә ышаныч картасы да булырга тиеш. Ул нәрсә билгеле, нәрсә ихтимал һәм нәрсә әле дә карарга комачаулый икәнен күрсәтә.",
                                ),
                                tr(
                                    "That structure is what makes research reusable. Another person can inspect the chain, challenge a claim, or update the conclusion when new evidence appears.",
                                    "Именно такая структура делает исследование переиспользуемым. Другой человек может открыть цепочку, оспорить тезис или обновить вывод, когда появятся новые данные.",
                                    "Нәкъ шушы структура тикшеренүне яңадан кулланыла торган итә. Башка кеше дәлилләр чылбырын карый, бер фикерне бәхәсләшә яки яңа evidence чыккач нәтиҗәне яңарта ала.",
                                )
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "wf-research-guided",
                            "kind": "guided_practice",
                            "title": tr("Guided Practice", "Практика с опорой", "Юнәлешле практика"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Build a prompt for a 2-source comparison that returns: claims table, evidence quality, uncertainty flags, and missing-data requests.",
                                "Соберите промпт для сравнения 2 источников с выходом: таблица claims, качество evidence, флаги неопределенности и запросы недостающих данных.",
                                "2 чыганак чагыштыру өчен промпт төзегез: claims таблицасы, evidence сыйфаты, билгесезлек флаглары һәм җитмәгән мәгълүмат сораулары кайтсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "bonus_markers": ["source", "uncertainty", "assumption"],
                                "weak_area_tags": ["research", "uncertainty-control"],
                            },
                        },
                        {
                            "slug": "wf-research-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr(
                                    "Which output is safest for early synthesis?",
                                    "Какой формат наиболее безопасен для раннего синтеза?",
                                    "Иртә синтез өчен кайсы формат куркынычсызрак?",
                                ),
                                a=tr("Single final conclusion only", "Только один финальный вывод", "Бер финал нәтиҗә генә"),
                                b=tr(
                                    "Claims table: evidence, confidence, open questions",
                                    "Таблица утверждений: доказательство, уверенность, открытые вопросы",
                                    "Фикер таблицасы: дәлил, ышаныч, ачык сораулар",
                                ),
                                c=tr("No structure, free paragraph", "Без структуры, свободный абзац", "Структурасыз ирекле абзац"),
                                exp_a=tr(
                                    "Too compressed, uncertainty gets hidden.",
                                    "Слишком сжато, неопределенность теряется.",
                                    "Артык кыска, билгесезлек югала.",
                                ),
                                exp_b=tr(
                                    "Correct: evidence and confidence are visible.",
                                    "Верно: видны доказательства и уверенность.",
                                    "Дөрес: дәлил һәм ышаныч күренә.",
                                ),
                                exp_c=tr(
                                    "Unstructured output is hard to validate.",
                                    "Неструктурированный ответ трудно проверять.",
                                    "Структурасыз җавапны тикшерү авыр.",
                                ),
                            ),
                        },
                        {
                            "slug": "wf-research-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 9,
                            "task": tr(
                                "Draft a research workflow prompt for choosing between two learning plans with final recommendation confidence and one counterargument.",
                                "Соберите research-workflow промпт для выбора между двумя учебными планами: итоговая уверенность рекомендации и один контраргумент обязательны.",
                                "Ике уку планы арасыннан сайлау өчен research-workflow промпт төзегез: финал ышаныч дәрәҗәсе һәм бер контраргумент мәҗбүри булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 46,
                                "weak_area_tags": ["evidence-use", "decision-support"],
                            },
                        },
                        {
                            "slug": "wf-research-reflection",
                            "kind": "reflection",
                            "title": tr("Reflection", "Рефлексия", "Рефлексия"),
                            "estimated_minutes": 4,
                            "task": tr(
                                "Which uncertainty signal will you always include from now on?",
                                "Какой сигнал неопределенности вы будете включать всегда?",
                                "Алга таба һәрвакыт кайсы билгесезлек сигналын кертәчәксез?",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 60,
                                "min_words": 12,
                                "required_markers": [],
                                "bonus_markers": [],
                                "forbidden_phrases": [],
                                "weak_area_tags": ["research-awareness"],
                            },
                        },
                    ],
                },
                {
                    "slug": "wf-writing-workflow",
                    "title": tr("Writing Workflow", "Workflow для текста", "Язу workflow"),
                    "summary": tr(
                        "Move from draft to publish-ready text with checkpoints.",
                        "Переходите от черновика к готовому тексту через контрольные точки.",
                        "Караламадан әзер текстка контроль нокталары аша күчегез.",
                    ),
                    "estimated_minutes": 34,
                    "reward_lmn": 26,
                    "is_final_assessment": True,
                    "unlock_after_lessons": ["wf-task-briefing", "wf-research-and-synthesis"],
                    "steps": [
                        {
                            "slug": "wf-writing-theory",
                            "kind": "theory",
                            "title": tr("Theory", "Теория", "Теория"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "Strong writing workflows separate modes of thinking because planning, drafting, and editing optimize for different things. When you force them into one step, quality starts fighting with speed.",
                                    "Сильный процесс работы с текстом разделяет режимы мышления, потому что планирование, черновик и редактирование оптимизируют разные вещи. Когда вы пытаетесь сжать их в один шаг, качество почти всегда начинает проигрывать скорости.",
                                    "Көчле writing-workflow фикерләү режимнарын аера, чөнки планлаштыру, каралама язу һәм редактура төрле максатка эшли. Аларны бер адымга кысканда, сыйфат еш кына тизлеккә җиңелә.",
                                ),
                                tr(
                                    "Planner decides purpose, audience, and structure. Writer turns that plan into material. Editor checks logic, clarity, risk, and excess certainty.",
                                    "Planner решает, зачем пишется текст, кто его читает и как должна выглядеть структура. Writer превращает этот каркас в материал. Editor проверяет логику, ясность, риски и лишнюю уверенность.",
                                    "Planner максатны, аудиторияне һәм структураны билгели. Writer шул каркастан текст җыя. Editor логиканы, ачыклыкны, рискларны һәм артык ышанычны тикшерә.",
                                ),
                                tr(
                                    "When these modes collapse into one step, prose often gets smoother while meaning gets weaker. The text sounds finished before the thinking is finished.",
                                    "Когда эти режимы схлопываются в один шаг, текст часто становится более гладким, но менее точным. Он звучит как готовый, хотя само мышление внутри него еще не дозрело.",
                                    "Бу режимнар бер адымга кушылса, текст шомара, ләкин мәгънәсе еш зәгыйфьләнә. Уйлау әле бетмәгән килеш, нәтиҗә инде «әзер» кебек яңгырый башлый.",
                                ),
                                tr(
                                    "Useful checkpoints are simple: does the text answer the task, is it grounded in the input, and can the target reader act on it? If one of these fails, style polishing should not be your next move.",
                                    "Полезные checkpoints здесь простые: отвечает ли текст на задачу, опирается ли он на входные материалы и может ли целевая аудитория что-то сделать с этим результатом. Если хотя бы один пункт провален, следующий шаг - не полировка стиля, а возврат к основе.",
                                    "Файдалы checkpoints бик гади: текст бурычны яптымы, ул керү материалларына таянаммы һәм максат аудиториясе аның белән эшли аламы? Шуларның берсе дә эшләмәсә, киләсе адым стильне ялтырату түгел, ә нигезгә кире кайту булырга тиеш.",
                                ),
                                tr(
                                    "This is what makes writing reproducible. You stop waiting for inspiration and start using a process that still works under deadlines, fatigue, and context switching.",
                                    "Именно это делает письмо воспроизводимым. Вы перестаете ждать вдохновения и начинаете пользоваться процессом, который работает под дедлайном, усталостью и сменой контекста.",
                                    "Нәкъ менә бу язуны кабатлана торган процесска әйләндерә. Сез илһам көтүдән туктыйсыз һәм дедлайн, ару һәм контекст алышыну шартларында да эшли торган процесс куллана башлыйсыз.",
                                )
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "wf-writing-guided",
                            "kind": "guided_practice",
                            "title": tr("Guided Practice", "Практика с опорой", "Юнәлешле практика"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Create a prompt that produces outline, draft, and edit checklist in one flow, with separate headings for each stage and a quality gate in [CHECK].",
                                "Соберите промпт, который дает план, черновик и чек-лист редактуры в одном потоке, с отдельными заголовками этапов и quality gate в [CHECK].",
                                "Бер агымда план, каралама һәм редактура чек-листы чыгара торган промпт төзегез: һәр этап өчен аерым башлам һәм [CHECK] эчендә quality gate булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 45,
                                "bonus_markers": ["outline", "draft", "edit"],
                                "weak_area_tags": ["writing-flow", "multi-stage"],
                            },
                        },
                        {
                            "slug": "wf-writing-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr(
                                    "What makes writing output easier to edit?",
                                    "Что делает текст проще для редактуры?",
                                    "Текстны төзәтүне нәрсә җиңеләйтә?",
                                ),
                                a=tr("One giant paragraph", "Один большой абзац", "Бер зур абзац"),
                                b=tr("Sections with purpose labels", "Секции с метками назначения", "Максат тамгасы булган бүлекләр"),
                                c=tr("Random style shifts", "Случайные смены стиля", "Очраклы стиль алышыну"),
                                exp_a=tr("Hard to navigate.", "Сложно навигировать.", "Юл табу авыр."),
                                exp_b=tr("Correct: structure enables precise edits.", "Верно: структура упрощает точечную правку.", "Дөрес: структура төгәл төзәтүне җиңеләйтә."),
                                exp_c=tr("Inconsistent tone hurts clarity.", "Непоследовательный стиль ухудшает ясность.", "Стиль тотрыксызлыгы ачыклыкны киметә."),
                            ),
                        },
                        {
                            "slug": "wf-writing-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 10,
                            "task": tr(
                                "Build a writing workflow prompt for a post, email, or documentation page with explicit audience level, tone constraints, and final edit rubric.",
                                "Соберите writing-workflow промпт для поста, письма или документации с явным уровнем аудитории, ограничениями тона и финальной рубрикой редактуры.",
                                "Пост, хат яки документация өчен writing-workflow промпт төзегез: аудитория дәрәҗәсе, тон чикләүләре һәм финал редактура рубрикасы ачык булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 52,
                                "pass_score": 75,
                                "weak_area_tags": ["writing-transfer", "editing-loop"],
                            },
                        },
                        {
                            "slug": "wf-writing-final",
                            "kind": "final_checkpoint",
                            "title": tr("Module Final Checkpoint", "Финальная проверка модуля", "Модульнең финал тикшерүе"),
                            "estimated_minutes": 7,
                            "task": tr(
                                "Deliver a final writing workflow with explicit quality checks in [CHECK].",
                                "Сдайте финальный writing-workflow с явными проверками качества в [CHECK].",
                                "[CHECK] эчендә ачык сыйфат тикшерүе белән финал writing-workflow бирегез.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 56,
                                "pass_score": 76,
                                "required_markers": [
                                    "[ROLE]",
                                    "[CONTEXT]",
                                    "[TASK]",
                                    "[CONSTRAINTS]",
                                    "[OUTPUT]",
                                    "[CHECK]",
                                ],
                                "weak_area_tags": ["module-1-synthesis"],
                            },
                        },
                    ],
                },
            ],
        },
        {
            "slug": "professional-execution",
            "title": tr("Professional Execution", "Профессиональное применение", "Профессиональ куллану"),
            "summary": tr(
                "Bring workflows into analysis, debugging, and final delivery.",
                "Перенесите workflow в анализ, отладку и финальную сдачу.",
                "Workflow-ны анализ, төзәтү һәм финал тапшыруга кертегез.",
            ),
            "lessons": [
                {
                    "slug": "wf-analysis-workflow",
                    "title": tr("Analysis Workflow", "Workflow аналитики", "Анализ workflow"),
                    "summary": tr(
                        "Use prompting for decisions, not just text generation.",
                        "Используйте промптинг для принятия решений, а не только для текста.",
                        "Промптингны текст өчен генә түгел, карар кабул итү өчен дә кулланыгыз.",
                    ),
                    "estimated_minutes": 30,
                    "reward_lmn": 22,
                    "is_final_assessment": False,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "wf-analysis-theory",
                            "kind": "theory",
                            "title": tr("Theory", "Теория", "Теория"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "Analysis is for decisions, not for impressive summaries. Its job is to preserve the structure of choice instead of hiding it behind polished prose.",
                                    "Аналитический процесс нужен не для впечатляющего summary, а для принятия решения. Его задача - сохранить структуру выбора, а не спрятать ее за гладким текстом.",
                                    "Анализ впечатляющий summary өчен түгел, ә карар кабул итү өчен кирәк. Аның эше - сайлау структурасын саклау, ә аны шома текст артына яшермәү.",
                                ),
                                tr(
                                    "That means comparing options under the same criteria, not giving each option its own free-form paragraph. The same grid is what makes comparison honest.",
                                    "Это значит сравнивать варианты по одним и тем же критериям, а не раздавать каждому свой свободный абзац. Именно общая сетка делает сравнение честным.",
                                    "Бу вариантларны бер үк критерийлар буенча чагыштыруны аңлата, һәрберсенә ирекле абзац бирүне түгел. Нәкъ уртак челтәр чагыштыруны гадел итә.",
                                ),
                                tr(
                                    "Good analysis keeps downside and confidence visible. A recommendation without failure conditions is only polished preference.",
                                    "Хорошая аналитика держит на виду downside и confidence. Рекомендация без условий отказа - это просто отполированное предпочтение.",
                                    "Яхшы анализ downside белән confidenceны яшерми. Уңышсызлык шартлары күрсәтелмәгән рекомендация - ул бары тик матурланган өстенлек кенә.",
                                ),
                                tr(
                                    "Decision-ready work also includes the reason not to choose each option. That is where real trade-offs become visible.",
                                    "Анализ, готовый к решению, всегда включает и причину не выбирать каждый вариант. Именно там становятся видны настоящие trade-offs.",
                                    "Карарга әзер анализ һәр вариантны нигә сайламаска мөмкин икәнен дә күрсәтергә тиеш. Чын trade-offs нәкъ шунда күренә.",
                                ),
                                tr(
                                    "Once this structure is present, judgment stops looking magical. The learner sees options, criteria, evidence, risk, and a recommendation with limits.",
                                    "Когда такая структура появляется, суждение перестает выглядеть магией. Пользователь видит варианты, критерии, evidence, риск и рекомендацию с границами применимости.",
                                    "Мондый структура барлыкка килгәч, карар магия кебек күренми башлый. Укучы вариантларны, критерийларны, evidenceны, рискларны һәм чикләре булган рекомендацияне күрә.",
                                )
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "wf-analysis-guided",
                            "kind": "guided_practice",
                            "title": tr("Guided Practice", "Практика с опорой", "Юнәлешле практика"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Create a decision prompt with at least 3 options, trade-offs per option, recommendation confidence, and one 'do-nothing' baseline.",
                                "Соберите decision-промпт минимум с 3 вариантами, компромиссами по каждому варианту, уверенностью рекомендации и baseline «ничего не менять».",
                                "Decision-промпт төзегез: кимендә 3 вариант, һәр вариантка компромисслар, тәкъдим ышанычы һәм «берни үзгәртмәү» baseline булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "bonus_markers": ["trade-off", "confidence", "option"],
                                "weak_area_tags": ["analysis", "decision-quality"],
                            },
                        },
                        {
                            "slug": "wf-analysis-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr(
                                    "What makes analysis output decision-ready?",
                                    "Что делает аналитический вывод пригодным для решения?",
                                    "Анализ нәтиҗәсен карар өчен әзер иткән нәрсә нәрсә?",
                                ),
                                a=tr("Only one recommendation", "Только одна рекомендация", "Бер тәкъдим генә"),
                                b=tr("Options + criteria + confidence", "Варианты + критерии + уверенность", "Вариантлар + критерийлар + ышаныч"),
                                c=tr("Maximum verbosity", "Максимальный объем", "Максималь күләм"),
                                exp_a=tr("No comparison context.", "Нет контекста для сравнения.", "Чагыштыру контексты юк."),
                                exp_b=tr("Correct: comparable structure supports choice.", "Верно: сравнимая структура поддерживает выбор.", "Дөрес: чагыштырыла торган структура сайлауны җиңеләйтә."),
                                exp_c=tr("Volume does not equal usefulness.", "Объем не равен полезности.", "Күләм файдалылык дигән сүз түгел."),
                            ),
                        },
                        {
                            "slug": "wf-analysis-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 9,
                            "task": tr(
                                "Build an analysis prompt for choosing a weekly priority under limited time with criteria weights and an explicit rejected option.",
                                "Соберите аналитический промпт для выбора недельного приоритета при дефиците времени с весами критериев и явно отклоненным вариантом.",
                                "Вакыт чикле шартта атналык приоритет сайлау өчен анализ промпт төзегез: критерий авырлыклары һәм ачык кире кагылган вариант булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 45,
                                "weak_area_tags": ["priority-analysis", "constraint-decisions"],
                            },
                        },
                        {
                            "slug": "wf-analysis-reflection",
                            "kind": "reflection",
                            "title": tr("Reflection", "Рефлексия", "Рефлексия"),
                            "estimated_minutes": 4,
                            "task": tr(
                                "Which criterion do you rely on too much when deciding?",
                                "На какой критерий вы обычно опираетесь слишком сильно?",
                                "Карар кабул иткәндә кайсы критерийга артык таянасыз?",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 60,
                                "min_words": 12,
                                "required_markers": [],
                                "bonus_markers": [],
                                "forbidden_phrases": [],
                                "weak_area_tags": ["decision-bias-awareness"],
                            },
                        },
                    ],
                },
                {
                    "slug": "wf-prompt-debugging",
                    "title": tr("Prompt Debugging Workflow", "Workflow отладки промптов", "Промпт төзәтү workflow"),
                    "summary": tr(
                        "Find failure patterns and recover output quality systematically.",
                        "Системно находите сбои и восстанавливайте качество ответа.",
                        "Хата паттернын системалы табып, җавап сыйфатын кире кайтарыгыз.",
                    ),
                    "estimated_minutes": 32,
                    "reward_lmn": 24,
                    "is_final_assessment": False,
                    "unlock_after_lessons": [],
                    "steps": [
                        {
                            "slug": "wf-debug-theory",
                            "kind": "theory",
                            "title": tr("Theory", "Теория", "Теория"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "Debugging turns vague dissatisfaction into a repeatable method. You stop reacting to a bad answer emotionally and start treating it like a diagnosable system failure.",
                                    "Процесс отладки превращает смутное недовольство в повторяемый метод. Вы перестаете эмоционально реагировать на плохой ответ и начинаете видеть в нем диагностируемый сбой системы.",
                                    "Төзәтү томан ризасызлыкны кабатлана торган ысулга әйләндерә. Сез начар җавапка хис белән генә карамыйсыз, ә аны диагноз куеп була торган система сбое итеп күрәсез.",
                                ),
                                tr(
                                    "Start by naming the failure precisely: vague, off-target, shallow, unsafe, or structurally incomplete. Precise labels make weak answers discussable and fixable.",
                                    "Начинать лучше с точного ярлыка сбоя: размыто, мимо задачи, поверхностно, небезопасно, структурно неполно. Точный ярлык делает слабый ответ обсуждаемым и исправимым.",
                                    "Башлау өчен хатага төгәл ярлык бирегез: томан, максаттан чит, өстән-өстән, куркыныч, структурасы тулы түгел. Төгәл ярлык зәгыйфь җавапны аңлашыла һәм төзәтелә торган итә.",
                                ),
                                tr(
                                    "Then map the failure to the likely prompt block. Bad relevance is often a Task problem; invented detail is often a Context or constraint problem; messy shape is usually an Output problem.",
                                    "После этого свяжите сбой с вероятным блоком промпта. Плохая релевантность часто означает проблему в Task, придуманные детали - проблему в Context или ограничениях, а хаотичная форма обычно указывает на Output.",
                                    "Аннары хатаны ихтимал промпт блогы белән бәйләгез. Релевантлык начар булса, еш кына сәбәп Taskта; уйлап чыгарылган детальләр Contextта яки чикләүләрдә; буталчык форма, гадәттә, Output белән бәйле.",
                                ),
                                tr(
                                    "Change one block at a time and compare before versus after. Multiple edits feel productive, but they destroy the learning signal.",
                                    "Меняйте только один блок за раз и сравнивайте до и после. Несколько правок сразу выглядят продуктивно, но именно они убивают учебный сигнал.",
                                    "Бер вакытта бер блокны гына үзгәртегез һәм «элек/соңыннан» чагыштырыгыз. Берничә төзәтмә берьюлы нәтиҗәле кебек тоела, ләкин нәкъ алар өйрәнү сигналын юк итә.",
                                ),
                                tr(
                                    "A good debug loop ends with both a decision and a lesson. You keep the change, refine it, or roll it back, and you understand why.",
                                    "Хороший дебаг-цикл заканчивается не только решением, но и уроком. Вы либо оставляете изменение, либо уточняете его, либо откатываете - и понимаете почему.",
                                    "Яхшы дебаг-цикл карар белән генә түгел, сабак белән дә тәмамлана. Сез үзгәрешне йә калдырасыз, йә төгәллисез, йә кире кайтарасыз - һәм ни өчен шулай эшләгәнегезне аңлыйсыз.",
                                )
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "wf-debug-guided",
                            "kind": "guided_practice",
                            "title": tr("Guided Practice", "Практика с опорой", "Юнәлешле практика"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Write a debug prompt that outputs: failure label, root cause hypothesis, targeted revision, and expected quality delta.",
                                "Сделайте debug-промпт с выходом: ярлык сбоя, гипотеза причины, точечная правка и ожидаемый прирост качества.",
                                "Debug-промпт языгыз: хата ярлыгы, төп сәбәп гипотезасы, төгәл төзәтмә һәм көтелгән сыйфат үсеше кайтсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "bonus_markers": ["failure mode", "revision", "risk"],
                                "weak_area_tags": ["debugging", "quality-recovery"],
                            },
                        },
                        {
                            "slug": "wf-debug-quiz",
                            "kind": "quiz",
                            "title": tr("Checkpoint Quiz", "Квиз-проверка", "Тикшерү квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr(
                                    "Which debugging move gives the clearest signal?",
                                    "Какой шаг отладки дает самый чистый сигнал?",
                                    "Кайсы төзәтү адымы иң чиста сигнал бирә?",
                                ),
                                a=tr("Change everything at once", "Изменить все сразу", "Барысын берьюлы үзгәртү"),
                                b=tr("Change one block and compare outputs", "Изменить один блок и сравнить выход", "Бер блокны үзгәртеп нәтиҗәне чагыштыру"),
                                c=tr("Retry without modifications", "Повторить без изменений", "Үзгәртүсез яңадан кабатлау"),
                                exp_a=tr("You lose causality.", "Теряется причинность.", "Сәбәп бәйләнеше югала."),
                                exp_b=tr("Correct: controlled delta reveals impact.", "Верно: контролируемая дельта показывает влияние.", "Дөрес: контрольле дельта тәэсирне күрсәтә."),
                                exp_c=tr("No new information is introduced.", "Новой информации почти нет.", "Яңа мәгълүмат диярлек юк."),
                            ),
                        },
                        {
                            "slug": "wf-debug-applied",
                            "kind": "applied_exercise",
                            "title": tr("Applied Exercise", "Прикладное упражнение", "Кулланма күнегү"),
                            "estimated_minutes": 10,
                            "task": tr(
                                "Choose a weak prompt from your own work and write a debug+fix workflow with two revision cycles and one rollback condition.",
                                "Возьмите слабый промпт из своей практики и соберите workflow отладки с двумя циклами правок и одним условием отката.",
                                "Үз эшегездән көчсез промпт алып, ике төзәтү циклы һәм бер rollback шарты булган debug+fix workflow языгыз.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 54,
                                "pass_score": 75,
                                "weak_area_tags": ["self-debugging", "repair-loop"],
                            },
                        },
                        {
                            "slug": "wf-debug-reflection",
                            "kind": "reflection",
                            "title": tr("Reflection", "Рефлексия", "Рефлексия"),
                            "estimated_minutes": 4,
                            "task": tr(
                                "What failure label appears most often in your prompts?",
                                "Какой ярлык сбоя чаще всего встречается в ваших промптах?",
                                "Сезнең промптларда иң еш очрый торган хата ярлыгы кайсы?",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 60,
                                "min_words": 12,
                                "required_markers": [],
                                "bonus_markers": [],
                                "forbidden_phrases": [],
                                "weak_area_tags": ["debug-awareness"],
                            },
                        },
                    ],
                },
                {
                    "slug": "wf-capstone",
                    "title": tr("Workflow Capstone", "Финальный проект процесса", "Эш агымының финал проекты"),
                    "summary": tr(
                        "Deliver one end-to-end workflow for your own real scenario.",
                        "Соберите один end-to-end workflow для вашего реального сценария.",
                        "Үз реаль сценариегыз өчен бер end-to-end workflow тапшырыгыз.",
                    ),
                    "estimated_minutes": 40,
                    "reward_lmn": 32,
                    "is_final_assessment": True,
                    "unlock_after_lessons": ["wf-analysis-workflow", "wf-prompt-debugging"],
                    "steps": [
                        {
                            "slug": "wf-capstone-brief",
                            "kind": "theory",
                            "title": tr("Capstone Brief", "Бриф финального проекта", "Финал проект брифы"),
                            "estimated_minutes": 5,
                            "content": [
                                tr(
                                    "The capstone standard is simple: package the workflow so another person can run it tomorrow without you. If it lives only in your head, it is not a system yet.",
                                    "Стандарт финального проекта очень простой: оформите workflow так, чтобы завтра его мог запустить другой человек без вас. Если он живет только у вас в голове, это еще не система.",
                                    "Капстоун стандарты гади: workflowны иртәгә башка кеше сезсез дә эшләтерлек итеп җыегыз. Әгәр ул бары тик сезнең башыгызда гына яши икән, димәк ул әле система түгел.",
                                ),
                                tr(
                                    "That usually means stage boundaries, inputs and outputs, checks, fallback behavior, and clear ownership. Otherwise the first handoff turns into improvisation.",
                                    "Обычно это означает границы этапов, входы и выходы, проверки, fallback-поведение и ясную ответственность. Иначе первый же handoff превращается в импровизацию.",
                                    "Бу, гадәттә, этап чиген, керү-чыгуны, тикшерүләрне, fallback тәртибен һәм ачык җаваплылыкны аңлата. Югыйсә беренче handoff ук импровизациягә әйләнә.",
                                ),
                                tr(
                                    "The real target is transferability. The workflow should survive handoff, context switching, and ordinary human forgetfulness.",
                                    "Главная цель здесь - переносимость. Процесс должен переживать handoff, смену контекста и обычную человеческую забывчивость.",
                                    "Төп максат - күчерелеш. Workflow handoffны, контекст алышынуны һәм гадәти кешелек онытучанлыгын уза алырга тиеш.",
                                ),
                                tr(
                                    "Final quality is proved operationally: what starts the process, what counts as success, what signals failure, and what happens next. That is when a clever prompt becomes a working system.",
                                    "Финальное качество доказывается операционно: что запускает процесс, что считается успехом, какой сигнал означает сбой и что происходит дальше. Именно так умный промпт превращается в рабочую систему.",
                                    "Финал сыйфат операцион яктан исбатлана: процессны нәрсә эшләтеп җибәрә, нәрсә уңыш дип санала, нинди сигнал хата турында әйтә һәм аннары нәрсә була. Нәкъ шул чакта акыллы промпт эшли торган системага әйләнә.",
                                )
                            ],
                            "submission": {"type": "none"},
                        },
                        {
                            "slug": "wf-capstone-v1",
                            "kind": "guided_practice",
                            "title": tr("Workflow v1", "Процесс версия 1", "Эш агымы 1 нче версия"),
                            "estimated_minutes": 8,
                            "task": tr(
                                "Submit end-to-end workflow v1 with stage boundaries, measurable [CHECK], and explicit owner for each stage.",
                                "Отправьте end-to-end workflow v1 с границами этапов, измеримым [CHECK] и явным owner для каждого этапа.",
                                "End-to-end workflow v1 җибәрегез: этап чиге, үлчәнә торган [CHECK] һәм һәр этап өчен ачык owner булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 58,
                                "pass_score": 76,
                                "bonus_markers": ["Stage 1", "Stage 2", "Stage 3", "[CHECK]"],
                                "weak_area_tags": ["capstone-v1"],
                            },
                        },
                        {
                            "slug": "wf-capstone-quiz",
                            "kind": "quiz",
                            "title": tr("Synthesis Quiz", "Синтез-квиз", "Синтез квизы"),
                            "estimated_minutes": 4,
                            "submission": _quiz(
                                question=tr(
                                    "What makes a workflow production-ready?",
                                    "Что делает workflow готовым к продакшену?",
                                    "Workflow-ны продакшенга әзер иткән нәрсә нәрсә?",
                                ),
                                a=tr("Looks impressive", "Выглядит впечатляюще", "Матур күренә"),
                                b=tr("Clear inputs, checks, failure recovery", "Ясные входы, проверки и восстановление после сбоя", "Ачык керү, тикшерү һәм хата булганда торгызу"),
                                c=tr("Very long prompt text", "Очень длинный текст промпта", "Бик озын промпт тексты"),
                                exp_a=tr("Appearance is not reliability.", "Внешний вид не равен надежности.", "Тышкы күренеш ышанычлылык түгел."),
                                exp_b=tr("Correct: operational clarity drives reliability.", "Верно: операционная ясность дает надежность.", "Дөрес: операцион ачыклык ышанычлылык бирә."),
                                exp_c=tr("Length can hide missing logic.", "Длина может скрывать отсутствующую логику.", "Озынлык җитмәгән логиканы яшерергә мөмкин."),
                            ),
                        },
                        {
                            "slug": "wf-capstone-v2",
                            "kind": "applied_exercise",
                            "title": tr("Workflow v2", "Процесс версия 2", "Эш агымы 2 нче версия"),
                            "estimated_minutes": 12,
                            "task": tr(
                                "Submit v2 with one measurable upgrade, one fallback path if quality drops, and one regression test you will run weekly.",
                                "Отправьте v2 с одним измеримым улучшением, одним fallback-путем при падении качества и одним регрессионным тестом на еженедельный запуск.",
                                "v2 җибәрегез: бер үлчәнә торган яхшырту, сыйфат төшсә бер fallback юлы һәм атна саен эшләтеләчәк бер regression тест булсын.",
                            ),
                            "submission": {
                                **_BASE_TEXT_VALIDATOR,
                                "min_words": 65,
                                "pass_score": 78,
                                "bonus_markers": ["fallback", "metric", "threshold"],
                                "weak_area_tags": ["capstone-v2", "operational-quality"],
                            },
                        },
                        {
                            "slug": "wf-capstone-final",
                            "kind": "final_checkpoint",
                            "title": tr("Course Final Checkpoint", "Финальная проверка курса", "Курсның финал тикшерүе"),
                            "estimated_minutes": 11,
                            "task": tr(
                                "Write your deployment note: where this workflow will be used, by whom, and how success is tracked.",
                                "Напишите заметку по внедрению: где используется этот процесс, кем и как измеряется успех.",
                                "Кертү искәрмәсе языгыз: бу эш агымы кайда кулланыла, кем куллана һәм уңыш ничек үлчәнә.",
                            ),
                            "submission": {
                                "type": "text",
                                "pass_score": 78,
                                "min_words": 40,
                                "required_markers": ["workflow", "success", "risk"],
                                "bonus_markers": ["owner", "cadence", "metric"],
                                "forbidden_phrases": ["no risks", "works for everything"],
                                "weak_area_tags": ["course-synthesis"],
                            },
                        },
                    ],
                },
            ],
        },
    ],
}
