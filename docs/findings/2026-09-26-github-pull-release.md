# 2026-09-26 — GitHub pull + Release|x64

`git pull --ff-only origin main` в `AOE4HOOK`: `20da2d1d82` → `ab9dcfc4c9`.

Входящие коммиты:

- `af48da3d0c` Menu: one style on every page and the HUD; render the real pages offscreen.
- `ab9dcfc4c9` Tests: follow the Present inner split and the removed SCAR settle.

Community MSBuild `internal\AOE4HOOK.sln` `/t:Build` `Release|x64` — EXIT 0. Relic PID 27924 жив; `InternalInjector.dll` на линк был writable.

## Артефакты

| Артефакт | Размер | Время |
|---|---|---|
| `internal\x64\Release\InternalInjector.dll` | 13882880 | 00:40:22 |
| `dist\AOE4HOOK.exe` | 24169984 | 00:40:25 |

Standalone pack: `settings.manifest 2026.09.26+ab9dcfc4c9`, SHA-256 `9a61f23f65b2d6379f47823ab5b4cf0f6d4a8a18de7cb56b696b0fa6f71bc6da`.

`DllInjector.exe` не пересобирался (входные файлы не менялись, время 2026-09-25 18:46:53).
