# Cycle 9 reset: leftover-first, query user DTB, hitch on ping (2026-09-13)

Mailbox ops **1–12** unchanged (no op 13). Event **41** `22:07:45` was the
**previous** crash image `17E25811`. Idle map of **`29075A35`** is **live**
(`load_ok` 22:48:17, ping **pong** 22:52:20). Do **not** nested-map. Do
**not** remap `17E25811`. If this boot dies, crash image is `29075A35`.

HV-only prove: Enqueue + KickCtor + hasher. TimerQ skip. Overlay other boot.
Ritual: `aoe4-hv/docs/Cycle9-HvOnly.ps1`.
Build (no kdu): `aoe4-hv/docs/Build-Cycle9-Elevated.ps1`.

## Why 8h died (not dual-nCR3 theory)

1. Mailbox op 8 **name-first** → leftover `--cr3` while Relic **3832** lived
   disarmed the hold (22:03:52 sites 2→0), then rearm + Overlay RUN → 41.
2. Query returned **kernel** DTB (`svm_bringup` `cands[0]` =
   DirectoryTableBase). Arm `owner_cr3` is user DTB. Leftover after death =
   status=8 `not_found`, not restore.
3. Hitch snapshot only in DriverEntry. No NPF/HashRec after hold.

## Code (this turn)

| Change | Where |
|---|---|
| leftover CR3 first; live name only if no leftover CR3 | `mailbox.cpp` op 8 |
| dispatch tests | `stealth_reap.h` `stealth_clear_dispatch` |
| query user DTB (`UserDirectoryTableBase` first on no-probe path) | `hypervisor.cpp` `select_user_cr3` |
| `hashrec_hits++`; ping `data[]` `hitch inner= npf= hashrec= sites=` | `npt_stealth.cpp` + mailbox ping |
| usermode leftover refuse while Relic lives; print `owner_cr3=` | `zpp_aoe4.cpp` |
| hold prints owner + hitch | `zpp_at.py` |
| corpse `17E25811…` | `Map-AfterZppu.ps1` |
| 8h clear/rearm/inject retired (exit 7) | `Cycle8h-ClearLeftoverCr3` / `Rearm` / `Inject*` / `Evidence2` |

## Do not

- remap `17E25811` / `7B5C8989` / `AB7D293D` / `02F9B040` / `A1EA2CF1` /
  `D78C5065` / `8C9D7CDD` / `5351E024`
- `kdu` without **запускай** and `last_fix_time` newer than `22:07:45`
- Overlay / `--patch-game` / leftover `--clear` while Relic lives
- arm TimerQ `0x3E672DC`
- treat status=8 as NX restored
- `UpdateGoal complete` until live HV-only Done-when

SHA of the new sys/ELF is in `aoe4-hv/docs/_bsod/cycle9-build.json` after
`Build-Cycle9-Elevated.ps1`.

## Build (2026-09-13 22:43, no kdu)

| Artifact | SHA256 prefix | mtime | bytes |
|---|---|---|---|
| `zpp_loader.sys` | `29075A35` | 22:43:10 | 1098240 |
| ELF | `B18B9036` | 22:43:09 | 1048120 |
| `zpp_aoe4.exe` | `0B4A08BF` | 22:43:12 | 198144 |

`Verify-AmdPort` exit 0 (insn_boundary leftover dispatch PASS). Gate **20**.
ping **ud**. Relic **none**. Preflight `docs/_bsod/cycle9-preflight.txt`
22:44:53: sys `29075A35` not corpse. Next map = user **запускай** + idle
`Map-AfterZppu` (Relic 0). This turn did **not** kdu.

## Idle map (2026-09-13 22:48)

Elevated `Cycle9-MapIdle.ps1` / `Map-AfterZppu` (Relic 0). Wrapper
`cycle9-map.txt` stdout was empty; truth is `docs/last-zpp-start.log`.

| | |
|---|---|
| kdu start | 22:48:16 ping **ud** Relic none hitch spawn |
| mapper exit | 1 (kdu; not nested `svme_already`) |
| `load_ok` | 22:48:17 `elfst=46` exit=`7c` |
| hitch sample | **inner=0 npf=0** oth=0 full=6797 |
| hitch-host | 22:48:17–22:51:19 `stage=vmcall_skip`; Event 41 lines at end are **historical** 22:07 / 21:06 / 20:49 |
| ping | **pong** 22:52:20 Relic none |
| CIM `HypervisorPresent` | False (Hyper-V flag; SVM is ping pong) |
| cookie | `in_progress` left by Map-AfterZppu → set `load_ok_pending_alive` |
| next | `Cycle9-HvOnly.ps1 -Phase hold` (no overlay, TimerQ skip) |

Do **not** nested-map. If new Event **41**, do **not** remap `29075A35`.

## Hold 9752 failed (2026-09-13 23:02)

Target is **RelicCardinal `.text` NPT**, not Steam/ntdll/user32/RuntimeBroker.

| | |
|---|---|
| first hold | Steam `-applaunch` swallowed (cold Steam); timeout 300s; then `query` without Relic |
| query | hello retry=3 `cr3=64ccbd000` then `status=8`; next `mbox-ping` **no-reply rax=2** (`bad_buffer`) |
| Relic 9752 | started 23:00:08 `0x7FF6AA700000`; unpacked gold Enqueue/KickCtor; 45s settle |
| apply | stealth `--file` hello **no-reply rax=2** ×6 — NPT **never** armed |
| prove | slots=0 23:02:17/28 then **slots=1** 23:02:39 → KILL |
| Relic 30144 | Steam relaunch 23:02:27 same image; slots=0 23:06:27 |

Mailbox: CPUID ping **pong**, ZPPX hello flaky (`bad_buffer`, HV did not write). Do **not** nested-map. Do **not** Patch Game / user32 / Steam HKCU overlay / RuntimeBroker hide.

Ritual now: NPT Enqueue `0x3DD2550` + KickCtor `0x3E691F4` + hasher `0x3E57050` on live Relic. Skip 45s settle if process age ≥45s. Steam overlay registry **removed** from `Cycle9-HvOnly.ps1`.

## Relic 30144 NPT (2026-09-13 23:08)

Same image `0x7FF6AA700000`. Skip settle `process_age=390s`. Hello **ok**. Query
**status=0** `owner_cr3=0x39842000`. Relic `.text` arm (not OS):

| RVA | VA | eax | status |
|---|---|---|---|
| Enqueue `0x3DD2550` | `0x7FF6AE4D2550` | 0 | **0** sites=1 |
| KickCtor `0x3E691F4` | `0x7FF6AE5691F4` | 0 | **8** `not_found` (printed `sites=0` was **eax aux**, not ELF count) |
| hasher `0x3E57050` | not reached | | |

All three RVAs sit in one **2 MiB** VA `0x7FF6AE400000`. Resolve probed KickCtor
VA to pick EPROCESS after Enqueue 4K NX → not_found. Fix (not mapped yet):
name+PEB for arm; pass query `owner_cr3`; do not `read_guest_virtual` the
sibling site at resolve. REFUSE partial `--file`. Relic killed. ping **pong**.
Do not nested-map. Reap leftover `0x39842000`.

## Reap 23:16 (false sites=0)

`-Phase reap` ping **pong**, Relic none. `mbox-ping` and `status` both
**no-reply rax=2**. Missing `sites=` was treated as **0** → skipped `--clear`.
That is **not** identity restore. Enqueue leftover on `0x39842000` unknown.

Retry 23:17: hello ok, hitch **npf=1** `sites=0`, leftover `--clear --cr3 0x39842000`
**status=8** `not_found` (CR3 missed `owner_cr3`). Not proven restore; same
class as 8h leftover after death.

## User запускай? (2026-09-13 23:19)

**No.** ping **pong** this boot. Nested-map forbidden. KickCtor name+PEB
arm is source-only until a **new** sys after reboot. Do not `kdu` `29075A35`
while pong. Do not remap `17E25811`.

## KickCtor ELF built (2026-09-13 23:19, no kdu)

`Build-Cycle9-Elevated.ps1` (gate 21 cookie, ping **pong**, Relic none).
`build_windows.bat` 0, `build_zpp_aoe4.bat` 0, `Verify-AmdPort` 0.

| Artifact | SHA256 prefix | mtime | bytes |
|---|---|---|---|
| `zpp_loader.sys` | `A67B068F` | 23:19:47 | 1098240 |
| ELF | `3EA5B78C` | 23:19:46 | 1048256 (+136 vs `B18B9036`) |
| `zpp_aoe4.exe` | `504A55B3` | 23:19:49 | 198144 |

Not corpse `17E25811`. Not the mapped image `29075A35`. Arm/protect
`mailbox_resolve_target` skips site-VA EPROCESS probe (30144 KickCtor
status=8). Usermode passes query `owner_cr3`. Cookie set `idle_alive_ok`
so a **planned** reboot is not `load_ok_pending_alive` + newer boot
(false map-death). `last_fix_time=23:19:47` `launch_authorized=true`.
Do **not** nested-map this boot. After reboot ping **ud** Relic **0** →
`Cycle9-MapIdle` without asking запускай. If **new** Event 41, crash
image is `29075A35` (do not remap it). Overlay off. TimerQ still skip
(original Done-when not passed). `cycle9-next.json`.

## Reboot 1 no-op (2026-09-13 23:32)

`shutdown.exe /r /t 20` pid **16168** at 23:31. At 23:32:38 still
`LastBootUpTime=22:07:40` uptime **85** min. `shutdown /a` = **1116**
(no shutdown in progress). ping **pong** Relic none Event **41** still
`22:07:45`. Cookie `idle_alive_ok`. Nested-map still forbidden. Retry:
`Cycle9-RebootNow.ps1` (`Restart-Computer -Force`).

## Clean reboot + map A67B068F (2026-09-13 23:38)

`Restart-Computer -Force` at 23:33:32. Event **1074** 23:33:33 (not 41).
`LastBootUpTime=23:34:47`. HostPrep Capture `crash-20260913-233514`
ping_err (SYSTEM PATH). User ping **ud** Relic none gate **0**. sys
**`A67B068F`**. `Cycle9-MapIdle` 23:38:04 mapper exit 1, **`[OK] load_ok`**
23:38:05 hitch **inner=0 npf=0**. ping **pong** 23:38:49. Cookie
`load_ok_pending_alive`. Do **not** nested-map. If new Event **41**, do
**not** remap `A67B068F`. Overlay off. Hold started `Cycle9-HvOnly -Phase hold`.

## Hold Relic 21296 KickCtor status=0 (2026-09-13 23:40)

KickCtor name+PEB ELF **worked**. Relic **21296** `0x7FF760A50000`
owner_cr3 **`0x78AA76000`**. Overlay / RuntimeBroker / Patch Game **off**.

| RVA | VA | eax | status | sites |
|---|---|---|---|---|
| Enqueue `0x3DD2550` | `0x7FF764822550` | 0 | **0** | 1 |
| KickCtor `0x3E691F4` | `0x7FF7648B91F4` | 0 | **0** | 2 |
| hasher `0x3E57050` | `0x7FF7648A7050` | `0xFFFFFFFE` | **0** | 3 |

Hasher identity RPM `48 89 5c 24 20 57…` (not dirty). protect `0x3E57000`
status=0. hitch after apply **inner=0 npf=3 hashrec=3 sites=3**. query
**status=0**. slots=0 23:40:14–23:41:05 (≥50s logged; prove 60s). TimerQ
**still skip** (original Done-when not passed). Do not leftover `--cr3`
while Relic lives. Nested-map forbidden. If new Event **41**, crash image
`A67B068F`. rbhost `_src\x64dbg.exe` attach started 23:42 (not
`Start-X64dbgHidden` / RuntimeBroker).

## rbhost launch (2026-09-13 23:43)

`Cycle9-HvOnly -Phase attach` launched
`C:\Program Files (x86)\rbhost\release\_src\x64dbg.exe` (no RuntimeBroker).
slots=0 23:43:08–23:43:59 while Relic **21296** lived. **No x64dbg process
remained** after the prove (CIM empty) — DualFlag/hidden dbg ≥60s with a
**live** debugger is **not** proven. Later `Start-Process -Verb RunAs`
UAC **2143/service cannot accept commands**. TimerQ still skip. Overlay
off. Do not leftover `--cr3` while Relic lives. Nested-map forbidden.

## Host crash wininit 0x50006 (2026-09-13 23:45)

Hold on Relic **21296** was **status=0**. Host then died: wininit **1074
`0x50006`** 23:45:02, Event **6008** 23:47:18, **no new Event 41**.
Crash image **`A67B068F`**. Nested `-Verb RunAs` + possible shared OS
GPA NX. Do **not** remap. Do **not** hook ntdll/user32/kernel32.
Finding: [wininit 0x50006](2026-09-13-hv-cycle9-wininit-50006.md).

