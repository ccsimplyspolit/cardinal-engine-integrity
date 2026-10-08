# 2026-09-12 ? universal HV modules + RA session dest + timer inventory

Date: 2026-09-12. Trees: `aoe4-hv` + this finding. Build **16.3.11308.0**.
RVAs only. IDB `runtime_exe.i64` imagebase `0x7FF7A5500000` (MCP open
timed out 600s; Hex-Rays named C from the same IDB used).

## Goal (this turn)

1. HV game-agnostic: usermode modules, stop remap-per-task.
2. Study disk crypt vs **session** dest block the game writes into itself.
3. Find every timer/checker/slots/accum; hold WindowWatch at
   `slots=0 accum=0 flag=0 begin=0 end=0 (uninit/empty)`.

Not ranked first. Do not remap this boot (TSC-hide ELF, key
`0x53e50527fa8d666`).

## 1. Universal HV (ADR-007)

Mapped ELF cannot grow Relic knowledge without reboot. Query on this
boot is `status=8 not_found` (`eprocess_is_target` ignored mailbox
`push_probe_name`). `mailbox_op_protect` is coded, not mapped.

| Frozen | Lives in usermode |
|---|---|
| Mailbox ops **1?12** (`mailbox.h`) | `tools/zpp_aoe4/modules/*.json` |
| NPT write-split / ZPPN (after next map) | `zpp_at.py locate/window/timers/session` |
| No Relic RVA in `hypervisor.cpp` | RPM of `.data` / AOB of `.text` |

Next unused op = **13** (that *is* a remap). Query-fix + protect ship
**together** on the next **????????**, then freeze again.

WindowWatch empty at 16:09 is already the idle ring. Holding it does
not need a new VMMCALL.

## 2. Two crypt layers (do not mix)

### 2.1 Disk / boot ? overlay AEAD + compact XOR

Steam `.text` is ciphertext. Unpacker (already written):

```text
cd K:\aoe4_dlc\aoe4\gamesource\tools
python -m unpacker rediscover
python -m unpacker unpack-disk
python -m unpacker leftover-gap
python -m unpacker ra-sim
```

Writer: `RA_Integrity_Dispatcher` `0x3E44034` ? store
`xor [rsi], rax; rax *= R8` in `RA_TextXor_7AB0` `0x3E45870`.
Once-flag `0x7AF7655`. ~110 ms after Resume. Canon:
`AOE4HOOK/docs/RELIC_UNPACK_ALGORITHM.md`.

This is **not** the WindowWatch ring.

### 2.2 Session ? dest slot 0 (the self-write protected block)

After compact, leftover vs `unpacked_static` is **100% dest slot 0**
(`leftover-gap`, `notDest=0`). Fat pack: `destRva = rva + [rec+0x90]`.

Code: `RA_Integrity_45E8` `0x3E545E8` (named Hex-Rays
`gamesource_unp_humanized/named/RA_Integrity_45E8_0x3E545E8.c`).

HashRec = MSVC map node `+0x28` (`g_RA_HashMap` `0x7AF7AF8`):

| Off | Field |
|---|---|
| `+0x00` | size `n` |
| `+0x10` | source wyhash (`[obj+0x10]`) |
| `+0x18` | dest wyhash (`[obj+0x18]`) |
| `+0x20` + `+0xA0` | dest pointer |
| `+0x130` | source |
| `+0x138` | refcount |
| `+0x150` | copied-once |

Same `R8 = 0xDA942043DA942043`. **Different store:**

| Phase | When | Op | k0 |
|---|---|---|---|
| Cloak | first refcount, after Hasher(source) + memcpy `0x3E5547E` | `*dest ^= k; k*=R8` | `(g_RA_DestXorSeed ^ n)*R8` @ `0x3E55493` |
| Unlock | last refcount drop | `*dest = k; k*=R8` (assign) | `R8 * g_RA_UnlockPrng` (`xmm` `0x7AFD990`) |

Hasher of **source** is *before* memcpy (`0x3E55314`). Hasher of **dest**
is *before* unlock (`0x3E555F3`). Mismatch decrements
`g_RA_HashMismatchBudget` `0x7542030`.

**What we can do**

| Piece | Do | Do not |
|---|---|---|
| Session xmm / seed | RPM observe (`zpp_at.py session`) | freeze to static |
| Dest block | leftover-gap / ra-sim; let 45E8 run | stub 45E8 (boot-kill); NPT-protect dest (identity stale vs `[obj+0x18]`) |
| Code | hasher identity-golden + optional ZPPN execute (not `--eax 1`) | 14-byte plant of hasher |
| New PID | `zpp_at.py locate` unique AOBs + rebase | mix VAs; open Steam exe in IDA |

Leftover **grows** vs T+20s gold as unlock assign replaces cloak XOR.
That is the session working, not a missed compact rec. It runs with
**slots=0**.

## 3. Timers / slots / accum ? every layer

WindowWatch prints **only** the RA window vector:

```
lock 0x7AF6DC0  begin 0x7AF6DC8  end 0x7AF6DD0  cap 0x7AF6DD8
accum 0x7AFB750  flag 0x7AFB758  stride 0x198  thresh 0x46
```

`RA_Enqueue` `0x3DD2550` (Hex-Rays): lock, scan existing tags, `accum +=
slot+400`, if `accum>=0x46` set flag, `end += 408`, then **KickCtor**
`0x3E691F4`. Tag Watcher `0x20220002`. `begin==end==0` ?
`(uninit/empty)` ? the 16:09 lines. That is **ideal for this layer**.

Independent (must **not** be forced to zero):

| Layer | RVA | Healthy idle | HV/usermode hold |
|---|---|---|---|
| Window ring | above | all zero | **hide** so Enqueue never runs |
| TimerQ | list `0x7AF6D88` | ~286 nodes | never `list=0` |
| FlushTree | `0x7AFB6D8` | keys 4/8/0x2710/0x2711 deadlines | heartbeat `now+period` |
| WatcherBeat | `0x7542080` | 100 after FlushArm(4) | hide; **do not** stub Watcher |
| packEnable | `0x7542010` | observe | ? |
| KickCtor | `0x3E691F4` | not called | never stub (armed timers still Exit) |
| 7AB0 / 77E8 / C8E4 | `0x3DD7AB0` / `77E8` / `C8E4` | not packing | hide / heartbeat; do not plant |
| INT3 retaddr | `0x3E1CAF8` / `0x3E41FDC` | EP not `0xCC` | soft-bind |
| JUMPOUT gate | `0x7AFB0A0` | 0 | hasher valid |
| dest leftover | HashRec dest | grows | observe; not slots |

Zeroing the ring **after** Enqueue does not un-arm KickCtor. Nop of
Enqueue prologue ? `slots=0` then death ~8s (EventSchedule first).
ZPPN Watcher ? countdown expire ? IAT-kick even if hasher sees original
bytes.

## 4. Signatures for the next process open (same build)

Unique AOBs (16-byte MSVC prologue is **not** unique ? 7AB0 hits 334):

| Name | RVA | AOB n |
|---|---|---|
| `RA_IatScan_7AB0` | `0x3DD7AB0` | 28 |
| `RA_IatObj_Fwd` | `0x3E1E2A4` | 28 |
| `RA_Enqueue` | `0x3DD2550` | 16 |
| `RA_IatObj_CrtInit` | `0x3A8F0C` | 16 |
| `RA_Hasher` | `0x3E57050` | 16 |

`python aoe4-hv\tools\zpp_at.py locate` ? rebase `image+RVA`, verify;
mismatch searches `.text` (new build). Data timers have no unique AOB;
they ride the same rebase.

## 5. IDA

`idb_open` / `idalib_open` on `runtime_exe.i64` : WinError 10054 then
worker not ready in 600s. Open instances were COH3/LM ScarToolKit, not
Relic. Study used:

- named Hex-Rays `RA_Integrity_45E8` / `RA_Enqueue` / `RA_Integrity_Dispatcher`
- `ra-map.json`, `UPDATE_GUIDE` 3.3-3.4, `patchAT/sites.h`
- leftover-gap / ra-integrity findings

Re-open 60644 IDB in a dedicated IDA when the MCP is free; do not treat
Steam `RelicCardinal.exe` as code.

## 6. Live PID 47604 (2026-09-12 ~16:20, same session as 16:09 WindowWatch)

`zpp_at.py locate/window/session/timers` RPM (not ZPPX query). Relic started
15:53, base `0x7FF614B70000`, overlay hide ON, no dbg attach.

| Check | Result |
|---|---|
| Unique AOBs (7AB0/Fwd/Enqueue/CrtInit/Hasher) | all `sig_ok` |
| WindowWatch ring | `slots=0 accum=0 flag=0 begin=0 end=0 (uninit/empty)` **IDEAL** |
| TimerQ list `0x7AF6D88` | **nonzero** heap `0x199...` - healthy, not empty |
| FlushTree `0x7AFB6D8` | **nonzero** |
| WatcherBeat `0x7542080` | `0x2D` (countdown; hide does not stop the tick) |
| dest XOR seed | `0xFDFDFBCD1B3F5D7B` (same as 52920/60644) |
| mismatch budget | **99** |
| JUMPOUT gate | **0** |
| dispatcher once | **1** (compact XOR already ran) |
| RA image base/size | match live / `0x8C3D000` |

This proves the 16:09 lines: empty ring **and** live session dest **and** a
full TimerQ at once. HV-zeroing TimerQ/FlushTree would be a new death class.

## 7. What is not done

- Query/protect/nop5 still need **one** authorized remap (all three coded).
- WindowWatch empty is verified live on PID 47604 - not yet by HV execute-NOP.
- No live Vs AI proof that a visible debugger stays empty
  (`hold --apply` needs the next map, then a Vs AI match).
- IDA MCP decompile of 45E8 this turn: **not** from a live IDB session.
  Inventory is Hex-Rays named C + live E8 scan of plaintext `.text`.

## 8. Live E8 inventory (PID 47604) and HV empty hold

`python aoe4-hv\tools\zpp_at.py calls` on live `.text` (not Steam ciphertext):

| Callee | E8 sites |
|---|---|
| RA_Enqueue `0x3DD2550` | **66** |
| RA_EventSchedule `0x3DD15E4` | **107** |
| RA_FlushArm `0x3E8B3A0` | **17** |
| RA_TimerQ_Push `0x3E672DC` | **1** (from EventSchedule, matches ra-map) |
| RA_KickCtor `0x3E691F4` | **1** (from Enqueue, matches ra-map) |
| RA_IatScan_7AB0 | **0** (vtbl, no code xrefs) |
| RA_Integrity_45E8 | **1** (JUMPOUT `0x3F57580`) |

Watcher-pack Enqueue (tag `0x20220002` family, **not** IAT `20DE00AD` / INT3 / 45E8 fail): **37** `E8_ok` sites, **29** 4K pages (limit 32). Includes patchAT's 6 WW/sib calls plus StringPack `0x3E5D96D`, SiblingPathScan `0x3E662FF`/`0x3E669EE`, and unnamed WW clones in `0x3F5xxxx-0x3F70xxx`.

HV hold (after next map, still **one** remap with query+protect+nop5):

```text
python aoe4-hv\tools\zpp_at.py hold --apply
```

Execute copy: 5-byte NOP (`mailbox_stealth_nop5_eax = 0xFFFFFFFF`). Identity hasher still sees `E8`. Watcher continues (FlushArm/countdown). Do not stub Watcher/Enqueue prologues. Do not zero TimerQ. Builtin `--eax 1` at these sites would `ret` out of Watcher mid-function.

This boot: do not `--apply` (query not_found on mapped TSC-hide ELF). New
ELF with nop5+protect is built (`zpp_hypervisor` 16:34), not mapped.

## 9. Live 47604 dest / match / 12s empty (2026-09-12 16:36)

IDA MCP: `idb_open` on `runtime_exe.i64` still kills the session (WinError 10054).
Unpacker `leftover-gap.json`: leftover **100% dest0**, `notDest=0` (60644/gold).
`unpacked_static.exe` not on disk this host; `pack-decoded.bin` absent - live dest
heads from `unpacker-fat-leftover.json` hitHead (16 spans) classified **other**,
not a clean unlock-PRNG store. Session dest is PID-divergent (leftover-aslr).

DualFlag `Application*` `0x3A927FF170`: `2D0=0 2D1=1 +541=0` - **not** Vs AI
target (`2D0=1 2D1=0`). Overlay log last write **2026-09-08** - this Relic has
no InternalInjector. WindowWatch PID 40584 is the hide.

`zpp_at.py watch --sec 12`: 12/12 samples `slots=0 accum=0 flag=0` empty.
That is **menu hold**, not Vs AI.

cycle-state `launch_authorized=false`. HV `hold --apply` still needs the
authorized remap word.

## 10. Live HashRec dest (PID 47604)

`zpp_at.py hashrec` walked MSVC map `g_RA_HashMap` `0x7AF7AF8`:

| | |
|---|---|
| map size | **368** (walked 368) |
| dest in Relic image | **368** |
| dest formula | `*(rec+0x20)+*(rec+0xA0)` |
| unlock PRNG assign | **273** |
| other (cloak/static/mixed) | **93** |
| short | **2** |
| refcount | all **0** (unlock already ran) |
| source RVA | none in image (heap copy after memcpy) |

Canon leftover head dest `0x679533` is **unlock_prng** on this PID (fat
`hitHead` `0x679530` was the leftover span start, not HashRec dest).
Do not NPT-protect these dest pages. Do not stub 45E8.

Vs AI still not running (`2D0=0 2D1=1`). Overlay not in this PID.
`launch_authorized=false`.

## 11. LLVM 18.1.8 (2026-09-12 16:50)

`D:\CustomPrograms\LLVM` is **gone**. Live toolchain is
`C:\Program Files\LLVM` 18.1.8 (`clang` / `clang++` / `clang-cl` / `clangd` /
`lld-link`). ELF still uses NDK r19b.

Previous `build_windows.bat` left **stale** `zpp_loader.sys` (14:59,
1044480 B): Git `sh` + NDK make 3.81 could not exec
`C:/Program Files/LLVM/bin/clang` (space). Assemble failed, recipe used `;`
so make printed Built anyway. `elf_binary.o` stayed 14:59 ? the 16:34 ELF
(query + protect + nop5) was **not** incbin'd.

Fix: `LLVM_ROOT := C:/PROGRA~1/LLVM`; quote clang in `zpp_toolchain.mk`;
assemble recipe `&&`; PATH in `build_windows.bat`. Rebuild **without map**:

| File | Size | Time |
|---|---|---|
| `zpp_hypervisor` | 1013640 | 16:34:37 (unchanged this pass) |
| `elf_binary.o` | 1014008 | 16:50:14 |
| `zpp_loader.sys` | 1046528 | 16:50:15 |

`tests/Verify-AmdPort.ps1` PASS (offline, no VMRUN). `cycle-state`
`launch_authorized=false`. Next **????????** maps this sys.

## 12. Live Vs AI (PID 47604, 2026-09-12 ~16:53)

User in skirmish vs AI. Same Relic as menu (PID **47604**, started 15:53,
base `0x7FF614B70000`). Overlay **not** injected. WindowWatch **40584**
hide ON. No x64dbg.

| Signal | Value |
|---|---|
| `Application*` | `0x3A927FF170` |
| DualFlag word | **`0x0100`** (`2D0=0 2D1=1 +541=0`) native companion |
| `Application+0x330` | `0x199A165E990` heap ? **in match** |
| WW ring | **45/45** `slots=0 accum=0 flag=0 begin=end=0` |
| WatcherBeat | 33 then **71** (still ticking) |
| packEnable `0x7542010` | **1** |
| JUMPOUT / budget | 0 / 99 |

DualFlag `2D1=1` is **not** "not vs AI". `0x0001` is overlay
`MpBypassDataClear`. In-match without overlay stays `0x0100`. Classifier
in `zpp_at.py match` now uses `+0x330` for world.

Empty ring here is **WindowWatch hide**, not HV (`hold --apply` not
mapped). TimerQ / dest leftover independent. Keep playing; do not attach
dbg; remap still needs the launch word.

## 13. Vs AI 180s + dest pages + locate AOBs (16:56?17:00)

Same PID 47604, still in_match (`+0x330` live). Overlay still out.

`watch --sec 180`: **177/177** empty (`slots=0 accum=0 flag=0 begin=end=0`).
Hide, not HV. Combined with ?12 ? 3.5 min in-skirmish empty ring.

`hashrec` during match:

| | |
|---|---|
| unique dest | **174** |
| dest 4K pages | **113** (`aoe4_16.3.11308_dest_pages.json`) |
| kinds | other 93 / unlock_prng 273 / short 2 |
| refs_live | **4** (session dest still referenced in match) |
| enqueue_hold overlap | **0** |
| hasher / Enqueue / Watcher page | not dest |

Do not `mailbox_op_protect` those 113 pages. ZPPN `--nop` on 37 Enqueue
calls does not share dest pages.

`sigscan` unique AOBs (plaintext `.text`, next PID same build):
EventSchedule 32B, FlushArm **36B** (32B has clones `0x23EF070` /
`0x2D02350` / `0x3EB3764`), KickCtor 28B, TimerQ_Push 16B, 45E8 32B,
Dispatcher 32B, TextXor 24B, JUMPOUT 16B, WindowWatcher 24B (locate
only, do not plant). Catalog: `aoe4_16.3.11308.json` +
`aoe4_16.3.11308_code_sigs.json`. IDA MCP still COH3/LM, not 60644.

## 14. Dest-page protect split + prove (2026-09-12 17:03)

`protect --rva 0x3E57050 --size 0x1000` spans dest page **`0x3E58000`**.
Usermode now skips dest 4K from `aoe4_16.3.11308_dest_pages.json` and
would protect only `0x3E57000`. Pure dest (`0x645000`) is REFUSE.

`zpp_at.py prove`: live Vs AI PID 47604
`verdict=hide_hold` (`dbg_visible=0`, `windowwatch.exe` present, ring empty).
HV proof after remap = `hold --apply` then `prove --sec 60` with x64dbg
**open**, no File?Attach ? `hv_hold`.

`cycle-state.json` `sys_built` set to **16:50:15** (query+protect+nop5
loader). `launch_authorized` still false.

## CLI

```text
python aoe4-hv\tools\zpp_at.py hashrec
python aoe4-hv\tools\zpp_at.py sigscan
python aoe4-hv\tools\zpp_at.py dest
python aoe4-hv\tools\zpp_at.py match
python aoe4-hv\tools\zpp_at.py watch --sec 60
python aoe4-hv\tools\zpp_at.py abi
python aoe4-hv\tools\zpp_at.py locate
python aoe4-hv\tools\zpp_at.py window
python aoe4-hv\tools\zpp_at.py timers
python aoe4-hv\tools\zpp_at.py session
python aoe4-hv\tools\zpp_at.py calls
python aoe4-hv\tools\zpp_at.py hold
python aoe4-hv\tools\zpp_at.py prove --sec 1
python aoe4-hv\tools\zpp_at.py protect --rva 0x3E57050
```
