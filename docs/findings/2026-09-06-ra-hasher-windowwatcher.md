# 2026-09-06 — RA hasher, JUMPOUT hang, WindowWatcher pack

Build **16.3.11308.0**. IDB: `K:\aoe4_dlc\dumps\RelicCardinal_60644_20260906_full_analysis\ida\runtime_exe.i64` (MCP session `a1220dbc`, imagebase **`0x7FF7A5500000`**). RVAs only.

## Timer / window path

```text
fail → RA_EventSchedule (0x3DD15E4) → timerq push (0x3E672DC) → list @ 0x7AF6D88
     → RA_Enqueue (0x3DD2550) → slot window + kick ctor (0x3E691F4)
```

Window `.data` (same as UPDATE_GUIDE §3.3): lock `0x7AF6DC0`, begin `0x7AF6DC8`, end `0x7AF6DD0`, cap `0x7AF6DD8`, accum `0x7AFB750`, flag `0x7AFB758`, stride `0x198`.

## Two different “slots=3 accum=600”

| Pack | Meaning |
|------|---------|
| WindowWatcher `tag=0x20220002` | Debugger **window** visible (x64dbg opened, even without attach). `slots=3 accum=600` |
| TOP fail pack | Same slot count can be the 2s/120s/180s RA fail pack — confirm tag / log |

Opening **x64dbg’s window** is enough. `WindowWatch.exe` attach itself counts as a “debugger window” if it is up **before** overlay neutralize.

User log 15:35 pid **17024**, base `0x7FF73EE70000`: uninit → 2s later `slots=3 accum=600` = WindowWatcher, not JUMPOUT.

Cloak inject later: pid **33736** @ 16:05. DllInjector warned `devenv.exe` already open.

## Never stub

| RVA | Role |
|-----|------|
| `0x3E691F4` | Kick ctor |
| `0x3E545E8` (`45E8`) | Integrity / hash path — `mov eax,1; ret` **boot-kills** |
| `0x3E46FF8` | Thunk |
| `0x3E47000` | Walker |
| `0x3E57050` | Hasher (raw-loads `a1`) |

## Pass / fail stubs (neutralize)

| RVA | Neutralize |
|-----|------------|
| Watcher `0x3F0A7D0` + sibling `0x3F328D8` | **pass** (`ret 1`). `ret 0` → `ExitProcess` |
| Enqueue `0x3DD2550` + timerq `0x3E672DC` | **fail** (`xor eax,eax; ret`) |
| D02C / F448 | **pass** |

## Hasher vs memcpy cloak (IDA)

Memcpy/memmove cloak is **not** enough. Hasher `0x3E57050` raw-loads `a1`. `45E8` hashes the **source before memcpy** at `0x3E55314`: buffer `[obj+0x130]`, compared to `[obj+0x10]`. Memcpy at `0x3E5547E` is later.

Thunks: memcpy RVA `0x4FB381E`, memmove `0x4FB3824` (`jmp [iat]` → VCRUNTIME140).

Do **not** Relic IAT-patch (pack `0x20DE00AD` / `0x56FD3C0`). Do **not** `PAGE_GUARD` Relic `.text`.

Overlay tried 14-byte abs-jmp on `vcruntime140!memmove`/`memcpy` and `ucrtbase!memmove`, copy via **ntdll `RtlMoveMemory` `GetProcAddress`** (winnt `RtlMoveMemory` is a `memmove` macro → recursion). Log: `[RA] integrity cloak ON hooks=3`. **Did not stop the ~16s hang** — hasher reads live `.text`.

**Reconfirm (IDA `a1220dbc`):** same. `xor r8, [rcx]` in hasher; 45E8 hashes `[rdi+130h]` **before** `call memcpy` @ `0x3E5547E`. Second hash `0x3E555F3` is dest (`[obj+0xA0]+[obj+0x20]` vs `[obj+0x18]`). Cloak insufficient **and** unsafe (`0x10E`). New: Walker clones `0x3E48680` / `0x3E49CF0` (Dispatcher calls latter @ `0x3E44E8A`, `0x3E451D5`).

Next (not done): HW-BP/VEH on `0x3E57050` / `0x3E56678`, temporarily restore `saved[]`, re-apply stubs. Do not 14-byte hook the `7050` prologue (hashed). Do **not** re-enable IntegrityCloak.

## JUMPOUT hang (~16s)

RVA **`0x3F57539`**. Fail at `0x3F575B1` (`xor rax/rsi; mov rsp,rax; mov rbp,rsi; jmp rax`). RIP after JUMPOUT looks like CF04+2 junk. No `[CRASH]` VEH. `Responding=False`. x64dbg HTTP attach: `slots=0`, RIP in that junk.

`-nodbg` **data** byte RVA is **`0x844B2ED`** (`dev_bypass.cpp`). Old docs/DLL said `0x544B2ED` — wrong.

## Cycle that keeps slots=0

**Superseded 2026-09-06 late:** hide + watcher stubs are default — dbg **may be
open before inject**. See [2026-09-06-window-hide-default.md](2026-09-06-window-hide-default.md).

Historical (pre-default hide):

1. Close **x64dbg and WindowWatch**
2. Steam launch (`-dev -nodbg`)
3. Inject `Release|x64` (`DllInjector.exe` default = profiler + RA neutralize)
4. Wait `[RA] neutralize ON` in `%TEMP%\aoe4_internal.log`
5. **Then** open WindowWatch / x64dbg

Injector High vs Relic Medium: SDDL `D:(A;;GA;;;AU)S:(ML;;NW;;;ME)`. Do not `--ra-veh` with VS. Do not VS + x64dbg + INT3 VEH together.

Proc-scan A/B / term thunk: skip on packed/mismatch; do not abort the whole neutralize (that produced `slots=3` once).

## Hide x64dbg title only is weak

`GuiUpdateWindowTitle` **appends**. Title rename / `00_retitle.lua` (CE) / rename `x64dbg.exe` does not cover class, `x64dbg.exe` proc-scan, or hasher hang. Relic first title gate is XOR `PID:` **and** `Thread:` **and** (`Module:` / `Main Thread`) via hashed `GetWindowTextW` `0x3F0A910`, not the IAT python sites. ScyllaHide in Relic (`NtUserBuildHwndList` / `FindWindowEx` / `IsWindowBad`) matches title **and** class; bad-name list includes `x64dbg`, `[CPU`, `ida`, `Cheat Engine`. Qt class `Qt5QWindowIcon` is not on that class list. Hide research: [2026-09-06-x64dbg-windowwatcher-hide.md](2026-09-06-x64dbg-windowwatcher-hide.md).
