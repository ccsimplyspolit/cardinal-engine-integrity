# 2026-09-06 — Relic disk unpacker (layers, not a magic XOR)

> **Закрыто 2026-09-06 23:34.** Это дневник охоты, не backlog.
> Канон: [RELIC_UNPACK_ALGORITHM.md](../RELIC_UNPACK_ALGORITHM.md).
> AEAD no-game **есть** (`unpack-disk` / `rediscover`).
> Секция «Next» ниже (suspend 7AB0 / overlay table) — сделана в том же дне.
> Пайплайн: [2026-09-06-unpack-pipeline.md](2026-09-06-unpack-pipeline.md).

User: fully strip the cipher, write an unpacker, walk the crypt
structure step by step, start implementation.

Build **16.3.11308.0**. Tool:
`K:\aoe4_dlc\aoe4\gamesource\tools\unpacker\`
(`python -m unpacker all` from `tools\`). **RVAs only.** No Steam
overwrite. Encrypted `.text` is not disassembled.

## What “fully unpack” actually is

Three different products. Do not mix them.

| Product | Meaning | We have it? |
|---|---|---|
| **Oracle PE** | Disk headers + live `.text` | **Yes** — `RelicCardinal.unpacked_analysis.exe` |
| **Static unpacker** | Steam exe in, plaintext out, game never runs | **Yes** — `python -m unpacker unpack-disk` (99.328% vs 52968 T+20s; leftover = post-unpack RA) |
| **RA sim** | 45E8 dest-XOR leftover decrypt after compact | **Yes** — `python -m unpacker ra-sim` (Hasher 174/174; T+20s gold dest = unlock PRNG, not cloak) |
| **Runtime lift** | pe-sieve / `memory.bin` after Arxan finished | **Yes** — this *is* the decrypt |

C⊕P already killed a period-N XOR ([vmp-deob-vs-relic](2026-09-06-vmp-deob-vs-relic.md)).
dearxan is FromSoft GuardIT, wrong shape
([game-folder-unpack](2026-09-06-game-folder-unpack.md)).

## Step-by-step (required)

1. **Atlas** — mark every 4 KiB `.text` page C vs P.  
   Result: **17640 / 22236** cipher (79.33%), **803** plaintext islands.
   Largest islands: `0x516B000–0x56DD000` (1394 pp, includes EP) and
   `0xD6000–0x3CF000` (761 pp). Bitmap: `dump/crypt/text-page-plain.bin`.
2. **Headers are plaintext** — parse TLS / IAT / overlay **without**
   treating cipher `.text` as code.
3. **Find the first writer** of cipher pages. Candidates, in order:
   Steam/loader (before Relic EP) → TLS → `_scrt_initialize_crt` →
   VEH-on-fault → CRT$XCU. The stub **must** start in a plaintext
   island or in another module.
4. **Pre-TLS dump** — `CREATE_SUSPENDED` Relic, RPM `.text` at
   `B+0x3DD7AB0` (28-byte unique AOB).  
   - Already plaintext → Steam/loader unpacked; Relic has no stub.  
   - Still garbage → stub is inside Relic; emulate that function.
5. **Recover the transform** (AES / custom / LZ4+map) **or** Unicorn
   the stub against disk pages; verify every cipher page vs 60644 live.
6. **Overlay** `0x8076800` / 10 049 828 B — leftover after last section,
   not in `SizeOfImage`. Entropy ~8. Four ASCII `lz4` hits, **zero**
   LZ4 frame magics. Not a second PE.

## This turn (implementation + negatives)

| Hunt | Result |
|---|---|
| TLS disk vs live | **Same one callback** `0x4FB0B6C` = MSVC `TlsCallback_0` (only `DLL_THREAD_ATTACH`). Page is plaintext. No extra Arxan TLS that deleted itself |
| EP | Vanilla `start` → `_security_init_cookie` → `__scrt_common_main_seh` |
| IAT `VirtualProtect` (13 funcs) | Relic **heap** (`HPMVGLMV` tag) at `0x3CD9910`. Not the disk crypt. Pages mixed/cipher |
| IAT `AddVectoredExceptionHandler` | **One** xref: `0x3CD86C0` → BugSplat `MiniDmpSender`. Not Arxan |
| `_initterm` 12607 slots | 12583 on plaintext pages, 23 on cipher-grain pages (incl. `RA_Integrity_Dispatcher_Once` `0x3DDF150`). Bulk `.text` is already plain **before** C++ inits |
| Overlay | No `04 22 4D 18`. `lz4` at `+0x2E` is 3 entropy bytes (`6c 7a 34`) |

So: Relic’s own TLS / CRT$XCU / IAT protect / VEH are **not** the
disk unpacker. The writer is earlier (Steam / mapped overlay / a
plaintext-island stub we have not named) or uses a syscall copy of
`NtProtectVirtualMemory` with no IAT xref.

## CLI

```
python -m unpacker atlas|hunt|overlay|crt|oracle|verify|all
```

Reports: `aoe4\gamesource\meta\unpacker-*.json`.

## Next (still no plant)

1. Suspended Relic RPM at 7AB0 (28-byte AOB) — answers Steam vs Relic.
2. If Relic: walk plaintext island `0xD6000–0x3CF000` for a loop that
   `VirtualProtect`s / writes other `.text` RVAs (syscall, not IAT).
3. Overlay chunk table (not brand strings).
4. Do **not** run dearxan / VMP-Deob. Do **not** stub 7AB0 because
   we can splice a PE.

**Update 23:34:** items 1–3 landed the same day (suspend + pack-catch +
footer/AEAD/`hunt_directory`). Do not resume this list as open work.

## Continue (suspend + poll)

`python -m unpacker suspend` then `resume-poll`. Relic **terminated**
(never left running). PID 3380 / 42268. Base `0x7FF6E6700000`.

| t after Resume | 7AB0 | modules |
|---|---|---|
| CREATE_SUSPENDED | **disk cipher** (`427a92f1…`) | PEB mapped, no Ldr |
| 0 ms | still cipher | 0 enumerated |
| ~6–11 ms | still cipher | `steam_api64.dll` present |
| ~12–25 ms | still cipher | module count stable at **59** |
| **~109–130 ms** | **live 28-byte AOB** | still 59; Fwd flipped in the same poll |

EP stayed CRT on disk and live (control). Page `0x1000` first 16 B is a
mixed/plain grain (not a counterexample).

**Verdict:** Windows mapped Steam `.text` as-is. Decrypt is **in-process
after Resume**, bulk (~72 MiB of cipher pages in ~100 ms), **not**
`steam_api64` DllMain (that DLL is already loaded ~100 ms earlier).
No `steamclient64` / overlay in the 59-module set.

`GetThreadContext` at first plaintext poll: RIP in
`RelicCardinal` **RVA `0x3E8710B`** =
`XXH3_hashLong_64b` `0x3E86FB0` (page **plain on disk**, constants
`9E3779B185EBCA87` / `C2B2AE3D27D4EB4F`). Caller
`XXH3_64bits` `0x3E87F00`. Parent `0x3E76988` (0x172e) is an SRW-locked
walker that **hashes**, not a `VirtualProtect` writer.

So the poll is ~0–5 ms **after** the writer; we landed on the
post-decrypt integrity hash. Island `0xD6000–0x3CF000` has **0**
`mov r10,rcx; mov eax,imm; syscall` gates (8 lone `0F 05` look like
immediates).

Reports: `meta/unpacker-suspend.json`, `unpacker-resume-poll.json`,
`unpacker-island-syscalls.json`.

Next: hook/poll `VirtualProtect` **target** = Relic `.text`, or break
the first write to `B+0x3DD7AB0`, to name the writer (not XXH3). Still
no plant.

## Continue (write-catcher)

Relic was **not** running; `python -m unpacker write-catch` created
PID **51852** (and 46712), base `0x7FF68CB90000`, then **Terminate**.
Busy-poll 8 B at 7AB0, no sleep, freeze **all** threads on first
mismatch vs Steam disk.

| | 46712 | 51852 |
|---|---|---|
| firstWrite | 0.143 s / 59373 polls | 0.132 s / 58026 polls |
| 7AB0 / Fwd / Enq | already full live AOB | same |
| protect 7AB0 | `PAGE_EXECUTE_READ` (0x20), alloc `WRITECOPY` (0x80), region `0x7c000` from `0x3DD7000` | same |
| primary RIP | **`imagehlp+0x21DC`** rcx=4 rdx=`0x1DF140` | **same RIP + args** |
| Relic RIP | none | none |

`imagehlp.dll` is **absent** from the 59-module list at the flip and
**present** in `modulesAfterFreeze`. Stack under primary:
`imagehlp+0x255B` → `KERNELBASE!MapViewOfFile+0xF0` (`0x3F8C0+0xF0`).
RIP bytes are a stride-9 table walk (cert/PE helper between
`ImageGetCertificateData` `0x13F0` and `ImageDirectoryEntryToData`
`0x2B40`). Relic PE security directory is **empty** (`0,0`) — rcx=4
is not `IMAGE_DIRECTORY_ENTRY_SECURITY` of Relic itself.

Two workers sit in **pagefile-backed** views (`RIP` not in any module;
gadget `xchg r15,[rsp]; ret`). Relic IAT `MapViewOfFile` /
`CreateFileMappingA` have **one** code xref: RVA **`0x3B7D1C0`**
(plaintext island `0xD6000–0x3CF000`) =
`Essence_PlatformMemory_MapView` (`PlatformMemory.cpp` —
`CreateFileMappingA(-1, PAGE_READWRITE, aligned_size)` +
`MapViewOfFile(..., 0xF001F)`). Engine allocator, **not** the disk
stub. Sibling `0x3B7D100` is a stub `MapPages Not Implemented`.

7AB0 lives in a **17-page** cipher run `0x3DD7000–0x3DE8000`; page
*start* `0x3DD7000` is already plain on disk (mixed grain). Bulk write
still finishes between two ~2.4 µs RPM samples.

Report: `meta/unpacker-write-catcher.json`. Still no plant. Writer
unnamed — next is write-watch / `NtProtectVirtualMemory` on
`B+0x3DD7AB0`, not another 5 ms RIP lottery.

## Continue (Dr0 writer + rolling XOR)

`DEBUG_EVENT.u` was 4 bytes early on the first hwbp pass (missed
`SINGLE_STEP`; Relic still decrypted then exited). Padded union, reran.

PID **39712**, base `0x7FF6043F0000`, watch `B+0x3DD7AB0`, Dr7 write-1.
Hit **t=0.205 s**, Dr6 bit0, RIP **`0x3E45873`** =
`RA_Integrity_Dispatcher+0x183F` (`add rsi, 8` after the store).
Store is `xor [rsi], rax` at **`0x3E45870`**. Page `0x3E45000` is
**plaintext on disk**. 7AB0 page was `PAGE_EXECUTE_READWRITE` (0x40),
region `0x1000`. `rcx=0x20A` qwords left + `rdx=5` tail = **0x1055**
(7AB0 size). Called from CRT `RA_Integrity_Dispatcher_Once` `0x3DDF150`.

Loop (same `r8` on 7AB0 and Enqueue):

```
xor  [rsi], rax
add  rsi, 8
imul rax, r8          ; r8 = 0xDA942043DA942043  (image immediate)
sub  rcx, 1
jnz
; tail: xor [rsi], al / inc rsi / shr rax, 8
```

`0x5A942043DA942043` was a **false read**: it differs only in bit 63, so
the keystream collides when `k0` is even (7AB0 / Enqueue). Dr0 `r8` is
`0xDA94…`.

## Continue (range table + k0 + overlay pack)

`k0 = (len XOR g_RA_DestXorSeed) * r8`. Seed RVA `0x7AF7688`, live
60644 = `0xFDFDFBCD1B3F5D7B` (type-2 pack section). Disk `.data` there
is **not** the seed (`0x144DDA00144D80`).

Record (compact, type filter `edx=3`):

| Off | Field |
|-----|--------|
| `+0x00` | `self_size` (walk: `rdi += [r14]`) |
| `+0x08` | `len` |
| `+0x10` | RVA |
| `+0x18` / `+0x20` | cksum / `~cksum` |
| `+0x38` | `0x15` memcpy-from-`+0x39` then XOR; `0x16` XOR in-place |

Fat records (`edx=1`): type at `+0x140`.

7AB0: `n=0x1055`, k0 formula **match**. Enqueue span is **2327** B
(not 64); formula matches that length.

`python -m unpacker ranges` / `apply-formula` vs 60644 live `.text`
(91 078 656 B):

| | bytes |
|---|---|
| already plain on disk | 36 050 433 |
| type `0x16` formula-ok apply | **+51 111 751** (98 850 spans) |
| match after apply | **87 162 184 (95.7%)** |
| still differ | **3 916 472** (≈ type `0x15`) |

Overlay **is** the pack: footer `D ^ ~(B*C) == A` at end-32
(`RA_PackFooter_Parse` `0x3F913AC`), `tableSize=0x995884`,
`tableOff=0x8076800`. Ingest `0x3F7D07C` is **not** memcpy: 64-byte
header + AEAD (output = size−88). Constant `SigEd25519 no Ed` next
to the stream (libsodium-family). Needles for `0x3DD7AB0` are **heap**,
not in `memory.bin`.

## Continue (live pack dump)

User Relic **24044** left running. `OpenProcess` unelevated = 5;
seed at `B+0x7AF7688` already set (table freed after Dispatcher).

Child `DEBUG_PROCESS` PID **3160** (Steam exe, then Terminate). Dr0
**write** on seed, hit **t=0.097 s**, RIP `0x3E45334`,
`rax=0xFDFDFBCD1B3F5D7B`. Heap region `10 051 584` B →
`dump/crypt/pack-decoded.bin`. Compact section at **2432571**,
size **7 612 623**, **105 383** records (3175×`0x15` + 102208×`0x16`).
7AB0 rec `self=57` type `0x16`.

`python -m unpacker apply-pack` (record order, disk `.text` in):

| | bytes |
|---|---|
| plain before | 36 050 433 |
| after compact apply | **90 427 184 (99.285%)** |
| still differ | **651 472** |

Leftover is ~159 pages — same order as post-unpack RA self-mod
(26392 vs 60644: 214 pages). `edx=1` fat walk from the first
directory guess is not a record stream (false `+0x140` hits).

CLI: `pack-heap` (live RPM) / `pack-catch` (child Dr0) / `apply-pack`.
Do **not** plant Dispatcher. Overlay AEAD **closed** later the same day
(`unpack-disk` / `pack-decoded-static.bin` == heap`[64:]`). This
paragraph is historical: at pack-catch time only the heap dump existed.

## Continue (leftover 651 KiB is post-unpack, not missing cipher)

`python -m unpacker leftover` / `leftover-deep` / `leftover-aslr` /
`apply-fat` vs 60644 live `.text` and 26392 pe-sieve image
(`00007ff7007b0000.RelicCardinal.exe.bin`, base `0x7FF7007B0000`).

| Hypothesis | Result |
|---|---|
| PE `DIR64` relocs (disk `0x140000000` → live `0x7FF7A5500000`) | **0** reloc sites in `.text`. 0 qword delta-hits |
| Compact walk truncated (`COMPACT_SIZE`) | EOF walk = same **105 383** recs; 0 new |
| Leftover RVA sitting in pack as qword | **0** hits |
| Same `k0=(len^seed)*r8` on leftover *runs* | **101** B (noise) |
| Fat `edx=1` as compact `0x15`/`0x16` | 174 walked recs are types **1/6/7**; 0 applied; score unchanged |
| Missing layer (both lives same plaintext) | 26392 vs 60644 leftover match **3.67%** RA / **0.35%** outside |

Leftover after compact apply:

| | bytes |
|---|---|
| still differ | **651 472 (0.715%)** |
| in RA band `0x3DD0000–0x3F90000` | **604 159 (92.7%)** |
| outside RA (largest `0x6B8DF3` n=1546) | **47 313** |
| leftover pages | **221** (same order as 26392 vs 60644 self-mod ~214) |
| covered by compact but wrong | **0** |

`recover_spans` on leftover “recovers” ~98% only as ~8-byte fragments
(any differ qword is a trivial XOR). That is **not** the rolling cipher.

**Verdict:** stage **5/6** (pack XOR in record order) is done. The 0.715%
is post-unpack RA mutation / session-divergent code, not a third disk
transform. Oracle / runtime lift already include it; a disk-only PE will
**not** match a late 60644 `.text` on those 221 pages.

### Pack directory (decoded heap dump)

Table starts at **dump+64** (16-byte heap hdr + 48). `ptr = table+776+off`.
Matches `RA_PackSection_Get` (`*a3 = *(v6+24*type+8)+v6+776`).

| type (`edx`) | dump ptr | size | role |
|---|---|---|---|
| 0 | 840 | 1 591 461 | not a compact/fat record stream (0 recs) |
| 1 | 1 592 301 | 840 262 | fat; type byte `+0x140`; `0x15` memcpy+`+0x141` then XOR; `0x16` in-place XOR; else `0x5E68` (alloc / not this leftover) |
| 2 | 2 432 563 | 8 | seed → `g_RA_DestXorSeed` |
| 3 | 2 432 571 | 7 612 623 | compact XOR recs |
| 5–16 | after compact | 48–3088 | trailers; not `.text` XOR |

Dispatcher `PackSection_Get` immediates: **2** (seed), **4** (wchar
`0x200` words; empty in this directory), **3** (compact), **1** (fat).

### Overlay AEAD (still stage 6)

`RA_PackIngest` `0x3F7D07C` (renamed in 60644 IDB `a1220dbc`, saved).
Need `a3>=0x59`. Copies 64-byte header into ctx, then
`RA_PackAead_Open` `0x3F7B4D4`: body `a3-64`, require `>0x18`, output
`a3-24` → total plaintext **size−88**. Trailer last-8 copied as tag;
`0x3FB30B0` rejects `len<0x10`, calls `0x3FB3000`. Key material from
container `+1456` (`sub_7FF7A9479AEC`). Near-stream `SigEd25519 no Ed`.
ChaCha `"expand 32-byte k"` in-image is **not** proven to be this AEAD.

Reports: `meta/unpacker-leftover.json`, `unpacker-leftover-deep.json`,
`unpacker-leftover-aslr.json`, `unpacker-apply-fat.json`.

Next: disk-only pack = implement overlay AEAD (key at `+1456` / libsodium
family). Do **not** plant Dispatcher. Do not chase leftover 651 KiB as
missing XOR records.

## Continue (Stage 6 AEAD identified, disk open not closed)

`+1456` is **not** an embedded key. `RA_PackContainer` `9D18` heap-allocs
an empty 784-byte crypto ctx; PackIngest copies the **64-byte overlay
header** into it.

Confirmed in 60644 IDB (`a1220dbc`, saved):

| RVA | Name | Evidence |
|---|---|---|
| `0x3FC9210` | `crypto_core_hsalsa20` | 10 double-rounds; sigma `expand 32-byte k`; in=16 zero at `0x7AF18970` |
| `0x3FBBF80` | `crypto_scalarmult_curve25519` | clamp `x[0]&=0xF8` / `x[31]&=0x3F\|0x40`; `121666`; 254-bit ladder |
| `0x3FB5050` | `crypto_box_beforenm` | `scalarmult(tmp, header[0:32], header[32:64])` then HSalsa20(out, zeros, tmp) |
| `0x3FB52E0` | `crypto_secretbox_open` | HSalsa20(sub, ctx+688, derived); stream at `+16`; Poly1305 verify |
| `0x3F7B4D4` | `RA_PackAead_Open` | body `size-64`; skip 16 (mac); copy last 8 → ctx+688; out=`size-88` |

HSalsa20 **self-test vs libsodium core2 = pass**.

`python -m unpacker overlay-aead`: footer tableOff=0, tableSize=`10049668`,
plainExpect=`10049580`. Header (64 B) + mac16 + ct + extra8
(`93974ef745fa390c`). Seed-oracle (`0xFDFDFBCD1B3F5D7B` at plain
`2432499` / dump `2432563`) — **0 hits** across box key order × nonce
guesses (zero24, extra8‖zeros, zeros16‖extra8, header slices).

So: cipher family is **X25519-XSalsa20-Poly1305**, but the disk open is
not matching `pack-decoded.bin` yet. Remaining deltas: provider
`salsa20` at `4BC0` (not the in-image HSalsa), their point decode
`0x3FC9510` vs `cryptography` X25519, or nonce not `extra8‖0`.

Do **not** plant Dispatcher. Next: dump `52E0` rcx/rdx/r8/r9/stack
(derived key + 24-byte nonce) from a `pack-catch` child, then replay.

## Continue (Stage 6 closed — disk-only pack AEAD)

Child `aead-catch` (DEBUG_PROCESS, Dr0-exec `0x3FB52E0`, skip `r9<1e6`,
EFLAGS.RF). PID **53436**, base `0x7FF6196D0000`. First hits are tiny
boxes (`r9=3,6,0x1e,5`). Overlay hit at t=0.041s:

| Field | Value |
|---|---|
| r9 / mlen | `0x99582C` = **10049580** = tableSize−88 |
| nonce24 | `93974ef745fa390c` ‖ 16×`00` (extra8‖0) |
| header | Steam overlay `81fab5f2…` |
| derived key | `532b4c79a806aabf5822b165037ff0c56cfff1f87b5f60ee1d106c19a1302203` |

Replay failed until keystream used **secretbox_open_detached skip32**
(first 32 bytes of Salsa20 counter-0 = Poly1305 key; payload XOR starts
at stream+32; rest `xor_ic` counter=1). Old `seek_xor` treated ct[0] as
counter 1 (64-byte skip) — seed oracle looked random.

Disk recipe (no game):

```
sk = overlay[0:32]          # scalar (not the usual pk-first naming)
pk = overlay[32:64]
k  = HSalsa20(zeros16, X25519(sk, pk))   # == live key; box_sk_pk
n  = extra8 || zeros16                   # extra8 = body[-8]
pt = XSalsa20_xor(k, n, body[16:-8], skip32=True)
```

`cryptography` X25519 matches their ladder for this header.
`box_sk_pk == live key`. `pack-decoded-static.bin` (10049580 B) **byte
equals** heap dump `pack-decoded.bin[64:]`.

| CLI | Result |
|---|---|
| `overlay-aead` | 4096/4096 vs dump+64; seed at static `2432499` |
| `apply-pack` | 105383 recs; **99.285%**; leftover 651472 B |
| `unpack-disk` | `K:\aoe4_dlc\analysis\game_16.3.11308\RelicCardinal.unpacked_static.exe` (144752932 B) |

Provider salsa (60644 IDB saved): `crypto_stream_salsa20` `0x3FC2900`,
`xor_ic` `0x3FC2990`, SIMD keysetup `0x3FC4710` / iv `0x3FC46E0`.
Keystream matches NaCl/libsodium once skip32 is applied.

Do **not** plant Dispatcher. Do not chase leftover 651 KiB as missing
XOR — it is post-unpack RA (221 pages; 26392 vs 60644 diverge).

## Audit (2026-09-06 22:21)

`python -m unpacker audit` — **55 pass / 0 fail / 0 skip**.
Report: `aoe4/gamesource/meta/unpacker-audit.json`.

Re-derived AEAD from Steam overlay (no catcher). Fresh plaintext ==
`pack-decoded-static.bin` == heap dump `[64:]`. Live catch key/nonce
match `box_sk_pk` + `extra8‖0`. skip32 off → 17/4096 vs dump (noise).
Compact 105383 (3175×`0x15`, 102208×`0x16`), EOF exact, type2/type3
directory slots, 7AB0 `n=0x1055` `k0=0x4A892571D5CEF30A` and **span
matches 60644 after XOR**. apply 90427184 / leftover 651472 / 99.285% /
221 pages / RA 604159 B (92.74%). DIR64 in `.text` = 0. Leftover RVAs
not in pack. 26392 vs 60644 leftover: RA 3.67%, outside 0.35%.
`unpacked_static.exe` `.text` == applied buffer; headers/sections/size
== Steam disk; overlay still ciphertext. Oracle PE `.text` == 60644
live (91 078 656). FileVersion **16.3.11308.0**. Disk `0x7AF7688` ≠
seed; 60644 memory there = seed.

Not in this pass (optional): T+unpack child dump, fat/type0 semantics,
Poly1305 MAC, running the static PE as a game.

## Live full dump PID 24044 (2026-09-06 22:23)

User Relic left **running**. Elevated `dump_sdk_pack.py 24044`.
Folder: `K:\aoe4_dlc\dumps\RelicCardinal_24044_20260906_222353_sdkpack\`

| Artifact | Value |
|---|---|
| Relic base | `0x7FF6196D0000` (do not mix with 60644 `0x7FF7A5500000`) |
| SizeOfImage | `0x8C3D000` (147 050 496) |
| Full minidump | `RelicCardinal_24044_full.dmp` **7 575 482 427** B, `MiniDumpWriteDump` ok |
| Modules | 150/150 PE images; `injector_in_process=false` |
| Seed `0x7AF7688` | `0xFDFDFBCD1B3F5D7B` (same as pack type2) |
| Native probes | ScarDoString / SimWorld* / GetGameTicks **ok** |

`.text` vs static unpack: **90 453 924 / 99.314%**, leftover **624 732** B
(210 pages), RA band 604 276 B (**96.73%**). Closer to static than late
60644 (651 472 B) — two live sessions diverge from each other
(24044 vs 60644 leftover 631 398 B). Confirms leftover is post-unpack
RA, not missing XOR. Process 24044 was not killed.

## Full access pass (37560 + minidump scan)

User granted live attach/dump. PID **37560** (start 22:26) module dump
`dumps\RelicCardinal_37560_20260906_222703\00007ff6196d0000.RelicCardinal.exe.bin`.
Same ASLR base `0x7FF6196D0000`. Seed ok. Natives ok. Relic not killed.
Second 7 GB minidump **not** taken (24044 already has one; MiniDump froze
the previous session).

| Pair | same | leftover | pages | RA % |
|---|---|---|---|---|
| 37560 vs static | 90 454 720 / 99.315% | 623 936 | 210 | 96.72 |
| 24044 vs static | 90 453 924 / 99.314% | 624 732 | 210 | 96.73 |
| 37560 vs 24044 | 90 474 823 / 99.337% | 603 833 | 202 | 96.63 |

Leftover is already ~624 KiB at **T+1 min**. It is early RA self-mod, not
only a late-session drift.

`python -m unpacker dump-scan` on `RelicCardinal_24044_full.dmp` (7.58 GB,
7644 ranges): seed at `B+0x7AF7688` = live seed (**one** hit — pack type2
copy already freed). Pack plaintext head and overlay `81fab5f2` **absent**
from the dump (overlay is PE-file tail, not mapped; ingest heap freed).

## Why 24044 dump looked incomplete (then 37560 snapshot)

WindowWatch log 22:24:49–55 is the smoking gun, not a missing MiniDump stream.

`dump_sdk_pack.write_minidump` called `MiniDumpWriteDump` **on the live
process**. That **suspends every Relic thread** for the whole write
(~minutes). File close 22:24:51. Then:

| t | WW |
|---|---|
| 22:24:49–51 | `slots=0` uninit (threads frozen; dump finishing) |
| 22:24:52–54 | `slots=4 accum=1200` (resume; window finally allocated) |
| 22:24:55 | `RPM failed err=299` process dying |

So 24044 `RelicCardinal_24044_full.dmp` (7.58 GB, 7644 ranges) is a
**frozen-then-dying** snapshot. RA window was still `begin=end=0` inside
the file. Pack heap already freed. ERROR_PARTIAL_COPY (299) is WW losing
the dying PID, not “streams truncated”.

Fix: `AOE4HOOK/tools/dump_relic_snapshot.py` — `PssCaptureSnapshot`
(`PSS_CAPTURE_VA_CLONE`) then MiniDump the **clone**. Relic keeps
running. `dump_sdk_pack` now routes minidump through this.

New dump (PID **37560** still alive after):
`dumps\RelicCardinal_37560_20260906_222948_snapshot\RelicCardinal_37560_full.dmp`
**6 162 501 155** B, 5703 ranges, seed at `B+0x7AF7688` ok. RA window
still uninit in this session (menu) — that is game state, not a short
dump. Do **not** MiniDumpWriteDump the live Relic again.

## Snapshot dump `.text` vs static (2026-09-06 22:35)

`python -m unpacker dump-text` on
`RelicCardinal_37560_20260906_222948_snapshot\RelicCardinal_37560_full.dmp`
(6 162 501 155 B, 5703 ranges, 0 missing `.text` pages).

| Pair | same / pct | leftover | pages | RA % |
|---|---|---|---|---|
| snapshot vs static | 90 453 970 / **99.314%** | 624 686 | 210 | 96.73 |
| 37560 module PE vs static (T+~1 min) | 90 454 720 / 99.315% | 623 936 | 210 | 96.72 |
| snapshot vs same-PID module PE | 90 689 446 / 99.573% | 389 210 | 128 | **100.00** |

Dump vs earlier same-process module PE: **all** extra leftover is in RA
`0x3DD0000–0x3F90000`. That is post-unpack self-mod between ~T+1 min and
the 22:29 snapshot, not missing XOR records.

`raInDump`: begin=end=0, accum=0, flag=0, seed `0xFDFDFBCD1B3F5D7B` ok.
`dump-scan`: seed **one** hit at `B+0x7AF7688`; pack plaintext head and
overlay `81fab5f2` absent (same as 24044).

First leftover RVAs vs static start at `0x679533` (outside RA; same as
module PE). Largest non-RA leftover in the 60644 leftover report is
`0x6B8DF3` n=1546 (ChaCha island neighbourhood, not pack AEAD).

Module PE vs static leftover by 1 MiB RVA (total 623 936):

| bin | bytes | RA? |
|---|---|---|
| `0x600000` | 7 873 | no (incl. `0x679533` / `0x6B8DF3`) |
| `0x700000` | 7 857 | no |
| `0xA00000` | 4 624 | no |
| `0x3D00000` | 2 300 | mixed (RA starts `0x3DD0000`) |
| `0x3E00000` | 404 535 | yes |
| `0x3F00000` | 196 747 | yes |

`--wait-ra` on `dump_relic_snapshot.py` polls `slots>0` then VA-clone
dumps. PID **37560** still menu (`slots=0`) at 22:35 — need a match for
a live window heap in the file. Do **not** MiniDump the live process.

## Online match capture PID 37560 (2026-09-06 22:40)

User entered an **online** match. `--wait-ra 1800` fired at `slots=1`.
Relic **survived** the VA-clone dump, then died ~2 min later during a
second capture wave (`EnumProcessModules` **299**). Process gone after.

| Artifact | Path / value |
|---|---|
| Full dump | `dumps\RelicCardinal_37560_20260906_224012_snapshot\RelicCardinal_37560_full.dmp` **9 355 070 720** B, 8848 ranges, clonePid 51952 |
| Relic after dump | **alive** (`relicAliveAfter=true`) |
| RA live RPM | `dumps\RelicCardinal_37560_20260906_224215_ra\` (`ra_window.bin` 408, `ra_data.bin` 19072) |
| Module PE | `dumps\RelicCardinal_37560_20260906_224215\00007ff6196d0000.RelicCardinal.exe.bin` natives OK |
| Base | `0x7FF6196D0000` (same ASLR as menu dumps) |
| Seed | `0xFDFDFBCD1B3F5D7B` one hit |
| Pack / overlay head | **absent** (ingest heap still freed) |

RA window in dump **==** live RPM heap (408 B):

| Field | Value |
|---|---|
| begin/end/cap | `0x239DCBB3F80` / `+0x198` / same (cap==end) |
| slots / accum / flag | **1 / 0 / 0** |
| lock / jumpout | 0 / 0 |
| dispatcherOnce | `01` |
| F448 image | base=`B` size=`0x8C3D000` (whitelist matches live image) |
| hashmap | `0x239D12F0810` (128 B pulled from dump) |
| slot+0 kind | **3** |
| slot+8 tag | **`0x40230001`** (overlay: OP20 leftover, Relic canned, not DoString) |
| slot+10 | `B+0x56F9C88` |

Overlay log 22:39:44 classified the same slot (`kind=3` / `40230001` /
`+10=0x56F9C88`). `WindowClear` **suppressed** (`POST n=1`). This is
**not** Watcher `0x20220002` and **not** IAT kick `08050001`.

`.text` vs static:

| Pair | leftover | pct | RA % |
|---|---|---|---|
| 22:40 snapshot vs static | 642 519 | **99.295%** | 94.15 |
| 22:42 online module vs static | 652 012 | 99.284% | 94.24 |
| menu snapshot vs static | 624 686 | 99.314% | 96.73 |

In-match leftover grew (~18–28 KiB vs menu). Still post-unpack RA, not
missing XOR. 0 missing `.text` pages.

Second snapshot at 22:42 failed `EnumProcessModules winerr=299`; Relic
absent after. Do **not** stack module-PE + second VA-clone on a live
online PID. First clone already has the window.

Tools: `dump_ra_capture.py`, `python -m unpacker dump-extract <dmp>`.

## 100% unpacker push (PID 52968, 2026-09-06 22:46)

User authorized launch + visible **x64dbg.exe** (not hidden rbhost) to
force `slots>1`. Steam `-applaunch 1466860 -dev -nodbg -notrap`.
`run_unpacker_live_cycle.py`: seed → early module PE → launch
`C:\Program Files (x86)\rbhost\release\x64\x64dbg.exe` → wait
`--min-slots 3` → RA capture → **one** VA-clone. Relic **alive** after.
**No plant. No attach. No live MiniDump.**

New ASLR base **`0x7FF7AD880000`** — do not mix with 37560
`0x7FF6196D0000`.

| Artifact | Value |
|---|---|
| Early PE (T+~20s) | `dumps\RelicCardinal_52968_20260906_224630\00007ff7ad880000.RelicCardinal.exe.bin` |
| RA RPM | `dumps\RelicCardinal_52968_20260906_224637_ra\` heap **1224** B |
| Full dump | `dumps\RelicCardinal_52968_20260906_224637_snapshot\RelicCardinal_52968_full.dmp` **3 418 120 595** B, 4111 ranges |
| Window | `slots=3 accum=600 flag=1` |
| slot kinds | 6 / 1 / 3 |
| slot+8 | **`0x20220002`** (Watcher) |
| slot+10 | `B+0x56FA5A0` (same ptr all 3) |

`.text` vs static (best so far):

| Pair | leftover | pct | RA % | outside |
|---|---|---|---|---|
| 52968 T+20s module | **612 209** | **99.328%** | 98.70 | 7 969 |
| 52968 snapshot | 612 901 | 99.327% | 98.70 | 7 969 |
| 37560 menu snapshot | 624 686 | 99.314% | 96.73 | ~20 KiB |
| 60644 late | 651 472 | 99.285% | 92.74 | ~47 KiB |

### Fat vs leftover (not a third disk XOR)

`python -m unpacker fat-leftover`: 174 fat recs (types 1/6/7) overlap
**651 001 / 651 472** leftover bytes vs 60644 (130 recs). Type **1**
covers the `0x679530` / `0x6B8DF0` / `0xA91340` island; type **7** the
RA band. `self-0x141 == n` on all 174.

Offline apply vs 52968 early PE **worsens** leftover (99.328 → ~99.14):
0x15 memcpy+XOR, 0x16 on static/disk, raw memcpy, type1-only. Fat
`edx=1` types 1/6/7 stay the **`0x5E68` runtime path**, not compact
`0x15`/`0x16`. Geographic overlap ≠ missing disk cipher.

**100% vs late live `.text` is not a disk-unpack target.** Compact XOR
already has `coveredButWrong=0`. Ceiling at T+20s is **99.328%**; the
remaining ~604 KiB is RA-band self-mod that exists before menu. Oracle
PE / runtime lift already include it.

Reports: `meta/unpacker-fat-leftover.json`, `unpacker-fat-apply-try.json`.
CLI: `run_unpacker_live_cycle.py`, `dump_relic_snapshot.py --min-slots`.

## Stage 7 gold splice — 100% vs 52968 T+20s (2026-09-06 22:51)

Disk XOR cannot emit RA self-mod. `python -m unpacker splice-gold` copies
only leftover runs from the earliest live module PE onto
`unpacked_static.exe`.

| | Value |
|---|---|
| Gold | `dumps\RelicCardinal_52968_20260906_224630\00007ff7ad880000.RelicCardinal.exe.bin` |
| Out | `K:\aoe4_dlc\analysis\game_16.3.11308\RelicCardinal.unpacked_gold.exe` |
| Before | leftover 612 209 (99.328%), RA 604 240, outside 7 969, 2404 runs |
| After | leftover **0 / 100.0%** |
| Audit | **56 pass / 0 fail** (`gold-100`) |

`unpacked_static.exe` stays disk-only. Oracle PE stays the 60644 lift
(also 100% vs that later live). Lives diverge in RA; gold is pinned to
52968 T+20s (least drift). Not a third disk cipher.

## RA sim after unpack (2026-09-06 22:56)

User asked for **Dispatcher/45E8 simulation**, not another gold splice.
IDB `runtime_exe.i64` session `a1220dbc`. Hex-Rays
`gamesource/src/ra/RA_Integrity_Dispatcher_0x3E44034.c` +
`RA_Integrity_45E8_0x3E545E8.c`. **No plant.**

| Fact | Evidence vs 52968 T+20s gold |
|---|---|
| Compact leftover == disk leftover | **612 209 / 612 209** |
| Compact coverage of leftover | **0** (ckFail compact **0**) |
| Aligned rolling XOR leftover→gold | 18 606 B, **0** runs ≥16 |
| Fat 174 recs types 1/6/7 | `ckPair` **0/174** (`+0x120` ≠ `~+0x128`) |
| Dest slot 0 | `destRva = rva + [rec+0x90]`, addend **2/3/5** (leftover starts at `0x679533` = `0x679530+3`) |
| Fat payload vs static@dest | **781 275 / 784 408 (99.6%)** — dest snapshot, not plaintext |
| 45E8 dest-XOR `(n^seed)*r8` @ dest | leftover **761 333** (worsens by 149 124) |
| Payload memcpy @ dest, no XOR | leftover **612 804** (−595) |

5E68 (`cmp al,16h / jnz`): memset HashRec `0x162`, alloc+memcpy payload
to heap, rebase 16 dest slots, `RA_HashMap_FindOrInsert`. **No .text XOR.**
45E8 match path: `dest = [+0x20]+[+0xA0]`, memcpy then rolling XOR.
Hash mismatch sets `v203=0` and **skips** memcpy. Cloak vs gold leftover
**grows** because T+20s dest is unlock PRNG, not because dest-XOR is wrong
— see next section.

## RA sim: leftover decrypt is 45E8 cloak (2026-09-06 23:05)

Scoring cloak vs 52968 T+20s gold was the wrong oracle.

| Check | Result |
|---|---|
| `RA_Hasher` port == Unicorn on 60644 image | 36/36 (n≤0xF0) |
| Hasher(payload, 0) == `[rec+0x120]` | **174/174** |
| Hasher(payload ⊕ k0, 0) == `[rec+0x128]` | **174/174** |
| Cloak dest Capstone | MSVC prologues (`mov [rax+8],rcx; push rbp…`) **142/174** |
| Gold dest at same RVA | junk (`and al`, `retf`, `cli`) |
| Gold dest is rolling *store* `k'=k*R8` | **106/174** recs, 543 664 B |
| 60644 dest is the same stream | **116/174** |
| Cloak + ASLR-delta vs gold | **0** qwords |
| 45E8 unlock path `0x3E545E8` | last refcount: `*dest = r8 * g_RA_Prng` (assign, not XOR) |

Default `ra-sim` now **applies** dest-XOR. Leftover vs gold grows because
live dest is the unlock PRNG, not because cloak is wrong. `--no-cloak`
keeps static. Unlock / rdtsc PRNG is not disk-simulable.

Hasher table RVA `0x56FB700` → `dump/crypt/ra-hasher-table.bin`. CLI:
`python -m unpacker ra-sim`.

## Full unpacker pass (2026-09-06 23:10)

User: use the unpacker fully. Relic was **not** running — no
`pack-catch` / `hwbp` / MiniDump. Hex-Rays worker still on
`runtime_exe.i64` (~311k / 534k).

### AEAD no longer needs `cryptography`

`overlay_aead.x25519` fell through to `None` in the ida-mcp venv
(`No module named cryptography`). That made audit **53 pass / 5 fail**
(`box-sk-pk`, `live-key-match`, `decrypt-n`, `seed-in-pt`,
`pt-vs-static-file`). The pack on disk was fine; only key derivation
was skipped.

Bundled RFC 7748 Montgomery ladder (`x25519_pure`). Selftest: RFC §5.2
both vectors + §6.1 Alice×Bob. Fresh `overlay-aead`:

| Check | Result |
|---|---|
| `box_sk_pk` == live catch `532b4c79…1302203` | **yes** |
| Opposite `box_pk_sk` | not the live key |
| skip32 + extra8 pad, first 4 KiB vs `pack-decoded.bin+64` | **100%** |
| Seed at static off 2432499 | `7b5d3f1bcdfbfdfd` = `SEED_LIVE` |
| Rewrote `pack-decoded-static.bin` | 10 049 580 B |

Audit now **62 pass / 0 fail** (includes `x25519`, `gold-100`,
`rasim-ne-static` 781 523, Hasher 174/174).

### Leftover suite (re-run)

| Command | Verdict |
|---|---|
| `leftover` | 99.285% vs 60644; leftover 651 472; RA 604 159; 0 DIR64 in `.text` |
| `leftover-aslr` | **post-unpack RA / session-divergent; not missing compact XOR**. 26392 vs 60644 leftover: RA 3.67%, outside 0.35% |
| `leftover-deep` | 105 383 compact recs, eof walk exact, 0 new recs after compact |
| `fat-leftover` | 174 fat recs; 130 overlap leftover (651 001 B, 603 729 in RA) |
| `verify` | oracle `.text` vs 60644 live: **22236 pages, differ 0** |

### `corpus --dumps` — every Relic full.dmp

15 / 15 Relic minidumps. `textMissingPages=0`. Seed at RVA `0x7AF7688`
is `7b5d3f1bcdfbfdfd` on **every** dump (`seedOk=true`). First leftover
run always starts at RVA `0x679533` (RA cloak, not a third cipher).

| Dump | Base | vs static | leftover | RA% |
|---|---|---|---|---|
| 60644 full | `0x7FF7A5500000` | 99.285% | 651472 | 92.74 |
| 18816 | `0x7FF628550000` | 99.299% | 638873 | 94.55 |
| 18816 redump | same | 99.276% | 659309 | 91.64 |
| 19944 | `0x7FF666BE0000` | 99.307% | 631166 | 95.73 |
| 26392 sdkpack | `0x7FF7007B0000` | 99.310% | 628527 | 96.23 |
| 53820 | `0x7FF764200000` | 99.310% | 628561 | 96.23 |
| 37716 | `0x7FF7CECA0000` | 99.304% | 633868 | 95.31 |
| 40392 | `0x7FF7A4750000` | 99.312% | 626531 | 96.44 |
| 13568 | `0x7FF7C9A70000` | 99.323% | 616662 | 97.96 |
| 13632 | same | 99.323% | 616704 | 97.96 |
| 42656 STK | `0x7FF6F0130000` | 99.293% | 643645 | 93.87 |
| 24044 | `0x7FF6196D0000` | 99.314% | 624813 | 96.73 |
| 37560 menu snap | same | 99.314% | 624686 | 96.73 |
| 37560 online snap | same | 99.295% | 642519 | 94.15 |
| 52968 T+20s snap | `0x7FF7AD880000` | **99.327%** | 612901 | 98.70 |

Module PEs (already scored): gold / 52968 bin **99.328%** leftover
612 209; rasim default cloak **99.142%** leftover 781 523 vs static
(expected — `rasim-ne-static`). Report:
`aoe4\gamesource\meta\unpacker-corpus.json`.

### CLI strings vs unpacker products

Layer B six (` -nodbg` … ` -notrace`) are **already plaintext on the
Steam disk** (count 1). ` -dev` Layer B blob is 0 on disk and live.

`.rdata` native-name XOR is **not** compact `.text` XOR. RVA
`0x77A2961`:

| Image | bytes at RVA | `Game_IsRTM` count |
|---|---|---|
| Steam disk / static / gold / rasim / oracle PE | `cc eb e4 ed d0 c7 fe de d7 cf 81` | **0** |
| 60644 `memory.bin` (live image) | `Game_IsRTM\x00` | **1** |

`Misc_IsDevMode` and the extra `Misc_IsCommandLineOptionSet` copy are
the same: live image only. `TestConfig_` is 0 on every PE. Oracle
analysis PE splices live **`.text` only** — `.rdata` stays disk XOR.
String xrefs for XOR names still require the runtime IDB / live image,
not `unpacked_static.exe`.

### Did not run

Live Relic cycle (`suspend` / `resume-poll` / `write-catch` / `hwbp` /
`pack-catch` / `aead-catch`). Game was down. Do not MiniDump a live
Relic. Do not plant RA because leftover is not 100%.

## Invert k0 + footer table (2026-09-06 23:17)

`n = (k0 * inv(r8)) XOR seed`. Observed first-qword k0 (disk ⊕ live):

| Site | k0 | invert n | compact rec |
|---|---|---|---|
| 7AB0 `0x3DD7AB0` | `0x4a892571d5cef30a` | **4181** `0x1055` | type `0x16` self=57 |
| Enqueue `0x3DD2550` | `0x474ad0dad2909844` | **2327** `0x917` | type `0x16` self=57 |

Guess `n=64` was wrong. Formula matches inverted length; rolling XOR covers the whole span.

Footer `RA_PackFooter_Parse` `0x3F913AC` (overlay last 8 KiB, 1 hit):

| Field | Value |
|---|---|
| A / B / C / D | `c55d09b0…` / `21637264…` / **`0x995884`** / `fe273a55…` |
| check `D ^ ~(B*C) == A` | true |
| tableOff / tableSize | **0** / 10 049 668 |
| plainExpect (size−88) | 10 049 580 |
| tailAfterTable | 160 |
| aux | `0x9958ac` |

Disk-absolute tableOff = overlay `0x8076800`. Slice at tableOff is the AEAD blob (`81fab5f2…`). Inner directory after decrypt: `ptr = table+776+off`.

| type | ptr | size |
|---|---|---|
| 0 | 776 | 1 591 461 |
| 1 fat | 1 592 237 | 840 262 |
| 2 seed | 2 432 499 | 8 |
| 3 compact | 2 432 507 | 7 612 623 |
| 5…16 | tail | small |

`find_table` now hunts the seed value (size=8), so static table=0 and heap table=+64 both work. Compact walk from dir type3: **105 383** recs, Enqueue n=2327.

`recover_spans` keep rule: formula match **or** n≥16. Raw 534 796 → kept **99 925** (98 850 formula + 1 075 ≥16 no-formula). Dropped 434 871 tiny non-formula runs. Bin: `dump/crypt/recovered-xor-ranges.bin`.

`python -m unpacker ranges`. Audit: `enqueue-len`, `enqueue-invert`, `7ab0-invert`, `span-keep-rule`.

## Leftover gap closed: 100% dest slot 0 (2026-09-06 23:14)

`python -m unpacker leftover-gap`. After compact, leftover vs 52968
T+20s (**612 209**) and vs 60644 (**651 472**) sits **entirely** in fat
dest slot 0 (`destRva = rva + [rec+0x90]`). `notDest=0`, other dest
slots (1–3 exist on 171/14/9 recs) cover **0** leftover bytes.

| Check | Gold 52968 | 60644 live |
|---|---|---|
| leftover | 612 209 | 651 472 |
| in dest0 | **612 209** | **651 472** |
| not dest | **0** | **0** |
| dest0 looks like unlock `k*=R8` store | 117/174 | 127/174 |
| cloak == gold dest | **3**/174 | — |
| selective cloak on non-PRNG dests | leftover **761 333** (same as cloak-all) | — |

There is **no missing compact / type-0 / extra pack XOR**. Static dest
already holds the fat payload snapshot (~99.6%). Live dest is session
RA: 45E8 dest-XOR then unlock `*dest = r8 * g_RA_Prng`. T+20s almost
never still has cloak plaintext (3 recs). Cloak vs gold is the wrong
oracle. `splice-gold` remains the only 100% vs a live image.

CLI: `python -m unpacker leftover-gap`. Audit: `leftover-is-dest0`.

## Recheck: other-agent X25519 fix (2026-09-06 23:11)

Independent pass. Problem they solved is real; leftover vs gold is not.

**Cause (reproduced):** ida-mcp venv `3.12.13` has **no** `cryptography`.
Old `x25519()` excepted and returned `None` → `box_key` None → audit
`box-sk-pk` / `live-key-match` / `decrypt-n` / `seed-in-pt` /
`pt-vs-static-file` all fail even though `pack-decoded-static.bin` on
disk was already correct. Our 3.14 run at 23:07:29 was **61/1**
(`x25519` only): wrapper still used `cryptography`, but
`x25519_selftest()` hit a half-written / stale-pyc `x25519_pure`
(3.12 pyc 23:07:23 vs source 23:07:22).

**Ladder now:** RFC 7748 `a24=121665`, clamp `x[0]&=248` /
`x[31]&=127|64`, `u` mask bit 255. Game decompile at `0x3FBBF80` shows
`121666` (ref10 form) — different arrangement, same curve.

| Probe | Result |
|---|---|
| RFC §5.2 v1 / v2 / §6.1 Alice×Bob | **3/3** on 3.12 and 3.14 |
| `x25519_pure` == `cryptography` 46.0.5 | **yes** (3.14) |
| 3.12 wrapper (no crypto) == RFC Alice×Bob | **yes** |
| `HSalsa20(0, x25519_pure(hdr[0:32], hdr[32:64]))` == live `532b4c79…1302203` | **yes** |
| Opposite order | not the live key |
| `pack-decoded-static.bin` == `pack-decoded.bin[64:]` + seed @ 2432499 | **yes** |
| `python -m unpacker audit` (3.14, pyc wiped) | **62 pass / 0 fail** |

Corpus leftover table is RA, not a third cipher. rasim vs static
781 523 is dest-XOR vs T+20s PRNG gold — do not score cloak against
gold. Do not plant.

## splice-gold --all (2026-09-06 23:16)

`python -m unpacker splice-gold --all`: leftover lift vs every corpus
live PE. **9/9 hundred=true**. Wrote gold PEs for 52968, 60644 memory,
52968 T+20s bin. Same leftover, copied — not unlock-PRNG emulate.
Live CLI / C4SP3R: [2026-09-06-live-cli-c4sp3r.md](2026-09-06-live-cli-c4sp3r.md).

## Post-unpack layer on live 52920 (2026-09-06 23:28)

`g_RA_Prng` in the leftover-gap note is `g_RA_UnlockPrng` RVA
`0x7AFD990` (shared session `xmm`, not RA-only). Cloak site
`0x3E55493`. Unlock is last-refcount **assign** `k = R8 * xmm`.

Elevated RPM dest0 (no MiniDump):
`AOE4HOOK/tools/probe_ra_integrity.py`.

PID **52920** menu ~T+8m, **slots=0**, seed same as 60644, mismatch
budget **99**, JUMPOUT gate **0**. dest0 leftover **621 219**
(unlock **118**/174, cloak 3, static 52, other 1 × n=12 @
`0x3F56B48`). First leftover dest still `0x679533`. Integrity leftover
does not need Watcher slots.

[ra-integrity-layer](2026-09-06-ra-integrity-layer.md).

