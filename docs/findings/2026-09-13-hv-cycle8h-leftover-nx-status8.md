# Cycle 8h: leftover NX after 15720/10324/19956 — status=8 is not_found, not restore (2026-09-13)

Mailbox ops 1–12 unchanged. No op 13. **STOP. Do not map.** ping **ud**. Event **41** `22:07:45` on `17E25811`.
Live stamp `cycle8h-leftover-nx-live.txt` 22:22:16: Relic **0**, last 41 **22:07:45**.

Closes the quote: leftover NX after 15720/10324/19956 — clear status=8, not proven.

## Verdict

| Claim | Status |
|---|---|
| leftover `--clear --cr3` status=8 = NX restored | **false** — mailbox `not_found` (8). ELF did **not** call `stealth_restore_primary` |
| printed `sites=0` on status=8 = slots empty | **false** — ELF returns before `reply.aux = stealth_site_count`; print is request aux 0 |
| identity NX restored on those GPAs (live bits) | **not proven** — **blocked by 41** (SVM off; no NPTE dump) |
| code path that *would* restore identity | **specified** — reap / matching `--cr3` / name resolve |
| keyed `ping` / `Get-HvPingToken` reaps leftover | **false** — only mailbox op 3 |
| `zpp_ctl stealth --clear` clears Relic leftover | **false** — ZPPN r8=2, **this** caller CR3 |
| leftover GPA NPTE readable without op 13 | **no** — ops 1–12 have no PFN/NX |

**leftover NX = still unknown / blocked.** Not proven restored. Do not invent PTE.

## CR3 re-check (hold files)

| PID | Image | CR3 | Surviving file |
|---|---|---|---|
| **3832** | `0x7FF7B6EE0000` | **`0x55ABF3000`** | `cycle8h-hold.txt` query `status=0 cr3=55abf3000` `image_rpm=7ff7b6ee0000` |
| **15720** | `0x7FF7B6EE0000` | `0x157A64000` | cycle-state *had* this CR3 when pid=`15720 dead` (overwritten 21:38). `cycle8h-steam.txt` only `pid=15720 start=21:23:08`. Hold log overwritten by 3832. Same ASLR this boot. |
| **10324** | (same boot) | `0x80b47e000` | **no** hold/query line. Hardcoded in `Cycle8h-ClearLeftoverCr3.ps1`. Event 1000 pid `0x2854` = 10324 ntdll `0x328b0` 21:34:42 |
| **19956** | (same boot) | `0x1BD9F9000` | **no** hold/query line. Same script. Event 1000 pid `0x4DF4` = 19956 ntdll `0x27384` 21:36:21 |

Do not treat the three leftover CR3s as re-read query lines. 3832 is the only hold-file query still on disk.

Hold RVAs (16.3.11308.0), not PTE:

| PID | Armed |
|---|---|
| 15720 | Enqueue `0x3DD2550` eax=0, KickCtor `0x3E691F4` eax=0, TimerQ `0x3E672DC` eax=0, hasher `0x3E57050` `0xFFFFFFFE` + protect `0x3E57000` |
| 10324 | packed Enqueue/KickCtor (ciphertext 4K) |
| 19956 | Enqueue + KickCtor + hasher after 45s settle (no TimerQ) |
| 3832 | Enqueue + KickCtor + hasher; **no** TimerQ |

## 1. Code — when status=8, when NX is restored

`um_command_status::not_found = 8` (`capture_config.h`).

### mailbox op 8 `stealth_clear` (`mailbox.cpp`)

1. `mailbox_resolve_target` (live EPROCESS by name + `find_running_process`).
   If **yes**: `stealth_disarm_cr3(reply.target_cr3)` — **live** DTB. This is 22:03:52 (`cycle8h-evidence2.txt`): leftover `--cr3 0x157a64000` printed `clear status=0 sites=0 cr3=55abf3000` while 3832 lived. Name resolve ignored leftover CR3 and disarmed the live hold.
2. If resolve **fails** and leftover CR3 is set: scan `stealth_sites[i].owner_cr3 == want`.
3. If **no** match: `status=8`, return. **No** `stealth_disarm_cr3`. **No** `stealth_restore_primary`.
4. If match: `stealth_disarm_cr3(want)` then `reply.aux = stealth_site_count`.

Process gone → resolve fails (no running Relic). leftover `--cr3` restores **only** if a site still has that `owner_cr3`.

`owner_cr3` at arm is the DTB `stealth_arm` received. Agent sets `target_cr3=0` so ELF uses `UserDirectoryTableBase` / `select_user_cr3`. Query CR3 is kernel DirectoryTableBase (KPTI). leftover `--cr3` with a **query** value can miss `owner_cr3` even if NX is still set.

### restore (identity RWX, original PFN)

`stealth_restore_primary`: `page_number(original_pfn)` + `identity_access()` (R=1 W=1 X=1).

Called from last-site `stealth_disarm_va`, `stealth_disarm_page_slot`, `stealth_teardown`.

`stealth_reap_page_if_stale`: if `guest_virtual_to_physical(owner_cr3, va)` no longer equals the hooked GPA → disarm those sites; if no live site on the 4K → `stealth_disarm_page_slot` → restore. Policy is stale GVA only (`stealth_npf_must_disarm`). Not CR3 mismatch (Cycle 8e).

Callers: NPF `handle_stealth_npf`; mailbox **op 3** `stealth_reap_stale()`. Keyed VMMCALL ping does **not** reap. `zpp_ctl stealth --clear` is ZPPN r8=2 on **this** CR3 (`hypervisor.cpp` `stealth_cmd_clear`).

Every `zpp_aoe4` command runs `do_hello` → mailbox ping → reap **before** op 8. So 21:38:07 leftover `--clear` **did** reap first. That still does not dump NPTE. ping reply `aux` is CPU index.

## 2. Live logs (old boot 21:05:57) — not PTE

| Time | What | Meaning |
|---|---|---|
| 21:19 hitch | `inner=0 npf=0` 32 CPU | idle map; **before** Relic |
| 21:25 | 15720 hold TimerQ + hasher | NX armed (code), no NPTE dump |
| 21:26–21:29 | 15720 AV `0x3AD6BC6` / `0x8CD153` | process gone; host pong |
| 21:30:42 | `zpp_ctl stealth --clear` status=ok | **python** CR3, not Relic leftover |
| 21:34 | 10324 packed hold | dead ntdll `0x328b0` |
| 21:35:48 | `zpp_ctl stealth --clear` status=ok again | same: this CR3 |
| 21:36 | 19956 ntdll `0x27384` | dead |
| 21:38:07 | leftover `--cr3` x3 | hello + mbox-ping then `clear status=8 sites=0 cr3=<leftover>` Relic **0**, ping **pong** |
| 22:03:52 | leftover `--cr3` while 3832 live | `status=0 cr3=55abf3000` — disarmed **live** hold |
| 22:07:45 | Event 41 | SVM gone |

21:38:07 status=8 = resolve miss + no `stealth_sites` tagged with those leftover CR3s. Compatible with (a) ping-reap already restored under a **different** owner DTB, or (b) leftover CR3 never matched `owner_cr3`. **Not** a read of identity NX.

Hitch after hold: **none**. Do not write NPF was.

## 3. This boot (22:07:40)

`cycle8h-leftover-nx-live.txt` 22:22:16: ping **ud**, Relic **0**, Event 41 **22:07:45**. `--clear` refused. Identity/stealth tables gone with the map. No leftover GPA walk. No op 13.

## Do not

- remap `17E25811` / nested-map / invent NPTE
- treat leftover `--clear` status=8 as NX off
- `stealth --clear --cr3` while any Relic lives
- hold 15720 / 10324 / 19956 / 3832
- add mailbox op 13
- remap `17E25811` (usermode guard is not a new sys)

Usermode guard rebuilt **22:32:18**:
[post-41 usermode guard](2026-09-13-hv-cycle8h-post41-usermode-guard.md).
