# 2026-09-06 — OS-body hide (no Relic `.text`) for slots + x64dbg

Goal: stop RA slot packs **and** the ~1 min hang/kick when x64dbg is visible,
without hasher-visible Relic `.text` (JUMPOUT / 36000 IAT pack).

Related: [window-hide-default](2026-09-06-window-hide-default.md),
[windowwatcher hide](2026-09-06-x64dbg-windowwatcher-hide.md),
[36000](2026-09-06-inject-crash.md#pid-36000-1714--watchersibling-ret-1-only-iat-pack-kick),
[36208 attach-on-PID](2026-09-06-x64dbg-crash-catch.md#pid-36208-1716--game-first-attach-immediately-no-inject).

## IDA (runtime_exe.i64 `0x7FF7A5500000`)

| RVA | Name | Role |
|-----|------|------|
| `0x3DD2550` | `RA_Enqueue` | lock `0x7AF6DC0` stride `0x198`; tag check `sub_*(a3, 0x20DE00AD, 0x01010001)` |
| `0x3F0A7D0` | `RA_WindowWatcher` | titles via hashed `GetWindowTextW`; pack `0x20220002` |
| `0x3F328D8` | `RA_WindowWatcher_Sibling` | process-name walk → same enqueue tag; **0 named callers** |
| `0x56FD380` / `0x56FD3C0` | slot `+10` on 36000 | **0 xrefs** in IDB; overlay “IAT extra”; not Toolhelp IAT `0x56DE820` |
| `0x08050001` | immediate | enqueue `0x3DD26A4` / `0x3DD28EC` + one UnDecorator false-positive |

`CreateToolhelp32Snapshot` IAT xrefs are CRT thunks (`0x64EC40` class), **not**
Watcher/sibling. Sibling hashed-GPA’s the OS export (same pattern as
`GetWindowTextW` `0x7AFDE08`). Hooking the **kernel32/ntdll body** still
catches that. Patching Relic IAT is the `0x56FD3C0` pack.

`0x20220002` as a raw immediate: **0 hits** (built in-reg). `0x20DE00AD`: 13
sites around enqueue / integrity.

## Why Relic `.text` stubs failed

PID **36000**: watcher+sibling `ret 1` → WW pack gone, then `08050001`/`08060001`
`slots=8 accum=0` → kick ~4s. Hasher sees those two Relic patches.

PID **7764**: neutralize OFF + user32 hide → Present lived, then WW `slots=7`
(process scan still saw `x64dbg.exe` / `WindowWatch.exe`).

## Patch (superseded 17:28 — do not replant)

Evening PIDs 36540 / 26508 / 10192: **any** OS export-body jmp (user32 /
kernel32 / ntdll) packed `08060001` `+10=0x56FD3C0` ~2 s after OverlayBoot.
Hook machinery remains in `ra_hide.cpp` but **`RaHideInstallUser32Body` does
not plant**. Hide is `SetWindowText` retitle only.

`AOE4H_RA_TEXT_NEUTRALIZE` default **0**. No hasher / enqueue / FairPlay
`.text`. Cloak off. HTTP intercept off.

## Ritual (user, 17:17)

1. Close x64dbg. **WindowWatch can stay** (26508: slots=0 until OverlayBoot).
   Prefer repo `x64\Release\WindowWatch.exe` — writes `Logs\ra_window.log`.
2. Launch game (`-dev -nodbg`). Wait for **titled** window.
3. Elevated `DllInjector.exe`.
4. Start x64dbg elevated, **attach immediately** (after inject).
5. Do **not** attach on PID-create before the window (36208 boot AV).

## Verify log

Expect: `[RA] hide ON retitle=N bodies=0` and
`[RA] neutralize OFF (compile-time AOE4H_RA_TEXT_NEUTRALIZE=0…)`.
WindowWatch stays `slots=0` after inject (26508 proof: 0 until OverlayBoot).
Sibling may still pack when `x64dbg.exe` exists.

## PID 36540 (17:22) — first cycle, QSI was lethal

Closed x64dbg/WindowWatch, titled Relic, inject, **then** started x64dbg.

| Field | Value |
|-------|--------|
| PID | **36540** |
| OverlayBoot | 17:22:30.967 |
| Hide | GWTW/A + FindWindowW + **ntdll QSI stolen=16** + kernelbase `K32EnumProcesses`. Process32 steal=0 |
| Neutralize | OFF |
| Slots | 17:22:32.591 **4** `08060001` `+10=0x56FD3C0` — **before** x64dbg existed (x64dbg 17:22:36) |
| Dead | log stops 17:22:32.677 (~2 s). No FOCUS after first. |

ntdll syscall-stub hook / EnumProcesses body is hasher-or-IAT visible. **Removed**.
Process32 decoder extended (`4C 8B DC` + `xor r32`) so Toolhelp can plant without ntdll.

## PID 26508 (17:24) — Process32+QFPI, no QSI

`proc=1 qfpi=1 find=1 qsi=0`. Relic lived past first Present. At 17:24:15
`slots=4 accum=0` same `0x56FD3C0` pack **without** x64dbg. Dead before
x64dbg attach (x64dbg 39100 came up, Relic already gone).

OS body hooks other than user32 `GetWindowText*` are IAT-visible. Reverted
install to **user32 titles only** (7764-safe). Toolhelp/QSI/QFPI stay in
source but not planted.

## PID 10192 (17:25) — user32 titles only, still IAT pack

`user32=2 proc=0 qsi=0`. Present 17:25:05.140. `slots=4` 17:25:06.889.
Last FOCUS 17:25:08.371. Relic dead. x64dbg was **closed**. So `0x56FD3C0` /
`08060001` is **not** “x64dbg window”. It fires after overlay inject even
with only `GetWindowTextW/A` bodies. 7764 (17:05) survived the same hide —
not reproduced this evening. No live BP session.

## WindowWatch 26508 (user paste, 17:24) — inject wrote the pack

PID **26508**, Relic `0x7FF69EEB0000`, enqueue `0x3DD2550`, stride `0x198`.

| Time | WindowWatch |
|------|-------------|
| 17:24:07–17:24:12 | **slots=0** `uninit/empty` — WW already attached, **no overlay yet** |
| 17:24:13+ | **slots=4** `begin=0000015E4D5FD7C0` through 17:24:24 |

OverlayBoot for that PID was **17:24:11**. Hide did **not** fail to hide
x64dbg. **LoadLibrary + user32/Toolhelp bodies** wrote the 4-slot
`08060001` / `+10=0x56FD3C0` pack. WindowWatch being visible did **not**
fill slots for six seconds pre-inject.

`0x56FD3C0` is an integrity descriptor (`RA_Integrity_Dispatcher` `0x3E44034`),
**not** Relic IAT of `GetWindowTextW` (that IAT is `0x56DF2C0`).

## Patch (17:28) — no OS export jmp

Any in-process export-body jmp (user32 / kernel32 / ntdll) trips
`0x56FD3C0`. Even GWTW-only (10192).

Hide is now **SetWindowTextW** on dbg HWNDs (`x64dbg` / `WindowWatch` / CE /
IDA / … — **not** Cursor/VS). Relic reads bland titles through the **real**
`GetWindowTextW`. `DllInjector` retitles **before** APC `LoadLibraryW`.
Overlay `RaHideTick` repeats every 1s. PEB unlink of this DLL stays.
Log: `[RA] hide ON retitle=N bodies=0`.

Does **not** hide `x64dbg.exe` from sibling `0x3F328D8` (process name).
If slots=4 again with **zero** export hooks, next suspects: PEB unlink,
DXGI Present hook, or LoadLibrary of `InternalInjector` itself.

## WindowWatch file tape (17:33)

External RPM stays the parallel monitor (survives Relic death; pre-inject).
Same 1 Hz line from the DLL (`src=dll`) after OverlayBoot. One file:
`Documents\AOE4HSettings\Logs\ra_window.log`. Do not retitle WindowWatch
(removed from hide needles). Relic `.text` still banned.

## PID 37388 (17:37) — bodies=0, still `0x56FD3C0`

Titled Relic (`-dev -nodbg -notrap`), WindowWatch already up, x64dbg **closed**.
Elevated inject. Log: `[RA] hide ON retitle=1 bodies=0`, neutralize skipped,
`hideText=0`, PEB unlink ok. First Present 17:37:59 (window still
`uninit/empty`). Then:

| Time | slots |
|------|--------|
| 17:38:01.976 | **2** `08060001` `+10=0x56FD3C0` |
| 17:38:02.233 | **4** same pack kinds 6/3/1/5 |
| 17:38:03 | last FOCUS; Relic gone, no WER |

OS export jmp is **not** required for this pack. Next isolate: PEB unlink
**and** Relic IAT / `.rdata` FairPlay+VAC pokes OFF (kind 5 = IAT extra;
UPDATE_GUIDE already forbids Relic IAT `0x56FD3C0`). Relic `.text` still
banned. DXGI Present stays (overlay).

## PID 33376 (17:40) — IAT/strings + PEB off, **lived**

Same ritual. Log: `PEB unlink OFF`, `xbox Relic IAT/strings OFF`, `bodies=0`,
`hidePeb=0 hideText=0`. First Present 17:40:02, snapshot empty. **No**
`MULTI_SLOT` / `0x56FD3C0` through 17:40:50+. Relic **alive**, FOCUS, ~70 fps
menu. WindowWatch stayed up. x64dbg not attached this pass.

Cause of 37388 pack was Relic IAT / `.rdata` pokes (FairPlay + Steam IAT),
not PEB unlink alone (both went off together). Relic `.text` still banned.

## PID 33376 (17:42) — x64dbg attach after inject

Inject already live (~2 min, slots empty). Elevated x64dbg + MCP
`debug_attach_pid` **without** system-breakpoint pause. Attach **ok**,
Relic stayed up. At 17:42:33 Relic saw the debugger:

- `WINDOW_WATCHER` `tag=20220002` + extra `01010001` / `01040001`
- `slots=11 accum=600` (not the `0x56FD3C0` IAT pack)
- `-nodbg` re-armed; neutralize stayed compile-off
- FOCUS continued; x64dbg title still `PID:` / `Thread:` / `Module:`
  (SetWindowText did not stick on x64dbg chrome)

Sibling `0x3F328D8` still sees `x64dbg.exe`. Do **not** plant watcher
`ret 1` (36000). Bypass: bland leaf `RuntimeBroker.exe` + 50–100 ms
retitle + PEB wipe — [ww-launch-attach](2026-09-06-ww-launch-attach.md).
Do **not** inject ScyllaHide HookLibrary into Relic (ntdll body = `0x56FD3C0`).

## Relic `.text` is banned

User: patch in Relic `.text` previously caused **instant crash** (36000 IAT
pack / JUMPOUT / BEX64). Do **not** plant watcher/sibling `ret 1`, hasher,
enqueue, FairPlay jmp, or latch3 as hide. Compile `AOE4H_RA_TEXT_NEUTRALIZE=0`.
Boot/UI/config no longer request neutralize (`ra_neutralize=0`). Hide stays
`SetWindowText` only.
