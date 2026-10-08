# 2026-09-13 session `3305282e` crash + resume

Parent chat HV grind did **not**
die on a mapper hang. The 3032-line transcript ends
`turn_ended status=success` at **16:28** after handing
`C:\Program Files (x86)\rbhost` to grind subagent
`5d63478e-d163-4345-acc5-e8a093437d0d`. That child **did** crash:
last user turn is the rbhost path; no assistant reply after line 52.

Cause class: **agent abort / context overflow** on a 7-day mega-session
(Sep 6 → Sep 13), not a new HostPrep boot by itself. Nested-map and
Event 41 15:54 are earlier in the same chat. Do not treat this resume
as `запускай`.

## Original goal (last phase)

After Windows **26H2 26340.9482**: one SVM map, then Relic
`-dev -nodbg -notrap`, fail-closed `hold --apply`, Vs AI, **unhidden**
x64dbg from `rbhost` for 60 s. STEP 13: one hypothesis per cycle.
Parallel agent-context notes for other agents. No mailbox op 13.

## Progress when the grind died

| Step | Result |
|---|---|
| Cycle 1 C-bit window | **mapped** 16:21:43 `load_ok` sys **16:20:21 / 1075200 B** 32/32 `cpu_ok` `userdtb_off=0 peb=2e0` |
| Keyed ping | **pong** with gitignored `last-zpp-key.txt`; unkeyed ping still **ud** |
| `Get-HvPingToken` | Cycle 2: loads that key (do not print it) |
| Relic | PID **5012** image **`0x7FF7BABB0000`** SizeOfImage `0x8C3D000` slots=0 |
| `hold --apply` | **20 / 39** `stealth_arm` `status=0`, rest **`status=10` hook_failed**, then mailbox `rax=2` |
| x64dbg | not started. `Start-X64dbgHidden.ps1` already targets `C:\Program Files (x86)\rbhost\release\x64` |
| Cookie | `in_progress` this boot `2026-09-13T15:54:23` attempt 16:21:40 |

## This resume (no `kdu`)

- Deleted `_bsod/_cycle1-*.ps1` that inlined `ZPP_HYPERCALL_KEY`.
- Gitignore `docs/_bsod/_*.ps1` / `_*.out.txt`.
- ELF Cycle 3 (source only, **not mapped**): nop5 + `E8` skips
  `insn_starts_at` left-scan (`npt_stealth.cpp`).
- `zpp_at.py` already refuses a second `hold --apply` pass after any
  `arm va=` (partial apply + mailbox death).
- Do **not** nested-map. Do **not** start x64dbg until a future
  `hold --apply` is 39/39 and slots=0.

Related: [Cycle 1](2026-09-13-hv-cycle1-cbit-window.md),
[Cycle 3 hold insn](2026-09-13-hv-cycle3-hold-insn-boundary.md),
[HV preflight](2026-09-13-agent-context-hv-preflight.md).
