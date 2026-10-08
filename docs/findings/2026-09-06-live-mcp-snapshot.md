# 2026-09-06 — live Relic + MCP snapshot (16:44–16:45)

Observe only. No inject, no Steam launch, no cloak, no IDA MCP. Cycle sibling `94667457` owns attach.

## Relic

| Field | Live |
|-------|------|
| `RelicCardinal.exe` | **DOWN** (16:44:07 and 16:45:17) |
| PID / Relic base | none |
| Overlay in | no |
| RA slots | not readable (no process) |

Steam **19688** since 16:36:16. WindowWatch **3448** since 16:40:31. No `DllInjector`, no `x64dbg`, no Cheat Engine, no `MSBuild`.

Last overlay session is already recorded: [inject 37124 AV](2026-09-06-inject-37124-crash.md). Documents log frozen at **16:42:43.835** (10 591 bytes). `%TEMP%\aoe4_internal.log` missing (this shell `TEMP=C:\WINDOWS\TEMP`; user `%LOCALAPPDATA%\Temp` also has no file).

## Last session (not live) — slots

From `Documents\AOE4HSettings\Logs\aoe4_internal.log` PID **37124**, Relic base `0x7FF6F92A0000`:

- `[RA] neutralize ON` 16:42:43.030 (`veh=0`, no kick stub)
- `[RA] integrity cloak OFF` (CRT splice). Engine `IntegrityCloak::Install` is overlay `.text` shadow only
- `[RA] Snapshot: uninit/empty begin=0 end=0` — **no `slots=` line**
- DXGI Present vtable slots 8 / 22 / 13 patched; first Present then process gone (~1 s). No `[GPU] AV`

Prev log (16:19 cloak-on / 0x10E) also has **no `slots=`** string.

## MCP

| Channel | Status |
|---------|--------|
| CE MCP | **down** — `Cheat Engine Bridge (v12/v99 pipe) is not reachable`. No CE process. `ping` / `get_processid_from_name` / `get_opened_process_id` all fail |
| x64dbg HTTP `:3000` | **down** — connection refused. `user-x64dbg` namespace error (discovery failed). No `x64dbg.exe` |
| VS `user-visual_studio` | **up** — `AOE4HOOK.sln` Ready, debugger **Design**, active `DllInjector\main.cpp`, devenv **21360** (16:34:56) |
| VS `vs-mcp-sse` `:5050` | Cursor namespace **error**. HTTP listener **is** up: `GET /` → **406**; `GET /` + `Accept: text/event-stream` → **400**. `GET /sse` with SSE Accept hung (do not poll that) |
| Frida `get_process_by_name` | timed out this turn; process list from PowerShell `Get-Process` |

## Binaries (not injected this turn)

`K:\aoe4_dlc\hh\AOE4HOOK\internal\x64\Release\InternalInjector.dll` **13 464 576** bytes, mtime **16:45:04** (newer than the 16:40:36 / 13 453 312 DLL that died in 37124). `DllInjector.exe` 218 624 bytes, 16:39:09.

Did not inject (sibling cycle + DLL just rewritten). Did not set `AOE4H_RA_CLOAK`.
