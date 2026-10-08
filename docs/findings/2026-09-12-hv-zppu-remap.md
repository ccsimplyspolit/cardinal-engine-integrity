# 2026-09-12 ZPPU cannot replace reboot remap

Session note. Canon:
aoe4-hv/docs/_bsod/090912-zppu-not-this-boot.md.

Unload SVM on all 32 CPUs would clear `EFER.SVME` so a later KDU map
would not hit `svme_already`. The leave path exists (`leave_svm` / `ZPPU`).
It is **not** proven, **not** a driver unload, and **must not run** on the
17:50 image: `guest_cpl()` stuck at 0 makes usermode ZPPU `leave_svm` on
user CR3 (ELF not mapped). Pass 18 leftover SVME hung without a dump.

Do not `zpp_ctl.py unload` / `zpp_unload.ps1` as the product remap
(32-CPU leave unproven). 20:14 ELF has CS.RPL; reboot + copy_phys map
20:44 is the chosen path. See [2026-09-12-hv-reboot-copyphys.md](2026-09-12-hv-reboot-copyphys.md).
