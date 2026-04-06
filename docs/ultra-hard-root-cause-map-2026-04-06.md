# Root Cause Map (2026-04-06)

## 1) Product model problems

### ISSUE PM-1
- Symptom: scenario entry felt like live preview, not explicit execution loop.
- Root cause: no run contract with persisted user momentum.
- Business impact: weaker habit formation.
- UX impact: perceived progress resets every visit.
- Conversion impact: weaker upgrade urgency.
- Retention impact: lower return trigger density.
- Architecture impact: orchestration scattered.
- Severity: CRITICAL.

## 2) Homepage problems

### ISSUE HP-1
- Symptom: homepage had strong UI but missing workspace continuity.
- Root cause: no local scenario workspace model.
- Business impact: users re-discover from scratch.
- UX impact: friction after first interaction.
- Conversion impact: reduced second-action probability.
- Retention impact: weak unfinished-action loop.
- Architecture impact: no dedicated state boundary.
- Severity: HIGH.

### ISSUE HP-2
- Symptom: run/copy actions did not consistently produce visible economy feedback.
- Root cause: engagement events not wired from homepage.
- Business impact: token economy perceived as detached.
- UX impact: no immediate reward acknowledgment.
- Conversion impact: weaker free-to-paid tension.
- Retention impact: fewer reward-driven returns.
- Architecture impact: event wiring hidden in non-entry surfaces.
- Severity: HIGH.

## 3) AI-scenarios problems

### ISSUE SC-1
- Symptom: scenario output generation logic improved but execution telemetry was underused.
- Root cause: no dedicated engagement hook in home run path.
- Business impact: limited insight and reward loop activation.
- UX impact: low confidence that action is recorded.
- Conversion impact: less trust in scenario progression.
- Retention impact: weaker run-repeat behavior.
- Architecture impact: analytics/economy coupling not explicit.
- Severity: HIGH.

## 4) Monetization problems

### ISSUE MO-1
- Symptom: Pro gate existed, but action-to-value-to-upgrade sequence was incomplete.
- Root cause: missing run/save/share progression at hero level.
- Business impact: lower monetization leverage per session.
- UX impact: value narrative could feel static.
- Conversion impact: fewer natural upgrade triggers.
- Retention impact: reduced scenario reuse.
- Architecture impact: paywall messaging not paired with state transitions.
- Severity: HIGH.

## 5) Token economy problems

### ISSUE TK-1
- Symptom: users could not reliably feel token progress tied to scenario execution.
- Root cause: no homepage integration with prompt economy events.
- Business impact: token system underutilized.
- UX impact: reward ambiguity.
- Conversion impact: lower premium pressure.
- Retention impact: weaker loop closure.
- Architecture impact: economy logic isolated from core entry.
- Severity: HIGH.

## 6) Telegram game loop problems

### ISSUE TG-1
- Symptom: game loop existed but site-side continuity to scenario workbench was shallow.
- Root cause: no shared workspace continuation model on homepage.
- Business impact: lower cross-loop amplification.
- UX impact: context switching cost.
- Conversion impact: lower re-entry efficiency.
- Retention impact: diminished return quality.
- Architecture impact: disconnected state lifecycles.
- Severity: MEDIUM.

## 7) UX/interaction problems

### ISSUE UX-1
- Symptom: user could interact but not accumulate explicit progress artifacts.
- Root cause: no unfinished/recent/saved scenario persistence in entry experience.
- Business impact: lower lifetime usage depth.
- UX impact: weaker sense of control.
- Conversion impact: less reason to upgrade/save.
- Retention impact: lower completion loops.
- Architecture impact: interaction events lacked durable state sink.
- Severity: HIGH.

## 8) Architecture/code problems

### ISSUE AR-1
- Symptom: workbench component remained heavy after first refactor.
- Root cause: state orchestration and engagement concerns not fully separated.
- Business impact: slower feature velocity.
- UX impact: regression risk in iterations.
- Conversion impact: experimentation friction.
- Retention impact: slower loop improvements.
- Architecture impact: SRP pressure in entry module.
- Severity: HIGH.
