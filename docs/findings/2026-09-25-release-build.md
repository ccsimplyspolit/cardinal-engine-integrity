# 2026-09-25 — Release|x64 AOE4HOOK.sln

Community MSBuild `internal\AOE4HOOK.sln` `/t:Build` `Release|x64` — EXIT 0 (~80 s). Relic PID 45052 жив; `InternalInjector.dll` на линк был writable (LNK1104 не было).

## Артефакты

| Артефакт | Размер | Время |
|---|---|---|
| `internal\x64\Release\InternalInjector.dll` | 13885952 | 18:47:51 |
| `internal\x64\Release\DllInjector.exe` | 224768 | 18:46:53 |
| `internal\x64\Release\WindowWatch.exe` | 206336 | 18:46:52 |
| `dist\AOE4HOOK.exe` | 24173056 | 18:48:11 |

Standalone pack: `settings.manifest 2026.09.25+ccbaa43266`, 700 entries, SHA-256 `2d706538813bab2981cbfcf95c8150fd90c74084e4ac1820618aa1c8720e61b6`.

HV / auth / titlehide не собирали (только sln Release).
