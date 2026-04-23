# Production Bot Guardrails

This repository contains the deployed Telegram bot. Do not replace the production code with an older local snapshot.

Before changing or deploying code, run:

```bash
python tools/check_prod_integrity.py
```

Rules for Qwen Coder, Codex, and any other coding agent:

1. Keep these production files: `bot_plans.py`, `website_api.py`, `utils/scheduler.py`, `routes.py`, `database.py`, `languages.py`, `prompts_souz_bot.py`.
2. Do not remove subscription, Stars payment, moderation, website API, saved prompts, Vosk STT, or OpenAI STT fallback logic.
3. Keep `get_text(locale, key, **kwargs)` with the first argument named `locale`. Do not rename it to `lang`.
4. Do not call `get_text(..., lang=...)` directly from `routes.py`; use another kwarg name or keep the language menu rendering helper.
5. Keep `.gitignore` patterns for `.env`, `.venv/`, `models/`, backup files, and temporary voice files.
6. AI model flags in `routes.py` and `languages.py` are intentional and must be preserved.
7. The deployed server should track the `production` branch. Experimental Qwen changes should be made in PRs or feature branches and merged only after the smoke guard passes.
