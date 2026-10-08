# Aegis type0 nullify — почему крашит

Дата: 2026-09-30. Build 16.3.11308.0.

**Отменяет:** `docs/findings/2026-09-29-aegis-type0-safe-bypass.md`.

## Что произошло

Ранее задокументированный "безопасный обход" через `--nullify-type0`
на самом деле НЕ работает. Проверено запуском:

- Патч `--nullify-type0` + type10 → игра стартует и через несколько
  секунд крашится:
  ```
  Application Error 0xc000001d (STATUS_ILLEGAL_INSTRUCTION)
  Fault RVA 0x0000000003de24f0
  ```
- Патч только type10 (без nullify) → игра работает нормально.
- Восстановление backup → работает.

## Почему

Разбор декомпила
`gamesource_unp_humanized/named/RA_Integrity_Dispatcher_0x3E44034.c`:

**Строка 864-882** — dispatcher вызывает `RA_PackSection_Get(state, 0, ...)`.
Если возвращает false (что как раз наш случай при `slot[0].size=0`):

```c
if ( !(uint8_t)RA_PackSection_Get(v371, 0, &v345, &v363, &v370) ) {
  sub_3F912B4(v371);   // cleanup
  sub_3F779B8(v372);
  ...
  return v1;           // ← РАННИЙ ВЫХОД
}
```

Type3 (строка 994) и type1 (строка 1182) остаются необработанными.

**Type3 / type1 содержат XOR-зашифрованные блоки .text** (opcodes 21/22
в цикле обработки). Каждая запись — это `{rva_offset, encrypted_bytes,
opcode}`. Диспетчер:

- opcode 21 (line 1104-1125, 1235-1303) — `memcpy` + XOR-декрипт с
  `g_RA_DestXorSeed` (0xDA942043DA942043) либо через `__rdtsc()`-key.
- opcode 22 (line 1013-1090, 1307-1336) — XOR-декрипт in-place по
  `g_RA_ImageBase + rva`.

Это **VM-replacement фейковых инструкций Aegis'а** на реальный код.

На RVA 0x3DE24F0 в disk exe и в runtime memory dump лежит:
`D5 DC CA A3 BC 48 89 7C 24 10 55 48 8B EC ...`. Байты идентичны — Aegis
их **не переписывает физически**, только декриптует при init. Без type3/1
декрипта `D5 DC` остаётся illegal opcode. `RA_Integrity_Dispatcher_Once`
(RVA 0x3DDF150) вызывает `call 0x3DE24F0` напрямую (`E8 5E 33 00 00`)
после `RA_Integrity_Dispatcher` — если декрипт не отработал, illegal
instruction crash.

## Правильный обход anti-tamper — уже реализован в проекте

**НЕ трогать overlay type0/type1/type3.** Только type10 (permit list) —
безопасно для инъекции DLL.

Anti-tamper выключается через **внешний инструмент `patchAT.exe`**
(K:\aoe4_dlc\hh\AOE4HOOK\patchAT\x64\Release\patchAT.exe, готовый билд).
Каталог сайтов в `patchAT/sites.h`. Не изобретать велосипед.

### Как пользоваться

```
patchAT.exe --list                catalog RVAs
patchAT.exe --probe               RA state snapshot
patchAT.exe --apply --nuclear     Watcher + D02C/F448 + schedule + enqueue
patchAT.exe --watch 120           re-apply if stubs torn (2 min)
patchAT.exe --restore             откат из Dumps\patchAT-save.bin
```

**Проверенные патчи** (sites.h):
- `RA_WindowWatcher (0x3F0A7D0)` → `mov eax, 1; ret` (6 байт)
- `RA_EventSchedule (0x3DD15E4)` → `xor eax,eax; ret` (3 байта)
- `RA_TimerQ_Push (0x3E672DC)` → `xor eax,eax; ret`
- `RA_Enqueue (0x3DD2550)` → `xor eax,eax; ret`
- `nop5` на `call RA_Enqueue` из Watcher/sibling (6 сайтов)

### RVA антитампера

- `kRaHashMismatchBudgetRva = 0x7542030` (uint64, live=99)
- `kRaAccumRva = 0x7AFB750` (порог 0x46)
- `kRaHashMapGateRva = 0x7AF7AF0`
- `kRaDestXorSeedRva = 0x7AF7688` (XOR seed для type3/type1)
- `kRaImageBaseRva = 0x7AF7B28`
- `kRaWatcherBeatRva = 0x7542080` (countdown → FlushArm(4), reset 100)

## Что нельзя (BANNED список в sites.h)

- `RA_Hasher` / `RA_Hasher_Large/Mid/Fold` — JUMPOUT family
- `RA_Integrity_45E8` — ret 1 = boot-kill (это VM opcode dispatcher, не
  чистый хешер: игре нужны её результаты для v148, v143 pointer updates,
  декрипта через тот же opcode-путь что type3/type1)
- `RA_Integrity_Dispatcher` — lea JUMPOUT; packs via Enqueue
- `RA_IatScan_7AB0` / `RA_IatPack_77E8` / `RA_IatPack_C8E4` — slots=4 в 4с
- `RA_KickCtor` — armed timers still Exit
- `RA_JumpoutHang` — jmp rax=0

Не патчить IAT Relic и hashed GPA .data (foreign ptr = extra pack).

## Файлы обновлены

- `gamesource/tools/unpacker/patch_overlay_disk.py` — `--nullify-type0`
  переименован в landmine warning с описанием краша.
- `internal/DllInjector/aegis_overlay.h` — убран `--nullify-type0` из
  вызова, обновлён комментарий.
- Память: `aegis-type0-nullify.md` полностью переписана,
  `aegis-type0-nullify-crash-analysis.md` новая заметка.
