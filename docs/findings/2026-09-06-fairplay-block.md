# 2026-09-06 — FairPlay / reportMatch send-block (default ON)

IDA store + call graph: [2026-09-06-ida-ra-analysis.md](2026-09-06-ida-ra-analysis.md).  
Autoscan: `K:\aoe4_dlc\dumps\RelicCardinal_60644_20260906_full_analysis\ida\autoscan_report.md`.  
Layer split: [2026-09-06-fairplay-vs-ra.md](2026-09-06-fairplay-vs-ra.md).

Module: `InternalInjector/xbox_enforcement.cpp`. **Cloak stays OFF** (BSOD `0x10E`). No hasher / 45E8 / KickCtor / `--ra-veh`.

## What Relic actually is

| Name | What it is here | Product VAC / RA kick? |
|------|-----------------|------------------------|
| FairPlayTampering (enum 2) | Xbox `XblReputationFeedbackType` string + **SEND** `SubmitReputationFeedback` → `XAsyncBegin` → `POST reputation.xboxlive.com` `/users/xuid(%s)/feedback` | No. Reputation / Avoid Me. **Also** the only named “trust” input: mapper + JSON type string. No separate `TrustFactor` func in this binary. |
| FairPlayCheater (enum 1) + other FairPlay* | Same mapper / same submit chain | Same POST family |
| `VACBanned` | XOR-decrypt Steam **callback name** at CRT init `0x28F770` (string `0x781E311`). Steam IAT is `SteamUser023`. **No** `ISteamUser::BIsVACBanned` vfunc / import. | Not Steam VAC. Still spoofed as not-banned (name + IAT wrap). |
| ESS `reportMatch` | `0x300E030` `POST /game/party/reportMatch` + `checkSums` | Match HTTP, not Exit |
| `INTEGRITYCHECK` | Log phrase `0x65393A2`, **0 xrefs** | No opcode to hook |
| Maelstrom `0x2F4E310` | eventbatch HTTP Content-Type | Telemetry, not login |
| PlayFab Party strings | Chat/session | **Not** hooked (would break login/chat) |

## Write path (HTTP intercept — not Relic `.text`)

**Do not** 14-byte jmp Relic `.text` at `0x2EFD750` / `0x30B61F0` / `0x40D5030` / `0x40D4E50` / `0x300E030` / `0x2F4E310`. Hasher `0x3E57050` raw-loads that image → PID **37124** BEX64 `0xC0000005` RIP=0 ([inject-crash](2026-09-06-inject-crash.md)).

Default-ON: hook **winhttp.dll / wininet.dll / libHttpClient.Win32.dll export bodies** (`http_intercept.cpp`). Process-global, outside Relic image. Not Relic IAT `0x20DE00AD`. Not CRT memcpy. Not mitmproxy (TLS pin).

| Filter | Action | Log |
|--------|--------|-----|
| `reputation.xboxlive.com` + `/feedback` / FairPlay* | rewrite body `{}` (HC Perform skip on drop) | `[RA] http drop` + key names |
| `POST /game/party/reportMatch` | strip `appBinaryChecksum` / `dataChecksum` / `modDLLChecksum` / `checkSums` | `[RA] http rewrite` |
| eventbatch + FairPlay/tamper/cheater only | `{"events":[]}` | `[RA] http telem-drop` |
| XBL login / title / session / create-join | **pass** | — |

Hosts fallback (fail-closed, all-or-nothing): `127.0.0.1 reputation.xboxlive.com` via `AOE4HOOK/tools/fairplay_hosts.ps1 -Apply` (admin). Never `*.xboxlive.com`. Never `aoe-api.worldsedgelink.com` (reportMatch is path-filtered on WinINet).

**Not hooked (Relic RVAs — leave live)**

| RVA | Why |
|-----|-----|
| `0x40EB180` `XAsyncBegin` | Shared XSAPI (18+ callers) — login |
| Mapper `0x411F380` / JSON `0x411ED00` | local only |
| Checksum serializer `0x2E23930` | create/join |
| Hasher / 45E8 / KickCtor / JUMPOUT | RA local |

## Read / trust path (clean)

No `TrustFactor` / `XblReputation` **GET** site in the autoscan. Relic’s local “am I FairPlay?” input is the **type string** the mapper writes into JSON / strcmp.

Default-ON: first byte of each FairPlay* literal zeroed (`.rdata`):

`0x57617D8` … `0x57619C8` (`FairPlayTampering` `0x5761800`, `FairPlayCheater` `0x57617F0`, siblings).

Mapper still runs; FairPlay cases produce empty names → readers see **not tampering / not cheater**.

## VACBanned spoof

- `.data` name `0x781E311` first byte cleared after CRT decrypt (no “VACBanned” token).
- Relic IAT: `SteamInternal_FindOrCreateUserInterface` (log `SteamUser*` version; no vfunc to swap on 023). `SteamAPI_RegisterCallback` pass-through (do not swallow login callbacks).
- Log: `[RA] VACBanned spoof ON`.

## Monitor lines (boot)

```
[RA] http intercept ON hooks=N winhttp=1 wininet=1 libhc=0/1 (no Relic .text; no Relic IAT; mitmproxy optional/unpinned only)
[RA] FairPlayTampering block ON http=1 hosts=0/1 text=0 (no Relic .text jmp; XAsyncBegin 0x40EB180 not hooked)
[RA] FairPlay trust clean ON strings=1 (mapper 0x411F380 is enum-only, not POST)
[RA] VACBanned spoof ON iat=1 name=1 (SteamUser023: XOR name, not ISteamUser::BIsVACBanned)
[RA] xbox enforcement cloak=off hasher=off text=0
```

Hit lines: `[RA] http drop|rewrite|telem-drop` with host/path/key names (not wholesale JSON / tokens).

## Live confirm

1. Inject `Release\InternalInjector.dll` (cloak still off — no `AOE4H_RA_CLOAK`). Do not use a DLL that logged Relic `.text` FairPlay jmps.
2. Boot: `[RA] http intercept ON` and `text=0`. Optional: run `fairplay_hosts.ps1 -Apply` as admin if `hosts block OFF write_fail`.
3. FairPlay: log `http drop` for `/feedback`; no live reputation POST body.
4. Match end: `http rewrite` for `/game/party/reportMatch` (checksum keys stripped).
5. XBL login / matchmaking still works.

## Files

- `AOE4HOOK/internal/InternalInjector/http_intercept.cpp` / `.h`
- `AOE4HOOK/internal/InternalInjector/xbox_enforcement.cpp` / `.h`
- `AOE4HOOK/tools/fairplay_hosts.ps1`
- Wired from `engine.cpp` `EngineStart` / `EngineShutdown` (not `ra_hide`, not `mp_bypass`)
