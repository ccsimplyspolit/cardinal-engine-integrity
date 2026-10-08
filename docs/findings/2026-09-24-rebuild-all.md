# 2026-09-24 — полный Rebuild (23:22–23:28)

`Release|x64` для живых проектов. `_arhive` не трогали. HV **не** мапили (`kdu` / `System32` не обновляли). Relic в момент сборки не держал DLL.

## Toolchain

- Первый `/t:Rebuild` через BuildTools MSBuild = EXIT 1: нет `Microsoft.Cpp.Default.props` (`VC\v170`).
- Рабочий MSBuild: `C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\MSBuild.exe`
- Auth: без `-p:EnableSourceControlManagerQueries=false` — Git SCM «недопустимая ссылка» (нули в ref). С флагом OK.
- HV: `build_windows.bat mode=release` (не голый `release` — make target missing).

## Артефакты

| Артефакт | Размер | Время |
|---|---|---|
| `internal\x64\Release\InternalInjector.dll` | 13811712 | 23:23:56 |
| `internal\x64\Release\DllInjector.exe` | 224768 | 23:22:50 |
| `internal\x64\Release\InternalInjectorStub.dll` | 6144 | 23:22:50 |
| `internal\x64\Release\BridgeWatch.exe` | 220672 | 23:22:49 |
| `internal\x64\Release\WindowWatch.exe` | 206336 | 23:22:49 |
| `dist\AOE4HOOK.exe` | 24097280 | 23:24:17 |
| `Launcher\x64\Release\launcher_target_test.exe` | 1323520 | 23:23:11 |
| `patchAT\x64\Release\patchAT.exe` | 187904 | 23:22:50 |
| `aoe4-hv\out\release\x86_64\zpp_hypervisor` | 198496 | 23:27:56 |
| `aoe4-hv\out\release\x86_64\zpp_loader.sys` | 228864 | 23:27:59 |
| `server\Aoe4Auth\bin\Release\net8.0\Aoe4Auth.dll` | 216064 | 23:27:09 |
| `tools\rrtex_decode\bin\Release\net8.0\rrtex_decode.dll` | 10752 | 23:27:15 |
| `tools\x64dbg-hidden\titlehide\titlehide.dp64` | 112640 | 23:27:51 |
| `titleboot.dll` / `relicconnect.dp64` | 114688 / 138752 | 23:27:51–52 |

Standalone pack: `settings.manifest 2026.09.24`, 700 entries, SHA-256 `deb75b4fa01d00bc681269a12446af1c6f12ab5e2e27e6beed26b88d968b570a`.

Предупреждение: `scar_native_peel.h(37)` C4018 (signed/unsigned) в `scar_natives.cpp` — не блокирует линк.

titlehide **не** копировали в `Program Files\...\rbhost` (скрипт пишет только в out-dir). `System32` / live map HV не трогали.
