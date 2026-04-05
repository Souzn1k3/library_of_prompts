from __future__ import annotations

import re


def normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("\n", " ").split())


def word_count(value: str) -> int:
    return len([part for part in value.replace("\n", " ").split(" ") if part.strip()])


def tokenize(value: str) -> list[str]:
    return re.findall(r"[a-zа-яё0-9]+", value.lower(), flags=re.IGNORECASE)


def extract_marker_payload(text: str, marker: str) -> str:
    pattern = re.compile(
        re.escape(marker) + r"\s*[:\-]?\s*(.*?)(?=\s*\[[A-Z_]+\]|\Z)",
        flags=re.IGNORECASE | re.DOTALL,
    )
    matched = pattern.search(text)
    if not matched:
        return ""
    return matched.group(1).strip()
