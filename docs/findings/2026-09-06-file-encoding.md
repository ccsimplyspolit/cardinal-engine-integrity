# 2026-09-06 — workspace text encoding (UTF-8 no BOM)

Agents / editors had mixed encodings (UTF-8, UTF-16-LE, UTF-8 BOM, stray C1 bytes). Canon for this tree:

| Kind | Policy |
|------|--------|
| Source / docs / skills / rules | **UTF-8 without BOM** (matches MSVC `/utf-8` on `InternalInjector` / `Standalone` / `LauncherTests`) |
| `mp_bypass.cpp` / `mp_bypass.h` | **Intentional UTF-16-LE, no BOM** — do not convert |
| `Documents\AOE4HSettings` | Do not mass-convert; fix only files this session wrote with bad encoding |

PowerShell 5.1 `Out-File -Encoding UTF8` writes **UTF-8 with BOM**. Use `[System.Text.UTF8Encoding]::new($false)` / `WriteAllBytes` when saving from PS.

## Method

Walked `k:\aoe4_dlc\hh` text extensions (`.cpp` `.h` `.hpp` `.c` `.cs` `.lua` `.scar` `.py` `.md` `.json` `.ini` `.xml` `.rc` `.def` `.ps1` `.bat` `.cmd` `.yml` `.yaml` `.txt` `.cmake` `.vcxproj` `.sln` `.filters` `.props` `.targets` `.editorconfig` `.mdc`).

Skipped: `.git`, `node_modules`, `graphify-out`, `.vs`, `__pycache__`, `obj`, `bin`, `x64\Release` / `Debug` / `Release_fowctrl`, binaries / dumps / IDB.

Detection: BOM, UTF-16 NUL density, strict UTF-8, then `charset_normalizer` for leftovers.

Scanned **~2836** text files. Almost all already valid UTF-8 no BOM.

## Inventory (non-UTF-8 / BOM)

| Path | Was | Action |
|------|-----|--------|
| `AOE4HOOK\internal\InternalInjector\mp_bypass.cpp` | UTF-16-LE no BOM | **keep** |
| `AOE4HOOK\internal\InternalInjector\mp_bypass.h` | UTF-16-LE no BOM | **keep** |
| 4× `_arhive\...\mp_bypass.cpp` + 4× `.h` | UTF-16-LE no BOM | **keep** (same exception) |
| `AOE4HOOK\docs\HYBRID_NATIVE_AUDIT.md` | ASCII + 12× `0x9D` (not CP1251) | latin-1 → UTF-8 |
| `AOE4HOOK\internal\InternalInjector\d3d12_capture.cpp` | UTF-8 BOM | strip BOM |
| `AOE4HOOK\internal\InternalInjector\d3d12_capture.h` | UTF-8 BOM | strip BOM |
| `.cursor\skills\radare2\scripts\recon.ps1` | UTF-8 BOM | strip BOM |
| `.agents\skills\radare2\scripts\recon.ps1` | UTF-8 BOM | strip BOM |
| `_arhive\SCHEME.txt` | UTF-8 BOM | strip BOM |
| 4× `_arhive\...\CardinalLuaInjector.sln` | UTF-8 BOM | strip BOM |
| 4× `_arhive\...\main.cpp` (uc scar injector) | UTF-8 BOM | strip BOM |
| 4× `_arhive\...\d3d12_capture.cpp` + 4× `.h` | UTF-16-LE no BOM | → UTF-8 |

`charset_normalizer` labeled `HYBRID_NATIVE_AUDIT.md` as Windows-1251. That is wrong: the only high bytes are twelve `0x9D` C1 leftovers (broken dash / table mark). Decoding as 1251 would invent `ќ`. Converted as latin-1 so the file is valid UTF-8; the twelve `U+009D` characters remain (no content rewrite).

This session’s findings (`2026-09-06-fairplay-vs-ra.md`, `…-ce-lua-path.md`, `…-ra-hasher-windowwatcher.md`, `…-vs-mcp-sse-autostart.md`, `…-bsod.md`, `…-ida-ra-analysis.md`) were already UTF-8.

## Converted (22)

**Live tree (5):**

1. `AOE4HOOK\docs\HYBRID_NATIVE_AUDIT.md`
2. `AOE4HOOK\internal\InternalInjector\d3d12_capture.cpp`
3. `AOE4HOOK\internal\InternalInjector\d3d12_capture.h`
4. `.cursor\skills\radare2\scripts\recon.ps1`
5. `.agents\skills\radare2\scripts\recon.ps1`

**`_arhive` copies (17):** `SCHEME.txt`, four `CardinalLuaInjector.sln`, four injector `main.cpp`, four `d3d12_capture.cpp` + four `.h`.

Line endings left as found (CRLF on Windows sources). No `/utf-8` project change.

## Intentional exceptions (keep UTF-16-LE, no BOM)

- Live: `AOE4HOOK\internal\InternalInjector\mp_bypass.cpp`, `mp_bypass.h`
- Archive mirrors (not converted): `_arhive\incoming\_incoming\ScarScripts3\source\InternalInjector\`, `_incoming_tester_scars\…`, `_scar_dev_handoff\…`, `_arhive\tmp\.codex-publish-aoe4hook-submodule\internal\InternalInjector\`

## Refused / not touched

| What | Why |
|------|-----|
| `Documents\AOE4HSettings` | Not mass-converted. Today’s overlay seeds (`PLUGINS.md`, `AI Profiles\README.txt`, `Config\*.ini`) already UTF-8; no session-written scars with mojibake |
| `.dll` `.exe` `.pdb` `.obj` `.lib` `.idb` `.i64` `.id0` dumps | Binary |
| `graphify-out`, `node_modules`, `.git`, `x64\Release` | Cache / VCS / build output |
| Valid UTF-8 files | Left as-is (including Russian in `docs\`, `ui_i18n.cpp`) |

## Spot-check

Russian in `docs\README.md`, `AI_BOT.md`, `ARCHITECTURE.md`, `UPDATE_GUIDE.md`, `ui_i18n.cpp` reads as Cyrillic (not `Рџ` / `Ð`). After convert: live leftover BOM / invalid UTF-8 in AOE4HOOK + `.cursor` + `.agents` + `docs` = **0** (except kept `mp_bypass*`).
