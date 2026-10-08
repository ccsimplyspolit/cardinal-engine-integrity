# 2026-09-13 — OP20 leftover at match start: overlay before Relic Lua TLS

Build `16.3.11308.0`. Overlay log `Documents\AOE4HSettings\Logs\aoe4_internal.log`.
RVAs only. Preferred ImageBase `0x140000000`. Do not plant Watcher, sibling,
7AB0, FlushArm, Enqueue, EventSchedule.

## Observation (13:57 log — ungated image)

Boot `13:48:08` (no `luaGate2500` stamp). Ranked 2v2 mission live `13:57:15`.

| Time | Artifact |
|---|---|
| 13:57:15.876 | Relic `Scenario Lua System started` |
| 13:57:15.877 | overlay quiet `ScarDoStringRaw` from DXGI Present (`ents=0 live=1`) |
| 13:57:15.900 | radar collect worker (`readFaults` tens of thousands) |
| 13:57:16.878 | auto DualFlag `0x0100→0x0001` (Present / `MaybeDataClear`) |
| 13:57:17.335 | `ai_lock_army.lua` + DualFlag |
| 13:57:17.337 | `eco_ai_on` |
| 13:57:17.346 | RA window `slots=1` tag=`40230001` kind=3 a2=0 `+10=0x56F9C88` |
| 13:57:17.356 | overlay `WindowClear` (does not cancel KickCtor) |
| 13:59:43 | process gone, no `[CRASH]` / `DEVICE_REMOVED` / BugSplat |

Same class as 12:59 / 13:03 in
[2026-09-13-ra-delayed-kick-silent-death.md](2026-09-13-ra-delayed-kick-silent-death.md).
Classifier `Relic canned, not DoString` is **tag taxonomy** (not D02C
`80240001`), not “overlay idle”. `overlayDoStringSinceLua=5` on the drain
line: overlay Lua already ran.

`kScarLuaAfterLoadMs=2500` did not wait: Mission Start in `warnings.log`
backdated `g_luaLoadSeenAt = now - 2500`, so `ScarLuaReloadReady()` was true
at Lua System + 1 ms.

Present “skip overlay” only skipped **draw**. `UiServiceScripts` /
`ScarEnsureVmProbed` / radar ran **before** `OverlayGuardShouldSkip`.

## Observation (14:56 log — `luaGate2500+hold4`)

Boot `14:55:28.798` stamp `luaGate2500+hold4` into Relic pid 17108 (menu).
Online 1v1 vs Xbox `BadPatto4784` (Lanzerxyz Zhu Xi). Warnings
`Documents\My Games\Age of Empires IV\warnings.log`.

| Time | Artifact |
|---|---|
| 14:56:48.821 | Relic `Loading step: [Scenario Lua System]` |
| 14:56:49.064 | overlay `[SCAR] … block DoString/DualFlag 2500 ms` |
| 14:56:49.066 | `why=lua-system` **slots=0 flag=0** `overlayDoStringSinceLua=0` |
| 14:56:53.134 | Relic `Loading step: [OnEndLoad]` (peer load still running) |
| 14:56:57.239 | Relic `GAME -- Starting mission` |
| 14:56:57.854 | `why=lua-settle` **slots=0 flag=0** `overlayDoStringSinceLua=0` |
| 14:56:57.855 | quiet probe **posted to window** tid=27408 (not Present tid=23956) |
| 14:56:57.869 | radar collect worker starts (hold over) |
| 14:56:57.874 | `why=first-dostring` **slots=0** `overlayDoStringSinceLua=0` |
| 14:56:57.880 | `[SCAR] cmd#1` bridge DoString ok |
| 14:56:58.721 | OP20 leftover `tag=40230001` kind=3 a2=0 `+10=0x56F9C88` `overlayDoStringSinceLua=3` |
| 14:56:59.883 | `why=dualflag-before` **slots=1** (DualFlag **after** the slot) |

Hold lasted until Starting mission, not Lua System+2500: Lua System was
already 8.2 s old when `GAME -- Starting mission` landed (peer
LoadArbitrator). `MatchStartHold` then used `g_luaLoadSeenAt` (Lua System
time), so the 2500 ms clock had expired and overlay resumed **0.62 s after
Starting mission**. OP20 landed **1.48 s after Starting mission** /
**0.87 s after first overlay DoString**. DualFlag did not write the slot.

No Present `ScarDoStringRaw` at Lua System +1 ms. No DualFlag / collect /
Marks scan during the hold. Gate requirement for “before Relic Lua TLS” is
met. Post-gate overlay still overlaps Relic’s ~1.5 s post-mission window.

## Observation (15:06 log — `luaGate2500+hold5`)

Boot `15:04:31.237` stamp `luaGate2500+hold5` into Relic pid 19352.
Online 1v1 Zhu Xi vs English. Warnings:

| Time | Artifact |
|---|---|
| 15:05:54.286 | Relic `Loading step: [Scenario Lua System]` |
| 15:05:54.410 | overlay hold 2500 ms; `why=lua-system` **slots=0 flag=0** `overlayDoStringSinceLua=0` |
| 15:05:57.990 | Relic `OnEndLoad` (does **not** start the hold5 clock) |
| 15:06:00.247 | Relic `GAME -- Starting mission` |
| 15:06:03.002 | `why=lua-settle` **slots=0 flag=0** `overlayDoStringSinceLua=0` (~2.75 s after Starting mission) |
| 15:06:03.004 | quiet probe **posted to window** tid=22524 (not Present tid=5136) |
| 15:06:03.006 | `why=first-dostring` **slots=0** |
| 15:06:05.003 | `why=dualflag-before` **slots=0 flag=0** DualFlag `0x0100→0x0001` |
| 15:06:05.005 | `why=dualflag-after` **slots=0 flag=0** |
| 15:06:09.705 | MapHack ON (after DualFlag; no leftover) |
| ≥15:07:13 | **no** `40230001` / OP20 leftover line (RaWatch 250 ms; T+73 s past Starting mission) |

14:56 OP20 was T+1.48 s after Starting mission with overlay already in Lua.
15:06 overlay stayed idle through that window. Relic did **not** Enqueue.
Process still in-match (not the 3 min KickCtor death).

## Observation (23:04 log — `luaGate2500+hold5+wasStrip`)

Boot `22:59:27` into Relic pid **8060**. Ranked 1v1 Zhu Xi vs chinese
`jason0347`. Same hold5 (Starting mission+2500). Do **not** extend that hold.

| Time | Artifact |
|---|---|
| 23:04:35.367 | Relic `GAME -- Starting mission` |
| 23:04:38.152 | `why=lua-settle` **slots=0 flag=0** |
| 23:04:38.168 | cmd#1 `bridge` len=160 (TWD, same hashes as 15:06) |
| 23:04:38.180 | cmd#2 `bridge` len=367 + collect worker (same as 15:06) |
| 23:04:38.929 | cmd#3 **world-feed** `bridge` len=8482 `SCAR bridge mode=full simTick=22 frozen=1` |
| 23:04:39.188 | OP20 leftover `tag=40230001` `overlayDoStringSinceLua=3` DualFlag still `0x0000` |
| 23:04:40.173 | DualFlag `0x0100→0x0001` **after** the slot |
| 23:08:14.411 | last overlay line; process gone; no `[CRASH]` / WER / BugSplat |

15:06 first `SCAR bridge: mode=full` was **15:07:04.806** (T+61 s, simTick=514).
DualFlag at 15:06:05 with slots=0. cmd#1/#2 TWD bridges were on both matches.

The leftover writer is the **early world-feed snapshot**, not DualFlag and not
the 2500 ms settle being too short. Overlay gate: `RadarScarBridgeTick` /
`PublishScarSnapshot` wait `MpBypassMatchStartDualFlagDone()`. Do not plant
Enqueue. Do not WindowClear.

## Observation (23:28 log — `luaGate2500+hold5+wasStrip+wfAfterDf`)

Boot `23:25:28` into Relic pid **27332**. Warnings
`GAME -- Starting mission` **23:28:14.455**. DualFlag on. No hold8.

| Time | Artifact |
|---|---|
| 23:28:09.045 | `why=lua-system` **slots=0 flag=0** |
| 23:28:14.735 | `why=starting-mission` **slots=0 flag=0** |
| 23:28:17.230 | `why=lua-settle` **slots=0 flag=0** |
| 23:28:17.241 | cmd#1 `bridge` len=160 hash=`0x1CA9D724` (TWD) |
| 23:28:17.249 | cmd#2 `bridge` len=367 hash=`0x150991A5` (TWD) |
| 23:28:19.242 | cmd#3 `ai_lock_skip_map` (not world-feed) |
| 23:28:19.242 | DualFlag-before **slots=0 flag=0** `overlayDoStringSinceLua=3` |
| 23:28:19.244 | DualFlag-after **slots=0 flag=0** |
| 23:29:20.722 | first `SCAR bridge mode=full` simTick=528 (T+61 s after Starting mission) |
| ≥23:33:08 | Relic **alive** pid 27332; **no** `40230001` / OP20 / `[CRASH]` (T+4.9 min) |

Same order as 15:06. 23:04 cmd#3 was the 8482 B snapshot before DualFlag.

## Finding

13:57: overlay `Game_ScarDoString` and DualFlag ran on the DXGI thread while
Relic’s window-thread Scenario Lua TLS was still coming up.

14:56: Lua-init window is **empty**. Relic `RA_Enqueue`s OP20 ~1.5 s after
`GAME -- Starting mission` **if** overlay Lua/radar resume in that window.

15:06 hold5 (`Starting mission`+2500 ms): overlay idle through that 1.5 s
window; DualFlag after T+5 s; **slots stay 0**. Overlay never calls Enqueue.

23:04 same hold5: leftover **259 ms after cmd#3 world-feed** (8482 B), DualFlag
still unset. 15:06 DualFlag ran **before** any world-feed. Relic `sub_3DDB29C`
is tripped by that early snapshot, not by TWD cmd#1/#2 and not by a short
settle. Do not lengthen `kScarLuaAfterLoadMs`.

## Relic writer of this leftover (named + reversed body)

Named `RA_Enqueue` RVA `0x3DD2550`
(`gamesource/src/readable/named/RA_Enqueue_0x3DD2550.c`,
`gamesource_unp_humanized/named/RA_Enqueue_0x3DD2550.c`) writes the window.

Named `RA_IatScan_7AB0` RVA `0x3DD7AB0` (`gamesource/src/readable/named/RA_IatScan_7AB0_0x3DD7AB0.c`,
`gamesource_unp_humanized/named/RA_IatScan_7AB0_0x3DD7AB0.c`) dispatches on
`a4`. After `a4 > 0xE`, `v207 = a4 - 15` then five successful decrements
reach `v212 == 0` → **`a4 == 20` (OP20)** → `sub_3DDB29C()` (RVA `0x3DDB29C`).
That callee’s reversed body (`reversed/03D00000/sub_3DDB29C_0x3DDB29C.c`):

```c
RA_EventSchedule(v3, v2, 0, 532480, 0);
RA_Enqueue(v9, 0, 0x40230001u, 3, v11, v12, v13);  // a2=0, kind=3
```

`unk_56F9C58` in that body sits 0x30 below live slot `+10=0x56F9C88` (same
`.rdata` neighborhood). D02C fail pack is a **different** tag (`0x80320001` /
FoW `80240001`).

Do **not** plant 7AB0 / B29C / EventSchedule / Enqueue. Overlay delay does not
NOP Relic’s callee; it keeps overlay out of the window that arms it.

## Attribution

| Layer | Claim | Status |
|---|---|---|
| Observation | 13:57: overlay DoString + DualFlag at Lua System +1 s, then OP20 | supported |
| Observation | Slot bytes match `RA_Enqueue(0, 0x40230001, 3)` | supported (named/reversed + live tag/kind/a2) |
| Observation | 14:56 hold4: lua-system/settle `slots=0`; OP20 1.48 s after Starting mission, DualFlag after the slot | supported |
| Observation | 15:06 hold5: lua-system / lua-settle / first-dostring / dualflag all `slots=0 flag=0`; no OP20 by T+73 s+ | supported |
| Observation | 23:04 hold5: settle slots=0; world-feed 8482 B at settle+0.78 s then OP20; DualFlag after; KickCtor 23:08:14 | supported |
| Observation | 23:28 wfAfterDf: DualFlag slots=0 then first mode=full T+61 s simTick=528; no OP20; alive T+4.9 min | supported |
| Finding | Overlay ran before window-thread Lua settle on 13:57 | supported |
| Finding | Lua-System+2500 expires before Starting mission on slow peer load; overlay then hits Relic’s ~1.5 s post-mission window | supported (14:56) |
| Finding | Starting-mission+2500 is **not** enough if world-feed publishes before DualFlag | supported (23:04 vs 15:06) |
| Attribution | Overlay Present DoString **is** Relic’s Enqueue | **not** supported |
| Attribution | Early world-feed `PublishScarSnapshot` trips 7AB0 `a4=20` → `0x3DDB29C` | supported (23:04 cmd#3 vs 15:06 T+61 s first full bridge) |
| Remaining | World-feed immediately after DualFlag (no 61 s interval) | no signal (23:28 first full still T+61 s) |

## Overlay gate (this tree)

Boot stamp: `luaGate2500+hold5+wasStrip+wfAfterDf`. Do not load two images.

- Mission Start does **not** skip `kScarLuaAfterLoadMs` (2500 ms). Do **not**
  stretch that hold to hide leftover.
- Settle clock is `g_matchStartedAt` from `GAME -- Starting mission` only.
  `OnEndLoad` does **not** start it (14:56: that line is still peer load).
- `ScarDoStringRaw` refuses unless `OnRelicWindowThread()` (hwnd or not).
- After Scenario Lua System, `ScarDoStringRaw` / CRT helper refuse
  `MatchStartHold()` (`detail=refused (lua settle)`).
- Quiet probe `PostMessageW(WM_SCAR_BRIDGE_EXECUTE)`, never Present
  `Game_ScarDoString`. `ScarEnsureVmProbed` hits `MatchStartHold` before
  `ScarInMatchWorld` (no TLS probe during hold).
- Auto DualFlag: `ScarMatchStartHold` then live world + window tid +
  `ScarVmIsLive`. DualFlag runs **after** a successful DoString, not before.
- World-feed `RadarScarBridgeTick` / `PublishScarSnapshot` wait
  `MpBypassMatchStartDualFlagDone()` (23:04 leftover). TWD cmd#1/#2 stay.
- Radar collect / draw / minimap wait `ScarMatchStartHold`.
- DXGI Present `holdMatchStart` is `ScarMatchStartHold()` (warnings.log
  only). Overlay draw skipped (`skip || holdMatchStart`).
- Leftover watch **logs only** (no `WindowClear`). KickCtor already armed.

23:28 wfAfterDf live result is **(1)**: DualFlag `slots=0` before any
`mode=full`; no `40230001`; process alive past Starting mission+4 min.
23:04 leftover was world-feed **before** DualFlag. Case (2) canned-while-idle
(`overlayDoStringSinceLua=0`) did not happen.

Read-only gate lines: `lua-system`, `starting-mission`, `lua-settle`,
`first-dostring`, `dualflag-before`, `dualflag-after`.

`starting-mission` is the Relic `GAME -- Starting mission` line (hold5 clock).
If OP20 appears after that line with `overlayDoStringSinceLua=0` (RaWatch
still runs during hold), Relic canned `0x3DDB29C` and a delay cannot prevent it.

Inject `internal\x64\Release\InternalInjector.dll` only (not a second image).
