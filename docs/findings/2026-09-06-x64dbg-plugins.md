# 2026-09-06 — x64dbg plugins vs Relic WindowWatcher

Sources: [x64dbg wiki Plugins](https://github.com/x64dbg/x64dbg/wiki/Plugins)
(177 rev, 2026-01-09), GitHub topic `x64dbg-plugin`, repos below.
Installed now: `ScyllaHideX64DBGPlugin.dp64` + `HookLibraryx64.dll` + MCP
under `C:\Program Files (x86)\rbhost\release\x64\plugins\`.

Relic constraints: no Relic `.text`, no ntdll/user32 body jmp in Relic
(26508 `0x56FD3C0`). Hide is path/leaf + `SetWindowText` + no EP INT3.

## Verdict

| Plugin | Repo | Helps us? |
|--------|------|-----------|
| **ScyllaHide `WindowTitle=`** | [x64dbg/ScyllaHide](https://github.com/x64dbg/ScyllaHide) | **Yes — debugger-side only.** Already in `AOE4_WindowHide` as `Runtime Broker`. Does **not** need Inject DLL. `GuiUpdateWindowTitle` still appends `PID:`/`Thread:`/`Module:` — keep the 50–100 ms hammer |
| ScyllaHide **Inject DLL** / NtUser* / NtQIP | same | **No.** Hooks Relic ntdll/win32u. Same class as 26508 pack |
| [brock7/xdbg](https://github.com/brock7/xdbg) | 2016, abandoned | **No.** Usermode hooks in the debuggee (ScyllaHide predecessor) |
| [VenTaz/Themidie](https://github.com/VenTaz/Themidie) | Themida 3.x | **No.** Wrong protector; injects into target |
| [XeroNicHS/x64dbg_AttachHelper](https://github.com/XeroNicHS/x64dbg_AttachHelper) | restore `DbgBreakPoint` / `DbgUiRemoteBreakin` | **Maybe later.** Fixes anti-attach stubs in **ntdll**, not WW titles. Relic hasher sees ntdll 0xCC |
| [Vicshann/GhostDbg](https://github.com/Vicshann/GhostDbg) | “noninvasive” | **Next candidate** for attach `01010001`. Cycle 6: path+VERSIONINFO stay `slots=0`; attach with EP=`0x48` still packs. Old (2018–20), Defender flags it. Do **not** use TitanHide/HyperHide |
| [mrexodia/TitanHide](https://github.com/mrexodia/TitanHide) | kernel SSDT | **No.** README: never on a production box. 0x10E cloak already BSODed this machine |
| [Air14/HyperHide](https://github.com/Air14/HyperHide) | Intel EPT hypervisor | **No.** Driver + VT-x. Same risk class |
| [Tennn/Mirage](https://github.com/x64dbg/x64dbg/wiki/Plugins) | VT-x EPT | **No.** Same |
| [stonedreamforest/NaiHeQiao](https://github.com/stonedreamforest/NaiHeQiao) | archived | **No.** Debug-signal workaround, not window hide |
| Dedicated “strip x64dbg chrome title” plugin | — | **Does not exist** on the wiki / topic. `GuiUpdateWindowTitle` is what *creates* XOR chrome |

## What to use

1. Keep ScyllaHide **installed**. Profile `AOE4_WindowHide`: `WindowTitle=Runtime Broker`, NtUser hooks in the **ini** do nothing until Inject DLL — leave Inject off.
2. Do not add TitanHide / HyperHide / Mirage / xdbg / Themidie.
3. Title race: overlay 16 ms + NAMECHANGE + WindowWatch 16 ms + in-dbg
   `titlehide.dp64` (IAT `SetWindowTextW` in RuntimeBroker only).
