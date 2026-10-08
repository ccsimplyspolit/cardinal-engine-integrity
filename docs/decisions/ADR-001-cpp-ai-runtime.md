# ADR-001: C++ owns AI think, SCAR only actuates

## Status

Accepted

## Date

2026-09-05

## Context

Software counterpick and eco scoring lived in Lua (`__EcoCounter_Tick`,
`AOE4HOOK_AI_PLAN` as a data bus). `ScarDoString` is serialized, measured in
tens of milliseconds, and ran on a 10 s tick from Present. Relic production
scoring is a separate multiply-list of `AIProductionScoring_*` factories; it is
not `PushScore` and not personality. Lua `LuaScoringFunction` callbacks run per
candidate and cannot do world scans.

## Options considered

### A. Keep thinking in Lua
- Pros: matches Relic script style; easy to tweak in Documents
- Cons: Present hitches; duplicate 10 s plan bus; cannot use worker threads;
  multiply-zero bugs stay opaque

### B. Replace Relic director with a fully custom C++ trainer
- Pros: full control
- Cons: needs proven native entrypoints, game-thread, lifetime; OOS vs humans;
  version-brittle

### C. C++ snapshot → parallel-safe math → thin SCAR availability (chosen)
- Pros: Relic still trains; overlay explains cuts; workers never call natives;
  hysteresis stays; hash/generation skip
- Cons: Relic utility and C++ rank can diverge until `GetSquadPBGProductionUtility`
  is probed live

## Decision

C++ owns sampling, role, floor, eco-lock, and production ranking on the collect
worker (`AiRuntimeOnPlanPublished`, ~2 s when armed). Present **only**
`PostMessage(WM_SCAR_AI_COMMIT)` (`scar.h`, `WM_APP+0x5346`). The Relic window
thread (`HandleAiCommitPosted`) installs `__EcoAct_*` once and applies a
hashed, latest-wins lean script if the generation is dirty.

Relic `ScoringFunctions_*` stay the trainer. Overlay overrides only the eco
hooks whose native gather scorer evaluates to 0 (`kEcoScoring`). Fine-tune
(`PushScore` / desire / gatherer / intentions) and `AI_SetPersonality` are
different layers — C++ hashed `__EcoAct` yields each Fine-tune Apply toggle.
See [AI_SCORING_PIPELINE.md](../AI_SCORING_PIPELINE.md).

Do **not** `SendMessage` / `ScarExecuteOnWindowThread` AI cuts from DXGI
Present (same FPS trap as the old per-frame `eco_ai_counter_flags`).

## Consequences

- `ai_counter_math.h` is the host-testable core (no Windows, no Lua).
- `ai_runtime.cpp` coordinates hysteresis (35 s) + actuator generation.
- `ai_production.cpp` is the observatory, not a second trainer.
  `UnitProfilePickTrain` is the overlay tier resolver.
- Engine natives stay on the Relic window thread (`FpsSec::AiCommit`).
- Session does not re-DoString `AOE4HOOK_AI_PLAN` while the runtime is armed.
  Radar world-feed may still publish the plan for SWM.
- Lua `__EcoCounter_Tick` is dead. Payload = generation + cut flags.
- FPS acceptance is `FpsProfileGetPresentPercentiles` (p95/p99/max/1% low),
  not average FPS alone.
- Queue state, Relic `CounterScore`, and `HasProductionQueue` stay Relic.
  Overlay counter is still role-bucketed until exact-unit snapshot lands.
