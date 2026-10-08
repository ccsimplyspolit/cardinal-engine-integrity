# 2026-09-26 — hypervisor BSOD log is the fatal VMEXIT, not the later switch

`svm_bringup` is on. A shutdown / invalid-VMCB / #DF exit is handled in
`vm_launch` and **returns before** `vmm_code`. The CMOS write that lived
in the exit switch never ran. `publish_vmexit` stored only the exit code
in RAM (`last_exit_code`), which dies with the reboot. Hitch copies that
code only if the loader gets back to `zpp_log`.

## What is written now

On shutdown (`0x7F`), invalid VMCB, and #DF, before that return (and
before `host_halt` when bring-up is off):

| Store | Contents |
|---|---|
| CMOS `0x58` `ZPBS` / `ZPBI` / `ZPBD` | exit code, guest RIP, exit info1, low 32 of RSP and CR3, `extra` = cpu:8 \| stage:8 \| exit:16 |
| CMOS `0x48` `ZPX1` | full guest RIP plus the same pack |
| `msrpm_handoff.bsod_rip/rsp/cr3/extra` | same context for `cpu_fail` if the CPU returns |

INIT is not written. Other CPUs receive INIT during a bugcheck and would
erase the bugcheck record.

A Windows bugcheck that reaches `VMMCALL 0x133A` still stores
`KiBugCheckData` (code and four parameters). The hypervisor then fills
`extra` and `ZPX1.ctx` with the **guest CR3**, plus CPU, `elfst`, and the
last published exit. The VMCB RIP at that instruction is the callback,
not the fault, so it is not stored as RIP.

Next map harvests both CMOS regions into
`docs/_bsod/bugcheck-cmos.log`:

```text
magic=ZPBS code=0x7F p1=<rip> p2=<info1> p3=<rsp32> p4=<cr3_32> cpu=N stage=N exit=0x7F ctx=<rip>
```

`zpp stage=cpu_fail` now ends with `bsodrip=` `bsodrsp=` `bsodcr3=` `bsodx=`.

Rebuilt `out/debug/x86_64/zpp_loader.sys` at 15:40, marker `ZPPBUGCK1`.
Not mapped.

## Reading it back without mapping the hypervisor

`out/debug/x86_64/cmos_harvest.sys` only reads those CMOS bytes and appends
`docs/_bsod/bugcheck-cmos.log`. It does not enter SVM. `HostPrep-AtBoot.ps1`
maps it with kdu when the previous boot's verdict is `bugcheck`,
`unexpected_reset`, or `critical_process`. A planned shutdown skips the map.
The reader returns `STATUS_INSUFFICIENT_POWER`, so KDU drops the image
after the file write. An empty CMOS still leaves
`docs/_bsod/cmos-harvest-status.txt` (`result=empty` or `result=hit`).

If the guest read of the callback record fails, the hypervisor no longer
replaces the shellcode's bugcheck code and parameters with a zeroed
CMOS record. It only adds the `ZPX1` extension (CR3, CPU, stage, last exit).


