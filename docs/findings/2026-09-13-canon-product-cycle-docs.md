# Canon sweep: HV → overlay AUTO → stock x64dbg (2026-09-13)

> **2026-09-14:** AUTO is **off**. Confirm RUN in overlay.
> [AUTO off](2026-09-14-patch-game-auto-off.md).

Docs / skills / comments only. Did **not** map. Did **not** launch
hidden rbhost.

## Point

Live order agents must follow:

1. Clean idle HV map (`hv_ping=pong`).
2. Titled Relic `slots=0`. IDA closed. No `x64dbg.exe` yet.
3. `python aoe4-hv/tools/zpp_at.py wait-hold`.
4. Elevated `DllInjector.exe --patch-game` → `[PatchGame] AUTO RUN`
   (usermode only).
5. Stock `x64dbg.exe` (`AOE4HOOK/tools/Run-ProductDbgCycle.ps1`).
6. Attach only if WindowWatch still `slots=0`.

Hidden `Start-X64dbgHidden.ps1` is fallback if stock packs sibling
`0x3F328D8` despite NPT.

## Updated (canon)

- Skills: `aoe4-project-map`, `aoe4-cpp-overlay` (mirrors `.agents` + home).
- Rules: `aoe4-hv-bsod-gate.mdc` §7, `aoe4-skills.mdc`, `run-as-admin.mdc`.
- Guides: `RELIC_COMMAND_LINE.md` DllInjector table, `aoe4-hv/README.md`,
  `aoe4-hv/docs/AOE4.md`, ADR-007 §6, `scyllahide/README.md`,
  `AOE4HOOK/docs/README.md` inject paragraph.
- Comments: `DllInjector/main.cpp`, `patch_game.h` / `patch_game_gate.h` /
  `patch_game.cpp`, `zpp_at.py wait-hold`, `Cycle8-Proof.ps1`,
  `Run-PatchAtCycle.ps1`, `Run-CleanCycle.ps1`, Patch Game i18n Sibling key.

## Banners only (journal kept)

- `2026-09-13-hv-hold-before-dbg.md`
- `2026-09-13-hv-full-map-handoff.md`
- `2026-09-13-agent-context-usermode-dbg.md` (CLI was “watch-only”)

Did **not** rewrite `STATUS.md`, 09-06 findings, or `_arhive`.
