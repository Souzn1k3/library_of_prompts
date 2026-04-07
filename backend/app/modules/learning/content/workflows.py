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
                                    "Workflow quality is decided before generation: clear brief first, prompt text second.",
                                    "Качество workflow решается до генерации: сначала четкий бриф, потом текст промпта.",
                                    "Workflow сыйфаты генерациягә кадәр хәл ителә: башта төгәл бриф, аннары промпт тексты.",
                                ),
                                tr(
                                    "A strong brief captures objective, constraints, stakeholders, and acceptance criteria.",
                                    "Сильный бриф фиксирует цель, ограничения, роли участников и критерии приемки.",
                                    "Көчле бриф максатны, чикләүләрне, катнашучы рольләрне һәм кабул итү критерийларын терки.",
                                ),
                                tr(
                                    "If acceptance criteria are missing, teams confuse output volume with output quality.",
                                    "Если критериев приемки нет, команда путает объем ответа с его качеством.",
                                    "Кабул итү критерийлары булмаса, команда җавап күләмен сыйфат белән бутый.",
                                ),
                                tr(
                                    "Briefing also reduces rework: hidden assumptions become explicit before execution.",
                                    "Брифинг снижает переделки: скрытые предположения становятся явными до запуска.",
                                    "Брифинг кабат эшне киметә: яшерен фаразлар эшләтү алдыннан ук ачыклана.",
                                ),
                                tr(
                                    "Operational rule: if another teammate cannot run your brief, it is still under-specified.",
                                    "Операционное правило: если другой участник команды не может запустить ваш бриф, он недоспецифицирован.",
                                    "Операцион кагыйдә: башка команда әгъзасы сезнең бриф белән эшли алмаса, ул әле җитәрлек төгәл түгел.",
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
                                    "Research workflows prevent hallucination drift by splitting work into explicit stages.",
                                    "Research-workflow защищает от дрейфа в галлюцинации за счет явных этапов.",
                                    "Research-workflow ачык этаплар ярдәмендә галлюцинация дрейфын киметә.",
                                ),
                                tr(
                                    "Core sequence: collect evidence, compare claims, mark uncertainty, then synthesize.",
                                    "Базовая последовательность: собрать evidence, сравнить claims, отметить неопределенность, затем синтезировать.",
                                    "Төп эзлеклелек: evidence җыю, claims чагыштыру, билгесезлекне билгеләү, аннары синтез.",
                                ),
                                tr(
                                    "Without uncertainty flags, confident-sounding answers can still be wrong.",
                                    "Без флагов неопределенности даже уверенный ответ может быть неверным.",
                                    "Билгесезлек флаглары булмаса, ышанычлы яңгыраган җавап та ялгыш булырга мөмкин.",
                                ),
                                tr(
                                    "Good synthesis preserves traceability: every key claim points to supporting evidence.",
                                    "Хороший синтез сохраняет прослеживаемость: каждый ключевой тезис связан с evidence.",
                                    "Яхшы синтез эзлеклелекне саклый: һәр төп фикер evidence белән бәйләнгән.",
                                ),
                                tr(
                                    "The output should separate known facts, assumptions, and open questions.",
                                    "В выходе нужно разделять подтвержденные факты, предположения и открытые вопросы.",
                                    "Нәтиҗәдә расланган фактлар, фаразлар һәм ачык сораулар аерым күрсәтелергә тиеш.",
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
                                    "Strong writing workflows separate thinking modes: planner, writer, and editor should not be collapsed into one step.",
                                    "Сильный writing-workflow разделяет режимы мышления: planner, writer и editor не стоит смешивать в один шаг.",
                                    "Көчле writing-workflow фикерләү режимнарын аера: planner, writer һәм editor бер адымга кушылмаска тиеш.",
                                ),
                                tr(
                                    "Planner defines structure and audience, writer produces draft, editor checks logic, clarity, and factual risk.",
                                    "Planner задает структуру и аудиторию, writer создает черновик, editor проверяет логику, ясность и фактические риски.",
                                    "Planner структура һәм аудиторияне билгели, writer каралама яза, editor логиканы, ачыклыкны һәм факт рисгын тикшерә.",
                                ),
                                tr(
                                    "When these roles are merged, output often sounds fluent but misses intent and precision.",
                                    "Когда роли смешаны, текст часто звучит гладко, но теряет намерение и точность.",
                                    "Рольләр кушылса, текст шома күренә, ләкин ниятне һәм төгәллекне югалта.",
                                ),
                                tr(
                                    "A good workflow includes checkpoints: objective fit, evidence support, and readability for target audience.",
                                    "Хороший workflow включает контрольные точки: соответствие цели, опора на evidence и читаемость для целевой аудитории.",
                                    "Яхшы workflow контроль нокталарын кертә: максатка туры килү, evidenceка таяну һәм аудитория өчен укылу җиңеллеге.",
                                ),
                                tr(
                                    "This is how writing becomes reproducible instead of depending on mood or inspiration.",
                                    "Так текст становится воспроизводимым, а не зависящим от настроения или вдохновения.",
                                    "Шулай итеп язу кәефкә яки илһамга түгел, кабатлана торган процесска әйләнә.",
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
                                    "Analysis workflows are for decisions, so they must expose options, criteria, and trade-offs explicitly.",
                                    "Аналитические workflow нужны для решений, поэтому должны явно показывать варианты, критерии и компромиссы.",
                                    "Анализ workflow карар өчен кирәк, шуңа вариантлар, критерийлар һәм компромисслар ачык күрсәтелергә тиеш.",
                                ),
                                tr(
                                    "A useful analysis output compares alternatives under the same criteria, not separate free-form paragraphs.",
                                    "Полезный аналитический выход сравнивает альтернативы по одним и тем же критериям, а не в разных свободных абзацах.",
                                    "Файдалы анализ нәтиҗәсе альтернативаларны бер үк критерийлар буенча чагыштыра, ирекле аерым абзацларда түгел.",
                                ),
                                tr(
                                    "Include confidence and downside risk, otherwise recommendations look precise but are fragile in practice.",
                                    "Добавляйте уверенность и downside-риск, иначе рекомендации выглядят точными, но разваливаются в реальной работе.",
                                    "Ышаныч дәрәҗәсе һәм downside риск кертегез, югыйсә тәкъдим төгәл күренә, әмма практикада какшый.",
                                ),
                                tr(
                                    "Decision-ready prompts should always include the reason not to choose each option.",
                                    "Решение-ready промпт обязан содержать причину, почему каждый вариант можно не выбирать.",
                                    "Карарга әзер промпт һәр вариантны нигә сайламаска мөмкин икәнен дә күрсәтергә тиеш.",
                                ),
                                tr(
                                    "This creates better judgment: the learner sees trade-offs, not only a final answer.",
                                    "Так формируется зрелое мышление: ученик видит компромиссы, а не только финальный ответ.",
                                    "Бу җитлеккән фикерләү бирә: укучы финал җавапны гына түгел, компромиссларны да күрә.",
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
                                    "Debugging workflows convert frustration into method: label failure, isolate cause, test one repair.",
                                    "Workflow отладки превращает фрустрацию в метод: маркировка сбоя, изоляция причины, тест одной правки.",
                                    "Төзәтү workflow фрустрацияне ысулга әйләндерә: хатаны тамгалау, сәбәпне аеру, бер төзәтмәне тестлау.",
                                ),
                                tr(
                                    "Start with failure labels such as vague, off-target, shallow, unsafe, or structurally incomplete.",
                                    "Начинайте с ярлыков сбоя: размыто, мимо задачи, поверхностно, небезопасно, структурно неполно.",
                                    "Хата ярлыкларыннан башлагыз: томан, максаттан чит, өстән-өстән, куркыныч, структура җитми.",
                                ),
                                tr(
                                    "Then map each label to likely prompt blocks: context gaps, weak constraints, unclear output, or missing checks.",
                                    "Затем свяжите ярлык с вероятным блоком промпта: пробелы контекста, слабые ограничения, неясный output или отсутствие проверок.",
                                    "Аннары ярлыкны ихтимал блок белән бәйләгез: контекст җитмәве, йомшак чикләү, томан output яки тикшерү юклыгы.",
                                ),
                                tr(
                                    "Repair quality improves when you change one block and compare before/after evidence.",
                                    "Качество правки растет, когда вы меняете один блок и сравниваете evidence «до/после».",
                                    "Сыйфат төзәлеше бер блокны үзгәртеп «до/после» evidence чагыштырганда арта.",
                                ),
                                tr(
                                    "This is the bridge from trial-and-error to disciplined improvement loops.",
                                    "Это переход от случайных проб к дисциплинированному циклу улучшений.",
                                    "Бу очраклы сынаудан дисциплиналы яхшырту циклына күчеш.",
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
                                    "Capstone standard: package your workflow so another teammate can run it tomorrow without your help.",
                                    "Стандарт капстоуна: оформите workflow так, чтобы завтра его мог запустить другой участник команды без вашей помощи.",
                                    "Капстоун стандарты: workflowны иртәгә башка команда әгъзасы сезнең ярдәмсез үк эшләтә алырлык итеп җыегыз.",
                                ),
                                tr(
                                    "A production-like package includes stage boundaries, checks, fallback actions, and ownership notes.",
                                    "Пакет уровня production включает границы этапов, проверки, fallback-действия и заметки по ownership.",
                                    "Production дәрәҗәсенә якын пакет этап чиген, тикшерүләрне, fallback гамәлләрен һәм ownership язмаларын кертә.",
                                ),
                                tr(
                                    "Your goal is transferability: the workflow should survive handoff and context switching.",
                                    "Цель - переносимость: workflow должен переживать handoff и переключение контекста.",
                                    "Максат - күчерелеш: workflow handoff һәм контекст алышынуны узарга тиеш.",
                                ),
                                tr(
                                    "Final quality is proven by measurable checks and clear failure recovery, not by elegant wording.",
                                    "Финальное качество доказывается измеримыми проверками и ясным восстановлением после сбоев, а не красивой формулировкой.",
                                    "Финал сыйфат матур формулировка белән түгел, ә үлчәнә торган тикшерү һәм ачык recovery белән дәлилләнә.",
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
