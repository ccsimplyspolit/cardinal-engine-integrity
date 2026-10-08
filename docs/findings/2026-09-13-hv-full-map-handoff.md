# 2026-09-13 HV full map + handoff (goal not met)

> **Superseded ritual (2026-09-13):** product is `wait-hold` →
> `--patch-game` → stock `x64dbg.exe` (`Run-ProductDbgCycle.ps1`).
> “Then hidden x64dbg → Attach” below is **not** the live order.
> [product cycle](2026-09-13-product-dbg-cycle.md).

Snapshot **2026-09-13 ~13:15**. Vs AI only. RVAs only — never mix VAs
across Relic PIDs. Hypercall keys stay in gitignored
`aoe4-hv/docs/last-zpp-key.txt` (file **missing** this afternoon).
Dump still `091226-15843-01.dmp` **20:10:42** BugCheck **0xDA** arg1
**0x107**. Boot that night: **2026-09-12T21:25:38**.

Canon ritual: [UPDATE_GUIDE.md](../UPDATE_GUIDE.md) HV-hold paragraph.
Session trail: [2026-09-13-hv-hold-before-dbg.md](2026-09-13-hv-hold-before-dbg.md),
[2026-09-13-hv-version-agnostic-offsets.md](2026-09-13-hv-version-agnostic-offsets.md).
HV tree: `k:\aoe4_dlc\hh\aoe4-hv` branch **`amd`** @ `986b5da`. Overlay:
`AOE4HOOK` **`main`** @ `e05a46e220`. Workspace `hh` is **not** a git
repo. OS-temp handoff (same facts, compact): `%TEMP%\aoe4-hv-handoff-2026-09-13.md`.

## Verdict

`hold --apply` **never** returned all `arm … status=0` this boot.
NPT execute-copy NOP is **not** armed. Hasher `protect 0x3E57050`
**never ran**. Hidden x64dbg was **never** started (correct: apply
never 0). `prove --sec 60` / `verdict=hv_hold` is **not** complete.

Now (13:15): Relic **not** running. Steam **31112** (12:00).
WindowWatch **47444** (12:29). x64dbg=0. Overlay not injected.
`zpp_ctl.py ping` = **`ud`**. `HypervisorPresent=False`.
`last-zpp-key.txt` **missing**. Last Relic in `warnings.log`: **12:37**
`RUN-OPTIONS []` (no `-dev -nodbg -notrap`, **no HV**). Last successful
SVM map: **00:55:36** `load_ok`, then overnight SVM gone.

## User-enforced order (do not skip)

1. Relic empty: WindowWatch `slots=0 accum=0 flag=0 begin=end=0`.
2. HV patch timers + checks + anti-tamper:
   `python tools/zpp_at.py hold --apply` / `wait-hold`.
   NPT execute-copy NOP, not overlay plant.
3. **Then** hidden x64dbg: `Start-X64dbgHidden.ps1`.
4. **Then** Attach.
5. Any slot → **kill Relic immediately**. Do not wait 2–3 min.

Success = all `arm … status=0`, hasher protect 0, window still empty.
**Then** hidden dbg. `prove --sec 60` still required for
`verdict=hv_hold`.

## Product split

```
usermode finds sites          HV arms via frozen mailbox ops 1–12
zpp_at.py / RPM / Toolhelp →  stealth_arm / protect (NPT)
identity (hasher raw-load) = original bytes
execute-copy               = NOP5
```

AT must **think everything is fine** on **identity**. NOP only on
**execute-copy**. No plant `.text`. No `--eax 1` hasher. No stub of
Enqueue / KickCtor / TimerQ / FlushArm / Watcher / 7AB0 / 45E8
prologues. Skip dest pages `0x3F04000` / `0x3F2D000` (sites
`0x3F04118`, `0x3F2D402`). Hasher `protect 0x3E57050` size `0x1000`
skip dest `0x3E58000`. Cap 32 stealth pages. HV name stem
`RelicCardinal`. Relic is **not** first VMRUN. No `sc start Aoe4Hv`.

| Layer | Arm | Forbidden |
|---|---|---|
| AT / window | ZPPN `--nop` `eax=0xFFFFFFFF` Watcher-tag `E8→Enqueue` | Watcher / Enqueue prologue, plant |
| Checks | INT3 `RetaddrInt3_CAF8` / `RetaddrInt3_1FDC` | IatPack / 45E8 stub |
| Timers | Enqueue NOP so KickCtor `0x3E691F4` never arms | stub TimerQ / KickCtor / FlushArm |
| Hasher | `protect 0x3E57050` write-split | `--eax 1` |

`hold --apply` REFUSE: rc=3 dirty window, rc=4 visible `DBG_PROCESS`,
rc=2 window RPM fail.

Scan when window empty: 37 Watcher-tag + 4 INT3 `E8→RA_Enqueue`
(`0x3DD2550`), skip dest, arm 39 sites / 29 pages, all `E8_ok`. Early
`wait-hold` at T+2.3s can see 57 WW E8 / 41 pages (compact XOR);
stable titled scan is 37+4 / 29.

Query typical (when SVM was up): `status=0 cr3=0x7e2da2000 image=0`
`image_rpm=` Toolhelp. `svm_bringup=true` skips PEB fill on query;
stealth uses RPM VAs in `sites.json`. Overlay often **not** injected
during hold.

## Trees / host

| | |
|---|---|
| HV | `k:\aoe4_dlc\hh\aoe4-hv` git **`amd`** `986b5da` (message «ц») |
| Overlay | `k:\aoe4_dlc\hh\AOE4HOOK` **`main`** `e05a46e220` |
| Plugins | **only** `Documents\AOE4HSettings` |
| Inject | `AOE4HOOK\internal\x64\Release\` `InternalInjector.dll` next to `DllInjector.exe`. Elevate `Start-Process -Verb RunAs` |
| Mapper | KDU NAL `aoe4-hv/docs/zpp-mapper.path` / `C:\Users\sshunko\source\repos\MyDriver23\third_party\KDU\Source\Hamakaze\output\x64\Release\kdu.exe` |
| Steam | `C:\Program Files (x86)\Steam\steam.exe -applaunch 1466860 -dev -nodbg -notrap` |
| Relic | `D:\SteamLibrary\steamapps\common\Age of Empires IV\RelicCardinal.exe` |
| WindowWatch | `C:\Users\sshunko\Downloads\WindowWatch.exe` |
| CPU | Ryzen 9 **7950X**, 32 threads, SVM+NPT |
| OS | Win11 Pro **25H2** `26200.7171` (AIDA 21:28). ntos file can still say `10.0.26100.7171` |
| PCID | **нет**. INVPCID да → KPTI = two CR3s when KVAS on |
| SME | C-bit **51**, MAXPHYADDR **48**, TSME **off**, identity NPT **34 GiB** |
| Hyper-V/VBS | Off. testsigning **No**. Do not enable TSME |
| AIDA finding | [2026-09-12-hv-aida-25h2-pcid.md](2026-09-12-hv-aida-25h2-pcid.md) |

Product remap = **ZPPU leave then one KDU `-map`**. Nested `-map`
while ping pongs = hang / `svme_already`.
`Start-ZppLoader.ps1` **aborts if Relic is running**. Relic-live remap:
`aoe4-hv/docs/Map-AfterZppu.ps1`. Leave: `python tools/zpp_ctl.py unload`
with `ZPP_HYPERCALL_KEY`, **32 CPUs**, 64-bit Python. **Do not**
`zpp_unload.ps1`.

Build: `aoe4-hv/build_windows.bat` (NDK ELF + LLVM sys) then
`tools/build_zpp_aoe4.bat`. `ZPP_AOE4` =
`aoe4-hv/out/debug/x86_64/zpp_aoe4.exe`. Last known good map artifacts
were ELF **00:55** (C-bit walk). Version-agnostic discover
(`kprocess_field.h`, `PsGetProcessPeb` decode) landed **on disk after**
that map and was **not** in the 00:55 image.

ADR: aoe4-hv/docs/decisions/007-universal-usermode-modules.md
(conflict hunks in this file **resolved 13:15**, keep HEAD =
version-agnostic). Status: aoe4-hv/docs/STATUS.md
(header conflict **resolved 13:15**). MACHINE.md discover paragraph
**resolved**.

## Why apply stays `status=8`

`status=8` = mailbox **`not_found`**, not `hook_failed` (10). Usermode
already has the 39 Enqueue sites. ELF cannot GVA→GPA Relic `.text`.

Two cooperating bugs:

1. **SME C-bit bit 51.** `pte::page_number()` used bits 12–51. C-bit
   PTE → GPA ~2 PiB → identity 34 GiB / `MmCopyMemory(Physical)` miss
   → walk 0. Same mask in loader `phys_v2p` → `userdtb` discover
   `found=0`.
2. **User CR3.** 25H2, PCID нет, INVPCID да → KPTI = two CR3s when
   KVAS on. Query CR3 is kernel `DirectoryTableBase` `0x28`.
   `UserDirectoryTableBase` often 0 on AMD (KVAS off) — then DTB
   **is** `0x28` (`cr3=0x7e2da2000` ≈ 31.5 GiB, inside 34 GiB). Walk
   of that DTB still failed after C-bit ELF was mapped
   (`userdtb_off=0 peb=0`).

C-bit strip **was mapped at 00:55** (`pte_phys.h`, walk, `ram_dtb`,
always-log `zpp userdtb_off=`). **Walk still failed.** Version-agnostic
discover is on disk and **not** in that map.

`zpp_aoe4` stealth correctly sets `target_cr3=0`. Protect was patched
to do the same (do not pass query kernel CR3).

Identity RPM still showing original E8/hasher prologue is “AT thinks
all is well” **only because nothing is split**, not because execute is
NOP.

## Failed Relic sessions (do not reuse those VAs)

| When | PID | Image | Window | Apply |
|---|---|---|---|---|
| 00:32 | 15556 | `0x7ff6ecd90000` | empty then packed `slots=3` | 39× status=8 |
| 00:46 | 53020 | same ASLR (different PID) | empty | 6× apply, 39× status=8 |
| 00:59 | 31656 | `0x7ff765e20000` | empty, titled `-dev -nodbg -notrap` | still 39× status=8 after C-bit map |
| 12:37 | (exited) | — | started **without HV**, `RUN-OPTIONS []` | n/a |

## Code map (keep HEAD semantics)

Clean (no `<<<<<<<`):
`hypervisor/include/zpp/x64/amd/pte_phys.h`,
`hypervisor/include/zpp/hypervisor/kprocess_field.h`.

**Poison — committed `<<<<<<< HEAD` vs `310f799`.** Git status of
`amd` was “clean” until docs edits; sources still contain markers.
**Cannot compile / must not KDU-map** until resolved. Keep **HEAD** =
C-bit walk + version-agnostic discover. Incoming `310f799` is older
mailbox ship.

| File | Hunks |
|---|---|
| `hypervisor/src/hypervisor/hypervisor.cpp` | 25 |
| `windows_loader/src/pe_file.cpp` | 15 |
| `windows_loader/src/main.cpp` | 4 |
| `hypervisor/src/hypervisor/mailbox.cpp` | 4 |
| `tests/amd_layout.cpp` | 3 |
| `hypervisor/include/zpp/hypervisor/hypervisor.h` | 2 |
| `hypervisor/include/zpp/hypervisor/capture_config.h` | 2 |
| `tools/zpp_at.py` | 2 |
| `hypervisor/include/zpp/hypervisor/msrpm_handoff.h` | 1 |
| `tools/zpp_aoe4/zpp_aoe4.cpp` | 1 |
| `tools/zpp_aoe4/modules/aoe4_16.3.11308.json` | 1 |

Docs already stripped 13:15: `docs/STATUS.md`, `docs/MACHINE.md`,
`docs/decisions/007-universal-usermode-modules.md`. `STATUS.md` still
mentions the marker string as a warning (not a live hunk).

Do **not** add mailbox op 13.

## Next session (in order)

1. Resolve **all** remaining `<<<<<<< HEAD` in the table (keep HEAD).
   Tree must compile. Confirm `rg '<<<<<<<' --glob '*.{cpp,h,py,json}'`
   is empty.
2. `build_windows.bat` + `build_zpp_aoe4.bat`.
3. Ping is already `#UD` → **one** elevated `docs/Map-AfterZppu.ps1`.
   Relic must be dead. Abort if `svme_already`. Do not nested-map.
4. Confirm log: `load_ok`, `zpp userdtb_off=` **printed**, `peb=`
   ideally non-zero, new key → `last-zpp-key.txt`, ping **pong**.
5. Steam `-applaunch 1466860 -dev -nodbg -notrap`. The moment Relic
   exists: `window` — if slots>0 kill and restart. If empty:
   `python tools/zpp_at.py hold --apply` **immediately**.
6. Success = all `arm … status=0`, hasher protect 0, window empty.
   **Then** hidden x64dbg, then Attach.
7. Document: append this folder + prepend `aoe4-hv/docs/STATUS.md` +
   `cycle-state.json`. RVAs only. Redact live hypercall keys.

If apply still status=8 after version-agnostic map: diagnose
`select_user_cr3` / `read_guest_physical` / C-bit vs KPTI with the new
`peb=` / `userdtb_off=` log. Not another nested map.

`cycle-state.json` was stale 00:09 (`ready_to_launch`,
`launch_authorized: false`, `sys_built` 23:51). Updated 13:15 to
match this snapshot.

## Do not

- Nested KDU `-map` on live ping-pong SVM
- `sc start Aoe4Hv` / testsigning Yes / `zpp_unload.ps1`
- Ranked / plant Watcher / stub 45E8 / protect dest / hasher `--eax 1`
- Debugger before apply=0 and slots=0
- Reuse old PID bases as if they were the new process
- Wait out a `slots=3` process
- Enable TSME
- Treat explorer hello rax=2 as HV dead if Relic query status=0 (when
  SVM is actually up)
- Graphify the overlay as a substitute for this HV map
- KDU-map an ELF that still contains `<<<<<<<`

## Suggested skills (next agent)

`handoff`, `saving-workspace-context`, `aoe4-project-map`, `aoe4-hv`,
`hypervisor-amd-svm`, `grinding-until-pass`, `aoe4-x64dbg`
(observe-hold / hidden dbg). After apply=0: `aoe4-injector-loader`
only if overlay inject is in scope.
