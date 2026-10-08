# 2026-09-13 crash-safe HV breadcrumbs (no map)

Boot **15:54:23**. Event 41 **15:54:27**. Minidump empty. Cookie
`docs/_bsod/map-attempt.json` still `in_progress` from boot **15:43:47**
sys **15:51:32** 1074688 B ping `ud`. `launch_authorized=false`. Mapper
off this pass.

## What logs existed (and why they failed)

| Path | Role | Failure mode |
|---|---|---|
| `%SystemRoot%\Temp\zpp_loader.log` | loader `zpp_log` FILE_WRITE_THROUGH | dies with the box / 0% dump hang |
| `docs/last-zpp-start.log` | Map-AfterZppu `Set-Content` then Add-Content | **all-NUL** mid-write (15:37); not flushed |
| `docs/_bsod/hitch-host.log` | Watch-ZppHitch DPC/ISR | last good copy is **15:07** `load_ok`; 15:51 map never left a hitch |
| `docs/_bsod/zpp_loader-live.log` | hitch copy of Temp | only if hitch is already running |
| `docs/_bsod/pre-map-trace.txt` | one Flush(true) line | existed but Map-AfterZppu wrote it *after* wiping last-zpp-start; Start-ZppLoader had none |
| `docs/_bsod/map-attempt.json` | cookie | WriteAllText then Open-Read Flush (no-op); missing utc/gate/CrashDumpEnabled |
| `docs/_bsod/pre-map.txt` | one-shot crumb | not dated reliably on Start-ZppLoader |
| HostPrep | PasswordLess + CrashDumpEnabled=0 | did **not** run Capture first |
| BlueScreenView | Desktop exe | never exported into `_bsod` |

`last-zpp-start.log` from 15:53 survived some lines (Relic none, ping, sys,
rotated prev log) then the mapper died — still not enough: hitch never
started, Temp log gone, cookie did not record gate/utc.

## What was added (no kdu / no sc start)

- `docs/HvCrashLog.ps1` — `Write-FlushedText` FileStream.Flush(true)
- cookie v2: utc, gate_ok/code/reason, CrashDumpEnabled, real flush
- append-only `pre-map-trace.txt` + dated `pre-map-*.txt` **before** kdu
  on both `Map-AfterZppu.ps1` and `Start-ZppLoader.ps1`
- hitch started and **waited alive** (`i=0`) then map; copy every second
  to `zpp_loader-live.log` with flush
- `last-zpp-start-live.log` append-only; archive before truncate
- loader dual-write `zpp_loader-k.log` on K: + stages
  `preflight_begin` / `cpu_enter` persist / `alloc_begin` /
  `preflight_done` / `after_load_ok`; ELF `bringup_stage` 10..70 in
  `elfst=` (RAM; hitch prints it after persist). **No mailbox op 13.**
- HostPrep **first** action: `Capture-CrashContext.ps1 -Boot`
- BlueScreenView `/scomma` + `/stext` into `docs/_bsod/`
- `Invoke-VmrunDumpGate.ps1` dry-run wrapper

## How a future 0% / Event 41 is diagnosable

After reboot, in order:

1. `docs/_bsod/boot-capture.json` + `crash-<stamp>/context.txt`
2. cookie: which sys mtime/size, ping, boot_at_attempt, gate
3. last flushed `pre-map-trace.txt` line (must include `kdu_begin`)
4. hitch last `i=` line and `zpp=` tail
5. `zpp_loader-k.log` last `stage=` / `elfst=`
6. Event 41 time vs cookie attempt_time
7. BlueScreenView CSV — **empty** while `CrashDumpEnabled=0`

## Dry-run this pass (no mapper)

`Invoke-VmrunDumpGate.ps1` and `Map-AfterZppu.ps1` and `Start-ZppLoader.ps1`
all exit **21** (cookie in_progress boot 15:43 vs now 15:54, sys 15:51
1074688 B, ping ud). No UAC, no kdu.

`Capture-CrashContext.ps1` → `docs/_bsod/crash-20260913-161926/`.
Live CrashDumpEnabled=**0**. Minidump none. Event 41 15:54:27 + 6008.
BlueScreenView `/scomma` exit 0, **csv 0 bytes** / txt 2 bytes
(`docs/_bsod/bluescreenview-status.txt`).

## Remaining gaps

- `CrashDumpEnabled=0` ⇒ **no BugCheck code in Minidump**. Photograph
  the screen if AutoReboot does not fire. Event 41 is the host signal.
- ELF `bringup_stage` is RAM until the loader persists a line. First
  VMRUN hang: last durable line is `elf_enter` for that CPU (now on K:).
- Hitch must be alive **before** kdu; if Get-Counter hangs, wait is 12 s
  then map anyway (logged).
- This pass did **not** rebuild/map `zpp_loader.sys`. Source-only until
  user **запускай** and a new `last_fix_time`.
