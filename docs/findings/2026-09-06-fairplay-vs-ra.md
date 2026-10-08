# 2026-09-06 — Xbox FairPlayTampering ≠ Relic RA kick

Канон слоёв + SEND-цепочки: [2026-09-06-ida-ra-analysis.md](2026-09-06-ida-ra-analysis.md).  
Autoscan: `K:\aoe4_dlc\dumps\RelicCardinal_60644_20260906_full_analysis\ida\autoscan_report.md`.

## Split

| Layer | What it is | Local Exit? |
|-------|------------|-------------|
| Relic RA window | TOP fail → enqueue `0x3DD2550` → slots/accum → kick ctor `0x3E691F4` | Yes (client kills itself) |
| Xbox FairPlay | enum `0x411F380` case 2 + **SEND** `0x40D4E50` → `XAsyncBegin` `0x40EB180` | No — reputation POST |
| ESS reportMatch | `0x300E030` POST `/game/party/reportMatch` + `checkSums` | No — match HTTP |

Official Xbox: title auto-reports on-disk / software / hardware tamper without a user click. Affects Fairplay reputation / Avoid Me. **Not** the delayed HUD/Rule Exit path in [UPDATE_GUIDE §1.4 / §1.6](../UPDATE_GUIDE.md).

## Relic SEND (16.3, IDB `runtime_exe.i64`)

| Item | RVA |
|------|-----|
| `"FairPlayTampering"` string | `0x5761800` |
| Enum mapper (not sender) | `0x411F380` `case 2` |
| JSON `/users/xuid(%s)/feedback` | `0x411ED00` |
| `SubmitReputationFeedback` | `0x40D4E50` → `0x40EB180` `XAsyncBegin` |
| PlatformReportJob | `0x30B61F0` (`feedbackType=7` hardcoded) |
| GetLiveContext / Report | `0x2EFD750` (vtable `0x6530680`) |
| `/game/party/reportMatch` | `0x300E030` (path str `0x65384E0`) |

Do not spend IDA time on FairPlay/ESS when the symptom is `slots>0` or delayed `Exit` after SCAR/HUD.

## Other report surfaces

- Checksum serializer `0x2E23930`: `appBinaryChecksum` / `dataChecksum` / `modDLLChecksum`
- Maelstrom eventbatch `0x2F4E310`; PlayFab host string only (no PlayFab DLL)
- **No** `ISteamUserStats` string or import
- `VACBanned` is XOR-encrypted init (`0x28F770`), not a VAC query
- `ReportPlayer` is UI loc; `Player_SetReputation` is XOR SCAR name (0 xrefs)
