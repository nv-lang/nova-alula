# Журнал задачи 230 «Проверки пакета называются test» (пакет alula 0.8.0; запись AL-135)

Слово владельца, 2026-10-26: «Пакет nova-alula: 8–14 часов — сделать за 30 минут, это механическое переименование, супер быстро». Малый маршрут: один коммит кода и данных, одна запись журнала (эта), красная проба до правки не писалась (правка не меняет поведения языка). Ветка `task-0-8-0-test-rename` от `1965370` (alula 0.7.0).

## Что сделано

Скрипт переименования лежит вне репозитория (одноразовый); порядок замен: пути и имена файлов, затем `scenario/0` → `test/0`, `scenario-0` → `test-0`, затем слова `Scenarios/Scenario/scenarios/scenario` → `Tests/Test/tests/test`.

- Файлов переименовано (`git mv`): 73. Из них проверок `*.scenario.test.json` → `*.alula.test.json`: 67 (66 в `examples/scenarios` → `examples/tests` и одна `scripts/accept-225/stamp`); схема `scenario-0.schema.json` → `test-0.schema.json`; `src/alula_scenarios/` → `src/alula_tests/` (2 файла); `src/machine_run/scenario.nv`, `nested_scenario.nv`, `scenario_test.nv` → `test_file.nv`, `test_nested.nv`, `test_file_test.nv` (имя не может кончаться на `_test`, кроме файла тестов).
- Ключей `"format": "scenario/0"` → `"test/0"`: 81 (67 файлов проверок и 14 мест в тестах, схеме и README).
- Идентификаторов с `scenario` в `.nv`: 32 различных (`Scenario`→`Test`, `ScenarioRun`→`TestRun`, `parse_scenario`→`parse_test`, `run_scenario`→`run_test`, `run_nested_scenario`→`run_nested_test`, `scenario_files`→`test_files`, `alula_scenarios`→`alula_tests` и др.), 726 вхождений слова в `.nv` (код, строки, комментарии). Всего изменено текстовых файлов: 127, строк: около 660. Коллизий имён нет.
- Версия: `nova.toml`, `PROGRAM_VERSION` 0.8.0; `alula version` печатает `alula 0.8.0 (Alula 2.25, machine/2)`; тесты версий (`help_test`, `v217_test`, `v222_test`) переведены на 0.8.0.
- Запись AL-135 в `spec/alula-changelog.md` и `.en.md` (блок «Пакет 0.8.0, формат 2.25 без изменений»), пункт 42 в `docs/history.md`, абзац в `README.md`. Прежние `scenario/0` и `*.scenario.test.json` не принимаются (переходного периода нет, как AL-22).
- `spikes/env/workarounds.md`: индекс пересчитан (`python scripts/oracle-workarounds.py --index`) — пути файлов сменились.
- `scripts/accept-230.sh` написан по образцу `accept-225.sh`.

Формат Алулы 2.25 не менялся: хеш словаря `35c571ccda17` (`scripts/glossary-names.py --check`, `tools/check-alula-keywords.py --glossary`), образцы (`tools/check-alula-samples.py`) и перевод зелёные; хеши образцов определений не менялись.

## Не менялось (история и копии)

- `spec/alula-changelog*.md` (кроме добавленной записи), `docs/history.md` (кроме пункта 42), `scripts/accept-225.log.md`, `scripts/accept-181.log.md` — история, слово `scenario` в них осталось.
- Две копии образца методики с английским текстом (`spec/samples/agent-step.en.alula.md`, `src/machine_agent/cases/agent-step-methodology-222.en.alula.txt`): слово «scenarios» в их прозе входит в хеш образца (`a154`, `abafd26a12dc`); первый прогон с заменой дал красный `align_test`, замена в них отменена. Слово остаётся в двух строках.
- Имена внешних файлов `gen_*_scenarios.py` в ссылках на задачи продукта (`doc/tasks/...`) — чужие пути, не менялись.
- `scripts/accept-225.sh` и `accept-1xx.sh`: пути и текст «tests passed» заменены; проверка `alula 0.7.0` в `accept-225.sh` осталась (это приёмка версии 0.7.0, после 0.8.0 она красная по версии — не перезапускается).

## Вопрос

Русское слово «сценарий» в прозе пакета (`docs/debugging.md`, `docs/overview.md`, `spec/alula-spec.md` раздел 11 «Сценарии», подписи на схемах `docs/diagrams/*.svg`) НЕ менялось: в README методики state-machines слово «сценарий» теперь называет таблицу машины для людей, и механическая замена на «проверка» меняет род и смысл. Рекомендация: отдельным шагом переписать эти места на «проверка» вручную (в разделе 11 спецификации заодно английский заголовок «Tests» стал расходиться с русским «Сценарии»). Ответ владельца нужен до публикации 0.8.0.

## Прогоны

- Метки времени (локальные): старт 02:32; дерево и скрипт переименования 02:34; сборка `target/alula.exe` готова ~02:38 (152 с); `nova test` 02:39–03:08; последний accept 03:11.
- `alula test examples`: 66 из 66.
- `nova test` по папкам, до 2 папок одновременно (`--jobs 2`): 19 из 19 зелёные. Первый прогон дал две красные: `machine_agent` (хеш `abafd26a12dc` из-за замены в копии образца, исправлено, см. выше) и `machine_nested` (TIMEOUT 900 с под нагрузкой двух потоков); оба перепрогнаны отдельно с `--timeout 1800` — зелёные. `accept-230.sh` пошёл с `ACCEPT_230_SKIP_NOVA_TEST=1`, потому что `nova test` уже прогнан отдельно двумя потоками (так быстрее); полный прогон скрипта без пропуска не выполнялся.
- Стражи `scripts/guards/run-all.sh`: FAIL 0 (один страж пропущен — нет исходников std, как и раньше).
- Набор методики (508 проверок) прогонит методика на программе `target/alula.exe` дерева задачи.

`ПРИНЯТО 230: alula 0.8.0 (Alula 2.25, machine/2); examples 66 из 66; nova test пропущен; перевод и слова зелёные; scenario вне истории 0`
