# Cycle 8d hang after Relic AV — not a nested map (2026-09-13)

Mailbox ops 1–12 unchanged. No remap this turn. Overlay inject did **not**
run (DLL still 19:39; no `DllMain` this session).

## Point

Event **41** `20:05:37` (boot `20:05:33`, 6008 previous shutdown
**20:04:24**) is **not** a second `kdu` on a live SVM. Boot `19:36:13`
had **one** idle map: Cycle **8d** `load_ok` **19:43:11** sys `A1EA2CF1`
(1088000). hitch `inner=0` `npf=0`, then `hitch_watch_end`. Cookie stayed
`load_ok_pending_alive` (hold stamp `19:53:20`). No second `kdu_begin`
after 19:43:09.

Hang sits **after** Relic `APPCRASH` `c0000005` **20:01:37** (WER 1001,
`RelicCardinal.exe` 16.3.11308.0) and a 20:04 snapshot with **two**
`RelicCardinal` PIDs (**34288** hold target + **32172**). Leftover rbhost
`smabcc.exe` 30868 was still up. Minidump empty (CrashDumpEnabled=0).

## What “несколько мапов подряд” actually was

Nested map = `kdu` while ping=`pong` / leftover SVME. **8d did not do that.**

The **previous** boot (`17:09:28`) did map five times without a reboot
(`pre-map-trace` ping=`ud` each time — leftover, not a clean `pong`):

| kdu | Cycle | Note |
|---|---|---|
| 17:32 | 5 | same boot |
| 18:03 | 6 | same boot |
| 19:05 | 8 | same boot |
| 19:18 | 8b | same boot |
| 19:32 | **8c Relic-live** | hang **19:34:40** → Event 41 **19:36:17** |

That chain is why 8c died. 8d was a **fresh** boot, Relic **none** at kdu.

## 8d timeline (boot 19:36:13)

| Time | Event |
|---|---|
| 19:43:11 | idle `load_ok` hitch inner=0 |
| 19:53:00 | Relic **34288** `0x7FF716E90000` `cr3=0x20dd0b000` |
| 19:53:20 | cookie hold note; arm Enqueue/KickCtor/TimerQ/hasher status=0 |
| 19:59:34 | prove `slots=0` + hidden rbhost 30868 |
| 20:01:37 | Relic WER `c0000005` |
| 20:04 | PIDs 34288 + 32172; rbhost still live |
| 20:04:24 | unexpected shutdown |
| 20:05:33 / 20:05:37 | boot + Event 41. ping `ping_err`. Relic none |

## Do not

- `kdu` / `sc start Aoe4Hv` / nested-map this boot
- remap 8c `D78C5065` / 8b `8C9D7CDD` / Cycle 3 `5351E024`
- remap 8d `A1EA2CF1` until this hang is fixed (Relic-AV + second Relic
  under armed NPT is the working hyp — not a second mapper)
- hold dead 34288 / 32172 / 3256 / 36364
- open IDA on a live Relic
- launch overlay / stock x64dbg until a **new** authorized idle map

Next map only after user **запускай** and a `last_fix_time` newer than
`20:05:37`. Capture: `docs/_bsod/crash-20260913-200601`.

## Fix (source, not mapped)

`handle_stealth_npf` used to treat **any** execute/write on a hooked GPA
as stealth (including after Relic died). Hide already called
`hidden_owner_still_maps`. Stealth now:

1. `stealth_reap_page_if_stale` — GVA→GPA miss → restore identity NX
2. Foreign-CR3 **execute** → `stealth_disarm_page_slot` (GPA reuse)
3. Mailbox ping also `stealth_reap_stale`

Mailbox ops 1–12 unchanged. Do not remap `A1EA2CF1`.

Built **not mapped**: sys 20:12:34 **1095168** SHA256 `AB7D293D…C49944`,
ELF **1044952** `499E03B5…1ADDF3`. Verify-AmdPort + insn_boundary PASS.
Parent then idle-mapped **8e** `load_ok` **20:18:01** (Relic none, hitch
`inner=0` `npf=0`). That is the live image.

## Cycle 8f (disk only, 20:18:34)

Same NPF policy, now in `hypervisor/include/zpp/x64/stealth_reap.h`
(`stealth_npf_must_disarm`: stale GVA **or** foreign-CR3 execute).
`handle_stealth_npf` calls it. `insn_boundary` + static_assert cover
Relic 34288 DTB vs other / write-only / C-bit. `Map-AfterZppu` exit **6**
refuses corpse SHA256 prefixes `A1EA2CF1` / `D78C5065` / `8C9D7CDD` /
`5351E024` (already exit **5** Relic-live, exit **4** ping≠ud).

sys **1095680** SHA256 `02F9B040A29F839624984A7AD5950C21675E284827F12CB99044CD3677269888`
ELF **1045424** `A1447EFFC71A62B386FF5058DC30259121BBABDE7425AECFC17EDAEB908153B7`.
Verify-AmdPort PASS. **Do not nested-map 8f** over live 8e this boot.
Cookie `sys_mtime` 20:18:34 / `sys_bytes` 1095680 is the overwritten
disk file after 8e `load_ok`; live remains `AB7D293D` 1095168.
