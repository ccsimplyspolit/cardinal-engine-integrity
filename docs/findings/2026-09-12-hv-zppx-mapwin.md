# 2026-09-12 HV ZPPX hello = bad_buffer, not #UD

Goal still `prove --sec 60` ? `hv_hold`. This is not a docs-instead-of-fix note.

## Live map 18:55 (sys 18:52, boot 18:28:40)

- PING ok (`pong cpu=0/7`, key `0x449f29164b805ba`).
- `zpp_aoe4 hello` **not** VEH `#UD`. HV returns `rax=2` (`bad_buffer`) and does **not** write the 4K mailbox (`nonce` unchanged). Agent used to treat `rax=2` as exit 2 / “ud”.
- Cause: bring-up `map_guest_physical` skipped OS PTE remap (dump 10625 / 0x1AA on ELF 2 MiB PDEs). User mailbox page has no `MmGetVirtualForPhysical` VA ? read fails.

## Fix (sys **19:23:33**, 1054720 B) — not mapped this boot

Loader plants 32×4K System-PTE windows (`MmAllocateMappingAddress` + `mapwin_va` / `mapwin_bytes` on handoff). Mailbox GPA copies remap **those** windows only. Do not remap ELF chunks. Do not `ZPPU`. Live SVM cannot take a second map.

Next: planned reboot, then `docs/Start-ZppLoader.ps1`, ping, `hello` / `query --name explorer.exe` status=0, Steam `-dev -nodbg -notrap`, `hold --apply`, `x64dbg.exe` open no attach, `prove --sec 60`.
