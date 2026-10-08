# 2026-09-06 — VirusTotal on Steam `RelicCardinal.exe`

SHA256 **`5380c577805565817f528af6eac385263413fa6815553f9a31fa62561cb45e8c`**.
Same bytes as Steam
`C:\Program Files (x86)\Steam\steamapps\common\Age of Empires IV\RelicCardinal.exe`
and 60644 `modules_disk\RelicCardinal.exe` (`meta/crypt-compare.json`).
144 752 932 bytes / 138.05 MB. Product version **16.3.11308.0**.

GUI (2026-09-06, ~17:37 UTC reanalyze, still finishing sandboxes):

- [Detection](https://www.virustotal.com/gui/file/5380c577805565817f528af6eac385263413fa6815553f9a31fa62561cb45e8c/detection)
- [Details](https://www.virustotal.com/gui/file/5380c577805565817f528af6eac385263413fa6815553f9a31fa62561cb45e8c/details)
- [Behavior](https://www.virustotal.com/gui/file/5380c577805565817f528af6eac385263413fa6815553f9a31fa62561cb45e8c/behavior)
- [Community](https://www.virustotal.com/gui/file/5380c577805565817f528af6eac385263413fa6815553f9a31fa62561cb45e8c/community)

VT `/ui/` JSON needs a session / API key (`RecaptchaRequiredError`). API v3 pass 2026-09-06 (key used in-session only, **not** stored in repo / `dump/vt`).

## API v3 (same SHA)

Endpoints: `GET /files/{sha}`, `/comments`, `/behaviours`, `/behaviour_summary`, `/dropped_files`, `/contacted_domains`, `/contacted_urls`. `?fields=pe_info,packers,malware_config` returned **no** `pe_info` / `packers` / `malware_config` (VT did not index a full PE parse on this 138 MB file).

| Query | Result |
|-------|--------|
| comments | `data: []` `count: 0` |
| dropped_files | `count: 0` |
| contacted_domains / urls | `count: 0` (no live net) |
| packers | absent |
| crowdsourced YARA / IDS / Sigma on the file object | null |
| votes | 0 / 0 |
| times_submitted / unique_sources | 11 / 11 |
| reputation | 0 |
| last_analysis_stats | malicious 0, suspicious 0, undetected 69, type-unsupported 6 |

Sandbox verdicts: Zenbox **CLEAN** (98), C2AE **UNKNOWN_VERDICT**. CAPE has no file-level verdict field.

Local JSON (gitignored): `K:\aoe4_dlc\aoe4\gamesource\dump\vt\`.

## Community

**Comments (0)** in both GUI and API. Nothing to mine — no packer name, key, or unpack recipe.

Community score **0**. Detection **0 / 69** (no vendor flagged it). Tags: `peexe`, `idle`, `64bits`, `checks-user-input`.

## Details (what DIE/VT actually say)

| Field | Value |
|-------|--------|
| Magic | PE32+ GUI x86-64 |
| DIE | PE64; MSVC **19.36.34444** LTCG; linker **14.36.34444**; VS **2022 17.6** |
| TriD | Win64 EXE generic 51.9% (no packer family) |
| Signature | **File is not signed** (Authenticode empty — already true on disk) |
| Version | Relic Entertainment / Cardinal / `16.3.11308.0` |
| Names | `RelicCardinal.exe`, `The build server will stamp this field`, `--copyright` |
| x509 leftover | `battleserver.reliclink.com` (game TLS name, not a signer) |
| First seen | 2026-07-17 (this SHA). Last analysis 2026-09-06 17:37 UTC |

DIE on VT does **not** label VMProtect / Themida / UPX / SteamStub / Denuvo / Arxan. That matches [disk-crypt](2026-09-06-relic-disk-crypt.md): brand-less in-place `.text`, normal MSVC IAT, CRT EP on disk.

Hashes VT printed (same file):

- MD5 `faaffd80e4a6e6e6caa4db2d4944a9cd`
- SHA-1 `17b5365d44f15d94b8416a695c28e3fb76f38a3a`
- Authentihash `58190c3e0564ca6c1ce904da60042323cc5c47a459938be328b68f092d41b5fa`

## Behavior (C2AE + CAPE + Zenbox)

Banner: some sandboxes still running. Activity summary already settled:

| Bucket | Result |
|--------|--------|
| Detections | NOT FOUND |
| Dropped Files | **NOT FOUND** |
| Network comms | NOT FOUND |
| IDS / Sigma | NOT FOUND |
| MITRE | T1056 Input Capture (info) ×2 — Credential Access + Collection. T1071 Application Layer Protocol only in the mixed view (HTTP strings in the image, no live C2) |
| CAPE badge | 1 |
| Zenbox badge | 2 |
| Behavior tags | `checks-user-input`, `idle` |

**Processes created (VT list):** only `"C:\Users\user\Desktop\RelicCardinal.exe"`.

Files opened: `IPHLPAPI`, `WINHTTP`, `bcrypt`, `d3d11`, `d3d12`, `dxgi`, common-controls. Registry: Session Manager / Segment Heap / WinSxS / Safer. Memory-pattern domains: Xbox Live / Autodesk FBX / office.com consent / relaxng — **SDK strings in the PE**, not a packer C2.

Memdump / EVTX artifact MD5s on the page (`7eb58e30…`, `e254b7be…`, `5a417269…`) are **sandbox dumps**, not Relic drops. They are worse than 60644 `modules_runtime\RelicCardinal.exe.memory.bin` (full in-place plaintext after Steam launch).

## Process tree (API, not a Relic drop chain)

C2AE `processes_tree` is **exactly** the first three lines the user pasted — Relic is **not even in that sandbox’s tree**:

```
2892  %windir%\system32\wbem\wmiprvse.exe
2752  %TEMP%\E0ZFDKNNQIC5C0AI.exe
2820  wmiadap.exe /F /T /R
```

Grouped `behaviour_summary` then appends Relic as a **sibling**:

```
6388  "C:\Users\user\Desktop\RelicCardinal.exe"
      files_opened: IPHLPAPI, WINHTTP, bcrypt, d3d11, d3d12, dxgi, common-controls
```

- `wmiprvse` + `wmiadap /F /T /R` = WMI provider + adapter rebuild. C2AE VM noise.
- `%TEMP%\E0ZFDKNNQIC5C0AI.exe` = C2AE helper. Not a child of Relic. `dropped_files` count 0.
- Relic decrypts `.text` **in-place**. It does not write a second PE.

Zenbox: only Relic created; tags `CHECKS_USER_INPUT` + `IDLE`; missing DLLs include **`steam_api64.dll`**, `libhttpclient.win32.dll`, `tensorflowlite_c.dll`, `bugsplat64.dll`, `amd_ags_x64.dll`, d3d11/12, winhttp, bcrypt, … — Desktop copy without the Steam game folder. Arxan never finishes.

CAPE signature (only “detection”): YARA `shellcode_stack_strings` → MITRE T1071 medium. Generic stack-string rule, not a packer family. Zenbox T1056 = `DirectInput8Create` (game input). Other Zenbox hits are PE trivia we already have: imagebase `0x140000000`, `.text` raw `0x56dd000`, extra sections `_RDATA` / `.rodata`, HIGH_ENTROPY_VA+ASLR+NX, only `.text` executable.

`idle` + `checks-user-input` = no Steam / SGA. VT memdump slices (`*.sdmp`, many 4 KiB–10 MiB at `0x7FF7…`) are idle Desktop mappings — worse than 60644 `modules_runtime\RelicCardinal.exe.memory.bin`. Do not download them.

## Does VT help decrypt?

**No.** It confirms identity (this SHA = our Steam disk) and the negative (not VMP-branded, not signed, no dropper). Decrypt of `.text` stays: live 60644 image / `RelicCardinal.unpacked_analysis.exe` / `unpack-disk`. Overlay 10 MiB is decoded by our AEAD (`rediscover`), not by VT. 13 AES map luas stay locked. Do not treat the TEMP exe or VT memdump as a second unpacker.

Do not reanalyze / download CAPE artifacts as a substitute for the runtime IDB.
