# 2026-09-12 reboot + copy_phys map (not ZPPU)

Session. Canon:
aoe4-hv/docs/_bsod/090912-reboot-copyphys.md.

User asked not to refuse ZPPU/reboot/map. Ranked paths on live SVM
20:14 (ping pong, hello rax=2, dump still 15843):

- Nested map: hang / `svme_already`
- Usermode ZPPU: CS.RPL fix is in this ELF, but 32-CPU leave + second
  KDU is unproven (Pass 18 leftover SVME)
- **Reboot + one map of sys 20:44 copy_phys:** chosen. Task
  `aoe4-hv-map-copyphys-2044` ? `Map-Loader2044.ps1`

After desktop: hitch `efer=4d01`, `copyphys_ok` / `mapwin_skip`, ping,
hello / query explorer status=0, then Steam Vs AI, `hold --apply`,
x64dbg.exe open no Attach, `prove --sec 60` = `hv_hold`.
