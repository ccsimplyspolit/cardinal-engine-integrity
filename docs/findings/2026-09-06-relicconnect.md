# 2026-09-06 — x64dbg soft-connect (`relicconnect`) without RA slots

Goal: **x64dbg open and bound to Relic**, RA window stays **empty**.

## Why File → Attach cannot stay at slots=0

Cycle 6 (PID 38948): bland dbg up 3 s = `begin=0` slots=0. MCP
`debug_attach_pid` → overlay edge **EP=0x48** and `slots=2` then `8`
(`01010001` / `01040001`). Not ctor `0x3EC3200` (that one needs EP `0xCC`).

`DebugActiveProcess` / TitanEngine SafeAttach sets kernel **DebugPort**.
Hiding that from Relic means hooking `NtQueryInformationProcess` in Relic
(ntdll body / IAT / ScyllaHide Inject / GhostDbg) → already packed
`0x56FD3C0`. TitanHide / HyperHide banned (0x10E).

Hashed-GPA FNV used for `GetWindowTextW` (`0x3AB480FDFB9CEE95`) has **no**
immediate for `NtQueryInformationProcess` / `CheckRemoteDebuggerPresent`.
Relic does not import those names either. Attach scanner is still
DebugPort-class.

## What we ship instead

Plugin `relicconnect.dp64` (rbhost `plugins\`, built with
`titlehide\build-titlehide.ps1`):

| Command | debugonly | What |
|---------|-----------|------|
| `relicconnect` | no | `OpenProcess` Relic (VM_READ + QUERY). No debug object |
| `relicslots` | no | RPM EP + RA `begin/end` @ `0x7AF6DC8` |

Log line: `[relicconnect] bound pid=… base=… (OpenProcess, no DebugPort)`.

x64dbg CPU / `DbgMemRead` / MCP `debug_attach_pid` still need a real
debuggee — that path packs. Live INT3 in Relic `.text` is hasher-visible.

`Start-X64dbgHidden.ps1` and `Run-CleanCycle.ps1` copy the plugin and **do
not** attach.

## Cycle 7 (PID 4940) — connect stayed empty, then host title packed

`relicconnect` / `OpenProcess`: **slots=0** at 18:47:23. At 18:47:31 Watcher
`20220002` slots=3 — not DebugPort. Needle was the elevated console path
`tools\x64dbg-hidden\…` (`x64dbg` substring). Launch host
`tools\rbhost\Start-Dbg.ps1` with `-WindowStyle Hidden`. MCP
`script_execute` argument is `command` (not `commands`).
