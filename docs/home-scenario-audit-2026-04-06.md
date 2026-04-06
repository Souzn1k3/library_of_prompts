# Home + Scenario Audit (2026-04-06)

## Critical findings

1. **SRP violation** in `frontend/app/HomeActionWorkbench.tsx` (pre-refactor)
- Search, filtering, scoring, scenario output generation, paywall messaging, and copy mechanics were coupled in one large component.
- Impact: hard to scale scenario UX and hard to test.

2. **Domain leakage** in home UI (pre-refactor)
- Prompt-centric fields and behavior were directly used by UI without scenario abstraction.
- Impact: blocked transition from "prompt catalog" to "scenario engine".

3. **Competing CTA surfaces** on homepage
- Multiple sections pushed users to different places (catalog, paths, shelf).
- Impact: hesitation and reduced first-click clarity.

4. **Runtime duplication** between homepage and prompt page
- Live output simulation logic lived in multiple files.
- Impact: inconsistency and duplicated maintenance.

## Refactor actions

- Introduced scenario domain/application/infrastructure layers:
  - `frontend/features/scenarios/domain/scenario.ts`
  - `frontend/features/scenarios/application/scenarioExplorer.ts`
  - `frontend/features/scenarios/application/scenarioRuntime.ts`
  - `frontend/features/scenarios/infrastructure/promptScenarioMapper.ts`
- Rewrote homepage entry workbench around one primary flow.
- Rewrote scenario section with chain + retention + game-to-token-to-store loop.
- Removed shelf/path sections from homepage composition.
- Unified live-result generation via shared scenario runtime.

## Remaining constraints
- Backend API is still prompt-native; scenario API contracts should be extracted in a future backend phase.
- TT localization for new keys currently falls back to RU defaults.
