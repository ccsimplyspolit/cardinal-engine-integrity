# 2026-09-06 — Visual Studio MCP :5050/sse autostart

## What the user showed

Dialog **VS MCP Server - Available Tools** (`MCPServer.ShowTools`) listing
`build_*`, `debugger_*`, `diagnostics`, `document_*`, `navigation_*`,
`solution_*`, `window_*` on `http://localhost:5050/sse`.

That is **CodingWithCalvin VS-MCPServer** (Marketplace `CodingWithCalvin.VS-MCPServer`
2026.7.8.66), not Cursor’s existing `user-visual_studio`.

## Two VS MCP products on this machine

| Cursor `mcp.json` | Binary | Transport | Typical tools |
|-------------------|--------|-----------|---------------|
| `visual_studio` (keep) | `K:\aoe4_dlc\tools\Unofficial-VS-MCP\proxy\VsMcp.StdioProxy.exe` → dhq_boiler VSIX `ub0b4zpr.jgd` | stdio → dynamic `http://localhost:<ephemeral>/` | `get_status`, `debug_*`, `build_solution` — namespace `user-visual_studio` (48 tools when devenv is up; not mcp_auth-only) |
| `vs-mcp-sse` (added) | `...\Extensions\x2iohogk.e13\Server\CodingWithCalvin.MCPServer.Server.exe` | SSE `http://127.0.0.1:5050/sse` (HTTP `http://127.0.0.1:5050` also) | `debugger_*`, `document_*`, `navigation_*`, `window_*` |

Do **not** overwrite `visual_studio`. Names collide on “VS MCP”; transports do not.

## How :5050 starts

VSIX package `CodingWithCalvin.MCPServer.MCPServerPackage` AutoLoads on shell
init. **Auto-start of the HTTP process is a separate option**
(`SettingsDialogPage.AutoStart`, default **Off**).

When started (menu or AutoStart), `ServerProcessManager` runs:

```text
CodingWithCalvin.MCPServer.Server.exe --pipe "vsmcp-<devenvPID>" --host "localhost" --port 5050 --name "Visual Studio MCP"
```

Job object dies with devenv. Standalone exe without the pipe = no DTE tools.

EnvDTE command names (note the doubled prefix):

`MCPServer.MCPServer.StartServer` / `StopServer` / `RestartServer` /
`CopyServerUrl` (clipboard `http://localhost:5050/sse`) / `ShowTools`.

Bare `MCPServer.StartServer` is **invalid**.

## Autostart (same family as CE / x64dbg)

This machine has **no** Startup-folder shortcuts and **no** Scheduled Tasks
for CE, x64dbg, or VS MCP. Those MCPs start with the host:

- CE: `autorun\ce_mcp_bridge.lua` when Cheat Engine launches
- x64dbg: `x64dbg_mcp.dp64` when x64dbg launches
- VS :5050: AutoStart when **devenv** launches

Not a login-time devenv task (would open VS every boot).

Persist AutoStart: **Tools → Options → MCP Server → Auto-start Server**.
Helper: `K:\aoe4_dlc\tools\vs-mcp-sse\start-server.ps1` (DTE
`Properties("MCP Server","General").AutoStart = true` +
`MCPServer.MCPServer.StartServer`).

`reg load` of `privateregistry.bin` failed here: *A required privilege is not
held by the client.* Did not elevate. DTE write is the non-admin path.

If devenv is already open and :5050 is down: **Tools > MCP Server > Start Server**
(one click) or the helper `-NoStartVs`.

## Cursor snippet (do not wipe other servers)

```json
"vs-mcp-sse": {
  "type": "sse",
  "url": "http://127.0.0.1:5050/sse"
}
```

## Verify (this session)

- Before: devenv down; :5050 connection refused.
- After `MCPServer.MCPServer.StartServer` (via `user-visual_studio` `execute_command`):
  - Listen `127.0.0.1:5050` + `[::1]:5050` — PID of `CodingWithCalvin.MCPServer.Server.exe`
  - `GET /sse` headers → **200** `text/event-stream` (body stays open; do not `Invoke-WebRequest` the stream)
  - `GET /` → **406** `application/json` (streamable HTTP wants MCP Accept headers)
  - `GET /mcp` → **404**
- DTE `Properties("MCP Server","General").AutoStart` = **True** (was False).
- `reg load` of `privateregistry.bin` failed: *A required privilege is not held by the client.* Used DTE instead.
- Cursor needs **Reload Window** to bind `vs-mcp-sse`.

## Also

Skill (both trees): `vs-mcp-sse`. LOCAL: `K:\aoe4_dlc\tools\vs-mcp-sse\LOCAL.md`.
Extension docs: [CodingWithCalvin/VS-MCPServer](https://github.com/CodingWithCalvin/VS-MCPServer).
