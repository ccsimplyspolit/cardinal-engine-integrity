# Hasher HashRec NPT emulate (2026-09-13)

Mailbox ops 1–12 unchanged (`eax=0xFFFFFFFE` is stealth_arm aux, like nop5).
One hypothesis. **Not mapped** this boot (Cycle 6 ping `pong`; no nested-map).

## Point

User: hook hasher so other apps (CE / x64dbg / overlay RPM/WPM) can touch
Relic `.text` and hasher does not JUMPOUT.

`--eax 1` on `RA_Hasher` `0x3E57050` is still **forbidden**: RAX is 64-bit
wyhash, 45E8 does `cmp rax,[rdi+10h]` / `[rdi+18h]`. Overlay 14-byte plant
is still forbidden (prologue is itself hashed).

## What we arm

NPT site at hasher **entry** with `eax=0xFFFFFFFE`:

- Identity page NX + W=0 (same dual-nCR3 as Enqueue). Copy stays **original**
  (no `mov eax,imm;ret`).
- Execute NPF at RIP=`0x3E57050`: if guest `RDI` looks like HashRec for this
  `(rcx,rdx)` (`[+0x130]==rcx` → `[+0x10]`, dest=`[+0x20]+[+0xA0]` → `[+0x18]`),
  emulate `ret` with that stored hash. 45E8 memcpy/cloak still runs.
- Else `n<=0x80`: live wyhash of guest `[rcx,rdx]` (Walker 0x18 blob).
- Else miss: one original insn on the copy (slow fallback).

Foreign process access is GPA/identity: RPM sees identity PFN (original on
hooked pages, live on the rest). WPM from kernel can dirty identity; 45E8
still matches stored hashes so JUMPOUT stays off.

Do **not** NPT-protect dest leftover (`0x3E58000` / `0x3F04000` / `0x3F2D000`).
Do **not** stub Watcher. Do **not** `--eax 1` hasher.

## Hold list (16.3.11308.0)

| RVA | Name | eax |
|---|---|---|
| `0x3DD2550` | `RA_Enqueue` | 0 (ret stub) |
| `0x3E691F4` | `RA_KickCtor` | 0 |
| `0x3E672DC` | `RA_TimerQ_Push` | 0 |
| `0x3E57050` | `RA_Hasher` | `0xFFFFFFFE` HashRec emulate |

Page `0x3E57000` is **not** dest leftover. 45E8 calls at `0x3E55314` /
`0x3E555F3` live on `0x3E55000` (also not dest). We hook hasher entry, not
those CALLs (would NX the whole 45E8 4K → NPF storm).

## Live this boot

Cycle 6 still mapped ping `pong`. Relic **36888** hold was `status=8` (CR3 walk). Do not retry that PID. Do not nested-map.

Cycle 7 ELF/sys rebuilt **18:41:30** (not mapped):

| Artifact | Size | SHA256 |
|---|---|---|
| `zpp_hypervisor` | 1036864 | `9698240BBC4AB725F8FC7EC81E8C13302E4BC95C546D7538786969A2DB505914` |
| `zpp_loader.sys` | 1086976 | `A99C6C15CE44F4A6D70D28D2F0F9F8DAE302F43C733E54C54F1F79018FD31C09` |

`insn_boundary` + `Verify-AmdPort` PASS. Next = user **запускай** after ZPPU leave + this image, then **new** Relic `-dev -nodbg -notrap`, then `hold --apply`.

## Files

- `hypervisor/include/zpp/x64/stealth_hashrec.h`
- `hypervisor/src/hypervisor/npt_stealth.cpp` (`stealth_hashrec_emulate`)
- `mailbox.h` / `hypervisor.h` sentinel `0xFFFFFFFE`
- `zpp_at.py` / `aoe4_16.3.11308.json` / `zpp_aoe4.cpp --hashrec`
- ADR-006 preferred path
