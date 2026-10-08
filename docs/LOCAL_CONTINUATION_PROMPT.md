# Промт для продолжения на локальной машине (Windows + игра)

Скопируй блок ниже в новую сессию Claude Code, открытую в локальном клоне
AOE4HOOK: `git pull` на `main`, не старее `e37db9f21e`.

---

```text
Продолжаем рефакторинг AOE4HOOK на локальной машине: Windows, VS 2022, установленная AoE4, IDA и Documents\AOE4HSettings.
Облачная часть завершена и лежит в main. Твоя задача — проверить её там, где облако не могло: сборка MSBuild и поведение в игре. Затем закрыть открытые вопросы по нативам.

Сначала прочитай, ничего не меняя:
- docs/REFACTOR_PLAN.md: этапы и статусы.
- docs/findings/2026-09-27-cloud-refactor.md: исправленные баги, что не менялось, LOCAL-ONLY чек-лист.
- docs/SCRIPT_BRIDGE_CONTRACT.md: протокол C++ ↔ SCAR (gen/dirty/ack, 73 ключа spec, строки Lua → C++, пути ordinary/lean/quiet/pump).
- docs/LUA_RUNTIME.md: игровая VM — Lua 5.3.

Правила:
- Коммиты без Co-Authored-By. Сообщения коммитов и комментарии в коде на английском, в стиле репозитория. Пушить в main.
- Переводы: ui_i18n.cpp правится руками, в отсортированную позицию kPairs, ключ зеркалится в gen_ui_i18n.py. gen_ui_i18n.py НЕ запускать.
- Тесты кладутся в tests/adversarial и регистрируются в run_host.ps1.
- Находки идут в docs/findings/2026-09-2X-*.md плюс строка в docs/findings/README.md.
- Баги исправляются отдельными коммитами, у каждого регрессионный тест, падающий на старом коде. Рефакторинг только с доказанной эквивалентностью.
- Не менять баланс скоринга, веса, пороги и clamp без доказательства.
- Что проверено в игре, а что нет, пиши прямо. Host-тесты не доказывают поведение в игре.
- Отчёт мне — по-русски.

Шаг 1. Сборка и host-тесты
1. powershell -File ci\ci.ps1. Это MSBuild Release|x64 для InternalInjector, DllInjector, тестов и хеш. Если ci.ps1 не проходит, собери хотя бы InternalInjector.vcxproj тем же MSBuild.
   В облаке ни разу не собиралось MSVC. Новые и изменённые файлы: ai_commit_state.h, ai_eco_act_spec.h, ai_scoring_script.h, civ_table.h, scar_compile_safe.h, ai_runtime.cpp, ai_session.cpp, prod_macro.cpp, scar.cpp, stk_control_feedback.h. Особое внимание: C2026 (лимит литерала 16380 байт, есть test_raw_literal_limit.py), ODR и inline в заголовках, предупреждения /W4.
2. powershell -File tests\adversarial\run_host.ps1. Ожидаемые падения, известные ещё до облачной работы: test_ai_build_order_store_image.py, test_verify_offsets_live.py, tools/test_unit_intelligence.py, tools/test_ootd_power.py. На этой машине у них есть данные: разберись, почему они падали, и почини.
3. Если GitHub CI (ci.yml, windows-latest) всё ещё падает за 3 секунды без шагов — это настройки аккаунта (раннер или биллинг Actions). Скажи мне, в код не лезь.

Шаг 2. Проверки в игре. Логи: warnings.log и лог оверлея. Каждую фиксируй: действие → ожидание → факт → строки лога.
1. Перезагрузка скоринга. Матч с AI BOT, затем смена сложности во вкладке AI BOT посреди матча.
   Ожидание: после неё проходит коммит (eco_ai_cuts), __EcoAct.installErr == nil, множитель Markets не растёт от коммита к коммиту.
   Проверь по строке [AOE4HOOK] ai scoring layer или скриптом в консоли SCAR. В игре нет библиотеки debug, поэтому цепочку обёрток смотри через __EcoActWrapInner и сравнение функций.
2. Поздняя игра. После Age IV + 5 минут, без дерева: военные здания не ставятся (проверка Afford).
3. Фильтр наций. Для Delhi, Ayyubids, Order of the Dragon, Macedonian, Templar и Lancaster:
   - выключил нацию → Hybrid AUTO пишет "civ off", prod_macro стоит;
   - выключил "Other" → эти нации играют.
   Плюс civ_filter в ini (одна нация): Hybrid слушается так же, как C++.
4. Выделение. С включённым AI BOT: строки [AOE4HOOK_CONTROL SEL] и MONKS содержат целые id, без ".0". Удержание выделения работает.
5. MacroBridge. MacroBridge.Run{action="cancel", ...} без force не пишет "refused vs human", а state.last не равен "vs_human".
6. Протокол коммитов. В логе каждое поколение (gen) уходит дважды. При неизменном состоянии новых gen нет, кроме heartbeat раз в 15 с. После выключения и включения AI BOT номера gen не повторяются.
7. Стоимость. Профиль FpsSec (AiCommit, EcoContest) за один матч до и после — сравни с коммитом до облачной работы (efd165d5) и опубликуй числа. Прирост FPS не заявляй без этих замеров.

Шаг 3. Открытые вопросы по нативам (решать только по данным из игры или IDA)
1. World_GetSquadsNearPoint с ownerType = 4. Поиск овец в kEcoOpen (ai_session.cpp) передаёт {3, 4}, а OwnerType бывает только 0..3. Что делает натив с 4: ошибка, пусто, что-то ещё? Если 4 бесполезна или опасна — убрать отдельным коммитом с доказательством.
2. Userdata-enum против числа. Наши скрипты шлют числа (SCMD_Gather → 105, OT_* → 0..3), Relic — userdata (SquadCommandType(105), OwnerType(n); см. sdk/scar/vm_census.json). Проверь в IDA или в игре, что натив принимает число как тот же enum. Если да — задокументируй. Если нет — перейди на userdata с тестом (test_census_enums.py уже запрещает type(ENUM)=='number').
3. hybrid_core.scar при AOE4HOOK_ECO_CPP=true: замерь per-tick стоимость Hybrid AUTO в игре. Есть ли что-то, что C++ уже считает по снимку мира, а Lua пересчитывает сканом сущностей? Переносить в C++ только с замером до и после.

Шаг 4. Итог
- Findings-файл docs/findings/2026-09-2X-local-verification.md со строкой в README. Для каждой проверки: результат, строки лога, что исправлено (коммиты).
- Обнови статусы в docs/REFACTOR_PLAN.md и LOCAL-ONLY чек-лист в docs/findings/2026-09-27-cloud-refactor.md.
- Отчёт мне по-русски: что собрано, что прошло в игре, что упало, что исправлено, что осталось.
```

---

## Для справки: что сделано в облаке

Подробности — в `docs/findings/2026-09-27-cloud-refactor.md`.

- **Исправленные баги:**
  - Markets накапливал множитель;
  - в позднюю игру пропадала проверка «хватает ли ресурсов»;
  - после перезагрузки Relic 66 из 107 хуков оставались хуками Relic;
  - фильтр наций работал неправильно: 10 из 23 в Hybrid, 3 в prod_macro, плюс игнорировался `civFilter`;
  - ложный отказ «vs human» в MacroBridge;
  - на Lua 5.3 id печатались как `123.0`.
- **Рефакторинг с доказанной эквивалентностью:**
  - единый сборщик скриптов скоринга;
  - заголовок `ai_eco_act_spec.h` (spec) и `ai_commit_state.h` (протокол коммитов);
  - обёртка `scar_compile_safe.h`;
  - таблица наций `civ_table.h`.
- **Новые тесты:** контракт C++ ↔ Lua, владельцы хуков, бюджет стоимости Lua, таблица наций, enum'ы из снимка VM, версия схемы моста.
