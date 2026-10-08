# 2026-09-06 — x64dbg settings audit for Relic WW / attach

Sources: x64dbg `SettingsDialog.h` / `SettingsDialog.cpp` (development),
`debugger.cpp` `GuiUpdateWindowTitle`, help Events / Exceptions / Other
settings, TitanEngine `UE_ENGINE_SAFE_ATTACH`. Live ini:
`C:\Program Files (x86)\rbhost\release\x64\x64dbg.ini`.
Apply: `AOE4HOOK/tools/x64dbg-hidden/Apply-X64dbgAoe4Ini.ps1` (elevated;
also called from `Start-X64dbgHidden.ps1`).

Relic constraints unchanged: no Relic `.text`, no OS export jmp, no
HookLibrary in Relic, no PEB LDR unlink, cloak OFF. Hide stays path/leaf +
`SetWindowText` hammer.

## Title chrome — no ini kill switch

`DebugUpdateTitle` always formats:

`%s - PID: %s - %sThread: %s%s%s`

(`Gui` `WindowLongPath` only swaps leaf vs full debuggee path). There is
**no** setting that strips `PID:` / `Thread:` / `Module:`. Keep the 50–100 ms
hammer. **Do not** set `WindowLongPath=1` (longer title, same XOR needles).

Keep `Language=ru_RU`. Live RU titles used `Модуль:` so the XOR triple
(`Module:` or `Main Thread`) may miss; `en_US` would add `Module:`.

## Applied (debugger-side only)

| Section | Key | Value | Why |
|---------|-----|-------|-----|
| Events | `EntryBreakpoint` `SystemBreakpoint` `TlsCallbacks` `TlsCallbacksSystem` + all other event pauses | `0` | Relic `0x3C3200` packs `01010001` if image EP byte is `0xCC`. Stock defaults plant INT3. Help “Attach Breakpoint” is **not** a separate ini key in current SettingsDialog (attach pause is `SystemBreakpoint`). |
| Engine | `SafeAttach` | `1` | NtDebugActiveProcess attach. **Does not** write Relic `.text`. |
| Engine | `SkipInt3Stepping` | `1` | Step over INT3; does **not** plant `0xCC`. |
| Engine | `DetachOnExit` | `1` | Close dbg without killing Relic. |
| Engine | `DisableAslr` | `0` | **Must stay 0** — would rewrite Relic PE. |
| Engine | `EnableDebugPrivilege` | `1` | Needed for attach. |
| Engine | `EnableSourceDebugging` | `0` | Extra symbol/source work; off. |
| Engine | `NoConsoleWindow` | `1` | Hide TitanEngine console HWND. |
| Engine | `VerboseExceptionLogging` | `0` | Less log spam; no hide effect. |
| Engine | `MaxSkipExceptionCount` | `0` | `erun` never stops skipping first-chance. |
| Engine | `BreakpointType` | `0` | Left INT3-short. UD2 still writes Relic `.text` on user BPs. |
| Gui | `WindowLongPath=0` | See title. |
| Gui | `ShowAttachConfirmation=0` | Faster MCP attach; no extra dialog. |
| Gui | `NoForegroundWindow=1` | Already on; don’t steal focus. |
| Gui | `NoCloseDialog=1` `ShowExitConfirmation=0` | Less titled dialogs. |
| Misc | `CheckForAntiCheatDrivers=0` | Extra driver enum / popup; not a Relic write, just noise. |
| Misc | `QueryProcessCookie=0` `QueryWorkingSet=0` | Extra `NtQuery*` into Relic. Stay off. |
| Misc | `TransparentExceptionStepping=1` | Keep. |
| Exceptions | `C0000005-C0000005:second:log:debuggee` + unknown `00000000-00000000:first` | First-chance AV at Relic `+0x3E9D280` (36208) no longer pauses attach. Second-chance still breaks. |

Do **not** set JIT (`setjit`) — Relic crash would pop x64dbg as AeDebug.

## ScyllaHide live profile was wrong

`plugins\scylla_hide.ini` `[AOE4_WindowHide]` had `WindowTitle=x64dbg`,
`DLLNormal=1`, NtUser hooks `1`, `PebBeingDebugged=1`. `DLLNormal=1` is
HookLibrary inject on attach → ntdll body → `0x56FD3C0`. Forced:

- `CurrentProfile=AOE4_WindowHide`
- `DLLNormal=0` and all NtUser / NtQIP / PEB hooks `0`
- `WindowTitle=Runtime Broker` (debugger-side only; `GuiUpdateWindowTitle`
  still appends chrome — hammer remains)

Repo copy `AOE4HOOK/tools/scyllahide/scylla_hide.ini` matched.

## Left off on purpose

| Setting | Why not |
|---------|---------|
| `DisableAslr` | Rewrites Relic PE |
| `QueryProcessCookie` / `QueryWorkingSet` | Extra queries into Relic |
| `WindowLongPath` | Worse titles |
| ScyllaHide Inject / NtUser* / KillAntiAttach | Relic hasher / ntdll `0xCC` |
| TitanHide / HyperHide | kernel / 0x10E class |
| Changing `Language` to English | Adds `Module:` needle |
| `BreakpointType` UD2 | Still a Relic `.text` write when we BP |

## Hide race fix (same day, continue)

Documented overlay hammer was **50 ms**. Real call site was `EngineFogService`
**250 ms** (Present). `GuiUpdateWindowTitle` wins that race.

Applied:

- Overlay: `RaHideTick` every Present (16 ms gate) + dedicated 16 ms thread +
  `EVENT_OBJECT_NAMECHANGE` out-of-context (no INCONTEXT — that would inject
  into Relic).
- WindowWatch: retitle 16 ms + NAMECHANGE pump; RPM still 100 ms.
- RU chrome needles: `Поток:` / `главный поток` (plus existing `Модуль:`).
- Debugger-side plugin `titlehide.dp64`: IAT + **delay-import** of
  `SetWindowTextW/A` and `SendMessageW(WM_SETTEXT)` (Qt path). Rescan
  modules after 1.5 s. No IAT work in `DllMain`. Overlay hide thread uses
  `MsgWaitForMultipleObjects` so NAMECHANGE is not stuck behind
  `WaitForSingleObject`. `Start-X64dbgHidden.ps1` self-elevates.

## Live cycle PID **38692** (18:12)

Steam `-dev -nodbg -notrap`. Visible Relic HWND `n=37` was already
`Age of Empires IV -dev -nodbg -notrap`. A broken `StringBuilder` dump
printed only `A` — wait script missed it. Detect titled = **visible +
GetWindowText length ≥ 10**, not a string match on the first char.

| t | slots |
|---|---|
| 18:12:04 inject | empty (`hide ON retitle=0 bodies=0`, neutralize OFF) |
| 18:12:21 dbg start (`titlehide` + rbhost) | **3** `20220002` kinds 6/1/3 |
| 18:14:36 MCP attach | **11** + `01010001`/`01040001` |

Relic EP `0x7FF7928F0884` bytes `48 83 EC 28` — **not** `0xCC`. Events=0
did its job. `01010001` on attach is a **different** scanner than EP INT3.

## WindowWatch console for the same PID

User paste matches `WindowWatch\main.cpp` wait/RPM, not a miss:

1. `[----:--:--] waiting for RelicCardinal.exe...` — `FindPid()` was 0
   (WW up **before** Relic). Old build printed a fake clock.
2. `[pid=38692] OpenProcess/module failed err=299` — first
   `CreateToolhelp32Snapshot(SNAPMODULE)` while Relic still mapping.
   Next second: `base=0x7FF78D940000 attached`.
3. `18:09:42`–`18:12:20` `slots=0 (uninit/empty)` — RA heap not allocated.
4. `18:12:21` `slots=3` — dbg start (`20220002`).
5. `18:14:36` `slots=11` — MCP attach.

WW now prints a real clock, says “not in process list” vs snapshot error,
retries 299 in 100 ms, and falls back to `EnumProcessModulesEx` / PEB base.

## Fix after that log (same evening)

`slots=3` at dbg **start** is Watcher kinds 6/1/3 (`+10` RVA `0x56FA5A0`),
not sibling `\x64dbg\` path. `titlehide` loaded as a plugin **after** the
first `GuiUpdateWindowTitle` chrome. Relic’s ~1 s Watcher won.

`01010001` on this attach is **not** `sub_7FF7A93C3200` (RVA `0x3EC3200`):
that packs only if Relic MZ entry byte is `0xCC` (`~*ep == 51`). Live EP was
`48 83 EC 28`. Other `0x01010001` immediates exist (`0x7FF7A99A493B` …).
Hiding kernel `DebugPort` still needs an ntdll hook → `0x56FD3C0`. Overlay
PEB wipe stays; do not plant QIP.

Shipped:

- `titleboot.dll` injected into **RuntimeBroker.exe** while CREATE_SUSPENDED
  (debugger only). IAT `SetWindowText` / `SendMessage(WM_SETTEXT)` **always**
  bland before the GUI thread runs.
- `titlehide.dp64` same always-bland policy.
- `Start-X64dbgHidden.ps1` CreateProcess suspended + LoadLibraryW titleboot;
  hammer uses GetWindowText **return length** (old C# `StringBuilder` miss).
- DllInjector UI-thread wait: `GetWindowTextW` length **≥ 10** (skip AMD
  `A`/`M`/`D`).
- WindowWatch wait/299 messages (built). Overlay 1 ms hide thread is in
  source; `InternalInjector.dll` **LNK1104** while Relic 38692 holds it.
