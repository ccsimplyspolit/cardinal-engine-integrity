# Cycle 8g: game freeze then Event 41 after Patch Game AUTO (2026-09-13)

Mailbox ops 1–12 unchanged. **Do not map.** Stock x64dbg was **not**
started (dbg script interrupted). Relic **6732** froze, then host
Kernel-Power **41**.

## Point

Event **41** `20:49:03` (boot `20:48:59`, 6008 previous shutdown
**20:47:38**) is **not** nested `kdu`. Boot `20:27:27` had **one** idle
map: Cycle **8g** `load_ok` **20:38:49** sys `7B5C8989` (1095168). hitch
`inner=0` `npf=0`. ping **pong**.

The game freeze is in the overlay log **before** the host died.

## Timeline (boot 20:27:27)

| Time | Event |
|---|---|
| 20:38:49 | idle `load_ok` 8g `7B5C8989` |
| 20:40:25 | Relic **1292** (died ~20:44, no WER) |
| 20:45:44 | Relic **6732** `0x7FF627330000` |
| 20:45:54 | `hold --apply` 4 sites **status=0**, hasher protect **status=0**, `slots=0` |
| 20:46:33 | APC `InternalInjector` DllMain / IntegrityCloak / Present hook |
| 20:46:43 | `[PatchGame] AUTO RUN` — user32 bodies + `-nodbg` + PEB; neutralize OFF |
| 20:46:44 | `[PRESENT] skip overlay … GPU Present` `1844674407370954` ms (`gpu_fault`) |
| 20:47:02 | Present stalled ~3 s, stack Relic `+0x3D48989` … |
| 20:47:06 | DXGI **`0x887A0006` DEVICE_HUNG** then **`0x887A0005` DEVICE_REMOVED** |
| 20:47:06 | VEH `c0000005` Relic RVA **`0x3AD6A86`** `rdi=0x887A0006` `av_addr=0` |
| 20:47:28 | Present stalled **21562 ms** (`ntdll`) |
| 20:47:38 | unexpected shutdown |
| 20:48:59 / 20:49:03 | boot + Event 41. ping **ping_err**. Minidump empty |

Capture: `aoe4-hv/docs/_bsod/crash-20260913-204926`. Cookie
`load_ok_pending_alive` (hold stamp `20:45:55`, `boot_at_attempt=20:27:27`).
Gate **21**.

## Freeze vs BSOD

1. **Freeze (usermode):** right after AUTO RUN the overlay Present guard
   treated a wrapped QPC delta as a multi-exabyte hitch (`%.0f` of
   `uint64` underflow) → `gpu_fault` skip + RTV recreate loop → NVIDIA
   TDR (`DEVICE_HUNG` / `DEVICE_REMOVED`) → Relic AV at `0x3AD6A86`
   while `rdi` still holds `0x887A0006`.
2. **Host 41:** same pattern as 8d — Relic dying **under armed NPT**.
   8g dropped KPTI foreign-CR3 disarm, so hold itself lived past apply
   (1292 and 6732 both `status=0`). Stale-GVA reap does not fire while
   the process still maps `.text` through TDR / AV. Host hang ~30 s after
   DEVICE_REMOVED.

x64dbg was not in the process list. Not rbhost. Not a second `kdu`.

## Do not

- `kdu` / `sc start Aoe4Hv` / nested-map this boot
- remap 8g `7B5C8989` / 8e `AB7D293D` / 8f `02F9B040` / 8d `A1EA2CF1` /
  8c `D78C5065` / 8b `8C9D7CDD` / Cycle 3 `5351E024`
- hold dead **6732** / **1292** / 16544 / 34288
- inject overlay AUTO on the next map until Present QPC hitch and TDR
  are fixed (or prove hold-only idle Relic for minutes with overlay off)
- open IDA on a live Relic

Next map only after user **запускай** and a `last_fix_time` newer than
`20:49:03`.
