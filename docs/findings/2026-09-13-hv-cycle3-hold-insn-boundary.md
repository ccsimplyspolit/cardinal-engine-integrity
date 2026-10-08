# Cycle 3 — hold `status=10` / `insn_starts_at` (2026-09-13)

Runtime owner cycle. **One hypothesis. Source only. Do not map this boot.**

SVM already `load_ok` **16:21:43** (Cycle 1 sys 16:20:21 1075200 B).
Cookie `in_progress`. Nested-map = Event 41.

## Cycle 3

| | |
|---|---|
| Hypothesis | `stealth_arm` refuses WW-clone / INT3-1FDC sites because `insn_starts_at` 15-byte left-scan reports mid-insn overlap on the **identity GPA copy**, even when usermode RPM first byte is `E8`. Mailbox returns `hook_failed` (**10**), not `not_found` (**8**). |
| Evidence | Relic PID **5012** `0x7FF7BABB0000`, slots=0, 39 sites `E8_ok`. First `hold --apply`: 20 `status=0` then 19 `status=10` (cluster `0x3F5D000` / `0x3F61000`–`0x3F70000` WW_family + `0x3E421E2`/`0x3E426F5`/`0x3E429F8`). `max_stealth_sites=64` `max_stealth_pages=32` (29 unique pages) — not a cap. Resolve worked (not status=8). Six retries + mailbox `rax=2`. |
| Changed | `hypervisor/src/hypervisor/npt_stealth.cpp`: nop5 + `copy[off]==0xE8` and decode length 5 → skip left-scan. Still require a real `E8 rel32`. `zpp_at.py` already stops retry after any `arm va=` line. |
| HV | **not remapped**. Disk ELF/sys **16:45:29**. Corpse was 16:20:21. |
| Mailbox | ops 1–12 untouched |
| Relic session | 5012 (do not reuse VA after death) |
| Vs AI / x64dbg | no. Do not start dbg on a 20/39 hold |
| Verdict | **ELF/sys rebuilt 16:45:29; not mapped** |
| Next | User **запускай** only after `Test-VmrunDumpGate` ok **and** ping is native `#UD` (keyed `Get-HvPingToken`). Never second `-map` while keyed ping is `pong`. Identity idle first. Exact commands: [Cycle 3 запускай path](2026-09-13-hv-cycle3-zapuskay-path.md). |

## Rebuild (16:45)

`stealth_nop5_e8_ok` extracted. `insn_boundary` leftover case PASS.
sys SHA256 `5351E024…AD5CF1`. See
[Cycle 3 ELF rebuild](2026-09-13-hv-cycle3-elf-rebuild.md).


## Do not

Quote `zpp key=` / `last-zpp-key.txt`. `sc start Aoe4Hv`. Remap 15:51 or 16:20 sys on a live SVM. Visible x64dbg before 39/39 apply.
