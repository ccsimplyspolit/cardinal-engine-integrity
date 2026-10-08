# 2026-09-06 — WindowWatcher launch `slots=3` + attach `slots=11`

Build **16.3.11308.0**. IDB `runtime_exe.i64` session `a1220dbc`, imagebase
`0x7FF7A5500000`. Live PID **33376** (inject lived `slots=0`, then dbg).

Related: [os-body-hide](2026-09-06-os-body-hide.md),
[x64dbg-windowwatcher-hide](2026-09-06-x64dbg-windowwatcher-hide.md).

## What packed

| When | WindowWatch | Overlay classify |
|------|-------------|------------------|
| 17:42:04 dbg **start** (no attach) | `slots=3 accum=600` | Watcher/sibling `tag=0x20220002` |
| 17:42:33 MCP **attach** | `slots=11 accum=600` | 3× `20220002` + 4× `01010001` (`+10` RVA `0x5703D70`) + `01040001` (`0x5703870`) |

`accum` stays 600 — only the WW triple adds 3×200. Extra attach slots are a
different scanner. `-nodbg` re-armed at the same millisecond and **did not**
prevent `01010001`.

IDA: `0x01010001` as a raw immediate is mostly Xbox/protocol writes, not the
enqueue site. The tag is carried on the descriptor at RVA `0x5703D70` (0
xrefs — table blob). `0x01040001` immediates sit inside `RA_Enqueue`
`0x3DD2550` only.

Sibling `0x3F328D8` → classifier `0x3EAFA2C` (`sub_7FF7A93AFA2C`, size
`0x2D6A`). Types **3 / 4 / 5** call `RA_Enqueue(..., 200, 0x20220002, 9)`.
Leaf via `wcsrchr('\\')`. **WindowWatch.exe is not type 3/4/5** (26508 /
33376 empty slots while it ran). **`x64dbg.exe` is.**

Watcher XOR chrome (same title buffer): `PID:` **and** `Thread:` **and**
(`Module:` **or** `Main Thread`). Live x64dbg RU title used `Модуль:` so that
triple may miss; the leaf + `x64dbg` substring still fire. `GuiUpdateWindowTitle`
rewrites chrome every attach — 1 Hz `SetWindowText` lost the race.

## Bypass (no Relic `.text`, no OS export jmp)

| Layer | What |
|-------|------|
| Sibling path | **Not** leaf-only. PID **38172** packed from `...\x64dbg\release\x64\RuntimeBroker.exe`. Portable tree renamed: `C:\Program Files (x86)\x64dbg` → `...\rbhost`. Launch `release\x64\RuntimeBroker.exe` (keep `x64dbg.exe` but do not start it). |
| Watcher titles | Shared `ra_retitle.h`: chrome + `x64dbg` + `[CPU` + path contains `\x64dbg\`. Overlay 50 ms, WindowWatch 100 ms, injector once before APC. EnumChildWindows. Do **not** retitle WindowWatch |
| Attach PEB | `RaHideWipePebDebug`: `BeingDebugged=0`, `NtGlobalFlag &= ~0x70`. **Not** `NtQueryInformationProcess` (26508 `0x56FD3C0`) |
| Banned | Watcher/sibling `ret 1` (36000), user32/ntdll/kernel32 body jmp, Relic IAT / FairPlay `.rdata`, ScyllaHide HookLibrary in Relic as the hide |

`01010001` on 33376 attach was **not** only DebugPort. IDA `sub_7FF7A93C3200`
(`0x3C3200`): if Relic MZ entry byte is `0xCC` (`~*ep == 51`) it EventSchedule
+ Enqueue. Stock `x64dbg.ini` had `EntryBreakpoint=1` `TlsCallbacks=1`
`SystemBreakpoint=1` — attach plants INT3 in Relic `.text`, hasher/RA packs.
Patched those Events to `0` (elevated). Do **not** plant ntdll QIP. PEB wipe
still runs for BeingDebugged.

## Ritual

1. WindowWatch **on** (repo `x64\Release\WindowWatch.exe`).
2. Steam `-dev -nodbg -notrap`. Titled Relic window.
3. Elevated `DllInjector.exe`.
4. Elevated `Start-X64dbgHidden.ps1` → CREATE_SUSPENDED
   `RuntimeBroker.exe` + `titleboot.dll`, then resume.
5. MCP `debug_attach_pid` immediately (`attach_break=false`). Do not attach
   on PID-create (36208). Relic `taskkill` may fail even elevated — Task
   Manager End Task works (user 17:53).

Expect: launch stays `slots=0` if first-paint chrome is gone **and**
VERSIONINFO is not `x64dbg` (cycle 5–6: `rbhost` → no `20220002`; dbg-up
3 s still `begin=0`). RA window **lazy-allocates on first Enqueue** — there
is no empty `slots=0` window to wait for. Attach `01010001` with live EP
`0x48` (cycle 6 overlay edge) is **not** ctor `0x3EC3200`. Kernel DebugPort
/ hashed QIP; ntdll hook banned (`0x56FD3C0`).
