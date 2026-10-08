# 2026-09-13 — Hosts: only FairPlay / report / Xbox-events telem

Scan of RelicCardinal 60644 `modules_runtime/RelicCardinal.exe.memory.bin` (147 050 496, RVA=file offset) plus live `warnings.log` (PID session 2026-09-13) and XSAPI/GDK. Goal: `hosts` deny **only** FQDNs whose whole host is trust / ban report / FairPlay / title telemetry / logging. Everything else stays off the deny list.

## Block (product)

```text
# AOE4H FairPlay begin
127.0.0.1 reputation.xboxlive.com
::1 reputation.xboxlive.com
127.0.0.1 vortex-events.xboxlive.com
::1 vortex-events.xboxlive.com
# AOE4H FairPlay end
```

Written by elevated `DllInjector` before APC (`internal/common/fairplay_hosts.cpp`). Overlay Install no-op if both FQDNs have v4+v6.

## IDA 2026-09-13 (same verdict)

GUI on `aoe4\gamesource\dump\ida-work\runtime_exe.i64` (60644 packed IDB will not open — `.nam` not a VA file). Session `4f6bd10b`, imagebase `0x7FF7A5500000`. Details: [ida-hosts-xref-confirm](2026-09-13-ida-hosts-xref-confirm.md).

- `reputation.xboxlive.com`: **0** Relic C-strings. `"SubmitReputationFeedback"` → `0x40D4E50` → `XAsyncBegin` `0x40EB180`.
- `vortex-events`: defined string is `"https://vortex-events.xboxlive.com"` RVA `0x5764F20`. Hex-Rays at `0x416CA70`: `strcpy` of that URL (Xbox in-game events). Host-only substring has 0 xrefs.
- Neighbor `"https://vortex-win.data.microsoft.com"` `0x5764F48` → `0x416E130` stays **off** hosts (Windows Diagnostic Data).
- ESS `"-api.worldsedgelink.com"` builder `0x3103180` (port 443). `reportMatch` path `0x65384E0` ← `0x300E030`.

## Protocol catalog (Relic process)

### HTTP / HTTPS (WinHTTP, WinINet, libHttpClient)

| FQDN / how built | Proto | Role | Hosts deny? |
|---|---|---|---|
| `reputation.xboxlive.com` (XSAPI, **0** Relic C-string hits) | HTTPS POST `/users/xuid()/feedback` + batch | FairPlay / reputation / Avoid Me. `SubmitReputationFeedback` `0x40D4E50` → `XAsyncBegin` `0x40EB180`. feedbackType table at `0x57617D8` | **yes** |
| `vortex-events.xboxlive.com` (`0x5764F36`, next to `xboxLive.InGame`) | HTTPS | Xbox in-game events (title telemetry) | **yes** |
| `vortex-win.data.microsoft.com` / `vortex.data.microsoft.com/collect/v1` | HTTPS | GDK + **Windows** Diagnostic Data | **no** (machine-wide) |
| `self.events.data.microsoft.com/OneCollector/1.0/` | HTTPS | Windows OneCollector | **no** |
| `settings.data.microsoft.com/.../telemetry/` | HTTPS | Windows telemetry config | **no** |
| `titleId.playfabapi.com` + `ED603` (`0x629CB79`) | HTTPS | PlayFab REST: SessionTicket / PlayFabID / EntityToken / RLinkProfileID — login **and** events | **no** (all-or-nothing) |
| `*-api.worldsedgelink.com` (template `-api.worldsedgelink.com` `0x653F9BD`; live `dr-activerelease1-api.worldsedgelink.com`) | HTTPS + WSS 443 | ESS login, create/join, **`/game/party/reportMatch`**, chat, presence WS | **no** (reportMatch shares host) |
| `sessiondirectory.xboxlive.com` | HTTPS | MPSD sessions | **no** |
| `user.auth` / `xsts.auth` / `device.auth` / `title.auth` / `title.mgt` / `sisu` / `auth.xboxlive.com` / `thirdpartytokens` | HTTPS | XBL / Steam link | **no** |
| `party.xboxlive.com` | HTTPS | Xbox party | **no** |
| `rta.xboxlive.com` `wss://.../connect` | WSS | Real Time Activity (presence subs) | **no** |
| `userpresence` / `presence` / `social` / `peoplehub` / `profile` / `privacy` / `notify` / `clubhub` / `achievements` / `leaderboards` / `userstats` / `statswrite` / `userposts` / `momatch` | HTTPS | Social, stats, Smart Match, invites | **no** |
| `api-dr.ageofempires.com` / `api-dev` / `api-flight` | HTTPS | World's Edge API | **no** |
| `battleserver.reliclink.com` | cert CN only | Legacy RelicLink TLS name | **no** |

Maelstrom `application/ms-maelstrom.v3+json;type=eventbatch` (`0x65328C0`, sender `0x2F4E310`) is a **Content-Type**, not a FQDN. Body rides ESS HTTP. Overlay spoofs only if body has FairPlay/Tampering/Cheater.

ESS `reportMatch` (`0x300E030`, path `0x65384E0`) is a **path** on the Relink API host. Hosts cannot cut it without killing create/join. Overlay spoof strips checksum keys when HTTP intercept is armed.

`logTelemetry` Relic CLI and overlay logs are **local files**, not a host.

### WebSocket

Live `warnings.log`: `WebSocketConnection` `host=dr-activerelease1-api.worldsedgelink.com port=443` — presence / automatch / invitations. Same ESS host family. **Not** in hosts.

XSAPI: `wss://rta.xboxlive.com/connect`. **Not** in hosts.

### TCP (non-HTTP)

Automatch JSON assigns `relayIP` + ports (example `20.90.13.208` 27014/27114/27214). Relic `BattleServerRelay` / `RL_BATTLESERVER_USE_RAW_SOCKETS`. Lockstep / QoS, not FairPlay. Overlay region block uses live `/32` firewall, **never** hosts.

### UDP

`Socks::SendQueue` strings sit next to `UDP`/`TCP` in RelicLink `SocketManager.cpp` — Relic's socket helper class, **not** SOCKS5. Battle-server / lockstep UDP. **No** hosts entry.

### SOCKS

13 image hits: `Socks::ReceiveQueue`, `Socks::Free`, `SockStatus: sockets` — RelicLink C++ type. Zero SOCKS5 proxy URLs.

### GRE / IPIP

`IPPROTO_GRE`: **0** hits in 60644 image. Unused.

### Trust / ban that is not HTTP

Relic RA kick (hasher / Enqueue / KickCtor) is **local**. Steam `VACBanned` is XOR name decrypt, not an HTTP query. Do not hosts-block `steamcommunity.com`.

## Why not more Xbox telem hosts

`vortex-win` / `vortex.data.microsoft.com` / `self.events.data.microsoft.com` appear in the same XSAPI blob as `vortex-events`, but they are also Windows Diagnostic Data. `hosts` is system-wide. Deny list stays Xbox-title-specific.

## Files

- `AOE4HOOK/internal/common/fairplay_hosts.cpp` / `.h`
- `AOE4HOOK/tools/fairplay_hosts.ps1`
- `AOE4HOOK/internal/DllInjector/main.cpp` print
- overlay log `[RA] FairPlay hosts block ON reputation+vortex-events v4+v6`
