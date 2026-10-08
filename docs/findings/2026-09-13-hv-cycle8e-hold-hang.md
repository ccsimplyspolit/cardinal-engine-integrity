# Cycle 8e hang ~1 min after hold — KPTI CR3 treated as foreign (2026-09-13)

Mailbox ops 1–12 unchanged. **Do not map.** Overlay inject did **not**
run (DLL still 19:39; Community MSBuild interrupted). No stock x64dbg.
No Relic WER this boot (unlike 8d APPCRASH).

## Point

Event **41** `20:27:31` (boot `20:27:27`, 6008 previous shutdown
**20:25:45**) is **not** nested `kdu`. Boot `20:05:33` had **one** idle
map: Cycle **8e** `load_ok` **20:18:01** sys `AB7D293D` (1095168). hitch
`inner=0` `npf=0`. ping **pong**. Relic **none** at kdu.

Hang sits **during a live hold**, not after Relic death:

| Time | Event |
|---|---|
| 20:18:01 | idle `load_ok` 8e `AB7D293D` |
| 20:18:34 | disk overwritten by **8f** `02F9B040` (1095680) — **not mapped** (`Map-AfterZppu` exit 6) |
| 20:21:39 | keyed ping **pong**; hitch-host watcher **ended** 20:21:03 (`npf=0`) |
| 20:22:37 | Relic **16544** `0x7FF6BC440000` Steam `-dev -nodbg -notrap` |
| 20:26:09 | `hold --apply` 4 sites **status=0**, hasher protect **status=0**, `slots=0` |
| ~20:25:45–20:26:30 | unexpected shutdown (6008 vs cookie 20:26:10; ~25s skew) |
| 20:27:27 / 20:27:31 | boot + Event 41. ping **ping_err**. Relic **none**. Minidump empty |

Capture: `aoe4-hv/docs/_bsod/crash-20260913-202754` (HostPrep `-Boot`).
Cookie stayed `load_ok_pending_alive` (hold stamp `20:26:10`,
`boot_at_attempt=20:05:33`). Gate **21**.

Hold CR3 split (KPTI) from `cycle8-hold.txt`:

- `hello cr3=0x1b3eed000` then `0x382a41000`
- `query cr3=0x27fca9000` (EPROCESS DTB) `image_rpm=0x7ff6bc440000`

## Hyp (held)

8e/8f `stealth_npf_must_disarm(stale=false, owner_dtb, guest_dtb, execute)`
returned **true** whenever guest CR3 PFN ≠ owner PFN. That was the 8d
“GPA reuse” extra. On a **live** Relic it matches **KPTI kernel CR3**
(hello) vs **user DTB** (query / `owner_cr3`).

Sequence: execute NPF on hooked `.text` with kernel CR3 →
`stealth_disarm_page_slot` restores identity **NX** while Relic still
maps the GVA → next fetch NPFs again → VMEXIT storm → Event 41. No
APPCRASH because the host died first.

8d (`A1EA2CF1`, **no** foreign-CR3 disarm) held Relic **34288** for
minutes (`slots=0` + rbhost) and hung **after** `c0000005`. 8e added
the disarm and hung **~seconds after apply**, Relic still “alive”.

Stale-GVA reap (`stealth_reap_page_if_stale`) is still the right 8d
fix. Foreign-CR3 execute disarm is **not**.

## Do not

- `kdu` / `sc start Aoe4Hv` / nested-map this boot
- remap 8e `AB7D293D` / 8f `02F9B040` / 8d `A1EA2CF1` / 8c `D78C5065` /
  8b `8C9D7CDD` / Cycle 3 `5351E024`
- hold dead **16544** / 34288 / 32172 / 36888 / 20068 / 5012 / 3088 /
  36364 / 3256
- open IDA on a live Relic
- launch overlay / stock x64dbg until a **new** authorized idle map
  whose `last_fix_time` is newer than `20:27:31`

Next map only after user **запускай**.

## Fix (source, not mapped)

`stealth_npf_must_disarm` = **stale GVA only**. Drop foreign-CR3
execute. `handle_stealth_npf` already reaps stale pages; kernel-CR3
fetch on a still-mapped hooked 4K falls through to the stealth copy
(non-site path). Mailbox 1–12 unchanged.

## Cycle 8g (built 20:35:46, **not mapped**)

sys **1095168** SHA256 `7B5C8989…DC2BBB`, ELF **1044872**
`E97A9C6E…EF4314`. Verify-AmdPort + insn_boundary **PASS**. Overlay
Release **20:35** `DllInjector.exe` has `--patch-game` UTF-16.
Do not remap `AB7D293D` / `02F9B040`. Next idle map only after
**запускай**.
