# 2026-09-07 — restore hide / RA tools / docs onto stable main

After `2bfac27` (six-commit revert) the user asked to pour back **only**:

- `internal/WindowWatch` + `internal/shared/ra_retitle.h` (WW include)
- `tools/x64dbg-hidden`, `tools/scyllahide`, `tools/rbhost/Start-Dbg.ps1`
- `tools/ra_emu.py` and dump/probe/CLI siblings
- `patchAT/` + ADR-002
- findings 2026-09-06/07 + RELIC_* + ADR-003/004 + UPDATE_GUIDE ritual

**Not** restored: overlay `InternalInjector` RA/AI (`dev_bypass`, `ra_heartbeat`, `ra_text_cloak`, `mp_bypass`/`ra_hide` bloat, AI store). Network Monitor stays `e66ae97`.

Second pour: DllInjector + Standalone + `inject_boot`, sdk offset header, adversarial tests, `fetch_build_orders` / dump_sdk / sga_mmap, AI docs. Tests that call unrestored II symbols (`AiEcoBlendBuildOrder`, …) will not pass until that DLL code is back.

Source tree: `cb70dba`.
