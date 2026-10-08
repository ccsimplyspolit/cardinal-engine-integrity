# 2026-09-06 Relic unpack algorithm + one pipeline

Канон (байты, слои, CLI): [RELIC_UNPACK_ALGORITHM.md](../RELIC_UNPACK_ALGORITHM.md).  
Код: `aoe4/gamesource/tools/unpacker` (`rediscover`, `unpack-disk`, `pipeline`).  
Обёртка: `aoe4/gamesource/tools/Run-RelicUnpackPipeline.ps1` / `.bat`.  
Кластер Hex-Rays — **по умолчанию**. Флага `-ClusterOnly` в этом ps1 нет (`-FullDecompile` = 534k).

## Зачем

После смены seed / AEAD-ключа / сдвига RVA хардкод `2432507` / `SEED_LIVE` / `0x7AF7688` ломается. Охота идёт по **форме**, не по числу из 16.3.11308.0.

## Форма (закрыто на этом билде)

| Шаг | Как найти |
|---|---|
| Overlay | после last PE section |
| Footer | `D ^ ~(B*C) == A` |
| AEAD | `sk=hdr[0:32]`, `pk=hdr[32:64]`, HSalsa20(0, X25519), XSalsa20 skip32 |
| Dir | слот size==8 + следующий size>1 MiB; `ptr = table+776+off` |
| Compact | type `0x15`/`0x16`, `k0=(n^seed)*r8` |
| r8 | qword `0xDA942043DA942043` в live `.text`; не `0x5A94` |
| RA имена | unique AOB из `ra-map.json` (7AB0 = **28** B) |

Leftover после compact = session RA (dest slot 0 / unlock PRNG), не дырка XOR. `splice-gold` = 100% vs один live PE, не рецепт.

## Пайплайн (один bat)

1. DUMP — elevate `dump_relic_module.py` если Relic жив. `-FullSnapshot` = VA-clone. **Не** MiniDump живой Relic.
2. `python -m unpacker rediscover` → `meta/unpacker-recipe.json`
3. `unpack-disk` (seed/r8/table из recipe + hunt)
4. `leftover-gap` + `audit` (сверка 1)
5. `ida/import_ra_names.py` на runtime IDB (не Steam PE)
6. Hex-Rays cluster (`--only-rvas`). `-FullDecompile` = 534k в фоне
7. `audit` + `Verify-RaDecrypt.py` + `Probe-IatObjSlot.py` если live (сверка 2)
8. `-Commit` — docs/tools/meta JSON. Не dumps, не PE, не IDB, не `pack-decoded*.bin`

Не сажать Watcher / 7AB0 / Fwd / FlushArm / Enqueue.

## Прогон rediscover (2026-09-06 23:34, без хардкода seed)

`python -m unpacker rediscover` из `aoe4/gamesource/tools` (ida-mcp 3.12).  
Steam overlay → footer → AEAD → `hunt_directory`. Live = 60644 `memory.bin`.

| Поле | Найдено | Канон 16.3.11308.0 |
|---|---|---|
| seed | `0xfdfdfbcd1b3f5d7b` | то же |
| seedRva | `0x7af7688` (1 хит) | то же |
| r8 | `0xda942043da942043` | 16/16 recs, 9153/9153 B vs live |
| table / seedType | 0 / 2 | то же |
| seedPtr / compactPtr | 2432499 / 2432507 | то же |
| compactRecs | 105383 | то же |
| overlayOff / tableSize | `0x8076800` / `0x995884` | то же |
| AOB 7AB0/Fwd/Enqueue/CrtInit | unique, drift=false | `ra-map.json` |

`hh`, `aoe4/gamesource` на этом диске **без** `.git` — `-Commit` пока no-op, пока не будет репо + remote.

## Документация сверена (тот же вечер)

Живые доки приведены к канону. Исторические findings не переписаны — сверху
баннер / Update, чтобы агент не открывал закрытый backlog.

| Было неверно | Стало |
|---|---|
| `RELIC_UNPACK_ALGORITHM.md` флаг `-ClusterOnly` | такого свитча нет; кластер по умолчанию, `-FullDecompile` = 534k |
| unpacker README «AEAD still needed» | AEAD + `unpack-disk` закрыты |
| relic-unpacker «Next» / «AEAD still needed» | баннер **закрыто** + пометка у абзаца pack-catch |
| UPDATE_GUIDE §2.2 «atlas / TLS-hunt / oracle» | `rediscover` → `unpack-disk` → pipeline |
| gamesource README «оверлей не unlock» | AEAD закрыт; 13 AES map-lua без ключа |
| disk-crypt / max-decrypt / VT / VMP-Deob / game-folder | overlay больше не «заперт»; static unpack наш |
| findings index «overlay+13 AES left» / «no public unpacker» | строки индекса поправлены |
