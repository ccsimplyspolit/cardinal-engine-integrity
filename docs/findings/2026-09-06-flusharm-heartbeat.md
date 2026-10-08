# 2026-09-06 — FlushArm heartbeat is `now + period`, not a mystery patch

User: injector WPM/hook, slots=0, RA не видит; эму heartbeat — «основной патч RVA».

## Что FlushArm реально пишет

`RA_FlushArm(int key)` `0x3E8B3A0`. После PRNG/SRW success:

```
now = KUSER InterruptTime          // sub_…65F0  RVA 0x3F765F0
                                   // 0x7FFE0320/324/328 + TickCountMultiplier
for node in g_RA_FlushTree:        // 0x7AFB6D8
    if node+0x20 == key:
        node+0x30 = now + node+0x28
```

`sub_…78EC` (вызов после store) — thunk 5 байт, не beat.

Fail (`v196` out of gate / now > `0x7AFB6F8`): EventSchedule `134218240` /
`2097160` + Enqueue `0x21C0001`. **Не эмулируем.**

Watcher: `--g_RA_WatcherBeat` (`0x7542080`) ≤ 0 → `FlushArm(4)` → beat=**100**.
Ещё `FlushArm(4)` на хит окна. Sibling `FlushArm(4)`. Ключи live:
`4` `8` `0x2710` `0x2711`.

Это **не** прячет запись в `.text`. Hasher raw-load и 7AB0 switch видят байты
независимо от deadline.

## Инструмент

| Путь | Файл |
|---|---|
| шлюз инжектора | `AOE4HOOK/tools/ra_emu.py heartbeat` / `write` |
| контракт | `AOE4HOOK/tools/ra_heartbeat.py` |
| in-process | `ra_heartbeat.cpp` (Present/`EngineFogService`, `AOE4H_RA_HEARTBEAT=0` off) |

`write` всегда тикает heartbeat до и после WPM. Пересечение RA → refuse
без `--force` (7AB0 всё равно увидит).

slots=0 ≠ heartbeat. Слоты пакует Watcher по окнам. Heartbeat держит C8E4
от expire, если Watcher не бьёт FlushArm.

Канон: [RELIC_RA_EMU.md](../RELIC_RA_EMU.md).
