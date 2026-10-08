# Cycle 3 hold hang (2026-09-13 17:11)

Runtime owner cycle. **Do not map.** Cycle 3 sys `5351E024…` (16:45:29)
is the corpse. `insn_starts_at` / nop5+E8 skip **did not** stop
`hook_failed` or the host hang.

## Verdict

Same class as Cycle 1, tighter bound: identity idle after `load_ok` was
fine (~8 min). Hang started **during first** `stealth --file` on Relic
(fail-closed, **no** retry hammer). Event **41** 17:09:32, 6008 previous
unexpected **17:07:55**. Minidump empty (`CrashDumpEnabled=0`). ping now
**ud**. Cookie `load_ok_pending_alive` + newer boot = this map died.

## Timeline (boot 16:32:44)

| t | |
|---|---|
| 16:58:16 | one `Map-AfterZppu` Cycle 3 sys 1075200 |
| 16:58:19 | `load_ok` 32/32 `exit=7c` `elfst=46` hitch `inner=0` `npf=0` |
| 17:03–17:06 | identity idle, keyed ping **pong**, Relic none |
| 17:07:34 | Relic **20068** `0x7FF634300000` `-dev -nodbg -notrap` (not dead VA `0x7FF7BABB0000`) |
| ~17:07:34+ | `wait-hold`: slots=0, 39 E8_ok sites, query status=0 |
| | 23× `status=0` then `status=10` from RVA `0x3F5B04B` WW_family |
| | fail-closed: refuse retry after `arm va=` |
| 17:07:55 | 6008 unexpected shutdown (dump writer 0%) |
| 17:09:28 | LastBootUpTime |
| 17:09:32 | Event 41 |

Capture: `aoe4-hv/docs/_bsod/crash-20260913-170956` (HostPrep `-Boot`
stamp 170956). hitch copy last mtime **17:01:20** — idle only; no hitch
sample covering the hold NPF. Relic WER: none this iteration.

## Hold sites

`docs/_bsod/cycle3-wait-hold.log`. Unique pages 29. First `status=10`:
`va=0x7FF63825B04B` RVA `0x3F5B04B`. INT3-1FDC all 10. Cycle 3 hyp
(left-scan on nop5+E8) **falsified** for this WW cluster.

Mailbox ops 1–12 untouched. x64dbg not started. Nested-map not done.

## Gate

`launch_authorized=false` `status=new_bsod`. Event 41 **after**
`last_fix_time` 16:45:29 → dry-run **21**. Do **not** remap this ELF/sys.
Ping `ud` is not green.

## Next (not this turn)

New Cycle 4 hyp from APM/NPT execute-copy on WW pages (not remap Cycle 3).
Then user **запускай** after `last_fix_time` newer than 17:09:32.
`Test-VmrunDumpGate` ok. One map. Identity idle. Relic. One wait-hold.
No nested-map.
