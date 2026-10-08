# Cycle 8h: elevated APC inject, no AUTO (2026-09-13)

User asked **«а инжект сделаешь?»**. One elevated `DllInjector.exe` APC
`LoadLibraryW`. **No** `--patch-game` / `--auto-patch`. `auto_run` stayed **0**.
**No** stock x64dbg Attach (next step). **No** nested-map / kdu / Relic `.text` WPM.

## Live

| | |
|---|---|
| Relic | **3832** start 21:38:49 `responding=True` |
| base | `0x7FF7B6EE0000` SizeOfImage `0x8C3D000` (16.3.11308.0) |
| ping | **pong** (map `17E25811` still live) |
| window pre | 22:01:51 `slots=0 accum=0 flag=0` uninit/empty |
| window post | 22:02:47 `slots=0 accum=0 flag=0` uninit/empty |
| `auto_run` | `0` before and after |
| DllInjector | elevated `K:\aoe4_dlc\hh\AOE4HOOK\internal\x64\Release\DllInjector.exe` exit **0** |
| DLL | sibling `InternalInjector.dll` 21:04:36; OverlayBoot 22:01:52; Present hooks ok; PEB unlink |

Dead PIDs **15720 / 10324 / 19956 / 6732** were not held. `relic_count=1`.
Second injector was not started (`dllinjector_count=0`).

## Proof DLL loaded (Toolhelp will lie)

DllInjector waits on Toolhelp **before** overlay hide, then exits 0.

`[RA] hide: PEB unlink ok module=00007FF8ED6C0000` at 22:01:52.773 — after that
`Get-Process.Modules` / Toolhelp **do not** list `InternalInjector.dll`.
InjectNow first pass logged `InternalInjector_post=False` (exit 8). That is
**hide**, not a failed APC.

Overlay log `Documents\AOE4HSettings\Logs\aoe4_internal.log` (rotated at inject):

- 22:01:52.550 OverlayBoot / HooksInit / DXGI Present hook
- 22:01:53.309 `scar AUTO=0 lua AUTO=0`
- 22:01:53.311 `[RA] Snapshot: uninit/empty`
- no `[PatchGame] AUTO RUN`

`[PatchGame] host self-check ok: slots=3 blocked` is a **synthetic** gate unit
test (`packed.slots = 3` in `PatchGameHostSelfCheck`). Not live WW slots.

## gpu_fault skip (not DXGI TDR)

22:01:54.579 `[PRESENT] SKIP overlay reason=gpu_fault` then 22:01:57.093
`RESTORE present_hr=0x00000000`. Same QPC-wrap family as 8g
(`fps_profile.cpp` `QpcDeltaMs`). Relic stayed up, ping pong, no new Event 41.
**Do not remap** `17E25811` for this skip. Capture-CrashContext not run (no
DEVICE_HUNG / Relic death).

## Do not

- second `DllInjector` into 3832 (PEB already unlinked)
- `--patch-game` / AUTO (8g Relic **6732** DXGI `0x887A0006` after AUTO)
- Attach while this step only; next is attach **without hide** if `slots=0`
- hold 15720 / 10324 / 19956 / 6732
- kdu / nested-map / WPM Relic `.text` / arm TimerQ `0x3E672DC`

Scripts: `aoe4-hv/docs/Cycle8h-InjectNow.ps1`, `Cycle8h-InjectVerify.ps1`.
Breadcrumbs: `aoe4-hv/docs/_bsod/cycle8h-inject-now.txt`,
`cycle8h-inject-verify.txt`.

## 22:12 append — host 41 after Overlay RUN

User pressed Overlay **RUN** 22:03:48 (`auto_run=1` left in
`config.ini`). Host hung 22:06:08. Event **41** `22:07:45` on mapped
`17E25811`. Relic **3832** gone with the host. ping **ud**. Leftover NX
on CR3 `0x55ABF3000` is **not** measurable (SVM off; Relic was still
mapping at last overlay line 22:06:36). **Do not remap.** Full NPT
write-up:
[Cycle 8h RUN then 41](2026-09-13-hv-cycle8h-run-then-41.md).
