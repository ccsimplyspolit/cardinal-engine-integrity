# 2026-09-07 — полный Rebuild (01:15–01:17)

`Release|x64` для живых проектов. `_arhive` не трогали. HV не ставили, `--arm` не было. Relic **18172** жив.

Первый `/t:Rebuild` `AOE4HOOK.sln` = EXIT 1: `WindowWatch.exe` LNK1104 (PID **51712** держал файл). Процесс стопнут, `WindowWatch.vcxproj` пересобран отдельно. WW **не** поднимали обратно.

| Артефакт | Размер | Время |
|---|---|---|
| `internal\x64\Release\InternalInjector.dll` | 13888512 | 01:16:31 |
| `internal\x64\Release\DllInjector.exe` | 212992 | 01:15:33 |
| `internal\x64\Release\InternalInjectorStub.dll` | 6144 | 01:15:33 |
| `internal\x64\Release\BridgeWatch.exe` | 220672 | 01:15:33 |
| `internal\x64\Release\WindowWatch.exe` | 206336 | 01:17:07 |
| `dist\AOE4HOOK.exe` | 24139776 | 01:16:53 |
| `Launcher\x64\Release\launcher_target_test.exe` | 1323520 | 01:15:55 |
| `patchAT\x64\Release\patchAT.exe` | 187904 | 01:15:32 |
| `aoe4-hv\driver\x64\Release\aoe4_hv.sys` | 12800 | 01:15:32 |
| `aoe4-hv\probe\x64\Release\aoe4_hv_probe.exe` | 40960 | 01:17 (force Rebuild) |
| `server\Aoe4Auth\bin\Release\net8.0\Aoe4Auth.dll` | 216064 | 01:15:36 |
| `tools\rrtex_decode\bin\Release\net8.0\rrtex_decode.dll` | 10752 | 01:15:39 |
| `tools\x64dbg-hidden\titlehide\titlehide.dp64` | 107520 | 01:17:06 |
| `titleboot.dll` / `relicconnect.dp64` | 107008 / 138752 | 01:17 |

titlehide скопирован в `C:\Program Files (x86)\rbhost\release\x64\`. `System32\aoe4_hv.sys` не обновляли.
