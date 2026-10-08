# [ОТМЕНЕНО 2026-09-30] Aegis type0 (HashMapGate) — safe bypass via slot.size=0

**ЭТА ЗАМЕТКА НЕВЕРНА.** Проверка 2026-09-30 показала: --nullify-type0
крашит игру с illegal instruction 0xc000001d @ RVA 0x3DE24F0. См.
`docs/findings/2026-09-30-aegis-type0-crash-explained.md`.

Ниже — оригинальный (ошибочный) текст 2026-09-29:

---

Дата: 2026-09-29. Build 16.3.11308.0.

## Проблема

Первая попытка Варианта B (обнуление всех 1.52 МиБ содержимого type0 +
модификация type10) привела к тому, что игра не стартует. Крипто было
проверено корректным (no-op re-encrypt даёт байт-в-байт идентичный файл),
но патченный overlay игра всё равно отвергала.

## Причина

Разбор функций (IDA `runtime_exe.i64`, ImageBase 0x140000000):

- **RA_PackFooter_Parse (0x3F913AC)**: копирует только 40 байт хвоста
  (footer 32 + aux 8) в state. Байты `+0x28..0x9F` (120 байт «подписи»
  из build-log `signed successfully. [Sig: 071aee0d1afc77e8]`) — мёртвые
  данные, они не читаются рантаймом. Подпись — build diagnostic.

- **RA_PackSection_Get (0x3F91340)** вызывается 5 раз в
  `sub_143E44034` (CRT init через `sub_143DDF150`). Типы: 2, 4, 0, 3, 1.
  Type 10 (DirectX Permit) через этот путь **не читается**.

- **`sub_143E44034` (CRT init, до main)**: аллоцирует пустое дерево и
  пишет указатель в `qword_147AF7AF0` (g_RA_HashMapGate) на 143E44390.
  Затем вызывает `PackSection_Get(state, 0, ...)`. При успехе входит
  в цикл на 143E45525:
  ```
  loop: alloc(19); read u32 rva_off, u8 hash_len, memcpy hash_len bytes;
        insert into g_RA_HashMapGate as {module_base + rva_off, ptr};
        extra -= (hash_len + 5); if extra > 0 loop.
  ```

- **Обнуление всех 1.52 МиБ type0** делает 318 292 итерации, каждая
  вставляет запись с ключом `module_base + 0` в multimap. Затем
  `sub_143E545E8` (RA hasher) при верификации страниц ищет реальный RVA,
  находит только массив дубликатов с ключом module_base — hash mismatch
  на каждой странице → анти-тампер.

## Безопасный фикс (Вариант B'):

Обнулить `slot[0].size` в directory (u64 по смещению 16 в plaintext).
Тогда `PackSection_Get(type=0)` возвращает failure по проверке
`if (!*(v6 + 16)) return 0`. Caller (`test al, al; jnz 143E45435`) не
прыгает, идёт по cleanup-ветке. Весь блок обработки type0 (и цикл
вставки) пропущен. g_RA_HashMapGate остаётся пустым; RA hasher
`sub_143E545E8` на пустом multimap возвращает "not found" на каждый
lookup — анти-тампер не срабатывает.

Реализация: `python -m unpacker.patch_overlay_disk --nullify-type0`.
Один u64 в plaintext, MAC перевычисляется корректно.

## Type10 (DirectX Permit) — безопасна

Формат: UTF-16LE `dll\ndll\ndll\n\x00` + null padding до 130 байт.
Наш патч воспроизводит это точно (drop `TwitchNativeOverlay64.dll` +
add `InternalInjector.dll`, оба ~ 40 байт UTF-16, помещаются в 130).
Тип не читается через PackSection_Get на CRT init, значит startup-краш
не может исходить отсюда.

## Что ЗАПРЕЩАЕТСЯ (перепроверка стоп-листа)

Стоп-лист из AGENTS.md — `77E8` — совпадает с последними байтами
build-signature `071aee0d1afc77e8`. Косвенное подтверждение, что это
маркёр анти-тампера, но он в overlay не хранится (проверено grep'ом
raw exe + 140 МБ memory dump: 0 совпадений). Значит используется как
"canary" в коде (например, hash-seed). Не трогать в наших вставках.

## Файлы

- Патчер: `gamesource/tools/unpacker/patch_overlay_disk.py`
- DllInjector: `internal/DllInjector/aegis_overlay.h` — вызывает
  патчер с `--nullify-type0`.
- Runtime data:
  - g_RA_HashMapGate: RVA 0x7AF7AF0 (VA 0x147AF7AF0)
  - qword_147AF7B28: module_base (используется парсером для VA=base+rva)
