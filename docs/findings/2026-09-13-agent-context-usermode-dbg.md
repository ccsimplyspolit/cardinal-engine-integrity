# 2026-09-13 agent context — usermode modules, fail-closed writes, Vs AI, x64dbg

> **Superseded (2026-09-14):** AUTO is **off**. `--patch-game` writes
> `auto_run=0`. Confirm overlay RUN, then stock `x64dbg.exe`
> (`Run-ProductDbgCycle.ps1`). [AUTO off](2026-09-14-patch-game-auto-off.md).

Agent-facing STEPS **7–11**. Cross-check of `aoe4-hv/tools/zpp_aoe4`, `zpp_at.py`, overlay hide / Present / injector, WindowWatch, `Start-X64dbgHidden.ps1`, [2026-09-07-hide-fix-ww](2026-09-07-hide-fix-ww.md), [2026-09-13-hv-hold-before-dbg](2026-09-13-hv-hold-before-dbg.md).

**This pass did not map HV, did not inject, did not change mailbox ops 1–12.**

Build **16.3.11308.0**. RVAs only. IDB `runtime_exe.i64` imagebase `0x7FF7A5500000`. Canon ritual: [UPDATE_GUIDE.md](../UPDATE_GUIDE.md) HV-hold paragraph, ADR-007, [RELIC_DEBUG_ATTACH.md](../RELIC_DEBUG_ATTACH.md).

This boot (2026-09-13 ~16:17): `aoe4-hv/docs/cycle-state.json` `status=new_bsod` `launch_authorized=false` Event 41 **15:54:27**. Ping `ud` is not a green light. Do not `hold --apply` until query `status=0` **and** the user said **запускай**.

---

## STEP 7 — preferred module files

Directory: `aoe4-hv/tools/zpp_aoe4/`. ELF stays dumb (ADR-007). Relic RVAs live here. Next mailbox op is **13** (remap). **Do not edit ops 1–12.**

| File | Kind | Exists | Role | Edit? |
|---|---|---|---|---|
| `modules/generic_hv.json` | `hv_abi` `frozen:true` | **yes** | Mailbox ABI only (ops 1–12). Any guest. Changing it does **not** change a mapped ELF. | **No ops.** Workaround flags in `this_boot_mapped` only. |
| `modules/aoe4_16.3.11308.json` | `game_module` | **yes** | Window / dest / timers / `hold_empty` / unique AOBs in `signatures[]`. This is the catalog `zpp_at.py` merges on top of `at_catalog.json`. | Yes — new RVA / AOB for **this** build. New build = **new** `aoe4_<ver>.json`, do not overwrite ABI. |
| `modules/aoe4_16.3.11308_code_sigs.json` | live `sigscan` capture | **yes** (PID **47604**) | Unique AOB lengths for *next* PID. Locate-only; **do not plant**. Subset of `CODE_SIGS` in `zpp_at.py` (9 of 14). | **Do not hand-author as ABI.** Recreate with `python tools/zpp_at.py sigscan` on a live titled Relic. |
| `modules/aoe4_16.3.11308_dest_pages.json` | dest skip list | **yes** (PID **46060**) | 4K pages 45E8 writes. `protect` / `hold --apply` skip these. | Recreate with `zpp_at.py dest` after a new session HashRec walk. |
| `at_catalog.json` | hasher / FairPlay policy | **yes** | ADR-006: hasher ZPPN ok, `--eax 1` forbidden. FairPlay out of HV. | Policy only. |
| `sites.json` | stealth VA list | **yes, empty** | Empty on purpose. `hold --apply` writes `%TEMP%\zpp_hold_sites.json`. | Do not fill Relic RVAs by hand. |
| `zpp_aoe4.cpp` | mailbox EXE | **yes** | Frozen ops 1–12. Name stem `RelicCardinal` (15-char EPROCESS). | No new op. |

### generic_hv.json (ABI only)

Ops **frozen**: hello=1, hello_ack=2, ping=3, query_cr3=4, read_virt=5, stealth_arm=6, stealth_disarm=7, stealth_clear=8, hide=9, unhide=10, status=11, protect=12. `next_op=13`.

`this_boot_mapped` (honest, not a wish): `query_uses_probe_name=false`, `protect_op=false`, `stealth_nop5=false`. Workaround: `locate` / `window` / `timers` / `session` / `calls` / `hold` use **RPM**, not ZPPX query. `stealth --nop` eax = `0xFFFFFFFF`.

Remap **only** if: new op ≥13, `mailbox_msg` wire, PSK rotate, NPT PTE / write-split / MTF kind, EPROCESS walk that is coded-not-mapped.

### aoe4_16.3.11308.json vs code_sigs.json

| | `aoe4_16.3.11308.json` | `aoe4_16.3.11308_code_sigs.json` |
|---|---|---|
| Who writes it | Humans after IDA / locate | `cmd_sigscan` (overwrites) |
| Has window/session/hold | yes | no (`pid` + `signatures` only) |
| Use for `hold --apply` | **yes** (`known_enqueue_rvas`, dest skip, window RVAs) | no |
| Use for next-PID AOB | `signatures[]` already in the game JSON | regenerate if a prologue is not unique |

**Create later (not this pass):** a new `aoe4_<FileVersion>.json` when Relic is not 16.3.11308.0; then `sigscan` + `dest` on that PID. Do **not** create mailbox 13. Do **not** invent a second ABI file.

Same-build new PID: `python tools/zpp_at.py locate` then `sigscan`. Steam exe is ciphertext.

---

## STEP 8 — fail-closed checklist before ANY write

Writes here mean ZPPX `stealth` / `protect` / `hide` / `unhide` **or** overlay Relic `.text` / DualFlag / PAGE_GUARD. RPM of `.data` is not a write.

`zpp_at.py hold --apply` already refuses some cases (rc=2 window RPM fail, rc=3 dirty ring, rc=4 visible `DBG_PROCESS`). It does **not** check version, CreationDate, CR3↔PID, or log a before/after dump. Agents still run the full list.

Refuse and stop if any box is empty or mismatches. Do not “try apply anyway”.

| # | Check | How | Pass |
|---|---|---|---|
| 1 | **PID** | Toolhelp `RelicCardinal.exe`. One process. | Exactly one. Ambiguous = stop. |
| 2 | **Creation time** | `Win32_Process.CreationDate` (or `Get-Process StartTime`) | Newer than last KickCtor death / last Event 41. Recycled PID + old VA list = **stale session**. |
| 3 | **CR3** | `zpp_aoe4 query --name RelicCardinal.exe` → `status=` `cr3=` | `status=0`. `status=8` = `not_found` (not `hook_failed`=10). Do not arm. Query CR3 is often **kernel** DirectoryTableBase; do not pass it as user DTB. `image=0` is normal this ELF — use `image_rpm`. |
| 4 | **Module base** | Toolhelp `EnumProcessModules` = `zpp_at.py window` `image=` | Match. Never reuse a VA from another PID (ASLR). SizeOfImage `0x8C3D000`. |
| 5 | **Version** | Relic `FileVersion` / `ProductVersion` | `16.3.11308.0`. Else stop; need a new game JSON. Steam disk is ciphertext — version from the **live** image. |
| 6 | **Range** | Site VA = `base+RVA`, page 4K, not dest | In `.text`. Skip dest pages (`0x3E58000` hasher dest, Enqueue `0x3F04000` / `0x3F2D000` sites `0x3F04118` / `0x3F2D402`). Cap 32 stealth pages. |
| 7 | **Original bytes** | RPM `n` bytes **before** arm | Watcher/INT3 sites: first byte `E8`. Hasher `0x3E57050`: `48895C2420574883EC304D8BD84C8BD2`. Mismatch = compact XOR still rewriting **or** wrong PID. Wait for titled window; early T+2s scan inflates 57 WW E8 / 41 pages vs stable 37+4 / 29. |
| 8 | **Signature** | `locate` unique AOB from game JSON | `sig_ok` at catalog RVA. 16-byte MSVC prologue is **not** unique (7AB0 334 hits). |
| 9 | **Stale session** | Compare PID + CreationDate + image + SVM key + CR3 to the last `window` / `hold` log | Any field from a dead Relic / previous map = refuse. `ZPP_HYPERCALL_KEY` must be **this** map (`last-zpp-key.txt`). Leftover CR3 after Relic exit is only for `stealth --clear`. |
| 10 | **Before/after log** | One block in the dated finding | Before: PID, StartTime, image, version, query status/cr3, window line, `E8_ok` / hasher `sig_ok`, dest skip, dbg list. After: each `arm va=… status=` (must be **0**, not 8), hasher protect rc, window still empty. |

`hold --apply` extra refuses (already in `zpp_at.py`):

- visible `x64dbg.exe` / `x32dbg.exe` / `x96dbg.exe` / `dbg64.exe` / `ollydbg.exe` / `cheatengine-x86_64.exe` / `ce-x64.exe` → rc=**4**
- `slots` or `accum` or `flag` ≠ 0 → rc=**3** (KickCtor may already be armed — **kill Relic now**)
- window RPM fail → rc=**2**
- missing `ZPP_HYPERCALL_KEY` → 1
- stealth page cap 32 after trim → 1

**Never write:** Watcher / Enqueue / TimerQ / KickCtor / FlushArm / 7AB0 / 45E8 **prologues**. Hasher `--eax 1`. Overlay 14-byte hasher plant. `mailbox_op_protect` on dest pages. ntdll QIP hook. `patchAT --ww` / `--iat` / `--enqsnap` / `--packs`.

Identity (hasher raw-load) must stay **original bytes**. NOP only on **execute-copy**.

---

## Overlay vs AT — what ticks the ring vs what stays off until hold status=0

Product inject: APC `LoadLibraryW` of sibling `InternalInjector.dll`. DXGI Present vtable patch happens **after** DllMain (`HooksInit` → timer → `InstallPresentHooks`). DllMain must stay short.

### Can itself tick AT (or look like a pack)

| Surface | Code | Effect on WindowWatch ring |
|---|---|---|
| APC inject / new PE | `DllInjector` `QueueUserAPC2` → `LoadLibraryW` | Sibling `0x3F328D8` matches leaf `x64dbg.exe` and path `\x64dbg\`. `InternalInjector.dll` is **not** that needle. PID **52920**: overlay-only hold stayed `slots=0`. |
| DXGI Present hook | `hooks.cpp` `InstallPresentHooks` / `BeforePresent` | Not WW slots by itself. First Present ~1s after inject is where crash-catch AVs were (37124 / 27072) — **dbg must already be attached** for that ritual, which is the **opposite** of HV hold. |
| `EngineFogService` every Present | RA watch 250 ms, FOWCTRL1+8, optional PAGE_GUARD re-arm | Watch is RPM. `WindowClear` on leftover OP20 **does not** cancel KickCtor. |
| DualFlag `.data` | `MpBypassMaybeDataClear` ~1 Hz in init; `dualflag_auto` default **1** in `config.ini` | Lobby/script gate (`Application+0x2D0/0x2D1`). **Not** a vs-AI detector. Menu no-ops. `0x0101` = Validation FAIL. Do not treat DualFlag as WW. |
| RA neutralize `.text` | `MpBypassInstallRaNeutralize` (D02C/F448/enqueue/watcher/timer inline) | **IAT-kick / JUMPOUT class.** Config default `ra_neutralize=0`. Must stay **off** until HV hold is proven — and generally **off** even after (ADR: no plant). |
| MapHack PAGE_GUARD | `EngineArmMapHackPageGuard` | Relic `.text` guards. Off until hold status=0. Integrity memcpy `0x3E77BD2` PAGE_GUARD **kills**. |
| HTTP intercept | `AOE4H_HTTP_INTERCEPT` default 0 | Off (27072). Not WW. |
| Overlay UI / ImGui | Present draw | Titles are Relic swap-chain HWND, not `PID:` chrome. |
| PEB unlink hide | `RaHideInstall` — **PEB only** now | IAT/hash hide skipped (09:22/09:31 pack `0x56FD3C0`). Log: `[RA] hide: IAT patched=0 hash=0`. |

Current `DllInjector` CLI (2026-09-13): `--watch` / `-w`, `--patch-game` /
`--auto-patch`, `--no-elevate`. There is **no** `--bare`. Product inject
after HV hold uses `--patch-game` so overlay AUTO RUN is usermode hide.
*(This paragraph originally said watch-only; that is stale.)*

### Must stay off until `hold --apply` returns 0 **and** query/arm `status=0`

- Overlay inject **unless** hide-only is required for a non-HV hide_hold. Preferred HV order: **no** `InternalInjector` in the Relic module list during apply ([hold-before-dbg](2026-09-13-hv-hold-before-dbg.md) PIDs 53020 / 31656 / 15556: overlay not injected).
- RA neutralize, hasher plant, watcher/sibling `ret 1`, `--ra-veh` INT3, CRT cloak, FairPlay `.text`, FOW PAGE_GUARD on Relic.
- Visible `x64dbg.exe` (DualFlag pack — 42396 at 23:54).
- File→Attach / MCP `debug_attach_pid` (41064 death ~8s, EP can stay `0x48`).
- Online / ranked. Network Monitor hooks.

### May stay on

| Tool | Why |
|---|---|
| `WindowWatch.exe` Release | RPM of the ring + dbg retitle. **Not** a sibling needle (26508). `prove` classifies this as `hide_hold`, **not** `hv_hold`. |
| Steam `-dev -nodbg -notrap` | Debugger trap / no Relic trap handler. Does not empty WW. |
| Overlay PEB unlink | After inject; does not stub Watcher. |

Log after inject (if you inject at all): PEB unlink line + `[RA] neutralize` **OFF**. Old `[RA] hide ON retitle=N bodies=0` string is from a previous hide stack; current `ra_hide.cpp` does not print that.

---

## STEP 9 — Vs AI only; kill Relic on slots

Vs **AI** skirmish only. Offline tab scripts live in `Documents\AOE4HSettings\Scar Scripts\_system\_menu\Offline\`. Do **not** use Online tab / ranked / relicconnect matchmaking for this ritual.

`zpp_at.py match` DualFlag is **not** a vs-AI detector (`0x0100` = native companion, typical menu/skirmish without overlay write). Confirm vs AI in the Steam lobby UI.

**Any** `slots≠0` or `accum≠0` or `flag≠0`: **kill Relic immediately**. KickCtor `0x3E691F4` is already armed; the 2–3 min silent death is delayed, not optional ([ra-delayed-kick](2026-09-13-ra-delayed-kick-silent-death.md)). Exception: **STEP 10** unhidden-dbg observation (document, then kill).

Do not wait for WER. Do not `WindowClear` as a fix.

---

## STEP 10 — x64dbg coexistence

Order is **observation → HV execute-copy → hidden attach**. Do not skip the unhidden probe.

### A. Unhidden observation (deliberate; then kill)

1. Relic titled, window **empty**, **no** overlay if possible. WindowWatch may stay (RPM).
2. Close leftover rbhost `RuntimeBroker.exe`.
3. Open **visible** `x64dbg.exe` (stock / MCP host path). **Do not** `Start-X64dbgHidden.ps1` yet. **Do not** File→Attach / `debug_attach_pid`.
4. If slots fire (expected: `tag=0x20220002` `slots=3 accum=600` within seconds — 41064 / 43084 / 42396): **document** PID, image, CreationDate, WW line, dbg PID, then **kill Relic**.
5. That pack is sibling/title AT, not HashRec dest0.

Do not apply hold while this `x64dbg.exe` is visible (`hold --apply` rc=4).

### B. HV patch so the same chrome does **not** fill the ring

1. New Relic, Vs AI, empty ring, **no** dbg, overlay off.
2. Fail-closed checklist (STEP 8).
3. `python aoe4-hv\tools\zpp_at.py hold --apply` (or `wait-hold`). Arms ZPPN `--nop` (`eax=0xFFFFFFFF`) on Watcher-tag + INT3-retaddr `E8→Enqueue`; hasher `protect 0x3E57050` size `0x1000` skip dest `0x3E58000`.
4. Every `arm … status=` must be **0**. `status=8` = walk failed (C-bit / user DTB) — NPT execute-copy **not** armed. Identity still original; AT still packs. **Do not Attach.**
5. Re-open **visible** `x64dbg.exe` **without** hide. Ring must stay empty. That is the HV proof chrome. Then STEP 11.

### C. Hidden path (after execute-copy is proven)

`AOE4HOOK/tools/x64dbg-hidden/Start-X64dbgHidden.ps1` (elevated):

- Tree `C:\Program Files (x86)\rbhost\release\x64` (folder still named `x64dbg` = sibling pack).
- Payload gold in `_src\`; process leaf is bland (`RuntimeBroker.exe` / random 6-char).
- `CREATE_SUSPENDED` + `titleboot.dll` + resume (Watcher never sees `PID:`/`Thread:`/`Module:` on first paint).
- `Apply-X64dbgAoe4Ini.ps1`: `[Events]` all 0 (`EntryBreakpoint=0` — EP `0xCC` is attach INT3 pack `01010001`).
- ScyllaHide `AOE4_WindowHide` — **no** HookLibrary in Relic (`0x56FD3C0`).
- Soft-bind only: MCP `relicconnect` / `relicslots`. **No** File→Attach until HV hold is `status=0` **and** STEP 11 `hv_hold`.

`prove` `DBG_PROCESS` looks for leaf **`x64dbg.exe`**. Hidden bland names are **invisible** to `dbg_visible`. After switching to rbhost, `prove` will not report `hv_hold` even if the debugger is up — that is why STEP 11 uses the **unhidden** `x64dbg.exe` after apply.

Ini / bland history: [hide-fix-ww](2026-09-07-hide-fix-ww.md) (41064 attach=death; bland launch still `slots=3`; 53700 hold without attach).

---

## STEP 11 — 15s proof (do not fake)

Command (cwd `aoe4-hv`):

```text
python tools\zpp_at.py prove --sec 15 --name RelicCardinal.exe
```

Default in `zpp_at.py` is `--sec 20`. ADR-007 text says 60. **This STEP is 15s.** Longer is fine; shorter than 15 is not STEP 11.

### Fields to record (every prove)

From `match` + `window` + `prove` stdout (do not invent):

| Field | Source |
|---|---|
| `pid` `image` | `window pid=` `image=` |
| Relic `StartTime` | CIM (stale-session) |
| FileVersion | live PE |
| DualFlag `2D0/2D1/541` `classify=` `in_match=` | `match` |
| `slots` `accum` `flag` `begin` `end` | `window` |
| `dbg_visible=` list | `prove` (`DBG_PROCESS` leaves only) |
| `hide_process=` list | `prove` (`windowwatch.exe`) |
| `verdict=` | first print |
| `samples=` | loop (~15) |
| `empty=` stayed 1 | `prove OK` line |
| query `status` `cr3` `image_rpm` | `zpp_aoe4 query` if SVM live |
| overlay in modules? | Toolhelp `InternalInjector.dll` |
| process exit code | 0 / 1 / 2 |

### Real verdicts in `cmd_prove` (code, not a wish)

| `verdict` | Condition | Exit | Meaning |
|---|---|---|---|
| `hv_hold` | empty **and** `dbg_visible` **and not** WindowWatch | **0** | **GOAL** — execute-copy holding the ring with chrome up |
| `hide_hold` | empty **and** WindowWatch | **2** | Retitle hide, **not** HV |
| `watcher_pack` | dbg visible **and** ring dirty | **1** | Normal AT (42396 class) |
| `empty_no_dbg` | empty, no dbg leaf, no WW | **2** | Menu/skirmish without chrome — **not** proof |
| `ring_not_empty` | dirty, no dbg leaf | **1** | Packed fill / leftover KickCtor |
| `prove FAIL ring at sample=N` | left empty during the 15s | **1** | Fail |

`--sec 1` is a classify-only snapshot (empty without dbg still exits 2).

### Real recorded verdicts (do not treat as `hv_hold`)

| When | What actually printed / logged | Not |
|---|---|---|
| 2026-09-12 PID **29604** | `prove --sec 8` → `verdict=watcher_pack`, `dbg_visible=['x64dbg.exe']`, `hide_process=['windowwatch.exe']` | hv_hold |
| 2026-09-12 PID **47604** | 177/177 empty over **180s** (hide, DualFlag `0x0100`, **no overlay**) | prove/hv_hold |
| 2026-09-13 PID **15556 / 53020 / 31656** | window empty; `stealth --nop` **status=8**; hasher protect **never ran**; x64dbg **not** started | hv_hold |
| 2026-09-13 13:15 handoff | `prove --sec 60` / `verdict=hv_hold` **not complete**; ping later `ud` | hv_hold |
| This pass (~16:17) | SVM not resident (`launch_authorized=false`). **No** 15s prove was run. Running `prove` without Relic+apply=0 would be a fake. | — |

There is **no** recorded `verdict=hv_hold` on this host as of this note.

---

## Injector path (only)

```text
K:\aoe4_dlc\hh\AOE4HOOK\internal\x64\Release\DllInjector.exe
K:\aoe4_dlc\hh\AOE4HOOK\internal\x64\Release\InternalInjector.dll
K:\aoe4_dlc\hh\AOE4HOOK\internal\x64\Release\WindowWatch.exe
```

`Release|x64` only. DLL next to the injector. **Not** `Release_fowctrl`. LNK1104 = Relic still has the DLL mapped — say so, do not retarget OutDir. Elevate (`Start-Process -Verb RunAs`). One InternalInjector image per Relic. Log: `Documents\AOE4HSettings\Logs\aoe4_internal.log`.

APC contract: `NtCreateSection` path + `QueueUserAPC2` SPECIAL → `LoadLibraryW`. No CRT, no `CreateRemoteThread`.

---

## Plugins (only)

`Documents\AOE4HSettings` (typically `C:\Users\sshunko\Documents\AOE4HSettings`). Do **not** recreate `AOE4HOOK\plugins`, `AOE4HOOK-SCAR-Plugins`, or `Documents\ScarScripts`.

Vs AI: Offline tab under `Scar Scripts\_system\_menu\Offline\`. Files AUTO is opt-in. `checksum_wrappers.scar` / `local_rules.scar` prepended from `Scar Scripts\System\`.

---

## Checklists for later agents

### Before `hold --apply` / `wait-hold`

1. `cycle-state.json`: not `new_bsod`; `launch_authorized` true; user said **запускай**. Else **stop**.
2. `python tools\zpp_ctl.py ping` = pong (not `ud`).
3. `generic_hv.json` ops still 1–12. Game catalog `aoe4_16.3.11308.json` (or newer ver file).
4. No `x64dbg.exe` / CE / Olly in the process list. rbhost leftover killed.
5. Steam Vs **AI**, `-dev -nodbg -notrap`, titled Relic HWND (not attach-on-PID-create).
6. Overlay **not** in modules (preferred). `ra_neutralize=0`. No PAGE_GUARD. HTTP off.
7. STEP 8 table: PID, CreationDate, CR3/`status=0`, base, version `16.3.11308.0`, range, original bytes, unique sig, not stale, before-log.
8. `python tools\zpp_at.py window` → `slots=0 accum=0 flag=0` uninit/empty.
9. `python tools\zpp_at.py locate` → `sig_ok`. Inflated WW E8 at T+2s → wait for stable titled scan.
10. Then `hold --apply`. After: all arm `status=0`, hasher protect 0, window still empty. `status=8` = **do not** start x64dbg.

### Before x64dbg

1. Apply already **0** and ring still empty. Else kill Relic; do not Attach.
2. STEP 10A already documented (unhidden chrome packed once) **or** you are on the post-apply unhidden prove (10B).
3. For STEP 11 `hv_hold`: visible leaf `x64dbg.exe`, **WindowWatch killed**, overlay off, `prove --sec 15` exit **0**. Do not log `hide_hold` / `empty_no_dbg` as success.
4. Hidden `Start-X64dbgHidden.ps1` only **after** that prove. Ini Events=0. No HookLibrary in Relic.
5. Attach / `debug_attach_pid` only after 3+4. Soft-bind (`relicconnect`) if Relic must live without DebugPort.
6. Any slot → kill Relic now.

---

## Live delta ~16:35 (session 3305282e resume)

x64dbg tree is **`C:\Program Files (x86)\rbhost`**
(`Start-X64dbgHidden.ps1` → `release\x64`). Product proof is still
**unhidden** `x64dbg.exe`, not hidden rbhost.

PID **5012** hold was **20/39** `status=10`. Do not start any dbg on
that process. Cycle 3 ELF not mapped. See
[3305282e resume](2026-09-13-agent-session-3305282e-resume.md).

## Do not

- Map HV / `kdu -map` / `sc start Aoe4Hv` from this note
- Change mailbox 1–12
- Mix VAs across PIDs
- Plant Watcher / 7AB0 / hasher `--eax 1`
- Fake `hv_hold` from an empty menu or from WindowWatch hide
- Use `Release_fowctrl` or a second plugin tree
