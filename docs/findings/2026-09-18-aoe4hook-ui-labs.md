# 2026-09-18 AOE4HOOK-UI labs (sibling, not overlay)

Canon: `C:\Users\Lanzerxyz\Documents\GitHub\AOE4HOOK-UI\HANDOVER.md`

This repo's in-game menu is still the **old** AOE4HOOK chrome (tag `v1.0.4`,
`InternalInjector.dll` 18.09 02:45). Three standalone D3D9 exe live **outside**
this tree and were never merged into the overlay.

| Lab | Role |
|---|---|
| `loader\` | Gamesense-style window. Inject runs our `DllInjector.exe` |
| `skeetmenu\` | Synvy ImGui **1.70** clone + AOE4HOOK tabs. Port candidate |
| `menulab\` | Legendware `IdaLovesMe` GUI. Dead end |

How to prove skeet is **not** in the DLL: zero hits for `MenuComputeMetrics`,
`MenuDrawTabIcon`, `GroupBoxTitle`.

Port (only if asked): hand-move the 1.70 widget patch onto overlay ImGui
**1.92.1**. Order and traps are HANDOVER §5 (`-101` slider, `+144` combo,
tab cell 74/71/72, tooltip clip, `NOMINMAX` vs legendware `color.h`).

Do not `git add` untracked `AOE4HOOK\skeet loader\` (~40 MB, Gideon).
Public CS dumps in `menulab\_ref\` did not contain the user's screenshot menu
(HANDOVER §7). Overlay defects in HANDOVER §2 (Crucible idle AI, exit crash,
Fast TC) are product bugs, not UI-lab work.

Pointer from this repo: `docs/README.md` + `.cursor/rules/aoe4hook-ui-labs.mdc`.
