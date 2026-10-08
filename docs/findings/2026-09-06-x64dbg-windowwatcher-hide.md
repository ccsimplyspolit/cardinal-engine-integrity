# 2026-09-06 — hide x64dbg from Relic WindowWatcher (research)

Build **16.3.11308.0**. IDB: `runtime_exe.i64` session `a1220dbc`, imagebase
`0x7FF7A5500000`. Overlay C++ (user32 body hide + watcher `ret 1`) is owned by
sibling implement workstream — this note is IDA / ScyllaHide only. **Cloak off.**

Related: [window-hide-default](2026-09-06-window-hide-default.md) (overlay
policy), [ra-hasher-windowwatcher](2026-09-06-ra-hasher-windowwatcher.md),
[ida-ra-analysis](2026-09-06-ida-ra-analysis.md) §C, profile
`AOE4HOOK/tools/scyllahide/`.

## Verdict

Opening the **x64dbg window** is enough for pack `tag=0x20220002`
(`slots=3 accum=600`). Attach is not required. `-nodbg` does not cover this.

| Layer | What it stops | What it misses |
|-------|---------------|----------------|
| Overlay user32 `GetWindowTextW` body | Hashed GPA + IAT title reads | Sibling **process** scan `0x3F328D8` |
| Overlay Watcher + sibling `ret 1` | Whole pack | Hasher / JUMPOUT (different path) |
| ScyllaHide `AOE4_WindowHide` | HWND list / FindWindow / FG; `IsWindowBad` title `x64dbg` / `[CPU` | Does **not** hook `GetWindowTextW`. `NtQuerySystemInformation` is **off**, so `x64dbg.exe` stays on a Toolhelp/QSI walk. `WindowWatch` is not in ScyllaHide needle lists |
| Title rename / `00_retitle.lua` / rename exe | Weak alone (1 Hz lost the race) | Pair with 50–100 ms hammer + `RuntimeBroker.exe` leaf. See [ww-launch-attach](2026-09-06-ww-launch-attach.md) |

Default overlay hide + stubs is enough to keep x64dbg open **before** inject.
Without overlay: inject ScyllaHide `AOE4_WindowHide` into Relic first, and do
not treat that as a full substitute for the sibling `ret 1` stubs.

## Relic does not IAT-call GetWindowTextW for the x64dbg chrome scan

`GetWindowTextW` **IAT** xrefs (USER32 `0x56DF2C0`) are **only** these two,
both inside `RA_WindowWatcher` `0x3F0A7D0` (size `0x422F`, 0 named callers):

| RVA | VA | Role |
|-----|-----|------|
| `0x3F0B3EC` | `0x7FF7A940B3EC` | After exe-leaf / `python` prefix. Title vs allowlist (IME / EmbeddedMenu / MenuWindow / TtkMonitor) |
| `0x3F0C9E3` | `0x7FF7A940C9E3` | Same path, only if `wcsstr(leaf, "python")==leaf` or helper `0x3E73764` |

Those sites are the **python / CE-host** branch, not the first x64dbg title
gate. Buffer is `WCHAR[512]`.

Primary title read is hashed-GPA helper `sub_…7250` (`0x3F87250`), FNV-1a
unbounded name hash `0x3AB480FDFB9CEE95` = `GetWindowTextW`, cache
`0x7AFDE08`. Call sites inside Watcher:

| RVA | Role |
|-----|------|
| `0x3F0A910` | Early title → XOR `wcsstr` chrome (below) + 88-entry title-hash table |
| `0x3F0E442` | Late title, paired with hashed `GetClassNameW` at `0x3F0E430` → `_wcsicmp` |

Hooking the **user32 export body** catches both hashed GPA and IAT. Patching
Relic IAT does not (pack `0x56FD3C0` / `0x20DE00AD`).

## Decoded XOR chrome (first title gate)

Needles are not plaintext in the image. Hex-Rays `wcscpy` + XOR:

| XOR key | Cipher (wchar) | Plain |
|---------|----------------|-------|
| `0x4F` (79) | `1F 06 0B 75` | `PID:` |
| `0x57` (87) | `03 3F 25 32 36 33 6D` | `Thread:` |
| `0x7A` (122) | `37 15 1E 0F 16 1F 40` | `Module:` |
| `0x17` (23) | `5A 76 7E 79 37 43 7F 65 72 76 73` | `Main Thread` |

Control flow is nested: `PID:` **and** `Thread:` **and** (`Module:` **or**
`Main Thread`) in the **same** `GetWindowTextW` buffer. Default x64dbg main
title (`filename - PID: %X [arch]`) has `PID:` only — this gate is Olly / verbose
chrome, not the string `x64dbg`. Overlay hide still blanks any title that
contains `PID:` / `Thread:` / `x64dbg` / … as a **superset**.

Plaintext `x64dbg` / `Cheat Engine` in the binary: **0**. No Frida string either:
`0x65E052C` is `Friday` from a weekday-name table next to HTTP-digest `auth-int` /
`userhash`; `frida-agent` / `gum-js-loop` have 0 hits (see
[IDA RA](2026-09-06-ida-ra-analysis.md#fairplay--ess--telem-autoscan-send-vs-ra-local)).

Still open: full 88-entry title-hash table at `unk` RVA `0x570C730`
(`0x7FF7AAC0C730`), and the late XOR title/class pair
`qword_7FF7ACFFCBD0` / `qword_7FF7ACFFCBF0`.

## Other hashed USER32 in the same Watcher prologue

Same FNV walk (basis `2166136261`, prime `16777619`, ASCII fold `| 0x20`).

| Helper RVA | Cache RVA | Hash | API |
|------------|-----------|------|-----|
| `0x3F87250` | `0x7AFDE08` | `0x3AB480FDFB9CEE95` | `GetWindowTextW` |
| `0x3F84F40` | `0x7AFDE00` | `0x51321B68AF96EF7F` | `GetClassNameW` |
| `0x3F873EC` | `0x7AFBB70` | `0x276383811CA03E79` | `GetWindowThreadProcessId` |
| `0x3F8771C` | `0x7AFDE50` | `0x07416F73B139DF49` | `IsWindowVisible` |
| `0x3F870B0` | `0x7AFDE70` | `0xF57910761A8C88A9` | `GetWindowRect` |

Early skip: no PID / own PID / not visible / tiny or extreme-aspect rect
(`< 66049` px or aspect `< 0.25`) → `return 1` (no pack).

No IAT `EnumWindows` / `GetClassNameW` / `GetWindow`. Watcher is an HWND
callback (data xrefs only). Sibling `0x3F328D8` (size `0x1974`) **does not**
call `GetWindowTextW` or `…7250` / `…4F40` — process-name path, same enqueue
`a2=200` `tag=0x20220002` (`539099138`).

## ScyllaHide vs this Watcher

Stock x64dbg plugin ini (`…\plugins\scylla_hide.ini`) ships
`CurrentProfile=VMProtect x86/x64` with **window hooks off**. That profile
does not hide HWND lists.

Repo profile `AOE4HOOK/tools/scyllahide/scylla_hide.ini` **AOE4_WindowHide**:

- ON: `NtUserBuildHwndList` / `NtUserFindWindowEx` / `NtUserQueryWindow` /
  `NtUserGetForegroundWindow`, PEB `BeingDebugged`
- OFF: KiUser, time, `PreventThreadCreation`, CRT, `NtQuerySystemInformation`

ScyllaHide `IsWindowBad` (`HookHelper.cpp`, upstream x64dbg/ScyllaHide):

- Title contains: `x64dbg`, `x32dbg`, `[CPU`, `Debug`, `ida`, `Cheat Engine`, …
- Class contains: Olly / IDA / WinDbg / Immunity — **not** modern Qt
  `Qt5QWindowIcon`
- Process list (only if QSI hook is on): `x64dbg.exe`, `devenv.exe`, …

`Inject DLL` from the x64dbg plugin also marks the **debugger PID** protected,
so every x64dbg HWND is stripped even if the title was renamed.

Gaps without overlay stubs:

1. Relic sibling still sees `x64dbg.exe` (QSI hook off by design here).
2. `WindowWatch` / `DllInjector` / Cursor titles are not in `BadWindowTextList`.
3. If Relic walks HWND via a path that is not `NtUserBuildHwndList` /
   `FindWindowEx`, titles still flow through hashed `GetWindowTextW`.

Do not enable cloak / PAGE_GUARD / KiUser on this profile (0x10E).

## Ritual (research)

**With overlay (sibling default):** dbg may be open → Steam `-dev -nodbg` →
`DllInjector.exe` → log `[RA] hide ON` + `[RA] neutralize ON … watcher=`.
Inject ASAP vs the ~3s Watcher tick.

**Without overlay:** copy/merge `AOE4_WindowHide` over the x64dbg plugin ini →
start Relic → ScyllaHide Options → that profile → Inject HookLibraryx64 into
Relic **before** other tool windows if you can → then open x64dbg / attach.

Never stub: kick ctor `0x3E691F4`, `45E8` `0x3E545E8`, thunk `0x3E46FF8`,
walker `0x3E47000`, hasher `0x3E57050`.
