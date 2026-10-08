# Cycle 1 — forced SME C-bit on copy-window PTE (2026-09-13)

Runtime owner cycle. Dump-gate fields kept. **One hypothesis only.**

## Cycle 1

| | |
|---|---|
| Hypothesis | DriverEntry hang after `copyphys_ok` is `zpp_copy_via_pte` forcing `sme_cbit` (bit 51) onto the reserved 4K window PTE during `copy_selftest`. TSME off. 15:07 `load_ok` planted PFN only. |
| Changed | Removed `pfn \|= sme_cbit` in `windows_loader/src/main.cpp`. Walks still strip C-bit via `pte_phys_4k`. No ELF/ABI/DTB/mailbox rewrite. |
| HV | map pending this write (ping was **ud**) |
| Mailbox | not reached |
| Relic session | none |
| Signatures | n/a |
| Vs AI | no |
| x64dbg open | no |
| 60 s | not reached |
| New dump | NO (Minidump empty; Temp Relic DMP if present is stale vs this iteration) |
| Root cause evidence | `zpp_loader-prev-20260913-155333.log` stops at `copyphys_ok` (alloc `FFFF93FA2F000000`). Next call is `zpp_copy_selftest` → `zpp_copy_via_pte` C-bit OR. hitch 15:07 (`FFFFA77D24400000`) reached `copyphys_self_ok` + `load_ok` `peb=2e0 dtb=28 name=338`. 15:51 sys 1074688 mapped 15:53 → Event 41 15:54:27. |
| Verdict | **map ok** — sys **16:20:21** 1075200 B SHA-256 `1CB50D1E64FF9A1C95D854A7454EE932235AF9AF4528940CC61D6786601437A8` mapped **16:21:43** `load_ok` 32/32 `cpu_ok` alloc `FFFFB3F8D2800000`. Keyed ping **pong**. Hypothesis held (no hang after `copyphys_ok`). |
| Next | Do **not** remap. Hold 20/39 is Cycle 3 (`insn_starts_at`), not a C-bit miss. |

## Preflight (16:19–16:20)

- Boot `2026-09-13T15:54:23`. HypervisorPresent=False. VBS not re-checked this line; prior 0.
- ping **ud** exit 2. Relic/steam/WW/x64dbg/kdu none.
- CrashControl **0 / AutoReboot=1**.
- Cookie `in_progress` boot 15:43 (dead map). Gate would be 21 until cookie `analyzed_failed` + `last_fix_time` > Event 41.
- aoe4-hv git **amd** `986b5da`.
- Relic Temp DMP: treat stale vs this iteration unless mtime ≥ 16:20.

## Do not

Nested KDU. `sc start Aoe4Hv`. Remap 15:51 sys. Mix VA across PIDs. Mailbox op 13.
