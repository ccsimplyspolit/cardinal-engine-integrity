# AOE4HOOK native (non-SCAR) features

Product overlay surface. Toolkit host catalog (RVAs, helper PE) lives in
`ScarToolKIT/recovered/NATIVE_FEATURES.md` — do not mix toolkit VAs with Relic.

Full magic-by-magic parity: `docs/SCARTOOLKIT_NATIVE_PARITY.md`.
Maphack / FOWCTRL1 consume: `docs/MAPHACK.md`.
Inject / menu header / Memory click-through: `docs/README.md`.

## Policy

- Overlay does **not** inject ScarToolKIT PE DllMain, `our_fow_helper.dll`, or Dodge CRT.
- Engine may arm PAGE_GUARD on FogCmp (`0x8D956F`) / TileCopy (`0x3B58B00`) for 16.3 visual FOW. That is overlay engine work, not a copy of the toolkit host. Integrity memcpy `0x3E77BD2` stays refused. latch3 / ov+4 are Debug fallbacks only (`EngineArmLatch3Fallback` / `EngineArmOv4Fallback`), not product Full Reveal.
- No sidebar tab named ScarToolkit. Trainer SCAR lives under Scripts (Alerts / Skirmish / Custom) and Debug.
- NativeEspData (`Documents\AOE4HSettings\NativeEspData\`) is the SCAR consumer of
  the C++ world feed. It is not a Run row.

## Inject

`internal\x64\Release\DllInjector.exe` APC `LoadLibraryW` of sibling `InternalInjector.dll`, then **exits**. `--watch` / `-w` waits on RelicCardinal. `Release` vs `Release_fowctrl` = same features, different `OutDir`. If Release is file-locked, inject the fowctrl copy. Do not load two InternalInjector images in one process.

## Two Memory tabs / menu header

Sidebar **Lobby → Memory** (`DrawNativeOverridesTab`) is identity, Dodge, spoof, reconnect, unofficial rejoin, skip-search CD. **Online → Camera / Radar / ESP** is a different tab (`DrawOnlineMemoryTab`, title `Online (Memory)`): zoom, radar, ESP, Full Reveal.

Opening Lobby Memory used to click-through **Force reconnect** on the same frame as the sidebar hit → Relic `LoginAsync` RVA `0x3109420` in the main menu (2026-09-03). Fix: ignore clicks for **3 frames**; log `[MEM] Memory tab opened — ignore clicks 3 frames (no LoginAsync)`.

Header `RA S1 A10 F0` is Relic AC window (`MpBypassGetWindowSnapshot`): slots / accum / flag. **Not** SCAR. Red when any of those is nonzero. `S1 A10 F0` is a single enqueue, not a kick pack (`S3 A600` / `S3 A240`). Red **Offline** pill is overlay Scar Trust (`ScarTrust_Offline`), not “not in a match”.

## Overlay natives (already in InternalInjector)

| Feature | Files | Notes |
|---|---|---|
| Full Reveal / Reveal Map | `maphack_fowctrl.cpp`, `engine.cpp` `EngineCrackFullReveal` | FOWCTRL1 `+8`/`+11` in this DLL |
| Camera zoom min/max | `zoom.cpp` | Autodeclinate `info+0x10`/`+0x14`. FOWCTRL1 `+16`/`+20` consumed as max-cap |
| 2D ESP | `esp.cpp` `EspDraw` | In-process D3D; no `ScarToolkit_ESP2D` HWND |
| Sheep / player ESP | `esp.cpp`, `radar.cpp` | `highlightSheep`, enemy boxes |
| Idle production alert | `radar.cpp` `RadarDrawIdleAlert` | `radarIdleAlert` |
| Resource / observer HUD | `radar.cpp` `RadarDrawObserverHud` | PlayerStock + census |
| World feed | `radar.cpp` SCAR bridge | `AOE4HOOK_WORLD_DATA` / `_STOCKS` / `_CENSUS` |
| Lobby identity / rank | `native_overrides.cpp` | aoe4world **profile_id** → Relic `getPersonalStat`. Steam **aliases** often empty. Overlay WinHTTP is **not** Relic ESS (game uses WinINet / RLink). Detected level/XP may fall back to identity when the heap scan is empty. |
| Force reconnect | `lobby_actions.cpp` | Lobby **«Переподключить серверы»** / Force reconnect = Relic `LoginAsync` RVA `0x3109420` (same path as the notification bell). UI thread. Does not hook the game HTTP stack. Official Relic `CanReconnect` only while the process lives. |
| Skip search cooldown | `lobby_actions.cpp`, `lobby_search_cooldown.h` | **On from inject; server acceptance still unverified.** Two client targets. (1) `IsAutomatchBanned` kind **4** in the profile account word (`model+0x13B0`, `account+272`): the model is identified by its evaluator slot `model+0xCB8 == 0x10D6310` (ctor `0x10CEAB0`), found by a read-only sweep of private RW memory on its own thread (8 s budget, stacks skipped, refused if the evaluator moved), cleared by `InterlockedCompareExchange` and the cached byte `+0xCC8` zeroed. `account+312` (`BannedTime`, shared with the other kinds) is never written. (2) A future deadline in the Automatch2 embedded Info (`root+0x17C0`, service+`0xD8`, Info+`0x158`). Reports last refusal (`result 11`) independently of writes. Off stops writing and puts nothing back. See [findings](findings/2026-09-29-search-cooldown.md). |
| Relay regions | `relay_failover.cpp`, `region_block.cpp`, `ui_debug.cpp` | Panel **Relay regions**. Retry + auto on TCP drop → `JoinSessionAsync` RVA `0x2EFC430` using login `relayServers` (URelayServerData stride 144). Match JSON has one `relayIP`. Not `StartLogin` / not `ResetSession`. Ranked: Relic list only, no fake peers. Azure region hop mid-lockstep is **unproven**. Auto drop uses Windows **TCP** table (`GetExtendedTcpTable`); UDP-only loss can miss. Firewall path: live `/32` of this snapshot, never Azure CIDR / hosts. **Session hold** toggle disables auto-retry to keep the current relay session alive in sandbox / custom lobbies. |
| Unofficial rejoin | `session_rejoin.cpp` | Writes `Documents\AOE4HSettings\Matches\rejoin_session.json` every 2 s; VEH crash flush (`SessionRejoinOnCrash` from `log.cpp`). Button **«Неофициальный rejoin»** = `LoginAsync`, no Leave. Auto LoginAsync on TCP drop (own session, skipped in menu). **Not** lockstep after process death. `MatchHeartbeat` RVA `0x7FEB10` is a sim tick. `WSADuplicateSocket` cannot outlive `ExitProcess` (MSDN). Host `KillAllDropped` RVA `0x6950F0` / `destructionFrame`. Ticket is not a world save. |
| Vs AI Save / Load | `stk_embedded.cpp` `save_match.scar` | Offline **Save / Load match** → `Event_SaveWithName` RVA `0x202B7D0`. Skirmish / vs AI only. Not a ranked world restore. `Matches\` journal is overlay stats, not simulation. |

AoM / Xbox status banners are **not** AoE4 ESS. AoE4 had a maintenance window **2 Sep 2026 21:00 UTC**.

## C2668 (`mp_bypass.cpp`)

MSVC **C2668** when anonymous-namespace helpers shared names with the public `MpBypass*` API (`MpBypassDataClear` / `MpBypassAutoClearEnabled`). Helpers are `*Ns` (`DataClearNs`, `AutoClearEnabledNs`, `SetAutoClearNs`, `DataRestoreNs`, `MaybeDataClearNs`); public wrappers call those, and other TUs use `::MpBypass*`. DualFlag behavior unchanged.

## Will not port

Dodge **RWX CRT**, `asset.php` helper mapper DllMain, Relic `VirtualProtectEx` of unrelated integrity sites, license/HWID.
In-process Dodge / Add AI live in `lobby_actions.cpp`. Autovill **SendInput** lives in `hotkeys.cpp` (hidden overlay). Kick/Lock Relic callees remain unresolved.
