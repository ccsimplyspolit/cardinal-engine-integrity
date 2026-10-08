# Cycle 3 запускай path (2026-09-13 16:51) — do not map

SAFE audit after Cycle 3 ELF rebuild. Goal still open: one SVM-map
then Relic `-dev -nodbg -notrap` then fail-closed `hold --apply` 39/39
then Vs AI then visible x64dbg from `C:\Program Files (x86)\rbhost`
60s. One hypothesis/cycle. Mailbox ops 1-12 untouched. **No map this
turn.** User has **not** said **запускай**.

## Proven on disk (this boot)

| | |
|---|---|
| LastBootUpTime | **2026-09-13T16:32:44** |
| Event 41 | **2026-09-13T16:32:48** (no 1074 for this hang; last 1074 is 14:22) |
| 6008 | unexpected previous shutdown **16:30:34** (logged 16:32:55) |
| Minidump | empty (`CrashDumpEnabled=0` AutoReboot=1 AlwaysKeep=0) |
| Capture | `docs/_bsod/boot-capture.json` stamp **163635**, boot matches |
| Cookie | `analyzed_failed` (attempt 16:21:40, corpse sys **16:20:21**) |
| Gate dry-run | **20** `launch_authorized=false` (Event 41 is **before** `last_fix`) |
| keyed `Get-HvPingToken` | **ud** |
| Relic | **none**. PID **5012** dead. Do **not** reuse `0x7FF7BABB0000` |
| `zpp_hypervisor` | 16:45:28 / 1025336 / SHA256 `62CDC1EF77762E0AB4E6752988DEBBF8F29D88A109FA862D179BFF7735CE0822` |
| `zpp_loader.sys` | 16:45:29 / 1075200 / SHA256 `5351E024F6321EBC4C3F99A82B8E576826C967A7C5B74340087A20AF7EAD5CF1` |
| source vs ELF | `insn_decode.h` 16:45:13, `npt_stealth.cpp` 16:45:16, `insn_boundary.cpp` 16:45:20 — older than ELF |
| `insn_boundary.exe` | leftover `48 8B 05` vs `E8` at +5 **PASS** (re-run 16:51) |
| `zpp_at.py` | refuse retry after any `arm va=` (mtime 16:37:50) |
| `last_fix_time` | 16:45:29 (sys mtime). **Not** launch permission |

Cycle 3 hyp unchanged: `stealth_nop5_e8_ok` + skip `insn_starts_at`
left-scan on nop5+E8. Not proven in SVM (not mapped).

## Gate after запускай (easy miss)

`Test-VmrunDumpGate` still refuses if **either**:

1. `launch_authorized` is false (today: **20**), **or**
2. `status` matches `bsod|new_bsod|...` even after authorized=true.

On **запускай** set **both** `launch_authorized=true` **and**
`status=ready_to_launch`. Leave `new_bsod` and the elevated gate still
fails. Cookie `analyzed_failed` does **not** block (only `in_progress` /
`load_ok_pending_alive`). Event 41 16:32:48 is older than last_fix
16:45:29, so the 41 check will pass once those two fields flip.

Continued chat is **not** запускай. Ping **ud** is **not** green.

## Exact next launch (run only after user запускай)

Relic closed. No nested-map. No `sc start Aoe4Hv`. No `Start-ZppLoader`
this cycle (user path is `Map-AfterZppu`). Do not quote `last-zpp-key.txt`.

### 0. Preflight (same boot 16:32:44)

```powershell
# Relic must be none. Kill any leftover. Never attach 0x7FF7BABB0000.
Get-Process RelicCardinal -ErrorAction SilentlyContinue
# keyed ping must be ud. If pong: STOP (SVM live). Nested-map = Event 41.
. K:\aoe4_dlc\hh\aoe4-hv\docs\HvCrashLog.ps1
Get-HvPingToken   # prints only ud|pong, never the key
```

CrashDumpEnabled must stay **0**.

### 1. Flip gate flags (only after запускай in this boot)

Edit `aoe4-hv/docs/cycle-state.json`:

- `launch_authorized` = `true`
- `status` = `ready_to_launch` (not `new_bsod`)
- keep `last_fix_time=2026-09-13T16:45:29`
- `pid` / `image_base` / `session_id` stay empty (new Relic after idle)

### 2. Elevated gate, then one map

```powershell
Start-Process -FilePath powershell.exe -Verb RunAs -Wait -ArgumentList @(
  '-NoProfile','-ExecutionPolicy','Bypass','-Command',
  '. K:\aoe4_dlc\hh\aoe4-hv\docs\Test-VmrunDumpGate.ps1; $g = Test-VmrunDumpGate; $g | Format-List; if (-not $g.ok) { exit [int]$g.code }'
)
```

Expect `ok=True` `code=0`. If 20/21: **STOP. Do not map.**

```powershell
Start-Process -FilePath powershell.exe -Verb RunAs -Wait -ArgumentList @(
  '-NoProfile','-ExecutionPolicy','Bypass','-File',
  'K:\aoe4_dlc\hh\aoe4-hv\docs\Map-AfterZppu.ps1'
)
```

**One** `Map-AfterZppu`. Expect `load_ok` in `C:\Windows\Temp\zpp_loader.log`
and hitch_watch_end. Keyed ping becomes **pong**. If ping was already pong
before this step: you nested-mapped — hang.

### 3. Identity idle minutes (no Relic, no hold)

Stay on identity NPT. Do **not** start Steam. Do **not** `hold --apply`.
Do **not** x64dbg. Host still up several minutes. Then Relic.

### 4. Relic then hold then Vs AI then visible dbg

1. Steam **1466860** `-dev -nodbg -notrap`. New PID, new image base.
   SizeOfImage `0x8C3D000`. **Never** `0x7FF7BABB0000`.
2. `python K:\aoe4_dlc\hh\aoe4-hv\tools\zpp_at.py locate` then
   `window`. Query Relic `status=0` before arm.
3. **One** `python K:\aoe4_dlc\hh\aoe4-hv\tools\zpp_at.py wait-hold`
   (apply=true, wait=true). Must be **39/39** `status=0`. Any `arm va=`
   then `hook_failed` / mailbox death: **STOP**, kill Relic, do not retry
   apply, do not nested-map, do not x64dbg.
4. Vs AI (slots still 0 or kill Relic).
5. Visible x64dbg from `C:\Program Files (x86)\rbhost\release\x64`
   60s. Not before 39/39. `Start-X64dbgHidden.ps1` is the DualFlag
   launcher; this goal wants the **visible** rbhost tree after apply.

Mailbox ops **1-12** untouched.

## Do not (this turn / until запускай)

`kdu` / `Map-AfterZppu` / `Start-ZppLoader`. Nested-map. Hold on a
fresh SVM before idle minutes. Reuse PID 5012 / `0x7FF7BABB0000`. Start
x64dbg before 39/39. Set `launch_authorized=true` without `запускай`.

Related: [Cycle 3 ELF rebuild](2026-09-13-hv-cycle3-elf-rebuild.md),
[Cycle 3 source](2026-09-13-hv-cycle3-hold-insn-boundary.md),
[Cycle 1 hold hang](2026-09-13-hv-cycle1-hold-hang.md).
