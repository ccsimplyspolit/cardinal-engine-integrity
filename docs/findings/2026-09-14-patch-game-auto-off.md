# Patch Game AUTO off + RUN danger confirm (2026-09-14)

Did **not** map HV. Overlay + DllInjector only.

## Point

`[patch_game] auto_run` is **forced 0**. Overlay `PatchGameTick` no longer
calls `PatchGameRun()` on a green gate. Leftover `auto_run=1` in
`Documents\AOE4HSettings\Config\config.ini` is logged and ignored.
`--patch-game` / `--auto-patch` still inject; they **clear** AUTO, they
do not arm it.

RUN is a red button. A modal repeats the hang warnings. **Cancel** is
the default focus. Confirm writes `[PatchGame] RUN applied`.

## Why

- Cycle 8g Relic **6732**: DXGI `DEVICE_HUNG` / Event 41 after AUTO.
- Cycle 8h Relic **3832**: three overlay RUN presses then Event 41;
  leftover `auto_run=1` would AUTO on the next APC.

## Files

- `internal/InternalInjector/patch_game.cpp` / `ui_patch_game.cpp` / `config.cpp`
- `internal/DllInjector/main.cpp`
- `tools/Run-ProductDbgCycle.ps1` waits for `[PatchGame] RUN applied`
