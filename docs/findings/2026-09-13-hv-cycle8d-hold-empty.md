# Cycle 8d: leftover EPROCESS + idle map + hold slots=0 (2026-09-13)

Mailbox ops 1–12 unchanged. Overlay / Patch Game / InternalInjector not used.

## Point

Cycle 8b `read status=8` was leftover `RelicCardinal` EPROCESS (same
`cr3=0x73632e000` after kill 36888/3088). Explorer MZ HV-read was
`status=0`. 8c ELF skipped leftovers on `probe_va` but `kdu -map` with
Relic **36364** already live → Event 41 19:36. Reboot **19:36:13** already
done. 8d is a **new** sys (`A1EA2CF1`, not `D78C5065`).

8d: `find_running_process` requires mapped user PEB when there is no
site VA; `probe_va` still skips leftovers on read/stealth. `Map-AfterZppu`
exit 5 if Relic live.

## Live

| Step | Result |
|---|---|
| Capture 19:42 | boot 19:36:13; Event 41 still 19:36:17; Relic none; ping `ud` |
| Build 19:42:30 | sys 1088000 SHA256 `A1EA2CF1…3219CC77`; ELF `5FBA31F1…FFC7B9C` |
| Map 19:43:11 | Relic **none**; `load_ok` hitch `inner=0` `npf=0` |
| ping | `pong` (keyed) |
| Relic **3256** | 19:47:10; died ~1 min — **IDA GUI** `runtime_exe.i64` open (not HV) |
| Relic **34288** | 19:53:00 `0x7FF716E90000` Steam `-dev -nodbg -notrap`; IDA closed |
| query | `status=0` `cr3=0x20dd0b000` image_rpm=`7ff716e90000` |
| HV read Enqueue | `status=0` `44 89 4c 24 20…` |
| HV read hasher | `status=0` `48 89 5c 24 20…` |
| hold --apply | Enqueue/KickCtor/TimerQ `eax=0` **status=0**; hasher `0xFFFFFFFE` **status=0**; protect `0x3E57000` **status=0**; dest skip `0x3E58000` |
| window after hold | `slots=0 accum=0 flag=0` |
| prove 60s no dbg | 59 samples empty; Relic still 34288 |
| hidden rbhost | `smabcc.exe` pid **30868** under `rbhost\` (not stock `x64dbg.exe`) |
| prove 60s hidden | 60 samples `slots=0`; leftover WW **19636** seen then killed (not overlay hide) |
| after 19:59 | ping `pong`; Relic **34288**; slots=0; identity Enqueue/hasher still golden |

Not armed: WindowWatcher `0x3F0A7D0`, sibling `0x3F328D8`, 7AB0, 45E8, WW E8 flood.

## Do not

- Remap Cycle 8c `D78C5065` / 8b `8C9D7CDD` / Cycle 3 `5351E024`
- `kdu -map` while Relic live
- Hold PID 36888 / 20068 / 5012 / 3088 / 36364 / 3256
- Open IDA while Relic is up (Watcher packs / process dies)
- `--eax 1` hasher / WPM `.text` / overlay / `sc start Aoe4Hv`
