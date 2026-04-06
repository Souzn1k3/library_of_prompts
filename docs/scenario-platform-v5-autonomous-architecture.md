# Scenario Platform V5: Autonomous Product + Growth + Revenue System

## 1. Архитектура автономной системы

### AI orchestration layer
- `ScenarioAutonomyService` управляет полным циклом без человека.
- Scheduler (`scenario_autonomy_scheduler`) запускает циклы по интервалу.
- Цикл: `generate -> test -> measure -> deploy -> iterate -> personalize`.

### Decision engines
- `ScenarioGenerationEngine`: генерация новых сценариев из behavioral signals.
- `ExperimentOrchestrator`: авто A/B для сценариев, UI, pricing, paywall.
- `GrowthDecisionEngine`: автономные решения по каналам (scale/kill/adjust).

### Feedback + telemetry + control
- Все шаги пишутся в V5 таблицы:
  - `scenario_autonomy_cycles`
  - `scenario_autonomy_experiments`
  - `scenario_autonomy_growth_decisions`
  - `scenario_autonomy_guardrail_events`
  - `scenario_autonomy_personalization_profiles`
- Guardrails применяются автоматически, при нарушениях срабатывает rollback/retire.

## 2. Как AI генерирует сценарии

- Сигналы источников:
  - поисковые запросы (`catalog_search_used`)
  - failed runs (`scenario_run` со статусами failed/error/timeout/blocked)
  - популярные действия (`scenario_*`)
  - retention gaps (signup без возврата)
- AI формирует DSL-план, создает draft blueprint, размечает как autonomous.
- Сценарий проходит pipeline `draft -> experiment -> publish`.

## 3. Как работает auto-growth

- Engine считает channel-level метрики: CAC, ROI, retention, conversion.
- Автоматические действия:
  - `scale_channel` при сильном ROI + retention.
  - `kill_channel` при негативной экономике.
  - `adjust_budget` в пограничных случаях.
- Дополнительно:
  - `adjust_paywall` при низком interaction rate.
  - `adjust_pricing` при слабом checkout-rate после pricing selection.

## 4. Как работает auto-revenue

- Revenue decisions встроены в те же циклы экспериментов.
- Orchestrator тестирует pricing/paywall варианты как first-class эксперименты.
- Победившие варианты становятся активной рекомендацией для personalization-профилей.
- Экономические решения журналируются в decision log и телеметрии.

## 5. Как происходит self-improvement

- Каждый автономный сценарий получает:
  - `autonomous_quality_score`
  - `autonomous_stage` (`draft/test/published/retired/rolled_back`)
  - `autonomous_last_iteration_at`
- При достаточном uplift AI авто-итерирует DSL и публикует улучшенную версию.
- Слабые сценарии автоматически переводятся в `retired` и исключаются из выдачи.

## 6. Почему система масштабируется сама

- Генерация сценариев не зависит от ручного контента.
- Эксперименты и выбор winner идут автоматически по guardrails.
- Growth/revenue решения принимаются автономно и записываются как applied decisions.
- Персонализация (`autonomy/personalization`) дает каждому пользователю индивидуальный продуктовый слой.

## Self-check V5

- AI создает новые сценарии сам: **да**.
- AI тестирует сам: **да**.
- AI принимает решения сам: **да**.
- Продукт улучшается без человека: **да**, через авто-итерации, guardrails и scheduler loop.
