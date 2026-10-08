# Rebuild-HvCycle was not the hitch wait (2026-09-13)

Mailbox 1–12 unchanged. **Do not map.** Event **41** still `21:06:01`.

## Point

The hitch 12s / WaitAlive / 50s poll fix is **`Map-AfterZppu.ps1`**,
not the rebuild wrapper. `Start-Process -Wait` on
`Rebuild-HvCycle.ps1` only waits for the child to exit.

This run **already finished in 24 s** (`21:12:03` → `21:12:27`):
Capture 11 s, `make clean` no-op, incremental `build_windows.bat` 4 s,
Verify 6 s, `zpp_aoe4` 2 s. ELF SHA256 still `E97A9C6E…EF4314` (same
as 8g ELF). Loader sys **`17E25811…EEFFE752`** 1094656 mtime 21:12:19.

What *looked* like 10 min: stacking Capture + `make clean` + full NDK
ELF + Verify + `zpp_aoe4` on one `-Wait`, plus a second outer
`Start-Process -Wait`, plus makefile `find` of VS/WDK when
`environment.config` is missing. Not `KeDelay`.

## Change

`Rebuild-HvCycle.ps1` is now incremental `build_windows.bat` only.
No Capture (HostPrep already ran this boot). No `make clean`. No
`zpp_aoe4`. No Verify in the wait path.

## Not this

- Not a new `kdu`. Gate **21** (cookie `load_ok_pending_alive` 8g).
- Do not remap `7B5C8989`. Disk `17E25811` is hitch-no-delay loader
  + same 8g ELF; never mapped this boot.
