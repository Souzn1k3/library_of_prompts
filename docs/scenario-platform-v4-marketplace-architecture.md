# Scenario Platform V4: UGC + Marketplace + Network Effects

## 1. Архитектура платформы

### Backend
- `scenarios/studio`: создание, редактирование, публикация пользовательских сценариев.
- `scenarios/marketplace`: discovery (`trending/new/top/best/personalized`), remix/fork, social signals.
- `scenario_blueprint_versions`: version history на каждый edit/publish/remix.
- `scenario_blueprint_comments`, `scenario_blueprint_ratings`, `scenario_blueprint_saves`: social proof и feedback loop.
- lineage: `root_blueprint_id` + `forked_from_id`, API lineage tree.
- usage signals: run/completion tracking для ranking и quality score.

### Frontend
- `/studio`: no-code builder + DSL editor + runtime preview + publish/version/lineage panel.
- `/scenarios/marketplace`: discovery + search + category filter + interactive preview + social actions.
- unified scenario runtime (V3) используется как execution layer для preview/run.

## 2. Как работает creator flow

1. Creator собирает сценарий в no-code builder.
2. Синхронизирует/редактирует DSL.
3. Тестирует в interactive runtime preview.
4. Сохраняет draft в studio.
5. Публикует в marketplace (`private/public/premium` + monetization mode).
6. Получает usage, saves, comments, ratings, remix/fork.
7. Улучшает сценарий; каждая правка фиксируется в version history.

## 3. Как работает user flow

1. User заходит в marketplace discovery section.
2. Находит сценарий через search/category.
3. Открывает interactive preview и запускает сценарий.
4. Сохраняет, лайкает, комментирует, оценивает.
5. Делает fork/remix под свой кейс.
6. Возвращается, так как есть персонализированная лента + сохраненные сценарии + lineage.

## 4. Как устроен marketplace

- Discovery sections:
  - `trending`: growth rate на основе run/save/fork/comment/rating signals.
  - `new`: recency.
  - `top`: usage-dominant score.
  - `best`: quality score (completion + rating + saves).
  - `personalized`: приоритет категорий creator/user behavior.
- Scenario card:
  - author, tags, visibility/monetization, usage stats, rating, comments.
  - CTA: `run`, `save`, `fork`, `remix`, `like`, `rate`, `comment`.
  - interactive preview через runtime engine.

## 5. Как работает монетизация

- `monetization_mode`:
  - `free`
  - `pro_only`
  - `paid` (`token_price`)
- `visibility=premium` нормализуется в marketplace + pro/paid gating.
- Remix/Fork billing:
  - paid сценарии списывают tokens при remix/fork.
  - pro-only требует non-free plan.
- Creator rewards:
  - publish/fork/like reward events сохраняются и начисляются в wallet.

## 6. Как создаётся network effect

- **UGC supply loop**: больше creators -> больше сценариев -> больше use-cases.
- **Demand loop**: больше users запускают/сохраняют/оценивают -> лучше ranking quality.
- **Remix loop**: каждый remix создаёт lineage graph и новый publish candidate.
- **Monetization loop**: creators видят value от публикации и возвращаются улучшать.
- **Feedback loop**: comments + ratings + usage metrics дают сигнал, что улучшать в next version.

## Self-check (V4)

- Пользователи могут создавать сценарии: **да** (`/studio`, create/patch/publish).
- Есть причины публиковать: **да** (discovery exposure + creator rewards + monetization).
- Есть причины возвращаться: **да** (saved/remix/history/personalized discovery).
- Есть рост без ручного вмешательства: **да**, через UGC + remix + social signals + ranking.
