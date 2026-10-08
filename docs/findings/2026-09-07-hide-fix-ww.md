# 2026-09-07 — WW log 23:46:30→3 then err=299

User pasted WindowWatch: slots=0 until **23:46:33** `slots=3 accum=600`, then
**23:46:42** `RPM err=299`. «исправляй».

Two different failures in one log (PID **41064**).

| t | What | Fix |
|---|---|---|
| 23:46:33 | Watcher `20220002` (dbg start, not attach) | Bland loaded names; **not closed**. VERSIONINFO on the exe was already `rbhost` |
| 23:46:42 | `debug_attach_pid` / DebugPort | **Do not attach.** Soft-bind only |

## What shipped

`Start-X64dbgHidden.ps1` + `Bland-RbhostFiles.ps1`:

- Payload `x64dbg.exe` / `x64dbg.dll` live in `rbhost\release\_src\`, not the
  process directory.
- Process dir has `RuntimeBroker.exe` + `rbcore.dll` (copy of the dll).
- Plugins: `rbhost_mcp.dp64`, `ScyllaHidePlugin.dp64`.
- Ini apply reads `RuntimeBroker.ini` (moving `x64dbg.ini` used to abort
  start — that left 28944 at slots=0 **because dbg never launched**).
- No `debug_attach_pid` in the hide-fix cycle.

## Live

| PID | Result |
|---|---|
| 41064 | hide ON, then attach → dead ~8s. EP=`0x48` |
| 43084 | slots=0 until bland dbg **38504** actually ran → **slots=3** |
| 28944 | 20s slots=0 while Start-Dbg died on missing `x64dbg.ini`; later dbg **14132** and Relic gone |
| **53700** | Steam + inject hide, dbg **14132 killed**. Hold without attach |

MCP `:3000` stayed down after the plugin rename. Soft-bind needs the MCP
plugin loaded — next check is whether `rbhost_mcp.dp64` still exports.

Do **not** File→Attach / `debug_attach_pid` on 53700. That is the 299.
[41064](2026-09-06-debug-attach-41064.md).
