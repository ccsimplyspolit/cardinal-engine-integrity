# HV usermode mailbox agent (ZPPX)

Date: 2026-09-11. Tree: `aoe4-hv`. Not overlay. No Relic plant.

## What

Split is now code, not just AOE4.md: **agent knows the game, ELF does not**.

- Leaf `ZPPX` (`0x5A505058`): RAX=leaf, RBX=key, RCX=4K mailbox VA
- Payload: ChaCha20-Poly1305 (`mailbox.h` + `chacha20_poly1305.h`)
- HV decrypts, `seq++`, walks ImageFileName like ZPPQ, then
  `stealth_arm` / `hide_guest_memory` with **blob CR3**
- EXE: `aoe4-hv/tools/zpp_aoe4/` -> `out/debug/x86_64/zpp_aoe4.exe`
- `sites.json` empty on purpose. No Watcher / 7AB0 in the repo.
- No OpenProcess on Relic `.text`. Image base = PEB `+0x10` after query.
- Overlay / DllInjector unchanged. No CPUID intercept. Not mapped this boot.

## Files

- `hypervisor/include/zpp/hypervisor/mailbox.h`
- `hypervisor/include/zpp/hypervisor/chacha20_poly1305.h`
- `hypervisor/src/hypervisor/mailbox.cpp`
- `tools/zpp_aoe4/zpp_aoe4.cpp`
- `tools/build_zpp_aoe4.bat`
- ADR-005 `aoe4-hv/docs/decisions/005-usermode-mailbox-agent.md`

## Not done this turn

- Not mapped (`launch_authorized=false`). Do not Relic-first.
- This boot (Pass 25): `zpp_aoe4 ping` = PONG (plaintext PING already live).
  `zpp_aoe4 hello` = `#UD` / exit 2 (ZPPX is in the new ELF, not this map).
- Overlay does not yet fill `sites.json`.
- `zpp_ctl.py` still plaintext lab; ZPPX is the encrypted path.

## P0/P1/P2 (2026-09-11, same boot, no remap)

- Poly1305 `finish()` donna-32 (sign of `g4 - 2^26`) and `block()` d3 = `h4*s4` (was `s2`). RFC 8439 section 2.8.2 in `selftest` + `tests/aead_rfc.cpp` + `Verify-AmdPort.ps1`.
- CR3 mask `0x000ffffffffff000` in AAD, KDF, `mailbox_owner_cr3`. Hello_ack DTB is masked.
- CLI: `mbox-ping`, `read`, `stealth --disarm`, `unhide` / `--all`, `clear` alias, `query --va`, `--wait`, leftover `clear --cr3` without live Relic.
- Harden: RtlGenRandom nonce, `write_guest_virtual` fail -> `bad_buffer`, zero `hello_key`, stub `PAGE_EXECUTE_READ`.
- Pass 25 mapped ELF still has no ZPPX. `hello` remains `#UD` / exit 2 until reboot + launch word. Do not plant Relic RVA in `sites.json`.
