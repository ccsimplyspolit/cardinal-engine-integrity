# 2026-09-12 HV copy_phys — no System-PTE remap

Dump 15843 0xDA 0x107 is from the 20:06 mapwin plant, before the 20:14
one-MDL map. Live SVM still pings; hello rax=2. `copy_phys` reads are
MmCopyMemory only (no MmMapIoSpace fallback — MiShowBadMapper on PT
PFNs after 1803). Writes: MmMapIoSpace of mailbox/.text. Do not map
until reboot. Sys **20:44:05**. Details:
`aoe4-hv/docs/_bsod/090912-copyphys-no-mapwin.md`.
