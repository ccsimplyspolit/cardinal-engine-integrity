# 2026-09-13 — DllInjector hosts block before APC

Elevated `DllInjector.exe` writes the FairPlay `hosts` block **on open**, before Relic PID wait and before APC `LoadLibraryW`. Overlay `XboxEnforcementInstall` still calls the same helper after inject; complete dual-stack block is a no-op.

Shared code: `AOE4HOOK/internal/common/fairplay_hosts.cpp`. Script: `AOE4HOOK/tools/fairplay_hosts.ps1` (same markers / dual-stack).

## Block written

```text
# AOE4H FairPlay begin
127.0.0.1 reputation.xboxlive.com
::1 reputation.xboxlive.com
127.0.0.1 vortex-events.xboxlive.com
::1 vortex-events.xboxlive.com
# AOE4H FairPlay end
```

IPv4-only leftover (pre-this) is incomplete: marked section is stripped and rewritten. Unrelated `hosts` lines stay.

FQDN list after protocol catalog ([2026-09-13-hosts-trust-telem-catalog.md](2026-09-13-hosts-trust-telem-catalog.md)): `reputation.xboxlive.com` (FairPlay POST) and `vortex-events.xboxlive.com` (Xbox in-game events). Dual-stack `127.0.0.1` + `::1`. ESS / PlayFab / vortex-win / SOCKS / GRE are not deny entries.

## Not in hosts (all-or-nothing; path-filter lives in HTTP intercept)

- XBL auth / session: `login.live.com`, `user.auth` / `xsts.auth` / `device.auth` / `title.*`, `sisu`, `party`, `sessiondirectory`, `smartmatch`, `*.xboxlive.com`
- Relic ESS: `aoe-api.worldsedgelink.com`, `dr-activereleaseN-api.worldsedgelink.com` (`reportMatch` shares create/join)
- PlayFab `ED603.playfabapi.com` / `titleId.playfabapi.com` — overlay spoofs FairPlay **in body**, hosts would kill all PlayFab
- Windows vortex / `events.data.microsoft.com`
- profile / presence / privacy / stats / achievements

Write fail does **not** abort inject. Injector prints `[hosts] ON|already|FAIL`. Overlay log `[RA] FairPlay hosts block ON reputation+vortex-events v4+v6`.

No firewall rule from DllInjector. No `flushdns`. No restore on injector exit. APC contract unchanged.

## Files

- `AOE4HOOK/internal/common/fairplay_hosts.h` / `.cpp`
- `AOE4HOOK/internal/DllInjector/main.cpp` (`wmain` after argv)
- `AOE4HOOK/internal/InternalInjector/xbox_enforcement.cpp` (`ApplyHostsBlock` → `FairplayHostsApply`)
- `AOE4HOOK/tools/fairplay_hosts.ps1`
