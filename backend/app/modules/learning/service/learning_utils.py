from __future__ import annotations


def safe_percent(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, round((done / total) * 100)))


def first_incomplete_step_slug(steps: list[dict], completed_step_slugs: set[str]) -> str | None:
    for step in steps:
        if step["slug"] not in completed_step_slugs:
            return step["slug"]
    return None
