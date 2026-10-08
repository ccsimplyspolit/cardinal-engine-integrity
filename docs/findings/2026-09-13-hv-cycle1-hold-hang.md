# Cycle 1 result — load_ok then hold hang (2026-09-13)

Runtime owner cycle. Dump-gate fields kept. **Do not map.**

## Chat tab 3305282e

Cursor Composer UUID `3305282e-6d1a-44c6-8c02-7dfb3f7e7c03` will not open
as a live tab (~4.3 MB jsonl, 3032 lines, 240 user / 2783 assistant,
2026-09-06 CLI/RA through 2026-09-13 HV). There is no repair-conversation
flow. Transcript on disk only. Work continues in the current chat.

Last user line in that jsonl (16:28): x64dbg path
`C:\Program Files (x86)\rbhost`. Parent had already mapped Cycle 1
and started Relic + `hold --apply`. Host then hung.

## Cycle 1 verdict

| | |
|---|---|
| Hypothesis | DriverEntry hang after `copyphys_ok` = forced `sme_cbit` on copy-window PTE |
| Changed | Removed `pfn \|= sme_cbit` (`windows_loader/src/main.cpp`). Sys **16:20:21** 1075200 B |
| HV | **PASS** `load_ok` 16:21:43. 32/32 `cpu_ok` `exit=7c` `elfst=46`. hitch `inner=0` `npf=0` `full7c` APERF tax. `hitch_watch_end` `efer=4d01` `keep_va` `vmcall_skip`. Keyed ping **pong**. |
| Mailbox | **PASS** then **FAIL**: hello + mbox-ping + query Relic `status=0` until last retry `mailbox no-reply rax=2` |
| Relic session | PID **5012** start 16:25:50 image `0x7ff7babb0000` size `0x8c3d000` titled `-dev -nodbg -notrap`. WER `RelicCardinal.exe.5012.dmp` 16:30:43 (dump session 16:30:25). |
| Signatures | hold 39 Watcher+INT3 E8 sites; dest skip `0x3f04000` / `0x3f2d000` |
| Vs AI | no (died during hold) |
| x64dbg open | no (user pointed at rbhost 16:28; not launched) |
| 60 s | not reached |
| New dump | kernel **NO** (Minidump empty, CrashDumpEnabled=0). Relic WER **YES**. Host Event **41** 16:32:48, **6008** unexpected 16:30:34. |
| Root cause evidence | Cookie `in_progress` attempt 16:21:40 boot 15:54 + newer boot 16:32:44 = last map died. First `stealth --file` armed ~20 sites `status=0`, then `status=10` (`hook_failed`). Five more NPT apply retries. Relic AV **c0000005 execute @ 0**. Host hung ~9 min after `load_ok`. C-bit hyp **confirmed for DriverEntry**. New failure = hold NPT execute-copy on fresh SVM. |
| Verdict | **failed** — do not remap this image into Relic/hold. `launch_authorized=false`. |
| Next | Fail-closed: `zpp_at.py hold` aborts after first partial `stealth_arm`. Wait user **запускай**. Next map = identity idle only (no Relic/hold until minutes alive). Do not nested-map. |

## Gate (this boot)

- LastBootUpTime `2026-09-13T16:32:44`
- Event 41 `2026-09-13T16:32:48` (no 1074)
- 6008 previous unexpected `16:30:34`
- Minidump empty; BlueScreenView empty
- CrashDumpEnabled=0 AutoReboot=1
- ping now **ud** (SVM dead after reboot)
- HostPrep Capture `crash-20260913-163312`; full Capture `crash-20260913-163635`
- Relic Temp DMP 15:12 is **stale** vs this iteration
- WER PID 5012 is this iteration

## Do not

`kdu -map` / `Map-AfterZppu` / `Start-ZppLoader` until **запускай** after this note.
Nested-map. `sc start Aoe4Hv`. Treat unkeyed ping `ud` as proof SVM is down
while a live map still has `last-zpp-key.txt`. Relic/hold on the next map
before idle minutes. Open x64dbg during a partial hold.
