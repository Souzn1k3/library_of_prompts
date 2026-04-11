from __future__ import annotations

import re


def normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("\n", " ").split())


def word_count(value: str) -> int:
    return len([part for part in value.replace("\n", " ").split(" ") if part.strip()])


def tokenize(value: str) -> list[str]:
    return re.findall(r"[^\W_]+", value.lower(), flags=re.UNICODE)


def alpha_char_count(value: str) -> int:
    return sum(1 for char in value if char.isalpha())


def token_signal_stats(value: str) -> dict[str, float | int]:
    tokens = tokenize(value)
    token_count = len(tokens)
    if token_count == 0:
        return {
            "token_count": 0,
            "alpha_token_count": 0,
            "long_alpha_token_count": 0,
            "digit_token_count": 0,
            "alpha_ratio": 0.0,
            "long_alpha_ratio": 0.0,
            "digit_ratio": 0.0,
        }

    alpha_tokens = [token for token in tokens if any(char.isalpha() for char in token)]
    long_alpha_tokens = [token for token in alpha_tokens if alpha_char_count(token) >= 3]
    digit_tokens = [token for token in tokens if token.isdigit()]
    return {
        "token_count": token_count,
        "alpha_token_count": len(alpha_tokens),
        "long_alpha_token_count": len(long_alpha_tokens),
        "digit_token_count": len(digit_tokens),
        "alpha_ratio": len(alpha_tokens) / token_count,
        "long_alpha_ratio": len(long_alpha_tokens) / token_count,
        "digit_ratio": len(digit_tokens) / token_count,
    }


def extract_marker_payload(text: str, marker: str) -> str:
    pattern = re.compile(
        re.escape(marker) + r"\s*[:\-]?\s*(.*?)(?=\s*\[[A-Z_]+\]|\Z)",
        flags=re.IGNORECASE | re.DOTALL,
    )
    matched = pattern.search(text)
    if not matched:
        return ""
    return matched.group(1).strip()
