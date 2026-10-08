# Patch Game tab (usermode after HV hold)

> **2026-09-14:** AUTO is **off**. Leftover `auto_run=1` ignored. RUN is
> red + confirm. [AUTO off](2026-09-14-patch-game-auto-off.md).

2026-09-13. Overlay `InternalInjector` only. Did **not** map HV, did **not** edit `aoe4-hv` ELF/mailbox, did **not** change AI BOT.

## What RUN does (DLL, after hold)

Gate (host-tested): exactly one `RelicCardinal.exe`, file version `16.3.11308.0`, RA window RPM `ok`, **`slots=0`**, RA neutralize `.text` **off**. Else RUN is grey and the HUD shows why.

On press:

1. `RaHideInstall` — PEB unlink of the overlay DLL (already on `EngineStart`; idempotent).
2. `ra_retitle::RetitleAll` + 50 ms hammer for 8 s. Skips current PID and **WindowWatch.exe** leaf. EnumChildWindows inside retitle.
3. `RaHideInstallUser32Bodies` — trampoline **user32 export prologues** (`GetWindowTextW` / `A`, lengths, `GetClassNameW`, `FindWindowW`/`A`). Catches hashed GWTW `0x3F87250` and IAT call sites. **Does not** patch Relic IAT GWTW (pack `0x56FD3C0` / `0x20DE00AD`) or hash caches `0x7AFDE08` / `0x7AFDE00`.
4. `.data` `-nodbg` RVA **`0x844B2ED`** write `1`. Log `[DevBypass] -nodbg forced`. Does **not** stub `Dev_NoDbg_Check` `0x3B77110`.
5. PEB `BeingDebugged=0`, `NtGlobalFlag &= ~0x70` (x64 PEB+`0xBC`). **No** ntdll QIP hook.
6. `XboxEnforcementInstall` (hosts / Network Monitor path; already ON at engine start).
7. Log `[RA] neutralize OFF (Patch Game RUN; no Relic .text)`.

Optional checkbox **ntdll NtQuerySystemInformation body**: default **off**. `RaHideInstallNtdllQsiBody` refuses (PID 36540 packed `08060001` in ~2 s). Skip for stock x64dbg. Hidden rbhost is fallback, not a sibling plant.

Persist across restart: `config.ini` `[patch_game] user32_body` / `ntdll_qsi`. `auto_run` is **always saved 0** (2026-09-14). RUN applied-state is session-only (`persists=false`). Overlay never AUTO-runs. Elevated `DllInjector.exe` also writes `auto_run=0`.

## What RUN does not do (HV remainder)

| Item | RVA / note | Owner |
|---|---|---|
| WindowWatcher stub | `0x3F0A7D0` | HV NPT / not DLL. Stub `.text` → IAT-kick |
| Sibling stub | `0x3F328D8` | HV NPT (Enqueue ret). Stock `x64dbg.exe` after hold. Hidden `Start-X64dbgHidden.ps1` = fallback; not plant |
| Enqueue / KickCtor / TimerQ | `0x3DD2550` + siblings | HV hold |
| hasher | `0x3E57050` | HV |
| 7AB0 / 45E8 / dest 4K | | HV / leave alive |
| Relic IAT GWTW | pack `0x56FD3C0` | never |
| VMMCALL / mailbox | ADR-005 | not from Present / this DLL |
| `MpBypassInstallRaNeutralize` | Watcher/Enqueue `.text` | Debug tab only; RUN **refuses** if ON |
| Attach / launch x64dbg | | not from this tab; wait `slots=0` |

OS-body jmp without HV Enqueue stub packed `08060001` on 2026-09-06 ([os-body-hide](2026-09-06-os-body-hide.md)). HUD warns: hold first.

## UI

- New `MenuTab_PatchGame` after AI BOT (`tab_schema=11`; old Probe/SendScar/Network indices +1).
- Nav: Automation → Patch Game. Title **Patch Game**. Blurb **usermode hide/hooks after HV hold.**
- CTA **RUN — DANGEROUS** (red) + confirm modal. Vs humans banner: hide only, no plant, no sim-write; still dangerous.
- HUD: Relic PID, version, slots/accum/flag/tag (`0x7AF6DC8`), **Hide ON/OFF** (RUN applied), **AUTO RUN OFF (forced)**, PEB unlink, user32 body, `-nodbg` byte, PEB debug, FairPlay, neutralize, HV ping from `aoe4-hv/docs/cycle-state.json` (file read, no VMMCALL). Product checklist is stock x64dbg after a **confirmed** RUN (not Attach, not Present `SendMessage`). Hidden rbhost is fallback.

## Files

- `internal/InternalInjector/patch_game_gate.h` / `patch_game.cpp` / `ui_patch_game.cpp`
- `ra_hide.cpp` — `RaHideInstallUser32Bodies`, PEB debug wipe, body restore on shutdown
- Host: `tests/adversarial/test_patch_game.cpp` (`slots=3` → RUN no-op)

## Build

`MSBuild InternalInjector Release|x64` → `AOE4HOOK\internal\x64\Release\InternalInjector.dll`
