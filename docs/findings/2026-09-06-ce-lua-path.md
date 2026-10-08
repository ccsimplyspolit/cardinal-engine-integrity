# 2026-09-06 — Cheat Engine autorun: `forEachForm` / `json` / `registerAITool`

## Symptom

CE lua-error dialogs (caption **Windows Performance Recorder** — that is our retitle, not WPR):

- `autorun\dmahelper.lua:1` — `module 'forEachForm' not found`
- `autorun\newdefaulttemplates.lua:1` — same
- `autorun\structureExportToCHeader.lua:1` — same
- `Extensions\AITools\aibase.lua:16` — `module 'json' not found`
- `Extensions\AITools\tools\aitools.lua:998` — `attempt to call a nil value (global 'registerAITool')`

Search path in the error is **LuaJIT**, not CE:

`C:\Users\sshunko\AppData\Local\Programs\LuaJIT\bin\lua\?.lua` …

MCP still started: `[MCP v12.0.0] Server Listening on: CE_MCP_Bridge_v99`.

## Cause

User-wide env:

```text
LUA_PATH  = LuaJIT bin\lua + luarocks share\lua\5.1
LUA_CPATH = LuaJIT bin + luarocks lib
```

Lua applies `LUA_PATH` as `package.path` at startup. CE then appends `autorun\xml` and `autorun\ceshare`, but **not** `Cheat Engine\lua\`. Modules actually live at:

| Module | Path |
|--------|------|
| `forEachForm` | `C:\Program Files\Cheat Engine\lua\forEachForm.lua` (defines global `forEachAndFutureForm`) |
| `json` | `C:\Program Files\Cheat Engine\lua\json.lua` (returns table) |

`registerAITool` is defined in `aibase.lua` **after** `require 'json'`. Json fail → cascade.

Earlier the same session: `ce_mcp_bridge.lua:2883 table index is nil` because `[vtByte]=` while `vtByte` was nil. Fixed in-repo with `ceVarType` + numeric `VT_BYTE=0` … `VT_POINTER=11`. Copy lives at `C:\Program Files\Cheat Engine\autorun\ce_mcp_bridge.lua`.

## Fix (do not unset LUA_PATH)

LuaJIT still needs that env. CE-local shim, filename sorts before `dmahelper.lua`:

- Repo: `AOE4HOOK/tools/cheatengine-mcp-bridge/MCP_Server/00_ce_lua_path.lua`
- Installed: `C:\Program Files\Cheat Engine\autorun\00_ce_lua_path.lua`

Prepends `getCheatEngineDir()..\lua\?.lua` to `package.path` and `clibs64` to `package.cpath`.

Live `evaluate_lua` after the same prepend: `forEachForm` ok, `json.decode` is a function.

**Restart CE** so autorun re-runs. Do not rely on a live path patch for boot scripts.

## Related autorun (ours)

| File | Role |
|------|------|
| `autorun\00_ce_lua_path.lua` | Restore CE `lua\` on `package.path` |
| `autorun\00_retitle.lua` | Caption/title → `Windows Performance Recorder` (WindowWatcher matches `"Cheat Engine"`). Repo copy: `MCP_Server/00_retitle.lua` |
| `autorun\ce_mcp_bridge.lua` | Named pipe `CE_MCP_Bridge_v99` |

Pipe: `\\.\pipe\CE_MCP_Bridge_v99`. Cursor namespace: `user-cheatengine`.
