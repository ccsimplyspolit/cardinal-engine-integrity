# Product dbg cycle: HV hold → `--patch-game` → stock x64dbg (2026-09-13)

> **2026-09-14:** AUTO is **off**. Inject writes `auto_run=0`. User must
> confirm overlay RUN. [AUTO off](2026-09-14-patch-game-auto-off.md).

Did **not** nested-map. Cycle **8e** `AB7D293D` is already `load_ok` 20:18
(`hv_ping=pong`). Disk 8f stays unmapped. This note aligns the **usermode**
order (stock x64dbg, not rbhost).

## Point

The intended live order is **not** hidden rbhost first:

1. Clean idle HV map (`hv_ping=pong`). NPT ret-stub `RA_Enqueue`
   `0x3DD2550`, `RA_KickCtor` `0x3E691F4`, `RA_TimerQ_Push` `0x3E672DC`;
   hasher `eax=0xFFFFFFFE` at `0x3E57050`.
2. Titled Relic `slots=0`. IDA GUI **closed**. No `x64dbg.exe` yet
   (visible dbg before hold = DualFlag).
3. `python aoe4-hv/tools/zpp_at.py wait-hold`.
4. Elevated `AOE4HOOK/internal/x64/Release/DllInjector.exe --patch-game`
   writes `[patch_game] auto_run=1` `user32_body=1` then APC. Overlay
   `PatchGameTick` logs `[PatchGame] AUTO RUN` and applies **usermode**
   only (user32 bodies, retitle, `-nodbg` `0x844B2ED`, PEB wipe). No
   Relic `.text`. ntdll QSI body stays OFF (`08060001`).
5. Stock `x64dbg.exe` (leaf/path may contain `x64dbg` — sibling
   `0x3F328D8` would Enqueue `20220002` without NPT; hold makes that
   call a ret). No `Start-X64dbgHidden.ps1`, no RuntimeBroker, no
   titleboot. Events=0 / SafeAttach / DisableAslr=0 on that ini.
6. File→Attach / `debug_attach_pid` **only** if WindowWatch still
   `slots=0`. Any slot = kill Relic.

Script: `AOE4HOOK/tools/Run-ProductDbgCycle.ps1` (self-elevates; **never**
kdu). Hidden rbhost remains fallback if stock still packs sibling after
hold+AUTO.

## Live this boot

**Stale.** 8e hung after hold (Event 41 `20:27:31`). Cycle **8g**
`7B5C8989` is on disk, **not mapped**. Do not run this usermode cycle
until a new idle map + `hv_ping=pong`. Do not remap `AB7D293D`.
Do not `Start-X64dbgHidden`.

## Why stock attach is still unproven

Cycle 8d hang after Relic AV. 8e adds stale-NPT reap. Stock attach after
hold+AUTO has **not** been proven (8d used hidden `smabcc.exe` then Relic
`c0000005`). Any slot = kill Relic.

## Docs / skills aligned

`UPDATE_GUIDE` § flags + HV hold + §9.3, `RELIC_DEBUG_ATTACH.md`,
`aoe4-x64dbg` / `aoe4-hv` / `aoe4-injector-loader` / `x64dbg-mcp-stack`,
Patch Game i18n. Stale `--bare` / InjectBoot mapping / “hidden then
Attach” as product path removed from those canon spots.
