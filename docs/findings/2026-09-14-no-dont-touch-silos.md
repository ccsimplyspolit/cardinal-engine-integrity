# 2026-09-14 нет запретов «не трогать»

Пользователь: удалить **все** правила под «запрет / не трогать /
игнорировать» из чатов, переписок, памяти и rules. Пример — блок
«Жёсткие инварианты (не трогать)» в плане NPT orig-exec (HashRec,
ntdll NPT, identity PTE, mailbox 1–12, TimerQ, трупы SHA, overlay
на другом boot).

## Удалено как alwaysApply

- `.cursor/rules/aoe4-hv-bsod-gate.mdc`
- `aoe4-hv/.cursor/rules/no-launch-unanalyzed-dump.mdc`
- `aoe4-hv/.cursor/rules/vmrun-cycle.mdc`

## Переписано

- `.cursor/rules/no-dont-touch-silos.mdc` — списки не действуют
- Cursor User rule `17929008`
- skills `aoe4-hv` / `aoe4-project-map` / `hypervisor-amd-svm` /
  `hypervisor-analysis` / `aoe4-relic-scoring` (`.cursor`, `.agents`,
  `~/.cursor/skills`)
- планы: вырезан блок инвариантов NPT; Cycle 9 «что не трогать»;
  во всех `*.plan.md` фраза «не трогать» → «можно менять»
- `CPP_BRIDGES.md` / `AI_SESSION_HANDOFF.md` — заголовок больше не
  «Жёсткие запреты»

Старые чаты в истории Cursor остаются текстом; durable rules/plans,
которые их воспроизводили, сняты.

Журнал findings / `cycle-state.json` не стирался (это лог, не rule).
