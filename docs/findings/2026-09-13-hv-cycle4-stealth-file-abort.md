# Cycle 4 — abort stealth --file on first status!=0 (2026-09-13 17:18)

Runtime owner. **Do not map.** Mailbox ops 1–12 wire **unchanged**.
Cycle 3 corpse sys `5351E024…` 16:45:29 stays unmapped.

## Cycle 4

| | |
|---|---|
| Hypothesis | Continuing `stealth --file` after the first `hook_failed` (status=10) keeps NPT execute-copy on mixed WW pages and hangs the host. Cycle 3 already fail-closed *retries*; the first file still armed all 39 VAs. |
| Changed | `tools/zpp_aoe4/zpp_aoe4.cpp`: `--file` returns on first `msg.status != 0`. Rebuilt `zpp_aoe4.exe` 17:17:29 (197632). |
| HV | not remapped (ping **ud**, gate **21**, Event 41 17:09:32 after last_fix 16:45:29) |
| Mailbox | **FROZEN** op 6 request/response |
| Relic session | none this boot (17:09:28). Dead **20068** `0x7FF634300000` |
| Signatures | first fail RVA `0x3F5B04B` logged observation-only |
| Vs AI | no |
| x64dbg open | no |
| 60 s | no (HV not resident) |
| New dump | NO (empty Minidump) |
| Root cause / evidence | wait-hold log: 23× status=0 then 10 from `0x3F5B04B`, remaining arms still issued, unexpected 17:07:55 |
| Verdict | **source+agent only**. STEP 1 smoke blocked until new map of a *non-corpse* policy + `запускай` |
| Next | Do not remap Cycle 3 ELF. User **запускай** after this Cycle 4 agent is the test. Identity idle. Relic. One wait-hold (must stop at first 10). |

STEP 0 this boot: ping ud, VBS 0, Relic none, HostPrep register 17:17:25 (query from medium IL denied), CrashDumpEnabled=0.
