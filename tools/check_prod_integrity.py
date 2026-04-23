from __future__ import annotations

import ast
import py_compile
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    ".gitignore",
    "requirements.txt",
    "prompts_souz_bot.py",
    "routes.py",
    "database.py",
    "languages.py",
    "bot_plans.py",
    "website_api.py",
    "utils/scheduler.py",
]

REQUIRED_TOP_LEVEL_SYMBOLS = {
    "routes.py": {
        "classes": {
            "AIChatState",
            "PromptReviewState",
            "ModerationCommentState",
        },
        "functions": {
            "_parse_admin_telegram_ids",
            "sync_subscription_cache",
            "build_tariffs_text",
            "get_tariffs_menu_inline",
            "get_tariff_checkout_inline",
            "apply_subscription_snapshot",
            "start_ai_session",
            "process_pre_checkout_query",
            "handle_successful_payment",
            "tariff_buy",
            "notify_admins",
            "moderation_panel",
            "moderation_approve",
            "moderation_reject_reason",
            "process_prompt_review_voice",
            "_get_vosk_model",
            "_transcribe_voice_with_vosk",
            "_transcribe_voice_with_openai",
            "transcribe_voice_to_text",
            "render_language_menu",
            "clean_markdown",
            "handle_ai_message",
        },
    },
    "database.py": {
        "classes": set(),
        "functions": {
            "update_user_plan",
            "get_user_plan",
            "grant_game_reward",
            "count_ai_messages_today",
            "get_saved_prompts",
            "save_prompt_for_user",
            "remove_saved_prompt_for_user",
            "update_user_coins",
            "get_top_best_users",
        },
    },
    "languages.py": {
        "classes": set(),
        "functions": {"get_text"},
    },
}

REQUIRED_IMPORTS = {
    "routes.py": {"bot_plans", "website_api"},
    "database.py": {"bot_plans", "website_api"},
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def parse_file(relative_path: str) -> ast.Module:
    path = ROOT / relative_path
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        fail(f"{relative_path} has syntax error: {exc}")


def top_level_symbols(tree: ast.Module) -> tuple[set[str], set[str]]:
    classes: set[str] = set()
    functions: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.add(node.name)
    return classes, functions


def imported_modules(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".", 1)[0])
    return modules


def check_required_files() -> None:
    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).is_file():
            fail(f"required production file is missing: {relative_path}")


def check_compiles() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        for relative_path in REQUIRED_FILES:
            if relative_path.endswith(".py"):
                target = tmp_root / (relative_path.replace("/", "_") + "c")
                py_compile.compile(str(ROOT / relative_path), cfile=str(target), doraise=True)


def check_symbols() -> None:
    for relative_path, required in REQUIRED_TOP_LEVEL_SYMBOLS.items():
        tree = parse_file(relative_path)
        classes, functions = top_level_symbols(tree)
        missing_classes = sorted(required["classes"] - classes)
        missing_functions = sorted(required["functions"] - functions)
        if missing_classes:
            fail(f"{relative_path} is missing classes: {', '.join(missing_classes)}")
        if missing_functions:
            fail(f"{relative_path} is missing functions: {', '.join(missing_functions)}")


def check_imports() -> None:
    for relative_path, required_modules in REQUIRED_IMPORTS.items():
        tree = parse_file(relative_path)
        modules = imported_modules(tree)
        missing = sorted(required_modules - modules)
        if missing:
            fail(f"{relative_path} no longer imports: {', '.join(missing)}")


def check_language_contract() -> None:
    tree = parse_file("languages.py")
    get_text = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "get_text"
        ),
        None,
    )
    if get_text is None:
        fail("languages.py is missing get_text")
    if not get_text.args.args or get_text.args.args[0].arg != "locale":
        fail("get_text first argument must stay named 'locale' to avoid lang= conflicts")

    routes_tree = parse_file("routes.py")
    for node in ast.walk(routes_tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "get_text":
            if any(keyword.arg == "lang" for keyword in node.keywords):
                fail("routes.py must not call get_text(..., lang=...), use another kwarg name")


def check_requirements_and_gitignore() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for package in ("aiohttp", "vosk"):
        if package not in requirements:
            fail(f"requirements.txt must include {package}")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".env", ".venv/", "models/", "*.bak_*", "*.last_uploaded_check"):
        if pattern not in gitignore:
            fail(f".gitignore must keep pattern: {pattern}")


def check_qwen_flags() -> None:
    routes = (ROOT / "routes.py").read_text(encoding="utf-8")
    languages = (ROOT / "languages.py").read_text(encoding="utf-8")
    for flag in ("🇫🇷", "🇨🇳", "🇺🇸"):
        if flag not in routes or flag not in languages:
            fail(f"AI model flag {flag} must be preserved")


def main() -> int:
    check_required_files()
    check_compiles()
    check_symbols()
    check_imports()
    check_language_contract()
    check_requirements_and_gitignore()
    check_qwen_flags()
    print("Production integrity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
