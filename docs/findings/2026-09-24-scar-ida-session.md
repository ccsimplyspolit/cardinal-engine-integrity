# SCAR audit, IDA session 660eb217

Срез RelicCardinal 16.3.11308.0. IDB `K:\aoe4_dlc\aoe4\gamesource\dump\ida-work\runtime_exe.i64`, imagebase `0x7FF7A5500000`. Сессия MCP `660eb217`, Hex-Rays готов, auto-analysis повторно не запускался. GUI за 30 с не зарегистрировался; headless открыт, пока файл никто не держал.

Каталог [SCAR_ANALYSIS](..\..\README.md): 2821 имя, окрестность AOE4HOOK 397 имён. Замкнутый статический CFG есть только у leaf без indirect. Подробный разбор сессии: IDA_SESSION.md.

## Что подтвердил Hex-Rays

- `Player_GetID` `0x19759F0`: чтение `DWORD` по `+8`, без вызовов.
- `Player_GetResources` `0x19740F0`: копия 40 байт с `+0x16C` в выходной буфер. Число 364 в псевдокоде равно `0x16C`.
- `Player_GetResource` `0x1974080`: декомпилятор оборвался; инструкции читают `float` по `player+index*4+0x16C` после проверки числа определений `/48`.
- `Player_SetResource` `0x1973D80` уменьшает запас через `0x1E21450`. Там observers `+1912/+1920`, virtual callback и событие `0x1E2FD70`.
- `AI_Enable` `0x293FA40` и dispatcher `0x29175D0`: TLS `+134` выбирает немедленный virtual `+16` либо очередь `0x2922980`.
- `LocalCommand_SquadEntity` kind `3` и `LocalCommand_SquadSquad` kind `4` сходятся в dispatcher `0x1AA5A50`. Тот ставит команду через TLS-слот `+128` и virtual `+48`. Текста пакета и второго клиента в теле нет.
- `SGroup_CountSpawned` считает объекты с `DWORD +340 != 0`. Это не `EGroup_Count`.
- `Entity_IsPartOfSquad`: VA регистрации `0x7FF7A6ED82A0` не является стартом функции в этой IDB.

## Чего сессия не делает

Прямой вызов обёртки из DLL по-прежнему упирается в TopValidator `0x3DDD02C`, если return address вне `RelicCardinal.exe`. Сессия не патчила `.text`, не ставила VEH и не подменяла адрес возврата. `SAFE` ни одному способу не присвоен. Server apply для command и win/FOW не доказан.

## Добавление той же даты, сессия 49813d37

Восемь AI-тел на той же IDB. `AI_IsEnabled` подтверждён: `Player+1578`, реестр `0x84C8C08`, gate `AIPlayer+4852`. `AI_IsAIPlayer` читает только `Player+1578`. `AI_LockEntity` и `AI_LockSquads` ставят callable в dispatcher `0x29175D0`; у группы squad сначала разворот `0x20E7DB0`. `AI_EnableAll` обходит весь реестр и при TLS `+134` зовёт `0x29753A0`, иначе `0x2922980`. `AI_DoString` ищет AIPlayer по integer id и исполняет непустую строку через `AIPlayer+0xFC8`; это не `ScarDoString` `0xAA9B00`.

## Добавление той же даты, сессия ca676c09

Десять Entity-тел. `Entity_GetPosition` копирует 12 байт с `+0x2C`/`+0x34` в выходной буфер. `Entity_GetID` при ненулевом объекте читает `DWORD +0xA0`. Health и max идут через virtual `+272` к float `+0x7C` и `+0x80`. Percentage при max `<= 0` возвращает 0, иначе helper `0x13E1EB0`/`0x13E1E10`. `Entity_FromID` при промахе бросает C++ exception. `Entity_GetSquad` по VA `0x7FF7A6ED82E0` не является стартом функции.

## Добавление той же даты, сессия 682d0040

`LocalCommand_Entity` уходит в `0x1A96300` (`Invalid entity command`), не в squad dispatcher `0x1AA5A50`. `LocalCommand_EntityBuildSquad` зовёт `0x1AA81C0` с литералом 3 и пишет `player+8` в descriptor. `LocalCommand_Player` и `LocalCommand_PlayerUpgrade` при id `-1` бросают `Invalid player command` и сдают команду через TLS `+128`, virtual `+48`. `PlayerSquadConstructBuilding` записывает высоту обратно во входные позиции. `Player_CanSeeEntity`: null entity — false, null player — true. `Player_ClearAvailabilities` пишет байт `3` в дерево `player+0x518`. `Player_GetEntities` пересобирает кэш-группу `__Player%dEntities`. Девять имён (`Player_RestrictBuildingList`, `Player_SetSquadProductionAvailability` и ещё семь) в регистрации этого среза отсутствуют: адрес в IDA не передавался.

## Добавление той же даты, сессия d23c5b7b

`EGroup_Count` — `(end−begin)>>3`. `EGroup_CountSpawned` считает объекты с битом 8 в `+216` через `0x20E74F0`; у `SGroup_CountSpawned` другой критерий, `DWORD +340`. `EGroup_Create` при занятом имени бросает exception. `EGroup_Add` пишет identity `+0xA0` и пропускает дубликат. `GetEntityAt` / `GetSpawnedEntityAt` — индекс с 1, вне диапазона ошибка `0x3618A40`, разные развороты `0x20E6F00` и `0x20E70F0`. `EGroup_CreateIfNotFound` и девять соседних SGroup/EGroup имён в регистрации отсутствуют.

## Добавление той же даты, сессия 6ba7c866

`SGroup_Count` и `SGroup_Clear` совпадают по формуле с EGroup, но `SGroup_Create` держит реестр на `a1+40`, не на `+32`. `SGroup_Add` пишет `squad+0xA0` без фильтра `0x21E20C0` и без проверки nullptr. `GetSquadAt` разворачивает через `0x20E7DB0`, `GetSpawnedSquadAt` через `0x20E7F50`. `SGroup_ForEach` вызывает `ForEachEx` с флагами 1,0 и поэтому идёт по spawned-набору. Callback исполняется через TLS `+192` и `0x3DABD50`.

## Добавление той же даты, сессия 246dc5a4

`World_GetPlayerAt` нумерует с 1: индекс 0 и слишком большой индекс бросают C++ exception, слот `-1` возвращает 0. `World_GetAllNeutralEntities` очищает переданную группу и пишет в неё identity сущностей без owner. `World_GetGameTicks` и `World_GetGameTime` по зарегистрированным VA не являются стартом функции. `Squad_GetID` читает `DWORD +0xA0`. `Squad_FromID` при промахе бросает exception через lookup `0x1ADF190`. `Squad_GetFirstEntity` на пустом squad (`+320 == 0`) уходит в ошибку `0x3618A40`. `FOW_PlayerExploreAll` после пути Reveal всегда вызывает `0x1BC520`.

## Добавление той же даты, сессия 9f21d4f6

`Squad_GetBlueprint` кладёт в выходной буфер `squad+0x38` и vtable `0x22B0730`. `Squad_IsValid` на id 0 возвращает false и не бросает exception, в отличие от `Squad_FromID`. `Squad_IsAlive` — thunk `0x1E00E40`: сущность жива, если в `+216` есть бит `0x10` и нет `0x400`. `Squad_IsIdle` и `Squad_IsMoving` зовут один `0x1E04540` с id по `+56` и `+60`. `FOW_PlayerUnRevealAll` и `FOW_PlayerUnExploreAll` повторяют каркас Reveal с другими apply (`0x2134D90`, `0x2134FC0`). `FOW_UIRevealAll` идёт через глобал `0x7F41EA0`, а `FOW_UIUnRevealAll` только гасит там байт. `FOW_ForceRevealAllUnblockedAreas` ставит байты `+89` и `+5` без игрока.

## Добавление той же даты, сессия ee465e80

`Squad_GetPosition` копирует те же 12 байт, что `Entity_GetPosition`. `Squad_GetPlayerOwner` делает unbox `0x4004E0` от `squad+0x58`. `World_IsMultiplayerGame` читает байт глобала `0x84952B0+1`. `World_IsGameOver` истинен, когда состояние `> 1` и не `6`. `World_SetPlayerLose` зовёт `0x188CF20` с режимом `8`; у победы режим `5`. `World_GetPlayerCount` по зарегистрированному VA не является стартом функции. `Player_IsSurrendered` читает байт `player+0x619`. `Player_GetUIColour` собирает четыре байта r,g,b,a. `AI_UnlockSquad` ставит callable в тот же dispatcher, что и lock.

## Добавление той же даты, сессия 6c58fce0

`Entity_IsAlive` — `(флаги +216 & 0x410) == 0x10`, без чтения float. `Entity_IsValid` на id 0 возвращает false и не бросает exception. `Entity_IsCamouflaged` по зарегистрированному VA — три байта и постоянный 0. `Player_IsAlive` читает байт `+0x618 == 0`, `Player_IsSurrendered` — соседний `+0x619`. `Player_IsHuman` требует нулевые `+0x618` и `+0x62A`. `AI_IsLocalAIPlayer` проверяет флаг `+1578` и наличие записи в реестре, gate `+0x12F4` не читает. `AI_UnlockAll` шлёт в dispatcher только `player+8`.

## Добавление той же даты, сессия d7ebf349

`World_OwnsEntity` и `World_OwnsSquad` истинны, когда unbox `+0x58` дал 0: это отсутствие владельца, не id мира. `AI_GetDifficulty` без AIPlayer возвращает 127, иначе `DWORD +4872`. `AI_GetPersonality` без AIPlayer возвращает строку `Null Player`, иначе строку `+4880`. `AI_SetDifficulty` только ставит callable в dispatcher. `Player_GetRelationship` на null даёт 3, иначе байт матрицы. `Entity_Spawn` кладёт код 11 и зовёт `0x1E74100`; это не `Entity_Create`. `Squad_SetPlayerOwner` меняет владельца через `0x1E1B8F0` и `0x1E1B840`.

## Добавление той же даты, сессия ca497429

`Entity_IsBuilding` проверяет бит глобального id в наборе `entity+56`, аргумента типа нет. `Entity_IsUnderConstruction` смотрит virtual `+336` и dword `+40`. `Entity_GetBlueprint` кладёт `entity+56` и vtable `0x22AEF40`, не тот vtable, что у squad. `Entity_QueueProductionItemByPBG` ставит предмет через `0x1963CB0` и возвращает char. `Squad_IsOfType` ищет тип в определениях по `+264`. `Squad_IsGatheringResourceType` истинен, когда предикат `0x1E04540` принимает id ресурса и не принимает idle-id. `Player_ObserveRelationship` в этом теле совпадает с чтением матрицы `Player_GetRelationship`.

## Добавление той же даты, сессия e5a20c15

`AI_EnableEconomyOverride` кладёт строку из `0x293F5B0` и флаг в dispatcher. `AI_DisableAllEconomyOverrides` и `AI_RestartSCAR` шлют только `player+8`. `AI_RestartSCAR` не является `ScarDoString`. `AI_SetResourceIncomeDesire` сверяет индекс с числом ресурсов `/48` и stock `+0x16C` не пишет. `AI_GetPersonalityLuaFileName` отдаёт имя через `0x2926220`. `AI_DebugLuaIsEnabled` — постоянный 0. `Entity_GetBuildingProgress` считает `1 - (остаток +40 / полный +44)` у компонента virtual `+336`.

## Добавление той же даты, сессия cb7a6e31

`Entity_GetStateModelBool` ищет имя в определениях по `+1752` и читает байт через `0x15AD3E0`. `Entity_SetStateModelBool` при неизвестном имени выходит молча, иначе пишет через `0x1EE65C0`. `Entity_IsEBPOfType` берёт битовый набор с `*(entity+8)`, а `Entity_IsOfType` с `entity+56`. `Player_ClearPopCapOverride` пишет три `FLT_MAX` по `+0x484`, `+0x488` и `+0x48C` и других вызовов не делает. `Entity_SetInvulnerableMinCap` передаёт в `0x1EB7FA0` целую часть `max(0, value) * 8`.

## Добавление той же даты, сессия 16a7273f

`Entity_GetProductionQueueItem` и `Entity_GetProductionQueueItemType` делят один каркас: virtual `+176`, мир из TLS `+128` и `qword_7FF7AD948A20`, шаг записи очереди 144. Возврат предмета — virtual `+16` записи, возврат типа — virtual `+8`. Оба бросают исключение при пустом компоненте и при индексе за концом. `EGroup_FilterResource` вырезает совпавшие сущности из исходной группы, это не снимок. `FOW_UnExploreAll` игрока не принимает и зовёт `0x2134FC0` без хвоста `0x1BC520`. `FOW_UndoForceRevealAllUnblockedAreas` обнуляет только байт `+89`. `Player_CanPlaceStructureOnPosition` на пустой группе бросает `Group is empty`. Virtual `+48` после копии группы идёт в `qword_7FF7AD9D6CA0` (RVA `0x84D6CA0`), это не глобал command submit `qword_7FF7AD9D6C30`.

## Добавление той же даты, сессия 23fa7b85

`Player_GetAIType` (`0x1977030`) возвращает только байт `player+0x62A`. `Player_GetStartingPosition` (`0x19725A0`) копирует 8 байт с `+0x61C` и DWORD `+0x624` в выходной вектор; первый аргумент — выход. `Player_GetSlotIndex` (`0x19725C0`) ищет `player+8` в глобале RVA `0x84C7E18`, шаг записи 448, и возвращает поле `+96` плюс 1. `Player_GetResourceRate` не читает запас `+0x16C`: 40 байт берутся по `DWORD player+0x25C`, float индекса умножается на 8. `Player_NumUpgradeComplete` читает дерево по `player+0x550` и возвращает DWORD узла `+20` либо 0.

## Добавление той же даты, сессия bceb78eb

`Player_SetPopCapOverride` (`0x19763A0`) пишет переданный float в `+0x484` и `FLT_MAX` (`0x7F7FFFFF`) в `+0x488` и `+0x48C`. `Player_ClearPopCapOverride` заполняет все три слота `FLT_MAX`. `World_DistancePointToPoint` (`0x1955CC0`) берёт только float `+0` и float `+8`, средний `+4` пропускает, и прыгает в корень `0x3D3E5D0`. `World_IsReplay` (`0x1955900`) читает байт `+4` или `+13` объекта глобала RVA `0x84C7E18`. `Player_SetStateModelFloat` при отличии значения пишет float в мир и увеличивает DWORD `+44` и `+52`.

## Добавление той же даты, сессия 93206fcc

`World_Pos` (`0x1956700`) пишет три float в выходной вектор и мир не читает. `Player_GetSquads` (`0x19742B0`) очищает кэш-группу шаблона `__Player%dSquads` и заполняет её из списка `player+0x6A0` длиной `+0x6A4`, пропуская сквад через `0x21E20C0`. `Player_GetAllEntities` (`0x19748A0`) делает то же с шаблоном `__Player%dEntities`, но список id сидит за смещением `player+0x69C`, begin `+36`, длина `+40`, без этого предиката. Оба возвращают саму группу. `World_GetSquadsNearPoint` и `World_GetEntitiesNearPoint` делят запрос `0x1E51E00` и точку из float `+0` и индекса 2. Сквад проходит, когда `0x21E20C0` истинен; сущность — когда он ложен. Обоим нужен бит 8 флагов `+216`. `EGroup_ForEach` зовёт `0x21DFFF0` с флагами 1 и 0.

## Добавление той же даты, сессия a41e5b21

`AIPlayer_GetLocal` (`0x29926A0`) ищет DWORD объекта `+8` в реестре RVA `0x84C8C08` и при промахе возвращает 0. Отдельной проверки локальности нет. `AIPlayer_PushScoreMultiplier` (`0x29C8A60`) и `AIPlayer_PopScoreMultiplier` (`0x29C8AB0`) работают с таблицей `*(AIPlayer+0x1000)+0x890`, но зовут разные функции: `0x2C0A470` и `0x2C0A600`. Null-объект у обоих делает `ret`, не обнуляя `rax`. `AIPlayer_UpdateGathering` (`0x2993D10`) — одна инструкция `retn 0`. `AIPlayer_SetAbilityPriorityOverride` и `AIPlayer_SetAIAbilityPriorityOverride` оба входят в диспетчер `0x29175D0` разными лямбдами.

## Добавление той же даты, сессия 37d8c0ce

`AIProductionScoring_CanPushProductionScoringFunction` (`0x2C58960`) возвращает байт `*(AIPlayer+16032)+148`. Остальные разобранные scoring-функции при нулевом байте бросают `This function can only be called within a production scoring context`, увеличивают счётчик `+144` и вставляют узел через `0x2664320`. Сам расчёт очков в этих телах не выполняется. Три fitness-функции делят vtable RVA `0x6527638` и отличаются байтом узла `+33`: allied `2`, strongest `0`, weakest `1`. Пороги обязаны лежать в `[0,1]`, нижний строго меньше верхнего.

Имена окрестности без единственной регистрации остаются `UNKNOWN`. `UI_Remove` имеет две цели, `0xAC25A0` и `0x1130EE0`. `UI_SetPlayerDataContext` имеет `0xAC2620` и `0x1131DF0`. Ни одна из конфликтующих целей не выбрана.

## Добавление той же даты, сессия 3ebb71dc

Ещё десять scoring-вставок используют тот же контекст `*(AIPlayer+16032)` и `0x2664320`. `GroupNotProducedRecently` отвергает период меньше `0.125` (биты `0x3E000000` по RVA `0x844DF38`). `LackOfSecuredResourceDeposits` требует, чтобы нижний float был строго меньше верхнего и оба были больше нуля. `InverseRandomIntScore` копирует целое из `*(*(контекст+8)+0x1018)+0x6F8` в float узла и само число не бросает. `LuaScoringFunction` забирает refcount вызываемого объекта и тело Lua не вызывает.

## Добавление той же даты, сессия 3d00d8c7

`AIProductionScoring_MaxPopCapPercentage` принимает float только из `[0,1]` и пишет рядом байт `+28`. `MaximumGameTime` и `MinimumGameTime` оба кладут float в `+24`, но vtable разные: `0x6527110` и `0x6527138`. `MinimumTeamControlledSacredSites` пишет DWORD, не float. `MaxScoringFunction` и `MultiplyListScoringFunction` переносят три указателя вектора в узел и обнуляют их у вызывающего; vtable `0x65277A8` и `0x6527898`.

## Добавление той же даты, сессия 983eced6

`AIProductionScoring_NotProducedRecently` использует тот же порог `0.125`, что и групповой вариант, но vtable `0x6527820`, не `0x65277F8`. `NoUpgradeProductionBlockedByThisProduction` пишет id из определений `+216` даже когда поиск вернул `-1`. `PercentOfResourcesOwned` и `InversePercentOfResourcesOwned` — разные vtable, `0x6526EC0` и `0x6526E98`. Три `PlannedPlacement*` тоже не взаимозаменяемы: score и IsMoreThan пишут float, Valid дополнительных полей не имеет.

## Добавление той же даты, сессия a112adf2

`AIProductionScoring_RandomChoiceFromRange` читает семя из `*(*(контекст+8)+0x1018)+0x700` и обратно его не пишет. Шаг — `1664525 * state + 1013904223`, повторённый `a2` раз. В узел кладётся `1.0`, если `state % делитель` равен цели, иначе `0`. `RandomIntScore` это семя не трогает: он копирует целое с `+0x6F8`, как `InverseRandomIntScore`, но vtable `0x65278C0`. `PresenceOfEnemyTypes` и `PresenceOfMyTypes` создают узел через `0x26612C0` и `0x26615A0` и уничтожают входное дерево.

## Добавление той же даты, сессия 536b4c21

`ShouldConsiderNaval` копирует байт `+2` объекта по полю реестра RVA `0x84C8C08` со смещением `+80`, если байт AI `+59` и первый байт этого объекта ненулевые. `ShouldConsiderLimitedNaval` в тех же условиях копирует байт `+3`. `ShouldNotConsiderNaval` кладёт инверсию обоих байтов и ещё аргумент. `StrategicIntention` для строки `null` пишет id `-1` без поиска, остальные имена берёт из определений `+3288` и на промахе бросает `Invalid StrategicIntention`. `TimeToAcquire` при аргументе не больше нуля подставляет DWORD из `0x3FF740` по `+576`. `RemainingPersonnelPopCap` отвергает float меньше `1.0`.

## Добавление той же даты, сессия fb761797

Зарегистрированные `AIProductionScoring_*` окрестности хука закрыты. `AI_IsDebugDisplay` (`0x29402F0`) ищет id в реестре RVA `0x84C8C08` и затем делает `xor al, al`: возврат всегда 0. `AI_DebugLuaEnable` (`0x294A9B0`) — одна инструкция `retn 0`. `AI_ConvertToSimPlayer` (`0x294A770`) при null возвращает 0, иначе прыгает в `0x2922510`. `AI_SetDebugDisplay` после диспетчера `0x29175D0` обходит весь реестр и при нулевом байте TLS `+134` ставит лямбду в очередь `0x2922980`.

## Добавление той же даты, сессия ac737387

Чертежи ищутся в `qword_7FF7AD9464B8` (RVA `0x84464B8`) через `0x360FAF0`. Ability идёт с типом 0, reticule с `0x350000`, upgrade с `0x340000`, расовое расширение сущности с `0x130000`. Промах бросает `Cannot find "%s"`. `BP_GetSquadBlueprint` и `BP_GetSquadBlueprintByPbgID` — один и тот же хвост `0x19461D0`: обёртки побайтно совпадают. `BP_GetName` пишет в общий буфер. `Camera_GetOrbit` передаёт аргумент 3 в `0x1AEA670` после объекта глобала RVA `0x7B41F40`.

## Добавление той же даты, сессия 331da11e

`Game_GetLocalPlayerID` (`0xB275D0`) читает DWORD `+340` объекта `*(глобал RVA 0x7B41E28 + 816)`. `Game_HasLocalPlayer` (`0xB275B0`) истинен, когда этот DWORD не нуль. `Game_GetSPDifficulty` (`0xB81F70`) читает первый DWORD глобала RVA `0x84C7E18`, не байты реплея `+4` и `+13`. `Camera_SetInputEnabled` меняет только бит 0 DWORD `+228` глобала RVA `0x84C6BC8`. `Event_SaveWithName` ставит внутреннее SCAR-событие и сам файл не пишет. `Game_LoadGame` и `Game_LoadFromFileDev` делят проверки и перевод UTF-8, но загрузка разная: virtual `+16` против `0x7AB9B0`.

## Добавление той же даты, сессия 9aa5a3d8

`Game_SetPlayerSlotColour` и `Game_SetPlayerUISlotColour` — по одной инструкции `jmp` на `Game_SetPlayerColour` (`0xB28120`). Индекс цвета обязан быть от 1 до 16 и в очередь уходит уже уменьшенным на 1. Сам цвет пишет callback RVA `0xB765E0`. `Misc_AppendToFile` при нулевом байте RVA `0x84421BC` возвращает 0 и файл не открывает. `Misc_FindDepositsCloseToSquad` очищает переданную группу и наполняет её identity `+160` из запроса `0x1E9D410` по скваду `+0x2C`.

## Добавление той же даты, сессия 34314f15

`Misc_GetSimRate` (`0xB2BE30`) делит `1.0` на float по цепочке глобала RVA `0x7B41E28`: `+0x330`, затем `+0x1C0`, затем `+0x104`. `Misc_SetSimRate` (`0xB2BE60`) пишет в тот же float `1.0 / аргумент` и очереди не имеет. `Misc_GetSimDefaultStepsPerSecond` (`0xB2BE90`) возвращает константу `8.0`. `Misc_IsEntitySelected` смотрит только список выделения `+928`, `Misc_IsSquadSelected` — только `+952`. Оба ищут DWORD identity `+160`. `Misc_WriteFile` открывает файл режимом 2, `Misc_AppendToFile` — режимом 3; оба молчат, если байт RVA `0x84421BC` нулевой.

## Добавление той же даты, сессия 1d3e96b9

`Obj_GetCounterType` (`0x1AC8FB0`) читает DWORD `+0x30` объекта, найденного через мир TLS `+128` и смещение `+0x398`. Промах даёт `0xFFFFFFFF`. `Obj_SetCounterType` (`0x1AC9050`) пишет это поле только для значений от `-1` до `5`. `Modifier_ApplyToEntity`, `ApplyToPlayer` и `ApplyToSquad` сходятся в `0x23A6D20` и передают длительность как `int(value * 8)`, но дескрипторы разные: kind 3, kind 6 и kind 4. Пустой сквад отвергается по длине списка `+320`.

## Добавление той же даты, сессия 765bc2a3

`UI_IsReplay` (`0xB34FA0`) читает те же байты, что `World_IsReplay`: объект глобала RVA `0x84C7E18`, байт `+4` или байт `+13`. `UIWarning_Show` ставит строку в очередь вместе с фиксированными float `0.125`, `0.125` и `2.75` и возвращает id из `0xA24050`. `UI_CreateEventCueClickable` обрезает строки на 128 байт и хранит длительность как `int(value * 8)`, если float не меньше нуля. `UI_ModalVisual_Destroy` на id 0 выходит сразу.

## Добавление той же даты, сессия 210f3b37

Окрестность AOE4HOOK по зарегистрированным именам закрыта заметками. `getsimrate` (`0xB7F000`) читает тот же float, что `Misc_GetSimRate`: `1.0 /` поле по глобалу RVA `0x7B41E28`, цепочка `+0x330`, `+0x1C0`, `+0x104`. `getgametype` (`0xB7F1C0`) — байт `+1` глобала RVA `0x44952B0`, без проверки нуля. `app_currenttime` (`0xAE2180`) считает `(QPC − qword RVA 0x84CD088) * 1000 * double RVA 0x776B690`, обрезает к целому и делит на `1000.0`. `restart` (`0xB819F0`) пишет DWORD `+124` того же глобала симуляции значением 6 и только при DWORD `+120 == 5`, нулевом qword `+1320` и списке RVA `0x7B41DA0`/`0x7B41DA8`; отдельного вызова перезапуска нет. `dr_clear` (`0x376AE50`) и `dr_setdisplay` (`0x376AE90`) в IDB не размечены как функции: байты прыгают на virtual `+0x88` и `+0x38` глобала RVA `0x8448AA0`. `UI_SystemMessageShow` ставит строку в очередь магией `0xF82F052`. `__Internal_Game_SaveGame` при закрытых воротах фронтенда бросает `Front end unable to save` и сам файл не пишет.

## Добавление той же даты, сессия a7571422

Семьдесят коротких leaf вне окрестности хука. Байты IDB совпали с инструкциями дампа. `getlocalplayer` (`0xB7F0B0`) читает тот же DWORD `+340`, что `Game_GetLocalPlayerID`: объект `*(глобал RVA 0x7B41E28 + 816)`. `Player_GetSquadCount` (`0x1973910`) — DWORD `+0x6A4`. `Squad_Count` (`0x1998190`) — DWORD `+0x140`. `Misc_IsDevMode` (`0xBD9D40`) читает байт RVA `0x84421BC`, тот же адрес, что затвор `Misc_AppendToFile`. `Sound_ForceMusicEnabled` и `Sound_ForceSilenceEnabled` только читают соседние байты RVA `0x8449EB9` и `0x8449EBA`. Пустой `ret 0` (`C2 00 00`) не обнуляет EAX: так устроены `Squad_IncreaseVeterancyRank`, `UI_AutosaveMessageShow` и ещё семнадцать имён. `SAFE` не ставился.

## Добавление той же даты, сессия bb09158e

Ещё 31 leaf, 5–12 инструкций. `Game_GetSimRate` (`0xC00580`), `Game_SetSimRate` (`0xC00550`) и `setsimrate` (`0xB7FD60`) работают с тем же float `+0x104`, что `Misc_GetSimRate`: глобал RVA `0x7B41E28`, цепочка `+0x330`, `+0x1C0`. Запись кладёт `1.0 / аргумент`. `setsimframecap` (`0xB7FD90`) пишет соседний DWORD `+0x10C` и не опускает его ниже 1. `app_setidealframerate` (`0xAE2140`) пишет float `+0x344` самого глобала. `Entity_GetHeading` копирует 12 байт с `+0x20`/`+0x28` в выход. `World_DistanceSquaredPointToPoint` складывает квадраты float `+0` и `+8` без корня. `Entity_IsSpawned` — бит 3 байта `+0xD8`, null даёт 0. `EGroup_GetName` и `SGroup_GetName` — одни и те же 15 байт SSO. `Entity_ClearTagDebug` аргумент не читает.

## Добавление той же даты, сессия 33efa568

`Entity_IsActive` (`0x19D8340`) при null даёт 0. Иначе DWORD `+0xD8` должен дать маску `0x410 == 0x10` и установленный бит 3. `Vector_Lerp` (`0x1957030`) пишет в выход три компоненты `a + t * (b − a)`. `Team_GetRelationship` уменьшает оба id и без чтения памяти возвращает 3, 1 или 2. `EGroup_Remove` и `SGroup_Remove` — одни и те же 74 байта. `EGroup_Compare` и `SGroup_Compare` — одни и те же 84 байта: равный DWORD `+0x20` сразу даёт 1. `EGroup_IsValid` читает реестр `+0x20`, `SGroup_IsValid` — `+0x28`. `AI_SetPrefabActive` пишет байт `+0x2C`, `AI_SetPrefabCanReassign` — `+0x2D`. `World_GetLength` не сведён к полю: указатель закрыт двумя константами.

## Добавление той же даты, сессия 4fcb92ba

Чистые leaf без вызовов закрыты заметками. `Player_GetState` (`0xC02E50`) при попадании читает байт узла `+0x150`, при промахе — байт по абсолютному адресу `0x128`. `Squad_GetPositionDeSpawned` (`0x1997FD0`) усредняет float `+0x2C`, `+0x30` и `+0x34` и делит на длину `+0x140`; пустой список возвращает нулевой вектор. `Player_ObserveReputation` (`0x1973490`) при индексе вне 0..15 возвращает float 0, иначе float таблицы по `(idA << 4) + idB`. `Entity_RemoveBoobyTraps` (`0x19D9D70`) не содержит `call` и не читает аргумент сущности. `AIPlayer_IsTacticItemLocked` при промахе реестра читает адрес `0x1018`.

## Добавление той же даты, сессия 9038eb42

Шестнадцать SCAR-имён — один `jmp`. `Player_GetUnitCount` (`0x1973880` → `0x1E23150`) суммирует DWORD `+0x140` сквадов списка игрока `+0x6A0` длиной `+0x6A4`. `Squad_GetHealth` суммирует float `+0x7C`, но virtual `+0x108` не закрыт. `Player_CanSeeSquad`: пустой сквад даёт 0, null игрок даёт 1; нулевой третий байт требует одно попадание, ненулевой — все. `Entity_GetDebugEntity` при нулевом DWORD RVA `0x777D5D8` возвращает 0. `UI_IsQueueModifierDown` сам флаг клавиши не читает: прыгает с кодом `0xD9`, `0x87` или `0x8A`.

## Добавление той же даты, сессия 474f38cf

`App_SetMovieModeFramerate` и `App_ClearMovieModeFramerate` сходятся в `0x6735C0`. Известный код из таблицы RVA `0x5C338A0` пишется в DWORD `+0x340` глобала RVA `0x7B41E28` и копируется в DWORD RVA `0x7B41E30`. Неизвестный код, включая явное обнуление, оставляет 0 и печатает `Tried to start movie mode with an unknown framerate`. `Game_IsSaving` передаёт `*(глобал + 0x2E0)` в `0x17ABC40`: истина, если virtual `+0x48` истинен, или байт `+0xA` ненулевой, или байт RVA `0x7B41FD8` ненулевой и у узла SCAR DWORD `+0x14` равен 1. Слот virtual не закрыт. `Player_FindFirstEnemyPlayer` передаёт DL=1, `Player_FindFirstNeutralPlayer` — DL=3, в одно тело. `Squad_IsSiege` прыгает на `0x1DFE160`, и это не старт функции.

## Добавление той же даты, сессия a46c39c0

`MemoryStats_Enable` пишет 1 в байт `+0x58` синглтона, который при повторном вызове лежит в qword RVA `0x84CDFE8`. `MemoryStats_Disable` пишет в тот же байт 0. `Entity_IsInfantry` при null и при индексе `+0xB4 == -1` возвращает 0; иначе смотрит тип `0x130000` и бит глобала RVA `0x776ACD8`. `SGroup_CountAlliedSquads` передаёт режим 2, `SGroup_CountEnemySquads` — режим 1, в одно тело `0x21E2480`. Три сплайна камеры грузят глобал RVA `0x7B41F40` и отличаются только R8D: Linear 0, BSpline 1, Catrom 2. `Squad_IsUnderAttackByPlayer` обрезает `float * 8` так же, как сущность, и прыгает в `0x1E037B0`.

## Добавление той же даты, сессия 6fb83581

Обёртки очистки state model кладут на стек байт 0, передают его адрес и не читают байт обратно. У `*ClearStateModelTarget` адрес идёт в R8, у `*EnumTableTarget` — в R9. `Entity_SpawnDoNotAddPathfindingAndCollision` передаёт указатель на байт 2 в `0x1E74100`; это не `Entity_DeSpawn`, где EDX был 0. `SGroup_Destroy` при нулевом втором аргументе выходит сразу, иначе берёт реестр группы `+0x28` и DWORD `+0x20`. `Misc_IsSquadOnScreen` при null возвращает 0, иначе прибавляет к скваду `0x150`. `World_GetNeutralEntitiesNearMarker` и секторный близнец передают R9D=3 и нулевой RCX.

## Добавление той же даты, сессия 6b04caf6

`Squad_CanCaptureTeamWeapon` (`0x199C490`) при ненулевом втором аргументе зовёт `0x209A8F0` от объекта `+0x38` и всё равно возвращает 0. Результат вызова отбрасывается. `EGroup_Exists` читает реестр `+0x20` и истинен, если `0xC25460` вернул указатель. `SGroup_Exists` читает реестр `+0x28` и зовёт другой поиск `0xC25130`. `Camera_QueueRelativeSplinePanPos` передаёт R8D=0, `Camera_QueueSplinePanPos` — R8D=1, оба в `0x1809110` с глобалом RVA `0x7B41F40`. `AIPlayer_GetStateModelTargetListEntries` и `AllMarkers_FromName` возвращают исходный указатель, не результат своего вызова.

## Добавление той же даты, сессия 0639d897

`Vector_Length` (`0x1957000`) складывает квадраты float `+0`, `+4` и `+8` и прыгает в `0x3D3E5D0`, тот же корень, что у `World_DistancePointToPoint`. Средняя компонента здесь входит. `Squad_SuggestPosture` пропускает null и коды `3` и выше; коды `0..2` прибавляют к скваду `0x150`. `Squad_Kill` передаёт сквад `+0x118` и float `1.0` в `0x23DE680`. `AIEncounter_FormationPhase_GetExitCombatFitnessResult` при null возвращает `-1`, иначе float `+0x14`. `RulesProfiler_ResetTypeFilter` обнуляет RAX и читает байты с адреса `0`; строка вызывающего в фильтр не передаётся.

## Добавление той же даты, сессия f2bb3837

`Game_SkipEvent` (`0xB278B0`) ищет VM RVA `0x84CA6A8` по метке `0x53434152` и пишет 1 в байт `+0xD8`, если байт `+0xD9` не 0 и DWORD `+0xE4` не 1. Это тот же байт, что у `Event_Skip`. `EGroup_CountDeSpawned` вычитает из `(end-begin)/8` результат `0x20E74F0`, обхода `EGroup_CountSpawned`. `SGroup_CountDeSpawned` вычитает `0x20E82B0`. `Player_GetUpgradeTimeCost` переводит DWORD `+0x918` во float и умножает на `0.125`. `Camera_FollowEntity` пакует identity с байтом 3, `Camera_FollowSquad` — с байтом 4.

## Добавление той же даты, сессия ff509d10

`Camera_GetCurrentPos` и `Camera_GetCurrentTargetPos` оба зовут `0xDFBEB0` от глобала RVA `0x7B41F40` и копируют в выход 8 байт `+0x50` и DWORD `+0x58`. Различие имён в этих корнях не видно. `Entity_IsCuttable` и `Entity_IsInvincible` оба идут в `0x951260` от объекта `+0x38`: у первого байт `+0x73`, у второго `+0x76`. `Entity_GetMaxHoldSquadSlots` при промахе даёт 0, иначе DWORD `+0x1C`. `World_LeaveGameMatch` выходит без прыжка, если qword RVA `0x7B41DA0` равен `0x7B41DA8` или DWORD `+0x38` равен 6 или 7.

## Добавление той же даты, сессия b0e5e0af

`EBP_Exists` ищет имя в базе RVA `0x84464B8` через `0x360FAF0` с типом `0x130000` и истинен только если DWORD `+0x60` тоже `0x130000`. `SBP_Exists` использует тип `0x2E0000` и ту же проверку `+0x60`. `BP_GetType` при промахе возвращает `-1`, иначе DWORD `+0x60`. `Marker_GetProximityRadius` делает dynamic_cast объекта `+0x70`: промах даёт float 0, иначе float `+0x20`. `AIPlayer_PushUnitTypeScoreMultiplier` кладёт float в `0x2C0A470` на объекте `*(AI+0x1000)+0x8B8`.

## Добавление той же даты, сессия 0fd7d872

`Entity_IsStrategicPoint` истинен только если `0x71ED20` нашёл объект и его DWORD `+0x1C` равен 0. `Entity_IsVictoryPoint` использует тот же поиск и истинен, когда этот DWORD равен 1. `Entity_IsOnWalkableWall` берёт float `+0x2C` и `+0x34`, средний `+0x30` пропускает, и возвращает ответ `0x1E01F00`. `AI_GetAbilityMaxNumTargets` при null по `+8` даёт `-1`, при пустом указателе `+0xBB0` даёт 1, иначе DWORD `+8`. `Path_ShowCell` при разных концах списка RVA `0x8492AC0`/`0x8492AC8` дописывает упакованную клетку и увеличивает конец на 8.

## Добавление той же даты, сессия ce83cd79

`quit` (`0xAE1CA0`) на глобале RVA `0x7B41E28` всегда пишет байт `+0x542` = 0 и DWORD `+0x7C` = 9. Это то же смещение +124, куда `restart` пишет 6. Процесс эта функция не завершает. `Entity_IsEBPBuilding` берёт объект `+8`, требует DWORD `+0x60` = `0x130000` и проверяет бит глобала `0x776ACE0` через `0x407F30`. `Entity_IsVehicle` использует тот же вызов и тот же тип, но объект `+0x38` и бит `0x776ACDC`. `Misc_EnablePerformanceTest` при включении пишет 1 в байт `+0x25` объекта `*(global+0x10)+0x3B8` и прыгает в `0x8D6CA0`; при выключении пишет 0 и, если float `+0x50` не ноль, делит DWORD `+0x4C` на этот float в `+0x5C`. `Game_IsFtue` смотрит пару qword `0x7B41DA0`/`0x7B41DA8` и затем бит 17 DWORD `+0x28`.

## Добавление той же даты, сессия 22281743

`Squad_GetHeading` (`0x1997F50`) читает float `+0x20` и `+0x28`. Если сумма квадратов меньше `1e-6` (RVA `0x661E0C0`), в выход пишется `(0, 0, 1)`. Иначе компоненты делятся на корень, средний DWORD обнуляется. `Squad_HasAcceptedCommands` на null, пустом `+0x140`, индексе `-1` и нулевом TLS-объекте возвращает 1. Ноль возможен только когда DWORD `+0x20` найденного объекта равен 0. `BP_GetEntityArchetypeBlueprintForRace` пишет в выход `+8` элемент списка `+0xC30`, только если его DWORD `+0x60` равен `0x130000`. `Marker_GetProximityDimensionsOrDefault` при попадании dynamic_cast пишет float `+0x20` и `+0x24` в X и Z, Y всегда 0.

## Добавление той же даты, сессия 226cf79a

`Player_GetNumStrategicPoints` (`0x1974DC0`) обходит список DWORD длины `+0x110` и считает элемент, если `0x71ED20` нашёл объект с DWORD `+0x1C` равным 0. `Player_GetNumVictoryPoints` (`0x1974EB0`) использует тот же список и считает только `+0x1C == 1`. Это те же предикаты, что у `Entity_IsStrategicPoint` и `Entity_IsVictoryPoint`. `BP_GetSquadArchetypeBlueprintForRace` совпадает с вариантом сущности, но тип чертежа `0x2E0000`. `Squad_GetHoldSquad` возвращает второй объект TLS, если он ненулевой. `Squad_GetHoldEntity` возвращает результат `0x1E46780` только когда этот второй объект нулевой.

## Добавление той же даты, сессия c92a69c2

`Player_SetReputation` (`0x1973670`) при обоих id меньше 16 пишет float аргумента в слот `(idA<<4)+idB` таблицы объекта `+0x340`. Затем зовёт `0x1E41920` через объект `+0x308`, тот же хвост, что у `Player_SetRelationship`. `World_GetNumStrategicPoints` считает элемент мирового списка, если бит 3 DWORD `+0xD8` взведён и `0x71ED20` дал объект с DWORD `+0x1C` равным 0. `Squad_HasVehicle` требует тип `0x130000` и бит `0x776ACDC`. `Territory_ContainsSectorID` на том же поиске, что владелец сектора, возвращает 1, если DWORD `+0x74` не равен `-1`. `AIPlayer_GetDynamicUnitTypeMultipliersForEntity` этим срезом не закрыт: адрес начинается без пролога, а до первого `ret` вызовов больше, чем одно ребро графа на `0x407F30`.

## Добавление той же даты, сессия bba37971

`Entity_SetBackground` (`0x19DB890`) всегда передаёт маску `0x800`. Ненулевой аргумент идёт в `0x1E738D0`, который выходит сразу, если бит уже взведён. Нулевой аргумент идёт в `0x1E739F0`, который выходит сразу, если бит уже снят. `Camera_GetDeclination` читает слот с кодом 1, `Camera_GetDefaultOrbit` — с кодом 4, оба через `0xDFBEB0` и хвост `0x1AEA670`. `Camera_GetZoomDist` берёт объект через `0x1806680` и код 9. `Scar_Reload` ищет VM по глобалу `0x84CA6A8` и магии `0x53434152`, затем прыгает в `0x202B470`. `ShaderStats_SortPixelCount` пишет DWORD `+0xC` = 1, `ShaderStats_SortShaderNames` пишет туда 0.

## Добавление той же даты, сессия 361c2fd3

`Squad_IsRetreating`, `Squad_IsAttackMoving`, `Squad_IsCapturing` и `Squad_IsSettingDemolitions` зовут `0x472330`, затем передают в `0x1E04540` DWORD этого объекта: `+0x50`, `+0x54`, `+0x58` и `+0x60`. `AISquad_GetStateModelPlayerTarget` и `SquadTarget` кладут описание через `0x29BE770` и резолвят его вызовами `0x1E469F0` и `0x1E46900`. Варианты EnumTable копируют третий аргумент в R9 и зовут `0x29BE920`. `Camera_SetDeclination` кладёт входной float в XMM1 и прыгает в `0x1AE9EA0`; кода слота в корне нет.

## Добавление той же даты, сессия 98ccbbf2

`Camera_SetZoomDist` кладёт float в XMM1 и прыгает в `0x1AE9C80`. `Camera_SetDefaultZoomDist` — в `0x1AE9FB0`. `ShaderStats_Disable` пишет байт `+0` = 0 и, если qword `+0x10` и `+0x18` различаются, копирует начало в конец. `MemoryStats_Toggle` переворачивает байт `+0x58` объекта `0x3BCC860`. `Camera_FocusOnPosition` пакует точку с байтом вида 2 и зовёт `0x1AEAAD0`. `Entity_GetStateTreeTargeting_*` копируют третий аргумент в R9 и резолвят описание `0x19D2D30` теми же тремя вызовами, что цели AISquad.

## Добавление той же даты, сессия b50d9789

`AISquad_SetStateModelEntityTarget` при null передаёт нулевой байт в `0x29BEB00`. Иначе пакует байт вида 3 и DWORD `+0xA0`/`+0xA4`. EnumTable-вариант делает то же через `0x29BEBA0` и R9. `Squad_GetHealthPercentageWithShields` возвращает 0, если `0x1E067C0` дал float не больше 0, иначе хвост `0x1E06750`. `Physics_PurgeOrphans` при ненулевом объекте `*(глобал 0x7B41E98 + 0x50)` зовёт `0x1B4DC80` на `+8` и хвостом на `+0x10`. `Camera_FollowSelection` смотрит объект `*(0x84C6BC8 + 0x230)`: разные `+0x28` и `+0x30` уходят в `0x1807B00`.

## Добавление той же даты, сессия cc3a72ae

Сеттеры цели состояния пакуют один и тот же вид: сущность — байт 3 и DWORD `+0xA0`/`+0xA4`, отряд — байт 4 и те же поля, игрок — байт 6 и DWORD `+8`/`+0xC`. Null передаёт нулевой байт. AISquad без таблицы зовёт `0x29BEB00`, с таблицей — `0x29BEBA0`. Сущность зовёт `0x19E9590` или `0x19E9630`. `BP_GetSquadTypeExtRaceCount` ищет тип `0x2E0000` в базе `0x84464B8`. Промах даёт 0, попадание — DWORD `+0x38` результата `0x4866C0`.

## Добавление той же даты, сессия 47e64964

Сеттеры и удаления цели у отряда используют те же виды: игрок 6 и поля `+8`/`+0xC`, отряд 4, сущность 3, оба с `+0xA0`/`+0xA4`. Запись идёт в `0x19AF190`, таблица в `0x19AF300`, удаление из списка в `0x19AF230`. `Player_SetStateModelEnumTablePlayerTarget` и `SquadTarget` зовут `0x197EF50`. `Squad_RemoveSlotItemAt` при ненулевом `0x19AFBC0` уменьшает индекс на 1 и прыгает в `0x23EECD0`.

## Добавление той же даты, сессия d061cd6a

`BP_GetEntityChildBlueprintCount` ищет тип `0x130000` в базе `0x84464B8`. Промах даёт 0. Иначе указатель `+0x64` найденного чертежа уходит в `0x36102E0`. `BP_GetSquadChildBlueprintCount` делает то же с типом `0x2E0000`. `Squad_CanTargetSquad` при null передаёт нулевой байт в `0x1E0BE00`, иначе вид 4 и DWORD `+0xA0`/`+0xA4`. `Entity_Population` и `Squad_Population` на null дают float 0. `Squad_SBPGetMax` при null по `+8` обнуляет EAX и всё равно читает адрес `0x38`.

## Добавление той же даты, сессия 72826f09

`World_GetMetadataLayerBoolean`, `Integer`, `Number` и `PBG` ищут слой одним путём: объект `*(глобал 0x84952B0 + 0x70)`, вызов `0x23DC0B0`, затем dynamic_cast. Промах даёт 0. Попадание читает байт `+0x10`, DWORD `+0x10`, float `+0x10` или qword `+0x18`. `BP_GetEntityArchetypeBlueprintForPlayer` берёт DWORD игрока `+0x130` и `+0x134`, тип `0x220000`, и зовёт `0x19413F0`. Вариант отряда зовёт `0x19412F0`. `Game_RetrieveTableData` использует тот же объект данных `*(*(0x7B41E28+0x2D8)+0xE0)`, что и замок таблицы.

## Добавление той же даты, сессия 008d5822

`World_GetMetadataLayerString` на том же поиске, что остальные слои. Если qword `+0x18` меньше `0x10`, возвращает константную строку. Иначе указатель из начала строки. `Entity_StopAbility`, `Squad_StopAbility` и `Player_StopAbility` зовут `0x20C5220`, а при ненулевом результате — `0x20C24F0` со способностью `+8` и байтом флага. Виды те же: 3, 4 и 6. `setsimpause` читает DWORD `+0xF8` объекта `*(*(0x7B41E28+0x330)+0x1C0)` и сам этот dword не пишет. `Squad_HasActiveCommand` на пустом отряде и индексе `-1` даёт 0, в отличие от `Squad_HasAcceptedCommands`, который на тех же путях даёт 1.

## Добавление той же даты, сессия f50730af

Геттеры `Obj_*` разбирают объект так же, как `Obj_DeleteAll`: TLS `+0x80`, смещение `+0x398`, затем `0x4FA880` и `0x1F716C0`. `Obj_GetVisible` читает байт `+0x21`, `Obj_GetProgressVisible` — `+0x22`, `Obj_GetProgress` и `Obj_SetProgress` — float `+0x28`. `Obj_GetCounterVisible` и `Obj_GetSecondaryCounterVisible` читают один байт `+0x23`, и промах у обоих даёт 1. `Obj_GetShowColour` читает байт `+0x25`. `Obj_GetSecondaryCounterType` читает DWORD `+0x40`, промах даёт `-1`. `AIPlayer_IsOnAnIsland` смотрит объект `*(реестр 0x84C8C08 + 0x50)` и отвечает 1, если байт 0 равен 0, DWORD `+8` равен 0, или в списке есть запись с DWORD `+4` не меньше `0x3E8`.

## Добавление той же даты, сессия 9424c2c5

`Obj_SetProgressVisible` пишет байт в `+0x22`, `Obj_SetCounterVisible` — в `+0x23`, `Obj_SetSecondaryCounterVisible` — в `+0x24`, `Obj_SetShowColour` — в `+0x25`. Геттер вторичного флага читал `+0x23`, сеттер пишет `+0x24`. `Obj_SetCounterTimerSeconds` пишет float в `+0x34` только если DWORD `+0x30` уже равен 1. Вторичный таймер пишет в `+0x44` только если `+0x40` равен 1. `Obj_GetState` читает DWORD `+0x1C`, промах даёт 4. `AISquad_SetStateModelBool` при отличии байта увеличивает `+0x310` и `+0x320`, int — `+0x310` и `+0x31C`, float — `+0x310` и `+0x318`.

## Добавление той же даты, сессия 4e3c646d

Геттеры модели состояния при промахе имени возвращают третий аргумент, при null объекта — 0. У AIPlayer таблица лежит в `+0x11D8`, база значений в `+0x11E0`. У AISquad таблица в `+0x2F0`, база в `+0x2F8`. Слот имени bool — `+0x6D8`, int — `+0x738`, float — `+0x708`. `AISquad_GetStateModelVector3f` использует слот `+0x858` и копирует 8 байт плюс DWORD. `FOW_UnRevealTerritory` зовёт `0x2135490` только если байт `+0x618` равен 0.

## Добавление той же даты, сессия 59b5eb5d

Счётчики объекта открыты только для типов 2, 3, 4 и 5. `Obj_GetCounterCount` и `Obj_SetCounterCount` смотрят DWORD `+0x30` и читают или пишут `+0x38`. Максимум — `+0x3C`. Вторичный счётчик читается из `+0x48`, но геттер проверяет тип в `+0x30`, а сеттер — в `+0x40`. Вторичный максимум — `+0x4C` при типе `+0x40`. Промах и чужой тип дают `-1` и запись пропускают. `Obj_SetColour` собирает четыре байта в DWORD `+0x14`.

## Добавление той же даты, сессия e45d1646

`AISquad_SetStateModelEnumTableBool` пишет байт, только если первый DWORD 32-байтной записи равен 0. Int требует ключ 1, float — ключ 2. Все три при отличии увеличивают `+0x310` и `+0x314`. `AISquad_SetStateModelVector3f` копирует 8 байт и DWORD и увеличивает `+0x324`. `SBP_IsOfRace` ищет тип `0x2E0000` и сравнивает DWORD `+0x64` и `+0x68`. `EBP_IsOfRace` делает то же для типа `0x130000`. `FOW_RevealTerritory` и `FOW_PlayerUnRevealArea` проходят дальше только при нулевом байте `+0x618`.

## Добавление той же даты, сессия 20b39ce7

Геттеры enum-таблицы отряда используют те же ключи, что сеттеры: bool — 0, int — 1, float — 2, вектор — 3. Промах возвращает третий аргумент, null — 0. `AISquad_SetStateModelPBG` сравнивает три DWORD `+0x60`, `+0x64` и `+0x68` и при отличии увеличивает `+0x310` и `+0x32C`. `Squad_SetBackground` на каждого члена передаёт маску `0x800`: ненулевой флаг в `0x1E738D0`, нулевой в `0x1E739F0`. `FOW_PlayerRevealArea` проходит тот же байт `+0x618`.

## Добавление той же даты, сессия 5bee7419

`Loc_FormatTime_M_S` снимает целые часы делением на `3600.0` (RVA `0x661EA64`) и минуты делением остатка на `60.0` (RVA `0x661E8C4`). Если `0xC31800` вернул 0, печатает `Error formatting time.` через `0x3AE7570`. `Entity_RagDoll` на null выходит. Дальше нужны взведённый бит 4, снятый бит 10 и взведённый бит 3 DWORD `+0xD8`. При ненулевом qword `+0x68` найденной записи зовёт `0x1FFE120` с `R8B=1`. `World_GetAllSquads` на null даёт 0 и перед обходом сдвигает конец группы к началу.

## Добавление той же даты, сессия 6c830f3b

`FOW_RevealArea` после `0x1F06550` умножает радиус на `8.0` (RVA `0x661E7D0`) и усекает его. Запись `-1` и ненулевой байт `+0x618` пропускают вызов. Иначе точка вида 2 уходит в `0x21350F0`. `World_SetTeamWin` для игрока той же команды зовёт `0x188CF20` с кодом 5, для чужой — с кодом 8, затем `0x6995B0` с кодом 2 и взводит бит 1 DWORD `+0xA8` объекта `*(*(0x7B41E28+0x2D8)+0x28)`. `World_IsPointInPlayerTerritory` отвечает 0 только если оба байта таблицы `+0x40` равны 2. Индекс шире `0x10` даёт байт 0.

## Добавление той же даты, сессия 04fb47bc

`ShaderStats_Toggle` трижды берёт объект через `0x1A80F40`, инвертирует байт `+0` и копирует DWORD `+8` в `+4`. Если байт был включён и диапазон `+0x10`/`+0x18` не пуст, конец сдвигается к началу. `Obj_ShowProgress` и `Obj_ShowProgress2` отличаются только кодом в `0xB2D070`: 0 и 1. `Game_SkipAllEvents` открывает VM `0x84CA6A8` magic `0x53434152` и, пока байт `+9` не ноль, пишет байт `+8` = 1, если DWORD `+0x14` не равен 1. `BP_GetEntityParentBlueprintCount` ищет тип `0x130000` и считает родителей по указателю `+0x6C`. `AIPlayer_GetAnchorPosition` читает float `+0x61C` и DWORD `+0x624`, а в буфер ставит Y = 0. `UI_GetDecoratorVisibilitySquad` на null и промахе даёт 6, иначе байт `+0x28`.

## Добавление той же даты, сессия 67e67d4d

`BP_GetSquadParentBlueprintCount` ищет тип `0x2E0000` и считает родителей по указателю `+0x6C`. `BP_GetSimulationFloatProperty` читает слот имени `+0x1128`, int — `+0x1158`. Промах, индекс за счётчиком `+0x20` и слот `-1` дают 0. `Squad_RemoveStateModelListBool`, `Float` и `Int` ищут имя в `+0x918` и при живом отряде передают вид 4 и DWORD `+0xA0`/`+0xA4`. `Entity_GetStateModelVector3f` использует вид 3, `Player_GetStateModelVector3f` — вид 6 и DWORD `+8`/`+0xC`, `Squad_GetStateModelVector3f` — вид 4. Слот имени у всех трёх `+0x858`. `Player_GetMaxPopulationCap` читает float `+0x46C` и DWORD `+0x474`, трижды зовёт `0x21485C0` и выбирает результат байтом аргумента без проверки границы. `Camera_StartPan` пишет исходную точку в `+0x6C` объекта камеры `0x7B41F40`.

## Добавление той же даты, сессия 93ddfe66

`BP_GetEntityChildBlueprintAtIndex` ищет тип `0x130000` и берёт ребёнка по указателю `+0x64`. `BP_GetSquadChildBlueprintAtIndex` делает то же с типом `0x2E0000`. Промах пишет qword `+8` = 0. `BP_GetEntityParentBlueprintAtIndex` идёт по родителям `+0x6C`, пока счётчик не сравняется с индексом. `Player_SetResources` считает записи списка `+0x2E8`..`+0x2F0` шагом `0x30` и на каждый индекс зовёт `0x1973D80`. `Player_CompleteUpgrade` при null из `0x1F63010` зовёт `0x1EA3620` на поле `+0x264` и возвращает 1. Иначе пакует вид 6. `Squad_CanTargetEntity` на null даёт 0. Нулевой ответ `0x1E0B9A0` на `+0x150` тоже даёт 0. Нулевой флаг после этого даёт 1. `Obj_SetIcon` при живом объекте прыгает в `0x1ACB7A0` с полем `+0xA0`. `Terrain_GetCoverType_AsNumber` при null объекта возвращает DWORD `+4` результата `0x3624980`, иначе младший байт `0x2202ED0`.

## Добавление той же даты, сессия 7ccc18bb

`BP_GetSquadParentBlueprintAtIndex` ищет тип `0x2E0000` и кладёт родителя `+0x6C` с нужным номером в qword `+8`. Промах пишет 0. `Squad_SetResource` выходит, если индекс не меньше длины списка `+0x2E8`..`+0x2F0` шагом `0x30`. Иначе копирует блок `+0x10`/`+0x20`/`+0x30`, подменяет один float и зовёт `0x23FD8A0`. `UI_EnableSquadMinimapIndicator` пишет байт `+0x3A`, если DWORD `+0xC4` не `-1` и бит 4 байта `+0xC` взведён. `World_SetDesignerSupply` пишет байт `+0x9A` после `0x2053960`. `Player_GetMaxPopulationCapOverride` читает те же `+0x46C` и `+0x474`, затем заменяет результат float-ами `+0x484`, `+0x488` и `+0x48C`, когда они не равны `FLT_MAX` (`0x7F7FFFFF`, RVA `0x661EB30`). `Squad_GetLastAttacker` смотрит DWORD `+0xBC` и бит 4 байта `+0xC`, затем пакует вид 3.

## Добавление той же даты, сессия d61176d3

`Entity_SetStateModelFloat` ищет имя в слоте `+0x708`. При отличии float пишет его и увеличивает DWORD `+0x2C` и `+0x34`. `Squad_SetStateModelFloat` делает то же с видом 4. `Entity_SetStateModelVector3f` ищет слот `+0x858`, сравнивает три float и при отличии копирует 8 байт плюс DWORD, увеличивая `+0x2C` и `+0x40`. `Player_ResetResource` читает текущий ресурс по `+0x16C`. Если он больше 0, зовёт `0x1E21450`, затем пишет DWORD `+0x144` = 0. `Player_GiftResource` выходит, если модуль суммы не больше `1e-6`. Положительная сумма идёт в `0x1E20DD0`, отрицательная — в `0x1E21450`. `World_GetOffsetPosition` делит целый угол на `8.0` и умножает на `2*pi` (RVA `0x661E7AC`). `AI_CanSquadDecrew` отвечает 1, если байт `+0x2A8` не ноль, иначе если байт `+0x328` не ноль.

## Добавление той же даты, сессия ecaf1921

`Player_SetStateModelVector3f` использует вид 6 и DWORD `+8`/`+0xC`. `Squad_SetStateModelVector3f` — вид 4 и DWORD `+0xA0`/`+0xA4`. Оба пишут вектор слота `+0x858` и увеличивают `+0x2C` и `+0x40`, если три float различаются. `Obj_SetState` пишет DWORD `+0x1C`, если он ещё не равен новому состоянию, и при ненулевом байте `+0x21` шлёт событие типа `0x650000`. `Obj_Delete` при совпадении id уменьшает DWORD `+0xC`. `Territory_GetSectorContainingPoint` после `0x2053960` возвращает 0 для идентификатора 0 и `-1`. `Game_SendTributeSentEvent` ставит тип `0x980000` и в любом случае хвостом зовёт `0x3FBD80`.

## Добавление той же даты, сессия c74af8e1

`Obj_SetVisible` пишет байт `+0x21`. Ненулевой флаг копирует DWORD `+0x44` в `+0x2C`, нулевой пишет туда 0. Если показ включён и DWORD `+0x198` ещё 0, туда копируется тот же `+0x44`. Затем уходит событие типа `0x650000`. `AI_SetPrefabTarget_Position` при промахе реестра, null `+0x1050` или отсутствии записи с DWORD `+0x48` возвращает 0. Попадание пакует точку вида 2 и возвращает 1. `Misc_GetControlGroupContents` читает список `*(0x84C6BC8+0x198)` по `+0x400` шагом `0x30`. Индекс за длиной уходит в поздний выход.

## Добавление той же даты, сессия cdb0c23f

Геттеры цели enum-таблицы ищут имя в слоте `+0x8E8`. Сущность пакует вид 3 и DWORD `+0xA0`/`+0xA4`, игрок — вид 6 и DWORD `+8`/`+0xC`. Промах пишет нулевой байт дескриптора и всё равно зовёт резолвер: сущность `0x1E46780`, игрок `0x1E469F0`, отряд `0x1E46900`. `Entity_SetStateModelInt` ищет слот `+0x738` и передаёт значение в `0x1EE6640`. `Player_SetStateModelBool` ищет слот `+0x6D8` и передаёт байт в `0x1EE65C0`. `memtofile` собирает имя `memtofile_%s.csv` и пишет файл. `AI_CombatFitnessGetSquadArchetypePBGs` и структура отличаются вторым вызовом: `0x29A22E0` и `0x29A1F50`.

## Добавление той же даты, сессия ec0047d4

Три геттера цели отряда ищут слот `+0x8E8` и пакуют вид 4. Резолверы те же: сущность `0x1E46780`, игрок `0x1E469F0`, отряд `0x1E46900`. `Player_SetStateModelInt` и `Squad_SetStateModelInt` ищут `+0x738` и зовут `0x1EE6640`. `Squad_SetStateModelBool` ищет `+0x6D8` и зовёт `0x1EE65C0`. `Entity_GetStateModelFloat` при промахе имени даёт float 0, `Entity_GetStateModelInt` и `Player_GetStateModelInt` дают 0, `Player_GetStateModelBool` и `Squad_GetStateModelBool` дают байт 0. `Loc_FormatNumber` при нулевом ответе `0x36342E0` печатает `Error formatting number.`

## Добавление той же даты, сессия e75e8b76

`Squad_GetStateModelFloat` ищет слот `+0x708` и при промахе даёт float 0. `Squad_GetStateModelInt` ищет `+0x738` и при промахе даёт 0. Оба пакуют вид 4. Сеттеры enum-таблицы сущности, игрока и отряда используют одни слоты: bool `+0x6D8` и хвост `0x1EE68C0`, int `+0x738` и `0x1EE6960`, float `+0x708` и `0x1EE6A00`. Виды 3, 6 и 4. Проверки ключа записи в корне нет: индекс enum уходит в хвост. `Entity_GetStateModelEnumTableBool` при промахе даёт байт 0.

## Добавление той же даты, сессия ae8ce360

`Entity_GetStateModelEnumTableFloat` ищет слот `+0x708` и при промахе даёт float 0. `Entity_GetStateModelEnumTableInt` ищет `+0x738` и при промахе даёт 0. Индекс enum уходит в `0x1988B30` и `0x1988A80`. `Entity_SetStateModelEnumTableVector3f` копирует 8 байт и DWORD из слота `+0x858` и зовёт `0x1EE67E0`. Игрок делает то же с видом 6, отряд — с видом 4. `Squad_SetStateModelListEntityTarget` ищет имя в `+0x918`. Null цели пакует нулевой вид, живая цель — вид 3 и DWORD `+0xA0`/`+0xA4`. Отряд пакуется видом 4 и уходит в `0x19BD880`.

## Добавление той же даты, сессия 858d1a49

`Squad_SetStateModelListBool`, `Int`, `Float` и `Vector3f` ищут имя в слоте `+0x918` и пакуют отряд видом 4. Если хвост вернул ненулевой байт, корень увеличивает DWORD `+0x2C` и `+0x50`. `Squad_SetStateModelListPlayerTarget` пакует игрока видом 6 и DWORD `+8`/`+0xC`. `Squad_SetStateModelListSquadTarget` пакует цель видом 4. `Squad_GetRace` при промахе типа `0x220000` смотрит объект `+0x58` и указатель `+0x630`: предпочитает `+0x18`, иначе `+0x10`. `Setup_SetPlayerName` при попадании id игрока зовёт `0x1DEDF80` на поле `+0x63C` и хвостом уходит в `0x3FC060`.

## Добавление той же даты, сессия df4a1beb

`Squad_AddSlotItemToDropOnDeath` при годном предмете дописывает 16-байтную запись и увеличивает DWORD `+0x18`. `Squad_IsAbilityActive_CS` отвечает 1, если способность активна у отряда вида 4 или у любого члена списка `+0x13C` вида 3. Иначе 0. `AI_FindConstructionLocation` при промахе реестра `0x84C8C08` копирует в выход точку `(-10000, -10000, -10000)`, RVA `0x6166050`. `World_GetAllEntitiesOfType` при индексе имени `-1` в слоте `+0xA8` выходит, иначе сдвигает конец группы к началу. `AIPlayer_GetOwnedMilitaryPointEntitiesInRange` квадратит радиус и обходит список `+0xEC8` по диапазону `+0x230`..`+0x238`.

## Добавление той же даты, сессия 78000659

Обычные геттеры цели сущности, игрока и отряда ищут имя в том же слоте `+0x8E8`, что и enum-варианты. Индекса enum нет. Виды те же: 3, 6 и 4. Резолверы те же: `0x1E46780`, `0x1E469F0` и `0x1E46900`. Промах пишет нулевой байт дескриптора. `Player_ClearStateModelTarget` при индексе не `-1` пакует вид 6 и зовёт `0x1EE6480`. `Entity_EnableStrategicPoint` на null выходит. Нулевой флаг дополнительно зовёт `0x2064C40` с `R8B=1`, затем всегда `0x1E73D70`. `cmdline_string` при ненулевом байте `+0x20` копирует строку `+0x28` в глобальный буфер RVA `0x7795A68`.

## Добавление той же даты, сессия d59ad434

`Player_SetStateModelEntityTarget` `0x19783B0`, `Player_SetStateModelPlayerTarget` `0x1978250` и `Player_SetStateModelSquadTarget` `0x1978300` ищут имя в слоте `+0x8E8`. Индекс `-1` выходит. Живая цель пакуется видом 3, 6 или 4. Хвост `0x1EE6480`. Владелец у первых двух — вид 6. `Squad_SetMoveType` `0x199C4C0` пишет DWORD `+0x64` и `+0x68` объекта типа в `+0x14` и `+0x18`, если DWORD `+0x20` ещё ноль. `AISquad_FindFilteredCoverCompareCurrent` после поиска всегда копирует в выход три float `-10000` из RVA `0x6166070`. `AI_SetPrefabTarget_Waypoints` при промахе реестра `0x84C8C08` или null `+0x1050` возвращает 0. `UI_CreatePositionKickerMessage` пакует вид 2 и зовёт `0xB270C0`. `Camera_StartDeltaOrbit` и `Camera_StartOrbit` — два входа одной функции IDA с `0xC126E0`. Пять рёбер графа в окне не достигнуты. У delta виден косвенный слот `+0x30`.

## Добавление той же даты, сессия c8dbab87

`Event_StartEx` `0x202E100` зовёт `0x20452C0` на объекте `+0xD0`. Затем уменьшает счётчик по `+8` обоих аргументов. Счётчик меньше 1 освобождает блок `0x18`. `World_GetAllSquadsOfType` `0x195B270` ищет имя в слоте `+0x108`. Индекс `-1` уходит в поздний выход. Совпавший индекс дописывает qword `+0xA0` в группу шагом 8, а при заполненной ёмкости зовёт `0x485B40`. `LocalCommand_PlayerSquadConstructField` `0x1A9F580` дважды берёт TLS `+0x280` через `0x4005F0`, переписывает 8 байт обеих точек и зовёт `0x1A9D890` с `R9B=2`. Постановка команды не доказывает репликацию.

## Добавление той же даты, сессия e74c7e99

`BP_IsUpgradeOfType` `0x193F120` при нулевом указателе `+8` возвращает 0. Живой путь ищет имя в слоте `+0xD8` и при индексе не `-1` хвостом зовёт `0x1F57720`. `Entity_SetPosition` `0x19D3880` передаёт точку в `0x1E759B0` с `R8B=1`. DWORD `+0xB4`, если не `-1`, через TLS-таблицу `0x8448A20` слот `+0x80` приводит к `0x1E90730`. Хвост `0x1E7B5D0`. Прямой записи координат в корне нет. `Entity_SetHeadingGroundSnapOptional` вместо этого зовёт `0x2086C20` с двумя float точки и двумя флагами. `Obj_SetObjectiveFunction` копирует строку в слот `index*16+0x158` объекта из TLS `+0x398`, без проверки границы. `Scar_RemoveInit` обходит список `+0x198`..`+0x1A0` шагом `0x30` и при совпадении уменьшает конец на `0x30`. `Event_EnterProximity` передаёт строку `ProximityEnter` и код 0 в `0xC1F8F0`. Exit использует код 1 и `ProximityExit`, While — код 2 и `ProximityTimer`. Подписка внутри `0xC1F8F0` не разобрана.

## Добавление той же даты, сессия c2fabd6b

`Entity_CreateFacing` `0x19D2E70` при ненулевом флаге пишет float в `+4` точки после `0x1E4A8E0` с `R9D=7`. Идентификатор `-1` из `0x1FFDC50` возвращает 0, иначе указатель из TLS-таблицы. Создание внутри `0x1FFDC50` не разобрано. `UI_CreateSimpleSquadKickerMessage` проходит ворота `EDX=7`, требует DWORD `+0x154` не ноль и пакует вид 4 с тремя нулевыми float. Сущность проходит ворота `EDX=5` и биты 3 и 4 DWORD `+0xD8`, вид 3. `LCWatcher_RemoveFilter` `0x3722BA0` при совпадении строки `+0x20` уменьшает qword `+0x30` глобала RVA `0x84464D8`. `Entity_SetWorldOwned` выходит, если байт `+0x1C` объекта из `+0x38` не ноль. Иначе float `+0x2C` и `+0x34` уходят в `0x2053AB0`. `HintPoint_AddToEntity` делает `lock xadd` DWORD `+8` у `*(0x84C6BC8+0x238)` и пакует вид 3. Отряд пакует вид 4.

## Добавление той же даты, сессия 8d7ff6c5

`Entity_SpawnToward` `0x19D3CA0` возвращает 0, если бит 3 DWORD `+0xD8` установлен. Иначе точка из двух float источника и ответа `0x1E4A8E0` уходит в `0x1E759B0` с `R8D=0`, разница с целью — в `0x2086C20` с `R8B=1`, и возврат `AL=1`. `Squad_RewardActionPoints` `0x199F330` ищет ресурс в списке `+0x2E8` шагом `0x30` по глобалу RVA `0x8495170`. Промах даёт индекс `-1`, и float суммы всё равно пишется по этому индексу. Затем `0x1E20DD0` с `R9B=3` и тип `0x670000` в `0x19AEF80`. Постановка не доказывает репликацию. `AIEncounter_FormationPhase_GetSquadsAvailableAtEnd` обходит два списка и дописывает DWORD `+0x58`. Успех возвращает `AL=1`. Null из `0x293F6F0` выходит, не записывая `AL`.

## Добавление той же даты, сессия dea31861

`Entity_SetPlayerOwner` `0x19D42F0` выходит, если указатель из `0x4004E0` на `+0x58` совпал с новым владельцем. Иначе старый владелец получает `0x1E1AC00`, новый — `0x1E1AA60`. Ненулевой байт `+0x1C` объекта из `+0x38` тоже выходит. Иначе float `+0x2C` и `+0x34` уходят в `0x2053AB0`. Прямой записи владельца в корне нет. `Obj_SetTitle` `0x1AC8520` пишет текстовую пару в слот `+0x50` объекта из TLS `+0x398`. Нулевой второй DWORD пишет нулевую пару, `-1` дополнительно зовёт `0x1ACECB0` на `+8`, положительный и отличающийся копирует два qword в `+8` и `+0x10`. Совпавшая пара не пишется. `Obj_SetDescription` `0x1AC8690` делает то же в слот `+0x68`.

## Добавление той же даты, сессия 360b8ccc

`World_SetSharedLineOfSightEnabledAndMergeExploredMaps` `0x19587B0` сливает карты только если `0x2047AA0` вернул не ноль, байт флага равен нулю и байт `+4` результата `0x6DE1B0` не ноль. Индекс берётся из старшего DWORD игрока `+8`. После копирования DWORD `+8` и `+0x18` двух записей обнуляются. `LocalCommand_PlayerPlaceAndConstructFencePlanned` `0x1A9E550` пишет float в `+4` обеих точек, ищет метку `SCAR` (`0x53434152`) в глобале RVA `0x84CA6A8` и зовёт `0x1A9D890` с `R9B=1`. Сплайн planned использует помощник `0x1A9EB30`, constructed — `0x1A9F050`. Постановка команды не доказывает репликацию.

## Добавление той же даты, сессия 3f4eae0c

`AIPlayer_GetStateModelPBG` `0x29BAA20` ищет имя в слоте `+0x9D8`. Индекс `-1` и второй DWORD записи `-1` возвращают 0. Список лежит на `+0x11D8`, длина `+0x24C0`, шаг 8. `AISquad_GetStateModelPBG` читает тот же слот с объекта `+0x2F0`. `AISquad_GetStateModelEnumTablePBG` требует ключ DWORD 5 и шаг записи 32. `BP_GetSquadTypeExtRaceBlueprintAtIndex` `0x1940F90` ищет тип `0x2E0000` в базе RVA `0x84464B8`. Индекс не меньше длины `+0x38` оставляет qword `+8` выхода нулевым. Общий выход пишет vtable RVA `0x63FCA58`. Двоичный поиск после проверки длины и часть веток PBG не дочитаны.

## Добавление той же даты, сессия 4075bdca

`LocalCommand_PlayerPlaceAndConstructEntitiesPlanned` `0x1A9E2A0` пишет один и тот же float в `+4` обеих точек и зовёт `0x1A9D890` с `R9D=0`. Метка `SCAR` та же, RVA `0x84CA6A8`. Постановка не доказывает репликацию. `Game_GetTerrainTypeVariables` `0xBFF8E0` копирует 16 байт в lua-стек, если индекс `+4` не `-1`. Младшие 4 бита байта `+8` должны быть 5. Иначе лог `LuaConfig.cpp` строка `0x4FD` и запись DWORD по адресу 0. Затем добавляется строка `tt_none`. Это чтение lua-конфига. `Obj_Create` `0x1AC80B0` в окне дошёл до объекта TLS `+0x398`. Создание не достигнуто.

## Добавление той же даты, сессия 768e8e6e

`Obj_Create` `0x1AC80B0` берёт объект из TLS `+0x398` через `0x1F711F0`. Null возвращает 0. Иначе заголовок пишется в `+0x50`, описание в `+0x68`, строки в `+0xA0`, `+0xC0`, `+0x80` и при ненулевом аргументе в `+0xE0`. DWORD `+0x28` становится 0, байт `+0x22` становится 0. Возврат — DWORD, который уже лежал в `+8`. `UI_CursorShow` и `cursor_show` зовут `0x3565290` и прыгают в слот vtable `+0x28`. Скрытие использует слот `+0x18`. Цель слота не доказана. `getmapname` читает глобал RVA `0x84C7E18`, поле `+0x2DA0` и слот `+0x30`.

## Добавление той же даты, сессия b2e8fa42

`Entity_SimHide` `0x19DA420` при ненулевом флаге ставит бит `0x19` DWORD `+0xD8`, при нулевом снимает его, и пишет DWORD обратно. Затем слот vtable `+0x10` объекта `+0xB8`. Цель слота не доказана. `Misc_ScreenshotExt` `0xB7FBC0` копирует `0x10` байт в глобал RVA `0x84CE78C` и пишет DWORD RVA `0x84CE788` = `-1`. `Marker_StopActionById` читает глобал RVA `0x7B41E98`, поле `+0xD8`, затем `+0x48`, и прыгает в слот `+0x60`. `Entity_GetInvulnerableMinCap` при null возвращает float 0. `Camera_GetPivot` и `Camera_Unclamp` лежат внутри функции камеры с `0xC126E0`. Их короткие срезы не отделены.

## Добавление той же даты, сессия cb0489df

Четыре геттера обзора сущности зовут слот vtable `+0x160`. Null сущности или null из слота возвращают float 0. Иначе внутренний радиус — float `+0x20`, внутренняя высота — `+0x24`, внешний радиус — `+0x28`, внешняя высота — `+0x2C`. `Entity_GetTargetingType` `0x19DCE30` при промахе слота `+0x4D0` возвращает байт 2, иначе байт `+0x10`. `Entity_SetTargetingType` `0x19DCDB0` пишет этот байт в `+0x10` объекта из слота `+0x4C8`. `Entity_GetWeaponHardpointCount` читает DWORD `+0x14` объекта из слота `+0xF0`. `Entity_SetProjectileCanExplode` пишет байт в `+0x4C` объекта из слота `+0x178`. Цель слота не доказана.

## Добавление той же даты, сессия c3170502

`Entity_VisHide` `0x19D4E40` ставит или снимает тот же бит `0x19` DWORD `+0xD8`, что и `Entity_SimHide`, и прыгает в слот vtable `+0x10` объекта `+0xB8`. `Entity_StopFire` `0x19DB730` через слот `+0x2F8` пишет DWORD `+0x10` = 0 и зовёт `0x1F005F0`. `Entity_IsPlannedStructure` `0x19D97C0` возвращает 1, только если бит 5 байта `+0x80` объекта из слота `+0x150` установлен. `UI_IsXboxUI` читает глобал RVA `0x7B41E28`, указатель `+0x20`, и слот `+0xE8` с `EDX=1`. `memdump` копирует литерал `log:` и не читает свой аргумент. `AI_GetAnySquadCombatTarget` при байте 2 или 5 возвращает указатель `0x1E46900`; байты 0, 1 и больше 6 возвращают 0. Цель vtable-слотов не доказана.

## Добавление той же даты, сессия 4a4ae65f

`Entity_SetMeleeBlocksPerAttacks` `0x19DD070`, `Entity_SetRangedBlocksPerAttacks` `0x19DD0B0` и `Entity_SetProjectileBlocksPerAttacks` `0x19DD0F0` зовут слот vtable `+0xE8` и пишут два слова в DWORD `+0xDC`, `+0xE4` и `+0xEC`. Младшее слово берётся из DX, старшее из R8W. `Entity_IsUnderAttack` `0x19D6740` умножает float на 8.0 из RVA `0x661E7D0` и обрезает к целому перед хвостом `0x1EB77F0`. `Entity_DisableCancelConstructionCommand` `0x19DDAB0` кладёт флаг в бит 6 байта `+0x80` объекта из слота `+0x148`. `Entity_IsBurning` возвращает 1, если float `+0x10` больше float `+0x1C`. Цель слотов не доказана.

## Добавление той же даты, сессия 27c5e0bd

`Entity_IsAttacking` `0x19D6A80` умножает float на 8.0, обрезает к целому и возвращает 1, если ответ `0x2214780` не больше этого целого. Слот vtable `+0xF0`. `Entity_ForceSelfConstruct` `0x19D7E00` ставит бит 2 байта `+0x80` объекта из слота `+0x148`, затем `0x244B660` и хвост `0x1E13AB0`. `Entity_GetFilledHoldSquadSlots` `0x19D8D80` читает DWORD по адресу TLS плюс индекс из `+0x10` плюс `0xE8`. `Squad_HasDestination` возвращает 0, если DWORD `+0x1D4` равен `-1`. `Scar_DebugCheatMenuExecute` выходит при нулевом байте `+0x2D0` глобала RVA `0x7B41E28`. Цель слотов не доказана.

## Добавление той же даты, сессия c45dbeeb

`Entity_SetOnFire` `0x19DB6D0` через слот `+0x2F8` берёт float из `0x1EFF670` на `+0x38`, прибавляет 1.0 из RVA `0x661E3CC` и зовёт `0x1F01790` с `R8B=1`. `Entity_IsVaultable` `0x19D98E0` возвращает 1, если объект слота `+0x150` null или его DWORD `+0x28` равен 0. `Misc_Screenshot` `0xB7FBF0` у объекта `[глобал RVA 0x7B41E28 + 0x10]` пишет WORD `+0x368` = 0, qword `+0x3A8` = 0 и байт `+0x3B0` = 1. `AIEncounter_Cancel`, `AIEncounter_ForceComplete` и очистка целей читают указатель `+0x60` и DWORD `+8` и зовут `0x29975D0`. Сброс внутри помощника не разобран.

## Добавление той же даты, сессия 76463db1

Десять тел `AIEncounter_*` читают указатель `+0x60` и DWORD `+8` и зовут `0x29975D0` через реестр RVA `0x84C8C08`. `AIEncounter_CombatGuidance_SetSpreadAttackers` дополнительно кладёт байт флага в функтор. Само действие внутри `0x29975D0` не разобрано. `Misc_RemoveFile` `0x3746820` при нулевом байте RVA `0x84421BC` возвращает 0. Иначе переводит путь страницей `0xFDE9` и при ненулевом ответе зовёт `0x3AFD900`. `dr_terrainrect` при живом глобале RVA `0x8448AA0` передаёт строку `TerrainLine` в слот vtable `+0x1D8`.

## Добавление той же даты, сессия 4d4dcdc0

Двенадцать сеттеров `AIEncounter_*` читают указатель `+0x60` и DWORD `+8`. Одиннадцать кладут в функтор байт флага из DL. `AIEncounter_Notify_SetPlayerEventEncounterID` `0x29488D0` кладёт DWORD аргумента. Вызов `0x29975D0` у этого шаблона прочитан на `AIEncounter_CombatGuidance_SetSpreadAttackers`. В этом окне он не повторялся. Сброс внутри помощника не разобран.

## Добавление той же даты, сессия 8a859097

У двенадцати имён нет границы функции в инвентаре IDA, но байты по зарегистрированному RVA читаются. `Entity_IsCasualty` (`0x19DA450`) возвращает бит 6 DWORD `+0xD8`. `AI_ConvertToSimSquad` при null даёт 0, иначе прыгает в `0x2B2AA00`. `Cursor_Distance`, `Cursor_Info` и `Cursor_WeaponRanges` инвертируют байты RVA `0x844A1E9`, `0x844A1E8` и `0x844A1EB` и не пишут EAX. `Entity_IsMoving` при живом индексе `+0x1D4` прыгает в слот vtable `+0x108`. Цель слота не доказана.

## Добавление той же даты, сессия d1e680c3

`Game_IsPaused` (`0xB272A0`) возвращает байт `+0xE1` глобала RVA `0x84C6BC8`. Это не DWORD `+0xF8`, который читает `setsimpause`. `Game_LockRandom` после разбора TLS увеличивает DWORD `+0x3C`, `Game_UnLockRandom` его уменьшает. `Entity_TagDebug` пишет DWORD `+0xA0` в RVA `0x777D5D8` и `+0xA4` в `0x777D5DC`, затем прыгает в `0x20345D0`. `Marker_GetName` при qword `+0x30` меньше `0x10` возвращает указатель на `+0x18`.

## Добавление той же даты, сессия 23d385b6

`Player_GetEntityCount` (`0x1973890`) берёт DWORD `Player+0x69C` как индекс, ищет запись в таблице TLS RVA `0x8448A20` и возвращает DWORD `+0x28`. Это не длина списка. `Sim_CheckRequirements` инвертирует байт RVA `0x776AB58` и не пишет EAX. Остальные десять имён этого окна (`Scar_DrawMarkers`, `Scar_GroupInfo`, `Scar_GroupList`, `Sim_DebugDrawSimTick`, `Sim_DrawEntityCrusherOBB`, `Sim_DrawEntityExtensions`, `Sim_EntityDelay`, `Sim_EntityDrawPosture`, `Sim_EntityHistory`, `Sim_EntityInfo`) так же инвертируют отдельные байты в районе RVA `0x844A99A`–`0x844ABBE`. Границы функции в инвентаре IDA у них нет.

## Добавление той же даты, сессия 505cf600

`UI_SetSquadDecoratorAlwaysVisible` (`0xB366F0`) при null и при индексе DWORD `+0xC4` равном `-1` выходит без записи. Иначе берёт запись TLS RVA `0x8448A20`. Бит 4 байта `+0xC` должен быть установлен, тогда младший байт флага пишется в `+0x39`. `UI_IsCivSpecificMenuOpen` (`0xB37FA0`) возвращает 1, если байт по `*(*(глобал RVA 0x7B41E28 + 0x2D8) + 0x288)` равен `0x0C`. Десять имён `Weapon_*` и `Sim_EntityOOCTarget`, `Sim_SimBox`, `Sim_EntityOBB` инвертируют отдельные байты `0x844A36B`–`0x844AE59` и не пишут EAX. Границы функции в инвентаре IDA нет.

## Добавление той же даты, сессия 34c1438b

`Squad_EnableSurprise` (`0x199AFA0`) при null и при индексе DWORD `+0xBC` равном `-1` выходит без записи. Бит 4 байта `+0xC` записи TLS RVA `0x8448A20` открывает запись младшего байта флага в `+0x1E`. `Squad_SetInvulnerableEntityCount` (`0x199BF80`) пишет DWORD аргумента в `+0x98` и усечённый `max(0, float)`, умноженный на константу RVA `0x661E7D0`, в `+0x9C`. Индекс — DWORD `+0xB0`. Null, индекс `-1` и сброшенный бит обнуляют rcx и всё равно выполняют эти две записи по абсолютным `0x98` и `0x9C`. `World_EnableReplacementObjectForEmptyPlayers` (`0x195D750`) разбирает qword глобала RVA `0x84942F0` двумя константами и пишет флаг в `+0x4A`. `Squad_GetMax` прыгает в `0x212D4C0`, возврат в окне не виден. `Squad_IsUnderAttack` и `Squad_IsAttacking` рано возвращают 0 и прыгают в `0x22401E0` и `0x2240260`; на входе хвоста `-1` в DWORD `+0x14` или `+0x18` тоже даёт 0. Сами хвосты не закрыты. `Sim_EntityModifier` копирует инвертированный байт RVA `0x844A99D` ещё и в `0x844AAA8`.

## Добавление той же даты, сессия 91f02df7

`Squad_GetInvulnerableEntityCount` (`0x199BFE0`) возвращает DWORD `+0x98` той же записи TLS, куда `Squad_SetInvulnerableEntityCount` пишет счётчик. Индекс — DWORD `+0xB0`. Null, индекс `-1` и сброшенный бит 4 байта `+0xC` обнуляют rax и всё равно читают абсолютный адрес `0x98`. Поле `+0x9C` этот геттер не читает. `Squad_SetMoodMode` (`0x199EF80`) пишет младший байт флага в `+0x1C` при индексе DWORD `+0xBC` и установленном бите 4. `Squad_IsHoldingPosition` (`0x19A40C0`) в тех же воротах возвращает байт `+0x1F`, иначе 0. `Squad_IsInBackground` (`0x19A2010`) при нулевом DWORD `+0x140` возвращает 0. Иначе индекс `+0x13C` читает DWORD из записи TLS RVA `0x8448A20`, и бит 11 DWORD по адресу запись плюс тот DWORD плюс `0xD8` становится ответом. `Squad_AdjustAbilityCooldown` прыгает в `0x20C1010`, `Squad_ClearPostureSuggestion` прибавляет `0x150` и прыгает в `0x1E0C4A0`. Оба хвоста не закрыты.

## Добавление той же даты, сессия e20ca9ff

Двенадцать коротких тел с неразрешённым слотом vtable. Цель слота не доказана. `Entity_IsProductionQueueAvailable` (`0x19D59A0`) через слот `+0xB0` берёт индекс DWORD `+0x54` и возвращает 1, если младшее слово ответа слота `+8` записи TLS RVA `0x8448A20` равно 0. `Entity_ActiveCommandIs` (`0x19D5740`) возвращает 1, если аргумент равен DWORD по указателю из `+0x10`, а если там `-1` — по указателю из `+0x14`. `Misc_SetDesignerSplatsVisibility` сначала пишет флаг в байт RVA `0x8449EB8`. `RulesProfiler_Activate` при нулевом байте RVA `0x7B421D5` выходит, иначе пишет CL в `0x7B421FC`. `LCWatcher_Activate` всегда пишет флаг в байт `+0x18` глобала RVA `0x84464D8`. `UI_IsXboxControllerUI` требует два ненулевых ответа слота `+0xE8` с `EDX=1`. `UI_IsXboxKBMUI` вызывает тот же слот сначала с `EDX=1`, затем с `EDX=0`. `UI_PickIDForInputMode` при любом нулевом ответе возвращает первый аргумент, иначе второй. `Physics_GetNumRBodies` суммирует ответы слотов `+0x60` и `+0x68`. `dr_drawCircle`, `dr_text2d` и `dr_text3d` зовут слоты `+0x130`, `+0x110` и `+0x108` глобала RVA `0x8448AA0`.

## Добавление той же даты, сессия 2272c891

`Entity_HasAbility` (`0x19DA8C0`) через слот `+0x1B0` выбирает поле `+0x20`, если байт `+0x3D` равен 0, иначе `+0x2C`. DWORD этого поля индексирует TLS RVA `0x8448A20`, а следующий DWORD, сдвинутый влево на 3, задаёт длину списка qword. Совпадение с `[аргумент+8]` даёт 1. `Squad_HasAbility` (`0x19A01D0`) сначала ищет тот же qword в записи индекса `+0xB4` по полям `+0x30` и `+0x34`, затем у членов списка `+0x13C` длиной `+0x140` через слот `+0x1A8`. `Squad_SetRecrewable` (`0x199EEA0`) тем же списком членов зовёт слот `+0x3D8` и пишет флаг в байт `+0x14`. `Squad_HasWeaponHardpoint` получает индекс двумя вызовами через qword RVA `0x56E03C8` и `0x56DFBF0`, затем слотом `+0xF0`. `AISquad_IsRunningSquadTacticAbility` читает объект `+0x120`; слот `+0x40`, равный аргументу, даёт 1, иначе слот `+0x88` должен вернуть `0xE`. `Decal_RemoveAllDecalsAfterId` при идентификаторе ниже DWORD `+0x90` глобала RVA `0x84CBA68` делает `lock inc` DWORD `+0x190`. Цели слотов и вызовов через qword не доказаны.

## Добавление той же даты, сессия eb8e164c

`AI_ProductionGroupMaxNum` (`0x299A2B0`) ищет в списке `[AI+0xE00, AI+0xE08)` шаг `0x70` запись с DWORD `+0x6C`, равным аргументу, и возвращает DWORD `+0x64`. `AI_ProductionGroupMaxNumProduced` (`0x299A300`) возвращает DWORD `+0x68`. Промах обоих зовёт `0x3618A40` и попадает на `int3`. `Entity_DoBurnDamage` (`0x19DB670`) продолжает только если маска `0x410` DWORD `+0xD8` равна `0x10` и бит 3 установлен, затем через слот `+0x2F8` зовёт `0x1F01790`. `Sound_Stop` при аргументе `-1` выходит; иначе зовёт `0x382D340` между двумя вызовами через qword. Восемь сеттеров встречи кладут аргумент в функтор и зовут `0x29175D0` через реестр RVA `0x84C8C08`. Это другой адрес, чем `0x29975D0` у прежних `AIEncounter_*`. Слот `+0x20` уничтожает функтор, если он не на стеке. Действие внутри `0x29175D0` не закрыто.

## Добавление той же даты, сессия 347babff

Ещё двенадцать сеттеров встречи зовут тот же `0x29175D0` через реестр RVA `0x84C8C08` и уничтожают функтор слотом `+0x20`, если он не на стеке. Десять кладут float аргумента: пороги отступления и подкрепления, радиус связности отряда и `SetTargetArea`. `AIEncounter_FormationGuidance_SetFormUpAtEntityTarget` и `AIEncounter_TacticFilter_ResetAbilityPriority` кладут указатель аргумента, не число. Действие внутри `0x29175D0` не закрыто.

## Добавление той же даты, сессия 17bfbd60

`Entity_HasUpgrade` (`0x19D95D0`) через слот `+0x1D0` берёт индекс DWORD `+0x10` и зовёт `0x1EA3380` с указателем `[аргумент+8]`. Ненулевой EAX даёт 1. `Entity_ResetMeleeBlocksPerAttacks` копирует DWORD `+0xE0` ответа `0x408150` в `+0xDC` объекта слота `+0xE8`. Дальний бой копирует `+0xE4` в `+0xE4`, снаряд — `+0xE8` в `+0xEC`. Индекс `-1` читает эти DWORD с абсолютного адреса и всё равно пишет их в объект слота. `Marker_SetProximityCircle` выделяет `0x28` байт и записывает новый указатель в `+0x70`, а прежний ненулевой указатель зовёт слот 0 с `EDX=1`. `SetTargetLeash` кладёт float в `0x29175D0`. `DisableSquadPatrol` кладёт туда указатель `[аргумент+0xA0]`. `SetPriority` кладёт DWORD и float. `SetMoveExitParams` кладёт float и пару xmm2, xmm3. Тела `0x1EA3380`, `0x408150`, `0x23B35B0` и `0x29175D0` не закрыты.

## Добавление той же даты, сессия d6cc0398

`Entity_GetResource` (`0x19DCC60`) после `0x3624980` делит `[+0x2F0 минус +0x2E8]` на 12. Индекс вне длины, null или null слота `+0x4A0` дают float 0. Иначе читается float `[+0x14+индекс*4]`. `Entity_AddResource` (`0x19DCA20`) прибавляет аргумент к тому же смещению через слот `+0x498`. Промах поле не пишет. `Entity_ClearPostureSuggestion` пишет байт `+0x34` = `0x33` в объект слота `+0x218`. `Entity_IsHardpointActive` при индексе меньше DWORD `+0x14` зовёт `0x19D1CE0` и возвращает 1, если ответ ненулевой. Два `SetTargetPosition` копируют 8 байт аргумента и DWORD `+8` в `0x29175D0`. `LockTacticItemForAISquad` и `UnLockTacticItemForAISquad` кладут три указателя в тот же вызов, vtable `0x650E848` и `0x650E880`. Тела вызовов не закрыты.

## Добавление той же даты, сессия 8fd2c372

`Marker_SetProximityRectangle` кладёт два float в `0x23B3A50` и пишет новый указатель в `+0x70`. `Marker_SetProximityPoint` выделяет `0x20` байт, зовёт `0x3B347D0` и тоже пишет блок в `+0x70`. Прежний указатель зовётся слотом 0 с `EDX=1`. `Entity_SuggestPosture` при коде меньше 3 пишет этот код в байт `+0x34` и float в `+0x20` объекта слота `+0x218`. `Entity_CanAttackNow` возвращает 1, если младший байт ответа слота `+0x18` равен 5. `GetCameraNameFromPbgName` после `0x36126B0` возвращает буфер RVA `0x85C92E0`. `AISquad_FindSafePositionInEncounterLeash` при ненулевом ответе `0x2B7B480` пишет два float и нулевой средний DWORD; при нуле копирует константы. Пять сеттеров встречи снова кладут аргументы в `0x29175D0`. Тела вызовов не закрыты.

## Добавление той же даты, сессия 59b5f624

`Entity_ExtensionEnabled`, `Entity_ExtensionExecuting` и `Entity_ExtensionName` одинаково сравнивают байт аргумента с `+0x6C` и зовут `0x1E7A360`. Первая возвращает 1 при ненулевом ответе. Вторая берёт бит 6 байта `+0xC`. Третья зовёт слот `+0x150` и возвращает указатель. `Entity_IsProducingSquad` возвращает 1, если запись списка шагом `0x90` совпала по DWORD `+0x64` и `+0x68`. `Squad_NumUpgradeComplete` суммирует ответы `0x1EA3380` по членам. `World_GetOffsetPositionRelativeToFacingTarget` при совпадении трёх float копирует их, иначе зовёт `0x400CB0` и пишет смещённую позицию. `Entity_GetSquadsHeld` добавляет записи в группу через `0x485B40` и возвращает 1, если DWORD `+0x98` не нуль. Три сеттера снова кладут аргументы в `0x29175D0`. Тела вызовов не закрыты.

## Добавление той же даты, сессия 45bf051e

`Squad_GetMaxEntityDropOffDistance` (`0x19A3E50`) после `0x727DB0` обходит членов и оставляет в xmm6 максимум выбранных float. Null и пустой обход дают float 0. Индекс берётся из DWORD `+0x4C` объекта первого вызова, слот члена `+0x4E8`. `Squad_GetSquadsHeld` (`0x199CF90`) если конец выходной группы не равен началу, ставит конец равным началу, затем через слот `+0x1F8` добавляет записи вызовом `0x485B40`. Возвращает 1, если у какого-либо внутреннего объекта DWORD `+0x98` не нуль. `Entity_SetDemolitions` (`0x19D9B50`) при null второго аргумента и null слота `+0x2C8` даёт 0. Дальше слот `+0x4F8`, поиск по TLS и вызов `0x2129F20`. Успех возвращает 1. Тела вызовов и цели слотов не закрыты.

## Добавление той же даты, сессия 4af77be3

Девять `BP_Get*BlueprintByPbgID` ищут в базе RVA `0x84464B8` через `0x360FCE0`. Null и DWORD `+0x68` в диапазоне `0x7FFFFFFF..0xFFFFFFFE` зовут `0x3618A40` и попадают на `int3`. Иначе указатель пишется в выход `+8`, vtable в `+0`. Типы: ability `0`, entity `0x130000`, move `0x200000`, pass `0x270000`, map pool `0x1C0000`, AI ability `0x200`, formation coordinator `0xD0200`, formation target priority `0xC0200`, state-model tunings `0xF0200`. `UI_SetTutorializedWidgetsRequired` пишет флаг в байт `+0x4CC`, если `0x32B8ABE` вернул ненулевой байт. `memdumpf` копирует строку RVA `0x65B9738` и зовёт `0x3AF9750` и `0x3B6B540`. `AIEncounter_ResourceGuidance_IsSquadGroupEqual` при пустом диапазоне и при DWORD `+0x10` не меньше 2 уходит в `int3`, иначе прыгает в `0x2941100`. Хвост сравнения не закрыт.

## Добавление той же даты, сессия e69670dc

Три `BP_Get*ByPbgID` на той же базе: slot item тип `0x2C0000` / vtable `0x63FCA28`, upgrade `0x340000` / `0x62B5DC8`, weapon `0x3B0000` / `0x62AEE48`. `Misc_IsCommandLineOptionSet` (`0xBD9B20`) пропускает ведущие `-`; при нулевом байте RVA `0x844B2EF` зовёт `0x3C053E0` через qword `0x56DE598`, иначе `0x3AF23B0`. `Entity_SetAnimatorActionParameter` дважды зовёт `0x3B2FB10` и слот `+0x90` объекта `[сущность+0xB8]`. Семь UI/misc (`Game_QuitApp`, `HintPoint_RemoveAll`, `MapIcon_DestroyAll`, `Misc_AbortToFE`, `Misc_ClearSelection`, `Misc_ClearSubselection`, `Misc_RemoveCommandRestriction`) зовут `0x3642640`; при нулевом байте `+0x20` — слот 0 объекта `+0x10`, иначе `0x36427A0` с `EDX=0x19`.

Ещё двенадцать двухрёберных: `AIPlayer_CachedPathCrossesEnemyTerritory` хэширует EDX в таблицу `+0x3EB0` и сравнивает float с `0x2A9BCB0`. `AITactic_AICommandSquadMove` аллоцирует `0x58` байт, зовёт `0x2C742E0` и ставит в `tactic+0x78` через `0x2B51DF0`. `AI_GetAllMilitaryPointsOfType` обходит `[AI+0xEC8]+0x230` и дописывает identity `+0xA0` через TLS `0x8448A20`. Add/Remove exclusion area кладут позицию и два float в функторы `0x650E7D8` / `0x650E810` → `0x29175D0`. `AI_UnlockSquads` разворачивает группу `0x20E7DB0` и шлёт функтор `0x650EBC8`. `Camera_ClampToMarker` строит два функтора через `0xB547C0`/`0xB54700` и зовёт слот `+0x38` объекта камеры. `Decal_Destroy` — тот же UI-хвост с `EDX=0x1C`. `EGroup_GetClosestEntityInternal` ищет минимум xz² после `0x20E70F0`. `EGroup_RemoveNonHoldEntities` после `0x20E6F00` удаляет сущности с нулевым слотом `+0x200`. `Entity_SetAnimatorState` — слот `+0x18` у `[entity+0xB8]`. `Entity_SetRemainingResourceDepositAmount` — слот `+0xC8`, затем `0x1EC9AC0`/`0x1ECABD0`.

Ещё двенадцать: `Event_Delay` аллоцирует `0x38` байт и ставит таймер через `0x36B2610`/`0x2045EF0`. `FOW_RevealEntity` и `FOW_RevealSquad` идут через `0x1F06550` с типом sil `3`/`4`, затем `0x21350F0`. Девять Game/HintPoint сеттеров — UI-пакеты `0x3642640`/`0x36427A0` с разными размерами и полями (`EndSubTextFade` DWORD 3, `EndTextTitleFade` DWORD 2, `RequestSetLocalPlayer` 0/−1, `SetVisibility` указатель+байт, `SetDisplayOffsetInternal` 8+4).

Ещё двенадцать: `Loc_GetString` — `0x3D0FB90` и jump table `0x403470`. `Misc_AddRestrictCommandsMarker` совпадает по схеме с `Camera_ClampToMarker` (vtable `0x62AFBE8`/`0x62AFC20`). Circle/OBB/ClearControlGroup/DefaultCommands/SelectionInput/HideProgress/ShowProgressTimer — UI-пакеты с разными EDX. `Misc_SetEntitySelectable` сначала проверяет TLS индекс `+0xB4`. `Misc_GetScreenCenterPosition` читает float у `0x84C6BC8` и опционально зовёт `0xC5D690`/`0x32B8AC0`.

Ещё четырнадцать: `Player_GetEntitiesEGroup` обходит сущности игрока через TLS, фильтр `0x21E20C0` и слот `+0x508`, дописывает identity. `SGroup_ClearPostureSuggestion` / `SuggestPosture` разворачивают spawned `0x20E7F50` и зовут `0x1E0C4A0` / `0x1E0C350` на `squad+0x150`. `ContainsSGroup` / `ContainsSquad` сравнивают указатели или identity `+0xA0`. `Sound_SetForceMusic` / `SetForceSilence` пишут байты `0x8449EB9` / `0x8449EBA` и шлют UI-пакет. Остальные Sound_* и `Splat_Destroy` — UI-пакеты. `Squad_ExtensionEnabled` — `0x3FDE50` и `0x1E93810` с порогом `+0x54`.

Ещё четырнадцать: `Squad_ExtensionName` добавляет слот `+0x150`. `Squad_GetDestination` копирует через слоты `+0x108`/`+0xF8` после `0x1E8F310`. `Squad_GetInvulnerableMinCap` — `0x22AB1B0` или минимум по членам. `Squad_IsInAIEncounter` ищет AIPlayer и коды `0x25..0x2F` через `0x2A7C000`. Десять UI/Subtitle/Taskbar/Territory — пакеты `0x3642640`/`0x36427A0`.

Закрытие среза unclean two-edge (25 имён): Flash* берут lock inc на `0x84C6BC8+0x208` и шлют UI-пакеты; CoverPreview/CommandCard/Restrict/Pause/Subtitles/Decorators — те же `0x3642640`/`0x36427A0`. `UI_GetMarqueeRadius` и `UI_GetXboxCommandCardTab` идут через `0xC5D690`/`0x32B8AC0`. `World_GetTerritorySectorPosition` и `World_IsCurrentInteractionStageActive` — поиск `0x1F06550`. Локальные заметки на все имена с двумя рёбрами в static_cfg нанесены; recursive по-прежнему только при закрытых callees.

Начало трёхрёберных: восемь ForcedCombatTarget Add/Remove и LogDebug/SetDebugName/SetPatrolPath* кладут пакеты в `0x29175D0`. `Decal_Create` готовит дескриптор `0x38819E0` и UI-пакет. Цели слотов и тел вызовов не закрыты.

Ещё четырнадцать трёхрёберных: `SetTargetEntity`/`SetTargetSquad` — тип 3/4, `0x1EA0590`, аллок `0x28`, `0x29175D0`. `GetCachedPathLength` суммирует сегменты через `0x3D3E5D0`. `ProcessedPathSuccessful` читает байт `+0x18` той же таблицы. `GetOpponentPlayerAtIndex` — `0x293F870` и `0x1EDFDC0`. `GetStateModelEntityTarget` — слот `+0x8E8` и `0x1E46780`. `GetCurrentFallBackPosition` — коды `0x25..0x2F` и `0x1E46670`/`0x1E46D00`. DeepwaterFish / WaterLanes / IsAITargetable — булевы чтения без сети. `FindAISquadByID` прыгает в `0x2AC9730`. `ToggleDebugDisplay` — `0x29175D0` плюс обход реестра. Два `BP_GetAI*` — типы `0x200` / `0xD0200` в базе `0x84464B8`.

Ещё семь `BP_Get*Blueprint` по имени: типы `0xC0200`, `0xF0200`, `0x1C0000`, `0x200000`, `0x270000`, `0x2C0000`, `0x3B0000`; те же `0x36126B0`/`0x360FAF0`/`0x3618A40`.

Десять Entity трёхрёберных: `GetAttackTargetEntity`/`Squad` — `0x1801210`/`0x22BFAA0` и резолверы `0x1E46780`/`0x1E46900`. `GetLastAttacker` — `0x23E1130` + `0x1E46900`. `GetLastAttackers`/`GetLastEntityAttackers` — `0x23E0E50` и `0x485B40`/`0x4579E0`. Три `Get*BlocksPerAttacks` — слот `+0xE8` и `0x19E96E0`. `GetWeaponBlueprint` — `0x19D1CE0`. `IsResourceGenerator` — `0xB973A0`/`0x229F6E0`/`0x1DF7C30`.

Ещё двенадцать: StrategicPoint CapturedBy/Neutral; Enum_ToNumber/ToString; FOW_*SGroup; Formation_Place*; DeleteSaveGameDev; HasMatchTypeFlag; Ghost_*Spotting.

### unclean 3-edge remainder (14) — notes 1590

Closed Sound_PostEvent, Squad_CanCastAbilityOn{Entity,Squad,Position}, Squad_GetActiveUpgrades/LastAttackers/MinArmor/SpawnToward, UI_DestroyTagForPosition/FlashMenu/GetUICommandPBG, World_GetNumEntitiesNearPoint/GetPlayerIndex/GetRand. Capstone call targets: PostEvent→`0x382DC50`; ActiveUpgrades→`0x20242B0`/`0x199EDC0`/`0x3618A40`; UICmd type `0x5C0100`; FlashMenu type `0x4A0100`; DestroyTag EDX=`0x30`→`0x79F1A0`; SpawnToward→`0x3B2FB10`. Session `e69670dc`. Expected unclean 3-edge left **0**.

### unclean 0/2 leftovers + clean 4-edge (27) — notes 1634

Stubs `ret 0` for Game_ShowPauseMenu / SitRep_*Movie / UI_Add* / MessageBoxHide|Reset / Set*Context / SetProperty*. MessageBoxSetButton|SetText → `0x3FC060`. Closed all 27 four-edge wrappers with unresolved_indirect_count=0. Notable: Entity_InstantConvert/Revert and Squad_GetProductionQueueSize registered entries are throw-only. Session `e69670dc`.
### remaining 4-edge (35) — notes 1669

Closed last four-edge static_cfg names. Session e69670dc. Expected 4-edge left 0; next 5+ (~219).
### clean 5-edge (25) — notes 1694

Closed uind=0 five-edge wrappers. Session e69670dc. Next: remaining 5-edge with uind>0, then 6+.
### remaining 5-edge (25) — notes 1719

Closed last five-edge names (uind>0). Autosave/Quicksave share gates. Entity/Squad AddAbility/RemoveAbility jmp into 0x2405xxx / 0x23FCxxx. Session e69670dc. Expected 5-edge left 0.
### 6-edge (22) — notes 1741

Closed all six-edge wrappers. Entity_CompleteUpgrade has live path via 0x1EA3620 (unlike Squad twin). UI_Set*Callback share 0x36AC610. Session e69670dc. Expected 6-edge left 0.
### 7-edge (28) — notes 1769

Closed all seven-edge wrappers (Formation* protect/transport, AIPlayer threat/path, CanSee*, control groups, distances). Session e69670dc. Expected 7-edge left 0.

## Cont 8–10-edge (notes 1789→1820)

- Applied pending **9-edge** (13) → notes **1802**.
- Applied **10-edge** (18) → notes **1820**.
- Remaining unclean after 10-edge: count via script below.
- recursive still ~192; unresolved_indirect unchanged class; **0 SAFE**.

## Cont unclean 8–68-edge closed (notes 1789→1888)

- Applied 9e(13)+10e(18)+11e(12)+12e(12)+13–15e(17)+16–20e(14)+21–68e(13).
- Unclean `static_cfg` + `bytes_match` backlog: **0**.
- `fully_reviewed_recursive_contracts` still **192** (notes ≠ recursive complete; indirect/vtable still open).
- `unresolved_indirect_sites` **18193**; live **0**; **0 SAFE**.
- Session `e69670dc`.

## Cont recursive bounds TEB/IAT/int3 (192→295)

- Generator: allow bounded TEB `gs:[0x58]`, IAT/`.rdata` `external_or_noncode_pointer`, MSVC `int3` padding.
- `fully_reviewed_recursive_contracts` **295**; hook neighborhood recursive **70**/397.
- Notes still 1888; unclean static_cfg backlog 0; unresolved_indirect **18193**; live **0**; **0 SAFE**.
- Durable: UPDATE_GUIDE «SCAR recursive closure bounds»; OPEN_ITEMS indirect tail.

## Cont recursive thunk+vtable-install+MAX12 (295→305)

- IDA `e69670dc`: thunk `0x3254350` fallback `0x778B300` → `0x325B810` `__imp_free`.
- Allow vtable-install / `address_taken_not_proven_execution` / fallthrough; `MAX_CLOSURE=12`.
- recursive **305**; hook **74**/397. New: GetBlueprint/GetRace, ClearCombatTrainingCacheEntry, LCWatcher_RemoveFilter, World_GetTerrainCellType.
- Still **0 SAFE**; indirect sites 18193; live 0.

## Cont CRT heap facades (305→332)

- IDA singleton `0x84C9328`/`0x778B300`: `[vt+0]` malloc `0x325B7D0`, `[vt+8]` free `0x325B810`.
- Auto list `scar_crt_heap_facades.json` (775 bodies: only `[rax]`/`[rax+8]` + singleton refs).
- recursive **332**; hook **83**/397. Closed AI_IsEnabled/IsAIPlayer, EGroup/SGroup Add*, World_GetAll*, Misc_GetSelected*.
- Still 0 SAFE; game-vtable StateModel/FOW/fatal paths open.

## Cont MAX_CLOSURE=24 + MSVC EH vector (332→423)

- `MAX_CLOSURE` **12→24** (sim: +87 fully-bounded; plateau by 32).
- IDA `e69670dc`: MSVC `??_L@` `0x4FB05BC`, `??_M@` `0x4FB0464` — `call rdx` is CFG `__guard_dispatch_icall_fptr` → `_guard_dispatch_icall_nop` `0x516B040`, not game vtable.
- recursive **423**; hook **103**/397 (+4/+2 from EH vector on top of MAX24).
- Dump 14484 resolves fatal UI `0x8449D10`→obj `0x84E0F70` vt+0x40/`0x3CEA4E0`, vt+0x50/`0x3CEA5D0`, stack_cb `0x84CC908`→`0x3B72F70` — but bounding fatal alone unlocks **0** complete (always co-blocked). FOW `0x1F06550` as facade would +26/+5 — **not** applied (true `[rdx+8]` game vtable).
- Still **0 SAFE**; notes 1888; unresolved_indirect 18193; live 0.
- Hook incomplete first-sites (post): no_single_native 65; fatal `0x3AE75C0` 14; `0x36246E0` 8; FOW `0x1F06550` 5; `0x22AA8F0` 5; unvisited FOW explore `0x3B597B0` 3.

## Cont MAX48 + MemoryPool Default + end-padding (423→467)

- `MAX_CLOSURE` **24→48**.
- Capstone end-padding: allow `1≤unvisited≤3` when `decoded+unvis==size` (e.g. `0x3D0F780` 1027+3=1030, nind=0).
- IDA/dump: `0x36246E0` sole unknown `[rax+0x10]` = MemoryPoolHeap Default (`0x84CCC08`→LOOP vt `0x660B700`+0x10=`0x3C2EC50`→`HeapAlloc`).
- recursive **467**; hook **108**/397.
- FOW `0x1F06550` still open (true `[rdx+8]`; facade alone would +26 complete — not applied).
- Still **0 SAFE**; live 0; unresolved_indirect 18193.

## Cont switch jumptable `0x1E47470` (prep)

- IDA `e69670dc`: `jmp rax` at `0x1E4749F` is `jpt_7FF7A734749F` (cases 0–6); Capstone unvis 416 = unread arms.
- Added to `KNOWN_INDIRECT_THUNKS` with skip_unvisited (hand-proven IDA body).
- recursive stays **467** (never first-site alone). With StateModel helpers also facaded would be ~523 — **not** applied (`[rdx+0x4E8]`/`[rdx+0x4F0]` still game vtable).

## Cont switch jumptable batch (467→479)

- IDA-proven static jpt (skip Capstone unvis): `0x1EA0590`/`0x1EA04C0` (`jmp r8`), `0x1E46D00` (`jmp rax`), `0x3D30CE0` (`jmp r8`), `0x3B597B0` (`jmp rcx` FOW explore).
- recursive **479**; hook stays **108**/397. New: AISquad_Clear/SetStateModel*Target, Game_SetMapExplored, World_SetSharedLineOfSight*.
- Still open: fatal `0x3AE75C0`, StateModel `[rdx+0x4E8]`/`[rdx+0x4F0]`, FOW `[rdx+8]`. `0x3CDBE20` out-of-image jmp — not facaded.
- Still **0 SAFE**; live 0.

## Cont AISquad/scartype switches + Lua VM peel (479→498)

- Switch jpt batch #2: `0x29BE770`/`0x29BE920`/`0x21D95A0`/`0x19887E0`/`0x1988BE0` → recursive **487**, hook **109**.
- More only_jmp switches: `0x29BAD80`/`0x2940320`/`0x2999340`/`0x19D6*`/`0xC2F4C0`/`0x1A64F60`/`0x204A1E0`/`0x1E46670`/`0x11320D0` + CRT `0x3B347D0` Capstone gap → **492**.
- Lua VM chain (printf→writer→panic→GC→opcode→CFunction→pcall→resume→compare): `0x3D19D60`/`0x3D33330`/`0x3D13D10`/`0x3D308A0`/`0x3D18C60`/`0x3D2C440`/`0x3D14130`/`0x3D143A0`/`0x3D13DD0`/`0x3D2E6E0`/`0x3D30610`/`0x3D15240`/`0x3D2BC90`. `MAX_CLOSURE` **48→96**.
- recursive **498**; hook **111**/397. New closed: `AI_DoString`, `AIProductionScoring_LuaScoringFunction`, `BP_GetType`, `Event_Delay`, …
- EGroup_ForEach*/Enum_*/Event_Start* still hit fatal `0x3AE75C0` / other game vtable after Lua peel.
- Still **0 SAFE**; live 0. Goal 2821 not complete.

## Cont fatal→CRT future peel (498→582)

- IDA `e69670dc`: fatal logger `0x3AE75C0` (fnptr `0x84CC908`→`0x3B72F70`; console `0x8499D10`→obj/`vt` slots +0x40/+0x50). Next hop `0x3C03000` = MSVC `std::future` enqueue installing `_Associated_state<int>` vt `0x6534798` (`+0`/`+0x10`/`+0x28` = `0x2F8A1C0`/`0x2F8A5E0`/`0x2F8A740`).
- CRT cluster facades: drain `0x3C033D0`, set_exception/set_value `0x2F89970`/`0x2F89A60`, release `0x3C02580`, slab `0x3B4C090`, CRTMemoryHooks `0x3CDBE10`/`20`/`30`/`EE0`/`EF0` (init `0x3CDCA40`), Plat WaitHandle `0x3AE82D0`, GroupManager alloc `0xC25550`, SLIST pool `0x3705E30`/`0x3706BC0`/`0x3701850`, dbghelp `0x3B76E10`/`0x3C2FCB0`/`0x3AE7C80`, TLS atexit `0x3AE74F0`, `_alloca_probe` `0x4FB0CF0`.
- Metamethod switch `0x3D186B0` (jpt). TLS allow-list: `gs:[0x58]` + `gs:[0x10]` StackLimit.
- `MAX_CLOSURE` **96→256** (192 gave +73; 256 plateaus on game vt).
- recursive **582**; hook **126**/397. Closed: `EGroup_Create`/`Add`, `SGroup_Create`, `Player_GetAllEntities`, `Entity_IsBuilding`, `BP_GetEntityTypeExtRaceCount`, …
- Remaining first-sites: StateModel `0x1F52540`/`0x1F52600`, FOW `0x1F06550`, spatial `0x1E4ACB0` (`[tls_heap+0x30]`), `0x2AF8160`. `Entity_Create`/`AI_SetPersonality` still incomplete.
- Still **0 SAFE**; live 0. Goal 2821 not complete.

## Cont TLS MemoryPool/heap + Construct peel (582→606)

- IDA `e69670dc`: TLS MemoryPool free via `qword_0x84D6CA0[tls]+0x30` (`0x1E4ACB0`, `0x73EA60`, `0x742C90`/`0x742C20`/`0x742BB0`/`0x742B10`, `0x54EA80`, `0x744270`/`0x7441D0`/`0x745E00`, …). TLS heap `0x84D6C30` bias **0** / **+10** / **+14**: alloc `[vt+0x28]` / free `[vt+0x30]` (`0x1E4B880`, `0x20A18C0`, `0x20D2670`, `0x21494F0`, `0xA522A0`, `0x731CD0`, `0x2004760`, `0x1ACB890`, `0x1D6B5D0`/`0x1D6BFD0`, LocalCommand helpers `0x1AA79F0`/`0x1AA86E0`/`0x1AA5680`/`0x1AA4370`, …).
- Switches: tagged payload `0x22C01A0`/`0x22BFAA0` (jpt); command-type `0x20DFC00` (6 cases, jpt `0x20DFED0`).
- MSVC `std::_Func_impl`: dtor `0x1EC0BE0` (`[vt+0x20]`); invoke/dtor `0x1DE8D90`; move `0x415950` (`+0x8`/`+0x20`).
- MemoryPoolHeap Default via wrapper object `0x84CBBE8`: init `sub_7FF7A8B333B0` stores pool at `+0x70` (= `0x84CCC08`). Free slot `[vt+0x20]`=`0x3C2ED40`→`HeapFree` (`0x3FC060`); grow alloc/free `0x404AA0`.
- `MAX_CLOSURE` **256→384** (Construct hit 256 until raise). recursive **606**; hook **131**/397.
- New closed: `LocalCommand_PlayerSquadConstructBuilding`/`Fence`/`Field`/`SlottedSpline`/`Dependent`/`Replacer`; `Player_GetCurrentPopulationCap`; `Obj_SetTitle`/`Obj_SetDescription` (31 Obj_* total closed).
- Still open game vt: StateModel `0x1F52540`/`0x1F52600`, FOW `0x1F06550`, ability/cmd `0x21DB720` (`[vt+8]`/`[vt+10]`), `0x22AA8F0`. `Entity_Create`/`Obj_Create` incomplete. **0 SAFE**; live 0. Goal 2821 not complete.

## Cont AI scoring / _Func / SGroup peel (606→669)

- IDA `e69670dc`: FOW helper `0x1F06550` = handle-table probe + game `[obj+8]` — **not** facadeable. StateTree `0x22AA8F0` / colour `0xB28120` / winlose `0x69B270` likewise true game.
- LocalCommand Squad TLS twin `0x1AA5A50` (heap+MemoryPool free `+0x30`); SGroup_ForEach helper `0x21E1A80` + `SGroup_GetSpawnedSquadAt` `0x21E1060` (MemoryPool free). After peel, Squad* next-block on ability `0x21DB720`.
- `AIProductionScoring_*` (~55 bodies): CRT heap via `0x84C9328` + replaced scoring-node `(**vt)(this,1)` — batch KNOWN. Hook closed **62** scoring names.
- AIPlayer_Set* / AI_LockSquad / AI_SetAITargetable: outer `_Func` dtor facades `0x2993DA0`/`0x2995BC0`/`0x2995CB0`/`0x2949A60`/`0x293FD50`; shared apply `0x29175D0` (`[vt+0x10]` or list); payload `0x2922980` (`_Func` dtor after apply).
- recursive **669**; hook **194**/397 (+63 from 606). Still **0 SAFE**; live 0. Goal 2821 not complete.
- Remaining hook first-sites: FOW `0x1F06550` (7), StateTree `0x22AA8F0` (5), colour `0xB28120` (3), StateModel, ability `0x21DB720`, health `0x1E067C0` (`[vt+0x110]`+TLS), Event_Save `0x36A8290`.

## Cont LOC / PlaceAndConstruct + ability note (669→675)

- `0x4D61D0`: wchar grow via MemoryPoolHeap wrapper `0x84CBBE8+0x70` (`[vt+0x10]`/`[vt+0x20]`). Closed `Loc_FormatInteger`; `LOC`/`Loc_FormatNumber` next-block on format-arg `[vt+8]` (`0x3633760`) — leave.
- `0x186A900`: planned-construct group tree erase `(**vt)(this,1)` + CRT free. Closed 4× `LocalCommand_PlayerPlaceAndConstruct*Planned`/`SlottedSpline*`.
- Ability apply `0x21DB720`: TLS MemoryPool/heap `[vt+0x28]`/`[vt+0x30]` **and** ability `[vt+8]`/`[vt+0x10]`; also calls FOW `0x1F06550`. Not facadeable as a whole.
- recursive **675**; hook **194**/397. **0 SAFE**; live 0. Goal 2821 open.

## Cont AI _Func xrefs + SGroup TLS peel (675→806)

- IDA xrefs to shared apply `0x29175D0` (`sub_7FF7A7E175D0`): **148** callers; intersect incomplete first-sites → **123** new `KNOWN_INDIRECT_THUNKS` `_Func` wrappers (+ `AI_EnableAll` `0x293FE90`).
- SGroup TLS MemoryPool free `+0x30`: `0x21E0EC0`/`0x21E1210`/`0x21E13C0`/`0x21E17D0`/`0x21E1CF0`/`0x21E1DE0`/`0x21E1F50`/`0x21E2020`/`0x21E2480`; BP `0x2148480`; EntityBuildSquad TLS heap `0x1AA81C0` (then ability `0x21DB720`).
- EGroup_Destroy `0x19621C0` tree erase twin of PlaceAndConstruct erase.
- recursive **806**; hook **214**/397. Closed: `AI_Enable`/`EnableAll`/`Lock*`/`Unlock*`/`UpdateStatics`/`PauseCurrentTasks`/…; `SGroup_GetSquadAt`/`ForEachAllOrAny*`/`Contains*`/`GetPosition`/…; `EGroup_Destroy`; `BP_GetEntityBPDefaultSpeed`.
- Still open game vt: StateModel/FOW/ability/colour/health/winlose. **0 SAFE**; live 0. Goal 2821 open.
- `AI_FindClosestOpenPositionForAbility*`: CRT+_Func facade on `0x2B5D930` peels to ability-cast `0x251D180` — leave.

## Cont stubs + World metadata + TLS homebase (806→818)

- Generator: `allow_missing_boundary` (+ synthetic stub summary) for Capstone-missing leaves. Closed: `AIPlayer_GetClumpPosition` `0x29930E0`; `AI_ConvertToSimSquad`/`Entity`/`Player` `0x294A780`/`0x294A790` (+ sibling) → `0x2B2AA00`/`0x2B5AFC0`.
- `AI_FindClosestOpenPositionForStructure` via switch facade `0x2BD2430`.
- World metadata `0x23DC0B0`: string-table singleton alloc `[vt+0x10]` (rest IAT SRWLock/CRT). Closed 6× `World_GetMetadata*`.
- Switch `0x2B761E0` (FindBestSquadTarget helper, 7 comparators) + logger iostream/`[vt+0x30]`/`0x84D9D10[vt+0x38]` peel LogCombat past several sites → still open on filesystem `0x3B6E050` `[vt+8]` mounts — leave.
- TLS heap bias+14: `AIPlayer_Set/RemoveSquadHomebase` `0x299A4D0`/`0x299A670`.
- Still leave: StateModel/FOW/ability/`0x21DB720`/TFLite `0x2918290`/clumps `0x2BBEBC0`/`0x1DFFB70`/`0x22AA8F0` StateTree; FindBest→`0x2BE86F0` game vt; Camera/UI kicker game.
- recursive **818**; hook **214**/397. **0 SAFE**; live 0. Goal 2821 open.

## Cont construction/cover/Population + TLS peel wave (818→826)

- Construction switch `0x20D4020` (jpt `0x20D47E4` / `jpt_7FF7A75D406E`, 6 cases + TLS MemoryPool free in arms) → closed `Entity_CalcConstructionPlacement`.
- Cover: TLS free `0x23DA4B0` + heap bias+14 grow `0x23DABA0` → closed `Entity_GetCoverValue`. `Entity_Population` closed earlier in same wave.
- Target-list grow `0x742580` (TLS heap bias+14) → closed `AIPlayer_GetStateModelTargetListEntries`.
- `EBP_PopulationCost`: grow `0x5D0CC0` + insert `0x1875B30` + SSO reset `0x5D1540` + helper `0x1F6CF00` → closed.
- LocalCommand family dual TLS (`0x84D6C30`+`0x84D6CA0` `[vt+0x30]`): `0x1A95E60`/`0x1A9AFA0`/… peels to ability leave `0x21DB720` — names stay incomplete.
- Formation_GetDimensionsAndOffset: long TLS chain (`0x1A918C0`→…→`0x2154CF0`→`0x2154BD0`…) still open — continue peel, no game vt proven yet on that path.
- Leave forever still: StateModel/FOW/`0x21DB720`/TFLite/clumps; Marker_Destroy `0x20EC340` polymorphic `(**vt)(this,0)`; job-pool `0x3B41000` (callback `call r14` + `_Func`); StateTree `0x22AA8F0`.
- recursive **826**; hook **214**/397. **0 SAFE**; live 0. Goal 2821 open.

## Cont Formation TLS chain + shared free + Face/Loadout (826→831)

- Finished Formation_GetDimensionsAndOffset TLS chain through `0x2154BD0`/`0x2157D10`/`0x2157F60`/`0x2158390`/`0x4005A0`/`0x2057C70` → **closed**.
- Shared TLS MemoryPool free `0x4005A0` (also used by insert grow). Majority vote helper `0x2057C70` (TLS pool + Capstone mid-gap, `skip_unvisited`).
- Closed also: `AIPlayer_GetStateModelTargetListEntries` (earlier), `EBP_PopulationCost`, `SGroup_CalculateClusterSeparation`, `SBP_GetFirstEBP`, `AITactic_AdjustJumpSlideAbilityTarget`.
- `0x2007660` Entity_ConvertBlueprint: TLS heap **bias+10** (not +14). Peels to `0x1E7BE40`.
- `0x19775E0` CanPlace: TLS pool → `0x20D63F0` poly-dtor + TLS pool `0x84D6C80` — leave poly.
- CombatFitness `0x2998F00` `_Func`+TLS → TFLite leave `0x2918290`.
- Face/Loadout TLS peels advance (`0x199D820`/`0x199DA90`/`0x19979D0`/`0xB823C0`) but names still open on deeper game sites.
- recursive **831**; hook **215**/397. **0 SAFE**; live 0. Goal 2821 open.

## Cont World spatial TLS + Marker + alt pool 0x84D6C80 (831→840)

- World spatial queries: TLS MemoryPool free `0x84D6CA0[tls]+0x30` on `0x195BB00`/`0x19598C0`/`0x1956170`/`0x19594A0`/`0x1959270` (+ NearMarker/TerritorySector peels that stop on spatial poly `0x20E9AF0` / FOW `0x1F06550` / filter `0x1962370`).
- Bulk Capstone sole-unknown TLS MemoryPool batch (~83 helpers) + named: `Squad_SBPEntityAt`, `SquadGroup_CountSpawnedAndStatsInitialized`.
- `Marker_FromName`: TLS heap bias+14 grow `0x20EB980`.
- TerritoryGaps peels through `0x205F920`/`0x205E330` then FOW leave `0x1F06550`.
- `Squad_AddAbility` peels TLS heap/`0x84D6C80` alt pool/`0x8DCED0` → ability-slot poly `0x218A270` — leave.
- Misc_FindDeposits → entity `[vt+0xC8]` `0x1E9D410` — leave.
- First-class alt TLS pool: `0x84D6C80` (same family as CanPlace path; proven on `0x23FBBE0`).
- recursive **840**; hook **217**/397. **0 SAFE**; live 0. Goal 2821 open.

## Cont Player/Squad TLS + availability/_Func (840→847)

- Closed: `Squad_IsSiege`, `Squad_IsUnderAttackFromDirection`, `Squad_GetLastAttackers`, `Squad_AddSlotItemToDropOnDeath`, `Player_ClearAvailabilities`, `Player_SetAllCommandAvailabilityInternal`.
- TLS heap peels: bias 0 (`0x1DD8590`/`0x1DD7CF0`/`0x1E2BF50`/`0x23F41A0`/`0x1DEDF80`/`0x1DD96B0`/`0x1DDCB90`/`0x1DD7EA0`), bias+10 (`0x1FEB620`/`0x2701B60`/`0x2702AF0`), bias+14 (`0x1DFE160`/`0x1ECB610`), MemoryPool `0x199A6F0`/`0x2053E20`.
- `Player_AddAbility` `_Func`+TLS `0x1E27BC0` → deeper `0x1E33B50` leave. `Setup_SetPlayerName` MemoryPoolHeap wrapper `0x84CBBE8+0x70` → `0x1E2F730`. `GiveSlotItem` → poly `[vt+0xE8]` `0x23EECD0` leave. TerritoryConnected → `0x2702C20`.
- Hook neighborhood index now **388** names (was 397). recursive **847**; hook **215**/388. **0 SAFE**; live 0. Goal 2821 open.

## Cont _Func / string-intern / switch peels (847→857)

- Session IDA `e69670dc`. Territory TLS batch (`0x2701C70`+…) peels into FOW forever `0x1F06550` — no net close on TerritoryConnected.
- Capstone sole-TLS batch (~575) — no first-site unlock (blockers already game vt).
- Closed: `World_SetPlayerWin`/`Lose`, `World_GetRand`, `Marker_GetNumberAttribute`/`DoesNumberAttributeExist`/`DoesStringAttributeExist`, `LCWatcher_AddFilter`, `Player_CanSeePosition`, `Modifier_Create`.
- Facades: `_Func` invoke `0x69B270`; `_Func` dtor `0x29933E0`/`0x1AB9FC0`/`0x1AB9BF0`; string-intern MemoryPool alloc `[vt+0x10]` `0x2034F80`/`0x1937940`/`0x1938130`/`0x1937EA0`; switch jpt `0x23A6D20`/`0x22D7E40`/`0x36A6420`/`0x3B535A0`/`0x188BED0`.
- Leave: Camera `0x1AEA670` poly; ability `0x20C21F0`; UI kicker `0xB270C0` (`call [rax]`+MPH); TeamWin `0x6995B0` game-over poly; Modifier Apply → StateModel `0x1F52540`; KillPlayer → `0x1E29510`.
- recursive **857**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont Misc_Screenshot _Func (857→858)

- `Misc_Screenshot` `0xB7FBF0`: sole Capstone unknown = `_Func` dtor `[vt+0x20]` on screenshot callback holder.
- recursive **858**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont Scar_AddInit Lua switch (858→859)

- `Scar_AddInit` helper `0x36A9A20`: Lua TValue type switch `jmp rcx` via `jpt_7FF7A8BA9AA6` (`0x36A9C44`).
- Deposits `0x2087930` / Physics nested `0x3627A40`/`0x362F6D0`/`0xACCF00` peels advance then forever/game (`0x1E9D410` / `0x3884450`).
- String-intern batch (`Entity_SetExtEnabled`/`Squad_SetExtEnabled`/`Modifier_IsEnabled`/`Squad_Kill`) + `Game_SaveTextDataStore` `_Func`/`0x3739D90` JSON escape / `memtofile` printable switch — advance then game vt.
- recursive **859**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont Sound_Stop + Squad_GetAttackTargets (859→861)

- `Sound_Stop` `0x42D01B0`: Wwise opcode switch `jmp rcx` `jpt_7FF7A97D02D4` (`0x42D2590`, 65 cases) — closed.
- `Squad_GetAttackTargets` `0x1E03EE0`: tagged-value switch `jpt_7FF7A7303FCD` (`0x1E0416C`) — closed.
- FOW_Reveal* tagged Position switches (`0x1ABCC40`/`0x1ABCEA0`/`0x1ABD100`/`0x1ABD4A0`) peel then FOW forever `0x1F06550` (EGroup also issue-extractor).
- LocalCommand MovePos twins `0x1AA5E20`/`0x1AA6DF0` TLS+CRT+_Func → ability forever `0x21DB720`.
- recursive **861**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont Marker + missing-boundary batch (861→909)

- `Marker_GetStringAttribute` `0x1937BE0`: string-intern `[vt+0x10]` + TLS pool free `0x84D6CA0[vt+0x30]`.
- LuaConfig `0x36A8290` `_Func` invoke → closes `Game_GetTerrainTypeVariables`; Event_Save → Lua poly `0x20454B0` leave.
- `Marker_GetName`/`GetType` `0x19378C0`/`0x1937900`: TLS SSO getters (IDA data overlay; `allow_missing_boundary`).
- Batch 42 pure missing-boundary leaves: debug/Sim/Weapon/Cursor toggles `0x18A7140+`, World/Game/Player TLS getters, UI flag leaves, `World_EnableReplacement…`.
- Leave: `dr_clear`/`dr_setdisplay` jmp-vt; Entity/Squad remaining missing-boundary look mid-function/wrong entry; MovieCapture → `0x8D4B10` not in native graph.
- recursive **909**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont Squad TLS missing-boundary (909→915)

- Closed: `Squad_EnableSurprise`/`SetMoodMode`/`SetInvulnerableEntityCount`/`GetInvulnerableEntityCount`/`IsHoldingPosition`/`IsInBackground` — pure TLS getters/stores ending in `ret`.
- Leave jmp-helper: `Squad_IsUnderAttack`/`IsAttacking`/`GetMax`/`AdjustAbilityCooldown`/`ClearPostureSuggestion` (targets outside native graph).
- recursive **915**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont CRT leaves + IsPaused/MovieCapture (915→920)

- Closed: `cursor_setposition` `0x3B64F60` (CRT+Default arena); `Game_StoreTableData` `0x1799000` (CRT HeapAlloc); `AI_SetPrefabTarget_Waypoints` `0x2B892C0` (CRT); `Game_IsPaused` `0xB272A0` (global+byte leaf, `allow_missing_boundary`); `MovieCapture_Start` `0xAE23B0` thunk → `0x8D4B10` / `MovieCapture_Stop` capture-flag leaf.
- FOW_UIUnReveal* CRT peel chain (`0x1916780` fptr slot → `0x3F72C84` IAT free → `0x3F8E864` STL release → `0x3FA198D` CFG stub) ends at junk `0x4CBA4D2F` — leave.
- Session reopen `c96d58e7` (same IDB imagebase `0x7FF7A5500000`).
- recursive **920**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont StateTree targeting jumptables (920→924)

- Closed: `Entity_GetStateTreeTargeting_EntityTarget`/`PlayerTarget`/`SquadTarget`/`Vector3f` via `0x22BFCF0` + sister `0x22BFF40` (`jpt_7FF7A77BFDCC` / `jpt_7FF7A77C0079`).
- Leave: StopAbility `0x20CBB00` game vt slots; FOW_UIUnReveal* junk; Entity_*/Squad_*/dr_* missing-boundary.
- recursive **924**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont post-924 triage (no recursive gain; IDA c96d58e7)

- Generator: `issues_are_bounded_int3` now accepts Capstone `undecodable_tail:*` when KNOWN has `jumptable_rva` (EGroup jpt dwords+`cc` at `0x1ABD495` proven). `FOW_RevealEGroup` `0x1ABD100` then closes past issue-extractor → still blocks on FOW forever `0x1F06550` (same as RevealSGroup). recursive stays **924**.
- IDA leave (game vt / poly / forever): CombatFitness/`0x2918290` TfLite+`[vt+0]`; Entity_Enable* `0x1E73D70` obfuscated TLS; clumps `0x2BBEBC0`; deposits `0x2ABB930` container `[vt+0x10]`; SetMarkerPath `[vt+0x28]` on marker obj; Sound music helpers job-queue `call [rax]`; StateTree_Queue* dtor `[vt+0]` + alt pool `0x84D6C80[tls]+0x30`; UI_IsLayerContentLoaded helper `0xC5DA20` `[vt+0x18]`.
- Incomplete shape after rebuild: ~1015 no_native/multi; ~856 game/vtable; 16 missing-boundary; 7 unvisited (LogCombat/Precache/StopAbility/Challenge); 2 FOW junk graph; 1 was issue-extractor (now FOW forever). CRT/_Func/switch leaf hits in incomplete limits: **0**.
- Multi-target UI/Pause/SitRep (19): dual regs stub `0xAC2xxx` nullsub + real `0x113xxxx` job-queue — active VM binding not proven; leave.
- Goal 2821 open. Session `c96d58e7`, imagebase `0x7FF7A5500000`.

## Cont Entity data-overlay leaves (924→927)

- IDA overlay as `dq` on registration RVAs; Capstone graph `missing_function_boundary`. Proven pure leaves via `get_bytes` (no call/jmp-indirect):
  - `Entity_IsCasualty` `0x19DA450` — `[rcx+0xD8]>>6 & 1`
  - `Entity_IsPartOfSquad` `0x19D82A0` — `[rcx+0xB4]==-1` else TLS `gs:[0x58]` blob+id `setnz`
  - `Entity_GetSquad` `0x19D82E0` — null/-1→0 else TLS blob+id pointer
- Leave: `Entity_IsMoving` `jmp [vt+0x108]`; `Squad_GetMax` tail `jmp`; `dr_*` `jmp [vt+…]`; remaining overlay mid-entry/obfuscated.
- recursive **927**; hook **388** (hook neighborhood +3). **0 SAFE**; live 0. Goal 2821 open.

## Cont Entity_CycleDebug overlay leaf (927→928)

- `Entity_CycleDebug` `0x19D4DA0`: scan static id table + write two globals; no call/jmp-indirect (`allow_missing_boundary`).
- `Entity_TagDebug`/`Entity_BuildCycleList` jmp `0x20345D0` absent from native graph — leave.
- recursive **928**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont Squad overlay thunks (928→931)

- `Squad_IsUnderAttack` `0x199A690` → direct jmp `0x22401E0` (static_cfg leaf). Fail path `xor al; ret`.
- `Squad_IsAttacking` `0x199AA10` → direct jmp `0x2240260` (twin leaf).
- `Squad_GetMax` `0x19981A0` → all paths direct jmp `0x212D4C0` (closure 169, already bounded).
- Dual-reg UI/Pause: two registrar callbacks (`0xAC2680` nullsubs vs `0x11322C0` real), same insert `0x369AF80`; which VM table is passed is not proven statically — leave.
- recursive **931**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont ExtensionCount + AdjustCooldown (931→933)

- `Entity_ExtensionCount` `0x19DAE80`: cookie + TLS `gs:[0x58]`, `movzx` byte `[blob+idx+0x6C]`, `ret`. No call/jmp.
- `Squad_AdjustAbilityCooldown` `0x19A0160`: null/-1/flag `ret`; else direct jmp `0x20C1010` (closure 11).
- Leave: IsMoving `[vt+0x108]`; SetShowSilhouette `[vt+8]/[vt+0x10]`; TagDebug/BuildCycleList → `0x20345D0` not in graph; ClearPosture → `0x1E0C4A0` `[vt+0x218]`; `dr_*` jmp-vt.
- recursive **933**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont job-queue singleton (no recursive gain)

- `Game_EnableInput` `0xC000C0` and the same family call `0x3642640`, which returns TLS-init singleton `qword_7FF7ADBA7BF0` (RVA `0x86A7BF0`). Fast path is `[obj+0x20]==1` then alloc `0x36427A0`. Else calls `[vt+0]` on `[obj+0x10]`.
- Byte `+0x20` (`0x86A7C10`) has 12 data xrefs besides the ctor write of 1, so the else branch is live. `[obj+0x10]` in this image is a heap pointer, not a static vtable. Leave.
- `dr_*` global `qword_7FF7AD948AA0` (RVA `0x8448AA0`) is 0 in this IDB, so `jmp [vt+…]` has no dump snapshot. Leave.
- Pure CRT scan: 421 bodies already in `scar_crt_heap_facades.json`; 0 new incomplete blockers. TLS-pool-only blockers on the incomplete frontier: 0.
- recursive stays **933**; hook **225 / 388**. Goal 2821 open.

## Cont cursor hide/show singleton vtable (933→937)

- Getter `0x3B65290` returns singleton `off_7FF7ADBAD470`; first qword is vtable `off_7FF7ABAED5D8` (IDA c96d58e7).
- Hide `UI_CursorHide` `0xB36BC0` / `cursor_hide` `0xAE20E0` → slot `+0x18` = `0x3B664E0` (`lock xadd [+0xE88]`) → `vt+0x10` = `0x3B66520` (IAT leaf).
- Show `UI_CursorShow` `0xB36BA0` / `cursor_show` `0xAE20C0` → slot `+0x28` = `0x3B66500` → `vt+0x20` = `0x3B66560`.
- `closure_nodes` now follows `force_callees` on ordinary KNOWN bodies, not only `allow_missing_boundary`.
- recursive **937**; hook **388**. **0 SAFE**; live 0. Goal 2821 open.

## Cont next singleton scan (no recursive gain)

- Small incomplete roots that load a rip global (13): `0x7B41E28` / `0x7B41E98` / `0x7B41EA8` / `0x7B41F40` / `0x84C7E18` are heap pointers in this IDB; `dr_setautoclear` global `0x8448AA0` is null. Their `[vt+disp]` targets are not in the image.
- Other 6-instruction jmp-slot thunks (`0x3B6F730`, `0x4E975C0`, `0x4F00820`) are not SCAR roots and do not block any incomplete name.
- No other incomplete root calls the cursor singleton getter `0x3B65290`.
- recursive stays **937**. Goal 2821 open.

## Cont CRT-plus-one and .data getters (no recursive gain)

- Nine TLS `lea rax` getters used by incomplete names do not return an in-image vtable object. `0x3642640` is the job-queue singleton already left live. `0x8592280` and siblings are 0 or non-pointers.
- Ten blockers are CRT facade plus one other call. `Event_*` `call r8` is `[vt+0]` of a temporary from `0x2260300`, not a fixed slot. `UI_OverrideUIProperty` second call is `[0x84CBBE8]` (heap `0x22122C80A70`) `[obj+0x70]` `[vt+0x20]`.
- recursive stays **937**. Goal 2821 open.

## Cont hook frontier (still 937)

- Hook neighborhood **225 / 388** closed. Remainder: vtable **95**, no native **60**, missing graph **2** (`FOW_UIUnReveal*`), multi **2** (`UI_Remove`, `UI_SetPlayerDataContext`), boundary **2** (`dr_clear`, `dr_setdisplay`), broken labels **2**.
- `lea` targets in small incomplete Entity/UI bodies are the TLS blob table `0x8448A20`, strings (`0x63FF3C0`, `0x62B0000`), or a 2-pointer result vtable `0x62AEE48` (`0xB25810`/`0xB25820`) installed on the failure return. None is the object of the unresolved `call [rax+disp]`.
- recursive stays **937**. Goal 2821 open.

## Cont Entity_GetHealth slot +0x110

- 223 конструктора делают `lea rax, [rip]; mov [rcx], rax`. Qword по `+0x110` у этих таблиц не общий.
- `0x7FF7AB789948` слот `+0x110` = `0x97C8E0`: `mov rcx, [rcx+0xF0]; jmp [rax+0x90]`, сразу за слотом строка. Другие слоты попали в deleting destructor (размер `0x608`) или в RTTI, таблица короче `0x118`.
- `Entity_GetHealth` берёт vtable из экземпляра в `rcx`. Одна статическая таблица эту цель не задаёт.
- recursive stays **937**. Goal 2821 open.

## Cont slot +0x110 is not the health getter

- Таблица `0x7FF7AB784C88` держит настоящий код по `+0x108/+0x110/+0x118`. Слот `+0x110` = `0x2E2E630` (`mov al, 1; ret`), одна ссылка в образе. Это не компонент здоровья: `Entity_GetHealth` читает float по возвращённому указателю `+0x7C`.
- Конструкторные таблицы `0x62AEF40` / `0x62B0730` кончаются раньше `+0x110`. Слот 0 у `0x62AEF40` — `mov eax, 0x130000; ret` (тег типа).
- recursive stays **937**. Goal 2821 open.


## Cont Hex-Rays hook bodies (still 937)

- Session c96d58e7. `Entity_IsMoving` размечена `0x7FF7A6ED96E0`..`0x7FF7A6ED9722`. Null, `entity+0x1D4 == -1` или нулевой TLS-blob дают 0. Иначе `qword_7FF7AD948A20[tls]` + id и `jmp [vt+0x108]`. Слот не статический.
- `dr_clear` `0x7FF7A8C6AE50` и `dr_setdisplay` `0x7FF7A8C6AE90` размечены. Оба читают `qword_7FF7AD948AA0` (RVA `0x8448AA0`, в IDB 0). Ненулевой путь: `[vt+0x88]` и `[vt+0x38]`. Нулевой путь: `ret` без записи rax.
- `UI_Remove`: `0xAC25A0` = `nullsub_85`. `0x1130EE0` строит объект 64 байта (UTF-16 имя, vtable `off_7FF7AB847718`, слот 0 dtor RVA `0x156F6E0`) и ставит job `0x3642640`, magic `0x611A6AB5`, callback `0x1135880`. Иначе `call [vt+0]` на `[singleton+0x10]`.
- `UI_SetPlayerDataContext`: `0xAC2620` = `nullsub_93`. `0x1131DF0` объект 72 байта, vtable `off_7FF7AB7D9118`, слот 0 dtor RVA `0xE8CBC0`, тот же job, magic `0x98A3A255`, callback `0x1135B30`.
- Активная регистрация VM не выбрана. `Entity_GetHealth` слот `+0x110` по-прежнему с экземпляра. recursive **937**. Goal 2821 open.

## Cont AI* coverage check (not 100%)

- Имена с префиксом `AI`: каталог **403** = контракты **403**, флаги recursive совпадают. Закрыто **327**, открыто **76**.
- `AIProductionScoring_*` 62/62. Enable/lock path (`AI_Enable`, `AI_IsEnabled`, `AI_LockSquad`, `AI_UnlockSquad`, `AI_LockEntity`, `AI_UnlockEntity`, `AI_UnlockAll`) recursive.
- 19 без native. Крупные слоты: fitness `0x2918290` (9), clumps `0x2BBEBC0` (6), obstruction `0x1E42A50` (3), place `0x3B41000` (3). `AI_SetPersonality` остаётся на `0x2AF8160`.


## Cont job-post else stays open (still 937)

- `UI_AddCommandBinding` RVA `0x1131680`. Корень зовёт `[off_7FF7AB8241C8+0x20]` = `0x14809CC` (`sub rcx, 0x28; jmp 0x147FFE0`). `0x147FFE0` возвращает `rcx`. Это adjustor primary this.
- Пост в job идёт через `0x1133AF0`: magic `0xa1f70212`, callback `0x11359E0`, иначе `call [vt+0]` на `[singleton+0x10]`.
- `Game_QuitApp` `0xC00150`: magic `0xC3FDFE18`, callback `0xC0F900`. `HintPoint_RemoveAll` `0xB28C80`: magic `0xA2314E61`, callback `0xB76680`. Тот же else.
- Singleton `qword` RVA `0x86A7BF0` = 0 в IDB. Флаг `0x86A7C10` = 1. Значение флага в снимке не отменяет else: у байта есть другие писатели. recursive **937**. Goal 2821 open.


## Cont job-else dead + pool malloc/free (937→1041)

- Getter `0x3642640` возвращает адрес `qword_7FF7ADBA7BF0`. Init `0x3642450` пишет `1` в байт RVA `0x86A7C10` до возврата. Единственный другой store этого байта тоже `1` (`0x5B8C334`). Остальные 10 xref — `cmp byte, 0`. Ветка `je` после `cmp [rax+0x20], 0` у вызывающих getter мертва. Общие хвосты с живой веткой в мёртвые сайты не входят.
- `0x3B0D090` — рост пула. Все три code caller (`0x350CDC0`, `0x3618AB0`, `0x38C7120`) ставят `malloc` в `+0x20`/`+0x30` и `free` в `+0x28`/`+0x38` до вызова.
- `0x3B0CE30` — разбор того же пула: `call [+0x28]` и `call [+0x38]` это `free`.
- recursive **1041** (было 937). Hook closed **233 / 388**. `Game_SetPlayerColour` остаётся на `0x613480`. `UI_AddCommandBinding` остаётся на adjustor/`0x1131680`. 0 SAFE. Live 0. Goal 2821 open.

## Cont UI kicker 0xB270C0 (1041→1047)

- Шесть `UI_Create*KickerMessage` сидят на `0xB270C0`. Между `call 0x3642640` и `cmp [rax+0x20], 0` rax не переписывается; `je` ведёт в `call [rax]` — мёртвая ветка.
- Второй indirect: `mov rax, [rip]` → `0x84CBBE8`, `[rax+0x70]`, `call [vt+0x20]`, `r8d=0xE`. Тот же MemoryPoolHeap free, что у EventCue.
- Прямые callees уже bounded. Замыкание 40 узлов. recursive **1047**. Hook **234 / 388**. 0 SAFE. Goal 2821 open.

## Cont gap job-else + generic MPH free (1047→1064)

- Поиск `cmp [rax+0x20], 0; je` после `call 0x3642640` пропускает инструкции, которые не пишут `rax`. Иначе `je` не находился, если между вызовом и сравнением был `mov rcx, rax` / `lea`.
- `call/jmp [rax+0x20]` признаётся MemoryPoolHeap free, только если перед ним `mov rax,[rip]` попадает в `0x84CBBE8`, затем `mov rcx,[rax+0x70]` и `mov rax,[rcx]`.
- `World_SetTeamWin` и `UI_OverrideUIProperty` от этого не закрываются: у них остаются другие live `call [rax+disp]`. `Game_SetPlayerColour` остаётся на `0x613480`.
- recursive **1064**. Hook **236 / 388**. Среди новых: `UIWarning_Show`, `WinWarning_ShowLoseWarning`, `UI_SystemMessageHide`, `UI_SystemMessageShow`. 0 SAFE. Goal 2821 open.


## Cont CRT heap facade sites (1064→1067)

- `call/jmp [rax]` или `[rax+8]` после `mov rcx,[0x84C9328]; lea rax,[0x778B300|0x77CB300]; test rcx,rcx; cmove rcx,rax; mov rax,[rcx]` — тот же CRT alloc/free, что в `CRT_HEAP_FACADES`.
- Проверено на `UI_NewHUDFeature` `0xB36031`: rip даёт `0x84C9328` и fallback `0x778B300`, `edx=0x38`.
- Закрылись `Subtitle_PlayCharacterSpeech`, `Subtitle_PlaySpeechForSquadFromLocString`, `UI_NewHUDFeature`. Hook остаётся **236 / 388**. recursive **1067**. 0 SAFE. Goal 2821 open.


## Cont Event_* dtor is bounded, logger is not (still 1067)

- `Event_GroupCount` `0xC21460` (и близкие `0xC239C0`, `0xC1DF90`, `0xC1D8D0`, `0xC194C0`, `0xC1B0D0`): CRT alloc уже узнаётся facade-ом. Оставшийся `call r8` — deleting dtor слота 0 локальной vtable. Для GroupCount это `off_7FF7AB7B6EF8` → `0xC21420` (`base 0xC18D80`, затем `operator delete` 152). Оба dtor без indirect.
- Замыкание всё равно стопорится на `0x225CED0`: если `[obj+0x88]` ненулевой, `vsnprintf` и `call [std::function+0x10]`. Цель invoke не одна функция. Имена не закрыты.
- recursive **1067**. Hook **236 / 388**. Goal 2821 open.


## Cont resource flush is not the stack vtable (still 1067)

- `0x1E31D50` / `0x1E31F10` зовут `[this+0]`, `[this+8]`, `[this+0x18]`. Единственный code xref `0x1E31D50` — `0x1E21450`, аргумент это узел listener-списка, не стековый объект с `off_7FF7AB924C40`.
- Слот 0 таблицы `off_7FF7AB924C50` (`0x7318AB0`) к этим вызовам не привязан. `Player_AddUnspentCommandPoints` / `Player_ResetResource` / `Player_SetResourceInternal` остаются открыты.
- recursive **1067**. Hook **236 / 388**. Goal 2821 open.
