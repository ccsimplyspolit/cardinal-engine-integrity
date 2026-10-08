# New PID: RVA vs VA vs dest leftover (2026-09-13)

User: «RVA меняются каждый перезапуск; весь `.text` под integrity».

## RVA не пляшут на 16.3.11308.0

ASLR двигает **базу**. Каталог (`aoe4_16.3.11308.json`) — **RVA**.

```
B  = EnumProcessModules RelicCardinal (новый PID)
VA = B + RVA
```

Мёртвые VA прошлого PID не переносить. Relic **36888** this boot:
`B=0x7FF6F8E70000`, RPM `B+0x3DD2550` = Enqueue AOB
`44894c24205553565741544155415641` — тот же RVA, что в каталоге и
unpacked_static. Cycle 6 hold `status=8` был **HV CR3 walk**, не сдвиг RVA.

## Как найти в новом процессе (тот же билд)

Elevated, без plant:

1. `python aoe4-hv\tools\zpp_at.py locate` — RPM уникального AOB по
   `B+catalog.rva`. `sig_ok` = RVA жив. `sig_mismatch` → поиск в `.text`.
2. `python aoe4-hv\tools\zpp_at.py sigscan` — подобрать уникальную длину
   AOB (16…64) на каталожных entry. Пишет
   `aoe4_16.3.11308_code_sigs.json`.
3. Кольцо WindowWatch: `.data` RVA (`lock` `0x7AF6DC0` …) **стабильны**.
   Меняются heap-указатели `begin`/`end` (0 пока пусто).

Другой **патч** игры (не рестарт PID) — тогда AOB/RVA в каталоге
протухают. Steam ciphertext на диске не сканить.

16-байтный MSVC-пролог `48 89 5C 24…` у 7AB0 — **334** хита. Нужен
уникальный хвост (Enqueue 16B, Watcher 24B, 7AB0 28B).

## Integrity — не весь `.text`

Hasher `0x3E57050` raw-load **source** до memcpy. 45E8 пишет **dest**
слоты (cloak XOR, unlock assign). Leftover vs static = dest slot 0,
не «весь модуль под CRC».

Страницы dest leftover **самомодифицируются** после unpack
(`0x3E58000`, `0x3F04000`, `0x3F2D000`, …). AOB там может разъехаться
к T+20s. Их не NPT-protect и не брать как locate-якорь. Enqueue
`0x3DD2550` в этом PID был золотой.

NPT hold: identity = оригинальный source для hasher; execute-copy =
stub. WPM `.text` hasher видит.
