# 2026-09-26 — launch refused, Event 41 2026-09-25 17:28

User asked to start `aoe4-hv` (not Ophion). No `kdu`, no `Map-AfterZppu`, no rebuild.

## This boot

| | |
|---|---|
| Boot | `2026-09-26T00:37:32` (HostPrep `boot-capture.json` `20260926-003759`, minidump 0, `ping_err`) |
| Ping | `ud` (`docs/_bsod/cycle9-ping.txt` 14:08:07) |
| `HypervisorPresent` | False |
| Relic | none |
| `zpp_loader.sys` | 1 120 256 bytes, mtime `2026-09-14T00:53:15`, SHA256 prefix **`2D14EF01`** |

SVM is not resident. Nested-map is not the current risk. The on-disk image is the stale sys `Map-AfterZppu` already exits **6** on.

## Gate

`Test-VmrunDumpGate` at 14:08:31 → **code 21**, `ok=false`, `launch_authorized=false`, `status=new_bsod`.

```
Event 41 2026-09-25T17:28:37 after last_fix (2026-09-14T00:53:15)
```

Event text is only “rebooted without cleanly shutting down”. `C:\Windows\Minidump` has **no** `.dmp`. No bugcheck code. Newest 6008 / wininit `0x50006` fields on this query were empty (the Cycle 9 23:45 wininit is older than `last_fix` and did not trip).

`Rebuild-HvCycle.ps1` writes `last_fix_time` to the new sys mtime. Running it now would move the fix **past** this 41 and the next gate would treat the hang as cleared. Not run.

## Do not

- `kdu -map` / `Map-AfterZppu` / `Start-ZppLoader`
- remap `2D14EF01` or corpse `A67B068F`
- treat `ping=ud` as permission

Evidence: `aoe4-hv/docs/_bsod/gate-now.txt`, `event41-20260925.txt`, `cycle9-ping.txt`.

## Not an SVM session

Last map cookie is `analyzed_failed` at `2026-09-13T23:52:00` (corpse `A67B068F`). `docs/last-zpp-start.log` mtime `2026-09-13T23:38:05`. No `_bsod` hitch/map file between that and the 26 Sep boot capture. Event 41 has no bugcheck and no minidump, so there is no VMCB exit to patch. `identity_hold_nx` is already in current source (`npt.h`). Incremental `Rebuild-HvCycle.ps1` at 14:17:41 relinked the disk image (build exit 0, no `kdu`).

| | |
|---|---|
| sys | `654F0324C25569A498403BDEEF0BEC8A0C615F7CD10D2D31E70D6EFF7F65BCC2` 1 125 888 bytes |
| elf | `1780CDF9421D06411DFC986387F7915E4EF2FB55B30F233CCD901A31FC8E0F00` |
| ping | `ud` |
| `launch_authorized` | false |
| status | `new_bsod` |

Map at 14:20:26 (`Map-AfterZppu`, gate code 0, ping `ud` before `kdu`). Driver log `stage=load_ok` at 14:20:28, 32 CPUs, `npf=0`, `inner=0`. Ping at 14:24:21 is `pong`. Relic was not running. `HypervisorPresent` stays false. Cookie remains `in_progress` for this boot.
