# Relic RA emulator (data-only)

Build **16.3.11308.0**. **RVAs only.** No Relic `.text` plant of Watcher /
7AB0 / Enqueue / EventSchedule / FlushArm / C8E4 / 77E8 / Fwd / PathList /
CbRegister / Hasher / 45E8 / KickCtor.

Цель инжектора: **WPM / хук через шлюз**, C8E4 не expire. Heartbeat —
это `FlushArm` success write, не «невидимость `.text`».

## Шлюз (то, через что писать)

```
python AOE4HOOK/tools/ra_emu.py heartbeat --sec 8
python AOE4HOOK/tools/ra_emu.py write --rva 0x... --hex 90...
```

`write` = tick heartbeat → WPM → tick. In-process (после APC inject):
`RaHeartbeatTick` в `EngineFogService` (выкл. `AOE4H_RA_HEARTBEAT=0`).

Контракт [flusharm-heartbeat](findings/2026-09-06-flusharm-heartbeat.md):

`deadline = KUSER_now + period` на ключах `4` / `8` / `0x2710` / `0x2711`,
beat `0x7542080` = 100. Часы = `0x3F765F0` (InterruptTime). Не `call`
FlushArm (fail-path Enqueue `0x21C0001`).

**Два разных условия**

| Хочешь | Что держит |
|---|---|
| процесс не умирает через ~8 с без Watcher-beat | heartbeat (этот слой) |
| `slots=0` | Watcher не пакует окна (hide), не stub WW |
| RA не видит байты хука | Hasher / SNAP / 7AB0 — **не** heartbeat |

Heartbeat **не** делает `.text` невидимым. `write` в RA refuse без `--force`.

## Другие варианты hide (не PAGE_GUARD)

| # | Вариант | Слоты | Hasher/SNAP/7AB0 | Статус здесь |
|---|---|---|---|---|
| 0 | **Не писать Relic `.text`** — хук DXGI / `.data` / SCAR (оверлей) | hide WW | не видят: байт нет | **продукт, живой** |
| 1 | Писать **вне** RA∪SNAP∪dest0 + heartbeat | hide, не stub | Hasher может не ходить | **untested** клетка |
| 2 | Вместе с (1) обновить HashRec `+0x10/+0x18` | hide | только рычаг (1) | назван, не proven |
| 3 | `sync-snap` после своей записи | hide | не 7AB0 (42848) | есть CLI, мало |
| 4 | L3 iat-hold (C50/C58) | не про слоты | racy; хвост `0x3E80060` | data-only |
| 5 | PAGE_GUARD + VEH (тень) | не про слоты | одна страница; RA guard = slots=3 | код есть, DLL залочена |
| 6 | CRT `memcpy` cloak | — | **0x10E** | refuse |
| 7 | Кража KiUser | — | UD2, hits=0 | refuse |
| 8 | DR0 на Hasher / INT3 в Relic `.text` | pack/attach | видит отладчик | не для hold |
| 9 | EPT split-view (исполнение≠чтение) | n/a | закрыл бы Hasher | нет в репо, ядро |

Не смешивать: heartbeat ≠ слоты ≠ hide байт.

Канон решения: [ADR-004](decisions/ADR-004-ra-emulator.md).
Kick-слой: [ra-kick-emu](findings/2026-09-06-ra-kick-emu.md).
Сессия: [2026-09-06-ra-emu.md](findings/2026-09-06-ra-emu.md).

## Два кика

| Слой | Что | Эму |
|---|---|---|
| Expire | C8E4 `now > node+0x30` → EventSchedule → Enqueue `20DE00AD` | L1 `--keep-expire` |
| `.text` mismatch | 7AB0 switch → 77E8 IAT `slots=4` ~4 с | L3 gate **не** compare; L4 SNAP ≠ 7AB0 |

Hasher `0x3E57050` raw-load источника **до** memcpy. Cloak CRT это не прячет.

## Слои (`ra_emu.py`)

| # | Имя | Пишет | Честно |
|---|---|---|---|
| L0 | probe | нет | slots, gate, +8, SNAP, FlushTree, TimerQ, прологи |
| L1 | expire | FlushTree `+0x30`, beat=100 | только expire |
| L2 | timerq | unlink delay `526336` / `2097160` | не весь список |
| L3 | iat-hold | C50/C58 v8 in-range | 7AB0 переписывает; хвост `0x3E80060` жив; **не** vs stub |
| L4 | snap-sync | live окно → кучи ww/sib/7ab0 | не compare 7AB0 (42848 / 6224) |
| L5 | dest0 map | нет | 174 fat dest; пересечение с хуком |
| L6 | hook plan/apply | `.text` только если plan.safe | **untested** вне карт |

`g_RA_IatObj+8` (`0x7AF3BC8`) = **0** на pack. Fwd не эмулируем.

## Запрет apply (пересечение = refuse)

- RA-кластер `0x3DD0000`–`0x3F90000`
- SNAP-окна (26976 / 43676, RVA стабильны):

  | tag | winRva | size |
  |-----|--------|------|
  | ww | `0x3F092A0` | `0x8670` |
  | sib | `0x3F2F528` | `0x91F0` |
  | 7ab0+enq | `0x3DCD6E0` | `0x10FD0` |

- named: EventSchedule `0x3DD15E4`, Enqueue `0x3DD2550`, 77E8 `0x3DD77E8`,
  7AB0 `0x3DD7AB0`, C8E4 `0x3DDC8E4`, Ctor `0x3DDF000`, Fwd `0x3E1E2A4`,
  EP `0x3C3200`, 45E8 `0x3E545E8`, Hasher `0x3E57050`, KickCtor `0x3E691F4`,
  tail `0x3E80060`, FlushArm `0x3E8B3A0`, WW `0x3F0A7D0`, Sibling `0x3F328D8`,
  CbRegister `0x3F45000`
- dest0 fat (`destRva = rva+[rec+0x90]`), если pack на диске читается

Первый milestone: 14-byte хук **вне** этого множества + `hold`. Это клетка
«Untested» из [full-patch](findings/2026-09-06-full-patch-is-not-leftover.md).
Не сажать RA, чтобы «проверить эму».

## CLI

```
python AOE4HOOK/tools/ra_emu.py                  # L0
python AOE4HOOK/tools/ra_emu.py plan --rva 0x.. --len 14
python AOE4HOOK/tools/ra_emu.py hold --sec 8      # L1+L3
python AOE4HOOK/tools/ra_emu.py apply --rva 0x.. --hex ..
```

`--plant` / `--ww` / `--iat` refuse. Elevate `OpenProcess`.
JSON: `aoe4/gamesource/meta/ra-emu.json`.

Оверлей: neutralize OFF, `AOE4H_RA_CLOAK` OFF, IntegrityCloak не default.

PAGE_GUARD hide (лаб): Debug → **Dev: Relic .text PAGE_GUARD (Hasher probe)** —
страница dest0 `0x6AC153` вне RA, VEH без KiUser. [page-guard-hide](findings/2026-09-06-page-guard-hide.md).
Не вместе с IntegrityCloak KiUser. `Release\InternalInjector.dll` сейчас
может быть залочен живым Relic (не менять OutDir).

## Не делать

- Stub Watcher и «бить FlushArm из эму»
- 14-byte `FF 25` на Hasher / FairPlay SEND / `vcruntime!memcpy`
- MiniDump живого Relic
- Смешивать VA
