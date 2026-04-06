# Scenario-First Product Architecture v2

## 1) Entry-point redesign
- Homepage is now an action-first control surface, not a passive catalog.
- Primary flow: search task -> preview live result -> run scenario.
- Secondary surfaces (retention/game/chain) exist only to continue execution momentum.

## 2) Scenario domain model

```ts
ScenarioDefinition {
  id, slug, title, summary,
  technique,
  category: utility | learning | productivity | entertainment | growth,
  facets[],
  qualityScore, saveCount, copyCount,
  access: {
    freePreviewEnabled,
    freeRunsPerDay,
    fullBlueprintRequiresPro,
    proCapabilities[]
  },
  retention: {
    replayReason,
    nextScenarioSlug,
    unfinishedActionHint
  }
}
```

## 3) Layered architecture
- Domain: `frontend/features/scenarios/domain/scenario.ts`
- Application: scenario runtime and explorer orchestration.
- Infrastructure: mapper from prompt payloads to scenario domain model.
- UI: homepage and scenario page consume scenario use-cases without embedding mapping/scoring internals.

## 4) UX model
1. User lands on homepage.
2. Sees live output immediately in hero stage.
3. Adds task context and reruns quickly.
4. Opens full scenario page.
5. Sees full output stage first (top 80-90% viewport).
6. Encounters natural Free -> Pro gate for blueprint/copy/deep customization.

## 5) Monetization model
- Free: result preview + limited demo runs.
- Pro: full blueprint visibility, customization, unlimited reruns, save/chain.
- Token loop: web game demo -> Telegram gameplay -> token spend in Store -> scenario unlock motivation.

## 6) Retention model
- Next-step scenario chains are visible on homepage.
- Progress panel shows quality and save signals.
- Unfinished actions are preserved through scenario CTA to workspace/dashboard.

## 7) Growth loops
- Core loop: discover -> run -> result -> next scenario -> return.
- Viral loop: shareable scenario outcomes and Telegram continuation.
- Conversion loop: preview value first, then paywall only after experienced utility.

## 8) Metrics contract
- Activation: first scenario run in session.
- Scenario-to-run rate.
- Demo-to-pro conversion.
- Repeat usage rate.
- Return frequency (D1/D7/D30).
- Token earn/spend ratio.
- Chain completion rate.

## 9) Risk controls
- Avoid over-paywalling first action.
- Ensure game does not replace core utility usage.
- Keep single dominant CTA in hero to reduce hesitation.
- Keep scenario mapping deterministic and testable.
