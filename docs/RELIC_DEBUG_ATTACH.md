# Дебаг Relic без патча `.text` (канон)

Build **16.3.11308.0**. **RVA only.** Не сажать Watcher / sibling / 7AB0 / FlushArm / Enqueue.

Это продолжение ответа «слоты ≠ dest0, патч игры слоты не замораживает».  
Диск: [RELIC_UNPACK_ALGORITHM.md](RELIC_UNPACK_ALGORITHM.md).  
Почему plant умирает: [findings/2026-09-06-full-patch-is-not-leftover.md](findings/2026-09-06-full-patch-is-not-leftover.md).  
Окно RA: [UPDATE_GUIDE.md](UPDATE_GUIDE.md) §9.

---

## Два вопроса, два ответа

| Хочу | Делать | Не делать |
|---|---|---|
| Оверлей / SCAR / DualFlag | APC DLL | дебаггер на Relic |
| Пошагово смотреть RA / hasher | hide-стек ниже, slots проверить **до** BP | `ret 1` на Watcher, File→Attach, INT3 на EP |

Слоты (`tag=0x20220002`) — скан **окна и пути процесса**.  
HashRec dest0 — скан **записи в `.text`**. Они независимы: leftover 621 KiB при slots=0 (PID 52920).

**Продукт (2026-09-14):** HV NPT hold → inject (`auto_run=0`, AUTO выкл) → confirm overlay RUN (опасно) → **stock** `x64dbg.exe`. Hidden rbhost не нужен, если Enqueue уже ret-stub (sibling call не пишет слоты). Visible `x64dbg.exe` **до** wait-hold = DualFlag. Любой slot = убить Relic сразу. Скрипт (не map): tools/Run-ProductDbgCycle.ps1. [hold](findings/2026-09-13-hv-hold-before-dbg.md). [product cycle](findings/2026-09-13-product-dbg-cycle.md). [AUTO off](findings/2026-09-14-patch-game-auto-off.md).

«Выключить слоты» = не попасть в скан. Не = nop Watcher.

---

## Что видит Relic (три датчика)

### 1. Sibling path — `RA_SiblingPathScan` `0x3F328D8`

Классификатор `0x3EAFA2C`, типы 3/4/5 → `RA_Enqueue(..., 200, 0x20220002, 9)`.

Ловит:

- лист `x64dbg.exe` (даже если окно переименовано);
- любой путь с `\x64dbg\` (PID 38172: `...\x64dbg\release\x64\RuntimeBroker.exe`);
- VERSIONINFO `FileDescription` / `ProductName` = `x64dbg` (18480).

`WindowWatch.exe` **не** тип 3/4/5 — его можно держать.

### 2. Watcher titles — `RA_WindowWatcher` `0x3F0A7D0`

Первый заголовок: hashed `GetWindowTextW` (`0x3F87250`), не IAT.

XOR chrome в **одном** буфере: `PID:` **и** `Thread:` **и** (`Module:` / `Main Thread`).  
Дефолтный титул x64dbg (`… - PID: %X`) этого тройного AND не всегда закрывает; лист `x64dbg` закрывает.

`GuiUpdateWindowTitle` пишет chrome на каждый attach — 1 Hz `SetWindowText` проигрывает. Нужен hammer 16–100 ms + `titleboot` до first paint.

Патч Relic IAT `GetWindowTextW` → pack `0x56FD3C0`. Jmp в тело user32/ntdll — то же.

### 3. Attach INT3 — не слоты WW

`0x3C3200`: если первый байт EP Relic = `0xCC` (`~*ep == 51`) → EventSchedule + Enqueue `01010001`.  
Stock x64dbg: `EntryBreakpoint=1` `TlsCallbacks=1` `SystemBreakpoint=1`.  
Это **посадка INT3 в Relic `.text`**, hasher/RA пакуют. `-nodbg` не спасает.

File→Attach / attach-on-PID-create (36208) — отдельный kill.  
Kernel DebugPort / QIP: хук ntdll **запрещён** (`0x56FD3C0`). PEB wipe (`BeingDebugged=0`, `NtGlobalFlag &= ~0x70`) — да; `NtQueryInformationProcess` — нет.

---

## Продуктовый ритуал (HV + overlay + stock dbg)

Нет Relic `.text` plants. Overlay только usermode. IDA GUI закрыта, пока жив Relic.

```text
1. Чистый idle HV map, hv_ping=pong (этот скрипт не map; gate STOP → не запускать)
2. Закрыть x64dbg.exe / leftover rbhost. WindowWatch можно оставить
3. Steam Relic: -dev -nodbg -notrap, титул окна (не PID без HWND — 36208)
4. python aoe4-hv\tools\zpp_at.py wait-hold     (slots=0; NPT ret Enqueue/KickCtor/TimerQ)
5. elevated DllInjector.exe --patch-game
   [patch_game] auto_run=0 (AUTO OFF) — confirm RUN in overlay (DANGEROUS)
   лог [PatchGame] RUN applied
6. stock x64dbg.exe (не Start-X64dbgHidden, не RuntimeBroker)
   Events=0 SafeAttach=1 DisableAslr=0 на ini рядом с exe
7. File→Attach / debug_attach_pid только если WindowWatch slots=0
   любой slot = убить Relic
```

Или elevated `AOE4HOOK/tools/Run-ProductDbgCycle.ps1`.

## Fallback: hidden rbhost (если stock пакует sibling)

Инструменты: `AOE4HOOK/tools/x64dbg-hidden\`.  
`AOE4H_RA_TEXT_NEUTRALIZE=0`.

```text
Start-X64dbgHidden.ps1 → RuntimeBroker.exe, путь без \x64dbg\, VERSIONINFO rbhost
Apply-X64dbgAoe4Ini.ps1 (Events=0). Без HookLibrary в Relic.
Без HV hold: debug_attach_pid = смерть ~8с (41064). Soft-bind relicconnect — RPM.
```

Первый раз, если папка ещё `...\x64dbg\`: elevate `rename-portable.ps1`.

Ожидание: launch без `20220002`, если first-paint chrome снят **и** VERSIONINFO не `x64dbg`.  
RA-окно **ленивое**: пустого `slots=0` объекта нет, пока не было Enqueue. Смотреть WindowWatch, не «ждём слот».

Живой прогон 23:39–23:41: hold **52920** был `slots=0`. Hidden `rbhost` PID **52428** встал *раньше* нового Relic **26976**. T+20 с: **slots=3** `20220002`. Hide не закрыл sibling/title. [hold](findings/2026-09-06-debug-attach-hold.md).

23:46: **41064** hide + Hidden rbhost + MCP `debug_attach_pid` (`attach_break=false`) → Relic мёртв ~8 с. Recovery **51652** relicconnect, Relic жив, slots=3. [41064](findings/2026-09-06-debug-attach-41064.md).

`taskkill` Relic иногда не берёт даже elevate — End Task из Диспетчера.

---

## Что уже пробовали и умерло

| Действие | Итог |
|---|---|
| Watcher / sibling `ret 1` | IAT-kick slots=4 ~4 с |
| Enqueue nop + SNAP 7AB0 | slots=**0**, смерть ~8 с |
| `--packs` / `--nuclear` | быстрее |
| user32/ntdll body jmp | pack `0x56FD3C0` |
| ScyllaHide HookLibrary **в Relic** | то же |
| File→Attach | pack +15 с / slots=11 |
| EntryBreakpoint INT3 | `01010001` |
| `MpBypassWindowClear` | `.data` ноль, таймеры в куче живы |
| сажать Fwd / 7AB0 потому что `[+8]=0` | писателя нет; IAT-kick |

---

## Если нужен hasher, а не окно

Hide-ритуал **уже** стоит. Потом:

- hardware BP / VEH на `RA_Hasher` `0x3E57050` (не 14-byte hook пролога);
- вокруг raw-load восстановить `saved[]`;
- не ставить BP на Watcher / 7AB0 / FlushArm / Enqueue.

Это ещё не live-доказано на slots=0 PID. Не путать с «выключить слоты».

Продуктовый оверлей hasher не требует.

---

## CLI

```powershell
# один раз
Start-Process powershell -Verb RunAs -ArgumentList @(
  '-NoProfile','-ExecutionPolicy','Bypass','-File',
  'K:\aoe4_dlc\hh\AOE4HOOK\tools\x64dbg-hidden\rename-portable.ps1')

# каждый сеанс (после игры + inject)
Start-Process powershell -Verb RunAs -ArgumentList @(
  '-NoProfile','-ExecutionPolicy','Bypass','-File',
  'K:\aoe4_dlc\hh\AOE4HOOK\tools\x64dbg-hidden\Start-X64dbgHidden.ps1')
```

Чистый цикл с логом: `Run-CleanCycle.ps1` (elevate). Не `--enqsnap` / `--packs`.
