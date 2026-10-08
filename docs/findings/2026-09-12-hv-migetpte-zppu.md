# 2026-09-12 live MiGetPteAddress + ZPPU wait-for-leave

Session. Canon:
aoe4-hv/docs/_bsod/090912-migetpte-zppu-leave.md.

ntoskrnl 10.0.26100.7171: `MiGetPteAddress` RVA `0x405850`. Loader calls the live function (pattern scan). Unload waits for ping #UD 32/32. Not reboot. Not nested-map.
