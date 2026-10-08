# 2026-09-13 — IDA GUI open + hosts xrefs (60644 runtime)

User: open IDA yourself. Confirm FairPlay / telemetry FQDNs before changing the hosts deny list.

Build **16.3.11308.0**. Imagebase **`0x7FF7A5500000`**. RVAs only below. GUI left running (IDA PID **30628**, ida-multi `okfp` `:46676`, ida-pro-mcp session **`4f6bd10b`**). `run_auto_analysis=false`. Relic was not running (no `$ IDA registry mutex $`).

## Which IDB actually opens

| Path | Result |
|---|---|
| `K:\aoe4_dlc\dumps\RelicCardinal_60644_20260906_full_analysis\ida\runtime_exe.i64` (packed 2.47 GB) | GUI Error: `runtime_exe.nam: File is not a virtual array file?!` then **exit**. Sidecars from the failed unpack were deleted on close. This is also why `idb_open` on that file was WinError 10054. |
| `K:\aoe4_dlc\aoe4\gamesource\dump\ida-work\runtime_exe.i64` | **Opens.** `.nam` magic `VA*` (`56 41 2A 00`). Same imagebase. Title `IDA - runtime_exe.i64 (RelicCardinal.exe)`. |

IDA 9.3 binary is `C:\Program Files\IDA Professional 9.3\ida.exe` (no `ida64.exe`).

Do not start a second writer (IDASQL / idalib) on this IDB while the GUI holds it.

## Hosts list — IDA confirmation (product unchanged)

Still only:

- `reputation.xboxlive.com`
- `vortex-events.xboxlive.com`

### `reputation.xboxlive.com`

**0** C-string hits in Relic. XSAPI builds the host. Relic only has the method name and the GDK import-style string.

| Item | RVA | VA | Xrefs |
|---|---|---|---|
| `"SubmitReputationFeedback"` | `0x575D108` | `0x7FF7AAC5D108` | `sub_7FF7A95D4E50` size `0x1DC` (`0x40D4E50`) |
| that func | `0x40D4E50` | `0x7FF7A95D4E50` | code from `0x40D5030`; data slot |
| `XAsyncBegin` wrapper | `0x40EB180` | `0x7FF7A95EB180` | Hex-Rays: `XAsyncBegin(..., "SubmitReputationFeedback" path)` |
| `"XblSocialSubmitReputationFeedbackAsync"` | `0x653C710` | `0x7FF7ABA3C710` | `0x30B61F0` (size `0x358`), `0x30B6550` (size `0xB0`) |
| `"FairPlayCheater"` / `"FairPlayTampering"` | `0x57617F0` / `0x5761800` | | `Xbox_FairPlay_Mapper` `0x411F380` |
| `"feedbackType"` | `0x57617A8` | | JSON builder `0x411ED00` |

Hex-Rays at `0x40D4E50` already named in the IDB: *XSAPI SubmitReputationFeedback sender → XAsyncBegin via 0x40EB180. Called only from 0x40D5030*.

### `vortex-events.xboxlive.com` — **SEND**

Substring find on the host has **0** xrefs (it sits inside the HTTPS URL). The defined string is the full URL.

Blob next to `Microsoft.XboxLive.InGame` (`0x5764EB8`):

```text
Microsoft.XboxLive.InGame
baseType / baseData
Cannot add more events to payload.
https://vortex-events.xboxlive.com
https://vortex-win.data.microsoft.com
```

| Item | RVA | Xref |
|---|---|---|
| `"https://vortex-events.xboxlive.com"` | `0x5764F20` | `sub_*` **`0x416CA70`** size `0x49C` — Hex-Rays: `strcpy(..., "https://vortex-events.xboxlive.com")` then HTTP helper `0x40F9BF0` |
| host-only at `0x5764F28` | same URL +8 | 0 xrefs (use the HTTPS string) |
| `"https://vortex-win.data.microsoft.com"` | `0x5764F48` | `0x416E130` — **Windows** Diagnostic Data; **not** in hosts |
| `"Microsoft.XboxLive.InGame"` | `0x5764EB8` | `0x4169D70` |

### Keep off hosts (IDA same session)

| String | RVA | Why not deny |
|---|---|---|
| `"-api.worldsedgelink.com"` | `0x653F9B8` | `0x3103180` concatenates suffix, sets **port 443**. Live `dr-activerelease1-api…` login/join **and** reportMatch. |
| `"/game/party/reportMatch"` | `0x65384E0` | xref from `0x300E030` (size `0x15FF`) — **path**, same ESS host |
| `"titleId.playfabapi.com"` | PlayFab | two tiny `0x57` returners; `ED603` is a huge string table — login **and** events |
| `"Socks::SendQueue"` | | RelicLink class `0x320BBB0`, not SOCKS5 |
| `IPPROTO_GRE` | — | **0** hits |
| `reputation.xboxlive.com` as C-string | — | **0** hits (XSAPI) |

## Product

No hosts-list change. DllInjector + overlay already write both FQDNs dual-stack. Binaries in `AOE4HOOK\internal\x64\Release\` contain `reputation.xboxlive.com` and `vortex-events.xboxlive.com`.
