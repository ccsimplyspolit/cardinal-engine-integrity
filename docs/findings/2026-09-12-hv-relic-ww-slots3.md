# 2026-09-12 Relic launched on live 18:55 SVM � WW slots=3

User: launch game / debugger / WindowWatch yourself. OS reboot from 19:25 **did not happen** (boot still `2026-09-12T18:28:40`). Did not remap 19:23 sys (live SVM). Did not File?Attach. Did not inject overlay.

## Live

| | |
|---|---|
| Relic | PID **29604** `D:\SteamLibrary\...\RelicCardinal.exe -dev -nodbg -notrap` started 19:32:34 |
| image | `0x7FF6BB940000` SizeOfImage `0x8C3D000` (CE `enum_modules`) |
| WindowWatch | Release `internal\x64\Release\WindowWatch.exe` PID **42320** |
| x64dbg | PID **30132** process name `x64dbg.exe` (copy of rbhost RuntimeBroker; **no attach**) |
| CE | `cheatengine-x86_64-SSE4-AVX2` PID 48856, open Relic 29604 |

## Window ring (WW log + CE + `zpp_at.py window`)

`!slots=3 accum=600 flag=1 begin=0000015D40867970 end=0000015D40867E38`

CE RPM: begin `0x7FF6C3436DC8`=`0x15D40867970`, end=`0x15D40867E38`, accum=`600`, flag=`1`. `(end-begin)/0x198=3`.

`prove --sec 8` ? `verdict=watcher_pack`, `dbg_visible=['x64dbg.exe']`, `hide_process=['windowwatch.exe']`, DualFlag lobby/menu `in_match=False`.

PING still ok. ZPPX hello still `rax=2` (no 4K GPA window on sys 18:52). `hold --apply` not armed.

## Not this turn

IDA idalib worker is ScarToolKit_LM (max 1). Ghidra none. x64dbg MCP namespace error. Vs AI not started (menu). Next hold needs reboot + map sys **19:23:33** (Relic must be dead first).
