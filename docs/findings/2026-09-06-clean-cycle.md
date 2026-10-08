# 2026-09-06 — clean cycle actually run (titled → inject → hidden dbg → attach)

Agent must **run** `tools/x64dbg-hidden/Run-CleanCycle.ps1` (elevated), not
only describe it. Relic can look “closed” while PID still lives if
`RuntimeBroker.exe` under `rbhost` is attached (`TerminateProcess` = 5 until
that dbg dies).

## Cycle 4 (valid) — PID **18480**

| t | Event |
|---|---|
| 18:27:31 | titled `n=37` `Age of Empires IV -dev -nodbg -notrap` |
| 18:27:31–46 | 15 s settle |
| 18:27:46 | inject `[RA] hide ON retitle=0 bodies=0` neutralize OFF |
| 18:27:47 | Present alive |
| 18:27:48 | `Start-X64dbgHidden` + MCP attach `attach_break=false` `state=running` |
| 18:27:49.131 | **slots=3** `20220002` kinds 6/1/3 |
| 18:27:49.179 | **slots=11** + `01010001`/`01040001` |

`titleboot.dll` + always-bland `titlehide` **did not** keep launch at
`slots=0`. Same WW triple as 38692.

Relic still up after attach (2.2 GB, FOCUS heartbeat).

## Cycle 5 — PID **35720** (VERSIONINFO + hide)

| t | Event |
|---|---|
| 18:31:01 | titled `n=37` `Age of Empires IV -dev -nodbg -notrap` |
| 18:31:01–16 | 15 s settle |
| 18:31:16 | inject `[RA] hide ON retitle=0 bodies=0` neutralize OFF |
| 18:31:18.213 | RA window **uninit/empty** |
| 18:31:17 | `RuntimeBroker.exe` VERSIONINFO patched `FileDescription=rbhost` `ProductName=rbhost` |
| 18:31:19 | MCP attach `attach_break=false` `state=running` |
| 18:31:19.722 | **slots=8 accum=0** — **no** `20220002` Watcher/sibling |

Launch hide **worked**. FileDescription `x64dbg` was the cycle-4 `slots=3` needle
(`0x3EAFA2C` reads VERSIONINFO). Remaining pack is attach-only:

| slots | tag | `+10` RVA |
|-------|-----|-----------|
| 0–3 | `01010001` | `0x5703D70` (`off_7FF7AAC03D00+0x70`) |
| 4–7 | `01040001` | `0x5703870` (`off_7FF7AAC03800+0x70`) |

IDA: `01010001` ctor `sub_7FF7A93C3200` RVA **`0x3EC3200`** is **one-shot** at
RA window first-alloc. Packs only if Relic MZ EP byte is `0xCC`. Cycle 5
attached at the same millisecond the window appeared — ctor/attach race.
`01040001` ctor `0x3EC0FB4` is vtable-only; those slots ride Enqueue with
the `01010001` fail. Tick `0x3EC34C8` does **not** re-check EP.

Cycle script now waits `begin!=0` `slots=0` **before** dbg attach.

## Cycle 6 — PID **38948** (wait empty window — false lead)

| t | Event |
|---|---|
| 18:37:01 | titled `n=37` |
| 18:37:17 | inject hide ON. EP=`48 83 EC 28` `begin=0` uninit |
| 18:37:18–18:38:49 | 90 s poll: **still uninit**, EP stays `48`. Relic 2.5 GB, Present alive |
| 18:38:49 | bland dbg up. 3 s later still `begin=0` slots=0 |
| 18:38:53 | MCP attach `attach_break=false` |
| 18:38:54.064 | overlay attach edge **EP=0x48** rva `0x4FB0884` |
| 18:38:54.069 | overlay **slots=2** (`01010001` kinds 6+3, `+10=0x5703D70`) |
| 18:38:55 | RPM **slots=8** EP still `48 83 EC 28` |

RA window is **lazy**: `begin` stays 0 until first Enqueue. Waiting for
`slots=0` allocated never happens. dbg **start** stays clean (VERSIONINFO
fix holds). Attach pack is **not** `0x3EC3200` EP INT3 — EP was `0x48` at
the pack edge. `01010001` here is a different attach scanner (kernel
DebugPort / hashed QIP). ntdll hook still banned (`0x56FD3C0`).

## False starts (do not treat as the ritual)

| PID | Why invalid |
|-----|-------------|
| 38692 | leftover from prior session; `taskkill` failed while dbg 26240 attached |
| 36544 | wait accepted AMD `title=A` (`StringBuilder` length 1, real n was longer) |
| 39656 | real title, inject+attach OK; died after later `erun` (paused boot) |

## Cycle 7 — PID **4940** (relicconnect, no attach)

| t | Event |
|---|---|
| 18:47:00 | titled `n=37` |
| 18:47:15 | inject hide ON. `begin=0` uninit |
| 18:47:16 | bland dbg up. MCP `script_execute` sent `commands` (wrong) — plugin still `plugsetup` binds |
| 18:47:23 | **post-connect `slots=0` uninit** (OpenProcess does not pack) |
| 18:47:30 | Relic `WM_KILLFOCUS` |
| 18:47:31 | **slots=3 accum=600** `20220002` kinds 6/1/3 |

Soft-connect is clean. The +15 s WW triple is the **visible elevated host**
`...\tools\x64dbg-hidden\Start-X64dbgHidden.ps1` — Watcher `GetWindowTextW`
matches substring `x64dbg` on any desktop title. Cycle 5–6 only waited 2–3 s
after dbg start (then attach), so they never reached this period.

Cycle 8 host is `tools\rbhost\Start-Dbg.ps1` **Hidden**. MCP argument is
`command` (singular). Wait 20 s after `relicconnect` before calling empty.

## Cycle 8 — PID **37172** (Hidden host — hide still failed)

| t | Event |
|---|---|
| 18:52:59 | titled `n=37` |
| 18:53:15 | inject hide ON. `begin=0`. needles none |
| 18:53:15 | `Start-Dbg.ps1` Hidden |
| 18:53:16 | overlay **slots=3 accum=600** `20220002` (dbg start) |
| 18:53:19–41 | relicconnect ok; needles still none; slots stay 3 |

Hide path is closed. Next: `patchAT --apply` before first Enqueue.
See [patchAT](2026-09-06-patchAT.md).

Wait titled = visible + `GetWindowText` **char[]** + `n>=20` + substring
`Age of Empires` or `-dev`. DllInjector `FindUiThreadId` uses the same gate.

## Kill order

1. Non-`System32` `RuntimeBroker.exe` (`...\rbhost\...`)
2. Then Relic (`TerminateProcess` 5 while attached)

## Script

`AOE4HOOK/tools/x64dbg-hidden/Run-CleanCycle.ps1` — log
`Documents\AOE4HSettings\Logs\clean-cycle.txt`. Host without `x64dbg` in
the path: `tools\rbhost\Start-Dbg.ps1` Hidden.
