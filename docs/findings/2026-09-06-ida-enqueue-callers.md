# 2026-09-06 — full IDA dump: RA slot writers + attach INT3

IDB `runtime_exe.i64` session `a1220dbc`, imagebase `0x7FF7A5500000`,
build 16.3.11308.0, dump PID 60644. **RVAs only.** Other ProcDump sessions
(18816 / 53820 / 26392) are the same build — copy RVAs, never mix VAs.

User allowed Relic `.text` if slots stay empty. Choke is **one plant on
`RA_Enqueue`**, not 63 call-sites. Do not stub hasher / `45E8` / JUMPOUT /
KickCtor / vtable INT3 scanners.

## Choke points (patchAT `--full`)

| RVA | Name | Size | Prolog (IDB) | Stub |
|-----|------|------|--------------|------|
| `0x3DD2550` | `RA_Enqueue` | `0x917` | `44 89 4C 24 20 55 53 56` | **fail** `31 C0 C3` |
| `0x3E672DC` | `RA_TimerQ_Push` | `0x5E` | `48 85 C9 74 58 53 48 83` | **fail** |
| `0x3DD15E4` | `RA_EventSchedule` | `0xF69` | `48 89 5C 24 20 55 56 57` | **fail** |
| `0x3F0A7D0` | `RA_WindowWatcher` | `0x422F` | `48 89 5C 24 18 55 56 57` | **pass** `B0 01 C3` |
| `0x3F328D8` | `RA_WindowWatcher_Sibling` | `0x1974` | same | **pass** |
| `0x3DDD02C` | `RA_TopValidator_D02C` | `0x2CB` | `48 8B C4 48 89 58 10` | **pass** |
| `0x3E4F448` | `RA_RangeCheck_F448` | `0x1D8` | `48 8B C4 48 89 58 08` | **pass** |

`RA_Enqueue` **63 code xrefs** (`more=false`). `RA_EventSchedule` **101**.
`RA_TimerQ_Push` is **only** called from EventSchedule. `RA_KickCtor` is
**only** called from Enqueue. F448 is **only** called from D02C.

Watcher / sibling have **no code xrefs** (callback / vtable data only).
`GetWindowTextW` IAT (`0x7FF7AABDF2C0`) xrefs are **only** WindowWatcher
(2 sites). `IsDebuggerPresent` IAT is **only** `Dev_NoDbg_Check` + CRT
`__scrt_fastfail` — not the attach packer.

## Attach `01010001` with EP=`0x48` (reversed)

Not kernel DebugPort in Relic `.text`. Not `RA_EpInt3Ctor` (that one reads
the **MZ EP byte**). Two vtable methods compare **caller return-address
byte** to `0xCC` (software BP):

| RVA | Name | Check | Enqueue sites |
|-----|------|-------|----------------|
| `0x3E1CAF8` | `RA_RetaddrInt3_CAF8` | `mov rax,[rbp+ret]; cmp byte ptr [rax], 0CCh` | 1 |
| `0x3E41FDC` | `RA_RetaddrInt3_1FDC` | same (`[rbp+48h]`) | **3** |
| `0x3EC3200` | `RA_EpInt3Ctor` | Relic image EP `~*ep == 51` | 1 (tag args 0; slot tag from vtbl `+0x70`) |

Regex `cmp byte ptr [rax], 0CCh` in RA cluster `0x3DD0000`–`0x3F80000`:
**exactly those two** (plus EP ctor’s different EP load).

File→Attach / MCP `debug_attach_pid` plants INT3 on Relic `.text`. The next
RA method call whose **retaddr** is `0xCC` packs even when live EP is
`48 83 EC 28`. Soft-bind `relicconnect` (OpenProcess, no DebugPort) does
**not** plant INT3 — attach tags then stay empty; Watcher still packs
`20220002` on visible dbg titles.

Do **not** ret-stub CAF8 / 1FDC (vtable + post-check SRW work). `--full`
Enqueue fail eats their packs.

Slot tag `01010001` as a **raw immediate** (10 hits) is Xbox/protocol, not
RA. Live overlay `+10=0x5703D70` is `off_7FF7AAC03D00+0x70`. Xrefs to that
vtbl: **only** `RA_EpInt3Ctor` + `RA_EpInt3Tick` (tick does not re-check EP).

`01040001` immediates: **only** inside Enqueue `0x3DD26AC` / `0x3DD28F4`.
Enqueue also calls `RA_TagInList` (`0x3DD2E68`) with stack sentinels
`0x20DE00AD` and `0x01010001` (Hex-Rays; `find immediate` misses the
stack form).

## Unique Enqueue callers (grouped)

Base `0x7FF7A5500000`. One row per **function**.

| RVA | Role |
|-----|------|
| `0x3DDD02C` | D02C fail pack tag `0x80320001` (signed `-2145124351`) |
| `0x3E44034` | Integrity Dispatcher ×3 |
| `0x3E545E8` | Integrity 45E8 ×3 (hash fail → slots **and** JUMPOUT) |
| `0x3F0A7D0` | WindowWatcher ×4 tag `0x20220002` |
| `0x3F328D8` | Sibling ×2 tag `0x20220002` |
| `0x3EC3200` | `RA_EpInt3Ctor` — MZ EP `0xCC` only |
| `0x3E1CAF8` | `RA_RetaddrInt3_CAF8` — caller INT3 |
| `0x3E41FDC` | `RA_RetaddrInt3_1FDC` ×3 — caller INT3 |
| `0x3E5D6F0` | `RA_StringPack_2022` + `20220002` |
| `0x3E652DC` | Sibling helper kinds 3/4/5 size `0x1FFD` |
| `0x3E678E0` | `20220002` helper |
| `0x3E8B3A0` | hashed-GPA / proc helper (Watcher uses it) |
| `0x3E8F644` | `20220002` |
| `0x3E94180` | huge `0x8950` orchestrator |
| `0x3EA6BE0` | classifier-adjacent |
| `0x3EC6E64` | `0x1166` |
| `0x3ED6604` | |
| `0x3EDC9F8` | `20220002` |
| `0x3F03D80` | |
| `0x3F2D044` | |
| `0x3DD77E8` … `0x3DDC8E4` | early RA helpers (6 funcs) |
| `0x3E1E300` | large scanner (data-only xrefs; SRW + Enqueue) |
| `0x3F59650` … `0x3F6ECE0` | **11 clones** size `~0x225D` — sibling type 3/4/5 |
| `0x3F3D75C` | MSVC `UnDecorator` — **false positive**, ignore |

Listing search `20220002h` in RA cluster: 37 hits (Enqueue internals +
Watcher/sibling + clone family + StringPack + helpers). `find immediate`
on the dword **misses** `mov r8d, 20220002h`.

## D02C native callers (fail → EventSchedule + Enqueue)

| Caller RVA | Note |
|------------|------|
| `0x696360` | native site |
| `0xB7F100` / `0xB7F150` | helper / SCAR-adjacent |
| `0xC00090` | native site |
| `0x1ABE220` / `0x1ABE720` / `0x1ABE790` | native sites |

Pass-stub D02C (or F448) skips this pack. Enqueue stub still required for
Watcher / INT3 / integrity slot writes.

## Slot tags

| Tag | Where |
|-----|--------|
| `0x20220002` | Watcher, sibling, clones, StringPack, Enqueue body |
| `0x01040001` | Enqueue body only |
| `0x08060001` / `0x08050001` | Enqueue body only (TagInList stack). Live `+8` when caller passed `0x20DE00AD` |
| `0x01010001` | descriptor `0x5703D70`; INT3 scanners; Xbox immediates elsewhere |
| `0x80320001` | D02C in-reg, not `find immediate` |
| `0x20DE00AD` | IAT pack callers (`RA_IatPack_77E8` / `_C8E4` / Dispatcher) + Enqueue TagInList |

## IAT pack (36000 / 42764) — Watcher is the target

| RVA | Name | Role |
|-----|------|------|
| `0x3DD7AB0` | `RA_IatScan_7AB0` | data-only memcpy scanner; calls 77E8 ×4. **37836 stub = IAT-kick** |
| `0x3DD77E8` | `RA_IatPack_77E8` | Enqueue `20DE00AD` kinds 6/3/1/5 a2=0 |
| `0x3DDC8E4` | `RA_IatPack_C8E4` | second `20DE00AD` kind-6 + EventSchedule |
| `0x3DF510` | `RA_IatObj_Ctor` | vtbl `0x56FA4C0`; `Dispatcher_Once` |
| `0x3E1E300` | `RA_Scan_E300` | data-only; Enqueue callee, **no** `20DE00AD` imm. banned |

Detail: [2026-09-06-ida-iat-scan.md](2026-09-06-ida-iat-scan.md).

## Never write

| RVA | Why |
|-----|-----|
| `0x3E57050` (+ Large/Mid/Fold) | raw-load `.text` → JUMPOUT |
| `0x3E545E8` | `ret 1` boot-kill; hash **before** memcpy |
| `0x3F57539` | `jmp rax` with rax=0 hang |
| `0x3E47000` Walker | hashed ranges |
| `0x3E44034` Dispatcher | lea JUMPOUT; **slots** die if Enqueue is stubbed |
| `0x3E691F4` KickCtor | already-armed timers; stub does not cancel Exit |
| `0x3EC3200` / CAF8 / 1FDC | vtable / retaddr protocol — choke Enqueue |

`--full` = `Ww + Pass(D02C/F448) + Pipeline(EventSchedule/TimerQ) + Enqueue`.
Overlay `AOE4H_RA_TEXT_NEUTRALIZE` stays 0; lab is `patchAT.exe`.

**Live PID 40280:** 7 sites planted, window still uninit `slots=0`, overlay
Present OK ~3 s, then Relic gone (`base=0`, no VEH). Hasher still sees
Enqueue/EventSchedule stubs. Catalog is complete; `--full` is not a stable
attach.

IDA renames this pass: `RA_EpInt3Ctor`, `RA_EpInt3Tick`,
`RA_SiblingClassifier`, `RA_RetaddrInt3_CAF8`, `RA_RetaddrInt3_1FDC`,
`RA_StringPack_2022`, `RA_TagInList`. Later: `RA_IatScan_7AB0`,
`RA_IatPack_77E8`, `RA_IatPack_C8E4`, `RA_Scan_E300`.
