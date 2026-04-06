# Ultra-Hard Baseline Snapshot (2026-04-06)

## Stage 0 - Pre-change safety
- Required backup sequence executed:
  1) `git add .`
  2) `git commit -m "backup before ultra-hard product/system refactor"`
  3) `git push`
- Commit: `205ff56`

## Current state before this execution stage

### Homepage model (before this stage)
- Action-oriented hero existed but lacked explicit run/save/share/repeat orchestration.
- Workspace continuity (recent/saved/unfinished) was missing.
- Conversion tension existed but lacked engagement feedback loop from actual scenario events.

### Scenario model (before this stage)
- Scenario domain layer existed (`features/scenarios`) but entry flow was still mostly preview-oriented.
- Missing explicit execution contract at homepage interaction level.

### Monetization model (before this stage)
- Free/Pro gate copy existed.
- Scenario-level event tracking was not integrated into homepage run/copy actions.

### Retention model (before this stage)
- Game and chain blocks existed.
- No persistent unfinished/recent scenario workspace on entry point.

### Architecture model (before this stage)
- Scenario domain/application/infrastructure introduced.
- Homepage workbench still mixed orchestration + UI + engagement event concerns.

## Critical product-risk areas
1. Scenario usage looked interactive but lacked explicit execution-memory loop.
2. Save/return behavior was weak at first entry surface.
3. Run and copy actions were not consistently tied to economy events.

## Critical code-risk areas
1. Home workbench had high responsibility density.
2. Local continuity state for scenarios was absent.
3. Engagement tracking logic was not isolated into dedicated hooks.

## Unknowns to verify
1. Real-world conversion lift from run-first CTA vs open-first CTA.
2. Token reward salience impact on repeat usage.
3. Guest vs auth behavior on optional economy events.
