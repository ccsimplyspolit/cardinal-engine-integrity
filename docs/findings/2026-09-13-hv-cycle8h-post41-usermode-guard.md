# Cycle 8h: post-41 usermode leftover-clear guard (2026-09-13)

**STOP. Do not map.** ping **ud**. Event **41** `22:07:45`. sys still **`17E25811`**.
Goal not complete. Overlay forbidden. No TimerQ arm. No inject / Patch Game / stock x64dbg.

## Point

Usermode only. `zpp_aoe4` leftover `--cr3` is Toolhelp-refused while Relic lives
(fail-closed if Toolhelp fails). The 22:09 binary had a source-level refuse that
still queried the mailbox first; mailbox fail fell through and sent leftover CR3
-- that is the 22:03 live-disarm path (sites 2->0 on PID **3832**). Rebuilt
`out/debug/x86_64/zpp_aoe4.exe` **2026-09-13T22:32:18** SHA256 prefix `82198C70`.
Mailbox ops **1-12 unchanged**. ELF/sys **not** rebuilt (remap of `17E25811` forbidden).

Hitch-after-hold / HashRec hit counter would need a new ELF/sys and a remap.
They do not stop live leftover-clear + rearm. Skipped this session.

## Built

| Artifact | Value |
|---|---|
| `zpp_aoe4.exe` | 197632 B, mtime **2026-09-13T22:32:18**, SHA256 `82198C705B102715...` |
| strings | `REFUSE leftover --cr3`, `Toolhelp failed`, `named_live=` |
| `zpp_loader.sys` | still **17E25811** 1094656 B 21:12:19 (not mapped this turn) |
| ELF | still **E97A9C6E** 1044872 B 21:12:18 |
| `auto_run` | **0** (`Documents\AOE4HSettings\Config\config.ini`) |
| `last_fix_time` | **zpp_aoe4 mtime** 22:32:18 (not sys 21:12:19) |
| `launch_authorized` | **false** (no new sys AND gate) |

`last_fix` newer than Event 41 does **not** authorize map: sys SHA is still
the 22:07 corpse. Gate should drop Event-41/21 to **20** (`launch_authorized=false`).
Do not treat gate 20 or even 0 as permission.

## Scripts

- `Cycle8h-ClearLeftoverCr3.ps1` already refused Relic-live (exit 6)
- `Cycle8h-Evidence2.ps1` now skips leftover `--clear --cr3` while Relic lives
- `zpp_at.py` hold footer: leftover `--cr3` only after Relic is gone

## Not done (goal stays open)

1. New sys SHA **not** `17E25811` + user map ritual (this session = **fix only**)
2. Stock `x64dbg.exe` Attach on a living hold with `slots=0`
3. Dual-nCR3 PTE / NPF after hold / HashRec hits (ops 1-12 frozen; no op 13)
4. Leftover NX restore proof (`status=8` = not_found, not restored)
5. Host survives Overlay RUN / AUTO (8g and 8h both 41)
6. TimerQ waiver only -- do not arm `0x3E672DC`

## Do not

- remap `17E25811` / `E97A9C6E` / nested-map / `kdu`
- inject / Overlay RUN / `--patch-game` / AUTO
- arm TimerQ / leftover `--cr3` while Relic lives
- `UpdateGoal complete`
- treat `last_fix` > 22:07:45 as map permission

Related: [RUN then 41](2026-09-13-hv-cycle8h-run-then-41.md),
[leftover NX status=8](2026-09-13-hv-cycle8h-leftover-nx-status8.md),
[goal not complete](2026-09-13-hv-goal-not-complete.md),
[dual-nCR3 gap](2026-09-13-hv-cycle8h-dual-ncr3-gap.md).
