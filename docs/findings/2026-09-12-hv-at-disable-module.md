# HV AT-disable plug-in (catalog + zpp_at.py)

Date: 2026-09-12. Tree: aoe4-hv + AOE4HOOK finding. Game 16.3.11308.0.

## Goal vs reality

User goal: one HV plug-in that finds **all** anti-tamper checks and disables
them for unrestricted game modification.

**Not achievable as stated.** Relic AT is layered (RA window, Watcher, 45E8
cloak, hasher, 7AB0, FairPlay/ESS HTTP, debugger trap). HV canon forbids
planting Watcher/7AB0/.text from the ELF. ZPPN stealth on WindowWatcher
**IAT-kicks** the process. Hasher still **reads** original bytes on identity
nCR3. Server-side FairPlay is not disabled from the guest.

## What we built (plug-in v0)

| Piece | Path |
|---|---|
| Catalog (hasher family + Watcher/nodbg; FairPlay out of HV) | `aoe4-hv/tools/zpp_aoe4/at_catalog.json` |
| Usermode agent CLI | `aoe4-hv/tools/zpp_at.py` (`list`, `plan`, `hasher`, `mitigate`, `scan`, `arm`) |
| ADR | `aoe4-hv/docs/decisions/006-at-disable-module.md` |
| ZPPX channel | existing `zpp_aoe4.exe` hello + read_virt |

`zppn_sites[]` and all `zppn_arm` flags are **false/empty** until a site is
validated offline. `arm` is wired (no-op until whitelist populated).
`mitigate` prints the overlay + hosts recipe per layer.

## Usage

```text
set ZPP_HYPERCALL_KEY=0x...   rem from zpp key= in loader log
python aoe4-hv\tools\zpp_at.py hasher
python aoe4-hv\tools\zpp_at.py list
python aoe4-hv\tools\zpp_at.py plan
python aoe4-hv\tools\zpp_at.py mitigate
python aoe4-hv\tools\zpp_at.py scan   rem Relic + HV key
python aoe4-hv\tools\zpp_at.py arm
```

Real mitigation today: **overlay** `DllInjector` (`-dev -nodbg`, hide,
neutralize Watcher ret1, mp_bypass). HV adds optional ZPPM hide / ZPPN on
**whitelisted** sites only.

## Hasher: plant vs NPT hook (2026-09-12 later)

User: hasher **can** be hooked. The overlay ban was **14-byte plant** in
Relic `.text` (prologue sits in a hashed range; `RA_Hasher` raw-loads
`[rcx]`). That is not an HV ZPPN ban.

| Hook | Allowed | Why |
|---|---|---|
| Overlay `FF 25` on `0x3E57050` | no | other hashers / 45E8 see the plant |
| HV ZPPN execute of `0x3E57050` | **yes** | identity PFN stays original for data reads |
| ZPPN builtin `--eax 1` on hasher | **no** | RAX is 64-bit wyhash; `cmp rax,[obj+0x10]` misses -> JUMPOUT |
| ZPPN whole `45E8` `ret 1` | no | boot-kill (cloak/unlock skipped) |
| FairPlay HTTP in HV | no | overlay/hosts only |

Preferred: hasher still **runs** (or a real handler) while patched pages
keep a golden identity PFN so the hash matches stored `[obj+0x10]` /
`[obj+0x18]`. `python tools/zpp_at.py hasher`

## Live test 2026-09-12 16:01 (PID 47604)

Relic `0x7FF614B70000` Responding. HV ping `pong cpu=5 host_tsc=0`. **No remap. No arm.**

| Check | Result |
|---|---|
| `zpp_aoe4 ping` | ok `host_tsc=0` |
| `zpp_aoe4 query RelicCardinal.exe` | `status=8 not_found` `image=0` |
| `zpp_at.py scan` (ZPPX read) | blocked by query |
| `zpp_at.py scan-rpm` | all 16 RVA sites readable; Relic stayed up |
| `dispatcher_7ab0` | `sig_ok` |
| `hasher_raw` `0x3E57050` | `48 89 5C 24 20 57 48 83 EC 30 ...` (10-byte insn-aligned; builtin stub would fit) |
| `-nodbg` `0x844B2ED` | `00` (overlay not forcing) |
| RA window begin/flag | `0` (empty) |

Query miss: `eprocess_is_target` required shared `target_image_name[0]` which is empty unless ZPPH. Mailbox `push_probe_name` was ignored. Fix in `hypervisor.cpp` is **coded, not mapped** (do not remap this boot).

Did **not** ZPPN-arm hasher (`--eax 1` still forbidden). Next map: query then ZPPX scan; hasher hook needs a handler, not eax=1.

## Plant ban vs NPT patch (same day)

The overlay rule "do not 14-byte hook hasher `0x3E57050`" is **not** a ban on HV patching.

It forbids a **guest store** into Relic `.text` (`FF 25` / `EngineWriteRelicText`). Hasher raw-loads `[rcx]`; identity NPT is `trap_execute` = R=1 **W=1** X=0, so those stores still hit the original PFN. Other hashers then see the plant -> JUMPOUT/BEX64.

| Patch | Hasher sees it? | Use |
|---|---|---|
| Overlay/guest 14-byte plant | yes (identity W=1) | keep forbidden |
| ZPPN stub on stealth nCR3 only | no (identity PFN unchanged) | allowed |
| Overlay plant + ZPPN without write-split | still yes | still forbidden |

We do **not** lift the plant ban on this mapped ELF (identity still W=1).
Write-split is **coded** (`stealth_protect_va`, identity W=0, write NPF ->
stealth copy 1 insn, `mailbox_op_protect` / `zpp_at.py protect`). Not mapped.
After the next map: `protect` hasher/.text pages, then overlay plant is
hasher-invisible. Do not arm protect on this Relic.



