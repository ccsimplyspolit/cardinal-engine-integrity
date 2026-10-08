# Алгоритм распаковки RelicCardinal (канон)

Build, на котором это закрыто: **16.3.11308.0** (`FileVersion` Steam exe).  
SizeOfImage **`0x8C3D000`** (147 050 496). Preferred ImageBase **`0x140000000`**.  
`.text`: VA **`0x1000`**, **22236** страниц × 4 KiB = **91 078 656** B.

Инструмент: `K:\aoe4_dlc\aoe4\gamesource\tools`  
Пайплайн: `Run-RelicUnpackPipeline.ps1` (`.bat` рядом и в `AOE4HOOK\tools`).  
Канон RVA RA: `aoe4/gamesource/meta/ra-map.json`.  
Рецепт после охоты: `aoe4/gamesource/meta/unpacker-recipe.json`.

**RVA only.** VA из разных PID не складывать. On-disk Steam `RelicCardinal.exe` — не код.  
Не `MiniDumpWriteDump` на живой Relic. Не сажать RA.

История охоты (не backlog): [findings/2026-09-06-relic-unpacker.md](findings/2026-09-06-relic-unpacker.md).  
Пайплайн / прогон rediscover: [findings/2026-09-06-unpack-pipeline.md](findings/2026-09-06-unpack-pipeline.md).  
После unpack живёт другой слой: [findings/2026-09-06-ra-integrity-layer.md](findings/2026-09-06-ra-integrity-layer.md).  
«Полный патч Steam exe» не существует: [findings/2026-09-06-full-patch-is-not-leftover.md](findings/2026-09-06-full-patch-is-not-leftover.md).  
Читаемый unpack-disk: [findings/2026-09-08-gamesource-unp-humanized.md](findings/2026-09-08-gamesource-unp-humanized.md).

---

## 1. Шесть продуктов — не смешивать

| Продукт | Что на выходе | Команда / путь | vs late live `.text` |
|---|---|---|---|
| **Oracle PE** | заголовки диска + live `.text` 60644 | `RelicCardinal.unpacked_analysis.exe` | **100%** (это и есть lift) |
| **Static unpack** | Steam exe → plaintext, игра не нужна | `python -m unpacker unpack-disk` | **99.285%** vs 60644; **99.328%** vs 52968 T+20s |
| **Runtime lift** | pe-sieve / `memory.bin` после Arxan | `dump_relic_module.py` | сам plaintext |
| **RA sim** | dest-XOR leftover **после** compact | `ra-sim` / `--no-cloak` | leftover **растёт** vs T+20s gold (unlock ≠ XOR) |
| **Gold splice** | скопировать leftover с **одного** live PE | `splice-gold` | **100%** vs этот PE; через секунду устаревает |
| **Humanized named** | читаемый C/disasm каталога, только `static_match` | `python -m unpacker humanize` → `gamesource_unp_humanized/` | leftover **не** в этих span (16.3: 66/66 match, 651 472 B dest0 иначе) |

100% vs поздний live `.text` **не** цель диска. Leftover = session RA (cloak XOR + unlock PRNG assign).  
`splice-gold` — копия leftover, не рецепт и не эмуляция PRNG.

Пути PE (16.3.11308.0):

| Файл | Роль |
|---|---|
| `C:\Program Files (x86)\Steam\steamapps\common\Age of Empires IV\RelicCardinal.exe` | диск, шифр `.text` + overlay |
| `K:\aoe4_dlc\analysis\game_16.3.11308\RelicCardinal.unpacked_analysis.exe` | oracle |
| `K:\aoe4_dlc\analysis\game_16.3.11308\RelicCardinal.unpacked_static.exe` | static unpack |
| `K:\aoe4_dlc\analysis\game_16.3.11308\RelicCardinal.unpacked_rasim.exe` | RA sim |
| `K:\aoe4_dlc\dumps\RelicCardinal_60644_20260906_full_analysis\modules_runtime\RelicCardinal.exe.memory.bin` | live 60644 (канон для IDA / r8 / AOB) |
| `K:\aoe4_dlc\dumps\RelicCardinal_52968_20260906_224630\00007ff7ad880000.RelicCardinal.exe.bin` | T+20s gold leftover 612 209 |

Steam exe пайплайн **не** перезаписывает.

---

## 2. Что это не есть

Диск — **не** VMP / SteamStub / Denuvo / Themida / Enigma / UPX.  
DIE подписывает MSVC + Steam + D3D12; бренд-пакера нет.  
`UPX` в `.text` — три байта шифра, не stub.  
dearxan — FromSoft GuardIT, другая форма Arxan.  
VMP-Deob / `C:\vmp` — не этот бинарь.

Не писатель дискового `.text`:

| Кандидат | Почему нет |
|---|---|
| TLS | один callback `0x4FB0B6C` = MSVC `TlsCallback_0`, страница plaintext |
| EP | vanilla `start` → cookie → `__scrt_common_main_seh` |
| IAT `VirtualProtect` | Relic heap tag, не диск |
| IAT `AddVectoredExceptionHandler` | один xref → BugSplat |
| `_initterm` CRT$XCU | bulk `.text` уже plain **до** C++ inits |
| Overlay `lz4` | 3 entropy-байта, **0** LZ4 frame magic `04 22 4D 18` |

Писатель compact XOR: `RA_Integrity_Dispatcher` `0x3E44034` → store `xor [rsi], rax; rax *= r8` в `RA_TextXor_7AB0` `0x3E45870`.  
CRT Once: `RA_Integrity_Dispatcher_Once` `0x3DDF150`. Decrypt ~**110 ms** после Resume (после `steam_api`, до C++ inits).

13 AES-128 map `.lua` в Data.sga — **другой** ритуал, ключа в поставке нет.  
XOR имён SCAR-нативов: ключ **`0x8B ^ i`** на каждую строку в `.data` (не
`.rdata`). `python -m unpacker scar-xor` → `meta/scar-xor.json`. Static PE
оставляет шифр; live 60644 уже plaintext. [scar-xor](findings/2026-09-07-scar-xor.md).

---

## 3. Как мы это распаковали (порядок доказательств)

Не прыгать к XOR, пока слой выше не закрыт. Каждый негатив записан.

```text
1. Atlas 4 KiB: C vs P
     17640 / 22236 cipher (79.33%), 803 plaintext islands
     крупнейшие: 0x516B000–0x56DD000 (EP) и 0xD6000–0x3CF000
2. Headers plaintext → TLS / IAT / overlay без дизасма шифра
3. Не TLS / не VEH / не CRT$XCU / не IAT VirtualProtect
4. Suspended Relic: .text ещё шифр → stub внутри Relic, не Steam loader
5. Overlay = pack (футер), не второй PE и не LZ4
6. Live pack-catch: Dr0 write на seed → heap pack-decoded.bin
     compact 105383 recs, apply → 99.285% vs 60644
7. Leftover ≠ PE reloc, ≠ truncated walk, ≠ fat-as-compact
     leftover-gap: 100% dest slot 0 (notDest=0)
8. AEAD no-game: footer → X25519+HSalsa20+XSalsa20 skip32
     pack-decoded-static.bin == heap[64:]
9. unpack-disk = decrypt overlay + compact apply, игра не нужна
10. rediscover = то же по форме (без хардкода seed/RVA)
11. leftover после compact = 45E8 cloak XOR + unlock PRNG assign
     ra-sim cloaks leftover vs gold; splice-gold копирует leftover
```

Ложные следы, которые уже убиты (не повторять):

- период-N XOR (`C⊕P` page keys = 0)
- leftover = DIR64 relocs (0 сайтов в `.text`)
- leftover = «не хватает compact recs» (EOF walk = те же 105 383)
- fat type 1/6/7 как compact 0x15/0x16 (0 applied)
- r8 = `0x5A942043DA942043` (коллизия на чётных k0, bit 63)
- Enqueue n = 64 (invert даёт **2327**)
- 16-байтный MSVC-пролог как AOB 7AB0 (**334** хита)
- MiniDump живой Relic (убило 24044)
- второй VA-clone на тот же online PID (37560 умер)
- plant Watcher / 7AB0 / Fwd / FlushArm / Enqueue «чтобы слот завёлся»
- scoring cloak vs T+20s gold как успех (leftover **растёт**)
- смешивать VA 52968 `0x7FF7AD880000` / 37560 `0x7FF6196D0000` / 60644 `0x7FF7A5500000`

---

## 4. Инвариант vs что поедет на патче

Искать заново по **форме**. Числа ниже — снимок 16.3.11308.0.

| Инвариант (форма) | 16.3.11308.0 | Как найти после патча |
|---|---|---|
| Overlay = байты после last section (`raw+rsz`) | off `0x8076800`, 10 049 828 B, entropy ~8 | `overlay_off()` |
| Футер `D ^ ~(B*C) == A` (qword little-endian) | `RA_PackFooter_Parse` `0x3F913AC` | `find_footer` с конца, лимит 0x2000 |
| `tableSize = C`, `tableOff = (p-8) - C` | tableOff=0, C=`0x995884` (10 049 668) | из футера |
| `plainExpect = C - 88` | 10 049 580 | AEAD out = size−88 |
| AEAD header 64 B: `sk=hdr[0:32]`, `pk=hdr[32:64]` | sk head `81fab5f2…`, pk head `b887379d…` | те же срезы |
| `k = HSalsa20(zeros16, X25519(sk, pk))` | live key `532b4c79…1302203` | `box_key(pk, sk)` — **этот** порядок |
| body = blob[64:]; `ct=body[16:-8]`; `extra=body[-8:]` | extra `93974ef745fa390c` | MAC 16 prefix, last 8 = nonce |
| nonce = `extra \|\| zeros16`; XSalsa20 **skip32** | без skip32 первые 4 KiB ≠ dump | `secretbox_xor(..., skip32=True)` |
| Каталог: слот 24 B, `ptr = table + 776 + off` | HDR=776 | `hunt_directory` |
| type2 size=**8** = seed; type3 = compact | seed `0xFDFDFBCD1B3F5D7B` | size==8 + next size>1 MiB + walk recs |
| Heap dump table = **+64** vs static | seed 2432563 / compact 2432571 | `find_table` / hunt |
| Static table = 0 | seedPtr 2432499, compactPtr 2432507 | hunt |
| Compact rec: `self, n, rva` + type `@+0x38` | 105 383 = 3175×`0x15` + 102208×`0x16` | walk `self` |
| `k0 = (n XOR seed) * r8` | r8=`0xDA942043DA942043` | qword в live `.text`; score vs disk |
| `n = (k0 * inv(r8)) XOR seed` | Enqueue **2327**, 7AB0 **4181** (`0x1055`) | `invert_len` |
| Спан keep | формула **или** n≥16 | `keep_span` |
| Writer | `xor [rsi], rax; rax *= r8` @ `0x3E45870` | AOB / IDA `RA_TextXor_7AB0` |
| 7AB0 unique AOB | **28** B, не 16 B | `ra-map.decryptVerify.uniqueAob` |
| Seed **live** `.data` | RVA `0x7AF7688` | скан qword; **диск там другой** |
| Fat HashRec | type @ `+0x140`, dest addend @ `+0x90` | 174 recs types 1/6/7 |
| Unlock last-refcount | `*dest = r8 * g_RA_UnlockPrng` assign | RVA prng `0x7AFD990` — не с диска |

Поедет всегда: RVA функций, imagebase, seed value, tableOff, compact off, SizeOfImage, AOB 16-байт, AEAD sk/pk.

---

## 5. Overlay и футер (байты)

Overlay **не** входит в `SizeOfImage`. Runtime dump на этих RVA — нули.  
`overlay_off = max(section.raw + section.rsz)`.

На 16.3.11308.0:

| Поле | Значение |
|---|---|
| overlay off | `0x8076800` |
| overlay N | 10 049 828 |
| footer scan start | `n-32` = 10 049 796, шаг −1 |
| hit `p` | 10 049 676 |
| A @ `p-8` | check operand |
| B @ `p` | множитель |
| C @ `p+8` | **tableSize** = 10 049 668 = `0x995884` |
| D @ `p+16` | `D ^ ~(B*C) == A` (все `u64`, mul mod 2⁶⁴) |
| tableOff | `(p-8)-C` = **0** |
| tail after table | 160 B (футер + pad) |
| table blob | `overlay[0 : 0x995884]` |

Код: `unpacker/ranges.py` `find_footer` / `footer_fields`.  
IDA: `RA_PackFooter_Parse` `0x3F913AC`, ingest `RA_PackIngest` `0x3F7D07C`.

---

## 6. AEAD (no-game decode)

Формат table blob:

```text
blob[0:64]     header
  [0:32]       sk   (X25519 secret, RFC 7748 clamp в лестнице)
  [32:64]      pk   (X25519 public)
blob[64:]      body
  [0:16]       Poly1305 MAC (verify игра; мы skip — known-plaintext)
  [16:-8]      ciphertext
  [-8:]        extra8 → nonce24 = extra8 || 16×00
```

Ключ:

```text
shared = X25519(sk, pk)          # RFC 7748; игра 0x3FBBF80 показывает 121666 (ref10)
k      = HSalsa20(16×00, shared) # sigma "expand 32-byte k"  0x3FC9210
pt     = XSalsa20-XOR(k, nonce24, ct, skip32=True)
```

`skip32`: secretbox_open_detached — первые 32 байта keystream выбросить.  
Без skip32 первые 4 KiB **не** равны heap dump.  
Порядок `box_sk_pk`: `x25519(sk, pk)` затем HSalsa. Обратный порядок ≠ live key.

`cryptography` не обязателен. `x25519_pure` в `overlay_aead.py` (ida-mcp 3.12 его нет).  
Самотест: RFC 7748 §5.2 / §6.1 + libsodium HSalsa core2.  
Выход: `dump/crypt/pack-decoded-static.bin` (10 049 580 B).

Heap `pack-decoded.bin` (live catch) = **64 B префикс** + тот же plaintext.  
`heap[0:64] ≠ pt[0:64]`. Сравнивать `heap[64:]`.

Имена IDA: `crypto_box_beforenm` `0x3FB5050`, `crypto_secretbox_open` `0x3FB52E0`,  
`crypto_core_hsalsa20` `0x3FC9210`, `crypto_scalarmult_curve25519` `0x3FBBF80`.

---

## 7. Каталог pack

После AEAD plaintext — таблица секций.

```text
slot(type) = table + 24*type
off  = u64(slot+8)
size = u64(slot+16)
ptr  = table + 776 + off
```

16.3.11308.0 static (`table=0`):

| type | size | ptr | Смысл |
|---|---|---|---|
| 0 | 1 591 461 | 776 | type0 blob (не compact XOR) |
| 1 | 840 262 | 1 592 237 | fat HashRec (types 1/6/7) |
| 2 | **8** | 2 432 499 | seed qword |
| 3 | 7 612 623 | 2 432 507 | compact 0x15/0x16 |
| 4 | (wchar / aux) | — | `RA_PackSection_Get` type4 |
| 5+ | мелкие | — | не диск-XOR |

Heap dump: `table=64`, все ptr **+64** (seed 2432563, compact 2432571).

Охота без seed (`hunt_directory`):

1. `table` в `0..512` шаг 8.
2. Слот с `size==8` и валидным `ptr`.
3. Следующий слот `size > 1_000_000`.
4. Walk до 48 compact recs: `self≥0x39`, type `0x15`/`0x16`, RVA в `.text`, `0 < n < 0x200000`.
5. Побеждает максимальный `probeRecs` (≥4).

`find_table(blob, seed)` — ищет qword seed, затем тот же слот. Fallback = hunt.

---

## 8. Compact XOR (диск)

Запись (минимум `0x39` B, дальше payload для `0x15`):

| Off | Поле |
|---|---|
| +0 | `self` (размер этой rec) |
| +8 | `n` (длина XOR) |
| +16 | `rva` (dest в `.text`) |
| +0x38 | type `0x15` или `0x16` |
| +0x39 | payload, только type `0x15`, длина `n` |

Формула (все `u64`, mul mod 2⁶⁴):

```text
k0 = (n XOR seed) * r8
out[i:i+8] = in[i:i+8] XOR k
k = k * r8
хвост <8: побайтно, k >>= 8
```

- type `0x16`: `in` = текущие байты `.text[rva:rva+n]` (in-place).
- type `0x15`: `in` = payload из pack.

На 16.3.11308.0: **3175** × `0x15`, **102208** × `0x16`, skipped=0.  
7AB0: RVA `0x3DD7AB0`, n=`0x1055`, type `0x16`, self=57.  
Enqueue: RVA `0x3DD2550`, n=2327.

`r8` **не** `0x5A94…`. Коллизия только на чётных k0.

После apply vs 60644 live: **90 427 184** same (99.285%), leftover **651 472**.  
Уже plain на диске до XOR: **36 050 433**.  
vs 52968 T+20s gold: leftover **612 209**, из них RA **604 240**, outside **7969**.  
`leftover-gap`: `inDest0 == leftover`, `notDest=0`, `gapRuns=0`.

Выход PE = копия Steam файла, переписан только `.text`. Overlay в выходном PE **остаётся ciphertext** (так задумано).

---

## 9. Fat / HashRec / leftover после compact

Fat (type1): rec ≥ `0x141`, type @ `+0x140`, payload @ `+0x141`.  
На билде: **174** recs, types `0x1`=40, `0x7`=133, `0x6`=1. Это **не** compact.

Dest slot `i` (0..15):

```text
rva    = u64(rec + 0x10 + 8*i)
addend = u64(rec + 0x90 + 8*i)
dest   = rva + addend
```

Слот 0 есть у всех 174. Cloak 45E8: `*dest ^= k; k *= r8` с `k0=(seed^n)*r8`.  
Unlock (last refcount): `*dest = r8 * g_RA_UnlockPrng` — **присвоение**, не XOR.  
PRNG `@ 0x7AFD990` с диска не симулируется.

Поэтому:

- `ra-sim` (cloak on) vs T+20s gold: leftover **612 209 → 761 333** (хуже).
- `--no-cloak` = оставить static.
- Hasher(payload)==src и Hasher(cloak)==dst: **174/174**.
- `splice-gold` = единственный 100% vs конкретный live PE (копия байт).

Live 52920 menu, slots=**0**, dest0 leftover **621 219**. Integrity не требует WindowWatcher.

Не сажать: `RA_Integrity_45E8` `0x3E545E8`, Hasher `0x3E57050`, Walker, KickCtor, Dispatcher.

---

## 10. Rediscover (после патча / смены ключа)

```text
python -m unpacker rediscover
# --reuse-pack   только если pack-decoded-static.bin уже от этого билда
```

Пишет `meta/unpacker-recipe.json` + `unpacker-rediscover.json`.

Порядок:

1. Steam PE → `overlay_off` → `find_footer` (формула, не RVA).
2. AEAD decode (или reuse pack).
3. `hunt_directory` (size==8 + compact walk) → seed / table / compactPtr.
4. Кандидаты r8: qword в live `.text` + канон `0xDA94…`.
5. Score: первые 16 type-`0x16` recs, XOR disk vs live, взять max `bytePct`.
6. Seed RVA: скан live image на seed qword (на 16.3 — один хит `0x7AF7688`).
7. Unique AOB из `ra-map.decryptVerify.uniqueAob` в live `.text` → drift?

Прогон 2026-09-06 23:34 (без хардкода seed, ida-mcp 3.12, 14.8 с):

| Поле | Найдено |
|---|---|
| seed | `0xfdfdfbcd1b3f5d7b` |
| seedRva | `0x7af7688` (1 хит) |
| r8 | `0xda942043da942043` — 16/16 recs, 9153/9153 B |
| table / types | 0 / seedType 2 / compactType 3 |
| seedPtr / compactPtr | 2432499 / 2432507 |
| compactRecs | 105383 |
| overlay / tableSize | `0x8076800` / `0x995884` |
| AOB 7AB0, Fwd, Enqueue, CrtInit | unique, drift=false |

`unpack-disk` / `load_pack` читают recipe; если recipe стар — hunt всё равно находит каталог.

---

## 11. Пайплайн (один bat)

`aoe4\gamesource\tools\Run-RelicUnpackPipeline.ps1`  
`aoe4\gamesource\tools\Run-RelicUnpackPipeline.bat`  
`AOE4HOOK\tools\Run-RelicUnpackPipeline.bat` → тот же ps1.

Python: `paths.json` → `ida.stackPython` (ida-mcp 3.12).  
Рабочая папка unpacker: `aoe4\gamesource\tools`.

| Шаг | Что | Флаг |
|---|---|---|
| 1 DUMP | elevate `dump_relic_module.py <pid>` если Relic жив | `-SkipDump`; `-FullSnapshot` = VA-clone |
| 2 REDISCOVER | footer + AEAD + dir + r8 + AOB | всегда |
| 3 UNPACK | `unpack-disk` | всегда |
| 4 GAP | `leftover-gap` | `-SkipGap` |
| 5 VERIFY1 | `audit` | всегда |
| 6 IDA names | `ida/import_ra_names.py` на **runtime** IDB | `-SkipIda`; `-UpdateRaMap` пишет drift в ra-map |
| 7 DECOMPILE | `full_decompile.py --cluster-first --only-rvas` | `-SkipDecompile`; `-FullDecompile` = 534k фон |
| 8 VERIFY2 | `audit` + `Verify-RaDecrypt.py` + `Probe-IatObjSlot.py` если live | — |
| 9 GIT | docs / unpacker / meta JSON | **только** `-Commit`; `-Push` отдельно |

Флага **`-ClusterOnly` нет**. Кластер — режим по умолчанию. Полный Hex-Rays — `-FullDecompile`.

Только распаковка без IDA/дампа:

```text
python -m unpacker pipeline
python -m unpacker pipeline --skip-gap
```

Дамп:

1. `Start-Process -Verb RunAs`.
2. Модуль PE: image-layout `*.RelicCardinal.exe.bin` + `manifest.json` (PID, B, SizeOfImage).
3. Полный снимок: `dump_relic_snapshot.py` = `PssCaptureSnapshot` + `MiniDumpWriteDump` **клона**, только если commit charge тянет второй экземпляр VA.
4. Если `PssCaptureSnapshot` = **1455** (Relic ~9 GiB, мало FreeVirtual): `dump_sdk_pack.py --no-minidump` + `dump_relic_full_rpm.py` (VirtualQueryEx+RPM Memory64, без suspend, без `PROCESS_CREATE_PROCESS`). Пакет: `Capture-FreshRelicDump.ps1`. [fresh-relic-dump-38348](findings/2026-09-14-fresh-relic-dump-38348.md).
5. Никогда MiniDump на живой Relic (24044).
6. Не второй VA-clone на тот же online PID (37560).
7. VA разных PID не мешать.

IDA:

- Открывать `runtime_exe.i64` (копия `dump/ida-work` или канон 60644).  
  Не Steam PE, не `original_exe.i64`.
- Imagebase IDB 60644: `0x7FF7A5500000`. Имена = `imagebase + RVA`.
- Не `run_auto_analysis` на шифрованном диске.
- Не сажать: Watcher, Sibling, 7AB0, FlushArm, Enqueue, EventSchedule, C8E4, 77E8, Fwd, PathList, CbRegister.

`-Commit` не кладёт: `dumps\`, `*.dmp`, `*.i64`, Steam exe, `pack-decoded*.bin`, analysis PE.  
На 2026-09-06 у `hh` и `aoe4\gamesource` **нет** `.git` — `-Commit` пишет `not a git repo`.

---

## 12. Сверка

`python -m unpacker audit` — 67 pass / 0 fail (2026-09-06 23:20). Живые проверки:

| id | Смысл |
|---|---|
| `footer` / `plain-expect` / `extra8` / `ct-n` | форма overlay |
| `hsalsa` / `x25519` / `box-sk-pk` / `skip32-required` | AEAD |
| `live-key-match` / `live-key-not-pksk` | порядок sk,pk |
| `pt-vs-static-file` / `pt-vs-heap64` | decode == dumps |
| `compact-count` / `compact-types` / `enqueue-len` / `7ab0-len` | pack |
| `enqueue-invert` / `7ab0-invert` | `n = (k0*inv(r8))^seed` |
| `apply-same` / `leftover-n` / `apply-pct` | 90427184 / 651472 / 99.285% vs 60644 |
| `leftover-is-dest0` / `leftover-ra` | не дырка XOR |
| `reloc-text` | 0 DIR64 в `.text` |
| `gold-100` | splice vs 52968 T+20s |
| `rasim-hasher` / `rasim-ne-static` | 174/174; cloak ≠ static |
| `seed-rva-disk-not-live` / `seed-rva-60644` | диск @ `0x7AF7688` ≠ seed |
| `static-pe-overlay-still-ct` | выходной PE не подменяет overlay |

Второй проход после IDA/дампа: снова `audit` + `Verify-RaDecrypt.py` (AOB + `vtbl+10 == 7AB0`) + `Probe-IatObjSlot.py` если Relic жив (`g_RA_IatObj+8` обычно 0).

Ожидание leftover: диапазон RA `0x3DD0000–0x3F90000`, не «ещё один XOR на диске».

---

## 13. Карта файлов

| Путь | Роль |
|---|---|
| `tools/unpacker/rediscover.py` | охота формы → recipe |
| `tools/unpacker/recipe.py` | чтение/запись recipe |
| `tools/unpacker/leftover_aslr.py` | `find_table` / `hunt_directory` |
| `tools/unpacker/overlay_aead.py` | X25519 / HSalsa / XSalsa skip32 |
| `tools/unpacker/unpack_disk.py` | Steam → static PE |
| `tools/unpacker/apply_pack.py` | walk compact / load_pack |
| `tools/unpacker/ranges.py` | footer, k0, invert, r8 |
| `tools/unpacker/leftover_gap.py` | dest0 vs notDest |
| `tools/unpacker/ra_sim.py` | 45E8 dest-XOR |
| `tools/unpacker/audit.py` | 67 checks |
| `tools/unpacker/pipeline.py` | rediscover+unpack+gap+audit |
| `tools/ida/import_ra_names.py` | имена в runtime IDB |
| `tools/ida/full_decompile.py` | Hex-Rays cluster / full |
| `AOE4HOOK/tools/dump_relic_module.py` | elevate module PE |
| `AOE4HOOK/tools/dump_relic_snapshot.py` | VA-clone minidump |
| `meta/unpacker-recipe.json` | текущий рецепт |
| `meta/ra-map.json` | RVA + unique AOB |

---

## 14. CLI

```text
cd K:\aoe4_dlc\aoe4\gamesource\tools

python -m unpacker rediscover
python -m unpacker unpack-disk
python -m unpacker leftover-gap
python -m unpacker audit
python -m unpacker pipeline
python -m unpacker ra-sim
python -m unpacker ra-sim --no-cloak
python -m unpacker splice-gold --all

.\Run-RelicUnpackPipeline.ps1 -SkipDump
.\Run-RelicUnpackPipeline.ps1 -SkipDump -SkipIda
.\Run-RelicUnpackPipeline.ps1 -FullDecompile
.\Run-RelicUnpackPipeline.ps1 -Commit
```

Старые слои (охота, не ежедневный путь): `atlas` `hunt` `overlay` `crt` `suspend` `pack-catch` `apply-pack` `oracle` `corpus`.

`python -m unpacker all` = только atlas+hunt+overlay, **не** полный пайплайн.

---

## 15. После обновления игры

1. Не открывать новый Steam exe в IDA.
2. `rediscover` (форма). Если footer/AEAD/dir падают — смотреть overlay_off и футер, не подбирать RVA руками.
3. Сверить `aob.drift` в recipe с `ra-map.json`. Уникальный хит + drift → `-UpdateRaMap` или правка руками.
4. `unpack-disk` + `audit`. Leftover-n vs 60644 **изменится**, если live образ новый — не чинить XOR, пока `notDest!=0`.
5. Новый module PE + новый runtime IDB. Старые VA выкинуть.
6. Имена + cluster decompile. Полные 534k — отдельно, часы.
7. Overlay-ритуал (ScarDoString / DualFlag) — [UPDATE_GUIDE.md](UPDATE_GUIDE.md) §11. Unpack не заменяет DualFlag.

Не сажать Dispatcher / 7AB0 / Fwd, «чтобы проверить leftover».
