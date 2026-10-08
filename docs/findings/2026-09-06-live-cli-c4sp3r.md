# 2026-09-06 — Live Relic `-dev -nodbg -notrap`, leftover 100%, C4SP3R

User: do the leftover-100% / heartbeat / MiniDump / Steam-IDA / C4SP3R
list plus live CLI confirm. Hex-Rays worker left alone.

## What actually ran

| Ask | What we did |
|---|---|
| Leftover → 100% | `python -m unpacker splice-gold --all` — **9/9** live PEs **100%** after leftover lift. Disk XOR stays in `unpacked_static.exe`. Unlock PRNG is **not** simulated; this is splice, not a third cipher |
| Heartbeat / plant | Overlay `--dev` only. Log: `RA neutralize skipped (Relic .text banned)`. **No** 7AB0 / FlushArm / Watcher `.text` stub |
| MiniDump live Relic | **Not** `MiniDumpWriteDump` on the live PID. PSS clone planned; Relic died after slots=3 (background x64dbg), before the dump |
| Steam-exe in IDA | **Not opened.** Cipher `.text`. Hex-Rays still owns `runtime_exe.i64` (~331k / 535k) |
| C4SP3R | Elevated `AoE4 Functions by C4SP3R.exe`. Relic already had slots=3. Death is Watcher, not the name scrape |
| Live CLI | Steam `-applaunch 1466860 -dev -nodbg -notrap`. PID **39056** |
| Overlay | Elevated `DllInjector.exe --dev --no-pause`. Present + ImGui up. Relic survived inject |

## PID 39056 (this process)

| | |
|--|--|
| Start | 23:14:29 |
| Relic base | `0x7FF7E43A0000` (new ASLR — **do not mix VAs**) |
| SizeOfImage | `0x8C3D000` |
| Cmdline | `"…\RelicCardinal.exe" -dev -nodbg -notrap` |
| Seed RVA `0x7AF7688` | `0xFDFDFBCD1B3F5D7B` |
| RA at menu | **slots=3** accum=600 **before C4SP3R** (first probe 23:16:12). Cause: **x64dbg already open in the background** — Watcher title/process match. This session did not launch x64dbg; a leftover instance was enough |

### Layer B / `Misc_IsDevMode` (first live step)

Probe **before** inject (`23:16:12`):

| Byte | RVA | Value | Meaning |
|---|---|---|---|
| `g_Dev_NoDbgFlag` | `0x844B2ED` | **0** | `-nodbg` is on the line; flag is **lazy** — `Dev_NoDbg_Check` had not run (`parsed` `0x85A6C39` = 0) |
| `g_Dev_NoDbgParsed` | `0x85A6C39` | **0** | first call not taken |
| `Misc_IsDevMode` | `0x84421BC` | **1** | Relic itself, **before** overlay. One sample with `-dev`; no no-`-dev` control tonight |
| cmdline ready | `0x844B2EF` | **1** | Layer A table ready |

Probe **after** inject (`23:16:50`): nodbg flag **1**, parsed **1**. Overlay log: `[DevBypass] -nodbg forced (RVA 0x844B2ED, was 0)`.

So Steam `-nodbg` is **not** an eager write. Overlay `DevForceNoDbg` is still required if nothing has called `Dev_NoDbg_Check`. Trap skip at boot still uses `strstr(" -notrap")` on the raw line — that path does **not** need the byte.

## Leftover 100% (splice)

`meta/unpacker-splice-gold.json` `allHundred=true`. Wrote:

- `RelicCardinal.unpacked_gold.exe` (52968)
- `RelicCardinal.unpacked_gold_live_60644_memory.exe`
- `RelicCardinal.unpacked_gold_bin_52968_t20.exe`

100% vs **that** live `.text`. Next session’s leftover will differ (RA).

## XOR names (60644 live image vs disk)

`Harvest-XorNames.py` → `aoe4\gamesource\meta\xor-names.json`.

| | |
|--|--|
| SCAR docs names | 3190 |
| Plaintext in live **and** disk | 184 |
| Live plaintext, disk still XOR | **1877** |
| Missing from live image | 1131 (`Util_GetCommandLineArgument` is one) |

Key is **`0x8B XOR index`**: `Game_IsRTM` at RVA `0x77A2961` disk `cc eb e4…` ⊕ live = `8b 8a 89 88 8f 8e 8d 8c 83 82 81`. Same stream on `AI_IsRTM` `0x78198B1`, `Misc_IsDevMode` `0x77A2591`, `Misc_IsCommandLineOptionSet` `0x77A24B1`, `Game_IsCommandLineOptionSet` `0x7794D31`. unpack-disk does **not** apply this.

## Death: slots=3 from background x64dbg (user confirm)

User: Relic died because **slots=3**, because **x64dbg was already open** when Relic started.

Timeline agrees. First RPM (`23:16:12`) already had slots=3 / accum=600. Overlay inject at `23:16:42` did **not** kill it. C4SP3R started `23:17:06`. We did not `Start-Process` x64dbg this turn (`run_unpacker_live_cycle` was not used). A leftover x64dbg window/process is enough for WindowWatcher (`x64dbg` in the title or image name). `-nodbg` / overlay hide do **not** clear those slots.

C4SP3R (pid 40056) is a name scrape. It still does not add Layer A/B tokens. Next live cycle: **close x64dbg first**, then Steam, then inject. Do not bait Watcher.

## Do not (still)

- Open Steam `RelicCardinal.exe` in IDA
- `MiniDumpWriteDump` the **live** Relic (PSS clone only; not taken — process died)
- Plant 7AB0 / hasher / Watcher `.text` (36000 / JUMPOUT)
- Second-open `runtime_exe.i64` while Hex-Rays runs

## Clean retry PID 52920 (2026-09-06 23:21)

User: do it again. Closed leftover **x64dbg**, **C4SP3R**, and both **WindowWatch** (26896 / 44680) *before* Steam. No dbg launch.

| | |
|--|--|
| Start | 23:20:12 |
| Relic base | `0x7FF7E64B0000` (**do not mix** with 39056 / 60644) |
| Cmdline | `"…RelicCardinal.exe" -dev -nodbg -notrap` |
| Seed | `0xFDFDFBCD1B3F5D7B` |
| RA before inject | **slots=0** accum=0 `uninit/empty` |
| RA after inject | **slots=0** still |
| nodbg byte | 0 → 1 (`DevForceNoDbg`) |
| `Misc_IsDevMode` | **1** again before overlay |
| Overlay | hide ON retitle=1; neutralize skipped; `UiD3D12Init ok` hwnd `0xC414E4` |

Relic **alive**. Do not open x64dbg / C4SP3R / WindowWatch on this PID if we want slots to stay 0.

## Hold 52920 (2026-09-06 23:32) — overlay only, slots empty

User: overlay as now, nothing planted, slots empty.

RPM: begin=end=0, accum=0, flag=0, **slots=0** `uninit/empty`. Overlay log
still `RA neutralize skipped (Relic .text banned)`, hide ON, no Relic
`.text` stub. Closed leftover WindowWatch **54060** (started 23:21:10;
slots stayed 0 the whole time). No inject, no plant, no dbg.

## 52920 gone — live 26976 (2026-09-06 23:40:45)

Same ASLR `0x7FF7E64B0000`. Probe-only kick-emu: **slots=0**, SNAP
windows match 43676. No write flags.
[ra-kick-emu](2026-09-06-ra-kick-emu.md).
