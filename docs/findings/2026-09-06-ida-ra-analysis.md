# 2026-09-06 — законченный IDA-разбор RA / hasher / JUMPOUT / WindowWatcher / FairPlay

Build **16.3.11308.0**. Dump PID **60644**.  
IDB: `K:\aoe4_dlc\dumps\RelicCardinal_60644_20260906_full_analysis\ida\runtime_exe.i64`  
Imagebase **`0x7FF7A5500000`**. MCP session `a1220dbc`. **Только RVA** (VA = base + RVA).

## Где лежит store

| Что | Где |
|-----|-----|
| **IDA data store** | сам IDB: имена `RA_*` / `g_RA_*`, комментарии на функциях и ключевых EA, bookmark на `0x3DDD02C` |
| netnode_kv | схема `idasql-storage` (`snapshot:2026-09-06-ra-cluster`). Писать CLI `idasql -w` **нельзя**, пока worker держит этот IDB (второй writer). После закрытия сессии: `INSERT OR REPLACE INTO netnode_kv(key,value)` этим файлом |
| Этот файл | читаемый законченный разбор (store не markdown) |
| Сессионный след | [2026-09-06-ra-hasher-windowwatcher.md](2026-09-06-ra-hasher-windowwatcher.md), [2026-09-06-fairplay-vs-ra.md](2026-09-06-fairplay-vs-ra.md) |
| Sibling autoscan (534584 funcs, SEND sites) | `K:\aoe4_dlc\dumps\RelicCardinal_60644_20260906_full_analysis\ida\autoscan_report.md` |
| Канон RVA | [UPDATE_GUIDE.md](../UPDATE_GUIDE.md) §1.4 / §1.6 / §2.3 / §3.3–3.4 / §9.6 |

Не расширять `ida\decompiles\` (per-function `.c` — неверный формат). WindowWatcher Hex-Rays уже есть там как сырьё.

---

## 1. Слои (не смешивать симптомы)

| Слой | Что это | Локальный Exit? | Как проявляется |
|------|---------|-----------------|-----------------|
| **A. RA window** | TOP `D02C` → `F448` fail → `EventSchedule` + `Enqueue` → слоты / accum / `KickCtor` | Да | `slots>0`, delayed HUD/Rule Exit (~2s / 120s / 180s), порог accum `0x46` |
| **B. Integrity** | `Hasher` → `45E8` (hash **до** memcpy) → `JUMPOUT` / `Walker` / `Dispatcher` | Да, но иначе | ~16s hang, RIP junk, `Responding=False`. **Не** `slots` |
| **C. WindowWatcher** | `GetWindowTextW` + XOR needles + sibling. Pack `tag=0x20220002` | Да, через тот же Enqueue | `slots=3 accum=600` от **видимого окна** (x64dbg / CE / VS / сам WindowWatch) |
| **D. Xbox FairPlay** | enum `0x411F380` + **SEND** `SubmitReputationFeedback` → `XAsyncBegin` | **Нет** (репутация) | REST `/users/xuid(%s)/feedback`. Не RA `Exit` |
| **E. ESS `reportMatch`** | POST `/game/party/reportMatch` + `checkSums` | **Нет** | match-end HTTP, не sliding window |
| **F. Telemetry** | maelstrom `eventbatch` / PlayFab host | **Нет** | отдельный HTTP |
| **G. `-nodbg`** | cmdline ` -nodbg` → byte `0x844B2ED` | Нет | глушит `IsDebuggerPresent`. **Не** гасит WindowWatcher и hasher |

DualFlag / ScarDoString / Hang Detection (`TimeOutThread` 180000 ms) — отдельные механизмы.  
RA-кластер **не** импортирует WinHTTP / WinINet / `XAsync` — очередь локальная (`Enqueue`). Network SEND живёт в FairPlay / ESS / telem, не в D02C.

---

## 2. Call graph (RVA)

```text
native / helper call-sites
  └─ RA_TopValidator_D02C          0x3DDD02C   size 0x2CB
        ├─ RA_RangeCheck_F448      0x3E4F448   size 0x1D8   (единственный caller)
        │     читает g_RA_ImageBase 0x7AF7B28, Size 0x7AF7B30,
        │          Whitelist 0x7AF7B40, End 0x7AF7B48
        └─ fail:
              RA_EventSchedule     0x3DD15E4   size 0xF69   (~101 xref)
                 └─ RA_TimerQ_Push 0x3E672DC   size 0x5E
                       lock 0x7AF6D80  list 0x7AF6D88
              RA_Enqueue           0x3DD2550   size 0x917
                 tag 0x80320001  a2=80  a4=9
                 pack 6, 2,10,1, 120,90,3, 180,90
                 lock 0x7AF6DC0  stride 0x198
                 accum 0x7AFB750  cmp 0x46  flag 0x7AFB758
                 cmp [slot], 2
                    ==2 → ещё EventSchedule
                    !=2 → RA_KickCtor 0x3E691F4  (imul delay * 1000 ms)
                           qword callback @ 0x3E69428

RA_WindowWatcher                   0x3F0A7D0   size 0x422F  (callback, 0 named callers)
RA_WindowWatcher_Sibling           0x3F328D8   size 0x1974
  └─ Enqueue tag 0x20220002  a2=200  a4=9
        pack 6, 2,10,1, 80,60,3, 120,90     (slots=3 accum=600)

RA_Integrity_Dispatcher_Once       0x3DDF150   size 0x47
  if !g_RA_DispatcherOnce (0x7AF7655):
      alloc 24 → RA_Integrity_Dispatcher  0x3E44034  size 0x2491  (282 BB)
         lea RA_JUMPOUT                    0x3E4429C
         lea RA_Integrity_45E8_Thunk       0x3E447FD
         Enqueue ×3
         (внутренности диспетчера — open)

RA_JUMPOUT                         0x3F57539   size 0x78
  if g_RA_JUMPOUT_Gate (0x7AFB0A0) || 45E8==0
      → fail 0x3F575B1
        xor rax,rax; xor rsi,rsi; mov rsp,rax; mov rbp,rsi; jmp rax

RA_Integrity_45E8                  0x3E545E8   size 0x1DE4
  RA_Integrity_45E8_Thunk          0x3E46FF8   jmp 45E8
  hash @ 0x3E55314 = RA_Hasher(source)
  cmp rax, [obj+0x10]
  mismatch → xor eax,eax @ 0x3E55437 → JUMPOUT fail
  memcpy @ 0x3E5547E  (позже)
  второй Hasher @ 0x3E555F3
  Enqueue ×3 + RA_Integrity_Walker 0x3E47000  (единственный caller = 45E8)

RA_Hasher                          0x3E57050   raw-load *src
  ├─ RA_Hasher_Large               0x3E56678   (>0x80)
  ├─ RA_Hasher_Mid                 0x3E56BC0
  └─ RA_Hasher_Fold                0x3E56CD4   (из Large)

Xbox_FairPlay_Mapper               0x411F380   enum strings only (не sender)
  JSON builder                     0x411ED00   /users/xuid(%s)/feedback
  SubmitReputationFeedback         0x40D4E50   → 0x40EB180 XAsyncBegin  **SEND**
  orchestrator                     0x40D5030
  PlatformReportJob                0x30B61F0   hardcoded feedbackType=7
  XboxPlatform::GetLiveContext     0x2EFD750   vtable 0x6530680 (0 named code callers)

ESS reportMatch                    0x300E030   POST /game/party/reportMatch + checkSums  **SEND**
Dev_NoDbg_Check                    0x3B77110   flag 0x844B2ED  parsed-once 0x85A6C39
```

### D02C callers (первые)

| Caller RVA | Заметка |
|------------|---------|
| `0xB7F150` | helper со SCAR-контекстом (уже в гайде) |
| `0xB7F100` | сосед |
| `0x696360` | native site |
| `0xC00090` | native site |
| `0x1ABE220` / `0x1ABE720` / `0x1ABE790` | native sites (autoscan; не `0x1A6E220`) |

Enqueue callers — десятки (D02C, оба Watcher, 45E8, Dispatcher, плюс пачка `0x3E…` / `0x3F…`). Не stub’ить call-sites по одному: резать сам `Enqueue` / `TimerQ`.

---

## 3. `.data` globals

| Имя в IDB | RVA | Смысл |
|-----------|-----|--------|
| `g_RA_WindowLock` | `0x7AF6DC0` | `SRWLOCK` окна слотов |
| `g_RA_WindowBegin` | `0x7AF6DC8` | begin |
| `g_RA_WindowEnd` | `0x7AF6DD0` | end (`+= 0x198` на push) |
| `g_RA_WindowCap` | `0x7AF6DD8` | capacity; overflow → grow |
| `g_RA_WindowAccum` | `0x7AFB750` | uint64; `cmp rax, 46h` |
| `g_RA_WindowFlag` | `0x7AFB758` | uint8; ставится 1 когда accum ≥ `0x46` |
| `g_RA_TimerQLock` | `0x7AF6D80` | `SRWLOCK` heap-таймеров |
| `g_RA_TimerQList` | `0x7AF6D88` | односвязный список узлов (16 B: next + obj) |
| `g_RA_ImageBase` | `0x7AF7B28` | live image base для F448 / 45E8 RVA |
| `g_RA_ImageSize` | `0x7AF7B30` | размер образа |
| `g_RA_Whitelist` | `0x7AF7B40` | таблица диапазонов (count QWORD + packed lo/hi) |
| `g_RA_WhitelistEnd` | `0x7AF7B48` | конец таблицы |
| `g_RA_JUMPOUT_Gate` | `0x7AFB0A0` | ненуль → сразу JUMPOUT fail |
| `g_RA_DispatcherOnce` | `0x7AF7655` | once-флаг инициализации Dispatcher |
| `g_RA_HashMapGate` | `0x7AF7AF0` | ненуль → 45E8 ищет HashRec |
| `g_RA_HashMap` | `0x7AF7AF8` | MSVC map; HashRec = node `+0x28` |
| `g_RA_HashKeyTree` | `0x7AF7B20` | дерево ключей перед HashMap |
| `g_RA_DestXorSeed` | `0x7AF7688` | seed dest-XOR после memcpy |
| `g_RA_HashMismatchBudget` | `0x7542030` | 45E8 decrement; dump 99 |
| `g_Dev_NoDbgFlag` | `0x844B2ED` | ` -nodbg` (не `0x544B2ED`) |
| `g_Dev_NoDbgParsed` | `0x85A6C39` | cmdline уже разобран |

`slots = (end - begin) / 0x198`.

---

## 4. Что stub / никогда не stub

| RVA | Neutralize | Почему |
|-----|------------|--------|
| Watcher `0x3F0A7D0` + sibling `0x3F328D8` | **pass** `mov eax,1; ret` | `ret 0` → `ExitProcess` |
| Enqueue `0x3DD2550` + TimerQ `0x3E672DC` | **fail** `xor eax,eax; ret` | не копить слоты / не пушить timerq |
| D02C `0x3DDD02C` / F448 `0x3E4F448` | **pass** | не заходить в fail-pack |
| `KickCtor` `0x3E691F4` | **никогда** | уже armed таймеры; stub не отменяет Exit |
| `45E8` `0x3E545E8` | **никогда** | `mov eax,1; ret` = **boot-kill** |
| Thunk `0x3E46FF8` / Walker `0x3E47000` | **никогда** | continuity integrity |
| Hasher `0x3E57050` (+ Large/Mid/Fold) | **не 14-byte hook** | пролог сам в hashed range |
| JUMPOUT `0x3F57539` | не «лечится» ret | fail = `jmp rax` с rax=0 → hang, не слоты |
| FairPlay mapper / `-nodbg` | не RA-stub | другой слой |

`MpBypassWindowClear` (end=begin, accum=0, flag=0) **не** дренирует `0x7AF6D88` и не отменяет `KickCtor`.

---

## 5. Живой цикл (slots=0)

1. Закрыть **x64dbg и WindowWatch** (и CE/IDA attach, если не нужен).
2. Steam: `-dev -nodbg` (` -notrap` по желанию).
3. Inject `Release\|x64` `DllInjector.exe` (default = profiler + RA neutralize).
4. Ждать `[RA] neutralize ON` в `%TEMP%\aoe4_internal.log` (`kick=` `timerq=`).
5. **Потом** открывать WindowWatch / x64dbg.

Injector High vs Relic Medium: SDDL `D:(A;;GA;;;AU)S:(ML;;NW;;;ME)`.  
Не `--ra-veh` вместе с VS. Не VS + x64dbg + INT3 VEH в одной сессии.

Открытие окна x64dbg **до** neutralize = пачка `0x20220002`, не JUMPOUT.

---

## 6. Проваленные подходы (не повторять)

| Попытка | Почему нет |
|---------|------------|
| memcpy/memmove cloak (`vcruntime140` / `ucrtbase` → ntdll `RtlMoveMemory`) | `45E8` хешит **source** на `0x3E55314` **до** memcpy `0x3E5547E`. Hasher raw-load live `.text` |
| `45E8` stub `ret 1` | boot-kill |
| Прятать только title x64dbg / `00_retitle.lua` / rename exe | class + `x64dbg.exe` proc-scan + hasher hang остаются. ScyllaHide смотрит title **и** class (`x64dbg`, `OLLYDBG`, `ida`, `Cheat Engine`, `devenv`) |
| Relic IAT patch | pack `0x20DE00AD` / `0x56FD3C0` |
| `PAGE_GUARD` Relic `.text` / crack AOB `0x3E77BD2` | UD2 / kill (это не memcpy) |
| Clear слотов в x64dbg как «фикс» | таймеры уже armed |
| Путать FairPlay **SEND** / ESS `reportMatch` с RA kick | HTTP репутация / checksums, не `slots` / не `Exit` |
| Старый `-nodbg` RVA `0x544B2ED` | неверный; живой byte = `0x844B2ED` |

winnt `RtlMoveMemory` — макрос на `memmove` → рекурсия, если хукать криво.

---

## 7. Поведение узлов (не простыня Hex-Rays)

### D02C / F448 / pack

`D02C(a1)`: `ok = F448(retaddr, a1)`. Fail: XOR-0x59 формат (`%016llX`-класс), `EventSchedule`, затем

`Enqueue(ctx, 80, 0x80320001, 9, 6, 2, 10, 1, 120, 90, 3, 180, 90)`.

`a4` кратно 3; va идёт тройками по 24 байта. Интерпретация таймеров: **2s / 120s / 180s**.  
`F448`: если `a1` внутри `[ImageBase, ImageBase+Size)` — binary search whitelist; иначе/мимо таблицы → fail (`al=0` заставляет D02C паковать).

### Enqueue

Если `a4 % 3 == 0` и `a4 != 0`: на каждый слот — exclusive lock, скан stride `0x198`, `accum += slot[0x190]`, `cmp accum, 0x46`, set flag, `end += 0x198` или grow.  
`cmp dword [slot], 2`: tag 2 = ещё schedule; иначе alloc `0x1C0` + `KickCtor` (задержки `* 1000` ms).

### 45E8 / Hasher / JUMPOUT

Hasher — wyhash-семейство (`0x9E3779B185EBCA87`, fold `0x165667919E3779F9`). Считает по указателю, не по копии.  
JUMPOUT единственный code/data xref — `lea rcx, RA_JUMPOUT` в Dispatcher `0x3E4429C` (не прямой `call`). Fail-байты: `E8 01 00 00 00` + `xor rax/rsi; mov rsp,rax; mov rbp,rsi; eb 01 / jmp rax`.

### WindowWatcher

`HWND` callback. Needles XOR; `GetWindowTextW(..., 512)`; `wcsstr` / `_wcsicmp`. Enqueue `0x20220002`. Sibling подтверждён в асме: `mov r8d, 20220002h`. Neutralize = **pass**.

### FairPlay / ESS / telem (autoscan SEND) vs RA (local)

`GetWindowTextW` IAT (USER32 `0x56DF2C0`) — **только** WindowWatcher, 2 сайта `0x3F0B3EC` / `0x3F0C9E3` (python/CE-host). Основной title — hashed `0x3F87250` @ `0x3F0A910`. Plaintext needles (`x64dbg`, `Cheat Engine`, …) в бинаре **0**; XOR. Строки Frida в бинаре **нет**: по `0x65E052C` лежит `Friday` из таблицы дней недели (`Sunday` / `Saturday` / `Friday` / `Wednesday` / `Tuesday`) рядом с HTTP-digest строками `auth-int` / `userhash`. `frida-agent` / `gum-js-loop` — **0** хитов (ASCII и UTF-16, runtime image 60644, перепроверено 2026-09-28). Единственный lowercase `frida` @ `0x5B0ED7C` — внутри статического словаря Brotli (`…pragmafridayjunior…`, словарь с `0x5B0BE30`).

Нет named `*FairPlay*` / `*Checksum*` / `*reportMatch*` функций (534584 total). Domain — строки + XOR.

**FairPlay SEND** (не mapper):

```text
0x2EFD750  GetLiveContext / Report          vtable 0x6530680
  → 0x30B61F0  PlatformReportJob            feedbackType=7 hardcoded
    → 0x40D5030  orchestrator
      → 0x411ED00  JSON path /users/xuid(%s)/feedback
      → 0x411F380  enum strings (case 2 = FairPlayTampering)  — local
      → 0x40D4E50  "SubmitReputationFeedback"
           → 0x40EB180  XAsyncBegin          **SEND** (shared XSAPI, 18+ callers)
    callback 0x30B6550  XAsyncGetStatus
```

`0x411F380` **не** шлёт. Нет IAT `XblSocialSubmitReputationFeedbackAsync` — статически связанный XSAPI + строка `0x653C710`. UI `ReportPlayer` (`0x63ED5D0`) — loc table, 0 code xref. SCAR `Player_SetReputation` — XOR, 0 xrefs.

**ESS reportMatch SEND:**

```text
0x31C9910  match-end parent (не декомпилить, 0x33C4)
  → 0x31C91B0  walk 528-byte player slots
    → 0x300E030  POST /game/party/reportMatch (str 0x65384E0) + checkSums (0x65384C0)
0x300DF50  mutex + party-slot → 0x300E030
0x307DFC0  thunk vtable 0x653B2D0
0x30108A0  второй caller 0x300E030
```

Bare `reportMatch` `0x65384EC` — substring, **0 xrefs**. Host XOR `0x300F630` (`i ^ 0xD6`).  
Checksum serializer `0x2E23930` (vtable `0x652DE80`): `dataChecksum` `0x652CEA8`, `appBinaryChecksum` `0x652CEB8`, `modDLLChecksum` `0x652CFF8` — уходят и на create/join, не только reportMatch. `datacrc`/`appbincrc` @ `0x3002A40`.

**Telemetry SEND:** maelstrom Content-Type `0x2F4E310` (str `0x65328C0`); PlayFab host `titleId.playfabapi.com` `0x6532238`; `RRSendTelemetry` `0x3729B80` (likely, не декомпилить). `RL_TELEMSERVICE` — config key, не sender.

**Steam:** IAT `steam_api64` есть. **`ISteamUserStats` / `SteamUserStats` — нет** (строка и import). `VACBanned` — XOR decrypt init `0x28F770`, не VAC query.

`-nodbg`: `GetCommandLineA`, токен ровно ` -nodbg` (7 символов с пробелом). `return !flag && IsDebuggerPresent()`.

---

## 8. Сделано в IDA vs open

### Полностью разобрано

D02C, F448, Enqueue (lock/stride/accum/tag/kick), TimerQ, KickCtor, JUMPOUT+fail bytes, Hasher+Mid+Fold+Large роль, 45E8 hash-before-memcpy + mismatch `eax=0`, Thunk, Dispatcher **once-wrapper**, FairPlay mapper **и SEND-цепочка** (autoscan), ESS `reportMatch` POST, `-nodbg` flag/cache, WindowWatcher/sibling pack tags + `GetWindowTextW` unique, граф xrefs первого круга. Не сканировали 534k функций повторно.

### Open (не декомпилить целиком)

| Цель | Почему open |
|------|-------------|
| Dispatcher `0x3E44034` (282 BB) | как именно дергает JUMPOUT/45E8, какие 3 Enqueue-pack, что в 24-byte ctx |
| Walker `0x3E47000` (321 BB) | полный обход секций / какие RVA попадают в hash |
| EventSchedule `0x3DD15E4` (141 BB) | layout heap-таймера кроме push в `0x7AF6D88` |
| WindowWatcher needles | полный 88-entry title-hash + late XOR title/class pair. Первый XOR-блок decoded: `PID:`/`Thread:`/`Module:`/`Main Thread` (AND). IAT GWTW = python-path. См. [2026-09-06-x64dbg-windowwatcher-hide.md](2026-09-06-x64dbg-windowwatcher-hide.md) |
| Второй hash `0x3E555F3` | **закрыто:** dest (`[obj+0xA0]+[obj+0x20]`) vs `[obj+0x18]` (refcount-drop). Source hash остаётся `0x3E55314` |
| `g_RA_JUMPOUT_Gate` writers | кто ставит `0x7AFB0A0` |
| `0x31C9910` / `0x3729B80` | match-end / RRSendTelemetry — слишком большие; SEND уже доказан строками+xrefs |
| `OnChecksumMessage` / `localChecksum` / `ServerChecksum` | XOR, 0 xrefs |

Дальше: `analyze_component` только Dispatcher+Once+JUMPOUT+45E8 thunk, не весь Relic.

---

## 9. Новые RVA (этот проход)

| Факт | RVA |
|------|-----|
| D02C fail tag | `0x80320001` |
| F448 whitelist qword | `0x7AF7B28` / `+8` size / `+0x18` table / `+0x20` end |
| JUMPOUT gate | `0x7AFB0A0` |
| 45E8 hash / cmp / memcpy / xor-0 | `0x3E55314` / `[obj+0x10]` / `0x3E5547E` / `0x3E55437` |
| Hasher Large / Mid / Fold | `0x3E56678` / `0x3E56BC0` / `0x3E56CD4` |
| Dispatcher / Once / once-flag | `0x3E44034` / `0x3DDF150` / `0x7AF7655` |
| JUMPOUT lea / thunk lea | `0x3E4429C` / `0x3E447FD` |
| `-nodbg` parsed-once | `0x85A6C39` |
| Sibling `20220002h` sites | `0x3F337F9`, `0x3F33E8E` |
| FairPlay SEND | `0x40D4E50` → `0x40EB180` (`XAsyncBegin`); job `0x30B61F0`; gate `0x2EFD750` |
| ESS reportMatch POST | `0x300E030` path `0x65384E0`; callers `0x300DF50`, `0x30108A0`, `0x31C91B0` |
| ESS checksum keys | serializer `0x2E23930`; `dataChecksum`/`appBinaryChecksum`/`modDLLChecksum` |
| GetWindowTextW sites | IAT `0x3F0B3EC`, `0x3F0C9E3` (python-path); hashed `0x3F0A910` / `0x3F0E442` |
| D02C tag (этот IDA) | `0x80320001` (Hex-Rays `-2145124351`). Autoscan писал `0x80240001` — не подтверждено здесь |

---

## 10. Reconfirm hasher vs cloak (IDA `a1220dbc`, no new `.c`)

Cloak stays **default-off** (BugCheck `0x10E` / NVIDIA UMD + CRT `memcpy` jmp). Do not set `AOE4H_RA_CLOAK`. Do not re-enable IntegrityCloak.

**Hasher reads live bytes, not a CRT copy.**

- `RA_Hasher` `0x3E57050` (`.text`): `mov rbx, rcx` then `xor r8, [rcx]` / `xor rcx, [rdx+rbx-8]` / `mov eax, [r10+rbx-4]`. No `memcpy`.
- `45E8` increment: `mov rcx, [rdi+130h]; call RA_Hasher` @ `0x3E55314`; `cmp rax, [rdi+10h]`; fail `xor eax,eax` @ `0x3E55437`. **Then** `memcpy(r15, [rdi+130h], [rdi])` @ `0x3E5547E` (`r15 = [rdi+0A0h]+[rdi+20h]`), dest XOR `0xDA942043DA942043`.
- Second hash `0x3E555F3` is the **dest** path (`rcx = r15`), `cmp rax, [rdi+18h]`. Cloak of `vcruntime!memcpy` cannot satisfy the source check.
- Walker live-range call `0x3E483E7`: `Hasher(rbx, end-start)`. Record hash `0x3E48500` is a 0x18-byte stack blob, not the image.

**New RVAs**

| Факт | RVA |
|------|-----|
| Walker clones (size `0x1669`) | `0x3E48680` (data xref only), `0x3E49CF0` |
| Dispatcher → clone `0x3E49CF0` | `0x3E44E8A`, `0x3E451D5` |
| Walker Hasher sites | live range `0x3E483E7`; record `0x3E48500` |
| 45E8 dest expected | `[obj+0x18]` (source expected remains `[obj+0x10]`) |
