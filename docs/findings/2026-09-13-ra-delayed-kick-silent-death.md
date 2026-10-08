# 2026-09-13 — 13:03:11 silent death is the RA delayed kick, not a crash

Session: Relic started **12:37:42**, overlay injected **12:58:59** (DLL built
12:57:41, the post-`before_dx12_fix` build). **Online 4-player** match
(`scen`/`dry_arabia`, seed 968977131, peers + `LoadArbitrator` + PlayFab Party +
`BattleServerRelay`), mission start **12:59:55**. Process gone at
**13:03:11.29**.

This is **not** the 12:27:54 class in
crash_20260913_investigation/REPORT_RU.md.
That one was a real GPU hang. This one is an external `TerminateProcess`.

## The process was killed — it neither crashed nor exited

Every artifact that a crash or a chosen exit would leave is absent, and the
absences are individually checked rather than assumed:

| Artifact | 12:27:54 (GPU class) | 13:03:11 (this one) |
|---|---|---|
| `[PRESENT] hr 0x887A0005 DEVICE_REMOVED` | yes | **no** |
| overlay VEH `[CRASH]` / `[SEH]` line | yes (`0xC0000005` rva `0x3AD6A86`) | **no** |
| `[SCAR] [SEH] ScarDoString code=` | — | **no** |
| Relic `warnings.log` `Failed to Present` / `FATAL EXIT` | yes | **no** |
| Relic BugSplat minidump + `.xml` | yes (`release_16_3_0_rtm_x64D0EH5M94.dmp`, `BVT10DJ2.xml`) | **no** |
| Relic `rrdebugdred.*` (DRED) | yes | **no** |
| `nvlddmkm` id 153 | 2× at 12:27:54/56 | **no** |
| kernel `LiveKernelReports` / `Minidump` | WATCHDOG 141 | **no** (nothing on disk 13:02–13:06) |
| WER `Application Error` | — | **no** |

`warnings.log` ends 13:03:08.003 on a routine framerate line. It contains **no
`Requesting game quit with reason:`, no `Unloading step:`, no `Application
closed without errors`** — the exact discriminator established in
[2026-09-08-heap-av-crash-class.md](2026-09-08-heap-av-crash-class.md#capturing-the-games-own-account-of-a-death).
By that rule the process was killed.

The overlay log tail is **complete, not truncated**: the last SCAR cycle closed
normally, including the paired post-call clear that follows every other command.

```
13:03:11.250  MpBypass: data clear …
13:03:11.291  [SCAR] cmd#417 label=ai_lock_skip_map quiet=1 ok=1 len=1365 hash=0xA25BC867 ok
13:03:11.291  MpBypass: data clear …
<end of file>
```

So no exception was ever raised, on any thread — VEH is armed and provably
works (it logged the 12:27 AV), and `ScarDoStringSeh` wraps every DoString.
`WriteFile` without `FlushFileBuffers` still reaches the OS cache, so a kill
cannot eat the tail. Nothing was lost; nothing was there.

Also ruled out: **no hypervisor**. Boot is 11:29:04, `Aoe4Hv` service
`Stopped`, `HypervisorPresent=False`, no `zpp_loader.sys`, no x64dbg. The
`aoe4-hv` work in [hv-hold-before-dbg](2026-09-13-hv-hold-before-dbg.md) is the
**previous** boot (21:25:38) and is not in this picture.

## What armed the kill: RA took a slot 1 s after match start

```
12:59:56.702 [RA] ---- edge classify=OP20 leftover tag=40230001 a2=0 (Relic canned, not DoString) tick=5460734 ----
12:59:56.717 [RA] window slots=1 accum=0 flag=0 begin=0000021732E730D0 end=0000021732E73268 clears=0
12:59:56.720 [RA] slot[0] tag=40230001 kind=3 (op20/26/34/35 5s/15s class — not 180s)
12:59:56.720 [RA] slot[0] rva +10=0x56F9C88 +18=0x0
12:59:56.721 [RA] WindowClear POST slots=1 accum=0 flag=0 n=1  <<< RA suppressed
12:59:58.715 [RA] WindowClear POST slots=1 accum=0 flag=0 n=2  <<< RA suppressed
12:59:58.968 [RA] window slots=0 … clears=2
```

**Slot appears 12:59:56.70 → death 13:03:11.29 = 3 min 14.6 s.** That is the
documented window: *"Any slot at any time: kill Relic immediately. KickCtor is
already armed; the 2–3 min death is delayed, not optional"*
([hv-hold-before-dbg](2026-09-13-hv-hold-before-dbg.md#tonight-before-this-ritual)).

Same signature as the dump corpus entry for PID 37560 — online match,
`slots=1`, tag `40230001`, `+10=0x56F9C88`, and that process died too
(`.cursor/rules/aoe4-dumps.mdc`).

`WindowClear` cannot have helped, and the code says so itself
(`mp_bypass.cpp` ~1054):

```cpp
// Befriend RA: never empty packed fail slots here. WindowClear does not
// cancel already-armed kick timers and looks like tamper after a fail pack.
```

and ~1030: *"WindowClear zeros end/accum/flag. Does not prevent Relic enqueue
(opcode 20 / mapped-name clone 0x3F03D80); waiting 2500 ms does not either."*
[ra-kick-emu](2026-09-06-ra-kick-emu.md) tabulates the same thing: WindowClear
is **`.data` only**; only `--drain-timerq` touches the C8E4 deadlines, and the
overlay is explicitly told not to auto-drain from WindowClear.

The overlay was also running with every RA countermeasure off —
`[RA] xbox enforcement cloak=off hasher=off text=0`, `hasher=off`,
`INTEGRITYCHECK: string only — no opcode hook` — while MapHack `ON`
(FOWCTRL1+8, 13:00:25), AI BOT armed, and ~3 `ScarDoString`/s
(`cmd#417` in 195 s) in an **online** match.

## Conclusion

The kill was Relic anti-cheat's delayed kick, armed at match start and fired
~3¼ min later. Not a GPU fault, not a heap AV, not an overlay exception. The
overlay's contribution is that it **watched the slot appear, zeroed the window,
logged `RA suppressed`, and let the session run for three more minutes.**

Not proven: which thread/API issued the terminate. Naming it needs an
`NtTerminateProcess` hook, still declined for detection cost
([2026-09-08](2026-09-08-heap-av-crash-class.md), 01:58 class). The 3¼-min
correlation plus the artifact table is the case; it is not a captured caller.

## Wrong label fixed

`[RA] WindowClear POST … <<< RA suppressed` claimed something the same file
denies twenty lines earlier. Nothing was suppressed — the `.data` window was
zeroed while the armed timer survived. That string is why a doomed session was
allowed to continue. Retagged to name the residual risk instead.

## Diagnostic regressions found while chasing this

Both were set up by [2026-09-08](2026-09-08-heap-av-crash-class.md#actions-taken)
and are gone:

1. **`E:\aoe4_dumps` does not exist.** Drive `E:` is not present at all
   (`C` `D` `K` only). The death watcher that copies `warnings.log` +
   overlay log + `session_data.txt` on process disappearance had nowhere to
   write, so this death produced no capture — the one artifact that would have
   frozen `warnings.log` before the next launch rotates it.
2. **`HKLM\…\Windows Error Reporting\LocalDumps\RelicCardinal.exe` is absent.**
   Re-arming it is cheap but would not have helped here: a `TerminateProcess`
   raises no exception, so WER has nothing to capture. Worth restoring only for
   the AV classes.

Two further holes, neither the cause here, both already costing evidence:

3. **VEH drops the `[CRASH]` disk write whenever `g_scarInCall != 0`**
   (`log.cpp` 815–819, ring only). `g_scarInCall` is **process-global**, set
   across the whole of `ScarDoStringRaw` including its logging tail
   (`LogScarCommand` runs *before* `LogNoteScarEnd`). With a DoString in flight
   ~3×/s, a fault on Present or a collect worker loses its record to a flag
   about a different thread.
4. **`mp_bypass.cpp` and `mp_bypass.h` were UTF-16LE with no BOM** — the only
   two such files in `InternalInjector`. ripgrep classified them as binary and
   skipped them, so the whole RA window/kick layer was invisible to `rg`/Grep:
   `MpBypassWindowClear` looked like it had no definition anywhere in the tree
   (it is `mp_bypass.cpp:1213`). Any search-driven audit of RA silently missed
   96 KB. MSVC compiles UTF-16 without a BOM, so this never blocked a build —
   it only blinded tooling.

   **Converted to UTF-8 with BOM** (backup: `dumps/crash_20260913_investigation/before_utf8_fix/`).
   Behaviour-neutral, and verified as such rather than assumed:

   | Check | Result |
   |---|---|
   | Decoded text before vs after | identical (`-ceq`) |
   | `—` U+2014 count | 6 in `.cpp`, 5 in `.h`, unchanged |
   | `mp_bypass.obj` | 13:29:01, newer than source 13:28:40 → really recompiled |
   | `InternalInjector.dll` size | 13 876 736, unchanged |
   | `"OP20 leftover drain — WindowClear"` in the DLL | `… 64 72 61 69 6E 20 **E2 80 94** 20 57 69 …` — byte-identical em-dash |

   The project already passes `/utf-8`, so narrow literals were UTF-8 in the
   execution charset before and after; the DLL byte check above is the proof.

   This did **not** fix clangd. It still emits the same 22 diagnostics, partly
   a stale cached preamble and partly because `AOE4HOOK/internal` has **no
   `compile_commands.json`** (only `aoe4-hv/` has them), so clangd never had
   correct flags for the overlay — hence noise like `no member named 'size' in
   std::vector<Hit>`. Encoding was necessary, not sufficient.

## Second reproduction the same day — the 2–3 min window is not a coincidence

The 12:03 session (PID 3280, overlay boot 12:05:39, log kept as
`dumps/crash_20260913_investigation/aoe4_internal.prev.log`) is the same thing
one match earlier:

| | 12:03 session | crash session |
|---|---|---|
| match start | 12:09:46 | 12:59:55 |
| RA slot appears | **12:09:47.04** | **12:59:56.70** |
| tag / kind | `40230001` / `kind=3` | `40230001` / `kind=3` |
| classify | `OP20 leftover … Relic canned, not DoString` | same |
| `WindowClear` | 2×, `RA suppressed`, slots→0 | 2×, `RA suppressed`, slots→0 |
| last log line | 12:12:01.896, mid-stream, no `[CRASH]` | 13:03:11.291, mid-stream, no `[CRASH]` |
| **slot → death** | **2 min 14.9 s** | **3 min 14.6 s** |

So RA enqueues **~1 s after match start** and the process dies inside the
documented 2–3 min window, twice, from two different PIDs. The one session today
that never reached a match (12:23–12:27) has **zero** `[RA] window` lines and
died of the GPU hang instead. Two for two: slot → silent death.

## Commit archaeology — recent work did not cause the kick, with one exception

Asked which of the last four days' commits could be responsible. Checked with
`git log` restricted to the RA layer:

```
git log --since=2026-09-09 -- internal/InternalInjector/{mp_bypass.cpp,ra_hide.cpp,
    xbox_enforcement.cpp,http_intercept.cpp,maphack_fowctrl.cpp}
```

**Empty.** The RA layer has not been touched since `e66ae97050` / `2bfac2753d`
on 09-07. Everything in the 09-09…09-13 window is AI, menu/i18n and DX12 work.
The kick is therefore **not a regression from recent commits** — and
`slotSkip=0` / `hasher=off` / `cloak=off` is the standing state recorded by
`3d6f01709a` *"docs(mp): record sandbox wins with neutralize off"* (09-06),
after `830c5ad194` restored the `.text` neutralize and it lost. Turning it back
on is the plant territory [ra-kick-emu](2026-09-06-ra-kick-emu.md) refuses.

Two recent commits were in the DLL that died (built 12:57:41, so up to the
`e05a46e220` merge at 12:56) and both are innocent of the kill:

- `b703df3226` 12:32 `feat(ai): add workers-only lock mode` — the mode was live
  (`lock=workers_only ecoLock=1` in the log), 25 min old. AI scoring only.
- `3fa2c1a378` 12:47 `fix(overlay): latch DXGI device-removed` — held; the
  device-removed class did not recur.
- `4cca5eaeeb` 13:16 `fix(ai): park House without PopCap in workers_only`
  landed **after** the death, so the dead session did spam house foundations.
  Cosmetic against a kill.

### The one real regression: `5638b2eaed` muted the crash log

`5638b2eaed` (09-13 **11:59**, one hour before the session, in the dead DLL)
introduced the VEH gate that hole 3 above describes:

```cpp
-    const HANDLE file = OpenCrashLogAppend();
+    const bool scarInCall = InterlockedCompareExchange(&g_scarInCall, 0, 0) != 0;
+    const HANDLE file = scarInCall ? INVALID_HANDLE_VALUE : OpenCrashLogAppend();
```

The intent is sound and stated: Relic hooks `CreateFileW`, so opening the crash
log from VEH while the **window thread** sits inside `Game_ScarDoString`
re-enters that hook and can hang it. The defect is that `g_scarInCall` is
**process-global**, so the gate fires for *every* thread, and the same commit
put `NativeOverridesDisarmLevelOnCrash` + `SessionRejoinOnCrash` behind it too.
With DoStrings at ~2/s and the flag held across the whole of `ScarDoStringRaw`
(`LogScarCommand` runs before `LogNoteScarEnd`), any AV on Present or on the
collect worker lost its `[CRASH]` line to a flag about a different thread.
Before 11:59 the VEH always wrote.

**Fixed** by making the gate thread-affine against `g_scarTid`, which
`LogNoteScarBegin` already records as the thread inside the call:

```cpp
const DWORD scarTid = static_cast<DWORD>(InterlockedCompareExchange(&g_scarTid, 0, 0));
const bool scarInCall = InterlockedCompareExchange(&g_scarInCall, 0, 0) != 0
    && scarTid == GetCurrentThreadId();
```

Same protection for the window thread, crash logging restored everywhere else.
`Release|x64` rebuilt (`log.obj` 13:38:05 > source 13:37:37, DLL relinked
13:38:09); adversarial host suite green (103 + 9, `[OK]`). This did **not**
affect the 13:03 death — no exception was raised at all — it only means the
next AV is recorded again.

## Every log on the box, and what each one actually gave

Checked exhaustively rather than by memory. Three sources nobody had looked at
turned out to matter.

| Source | 13:03 death |
|---|---|
| `AOE4HSettings\Logs\aoe4_internal.log` | complete tail to 13:03:11.291, no `[CRASH]` |
| `My Games\…\warnings.log` | ends 13:03:08, no quit / unload / FATAL |
| `…\LogFiles\unhandled.*` | nothing appended after 12:59 |
| Relic BugSplat `.dmp` + `.xml` | **absent** (both present for 12:27) |
| `…\LogFiles\rrdebugdred.*` (DRED) | absent |
| WER `Application Error` / `ReportQueue` | absent; `LocalDumps\RelicCardinal.exe` not armed |
| `C:\Windows\Minidump`, `LiveKernelReports` | nothing 13:02–13:06 |
| System log `nvlddmkm` | nothing (2 events at 12:27) |
| **Steam `logs\gameprocess_log.txt`** | **`13:03:14 no longer tracking PID 5840, exit code 0`** ← new |
| **`AOE4HSettings\Matches\rejoin_session.json`** | written 13:03:10, **`"crash": false`** ← new |
| **`AOE4HSettings\Matches\aoe4_match_5840_…ndjson`** | 408 KB, to 13:03:10 ← new |
| `%TEMP%\aoe4_bridge_live.txt` | 13:03:11, `tick=5655265 n=324 vm=1 tcs=4 verdict=PASS` ← new |
| `%TEMP%\aoe4_world_*.txt` | 60 s snapshots, last 13:02:56 |
| `%TEMP%\aoe4_scar_cmds.log` | stops 13:00:28 — `silentOk` skips the body dump |
| `Logs\ra_window.log` | stale (01:46), held open by `WindowWatch` 47444 |

Two of the new ones settle the reading:

- **`exit code 0`.** An unhandled fault surfaces its exception code here
  (`0xC0000005`, `0xC0000409`). A zero can only come from `ExitProcess(0)` or
  `TerminateProcess(h, 0)` — a deliberate stop. That rules a fault out on its
  own. (12:27 was also 0, because Relic's fatal handler exits 0 after BugSplat —
  but 12:27 *has* the BugSplat, and 13:03 has none.)
- **`rejoin_session.json` with `crash:false` at 13:03:10**, one second before
  the end, and no crash snapshot ever written. `SessionRejoinOnCrash` never ran.

## Capture built for the next occurrence

`tools/watch_relic_death.ps1` (elevated). Runs outside the game entirely: no
injection, no hooks, no VM reads. The only handle it takes is
`OpenProcess(QUERY_LIMITED_INFORMATION|SYNCHRONIZE)` = `0x101000`, the same
right `gamingservices.exe` already holds — deliberately not `VM_READ`, which is
what `Get-Process` and WMI take, and never `TERMINATE`.

It holds that handle across the death so `GetExitCodeProcess` still answers,
then snapshots every row of the table above into
`K:\aoe4_dlc\dumps\deaths\<stamp>_pid<pid>\` with a `REPORT.md` that runs the
kill/exit discriminators automatically. (`E:\aoe4_dumps` from the 09-08 note is
gone — drive `E:` does not exist on this box; `K:` has 267 GB.)

**Naming the killer.** ETW `Microsoft-Windows-Kernel-Audit-API-Calls`
`{e02a841c-…}` **event id 5 is `NtOpenProcess`**: payload
`[targetPid, desiredAccess, status]`, and the *caller* pid/tid are in the record
header. Filtering `target == relic pid` and `desiredAccess & 0x0001`
(`PROCESS_TERMINATE`) names any external process that acquired the right to kill
it. `Microsoft-Windows-Kernel-Process` is captured alongside for the
`ProcessStop` record (start/stop time, exit status, image name).

Verified end to end, not assumed — `tools/etw_terminate_probe.ps1` plus a full
watcher self-test against Notepad killed by `taskkill`:

```
*** 13:58:39.547 openBy=49028 (<gone>) tid=45700 access=0x401 [TERMINATE]
13:58:39.600 id=2 payload=[24956,…,Notepad.exe]      <- Kernel-Process stop
verdict: KILLED BY ANOTHER PROCESS
```
`49028` was the `taskkill` PID. 429 620 ETW records scanned in that run.

**The absence is also an answer, and this is the load-bearing part.** A process
terminating *itself* uses the `-1` pseudo-handle and never calls
`NtOpenProcess`. So "no external `TERMINATE` opener" is not a hole in the
capture — it means the stop came from inside `RelicCardinal`, i.e. in-process
enforcement. The report states which of the two happened instead of leaving it
open. That is the question the 09-08 note left to an `NtTerminateProcess` hook,
answered without one and without touching the game.

Two defects were found by testing the tool rather than by reading it:
`0xFFFFFFFF` for `INFINITE` parses as Int32 `-1` in PowerShell and throws on the
`UInt32` marshal; and `@(Get-WinEvent -Path …)` over a 61 MB ETL killed the host
process before `REPORT.md` was written — the decode is now streamed under an
XPath id filter.

**Known limit, stated rather than hidden.** The audit stream runs ~15 MB/min on
this box, so the default 128 MB circular buffer holds about the **last 8
minutes**. That always covers the terminate itself and a handle opened shortly
before it — the `taskkill` shape — but a killer that opens a handle at match
start and sits on it for 20 minutes would have its `NtOpenProcess` scroll off
the front, leaving only the terminate. Raise `-EtlMaxMb` for that case; decode
cost grows roughly linearly (64 MB was ~430 k records, a few minutes).

Running now against the live PID 46296 (`K:\aoe4_dlc\dumps\deaths\watch.log`).

Still not done: WER `LocalDumps` re-arming (useless for a terminate, worth it
for the AV classes) and Security audit 4689.

## Do not conclude

- Do not read this as "the DX12 fix failed". The device-removed class did not
  recur in 24 min of this session; this death has no GPU artifact at all.
- Do not blame `readFaults=21155` at 13:03:07.999 (vs ~1–2 k baseline, 49.65 ms
  vs ~6 ms). It is 3.3 s before death and those reads are `__try`-guarded by
  design; treat it as unexplained, not causal.
- Do not treat `kind=3` / "Relic canned, not DoString" as benign. It was
  classified benign and the process still died on schedule.

## Third copy — 23:04 leftover → 23:08:14 (pid 8060)

Same KickCtor class, hold5 image (`luaGate2500+hold5+wasStrip`). Slot at
**23:04:39.188** (`40230001` / kind=3) after overlay world-feed cmd#3, not
during the 2500 ms settle (`lua-settle` was slots=0). Last overlay line
**23:08:14.411** (`ai_lock_army_relock sid=50100`), no `[CRASH]` / WER /
BugSplat. Slot → death **~3 min 35 s**. Writer still Relic `sub_3DDB29C`;
bypass is skip that world-feed until DualFlag, not a longer hold.

## Negative — 23:28 wfAfterDf, no slot, no KickCtor (pid 27332)

Stamp `luaGate2500+hold5+wasStrip+wfAfterDf`. Starting mission **23:28:14**.
DualFlag **23:28:19** `slots=0 flag=0` before any `mode=full`. First world-feed
**23:29:20** simTick=528. Overlay still writing at **23:33:08**; Relic alive.
No `40230001`. The 2–3 min death tracks the slot, not match age.
