# 2026-09-06 — x64dbg crash-catch ritual (attach before inject)

Both post-BSOD injects died before a debugger attached. WindowWatcher can
count the **x64dbg window** without attach (`tag=0x20220002`); that is not
why 37124 / 27072 died (slots were empty). They AVed ~1 s after first
Present (`BEX64` `0xC0000005` RIP=0). x64dbg was not on the process, so
the exception was not caught. **Cloak off. No Relic `.text` FairPlay.**
Crash-fix code is sibling `2be1eff4` — this note is the debugger ritual.

Related: [windowwatcher hide](2026-09-06-x64dbg-windowwatcher-hide.md),
[37124 AV](2026-09-06-inject-37124-crash.md),
[inject-crash / HTTP intercept](2026-09-06-inject-crash.md),
[attach cycle](2026-09-06-attach-cycle.md). Canon: [UPDATE_GUIDE §2.3.1](../UPDATE_GUIDE.md).

## Why attach never happened

| Session | PID | DLL | Result |
|---------|-----|-----|--------|
| 16:42 | **37124** | FairPlay Relic `.text` jmps ON | Inject OK, slots empty, BEX64 ~1 s after Present. x64dbg never attached. Dump: `%LOCALAPPDATA%\CrashDumps\RelicCardinal.exe.37124.dmp` |
| 16:53 | **27072** (`0x69C0`) | current (`[RA] http intercept ON`, `text=0`, cloak OFF) | Same shape: OverlayBoot 16:53:29.360 → first Present 16:53:29.989 → Event 1000 16:53:30. Relic base `0x7FF632140000`. **Do not inject this DLL again until sibling says safe.** |

WER dump **27072** (exists):

`C:\Users\sshunko\AppData\Local\CrashDumps\RelicCardinal.exe.27072.dmp`

110 745 606 bytes, 16:53:32. Event 1001 BEX64 `P8=c0000005` `P9=00000008` `PCH_84_FROM_unknown+0`. Same class as 37124.

x64dbg MCP (`:3000`) was down for both; Relic was dead before File → Attach.

## Standing (this session)

| Item | Status |
|------|--------|
| x64dbg | **elevated** PID **17584** (`Start-Process -Verb RunAs`, TokenElevation=1). First start 2344 was medium-IL — killed. |
| ScyllaHide | `CurrentProfile=AOE4_WindowHide` in `...\x64\plugins\scylla_hide.ini` (NtUser window hooks + PEB BeingDebugged). |
| MCP | `http://127.0.0.1:3000/` `status: ok`. |
| Exception BP | `SetExceptionBPX C0000005` + enable — armed. Cleared 16 TLS-callback BPs (nv/steam) so Relic can run. |
| Relic | **attached** PID **27164** (start 17:04:00), base `0x7FF632140000`, debugger **running**, `0xC0000005` armed. Prior **15504** died 17:02 after inject (live break missed). Dump: `%LOCALAPPDATA%\CrashDumps\RelicCardinal.exe.15504.dmp`. |
| 27072 dump | `C:\Users\sshunko\AppData\Local\CrashDumps\RelicCardinal.exe.27072.dmp` |

## Loop (what we actually repeat)

**Keep x64dbg open.** Do not close it between injects. `DllInjector.exe` is not the patcher — `InternalInjector.dll` is.

```
x64dbg elevated + ScyllaHide   (once)
  → Steam -dev -nodbg
  → Attach (C0000005 first-chance)
  → elevated DllInjector
  → if AV: dump in dbg, patch InternalInjector, rebuild Release
  → Relic restart (DLL lock) ; x64dbg STAYS
  → Attach → inject → look at slots / RIP
  → repeat
```

Anti-pattern: close dbg → launch game → inject → open dbg. 37124/27072 died in the 1 s Present window with nobody attached.

## Ritual (next launch)

Use **x64dbg** (x64). Relic is 64-bit — not x32dbg.

1. **Start x64dbg first, always elevated** (before Steam / before inject):  
   `Start-Process -FilePath 'C:\Program Files (x86)\x64dbg\release\x64\x64dbg.exe' -Verb RunAs`  
   Do not start a medium-IL x64dbg (attach / inject `0x2E4`). Rule: `.cursor/rules/run-as-admin.mdc`.  
   **Plugins → ScyllaHide → Options → profile `AOE4_WindowHide` → OK.**  
   Copy/merge `AOE4HOOK/tools/scyllahide/scylla_hide.ini` into  
   `...\x64\plugins\scylla_hide.ini` and set `CurrentProfile=AOE4_WindowHide`  
   (stock VMProtect/Themida leave NtUser window hooks **off**).  
   Confirm ScyllaHide log: `NtUserBuildHwndList` / `FindWindowEx` /
   `QueryWindow` / `GetForegroundWindow` on. PEB `BeingDebugged` on.
   Everything else (KiUser, time, QSI, CRT, `PreventThreadCreation`) **off**.
2. Steam launch args: **`-dev -nodbg`**. Do not skip the leading space on
   `-nodbg` if Relic parses the cmdline token that way.
3. When `RelicCardinal.exe` is alive: **File → Attach** (or MCP
   `debug_attach_pid`) **immediately**. ScyllaHide injects HookLibrary on
   attach and marks the debugger PID protected.
4. Exception breakpoint: first-chance **`0xC0000005`**. Do not pass/ignore
   AV. On break: registers, `Alt+K` callstack, `minidump` / file dump.
5. **Then** inject (`DllInjector.exe` next to `Release\InternalInjector.dll`)
   — only after crash-fix sibling says the DLL is safe, or attach to a
   still-living Relic. Attach-after-inject is a fallback only if you can
   attach **before first Present** (~1 s window). The 16:42 / 16:53
   sessions lost that race.

Without overlay, ScyllaHide window hooks are the no-DLL path. They do
**not** cover sibling proc-scan `0x3F328D8` (process name `x64dbg.exe`).
Overlay default (user32 `GetWindowTextW` body + watcher stubs
`0x3F0A7D0` / `0x3F328D8` `ret 1`) covers that after inject. Title hide
alone misses the sibling. Research hashed chrome scan is
`GetWindowTextW` at **`0x3F0A910`**, not IAT `0x3F0B3EC` / `0x3F0C9E3`.

## Do not

- Inject until sibling `2be1eff4` says the DLL is safe, or Relic is
  already alive and you are only attaching.
- Re-inject the 16:42 DLL (Relic `.text` FairPlay) or treat 27072 as a
  “safe” current DLL — it already BEX64’d with `http intercept ON text=0`.
- CRT cloak / `AOE4H_RA_CLOAK` / PAGE_GUARD Relic `.text` / `--ra-veh`
  with VS (0x10E / UD2).
- Steam-launch from an agent unless the user asked. Wait for Relic, attach.

## Click order (user)

1. x64dbg already running **elevated** + **AOE4_WindowHide**.
2. Steam: AoE4 with `-dev -nodbg`.
3. In x64dbg: **File → Attach** → `RelicCardinal.exe` → Attach. F9 if
   stopped at system/entry BP so the game runs under the debugger.
4. Options → Preferences → Exceptions: **do not ignore** `C0000005`.
   Command: `SetExceptionBPX C0000005`.
5. Sibling injects. Stay attached. On AV: dump + callstack; do not
   continue blindly.

MCP: plugin `auto_start_mcp_on_plugin_load` is true (`:3000`). Cursor
namespace `user-x64dbg`. Health `GET http://127.0.0.1:3000/`.

## PID 36208 (17:16) — game first, attach immediately (no inject)

User asked: launch Relic **first**, then go to x64dbg immediately (do not
pre-wait attach-before-Steam). x64dbg 17584 stayed open. No inject.

| Field | Value |
|-------|--------|
| PID | **36208** then a second Relic **40340** (Steam respawn?) |
| Relic base | `0x7FF759C30000` |
| Attach | MCP `debug_attach_pid` as soon as PID existed (title still empty) |
| Pause | RIP `0x7FF75DACD280` = **`+0x3E9D280`** (IDA: not a function; bytes `27` / `int1` junk). Stack 1 frame `from=0` |
| Exception | first-chance `C0000005` (armed). Switched to second-chance + `run` |
| After run | `state=running` ~2s, still no window title; then Relic **gone**. x64dbg `stopped`. No WER this window |
| Overlay | **not loaded** |

Attach-on-PID-create (pre-window) + first-chance AV is **lethal at boot**.
Next: wait for titled Relic window, then attach; keep `C0000005` **second-chance**
unless hunting JUMPOUT live.
