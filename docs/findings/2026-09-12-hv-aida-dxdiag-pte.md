# 2026-09-12 AIDA64 + DxDiag: HV PTE plant failed (large pages)

Session. Canon:
aoe4-hv/docs/_bsod/090912-aida-dxdiag-pte-large.md.

GPU is **RTX 5080** (not 5090). AIDA: 1 GB pages yes, 5-level no,
Hypervisor ???. Map 21:29 `copyphys_pte_fail` because NonPaged windows
are 2 MiB large. Next sys: reserved 4K one-MDL `'ppzD'`, `mapwin_va=0`,
PTE poke at VMEXIT. Reboot + one map. Do not nested-map live SVM.
