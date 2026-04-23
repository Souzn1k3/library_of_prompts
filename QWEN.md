# Qwen Coder Instructions

Do not overwrite the deployed bot with an older simplified version.

Required check before every commit:

```bash
python tools/check_prod_integrity.py
```

If this check fails, stop and fix the regression before committing.

Critical production features that must not be deleted:

- subscriptions and Telegram Stars payment flow in `routes.py` plus `bot_plans.py`;
- website integration and moderation flow through `website_api.py`;
- saved prompts database functions in `database.py`;
- Vosk voice recognition plus OpenAI STT fallback;
- language menu rendering without `get_text(..., lang=...)` conflicts;
- `.gitignore` protection for secrets, virtualenvs, models, backups, and temp voice files.

Use `master` or a feature branch for experiments. The server deploys from `production`.
