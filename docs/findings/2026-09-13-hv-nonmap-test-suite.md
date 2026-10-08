# Non-map test suite (2026-09-13 ~16:10)

**Do not map.** Product cycle (HV → hold → Relic → x64dbg) is blocked on
purpose: Event 41 **15:54:27**, cookie `in_progress` from boot **15:43:47**,
`last_fix_time=null`, `launch_authorized=false`. Ping `ud` is not a green
light.

Offline suite was run this turn. No `kdu -map`, no `Map-AfterZppu`, no
Steam Relic, no x64dbg attach.

## Results

| Check | Result |
|---|---|
| `tests/Verify-AmdPort.ps1` (debug) | **PASS** (exit 0). Includes NDK `clang++ -fsyntax-only` `tests/amd_layout.cpp`, RFC 8439 AEAD, insn-boundary, ELF no Intel VMX, VMRUN sequence, loader prefix no VMMCALL. Artifacts `out/debug/x86_64/zpp_hypervisor` 1024576 B **15:51:31**, `zpp_loader.sys` 1074688 B **15:51:32**. Script: «Offline checks only; no driver was loaded and no VMRUN was executed.» |
| `Test-VmrunDumpGate` dry-run | **exit 21** (expected). `ok=False`. Reason: `map-attempt cookie status=in_progress attempt_boot=2026-09-13T15:43:47 now_boot=2026-09-13T15:54:23`. Cookie returns before filling `last_event41`. Live Event 41 still **15:54:27** (also 15:43:51, 15:41:06). Event 6008 unexpected shutdown **15:54:34**. Minidump empty. |
| `python tools/zpp_ctl.py ping` | **ud**, process exit **2**. Text: `ud  (no ZPP*: old HV, no SVME, or VMMCALL not intercepted)`. SVM not resident. |
| Live `CrashDumpEnabled` | **0**. `AutoReboot=1`, `AlwaysKeepMemoryDump=0`, `LogEvent=1`. HostPrep source writes **0** (`docs/HostPrep-AtBoot.ps1` line 36). `last-hostprep.log` **15:54:50** still old string (`PasswordLess=0 AutoAdminLogon…` without CrashDump) — that boot’s HostPrep log line does not prove the new format ran. Live 0 is this session, not a next-reboot proof. |

`docs/last-zpp-start.log` at 16:10: len=608, nonzero=608, mtime **15:53:33** (not all-NUL this check). Gate still 21 from cookie.

`docs/cycle-state.json`: `status=new_bsod`, `launch_authorized=false`, `last_fix_time=null`. Not changed this pass.

## What this is not

These passing offline asserts are **not** a VMRUN / 32-CPU / Relic hold test.
That path stays blocked until Event 41 is analyzed, `last_fix_time` is set
to a real sys/ELF fix newer than 15:54:27, and the user says **запускай**.
