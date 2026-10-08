# 2026-09-07 22:06 — Rebuild overlay, HV не трогали

`Release|x64` `/t:Rebuild` `AOE4HOOK\internal\AOE4HOOK.sln` EXIT 0 (~70 s). Relic/WW **не** держали `InternalInjector.dll` / `WindowWatch.exe`. `aoe4-hv` не собирали, `--arm` не было.

titlehide: `build-titlehide.ps1` EXIT 0, копии в `C:\Program Files (x86)\rbhost\release\x64\`.

.NET: первый `dotnet build` Aoe4Auth / rrtex_decode упал на SDK 10 `Microsoft.Build.Tasks.Git` («недопустимая ссылка» из нулевых байт в git ref). Повтор с `-p:EnableSourceControlManagerQueries=false` — EXIT 0.

| Артефакт | Размер | Время |
|---|---|---|
| `internal\x64\Release\InternalInjector.dll` | 13868032 | 22:07:13 |
| `internal\x64\Release\DllInjector.exe` | 212992 | 22:06:26 |
| `internal\x64\Release\InternalInjectorStub.dll` | 6144 | 22:06:27 |
| `internal\x64\Release\BridgeWatch.exe` | 220672 | 22:06:26 |
| `internal\x64\Release\WindowWatch.exe` | 206336 | 22:06:26 |
| `dist\AOE4HOOK.exe` | 24122880 | 22:07:34 |
| `Launcher\x64\Release\launcher_target_test.exe` | 1323520 | 22:06:43 |
| `patchAT\x64\Release\patchAT.exe` | 187904 | 22:06:26 |
| `server\Aoe4Auth\bin\Release\net8.0\Aoe4Auth.dll` | 216064 | 22:07:55 |
| `tools\rrtex_decode\bin\Release\net8.0\rrtex_decode.dll` | 10752 | 22:07:57 |
| `titlehide.dp64` / `titleboot.dll` / `relicconnect.dp64` | 107520 / 107008 / 138752 | 22:06:26 |

Standalone pack: 699 entries, SHA-256 `2fc3a18b6cbf73bd9077970d421d8cfa48dd0bb1311f1c1cd0da1f546dd0aa20`.