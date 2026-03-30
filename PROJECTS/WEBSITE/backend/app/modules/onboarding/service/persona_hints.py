ROLE_HINTS: dict[str, list[str]] = {
    "student": ["study", "exam", "summary", "explain"],
    "developer": ["debug", "code", "api", "refactor"],
    "other": ["planning", "email", "workflow", "research"],
}

GOAL_HINTS: dict[str, list[str]] = {
    "learning": ["learn", "tutorial", "practice"],
    "solving_tasks": ["solve", "task", "step-by-step", "analysis"],
    "productivity": ["productivity", "time", "organize", "checklist"],
}

CONTEXT_HINTS: dict[str, list[str]] = {
    "chatgpt": ["chat", "assistant"],
    "code_assistant": ["code", "debug", "test"],
    "school": ["study", "exam", "notes"],
    "work": ["email", "meeting", "planning"],
}


def collect_persona_hints(
    *,
    role: str | None,
    goal: str | None,
    context: str | None = None,
    extra_hints: list[str] | None = None,
) -> list[str]:
    hints = [
        *ROLE_HINTS.get(role or "", []),
        *GOAL_HINTS.get(goal or "", []),
        *CONTEXT_HINTS.get(context or "", []),
        *(extra_hints or []),
    ]
    return list(dict.fromkeys(hints))


def build_persona_hint_query(
    *,
    role: str | None,
    goal: str | None,
    context: str | None = None,
    extra_hints: list[str] | None = None,
) -> str | None:
    query = " ".join(
        collect_persona_hints(role=role, goal=goal, context=context, extra_hints=extra_hints)
    ).strip()
    return query or None
