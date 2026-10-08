# 2026-09-12 HV remap without reboot (product)

Session. Canon:
aoe4-hv/docs/_bsod/090912-remap-without-reboot.md.

User: map/unmap/remap without reboot. Reboot was a bring-up shortcut
(clear `EFER.SVME`), not the product. Live SVM 21:29 still up; reboot
aborted. Next work is proven 32/32 `ZPPU` leave, then one `-map`.
Do not nested-map. Do not auto-reboot.
