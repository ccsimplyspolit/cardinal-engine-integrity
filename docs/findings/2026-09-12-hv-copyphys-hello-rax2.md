# 2026-09-12 copy_phys map 20:59 hello still rax=2

Session. Canon:
aoe4-hv/docs/_bsod/090912-copyphys-hello-rax2.md.

Reboot 20:58 **did** map sys 20:44 (`copyphys_ok`, ping pong). Hello
still mailbox no-reply rax=2: `MmCopyMemory` from GIF=0 VMEXIT does not
copy the usermode mailbox PFN. Next loader uses per-CPU PFN MDL, then
reboot + one map. Do not nested-map this SVM. No Relic yet.
