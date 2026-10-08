# IDA GUI crash on start (Python 3.10 + ida_mcp)

2026-09-09 ~00:41–00:42. User: IDA dialog «IDA has encountered a problem» then GUI would not start.

## Symptom

WER `APPCRASH` three times in ~50s:

| Time | PID | Fault |
|------|-----|--------|
| 00:41:22 | 0x9A64 | `ida.exe` 9.3.26.421 / `Qt6Core.dll` 6.8.2.0 / `c0000005` / offset `0x6270` |
| 00:41:32 | 0xBBD0 | same signature |
| 00:42:18 | 0x9898 (39064) | same signature |

Minidumps (install dir, ~600 MB each):

- `C:\Program Files\IDA Professional 9.3\ida-20260909-004128-48080.dmp`
- `C:\Program Files\IDA Professional 9.3\ida-20260909-004214-39064.dmp`

Older same-size dumps: `ida-20260906-000437-46520.dmp`, `ida-20260906-000756-58644.dmp`.

cdb on `004214-39064`: **execute non-executable address 0**. WER blamed `Qt6Core`; real caller is `idapython3+0x6d50` → `idapython3+0x1dd4` → `ida!get_std_dirtree` during GUI process start (`Timeline.Process.Start.DeltaSec=1`). RIP=0.

Launch was Start Menu: ImagePath `ida.exe`, title/lnk `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\IDA Professional 9.3\IDA Professional 9.3.lnk`. Shortcut itself is clean (target `ida.exe`, empty args, working dir = install dir). PATH in dump included `...\Python\Python310`.

## Isolation

| Launch | Result |
|--------|--------|
| `idat.exe -A -t` + empty `IDAUSR` | exit 0 |
| `ida.exe -t` + empty `IDAUSR` | GUI alive (Python 3.10.11 banner) |
| Each user plugin alone in temp `IDAUSR` | all OK (idasql, keypatch, HappyIDA, ida_mcp, ida_multi_mcp, SigMaker, ApplyCalleeTypeEx) |
| All plugins copied + real `IDAUSR` + `-t` / no `-t` (this session, after 3.10 still selected) | GUI alive 10s |
| `ida.exe -t` after `idapyswitch --force-path` **3.12.13** | GUI alive; plugins init including both MCP servers |

`ida_mcp` on 3.10: `ImportError: cannot import name 'NotRequired' from 'typing'` (`zeromcp/mcp.py`, Python 3.11+). Plugin `run()` / UI `ready_to_run` autostart has no try/except around that import. Isolated 3.10 load printed the traceback and sometimes survived; user Start Menu loop dumped.

Registry before fix: `HKCU\Software\Hex-Rays\IDA\Python3TargetDLL` = `...\Python310\python3.dll`. Skill/stack expected uv CPython **3.12**.

## Fix applied this session

```
idapyswitch.exe --force-path C:\Users\sshunko\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\python3.dll
```

Do **not** run `idapyswitch.exe` with no args: interactive default re-applies 3.10.

Loader tweak: `plugins\ida_multi_mcp.py` now `sys.path.insert(0, site-packages)` so `plugins\ida_multi_mcp.py` does not shadow the installed package on the fallback path.

3.12 boot log (empty `-t` DB): HappyIDA, Keypatch, IDASQL, ApplyCalleeTypeEx, `[MCP] Autostarting` `127.0.0.1:13338`, `[ida-multi-mcp]` `127.0.0.1:32723`. Two GUI MCP servers at once is noisy but did not crash in 12s.

## Do not

- Treat WER `Qt6Core.dll+0x6270` as a broken Qt install when RIP is 0 in `idapython3`
- Re-run bare `idapyswitch` (picks Python 3.10 as “previously used”)
- Open `K:\aoe4_dlc\7ff6f65c0000.RelicCardinal.exe.i64` (2.48 GB, History64[0]) just to “test start”
- Mix this with Relic live attach; registry mutex note in UPDATE_GUIDE still applies
