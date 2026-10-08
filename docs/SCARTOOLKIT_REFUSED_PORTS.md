# ScarToolKIT ports refused by HOOK

Date: 2026-08-28. Toolkit imagebase `0x7FF777A70000` (never mix with Relic ASLR).

This pass assessed Dodge, helper PE, and license for a HOOK-safe port. **None were implemented.** Overlay C++ was not edited: sibling **Port ZoomLUA and dofile** owns `InternalInjector` (`ui.cpp`, `zoom.cpp`, SCAR inject, rebuild). Lobby already prints that Dodge is not ported (`DrawStkLobbyPane`). Hook file: `Logs\needed_cpp_dodge.txt` (repo + `Documents\AOE4HSettings\Logs`).

CSV rows: `SCARTOOLKIT_PARITY_GAP.csv`. Broader gap write-up: `SCARTOOLKIT_PARITY_GAP.md`.

## License — nothing to port

AOE4HOOK is already an unlicensed overlay: it has no WinLicense gate, no `[license] key=`, no Stripe checkout, and no HWID bind. ScarToolKIT’s WinHTTP `activate.php`, HWID SHA-256, `X-STK-Auth` / Bearer session, and `NtTerminateProcess` on fail are **their** DRM, not a product feature to clone. There is nothing to port and no payment skip to implement. Settings already persist `hotkeys.ini` without a license check.

## Helper PE — original is 0 bytes (`wont_port`)

The ScarToolKIT helper payload was never recovered: `POST /api/asset.php` is `403 bad_asset_auth` on this disk, and `ScarToolKITU.exe` has a single MZ (no nested PE). **Do not** call scartoolkit.com, **do not** send `X-STK-Auth` to download, **do not** reconstruct mapper RVA `0xC55D0` / ManualMap / `%TEMP%\%02x.tmp` drop, and **do not** inject `our_fow_helper.dll` into Relic. Inner fog consume inside that missing image is unknown (integrity). Overlay already plants `FOWCTRL1` in InternalInjector (`implTag 'AOE4'`) and consumes **+8** (Full Reveal) and **+11** (Reveal Map one-shot) in-module. Zoom consume (+16/+20) is the ZoomLUA sibling’s job, not a second PE.

## Dodge — `wont_port` (RWX-only)

Toolkit Dodge is lobby chrome `Lobby.Button.Dodge` (draw interior `0xEEFCB` of `Overlay_DrawLobbyPanel` `0xEE670`) plus native `B5B990` / RVA `0xEB990`: `VirtualAllocEx` + `CreateRemoteThread` of a **0x29** RWX stub (`mov rcx/rdx/rax imm64; sub rsp,28h; call rax; … ret`) with immediates zeroed in the dump (truncated at `0x200`). IAT `CreateRemoteThread` xrefs are SCAR inject `AF04B0` and this Dodge site only. UI string: `Dodge on cooldown (%ds left)`.

Searched AOE4HOOK, `Documents\AOE4HSettings` SCARs, and recovered toolkit corpus (99 scars + Lua blobs): **no** Dodge that is SCAR, `SendInput`, or existing overlay logic. Overlay `SendInput` is production-macro groups 4–7 only (`hotkeys.cpp`). `World_LeaveGameMatch` is the engine quit path in Relic `core.scar`, not toolkit Dodge — do not wire it as a substitute. Idle-buildings SCAR explicitly is “not a ranked dodge.” **Do not** copy the RWX remote-thread stub into Relic. Lobby button stays unported.

## ZoomLUA / dofile — sibling, not this pass

**Port ZoomLUA and dofile** owns:

1. **ZoomLUA / FOWCTRL1 +16/+20** through existing `zoom.cpp` Autodeclinate (`info+0x10` / `+0x14`). Must **not** apply toolkit default **200.f** as live camera distance. No recovered ZoomLUA `Camera_SetZoomDist` SCAR body; visfog atmosphere is not ZoomLUA.
2. **dofile {PATH}** (scar 039 / `##ForceLoader`) sandboxed to `Documents\AOE4HSettings` only (no `..`, other drives, EXE dir, HTTP).

This agent did not touch `ui.cpp` to avoid a mid-edit collision.

## Implemented vs refused

| Item | Outcome | Why |
|---|---|---|
| License / HWID / activate | **Refused** | Overlay is already unlicensed; their DRM is not a HOOK feature |
| Helper PE / mapper `0xC55D0` / `asset.php` | **Refused** | Original payload **0 bytes**; extra image in Relic is integrity-unknown |
| Dodge CRT `0xEB990` | **Refused** | Only recovered method is truncated RWX + `CreateRemoteThread`; no SCAR/SendInput/overlay substitute |
| `World_LeaveGameMatch` as Dodge | **Refused** | Engine quit, not toolkit Dodge |
| ZoomLUA + sandboxed dofile | **Sibling** | `0133652d` holds InternalInjector |

No InternalInjector sources were added or patched in this pass.
