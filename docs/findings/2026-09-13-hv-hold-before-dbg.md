> **Superseded ritual (2026-09-13):** product is HV `wait-hold` →
> `DllInjector --patch-game` → **stock** `x64dbg.exe`
> (`Run-ProductDbgCycle.ps1`,
> [RELIC_DEBUG_ATTACH.md](../RELIC_DEBUG_ATTACH.md)). Hidden
> `Start-X64dbgHidden.ps1` then Attach is fallback only. This file stays
> as the 00:46 / 00:59 live-audit log.

## Live audit PID 53020 (00:46) ? hooks NOT armed, debugger NOT started

Relic **53020** titled `Age of Empires IV `, start 00:40:51,
`path=D:\SteamLibrary\steamapps\common\Age of Empires IV\RelicCardinal.exe`,
`image=0x7ff6ecd90000` SizeOfImage `0x8c3d000` match, responding.
x64dbg=0. Overlay **not** in modules (no `InternalInjector`). WindowWatch
44368+44488. SVM VMMCALL **pong**. ZPPX hello/mbox-ping **status=0**
(intermittent rax=2 on some hello). `query status=0 cr3=0x7e2da2000
image=0` `image_rpm=0x7ff6ecd90000`.

Window **empty** before and after apply: `slots=0 accum=0 flag=0`.
JUMPOUT gate=0. mismatch_budget=99. hasher_raw sig_ok (original
`48 89 5c 24 20 57?`). Enqueue/KickCtor/TimerQ/FlushArm/Watcher/7AB0
prologues **original** (correct ? forbidden to stub). dest skip
`0x3F04118`/`0x3F2D402`. 39 sites all `E8_ok`.

`hold --apply` 6/6: every `arm va=? status=8 sites=4294967295`. Hasher
`protect 0x3E57050` **never ran**. HV `read` of site/hasher VA hello
rax=2. **Zero NPT execute-copy. Zero hasher write-split.**

Did **not** start x64dbg. Ritual: apply=0 and slots=0 first. This SVM
cannot GVA?GPA Relic `.text`. Next = Relic dead, ZPPU 32/32, one map of
`pte_phys` ELF.

## Live PID 31656 (00:59) ? NPT identity OK, execute-copy NOT armed

New SVM **00:55:36** key `0x1e8e77bb5bf4ca8c` `load_ok` `userdtb_off=0 peb=0`
(always-log). ZPPU 32/32 then one KDU map. Relic **31656**
`image=0x7ff765e20000` titled `Age of Empires IV -dev -nodbg -notrap`.
x64dbg=0. Overlay not injected.

NPT contract check (AMD NPT, not NTP):

| Check | Result |
|---|---|
| Identity / RPM hasher `0x3E57050` | original `48 89 5c 24 20 57?` ? AT raw-load OK |
| Identity E8 Watcher+INT3 (39 sites) | all `E8_ok` ? no plant |
| Dest `0x3F04000` / `0x3F2D000` | skipped, not protect |
| Execute-copy NOP5 | **not armed** ? 39/39 `arm status=8` |
| hasher `protect` write-split | **not reached** |
| Enqueue/KickCtor/TimerQ/FlushArm/Watcher/7AB0/45E8 | prologues original (correct ? no stub) |
| `--eax 1` hasher | not used |
| Window | `slots=0 accum=0 flag=0` |
| x64dbg | not started (apply != 0) |

`query status=0 cr3=0x7e2da2000 image=0` (same CR3 as 15556/53020).
C-bit ELF **is mapped**; walk of Relic user VA still fails. Loader
`userdtb_off=0` ? `phys_reads_mz` still cannot prove a user DTB.
Identity == execute == original: AT ?thinks all is well? because
**nothing is split**, not because execute is NOP. Do not Attach.
Do not nested-map.

Early `wait-hold` at T+2.3s saw 57 WW E8 / 41 pages (compact XOR);
stable titled scan is 37+4 / 29. `known_enqueue_rvas` + page trim
landed in `zpp_at.py` / `aoe4_16.3.11308.json`.

## C-bit / user CR3 (status=8), code not mapped yet

`status=8` is `not_found`, not `hook_failed` (10). Usermode already had
the 39 Enqueue sites. ELF `mailbox_resolve_target` cannot GVA?GPA Relic
`.text` because:

1. Raphael **SME C-bit = bit 51**. `pte::page_number()` takes bits
   12?51, so a C-bit PTE becomes GPA ~2 PiB. Identity NPT is 34 GiB;
   `MmCopyMemory(Physical)` misses. Same bug in loader `phys_v2p`
   (`e &= 0x000ffffffffff000`) ? `userdtb_off` discover `found=0` and
   the log line is skipped when the offset is 0.
2. `select_user_cr3` `plausible()` allowed DTB `< 1 TiB`. Named `0x388`
   is first; overflow is secondary. On AMD KVAS is often off, so the
   process DTB **is** `DirectoryTableBase` `0x28` (query
   `cr3=0x7e2da2000` ? 31.5 GiB). Walk of that DTB still needs C-bit
   strip.

Wired on disk, **not** in the live SVM (map 00:04:46):
`hypervisor/include/zpp/x64/amd/pte_phys.h` (`phys48_*` drops bit 51),
ELF `guest_virtual_to_physical` / `guest_page_executable` /
`select_user_cr3` `ram_dtb` + 96 cands, loader `phys_v2p` +
`PsGetProcessSectionBaseAddress` fallback, always-log
`zpp userdtb_off=`. `tests/amd_layout.cpp` asserts C-bit strip.

Do not `hold --apply` on this SVM. Do not nested-map. Relic must be
dead for ZPPU 32/32 then one `Map-AfterZppu.ps1`.

## Live Relic 53020 (00:40, still empty)

`python tools/zpp_at.py window` 00:42: PID **53020**
`image=0x7ff6ecd90000` (same ASLR as 15556 ? **do not reuse VAs**).
`slots=0 accum=0 flag=0`. x64dbg=0. SVM ping **pong** key
`0x32e38c24a9d00638`. Apply on this map will still be status=8. Do not
Attach. If any slot appears, kill Relic now.

## Live apply 00:32 PID 15556 (empty window)

Relic **15556** `image=0x7ff6ecd90000` `slots=0`. x64dbg closed. SVM ping
pong. Usermode scan: **37** Watcher-tag + **4** INT3, skip dest
`0x3F04118`/`0x3F2D402`, arm **39** sites / **29** pages, all `E8_ok`.

`query` **status=0** `cr3=0x7e2da2000` `image=0` (kernel DirectoryTableBase;
`image_rpm` matches Toolhelp). Every `stealth --nop` **status=8 not_found**
(`aux` leftover). `mailbox_resolve_target` cannot GVA-to-GPA the Relic
`.text` VA. Not `hook_failed` (10). Loader log has **no** `userdtb_off=`.
KPTI two CR3s (PCID ???). NPT execute-copy never ran. Hasher protect not
reached. `prove` still unproven.

Do not Attach. Nested-map forbidden. Window still empty after the failed
apply.

# 2026-09-13 HV patches timers / checks / AT before debugger

Same boot **21:25:38**. SVM map **00:04:46** (hypercall key gitignored in `aoe4-hv/docs/last-zpp-key.txt`)
(leftover=180). Loader `zpp_loader.sys` **23:51:20**. Dump still
`091226-15843-01.dmp` **20:10:42** `0xDA` `0x107`. Do not mix VAs.
Do not nested-map.

User order (Vs AI only):

1. Relic **empty** (`slots=0 accum=0 flag=0 begin=end=0`).
2. HV patch **timers + checks + anti-tamper** (`zpp_at.py wait-hold`).
3. **Then** hidden x64dbg (`Start-X64dbgHidden.ps1`).
4. **Then** Attach.
5. Any slot at any time: **kill Relic immediately**. KickCtor is already
   armed; the 2?3 min death is delayed, not optional.

## What HV actually patches (catalog still forbids stubs)

| Layer | Usermode arm | Not |
|---|---|---|
| AT / window | ZPPN `--nop` (`eax=0xFFFFFFFF`) on Watcher-tag `E8?Enqueue` | Watcher / Enqueue prologue, plant `.text` |
| Checks | same scan: INT3 packs `RetaddrInt3_CAF8` / `RetaddrInt3_1FDC` | IatPack / 45E8 |
| Timers | Enqueue NOP so KickCtor `0x3E691F4` never arms | stub TimerQ / KickCtor / FlushArm / EventSchedule |
| Hasher | `protect --rva 0x3E57050 --size 0x1000` (skip dest `0x3E58000`) | hasher `--eax 1` |

Skip dest Enqueue pages `0x3F04000` / `0x3F2D000` (sites `0x3F04118`,
`0x3F2D402`). Cap 32 stealth pages. Name for HV: stem `RelicCardinal`.

`hold --apply` **REFUSE** (rc=3) if window already dirty; **REFUSE**
(rc=4) if `x64dbg.exe` (or other `DBG_PROCESS`) is visible.

## Tonight before this ritual

Visible MCP `x64dbg.exe` packed DualFlag even without Attach (42396 at
23:54). Packed fill still happens ~2?6 min with dbg closed. `hold --apply`
never succeeded this boot (`status=8` on 23:18 SVM; 00:04 SVM never
applied on an empty PID). Relic 42380 was already `slots=3` by ~00:07.

00:09: ping **pong**. Steam **42244** up. Relic **not** running.
x64dbg **23152** killed before Steam `-applaunch`. WindowWatch **44368**
kept (RPM).

## Code

`aoe4-hv/tools/zpp_at.py` `wait-hold`: one `.text` E8 pass; merge INT3
into the arm list; hasher protect after stealth rc=0; re-check window.

Canon: ADR-007 ?6, UPDATE_GUIDE ?2.3.1 HV hold, `hold_empty.hv_after_remap`
in `aoe4_16.3.11308.json`.
