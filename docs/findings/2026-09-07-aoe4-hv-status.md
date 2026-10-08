# 2026-09-07 — aoe4-hv: не запускать до ребута

Отдельный проект `hh\aoe4-hv`. Не часть шести коммитов / не InternalInjector.

## Live (01:08)

| | |
|---|---|
| Last boot | 2026-09-06 16:23 |
| `testsigning` BCD | записан 00:22 (`Yes`); **не live** (ребута не было) |
| `sc query Aoe4Hv` | STOPPED, **577** (DSE) |
| `System32\aoe4_hv.sys` | 9072 B @ 00:22:52 (старая копия) |
| build `driver\x64\Release\aoe4_hv.sys` | 11776 B @ 00:27:27 (новее, не скопирован) |
| Relic | **живой** PID 18172 с 01:07 |
| ADR-006 | файла нет на `main` |
| `--arm` | **ни разу** не проходил |

`Install-Aoe4HvStatus.ps1` в 00:22: подпись ок, `sc start` = 577. Probe usermode: AMD SVM=1 NPT=1, driver not loaded.

## Build (01:14) — собрано, не установлено

Community MSBuild + registry `KitsRoot10` = `C:\Program Files\Windows Kits\10\` (нет `km`) → WDK import ломается (`MSB4086` на `WindowsTargetPlatformVersion`). Обход: `aoe4-hv\scripts\Build-Aoe4Hv.ps1` — `ml64` + `cl /kernel` + `link /DRIVER` с x86 kit `10.0.26100.0` (`km` + `km\crt` + `shared`). Probe — обычный `v143` MSBuild.

| Артефакт | Размер | Время |
|---|---|---|
| `aoe4-hv\driver\x64\Release\aoe4_hv.sys` | **12800** B | 2026-09-07 01:15:32 (rebuild) |
| `aoe4-hv\probe\x64\Release\aoe4_hv_probe.exe` | 40960 B | 2026-09-07 ~01:17 (force Rebuild) |
| `System32\aoe4_hv.sys` | 9072 B @ 00:22 | **не копировали** |

Не `sc start`, не `probe --arm`. `System32` остаётся старой копией.

## Решение

Не `sc start`, не `probe --arm`, пока нет ребута с live testsigning. Первый VMRUN — не на живом Relic: неверный VMCB = BugCheck.
