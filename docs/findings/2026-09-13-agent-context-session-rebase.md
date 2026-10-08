# 2026-09-13 — agent context: Launch / SESSION REBASE / dest analysis

Build **16.3.11308.0**. RelicCardinal `SizeOfImage` **`0x8C3D000`**.
**RVAs only. Never mix VAs** (ASLR). This note is the agent-facing
protocol for STEPS 3–5 (Launch AoE4, SESSION REBASE, session/destination
analysis). It does **not** authorize map / inject / attach / plant.

Canon tables: [UPDATE_GUIDE.md](../UPDATE_GUIDE.md) §1.4–1.6, §2.1.1, §3.3–3.4.
Usermode module: `aoe4-hv/tools/zpp_aoe4/modules/aoe4_16.3.11308.json`.
Dest 4K exclude: `aoe4_16.3.11308_dest_pages.json` (HashRec walk PID **46060**).
Hold / protect: `aoe4-hv/tools/zpp_at.py`.
Named Hex-Rays: `AOE4HOOK/gamesource_unp_humanized/named/RA_*`.
RA map: `AOE4HOOK/gamesource/meta/ra-map.json`.

**This turn did not:** map HV, inject, attach a debugger, run `kdu`,
launch Relic, or patch Relic `.text`.

## IDA this turn

Prefer IDB:
`K:\aoe4_dlc\dumps\RelicCardinal_60644_20260906_full_analysis\ida\runtime_exe.i64`
(imagebase **`0x7FF7A5500000`**, on disk **2 471 458 670** B).

Older pe-sieve IDB base **`0x7FF6F65C0000`** is a different ASLR copy of
the same build. **Do not mix those VAs** with 60644.

MCP `idb_list` (user-ida-pro-mcp + plugin-ida-pro-mcp-idalib +
ida-multi-mcp) = **empty**. Two `idb_open(..., force_headless,
run_auto_analysis=false)` calls died with **WinError 10054**. Treat IDA
as **unavailable** this session (same class as
[2026-09-12-hv-universal-session-timers.md](2026-09-12-hv-universal-session-timers.md)).

Cross-check used instead (same 60644 image the IDB was built from):

| Source | What matched |
|---|---|
| `modules_runtime\RelicCardinal.exe.memory.bin` (147 050 496 B) | PE `ImageBase=0x7FF7A5500000`, `SizeOfImage=0x8C3D000`, **14/14 catalog AOBs** |
| `aoe4_16.3.11308.json` signatures + `CODE_SIGS` | unique n vs this `.text` (7AB0 16B = **334** hits, 28B = **1**) |
| named Hex-Rays `RA_Enqueue_0x3DD2550.c` | lock / stride / KickCtor |
| findings 2026-09-06/07/12/13 + ADR-007 | dest skip, WindowWatch vs dest leftover, dead PIDs |

Do not open on-disk Steam `RelicCardinal.exe` as code.

---

## STEP 3 — Launch AoE4 (ritual only)

Vs AI / menu. Not ranked. Not this agent's job to start the process.

```text
1. Kill visible x64dbg.exe / leftover rbhost RuntimeBroker (DualFlag / sibling path).
2. WindowWatch ON (repo x64\Release\WindowWatch.exe, elevated).
3. Steam Relic:  -dev -nodbg -notrap
   Wait for a real titled HWND. Do not bind a PID that has no window.
4. Overlay inject is a later product step (APC LoadLibraryW, elevated).
   Hold / rebase agents may run with overlay absent.
5. HV hold, if used: Relic empty → zpp_at.py wait-hold --apply
   → THEN hidden x64dbg → THEN Attach.
   Any WindowWatch slot → kill Relic immediately (KickCtor already armed).
```

Hide so `RA_WindowWatcher` never calls `RA_Enqueue` for tag `0x20220002`.
Do **not** File→Attach / `debug_attach_pid` (PID 41064 dead ~8s, EP=`0x48`).
Do **not** stub Watcher / Enqueue / KickCtor / TimerQ / FlushArm / 7AB0 / 45E8
prologues. Visible `x64dbg.exe` before hold apply = DualFlag.

WindowWatch empty is **only** the ring
`lock/begin/end/cap/accum/flag`. It is not TimerQ, not dest leftover.

Ideal: `slots=0 accum=0 flag=0 begin=0 end=0 (uninit/empty)`.
Live Vs AI PID **47604**: 177/177 empty over 180s (hide, DualFlag `0x0100`).

---

## STEP 4 — SESSION REBASE (every new PID)

Same build never needs a new ELF. New PID = new ASLR base.

```text
current_base = EnumProcessModules / Toolhelp / PEB+0x10
VA           = current_base + RVA
```

Then **fail-closed** (`STALE_SIGNATURE`) unless **all** of these hold:

1. `VA` ∈ `[current_base, current_base + SizeOfImage)`.
   Expect `SizeOfImage == 0x8C3D000` and RA rec `0x7AF7B30` matches.
2. PE section contains the RVA (table below). `.text` is **RX**
   (`Char=0x60000020`). `.rdata` **R**. `.data` **RW**.
3. Unique catalog AOB matches at `VA` (n from the table, not a 16-byte
   MSVC prologue). Surrounding bytes = that AOB.
4. RA rec `QWORD[current_base+0x7AF7B28] == current_base`.
5. `QWORD[current_base+0x56FA4D0] == current_base+0x3DD7AB0` (7AB0 vtbl).

Mismatch on a **same-build** locate → **`STALE_SIGNATURE`**: stop. Do not
invent a new RVA. Do not reuse a VA from another PID. Compact XOR at
**T+~2s** can inflate E8→Enqueue (57 WW / 41 pages); stable titled scan
is **37 Watcher-tag + 4 INT3**, allowlist `known_enqueue_rvas`.

New build only: `zpp_at.py sigscan` then edit the JSON module. Still no
Relic `.text` plant.

Commands (RPM, no plant):

```text
python aoe4-hv\tools\zpp_at.py locate
python aoe4-hv\tools\zpp_at.py window
python aoe4-hv\tools\zpp_at.py timers
python aoe4-hv\tools\zpp_at.py session
```

---

## session_id (logical; not a Relic C struct)

Capture once per live Relic. **Never copy** from a previous PID.

| Field | How (this host) | Relic RVA / note |
|---|---|---|
| `pid` | Toolhelp / `PsGetProcessId` decode | Windows PID reuse is real |
| `creation_time` | `GetProcessTimes` CreationTime / CIM `CreationDate` | **not** a Relic RVA |
| `cr3` | HV `query` `cr3=` is often **kernel DTB** when `image=0`. User walk = `DirectoryTableBase` **0x28** after SME C-bit strip; `userdtb_off=0` = KVAS off | Do not treat `0x7e2da2000` from 15556/53020/31656 as Relic user CR3 |
| `image_base` | Toolhelp / PEB `+0x10` / HV `image_rpm` | must equal RA `0x7AF7B28` |
| `image_size` | PE `SizeOfImage` | RA `0x7AF7B30` expect `0x8C3D000` |
| `.text` | PE section | RVA `0x1000`, VSize `0x56DCFDC`, Raw `0x56DD000`, **RX**. Search window in `zpp_at.py`: `TEXT_RVA=0x1000` `TEXT_SIZE=0x56DC000` (22236 pages) |
| `.rdata` | PE section | RVA `0x56DE000`, VSize `0x1E63370`, **R**. Hasher table `0x56FB700`, 7AB0 vtbl `0x56FA4D0` |
| `.data` | PE section | RVA `0x7542000`, VSize `0x1174039`, **RW**. Window / TimerQ / session seeds live here. WatcherBeat `0x7542080` is near the start |

60644 memory.bin PE `ImageBase` is the IDB base `0x7FF7A5500000` (that
dump only). Next process will differ.

Also persist (HV loader, not Relic): `zpp userdtb_off=` `peb=` `dtb=`
`name=` `links=` `pid=` `ntos=`.

---

## PE sections (60644 memory.bin = live image layout)

| Name | RVA | VSize | Characteristics | Prot |
|---|---|---|---|---|
| `.text` | `0x1000` | `0x56DCFDC` | `0x60000020` | RX |
| `.rdata` | `0x56DE000` | `0x1E63370` | `0x40000040` | R |
| `.data` | `0x7542000` | `0x1174039` | `0xC0000040` | RW |
| `.pdata` | `0x86B7000` | `0x3CC708` | `0x40000040` | R |
| `_RDATA` | `0x8A84000` | `0xE7C0` | `0x40000040` | R |
| `.rodata` | `0x8A93000` | `0xD50` | `0x40000040` | R |
| `.rsrc` | `0x8A94000` | `0x21CB0` | `0x40000040` | R |
| `.reloc` | `0x8AB6000` | `0x1869E0` | `0x42000040` | R |

EP RVA `0x4FB0884`. Only `.text` is executable.

---

## STEP 5 — static RVA vs runtime destination

Two different things share the word “dest”:

| | Static (rebase) | Runtime destination (session) |
|---|---|---|
| What | Function / global RVA in the PE | HashRec dest pointer: `*(rec+0x20)+*(rec+0xA0)` or fat `rva+[rec+0x90]` |
| Who writes | Compiler / unpacker / compact XOR once (`Dispatcher` `0x3E44034`) | **45E8** cloak XOR then unlock **assign** (`R8=0xDA942043DA942043`) |
| WindowWatch? | No | No. Leftover vs static is **100% dest slot 0** at `slots=0` |
| NPT protect? | Hasher page `0x3E57000` **yes** (identity golden) | Dest 4K pages **no** — hasher of dest vs `[obj+0x18]` needs identity stores |

Cloak: first refcount, after Hasher(source)+memcpy `0x3E5547E`:
`*dest ^= k; k*=R8`, k0=`(g_RA_DestXorSeed ^ n)*R8` at `0x3E55493`.
Unlock: last refcount: `*dest = k; k*=R8`, k0=`R8 * g_RA_UnlockPrng`
(`xmm` `0x7AFD990`). Seed `0x7AF7688` on 60644/52920/46060/47604 =
`0xFDFDFBCD1B3F5D7B`. Mismatch budget `0x7542030` live menu often **99**.
JUMPOUT gate `0x7AFB0A0` ideal **0**. Dispatcher once `0x7AF7655` = **1**
after compact.

### Why writing dest pages triggers AT

Hasher `0x3E57050` raw-loads **identity** `.text` (source then dest).
If NPT write-split / protect covers a dest page, 45E8 stores land on the
stealth copy while hasher still hashes identity → `[obj+0x18]` miss →
budget-- → JUMPOUT. Same for mailbox `protect` of hasher `size=0x1000`
from `0x3E57050`: span is pages **`0x3E57000` (ok)** and **`0x3E58000`
(dest — skip)**. `zpp_at.py protect` already drops dest pages.

Two Watcher-tag `E8→Enqueue` sites sit **on dest pages**. NOP / protect
there is a dest write as far as 45E8 is concerned. Hold **skips** them
and still arms the other Watcher-tag + INT3 sites.

Verified on 60644 `memory.bin` (rel32 → `RA_Enqueue`):

| Site | Page | Bytes | Target |
|---|---|---|---|
| `0x3F04118` | `0x3F04000` dest | `E8 33 E4 EC FF` | `0x3DD2550` |
| `0x3F2D402` | `0x3F2D000` dest | `E8 49 51 EA FF` | `0x3DD2550` |

Hold apply (when SVM can GVA→GPA): ZPPN `--nop` `eax=0xFFFFFFFF` on
execute-copy only. Identity stays original `E8`. Cap **32** stealth
pages. Do not `--eax 1` hasher. Do not ZPPN Watcher/Enqueue prologues.

---

## Objects (code)

Discovery: catalog AOB + named Hex-Rays + UPDATE_GUIDE + **60644
memory.bin match** (IDA xrefs unavailable this turn). `static` = this
RVA. `dest` = the 4K page is in `dest_pages.json` (45E8 self-write).

| RVA | Name | Sect / page | Static vs dest | Skip or arm | Unique AOB (60644) |
|---|---|---|---|---|---|
| `0x3DD2550` | `RA_Enqueue` | `.text` `0x3DD2000` | **static**. Not dest. SNAP lives inside 7AB0 window `0x3DCD6E0`/`0x10FD0` | **Hide** so Watcher never calls it. Do **not** nop prologue (`31 C0 C3` → slots=0 then ~8s EventSchedule death). HV: NOP **call sites** on execute-copy | n=16 `44894c24205553565741544155415641` |
| `0x3E57050` | `RA_Hasher` | `.text` `0x3E57000` | **static**. Page not dest. Neighbor `0x3E58000` **is dest** | **protect** identity golden `size=0x1000` but **skip dest `0x3E58000`**. No 14-byte plant. No `--eax 1` | n=16 `48895c2420574883ec304d8bd84c8bd2` |
| `0x3F0A7D0` | `RA_WindowWatcher` | `.text` `0x3F0A000` | **static**. Not dest | **Do not plant / ZPPN**. Hide titles. Stub `ret 1` → 7AB0 IAT-kick even if hasher sees original bytes | n=24 `48895c24185556574154415541564157488dac2490c7ffff` |
| `0x3F328D8` | `RA_WindowWatcher_Sibling` | `.text` `0x3F32000` | static, not dest | Same as Watcher. Path scan types 3/4/5 → Enqueue tag `0x20220002` | n=24 `48895c24185556574154415541564157488dac2440f3ffff` |
| `0x3E691F4` | `RA_KickCtor` | `.text` `0x3E69000` | static **on a dest page** | **Never stub, never protect**. 1 xref from Enqueue; already-armed heap timers still Exit | n=28 `488bc448895810488968184889702048894808574883ec30418bd949` |
| `0x3E672DC` | `RA_TimerQ_Push` | `.text` `0x3E67000` | static, not dest | **Never stub**. 1 E8 from EventSchedule. Do not `list=0` | n=16 `4885c97458534883ec30488bd9488d0d` |
| `0x3E8B3A0` | `RA_FlushArm` | `.text` `0x3E8B000` | static, not dest | **Never plant**. Heartbeat `now+period` in `.data`. 32B prologue clones at `0x23EF070` / `0x2D02350` / `0x3EB3764` — use **36B** | n=36 `488bc4488958104889701848897820554154415541564157488d68a14881ecd0000000` |
| `0x3DD7AB0` | `RA_IatScan_7AB0` | `.text` `0x3DD7000` | static, not dest | **Do not plant**. Watcher expire → IAT pack `slots=4` tags `08050001`/`08060001`. Heap clone ≠ rdata vtbl | n=28 `48895c24205556574154415541564157488d6c24e94881ec90000000` |
| `0x3E545E8` | `RA_Integrity_45E8` | `.text` `0x3E54000` | static **on dest page**; **writer of dest** | **Never stub** (boot-kill). **Never NPT-protect dest** | n=32 `488bc4488958104889701848897820554154415541564157488da808f9ffff48` |
| `0x3DD15E4` | `RA_EventSchedule` | `.text` `0x3DD1000` | static, not dest | Locate only. Many E8 callers. Fail path of FlushArm. Do not nop all | n=32 `48895c24205556574154415541564157488bec4881ec80000000488b05bb5b99` |
| `0x3E44034` | `RA_Integrity_Dispatcher` | `.text` `0x3E44000` | disk compact XOR (not session dest) | Observe once-flag. Do not plant | n=32 `488bc4488958104889701848897820554154415541564157488da828ecffffb8` |
| `0x3E45870` | `RA_TextXor_7AB0` | `.text` `0x3E45000` | disk `xor [rsi],rax; rax*=R8` | Disk layer. Not WindowWatch | n=24 `4831064883c608490fafc04883e90175ef488bbd38020000` |
| `0x3F57580` | `RA_JUMPOUT` | `.text` `0x3F57000` | fail `0x3F575B1` | Keep hasher valid so gate stays 0 | n=16 `e863d0efff4883f80074264881c4f004` |
| `0x3E1E2A4` | `RA_IatObj_Fwd` | `.text` `0x3E1E000` | static | Do not plant. `[obj+8]` live **0** through pack | n=28 `48895c240848896c24104889742418574883ec304883790800498bf9` |
| `0x3A8F0C` | `RA_IatObj_CrtInit` | `.text` `0x3A8000` | static | Locate | n=16 `4883ec28488d0da9ac7407e8f465a303` |
| `0x3E8B264` | `RA_FlushTree_Ensure` | `.text` `0x3E8B000` | static | Locate; then EraseKey `0x3E8CF80`. Do not erase keys 4/8/`0x2710`/`0x2711` | n=16 `40534883ec60488b05af04c7034885c0` |
| `0x3F815F4` | `RA_WorkQ_PeekSlot` | `.text` `0x3F81000` | static | Observe WorkQ `0x7AFD950`. Do not zero | n=16 `4883ec4883f904733d8bd1488d0d4ac3` |
| `0x3EC3200` | `RA_EpInt3Ctor` | `.text` `0x3EC3000` | **dest page** | Soft-bind; EP INT3 packs. Do not plant. Page skip-protect | n=24 `48895c2410488974241848894c2408555741544155415648` |
| `0x3E1CAF8` | `RA_RetaddrInt3_CAF8` | `.text` `0x3E1C000` | static | Hold may NOP its `E8→Enqueue` (`0x3E1CCE8`) on execute-copy before dbg | head `4c8bdc49895b10…` |
| `0x3E41FDC` | `RA_RetaddrInt3_1FDC` | `.text` `0x3E41000` | static | Same (`0x3E421E2` / `0x3E426F5` / `0x3E429F8` all `E8→Enqueue` on 60644) | — |
| `0x3DD77E8` | `RA_IatPack_77E8` | `.text` `0x3DD7000` | static | Do not plant (IAT-kick) | — |
| `0x3DDC8E4` | `RA_IatPack_C8E4` | `.text` `0x3DDC000` | expire `node+0x30` | Do not plant. Heartbeat instead | — |
| `0x3DDD02C` | TOP validator | `.text` | fail → enqueue | Observe | — |
| `0x3E4F448` | range check F448 | `.text` | whitelist vs image | Rec base/size must match live | — |

Hold Watcher-tag allowlist (no dest): 35 sites in `known_enqueue_rvas`.
Catalog `watcher_pack_sites` n=37 includes the two dest E8s above;
`hold --apply` **skips** those, arms **35** WW / **27** pages, then INT3
if stealth cap allows (live 53020/31656: **39** `E8_ok` after skip dest).

---

## Objects (data / session)

| RVA | Name | Sect | Skip or arm | Why dest-write / AT |
|---|---|---|---|---|
| `0x7AF6DC0` | window SRWLOCK | `.data` | hide; empty-ok | Enqueue takes this then mutates the ring |
| `0x7AF6DC8` / `0x7AF6DD0` / `0x7AF6DD8` | begin / end / cap | `.data` | hide | stride `0x198`; `end==cap` grow `0x3DD0BC4` |
| `0x7AFB750` / `0x7AFB758` | accum / flag | `.data` | hide | `+= slot+400`; thresh `0x46` |
| `0x7AF6D80` / `0x7AF6D88` | TimerQ lock / list | `.data` | **never list=0** | Healthy menu ~286 nodes. Not WindowWatch |
| `0x7AFB6D8` | FlushTree | `.data` | heartbeat | FlushArm writes `node+0x30=now+period` |
| `0x7542080` | WatcherBeat | `.data` | hide; do not stub Watcher | `<=0` → FlushArm(4), reset 100 |
| `0x7542010` | packEnable | `.data` | observe | `==1` Enqueue |
| `0x7AF7688` | dest XOR seed | `.data` | observe | cloak k0. Same live value this build |
| `0x7AFD990` | unlock PRNG xmm | `.data` | observe | last-refcount assign |
| `0x7542030` | mismatch budget | `.data` | hasher identity | 45E8 `--` on src/dst hash miss |
| `0x7AFB0A0` | JUMPOUT gate | `.data` | hasher identity | ideal 0 |
| `0x7AF7B28` / `0x7AF7B30` | recorded image base / size | `.data` | rebase check | 60644 dump: `0x7FF7A5500000` / `0x8C3D000` |
| `0x7AF7AF8` | HashMap | `.data` | observe | rec at map node `+0x28` |
| `0x7AF7655` | dispatcher once | `.data` | observe | 1 = compact XOR already ran |
| `0x7AF3BC0` | `g_RA_IatObj` | `.data` | observe `+8` | do not plant Fwd/7AB0 |
| `0x56FA4D0` | 7AB0 vtbl | `.rdata` | rebase: equals `base+0x3DD7AB0` | 60644: `0x7FF7A92D7AB0` |
| `0x56FB700` | hasher table | `.rdata` | observe | wyhash Large/Mid |
| `0x7AFD950` | WorkQ | `.data` | do not zero | 7AB0 work path |
| `0x844B2ED` | `-nodbg` flag | `.data` | overlay DevForceNoDbg | not a `.text` patch |

Dest 4K list is **113 pages** in `aoe4_16.3.11308_dest_pages.json`
(PID 46060, 174 unique dest). Includes hasher neighbor `0x3E58000`,
45E8 page `0x3E54000`, KickCtor page `0x3E69000`, skip-E8 pages
`0x3F04000` / `0x3F2D000`. Hasher / Enqueue / Watcher **function** pages
are **not** dest (`special` in that JSON).

---

## Dead image bases — never reuse

`VA = stale_base + RVA` is `STALE_SIGNATURE`. These processes are gone.

### HV hold PIDs (2026-09-13)

| PID | Image base | Note |
|---|---|---|
| **15556** | `0x7FF6ECD90000` | empty then `slots=3`; 39× `status=8` |
| **53020** | `0x7FF6ECD90000` (same ASLR as 15556 — still **dead**) | titled; `cr3=0x7E2DA2000` was query kernel DTB; hold not armed |
| **31656** | `0x7FF765E20000` | `-dev -nodbg -notrap`; identity original; execute-copy not armed |

Same CR3 in those three queries does **not** mean the user DTB is
reusable. `pte_phys.h` even asserts `!ram_dtb(0x7ff6ecd90000)`.

### Dump / live table (16.3.11308.0, SizeOfImage `0x8C3D000`)

| PID | Relic base (that process only) |
|---|---|
| 60644 (IDB) | `0x7FF7A5500000` |
| pe-sieve 16024 / `7ff6f65c0000` IDB | `0x7FF6F65C0000` |
| 46060 | `0x7FF6AF600000` |
| 47604 | `0x7FF614B70000` |
| 52968 | `0x7FF7AD880000` |
| 37560 / 24044 | `0x7FF6196D0000` |
| 26976 / 52920 | `0x7FF7E64B0000` |
| 39056 | `0x7FF7E43A0000` |
| 18816 | `0x7FF628550000` |
| 19944 | `0x7FF666BE0000` |
| 26392 | `0x7FF7007B0000` |
| 53820 | `0x7FF764200000` |
| 37716 | `0x7FF7CECA0000` |
| 40392 | `0x7FF7A4750000` |
| 13568 / 13632 | `0x7FF7C9A70000` |
| 42656 (STK) | `0x7FF6F0130000` |
| 41064 / 28944 / 53700 | gone; do not attach |

Also refuse: inventing VAs, mixing 60644 IDB VAs with pe-sieve VAs,
opening Steam exe as the IDA image.

---

## Other agents must

1. `VA = current_base + RVA` from **this** PID.
2. Validate image range, section, prot, unique AOB, surrounding bytes.
3. **`STALE_SIGNATURE` → fail-closed.** No “close enough” plant, no
   leftover VA from chat, no 16-byte MSVC prologue as 7AB0.
4. Never reuse the dead bases listed above.
5. Do not NPT-protect dest pages. Do not stub KickCtor / TimerQ /
   FlushArm / Watcher / 7AB0 / 45E8 / Enqueue prologues.
6. Do not map HV / `kdu` / attach from this note. Hold apply still
   needs a living SVM that can GVA→GPA Relic `.text` (`status=8` on
   15556/53020/31656 = not_found, not a green light).

## Cross-refs

- [2026-09-13-hv-hold-before-dbg.md](2026-09-13-hv-hold-before-dbg.md)
- [2026-09-13-hv-full-map-handoff.md](2026-09-13-hv-full-map-handoff.md)
- [2026-09-12-hv-at-catalog-46060.md](2026-09-12-hv-at-catalog-46060.md)
- [2026-09-12-hv-universal-session-timers.md](2026-09-12-hv-universal-session-timers.md)
- [2026-09-07-hide-fix-ww.md](2026-09-07-hide-fix-ww.md)
- [2026-09-06-ra-emu.md](2026-09-06-ra-emu.md) / [ra-kick-emu](2026-09-06-ra-kick-emu.md)
- [RELIC_DEBUG_ATTACH.md](../RELIC_DEBUG_ATTACH.md)
- ADR-007 `aoe4-hv/docs/decisions/007-universal-usermode-modules.md`
