# Stock x64dbg Attach refused (2026-09-13 22:17)

User asked for the product gap: **stock `x64dbg.exe` (no hide) + Attach**.
**Refused.** Gate red. No Attach, no `kdu`, no map, no remap `17E25811`.

Stock dbg without a living HV hold is DualFlag / sibling pack. Dead PID
**3832** is not a hold target.

## Live gate (elevated `Attach-GateCheck.ps1` 22:17:07)

| Check | Value |
|---|---|
| `LastBootUpTime` | **2026-09-13T22:07:40** (same boot as cycle-state) |
| Event **41** | **2026-09-13T22:07:45** (newest; this boot) |
| 6008 | 22:07:52, previous shutdown **22:06:08** |
| ping | **ud** (keyed `zpp_ctl.py`; `HypervisorPresent=False`) |
| RelicCardinal | **0** (3832 died with the host) |
| x64dbg / rbhost | **0** |
| Window slots | **n/a** (no Relic) |
| Minidump | empty (`CrashDumpEnabled=0`) |
| gate | **21** cookie `analyzed_failed` / prior `load_ok_pending_alive` attempt_boot `21:05:57` |
| map corpse | `17E25811` 1094656 B 21:12:19 |

Captures already on this boot: HostPrep `crash-20260913-220808` (ping_err),
full `crash-20260913-221025` (ping **ud**, Relic none). Cookie
`map-attempt.json` `analyzed_failed` 22:13:40. `ping-now.txt` stamp
**21:22:04 pong** is stale (pre-41).

## Why Attach is forbidden

Product Attach is only after: idle map `hv_ping=pong` → titled Relic
`slots=0` → `wait-hold` (NPT ret Enqueue / KickCtor; TimerQ skip) →
optional overlay AUTO → stock `x64dbg.exe` and WindowWatch still
`slots=0`.

This boot has **none** of that:

1. New Kernel-Power **41** on this `LastBootUpTime` (SVM `17E25811` died).
2. ping **≠ pong** (`ud`). No mailbox, no NPT stub, no hasher HashRec.
3. Relic **none**. Last session **3832** `image=0x7FF7B6EE0000`
   CR3 `0x55ABF3000` (RVA space 16.3.11308.0). Do not hold that PID.

Leaf `AOE4HOOK/rbhost/release/_src/x64dbg.exe` on a living Relic without
hold packs sibling / DualFlag. `debug_attach_pid` without hold killed
41064. Hidden `Start-X64dbgHidden.ps1` / `bwfwcu` is not this step.

## Last dead session (not live)

| | |
|---|---|
| PID | **3832** (gone; Event 41) |
| Relic base | `0x7FF7B6EE0000` |
| CR3 | `0x55ABF3000` |
| SizeOfImage | `0x8C3D000` |
| cause | Overlay RUN 22:03:48 + leftover `--clear` + rearm `sites=3` 22:05:57 → hang 22:06:08 |

Also dead (do not hold): 15720 / 10324 / 19956 / 6732 / 1292 / 16544 /
34288 / 32172 / 36888 / 20068 / 5012 / 3088 / 36364 / 3256.

## Do not

- Attach stock or hidden x64dbg this boot
- `kdu -map` / `Map-AfterZppu` / remap `17E25811`
- leftover `--clear` while Relic live
- `DllInjector` / `--patch-game` / Overlay RUN
- WPM Relic `.text` / arm TimerQ `0x3E672DC` / hasher `--eax 1`

Next Attach needs a **new** clean idle map after user **запускай**,
`last_fix_time` newer than Event 41 `22:07:45`, ping **pong** for
minutes, one new Relic `slots=0`, then `wait-hold`. This turn did not
map.

Canon: `aoe4-x64dbg`, `RELIC_DEBUG_ATTACH.md`, `VMRUN_CYCLE.md`.
Sibling: [Cycle 8h RUN then 41](2026-09-13-cycle8h-run-then-41.md),
[NPT leftover](2026-09-13-hv-cycle8h-run-then-41.md).
