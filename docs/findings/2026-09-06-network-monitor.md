# 2026-09-06 — Network Monitor tab + interceptable HTTP catalog

Overlay tab: **System → Network Monitor** (`MenuTab_Network`).  
Rules: `Documents\AOE4HSettings\Config\network_monitor.ini` (async write; not Present I/O).  
Hooks: `http_intercept.cpp` WinHTTP / WinINet / libHttpClient export bodies only. **No Relic `.text`.** **No Relic IAT `0x20DE00AD`.** Cloak **off**.

Restored onto stable `main` (`2bfac27`) from `cb70dba` — tab + WinHTTP/WinINet/libHttpClient hooks only.  
PID 27072: 14-byte steal on `WinHttpConnect` caused JUMPOUT; `MeasureStolen` must not fall back to 14.  
Do not hook Relic `.text` or Relic IAT `0x20DE00AD`. Cloak off. Hooks stay default-off unless `AOE4H_HTTP_INTERCEPT=1`.

IDB: `runtime_exe.i64` imagebase `0x7FF7A5500000` (session `a1220dbc`). RVAs only below.

## Hook arm (default OFF after PID 27072)

`HttpInterceptInstall` plants **zero** export bodies unless compile-time `AOE4H_HTTP_INTERCEPT=1` **or** process env `AOE4H_HTTP_INTERCEPT=1`.  
`MeasureStolen` never falls back to 14 bytes (WinHttpConnect is 13 push/rex then `LEA`; a 14-byte `FF 25` splits it → JUMPOUT class). No `LoadLibrary` of winhttp/wininet at boot. HC `PerformAsync` is **fail-open** (always call original).

Boot: `[RA] http intercept OFF (fail-open after PID 27072; set AOE4H_HTTP_INTERCEPT=1 to arm)`  
or `[RA] http intercept ON hooks=N winhttp=… wininet=… libhc=…`

The tab still edits/persists rules when hooks are off. Status line: `hooks N  winhttp=  wininet=  libhc=  armed|not armed` plus allow/deny/spoof counts.

## Policy order

1. **Allow** (first match) wins over deny.  
2. **Deny** — rewrite body `{}` on WinHTTP/WinINet; HC body `{}` then **still Perform** (fail-open).  
3. **Spoof** — rewrite and send (`{}` / strip keys / `{"events":[]}` / replace type string).  
4. Else **allow**.

Empty host/path/body fields on a rule are wildcards. `body` + `bodyAnd` are AND.

## Default rules (match pre-UI `Classify`)

| Group | id | Match | Action | On |
|-------|-----|--------|--------|----|
| Allow | `xbl_login_live` | host `login.live.com` | pass | yes |
| Allow | `xbl_user_auth` | host `user.auth.xboxlive.com` | pass | yes |
| Allow | `xbl_xsts` | host `xsts.auth.xboxlive.com` | pass | yes |
| Allow | `xbl_device_auth` | host `device.auth.xboxlive.com` | pass | yes |
| Allow | `xbl_title_mgt` | host `title.mgt.xboxlive.com` | pass | yes |
| Allow | `xbl_title_auth` | host `title.auth.xboxlive.com` | pass | yes |
| Allow | `xbl_sisu` | host `sisu.xboxlive.com` | pass | yes |
| Allow | `xbl_party` | host `party.xboxlive.com` | pass | yes |
| Allow | `xbl_sessiondir` | host `sessiondirectory.xboxlive.com` | pass | yes |
| Allow | `ess_party_create` | path `/game/party/create` | pass (also matches `createOrReportSinglePlayer`) | yes |
| Allow | `ess_party_join` | path `/game/party/join` | pass | yes |
| Allow | `ess_session` | path `/game/session` | pass | yes |
| Allow | `ess_login` | path `/login` | pass | yes |
| Allow | `ess_auth` | path `/auth` | pass | yes |
| Deny | `fairplay_reputation` | host `reputation.xboxlive.com` | `{}` | yes |
| Deny | `fairplay_feedback` | path `/feedback` | `{}` | yes |
| Spoof | `ess_report_match` | path `/game/party/reportMatch` | strip `appBinaryChecksum,dataChecksum,modDLLChecksum,checkSums` | yes |
| Spoof | `telem_eventbatch_fp` | body `eventbatch` AND `FairPlay` | `{"events":[]}` | yes |
| Spoof | `telem_maelstrom_fp` | body `maelstrom` AND `FairPlay` | `{"events":[]}` | yes |
| Spoof | `telem_eventbatch_tamper` | body `eventbatch` AND `Tampering` | `{"events":[]}` | yes |
| Spoof | `telem_eventbatch_cheater` | body `eventbatch` AND `Cheater` | `{"events":[]}` | yes |
| Spoof | `fairplay_type` | body `FairPlayTampering` | replace type → empty | yes |

No blanket `xboxlive.com` allow (that would win over reputation deny).

## Catalog — visible on WinHTTP / WinINet / libHttpClient

Relic imports (autoscan): WINHTTP (W APIs), WININET (`InternetConnectA`, `HttpOpenRequestA`, `HttpSendRequestW`), `libHttpClient.Win32` (`HCHttpCallRequest*` / `PerformAsync`). Overlay also uses WinHTTP (`data.aoe4world.com`, `aoe-api.worldsedgelink.com`).

Intercept hooks **A and W** WinINet (Relic ESS is A-connect / A-open / W-send). Without A, host+path slots miss and `reportMatch` cannot be distinguished from create/join checksums.

### FairPlay / reputation — default **Deny**

| Host / path | Where | Stack | Notes |
|-------------|-------|--------|-------|
| `reputation.xboxlive.com` `POST /users/xuid(%s)/feedback` | XSAPI `SubmitReputationFeedback` → `XAsyncBegin` `0x40EB180` | **libHttpClient** (typical) | Host **not** a Relic C-string (0 IDA hits). Path `/feedback` is in Relic (`0x7FF7AAC61799`). |
| body `FairPlayTampering` / `FairPlayCheater` / `feedbackType` | mapper `0x411F380` + JSON `0x411ED00` | same POST | Trust clean still zeros `.rdata` FairPlay* (`xbox_enforcement`). |

Do **not** hook Relic SEND RVAs `0x2EFD750` / `0x30B61F0` / `0x40D5030` / `0x40D4E50` / `0x40EB180`.

### ESS Relink (`worldsedgelink.com`) — path-filter only

Host XOR `0x300F630` (`i ^ 0xD6`). Literal `worldsedgelink.com` at RVA `0x653F9BD`. **Never** hosts-block `aoe-api.worldsedgelink.com` (create/join / community).

| Path | IDA VA (this IDB) | Default |
|------|-------------------|---------|
| `/game/party/reportMatch` | `0x7FF7ABA384E0` RVA `0x65384E0` SEND `0x300E030` | **Spoof** strip checksums |
| `/game/party/createOrReportSinglePlayer` | `0x7FF7ABA37DE8` | **Allow** (substring `/game/party/create`) |
| `/game/party/sendMatchChat` | `0x7FF7ABA37F10` | Allow |
| `/game/party/finalizeReplayUpload` | `0x7FF7ABA380C8` | Allow |
| `/game/party/peerUpdate` / `peerAdd` / `updateHost` | `0x7FF7ABA38480` / `…530` / `…568` | Allow |
| `/game/advertisement/host` `join` `leave` `update` `startObserving` … | `0x7FF7ABA2C998`…`CF38` | **Allow** (matchmaking) |
| `/game/account/getProfileProperty` `FindProfiles` | `0x7FF7ABA35600` / `628` | Allow (login/profile) |
| `/game/item/*` store / inventory / loadouts | `0x7FF7ABA29F50`… | Allow |
| `/game/leaderboard/applyOfflineUpdates` | `0x7FF7ABA29F98` | Allow |
| `/game/cloud/getTempCredentials` | `0x7FF7ABA30B20` | Allow |
| `/game/relationship/setPresence` `getPresenceData` … | `0x7FF7ABA372E8`… | Allow |
| `/game/chat/*` | `0x7FF7ABA36EB8`… | Allow |
| `/game/playerreport/reportUser` | `0x7FF7ABA36ED8` | **Allow** (player report UI, not proven FairPlay) |
| `/community/leaderboard/getPersonalStat` | overlay `native_overrides.cpp` | Allow (overlay WinHTTP) |

No literal `/game/party/join` or `/game/session` in this IDB (XOR or unused). Allow rules kept for current `Classify` parity.

Checksum serializer `0x2E23930` (`dataChecksum` / `appBinaryChecksum` / `modDLLChecksum`) also goes out on create/join — **do not** strip on body keys alone.

### Maelstrom / PlayFab telem — spoof **only** FairPlay/tamper/cheater

| Signal | RVA / VA | Default |
|--------|----------|---------|
| Content-Type `application/ms-maelstrom.v3+json;type=eventbatch;charset=utf-8` | `0x65328C0` sender `0x2F4E310` | spoof empty events **if** body also has FairPlay/Tampering/Cheater |
| `titleId.playfabapi.com` | `0x6532238` | Allow unless those body needles |
| PlayFab DLL | **none** | host string only |

Do not hook Relic `0x2F4E310`. Do not hook PlayFab Party login.

### XBL login / title / session — default **Allow**

IDA strings (this IDB): `sessiondirectory.xboxlive.com`, `title.mgt`, `user.auth`, `xsts.auth`, `device.auth`, `title.auth`, `sisu.xboxlive.com/connect/client/Steam`, `xboxlive.com/users/me/accountlink`, `…/networks/Steam/link`.  
`login.live.com` / `reputation.xboxlive.com` / `party.xboxlive.com` — **0** Relic literals (XSAPI constructs). Still allow-listed so a broad deny cannot break login.

### Overlay / Steam / other (same stacks)

| Traffic | Stack | Default |
|---------|--------|---------|
| `data.aoe4world.com` `/images/…` | overlay WinHTTP (`ui_icons.cpp`) | Allow (shows in Intercept) |
| `aoe4world.com` profile | overlay WinHTTP (`native_overrides.cpp`) | Allow |
| Relic WinHTTP `GET /statistics` (root-cert probe) | Relic WinHTTP | Allow if seen |
| `steamcommunity.com/profiles/` | Relic string `0x7FF7AB7F2E58` | **not proven** on WinHTTP; Allow if it appears |

### Not visible here (do not Relic `.text` hook)

| What | Why |
|------|-----|
| RA hasher / JUMPOUT / KickCtor / 45E8 | local, no WinHTTP/WinINet/HC |
| Steam VAC / `VACBanned` | `steam_api64` IAT + XOR name (`xbox_enforcement`), not HTTP |
| PlayFab Party XDK if it bypasses HC | no PlayFab DLL; if it uses raw sockets it will not appear |
| Xbox XDK that skips libHttpClient | not in these three modules |
| Relic IAT `0x20DE00AD` | refused (hasher-visible) |
| TLS-pinned bodies (mitmproxy) | optional/unpinned only; not this tab |

## UI

System sidebar **Network Monitor**. Sub-tabs (i18n): Intercept / Spoof / Deny / Allow → Перехватчик / Спуфер / Запрещатель / Разрешатель.

1. **Intercept** — ring 256: time, method, host, path, result, short body **key names** (no tokens), rule id. Pause / clear / filter.  
2. **Spoof** — per-rule enable + rewrite kind.  
3. **Deny** — host/path/body substring.  
4. **Allow** — wins over deny.

Persist: `QueueUserWorkItem` after rule edits. Load at `HttpInterceptInstall` (EngineStart). Shutdown flushes.

## Files

- `InternalInjector/http_intercept.cpp` / `.h`
- `InternalInjector/ui_network.cpp`
- `InternalInjector/ui.cpp` / `ui_internal.h` / `ui_i18n.cpp`
- `Documents\AOE4HSettings\Config\network_monitor.ini` (created on first load)
