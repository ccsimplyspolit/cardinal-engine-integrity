# 2026-09-06 — Window hide + watcher stubs are DEFAULT

Build **16.3.11308.0**. IDB: `runtime_exe.i64` imagebase `0x7FF7A5500000`.
Cloak stays **off** (0x10E NVIDIA UMD / CRT memcpy). Do not set `AOE4H_RA_CLOAK`.

## Why

WindowWatcher `tag=0x20220002` fires when a debugger **window** is visible to
Relic — attach is not required. Old ritual: close x64dbg/WindowWatch → inject →
`[RA] neutralize ON` → then open dbg.

## IDA: GetWindowTextW is Watcher-only

Relic calls `GetWindowTextW` only at:

| RVA | Role |
|-----|------|
| `0x3F0A910` | Hashed `GetWindowTextW` — XOR chrome + title-hash table |
| `0x3F0B3EC` | IAT `GetWindowTextW` — python / CE-host path |
| `0x3F0C9E3` | IAT `GetWindowTextW` — same path, python-leaf only |

Hashed GPA cache: `0x7AFDE08` (helper `0x3F87250`). Those IAT sites are the
**python / CE-host** branch. Primary x64dbg chrome read is hashed
`GetWindowTextW` at `0x3F0A910` (XOR `PID:` / `Thread:` / `Module:` /
`Main Thread`). Length / EnumWindows / FindWindow are not Watcher IAT
callees on this build. Research: [2026-09-06-x64dbg-windowwatcher-hide.md](2026-09-06-x64dbg-windowwatcher-hide.md).

## Default at inject (not opt-in)

| Layer | Default |
|-------|---------|
| user32 `GetWindowTextW` hide | ON (`[RA] hide ON user32_body=…`) |
| Watcher `0x3F0A7D0` + sibling `0x3F328D8` | **pass** (`ret 1`; `ret 0` → ExitProcess) |
| D02C / F448 | pass |
| enqueue / timerq | fail |
| CRT memcpy cloak / PAGE_GUARD / KiUser / `--ra-veh` | **OFF** |
| `--bare` | no hide, no neutralize |

DllInjector / Standalone publish `kInjectBootDefault` (includes
`kInjectBootHideWindows` + `kInjectBootRaNeutralize`). Mapping miss applies the
same defaults. `config.ini` `[scripts] ra_neutralize` default is **1**.

x64dbg / WindowWatch / VS / CE **may be open before inject**. Inject ASAP so
hide is live before the ~3s Watcher tick.

## Without overlay

`AOE4HOOK/tools/scyllahide/scylla_hide.ini` profile **AOE4_WindowHide**:
`NtUserQueryWindow` / `NtUserBuildHwndList` / `NtUserFindWindowEx` /
`NtUserGetForegroundWindow`. Apply in x64dbg: Plugins → ScyllaHide → Options →
that profile → inject HookLibrary into Relic **before** opening other tool
windows if you can. See `tools/scyllahide/README.md`.

## Never stub

Kick ctor `0x3E691F4`, `45E8` (`0x3E545E8`), thunk `0x3E46FF8`, walker
`0x3E47000`, hasher `0x3E57050`.

## Verify

Log: `[RA] hide ON` + `[RA] neutralize ON … watcher=`. Do not double-inject if
Relic already has this DLL.
