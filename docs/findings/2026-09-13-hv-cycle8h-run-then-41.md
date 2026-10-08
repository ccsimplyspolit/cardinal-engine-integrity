# Cycle 8h: Overlay RUN then Event 41 on map 17E25811 (2026-09-13)

**STOP. Do not map. Do not remap `17E25811`.** Mailbox ops 1–12 unchanged.
No leftover NX query this boot: ping **ud**, Relic **none**, SVM off.

HostPrep capture `crash-20260913-220808` (boot 22:07:40). Parallel Capture
`crash-20260913-221025`. Hud audit `cycle8h-hud-audit.txt`. Post-41
`cycle8h-post41.txt` 22:11:42 gate **21**.

## Point

User pressed Overlay **RUN** on Relic **3832** while HV hold (map
`17E25811` / ELF `E97A9C6E`) was live. ~2 min later the host hung.
Event **41** `22:07:45`, 6008 previous shutdown **22:06:08**. Minidump
empty (`CrashDumpEnabled=0`). Not nested `kdu`. Not a new sys SHA.

| Check (this boot 22:07:40) | Value |
|---|---|
| ping | **ud** |
| Relic | none (3832 gone) |
| HypervisorPresent | False |
| Event 41 | **22:07:45** (new vs 21:06:01) |
| 6008 | hang **22:06:08** |
| hitch | last sample still 21:22 `inner=0 npf=0` (map-time only) |
| leftover CR3 `0x55ABF3000` | not queryable (no SVM) |
| gate | **21** cookie `load_ok_pending_alive` attempt_boot 21:05:57 ≠ now |
| clocks after reboot | all 32 threads **4501** MHz (`HypervisorPresent=False`) — Task Manager 16 GHz was tsc_hide APERF, gone with SVM |
| System TDR 4101 / nvlddmkm 21:55–22:10 | **none** |
| overlay NTFS mtime | **22:04:35**; last line stamp 22:06:36; 6008 hang **22:06:08** (~11 s after rearm) |

## Timeline (old boot 21:05:57, map 21:19)

| Time | Evidence |
|---|---|
| 21:38:49 | Relic **3832** `0x7FF7B6EE0000` CR3 `0x55ABF3000` |
| 21:40–21:41 | slots=0 60s no dbg (`cycle8h-prove-slots.txt`) |
| 22:00:25–22:01:16 | hidden `jahjgw` **29080** slots=0 60s (`cycle8h-hidden3.txt`) |
| 22:01:52 | elevated APC inject `auto_run=0`; PEB unlink |
| 22:03:48 | Overlay log: hide ON, user32 bodies=4, **neutralize OFF (Patch Game RUN)** |
| 22:03:52 | `stealth --clear --cr3 <dead>` while Relic lived → mailbox cleared **live** DTB; `sites` 2→0 (`cycle8h-evidence2.txt`) |
| 22:04:19 | `config.ini` saved; leftover `auto_run=1` (hud-audit) |
| 22:05:12–22:05:57 | rearm hold no TimerQ; apply Enqueue/KickCtor/hasher `status=0` **sites=3** (`cycle8h-rearm.txt`) while WORLD collect still running |
| 22:06:36 | last overlay line (`aoe4_internal.log` WORLD collect n=916) — Relic still mapping |
| 22:06:08 | 6008 hang (clock vs last overlay line: host died with Relic **live**) |
| 22:07:40 | new boot; ping ud |

## Leftover NX (code + logs, no PTE dump)

Mailbox has **no** NPTE dump (ops 1–12 frozen; no op 13). After reboot
identity/stealth tables are gone. Do **not** invent PFN/NX bits from a
live walk.

What the **code** does on a hooked 4K (`npt_stealth.cpp`):

- `stealth_arm_primary_nx`: identity leaf `page_number(original_pfn)` then
  `trap_execute()` + `write(false)` → identity R=1 W=0 X=0, original PFN.
  (`trap_execute` alone sets W=1; arm then forces W=0.)
- Stealth walk: copy PFN, stub only there. Shared identity is **not**
  rewritten to the stub PFN (SimpleSvmHook leak).
- `stealth_restore_primary` on disarm/reap: same original PFN +
  `identity_access()` (RWX).
- `stealth_reap_page_if_stale` on NPF and mailbox **ping** only if owner
  GVA no longer maps the GPA. Cycle 8e: do not disarm on CR3 mismatch.

What this hang **is not**: Cycle 8d leftover (Relic APPCRASH, NX stays on
recycled PFNs). Overlay was still walking the world at 22:06:36. Relic
died **with** the host.

What this hang **cannot prove**: leftover NX on `0x55ABF3000` after death.
ping/reap never ran after 22:06. `stealth --clear --cr3` on a dead CR3
while another Relic lives is **unsafe** (usermode `pick_clear_cr3` queried
the live DTB; ELF op 8 resolves by name first). Source refuse rebuilt in
`zpp_aoe4.exe` **22:32:18** (Toolhelp fail-closed). Live `--clear --cr3`
is still lethal if usermode is bypassed. See
[post-41 usermode guard](2026-09-13-hv-cycle8h-post41-usermode-guard.md).

Dead-CR3 clear **before** 3832 started (`cycle8h-clear-cr3.txt` 21:38:07)
was `status=8 sites=0` = `not_found` (no EPROCESS + no `owner_cr3` match).
ELF did **not** restore identity NX. Printed `sites=0` is request aux.
Closed as **blocked / still unknown**:
[leftover NX status=8](2026-09-13-hv-cycle8h-leftover-nx-status8.md).

## NPF / HashRec (no invent)

- hitch `npf=0 inner=0` is the **21:19 map snapshot**. hitch-host ended
  21:22. No post-hold / post-RUN NPF sample.
- Op 11 status = `sites` / `hidden` / session only. No hashrec hit
  counter. Identity hasher prologue was `48 89 5c 24 20…` on HV `read`
  while 3832 lived (21:54 / 22:03). After reboot: no read.

## Dual-nCR3 close-out (honest)

| Claim | Status |
|---|---|
| Identity `read_virt` = original prologues while 3832 live | yes (Enqueue/KickCtor/hasher/TimerQ/WW) |
| Identity PFN/NX bits from a dump | **no** (would be op 13) |
| Stealth copy stub bytes | **no** (identity path only) |
| NPF after RUN | **no** log |
| Leftover NX after 3832 death | **no** — host died first; SVM off now |

## Do not

- remap `17E25811` / `E97A9C6E` (this SHA just hung under hold+RUN)
- nested-map / `kdu` / `sc start Aoe4Hv`
- inject / Overlay RUN / `--patch-game`
- hold 3832 / 15720 / 10324 / 19956 / …
- arm TimerQ `0x3E672DC`
- `stealth --clear --cr3` while any Relic lives
- treat ping `ud` as permission to map

Related: [dual-nCR3 gap](2026-09-13-hv-cycle8h-dual-ncr3-gap.md),
[inject no AUTO](2026-09-13-cycle8h-inject-no-auto.md),
[8h TimerQ GPU AV](2026-09-13-hv-cycle8h-hold-gpu-av.md),
[8g AUTO then 41](2026-09-13-hv-cycle8g-freeze-then-41.md),
[8d leftover NX](2026-09-13-hv-cycle8d-hang-after-relic-av.md),
[8e KPTI disarm](2026-09-13-hv-cycle8e-hold-hang.md).
