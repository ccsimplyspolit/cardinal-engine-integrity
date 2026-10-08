# 2026-09-06 — Inject crash (PID 37124) then FairPlay off Relic `.text`

Symptom note: [2026-09-06-inject-37124-crash.md](2026-09-06-inject-37124-crash.md).  
Hasher: [2026-09-06-ra-hasher-windowwatcher.md](2026-09-06-ra-hasher-windowwatcher.md).  
FairPlay layer: [2026-09-06-fairplay-block.md](2026-09-06-fairplay-block.md).

## Crash

| Field | Value |
|-------|--------|
| PID | **37124** (`0x9104`) |
| Relic base | `0x7FF6F92A0000` (16.3.11308.0) |
| Inject | 16:42:43 OverlayBoot |
| Crash | 16:42:44 Event 1000; dump 16:42:46 |
| Class | BEX64 **`0xC0000005`**, fault module `unknown`, offset `0` |
| Dump | `%LOCALAPPDATA%\CrashDumps\RelicCardinal.exe.37124.dmp` (110 494 097 bytes) |
| Thread | 37736 (`0x9368`) |
| `.ecxr` | **RIP=0 RSP=4 RBP=4 RSI=0** — JUMPOUT-style fail (`xor rax/rsi; mov rsp,rax; mov rbp,rsi; jmp rax`) |
| Overlay last line | 16:42:43.835 first Present FPS spike — then gone (~1 s) |
| Cloak | **OFF** (not the 16:23 `0x10E` path) |
| Slots | uninit / empty |

Log had **all FairPlay Relic `.text` 14-byte abs-jmps ON**: `0x2EFD750` / `0x30B61F0` / `0x40D5030` / **`0x40D4E50`** / `0x300E030` / `0x2F4E310`. Hide (user32) + watcher neutralize survived earlier injects. New this DLL vs last good neutralize = those Relic `.text` stubs.

`RA_Hasher` `0x3E57050` raw-loads live Relic `.text`. 14-byte `FF 25` on Relic image is hasher-visible → JUMPOUT / BEX64. Watcher `ret 1` on Relic `.text` was previously survived — left in place.

Did **not** inject again after this dump. Relic dead.

## Fix (this turn)

**Removed** all Relic `.text` FairPlay/ESS/maelstrom jmps.

**Added** in-process HTTP intercept (not Relic `.text`, not Relic IAT `0x20DE00AD`, not CRT memcpy):

| Layer | What |
|-------|------|
| **winhttp.dll / wininet.dll export bodies** | Connect / OpenRequest / Send / Write — filter URL+body |
| **libHttpClient.Win32.dll** | `HCHttpCallRequestSetUrl` / `SetRequestBody*` / `PerformAsync` (FairPlay XSAPI) |
| **hosts fallback** | `reputation.xboxlive.com` only (`tools/fairplay_hosts.ps1`) |
| **mitmproxy** | Optional debugger only if Relic does **not** pin TLS. Not required. |

Filter:

- `reputation.xboxlive.com` + `/feedback` / FairPlay types → rewrite body `{}` (libHttp Perform skip on drop)
- `POST /game/party/reportMatch` → strip `appBinaryChecksum` / `dataChecksum` / `modDLLChecksum` / `checkSums`, log key names (not wholesale JSON)
- maelstrom/eventbatch **only** if body has FairPlay/tamper/cheater → `{"events":[]}`
- **Pass** XBL login / title / session / party create-join; never hosts-block `*.xboxlive.com` or `aoe-api.worldsedgelink.com`

Keep: user32 hide, watcher neutralize, FairPlay* `.rdata` zero, VACBanned `.data` + Steam IAT wrap. Cloak OFF.

Boot lines: `[RA] http intercept ON` + `[RA] FairPlayTampering block ON http=1 hosts=0/1 text=0`.

Admin once if hosts write fails: `AOE4HOOK\tools\fairplay_hosts.ps1 -Apply` (optional `-Firewall`). `-Restore` removes only the marked block.

## PID 27072 (16:53) — HTTP intercept ON, still JUMPOUT

Second crash after Relic `.text` FairPlay jmps were removed. **Not** a mix of the old stubs.

| Field | Value |
|-------|--------|
| PID | **27072** (`0x69C0`) |
| Relic base | `0x7FF635B40000` (hasher hide `va=0x7FF635F97050` = `+0x3E57050`) |
| Inject | 16:53:29 OverlayBoot; DLL `InternalInjector.dll` 16:51:55 (13 479 424 bytes) |
| Crash | 16:53:30 Event 1000; dump 16:53:32 |
| Class | BEX64 **`0xC0000005`**, fault module `unknown`, offset `0`, P9=`8` |
| Dump | `%LOCALAPPDATA%\CrashDumps\RelicCardinal.exe.27072.dmp` (110 745 606 bytes) |
| Thread | 35912 (`0x8C48`) |
| `.ecxr` | **RIP=0 RSP=4 RBP=4 RSI=0** — same JUMPOUT as 37124. `r15=0x7FF635F5639C` (Relic `+0x41639C`) |
| Relic after | **dead**. DllInjector down. |

Log (Documents `aoe4_internal.log`; no `%TEMP%\aoe4_internal.log`):

- `cloak=off` / `[RA] integrity cloak OFF` / xbox `text=0` / `hasher=off`
- hide user32 body 3 + PEB unlink + neutralize ON (inline-ret+VEH+5byte) — historically survived
- **`[RA] http intercept ON hooks=12`** winhttp=1 wininet=1 libhc=1
- hooked lines all `stolen=14` except CloseHandle/HttpSendRequestW/HCHttpCallPerformAsync `stolen=15`
- first Present 16:53:29.989; hasher hide Present-arm threads=98; FPS spike 16:53:30.094; gone

`xbox_enforcement.cpp` has **zero** Relic `.text` plants (strings / Steam IAT / hosts only).

### Cause

1. **Dump class = JUMPOUT** (hasher-style `RIP=0`), not a winhttp trampoline RIP. Neutralize still writes Relic `.text`; hasher hide Present-arm is in `mp_bypass` (UTF-16).
2. **HTTP ABI is still unsafe.** `MeasureStolen` fell back to **14** when `InsnLen` stopped short. Live `WinHttpConnect` prologue `40 55 53 56 57 41 54 41 55 41 56 41 57 48 8D AC` decodes **13** push/rex bytes then `LEA` — a 14-byte `FF 25` splits the LEA. Same pattern on OpenRequest/Send/Write/InternetConnectW/HttpOpenRequestW and several HC exports.
3. `HCHttpCallPerformAsync` skip (`return S_OK` without completing the async block) is fail-closed vs XSAPI.

### Fix (no inject in the diagnose turn; elevated inject after rebuild)

- Default **`AOE4H_HTTP_INTERCEPT=0`**: `HttpInterceptInstall` logs `http intercept OFF` and plants **zero** export bodies. Network Monitor rule table stays.
- `MeasureStolen` returns **0** (skip) unless 14–16 insn-aligned; skip `E9`/`E8`/`CC`/`FF 25`.
- Do **not** `LoadLibrary` winhttp/wininet from boot.
- HC Perform **fail-open** (always call original).
- Cloak off. No Relic `.text` FairPlay. No `--ra-veh`. DllInjector / Steam-cycle **`Start-Process -Verb RunAs`** (no medium-IL `0x000002E4`).

## PID 15504 (17:02) — intercept OFF, still JUMPOUT

Elevated inject of the fail-open HTTP DLL (`http intercept OFF`, `text=0`, cloak off). x64dbg was **already attached** (`RelicCardinal.exe - PID: 15504`).

| Field | Value |
|-------|--------|
| PID | **15504** (`0x3C90`) |
| Crash | 17:02:07 Event 1000; dump 17:02:09 |
| `.ecxr` | **RIP=0 RSP=4 RBP=4 RSI=0** again. `r15=0x7FF635F5639C` (same Relic `+0x41639C` as 27072) |
| Dump | `%LOCALAPPDATA%\CrashDumps\RelicCardinal.exe.15504.dmp` |
| Last overlay | 17:02:06.846 first Present FPS; hasher hide Present-arm threads=94 |

HTTP export-body hooks were **not** the only JUMPOUT trigger. Remaining Relic `.text` writers: neutralize inline-ret+VEH+5byte + hasher hide Present-arm DRx.

### Follow-up fix

`AOE4H_RA_TEXT_NEUTRALIZE=0`: `MpBypassInstallRaNeutralizeInternal` plants **nothing** (sticky refuse). Present-arm DRx gated off. **user32 hide stays.** Cloak off. HTTP intercept stays OFF.

## PID 7764 (17:05) — Present lived (no JUMPOUT)

Elevated inject (`Start-Process -Verb RunAs`, no `--ra-veh`). x64dbg was **not** attached (title stayed `x64dbg [Elevated]`; injected after ~45s).

| Field | Value |
|-------|--------|
| PID | **7764** |
| OverlayBoot | 17:05:56.130 |
| DLL | `InternalInjector.dll` 17:04:29 (13 900 800 bytes) |
| HTTP | `http intercept OFF` `http=0` `text=0` cloak off |
| Neutralize | `neutralize OFF` (fail-open); `hasher hide` **not** armed |
| Hide | user32 body 3 ON |
| Present | first call 17:05:56.636; FOCUS 17:05:56 / 58 / 00 / 02; **fps=74** present=8.35ms |
| JUMPOUT | **none**. No new WER. No Event 1000. |

Then `[RA] hot edge slots=7 accum=600 installed=0 healthy=0` (WindowWatcher) and Relic exited **without** a dump — expected with Relic `.text` neutralize off while x64dbg / chrome titles are visible. That is a **kick**, not the 1s BEX64.

Relic **dead** after the WW edge. Present survived the inject window. Next experiment if they need both: watcher+sibling `ret` only, **no** hasher hide Present-arm / d02c/f448/enqueue plants.

## PID 36000 (17:14) — watcher+sibling `ret 1` only; IAT pack kick

Crash-catch: x64dbg PID **17584** already elevated + ScyllaHide `AOE4_WindowHide`. Steam `-applaunch 1466860 -dev -nodbg` (elevated). MCP `debug_attach_pid` **before** inject, TLS BPs disabled, first-chance `0xC0000005`, then elevated `DllInjector.exe` (no `--ra-veh`). WindowWatch PID 3448 stayed open.

| Field | Value |
|-------|--------|
| PID | **36000** |
| Relic base | `0x7FF7CBD20000` (16.3.11308.0) |
| OverlayBoot | 17:14:27.996 |
| DLL | `InternalInjector.dll` 17:13:24 (13 900 288 bytes) `Release\|x64` |
| HTTP | `[RA] http intercept OFF` `text=0` |
| Hide | user32 body 3 ON |
| Neutralize | **ON** watcher=`0x7FF7CFC2A7D0` (=base+`0x3F0A7D0`) sibling=`0x7FF7CFC528D8` (=base+`0x3F328D8`) `B0 01 C3` only. No hasher VA, no Present-arm DRx, no d02c/f448/enqueue/timerq/kick/45E8/thunk |
| Boot drain | timer list head `00000243460AF8E0` zeroed; `slot sink cleared slots=11 accum=600 flag=1` (WW pack already in `.data` before inject) |
| Engine cloak | `IntegrityCloak::Install` shadow copy of Relic image (`cloak=1 cloakGuard=0`) — **not** CRT memcpy splice |
| Present | first FOCUS 17:14:28.683; imgui=Y 17:14:30.680; **fps=71.3** 17:14:32.266 |
| Last overlay | 17:14:32.679 FOCUS — then gone (~4 s) |
| WER / Event 1000 | **none** this window (latest dump still 15504 @ 17:02) |
| x64dbg | attached, running; after death `state=stopped`. No first-chance `0xC0000005`. **Kick, not JUMPOUT.** |

Watcher pack **did not return** after the stubs (`tag=0x20220002` / `accum=600` absent). Instead hasher/IAT packed:

| t | slots | accum | tag | `+10` RVA |
|---|-------|-------|-----|-----------|
| 17:14:31.696 | **4** | 0 | `08050001` | `0x56FD380` kinds 6/3/1/5 |
| 17:14:32.257 | **8** | 0 | + `08060001` | `0x56FD3C0` same kinds |

This is the known **3-byte Relic `.text` `B0 01 C3`** signature from [CHECKSUM_AUDIT](../CHECKSUM_AUDIT.md): latch/GpuUpload plants packed `slots=4 / 0x56FD380` in ~3 s. Watcher+sibling `ret 1` is the same 3-byte write. `installed=1 healthy=1` — stubs stayed; hasher still saw them.

**Survived >30s Present?** No. **slots stayed 0?** No.

**Do not** add hasher hide / enqueue fail / HTTP / FairPlay `.text` from this. Next lever is **not** more Relic `.text` (hasher-visible). Hide + ScyllaHide already on; IAT pack is the remaining kick while dbg/WindowWatch stay open.
