from __future__ import annotations

import pytest

from app.modules.learning.content.production_systems import PRODUCTION_SYSTEMS_COURSE
from app.modules.learning.content.prompt_basics import PROMPT_BASICS_COURSE
from app.modules.learning.content.workflows import WORKFLOWS_COURSE


COURSE_FOUNDATIONS = "prompt-engineering-foundations"
COURSE_WORKFLOWS = "prompt-workflows-study-and-work"
COURSE_PRODUCTION = "production-prompt-systems"

UNIVERSAL_TEXT = """
[ROLE] Senior AI coach
[CONTEXT] This workflow supports study and work execution in a real project context.
[TASK] Build a clear brief, compare options, debug weak output, and refine results.
[CONSTRAINTS] Keep facts explicit, avoid vague wording, include risks and fallback.
[OUTPUT] Stage 1 brief, Stage 2 analysis table, Stage 3 action checklist.
[CHECK] score criterion metric 1-5 with threshold and confidence.
[EXAMPLE] changed because evidence improved; workflow success owner cadence metric risk fallback.
workflow success risk owner cadence metric threshold changed because Stage 1 Stage 2 Stage 3.
""".strip()

LOW_SIGNAL_TEXT = """
[ROLE] 14a 344 3 7 2423 1
[CONTEXT] 242 42a343 25554 7 555 22 4
[TASK] 326346363a46346 54 54 54 5445 4 54 54
[CONSTRAINTS] 2363 2572 a5757 427 88 11 22
[OUTPUT] 74754 a754 64564 54 4545 44 54 54 5445 4 54 54 a4 4 4 54 545
[CHECK] 63246 324623 4 63 246 2332 636 4a 64 4 4
""".strip()


def _auth_headers(token: str, language: str | None = None) -> dict[str, str]:
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    if language:
        headers["Accept-Language"] = language
    return headers


def _default_display_name(unique_email: str) -> str:
    local = unique_email.split("@", 1)[0]
    suffix = local[-8:] if len(local) >= 8 else local
    return f"Learning User {suffix}"


async def _register(async_client, unique_email: str, display_name: str | None = None) -> str:
    resolved_display_name = display_name or _default_display_name(unique_email)
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "password123", "display_name": resolved_display_name},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _choice_answer_for_step(step: dict) -> dict:
    quiz_questions = step.get("quiz_questions") or []
    if quiz_questions:
        choice_ids: dict[str, str] = {}
        for question in quiz_questions:
            question_id = question.get("id")
            if question_id == "trap_a":
                choice_ids[str(question_id)] = "a"
            elif question_id == "trap_c":
                choice_ids[str(question_id)] = "c"
            else:
                choice_ids[str(question_id)] = "b"
        return {"choice_ids": choice_ids}

    choices = step.get("choices", [])
    b = next((choice for choice in choices if choice.get("id") == "b"), None)
    choice_id = b["id"] if b else (choices[0]["id"] if choices else "")
    return {"choice_id": choice_id}


def _answer_for_step(step: dict) -> dict | None:
    submission_type = step.get("submission_type")
    if submission_type == "none":
        return None
    if submission_type == "choice":
        return _choice_answer_for_step(step)
    return {"text": UNIVERSAL_TEXT}


async def _submit_step(async_client, token: str, course_slug: str, lesson_slug: str, step: dict) -> dict:
    response = await async_client.post(
        f"/api/v1/learning/courses/{course_slug}/lessons/{lesson_slug}/steps/{step['slug']}/submit",
        headers=_auth_headers(token),
        json={"answer": _answer_for_step(step)},
    )
    assert response.status_code == 200
    payload = response.json()

    if not payload["passed"] and step.get("submission_type") == "text":
        retry_response = await async_client.post(
            f"/api/v1/learning/courses/{course_slug}/lessons/{lesson_slug}/steps/{step['slug']}/submit",
            headers=_auth_headers(token),
            json={
                "answer": {
                    "text": f"{UNIVERSAL_TEXT}\n{step.get('task') or ''}\n{step.get('title') or ''}",
                }
            },
        )
        assert retry_response.status_code == 200
        payload = retry_response.json()

    assert payload["passed"]
    return payload


async def _complete_lesson(async_client, token: str, course_slug: str, lesson_slug: str) -> list[dict]:
    lesson_response = await async_client.get(
        f"/api/v1/learning/courses/{course_slug}/lessons/{lesson_slug}",
        headers=_auth_headers(token),
    )
    assert lesson_response.status_code == 200
    lesson = lesson_response.json()

    outputs: list[dict] = []
    for step in lesson["steps"]:
        outputs.append(await _submit_step(async_client, token, course_slug, lesson_slug, step))
    return outputs


async def _complete_course(async_client, token: str, course_slug: str) -> list[dict]:
    course_response = await async_client.get(
        f"/api/v1/learning/courses/{course_slug}",
        headers=_auth_headers(token),
    )
    assert course_response.status_code == 200
    course = course_response.json()

    outputs: list[dict] = []
    for module in course["modules"]:
        for lesson in module["lessons"]:
            outputs.extend(await _complete_lesson(async_client, token, course_slug, lesson["slug"]))
    return outputs


@pytest.mark.asyncio
async def test_learning_start_target_without_auth_returns_catalog(async_client):
    response = await async_client.get("/api/v1/learning/start-target")
    assert response.status_code == 200
    payload = response.json()
    assert payload["target"] == "/learn"
    assert payload["has_active_course"] is False


@pytest.mark.asyncio
async def test_learning_start_target_active_redirect_and_resume(async_client, unique_email: str):
    token = await _register(async_client, unique_email)

    before = await async_client.get(
        "/api/v1/learning/start-target",
        headers=_auth_headers(token),
    )
    assert before.status_code == 200
    before_payload = before.json()
    assert before_payload["target"].endswith(
        "/learn/course/prompt-engineering-foundations/lesson/pe-foundations"
    )
    assert before_payload["has_active_course"] is False

    lesson_response = await async_client.get(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations",
        headers=_auth_headers(token),
    )
    assert lesson_response.status_code == 200
    first_step = lesson_response.json()["steps"][0]

    submit = await async_client.post(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations/steps/{first_step['slug']}/submit",
        headers=_auth_headers(token),
        json={"answer": _answer_for_step(first_step)},
    )
    assert submit.status_code == 200

    after = await async_client.get(
        "/api/v1/learning/start-target",
        headers=_auth_headers(token),
    )
    assert after.status_code == 200
    after_payload = after.json()
    assert after_payload["target"].endswith(
        "/learn/course/prompt-engineering-foundations/lesson/pe-foundations"
    )
    assert after_payload["has_active_course"] is True
    assert after_payload["active_course_slug"] == COURSE_FOUNDATIONS
    assert after_payload["target"] == after_payload.get("resume_href")


@pytest.mark.asyncio
async def test_learning_resume_moves_to_next_lesson_after_current_completed(async_client, unique_email: str):
    token = await _register(async_client, unique_email)

    await _complete_lesson(async_client, token, COURSE_FOUNDATIONS, "pe-foundations")

    start_target = await async_client.get(
        "/api/v1/learning/start-target",
        headers=_auth_headers(token),
    )
    assert start_target.status_code == 200
    payload = start_target.json()

    assert payload["target"].endswith("/lesson/pe-structure-pattern")
    assert payload["has_active_course"] is True
    assert payload["active_course_slug"] == COURSE_FOUNDATIONS
    assert payload["target"] == payload.get("resume_href")
    assert payload["resume_href"].endswith("/lesson/pe-structure-pattern")


@pytest.mark.asyncio
async def test_learning_step_validation_returns_meaningful_feedback(async_client, unique_email: str):
    token = await _register(async_client, unique_email)

    lesson_response = await async_client.get(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations",
        headers=_auth_headers(token),
    )
    assert lesson_response.status_code == 200
    theory_step = lesson_response.json()["steps"][0]
    theory_submit = await async_client.post(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations/steps/{theory_step['slug']}/submit",
        headers=_auth_headers(token),
        json={"answer": _answer_for_step(theory_step)},
    )
    assert theory_submit.status_code == 200

    fail_submit = await async_client.post(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations/steps/pe-foundations-guided/submit",
        headers=_auth_headers(token),
        json={"answer": {"text": "short"}},
    )
    assert fail_submit.status_code == 200
    payload = fail_submit.json()

    assert payload["passed"] is False
    assert payload["feedback"]["improvements"]
    assert payload["feedback"]["verdict"]
    assert payload["attempts"] >= 1


@pytest.mark.asyncio
async def test_learning_step_blocks_out_of_order_submission(async_client, unique_email: str):
    token = await _register(async_client, unique_email)

    submit = await async_client.post(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations/steps/pe-foundations-guided/submit",
        headers=_auth_headers(token),
        json={"answer": {"text": UNIVERSAL_TEXT}},
    )

    assert submit.status_code == 409


@pytest.mark.asyncio
async def test_learning_step_rejects_verbatim_template_copy(async_client, unique_email: str):
    token = await _register(async_client, unique_email)

    lesson_response = await async_client.get(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations",
        headers=_auth_headers(token),
    )
    assert lesson_response.status_code == 200
    theory_step = lesson_response.json()["steps"][0]
    theory_submit = await async_client.post(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations/steps/{theory_step['slug']}/submit",
        headers=_auth_headers(token),
        json={"answer": _answer_for_step(theory_step)},
    )
    assert theory_submit.status_code == 200
    guided_step = next(step for step in lesson_response.json()["steps"] if step["slug"] == "pe-foundations-guided")
    template_text = str(guided_step.get("placeholder") or "").strip()
    assert template_text

    submit = await async_client.post(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations/steps/{guided_step['slug']}/submit",
        headers=_auth_headers(token),
        json={"answer": {"text": template_text}},
    )
    assert submit.status_code == 200
    payload = submit.json()

    assert payload["passed"] is False
    assert payload["feedback"]["improvements"]
    assert payload["score"] < payload["feedback"]["pass_score"]


@pytest.mark.asyncio
async def test_learning_step_rejects_low_signal_marker_filler(async_client, unique_email: str):
    token = await _register(async_client, unique_email)

    lesson_response = await async_client.get(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations",
        headers=_auth_headers(token),
    )
    assert lesson_response.status_code == 200
    theory_step = lesson_response.json()["steps"][0]
    theory_submit = await async_client.post(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations/steps/{theory_step['slug']}/submit",
        headers=_auth_headers(token),
        json={"answer": _answer_for_step(theory_step)},
    )
    assert theory_submit.status_code == 200

    submit = await async_client.post(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations/steps/pe-foundations-guided/submit",
        headers=_auth_headers(token),
        json={"answer": {"text": LOW_SIGNAL_TEXT}},
    )
    assert submit.status_code == 200
    payload = submit.json()

    assert payload["passed"] is False
    assert any("конкрет" in item.lower() or "смыслов" in item.lower() or "шум" in item.lower() for item in payload["feedback"]["improvements"])


@pytest.mark.asyncio
async def test_learning_completion_rewards_and_my_modules_sorting(async_client, unique_email: str):
    token = await _register(async_client, unique_email)

    outputs_foundations = await _complete_course(async_client, token, COURSE_FOUNDATIONS)
    assert any(item["lesson_completed"] for item in outputs_foundations)
    assert any(item["course_completed"] for item in outputs_foundations)

    course_complete_event = next(item for item in outputs_foundations if item["course_completed"])
    assert course_complete_event["awarded_lmn"] > 0
    assert course_complete_event["awarded_badge"]
    assert course_complete_event["certificate_ready"] is True

    workflow_lesson_response = await async_client.get(
        f"/api/v1/learning/courses/{COURSE_WORKFLOWS}/lessons/wf-task-briefing",
        headers=_auth_headers(token),
    )
    assert workflow_lesson_response.status_code == 200
    first_workflow_step = next(
        step
        for step in workflow_lesson_response.json()["steps"]
        if step["slug"] == "wf-brief-theory"
    )

    workflow_submit = await async_client.post(
        f"/api/v1/learning/courses/{COURSE_WORKFLOWS}/lessons/wf-task-briefing/steps/{first_workflow_step['slug']}/submit",
        headers=_auth_headers(token),
        json={"answer": _answer_for_step(first_workflow_step)},
    )
    assert workflow_submit.status_code == 200

    my_modules = await async_client.get(
        "/api/v1/learning/my",
        headers=_auth_headers(token),
    )
    assert my_modules.status_code == 200
    my_payload = my_modules.json()

    assert my_payload["active_courses"]
    assert my_payload["active_courses"][0]["slug"] == COURSE_WORKFLOWS
    assert my_payload["completed_courses"]
    foundations = next(item for item in my_payload["completed_courses"] if item["slug"] == COURSE_FOUNDATIONS)
    assert foundations["progress_percent"] == 100
    assert foundations["certificate_ready"] is True


@pytest.mark.asyncio
async def test_learning_catalog_localization_en_ru_tt(async_client):
    en_response = await async_client.get("/api/v1/learning/courses", headers={"Accept-Language": "en"})
    ru_response = await async_client.get("/api/v1/learning/courses", headers={"Accept-Language": "ru"})
    tt_response = await async_client.get("/api/v1/learning/courses", headers={"Accept-Language": "tt"})

    assert en_response.status_code == 200
    assert ru_response.status_code == 200
    assert tt_response.status_code == 200

    en_title = en_response.json()["courses"][0]["title"]
    ru_title = ru_response.json()["courses"][0]["title"]
    tt_title = tt_response.json()["courses"][0]["title"]

    assert en_title
    assert ru_title
    assert tt_title
    assert en_title != ru_title
    assert tt_title != en_title


@pytest.mark.asyncio
async def test_learning_catalog_exposes_three_level_path(async_client):
    response = await async_client.get("/api/v1/learning/courses", headers={"Accept-Language": "en"})
    assert response.status_code == 200
    payload = response.json()

    slugs = [item["slug"] for item in payload["courses"]]
    assert COURSE_FOUNDATIONS in slugs
    assert COURSE_WORKFLOWS in slugs
    assert COURSE_PRODUCTION in slugs

    production = next(item for item in payload["courses"] if item["slug"] == COURSE_PRODUCTION)
    assert production["difficulty"] == "advanced"
    assert production["result_headline"]
    assert production["deliverable_preview"]


@pytest.mark.asyncio
async def test_learning_quizzes_expose_five_questions_per_step(async_client):
    for course in (PROMPT_BASICS_COURSE, WORKFLOWS_COURSE, PRODUCTION_SYSTEMS_COURSE):
        for module in course["modules"]:
            for lesson in module["lessons"]:
                for step in lesson["steps"]:
                    if step["kind"] != "quiz":
                        continue
                    assert len(step["submission"]["questions"]) == 5


@pytest.mark.asyncio
async def test_learning_quiz_follow_up_questions_use_distinct_prompts_and_choices(async_client):
    for course in (PROMPT_BASICS_COURSE, WORKFLOWS_COURSE, PRODUCTION_SYSTEMS_COURSE):
        for module in course["modules"]:
            for lesson in module["lessons"]:
                for step in lesson["steps"]:
                    if step["kind"] != "quiz":
                        continue

                    questions = step["submission"]["questions"]
                    for language in ("en", "ru", "tt"):
                        question_texts = [str(question["question"][language]) for question in questions]
                        assert len(set(question_texts)) == len(question_texts)

                        follow_up_choice_sets = [
                            tuple(str(choice["text"][language]) for choice in question["choices"])
                            for question in questions[1:]
                        ]
                        assert len(set(follow_up_choice_sets)) == len(follow_up_choice_sets)


@pytest.mark.asyncio
async def test_learning_course_and_lesson_include_context_metadata(async_client):
    course_response = await async_client.get(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}",
        headers={"Accept-Language": "en"},
    )
    assert course_response.status_code == 200
    course = course_response.json()

    assert course["result_headline"]
    assert course["prerequisites"]
    assert course["deliverables"]
    assert course["career_outcomes"]
    assert course["product_action"]["label"]
    assert course["product_action"]["href"]

    lesson_response = await async_client.get(
        f"/api/v1/learning/courses/{COURSE_FOUNDATIONS}/lessons/pe-foundations",
        headers={"Accept-Language": "en"},
    )
    assert lesson_response.status_code == 200
    lesson = lesson_response.json()

    assert lesson["objective"]
    assert lesson["deliverable"]
    assert lesson["scenario_title"]
    assert lesson["scenario_body"]
    assert lesson["debrief"]
    assert lesson["review_rubric"]
    assert lesson["common_mistakes"]


@pytest.mark.asyncio
async def test_lessons_localization_and_cache_is_language_aware(async_client):
    def title_for_slug(rows: list[dict], slug: str) -> str:
        item = next((entry for entry in rows if entry.get("slug") == slug), None)
        assert item is not None, f"Lesson {slug} should exist"
        return str(item["title"])

    en_first = await async_client.get("/api/v1/lessons", headers={"Accept-Language": "en"})
    ru = await async_client.get("/api/v1/lessons", headers={"Accept-Language": "ru"})
    en_second = await async_client.get("/api/v1/lessons", headers={"Accept-Language": "en"})

    assert en_first.status_code == 200
    assert ru.status_code == 200
    assert en_second.status_code == 200

    en_first_title = title_for_slug(en_first.json(), "pe-foundations")
    ru_title = title_for_slug(ru.json(), "pe-foundations")
    en_second_title = title_for_slug(en_second.json(), "pe-foundations")

    assert en_first_title == "What Makes a Prompt Work"
    assert ru_title == "Что делает промпт рабочим"
    assert en_second_title == "What Makes a Prompt Work"
