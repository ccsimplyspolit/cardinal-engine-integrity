# 2026-09-13 RelicCardinal.DMP (Temp) — snapshot, not the 15:23 hang

Path: `C:\Users\sshunko\AppData\Local\Temp\RelicCardinal.DMP`
Size ~3.61 GiB. User minidump **with full memory**. Session **15:12:12**
(boot 14:37, uptime 34m54s). Relic uptime **50 s**. PID **0x9ad0**.
Base **`0x7FF7E0540000`**. Exception **`80000003`** at address 0 —
snapshot (ProcDump / MiniDumpWriteDump), not an AV.

Thread 0 was in `accept` / `WSPSelect` (bring-up socket). Stack through
Relic `0x3DCD6CC` / `0x3DCFC75` (RA neighborhood) then `0x4FB0816`.

## RA / AT (sdk `RelicCardinal_16.3.11308.h`)

| RVA | Dump |
|-----|------|
| lock/begin/end `0x7AF6DC0` | **all zero** (empty window) |
| accum/flag `0x7AFB750` | **zero** |
| `RA_Enqueue` `0x3DD2550` | original `44 89 4c 24 20 55 53 56…` |
| hasher `0x3E57050` | original prologue |
| Watcher `0x3F0A7D0` | original `48 89 5c 24 18` |

HV was already `load_ok` from **15:07**. Hold was **not** applied. This
is the empty-window moment `wait-hold` needs. Nested KDU `-map` at 15:18
then Kernel-Power 41 (no kernel minidump).

Do not reuse this image base. Next Relic PID will ASLR again.

## Capture

`aoe4-hv/docs/Capture-CrashContext.ps1` + `Enable-CrashCapture.ps1`
(WER LocalDumps → `Documents\AOE4HSettings\Dumps\wer`,
AlwaysKeepMemoryDump, CrashOnCtrlScroll). Hitch copies
`zpp_loader-live.log` every second onto K:.
