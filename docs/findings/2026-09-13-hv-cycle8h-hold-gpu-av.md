# Cycle 8h: Relic freeze + Task Manager paint — GPU AV after TimerQ hold (2026-09-13)

Mailbox ops 1–12 unchanged. **No remap.** Overlay / Patch Game did **not**
run. Host stayed up (ping **pong**, no new Event 41). Relic **15720** is
dead — do not hold it.

## Point

User saw the game frozen dead and Task Manager Performance tab torn
(frequency `633015205482 ГГц`, overlapping UA/RU labels). That is **not**
a Taskmgr hang and **not** an NPF/CPU storm.

| Check (21:29:36) | Value |
|---|---|
| ping | pong |
| Event 41 | still `21:06:01` (this boot’s previous hang) |
| Display TDR log | 0 |
| CPU WMI | 4501 MHz, load 0 |
| Taskmgr 19172 | `responding=True` `hung=False` (started 21:26:54) |
| Relic | **gone** |
| hitch | last sample 21:22 idle `vmcall_skip`; watcher already ended |

Task Manager opened **during** the NVIDIA/Steam-overlay collapse. WMI
clock is sane; the Performance tab’s APERF/MPERF path sits on
`svm_slices::tsc_hide` and painted garbage while DWM recomposed after
the driver heap deaths. Restart Taskmgr after GPU is back.

## Timeline (boot 21:05:57, map `17E25811` 21:19:25)

| Time | Event |
|---|---|
| 21:23:08 | Relic **15720** `0x7FF7B6EE0000` Steam `-dev -nodbg -notrap` |
| 21:25:51 | `hold --apply` 4 sites **status=0** (Enqueue + KickCtor + **TimerQ** + hasher) + hasher protect, `slots=0` |
| 21:26:07–17 | `lghub_system_tray` / `nvcontainer` / `NVDisplay.Container` AV/heap (`0xc0000374`) |
| 21:26:26 | Steam `gameoverlayui64` heap `0xc0000374` (not InternalInjector) |
| 21:26:28 | Relic `0xc0000005` write@0 RVA **`0x3AD6BC6`** PID `0x3D68`=15720 |
| 21:26:51 | prove refused `relic_count=2` (WER dump still alive + remnant) |
| 21:26:54 | Taskmgr started — torn Performance tab |
| 21:26:57 | WER `RelicCardinal.exe.15720.dmp` 3.84 GB |
| 21:29:05 | second Relic AV RVA **`0x8CD153`** (same PID; known teardown null-deref) |
| 21:29:24 | WER `RelicCardinal.exe(1).15720.dmp` |
| 21:30:42 | `stealth --clear` status=ok, Relic already 0, ping still pong |

## Faults (RVA only)

WER ExceptionStream + Event 1000, Relic base `0x7FF7B6EE0000`:

| Dump | RVA | Note |
|---|---|---|
| `.15720.dmp` 21:26:57 | **`0x3AD6BC6`** write `info1=0` | same Present-suicide family as 8g **`0x3AD6A86`** (delta `0x140`); GPU already gone (`dumps/crash_20260913_investigation`) |
| `(1).15720.dmp` 21:29:24 | **`0x8CD153`** | [2026-09-06-bsod](2026-09-06-bsod.md) Relic VEH null-deref / `AI_LockSquad` class — teardown, not the first kill |

8g needed overlay AUTO + QPC wrap to reach `0x3AD6A86`. 8h reached the
same Present write@0 **without** InternalInjector: hold TimerQ + Steam
overlay + NVIDIA container heap.

## Why TimerQ

Catalog already: healthy menu TimerQ list ~286 nodes; `list=0` drops
normal work. `RA_TimerQ_Push` `0x3E672DC` is **only** called from
`EventSchedule` `0x3DD15E4`. Goal item 6: Heartbeat / EventSchedule must
live. A ret stub on that push is a silent EventSchedule kill **and** an
NPF on every schedule tick (identity NX → stealth copy) while Present
runs. 16 s later the NVIDIA stack and Steam overlay heap-die, then Relic
writes 0 at `0x3AD6BC6`.

This is **not** Cycle 8e (KPTI foreign-CR3 → host 41). Host lived.

## Fix (usermode, no remap)

- `zpp_at.py` + `aoe4_16.3.11308.json`: **do not arm** `RA_TimerQ_Push`.
  Hold stays Enqueue `0x3DD2550` eax=0 + KickCtor `0x3E691F4` eax=0 +
  hasher `0x3E57050` `eax=0xFFFFFFFE` + protect `0x3E57000`.
- Steam launch: `OverlayEnable=0` / `EnableGameOverlay=0` (8h
  `gameoverlayui64` died; still not InternalInjector).
- Dead PID **15720**. Do not nested-map. Do not remap `17E25811` unless
  a **new** Event 41 matches this sys.

## Do not

- `kdu` / nested-map / remap 8g `7B5C8989` / 8e `AB7D293D` / Cycle 3 `5351E024`
- hold 15720 / 6732 / 16544 / …
- DllInjector / `--patch-game` / arm WW / sibling / 7AB0 / 45E8 / E8 flood
- `--eax 1` hasher / WPM Relic `.text` / mailbox op 13
- treat Taskmgr torn paint as a second HV bug this boot

## 21:34 packed hold (PID 10324)

`wait-hold` applied **1.8 s** after a new Relic. Enqueue RPM
`0011dcf6…` / KickCtor `b338c28a…` = still **disk crypt**. Hasher page
was already live (`48895c24…`). Arm status=0 on ciphertext 4K. Relic
gone by 21:35. `zpp_at.py` now waits until Enqueue starts `44 89 4c 24 20`
and KickCtor `48 8b c4 48 89` (live 15720). Do not hold **10324**.

## 21:36 settle (PID 19956)

Unpacked prologues at T+15.7s, apply immediately. Relic **19956**
(`0x4DF4`) died in `ntdll+0x27384` `0xc0000005` then `0xc000041d`
(fatal user callback) — not Present `0x3AD6BC6`. PID **10324**
(`0x2854`) packed hold died `ntdll+0x328b0`. Leftover CR3 clear
returned mailbox **status=8 sites=0** = `not_found` (not NX off; aux not
ELF count). [leftover NX status=8](2026-09-13-hv-cycle8h-leftover-nx-status8.md).
`zpp_at`
now waits **45 s** after first live Enqueue/KickCtor before ZPPN.
Dead **19956**. No remap.

## 21:38 live (PID 3832)

Hold after unpack + 45s settle, **no TimerQ**. Enqueue/KickCtor/hasher
`status=0`. Relic **3832** `0x7FF7B6EE0000` `cr3=0x55ABF3000` start
21:38:49. Prove 21:40:21–21:41:12 **slots=0** six samples, process
still `responding=True` (cpu 348s, WS live). Taskmgr **19172** still
responding. Hidden x64dbg not started this prove. No remap.

Next: hidden x64dbg (`Start-X64dbgHidden.ps1`) while **3832** stays
`slots=0`. Do not hold 15720 / 10324 / 19956.

## 22:12 append — 3832 dead, Event 41 22:07

Hidden prove 22:00–22:01 (`jahjgw` live, slots=0) then inject 22:01 then
user Overlay RUN 22:03. Host 41 `22:07:45`. Do **not** remap `17E25811`.
[RUN then 41](2026-09-13-hv-cycle8h-run-then-41.md).

## 22:01 inject (PID 3832)

User asked for inject. Elevated `DllInjector.exe` (no `--patch-game`)
22:01:51–52. `auto_run=0`. Overlay live, `slots=0` at 22:02:47. PEB unlink
hides the module from Toolhelp. Attach is a **later** step (without hide),
only if slots stay 0. [inject no AUTO](2026-09-13-cycle8h-inject-no-auto.md).
