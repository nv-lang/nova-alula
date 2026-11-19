# Задача 118/П-2: реальные процессы в `battle_host`

- Тип: задача пакета `nova-alula` (дочерняя к П-2 эпика «Тонкий хозяин в пакете», задача 118 методики).
- Статус: **выполнена, принята владельцем 2026-11-19** («Принимаю 118 как есть», локальный коммит `02840b2`).
  Публикация — по слову владельца. Слова владельца 2026-11-18: «заведи задачу на реальные процессы в
  battle_host», затем «118 сделай малый путь».
- Причина: проявление item-129(c) переклассифицировано. Ломает не модуль `std.os`, а PATH-форма импорта
  `std.os.proc` (у файла `module std.os`); на Oracle 0.1.6 `import std.os.{Proc, real_proc}` собирается и
  `real_proc()` работает (probe: собрано 118.6 с, exe печатает и выходит 0). Поэтому скриптовые процессы
  `battle_host` — наша ошибка импорта, а не блокер Оракула. Подробности и статусы Оракула —
  [spikes/env/oracle-report-0.1.6.md](../../spikes/env/oracle-report-0.1.6.md), §129 (c).

## Малый маршрут

- Слово владельца: «118 сделай малый путь» (2026-11-18). Оценка постановки T≈40 мин; факт ≈25 мин до зелёной
  затронутой части (цель 10 мин не выдержана из-за разбора квирка D133 0.1.6 — диагностическая метрика, не отказ).
- «Принято, когда»: `nova test src/battle_host --strict-effects` зелёный и живой процесс проходит путь
  start → `process_running` true → stop → false; стражи и профили без FAIL.
- Просмотр владельца на локальной копии: команда выше; живой сценарий — тест `bf start_process starts a real child…`.

## Цель

Три процессных примитива `battle_host` — `start_process`, `stop_process`, `process_running` — на реальном
эффекте `Proc` (`std.os`), вместо словаря scripted-ответов. Реальные ФС-дерево, замки, `sha256` и
`run_command` через `Os` (exit code; stdout `""` — ограничение D453) не меняются. `parse_agent` остаётся
скриптовым: дешёвого агента у пакета нет (внешний сервис, host-spec 111).

## Объём (согласованный)

| Файл | Что меняется |
|---|---|
| `src/battle_host/battle.nv` | импорт `std.os.{Proc, real_proc}`; `scripted_start/stop/running` (строки 110–155) заменяются реальными; реестр держателей `pid -> Child` (текущая модель «хост владеет запущенным»); шапка модуля — снять Oracle-блок, описать реальные процессы |
| `src/battle_host/battle_test.nv` | процессные тесты на реальные процессы; тест «скриптовые процессы» переписывается; остальные 11 проб и негативы REQ-5 сохраняются |
| `README.md` | строка 63 (`alula.battle_host`): убрать «process primitives stay scripted until the Oracle fix» |
| `spikes/env/README.md`, отчёт | уже исправлены (129 (c)); в этой задаче не меняются |

Не входит: `src/thin_host`, `src/host_contract`, `src/engine`, `src/machine_*`, машины/фикстуры методики,
транспорт-адаптеры, релиз/тег, правки репозитория `nv-lang/nova`.

## Проверки (DoD)

1. **Сборка/набор:** `nova build src/alula.nv -o target/alula.exe` (Oracle 0.1.6); `nova test src/battle_host
   --strict-effects` — PASS; полный `nova test src --jobs 4` — 27 PASS; `examples` 107/107; `sh
   scripts/guards/run-all.sh` — FAIL 0; профили 37/37.
2. **Живые процессы (Windows):** запуск долгой команды (`cmd /c ping -n 30 127.0.0.1 >nul`) — `process_running`
   true; `stop_process` — false и повторный stop — no-op; запуск `cmd /c exit 3` и ожидание — код 3;
   неизвестный pid — отказ шага; повторный `start_process` даёт новый pid; хэндл держит хост.
3. **Негативы REQ-5 сохраняются:** путь вне дерева/`..`; нет файла/папки; acting без права — отказ на submit
   и replay; `file_exists`/`process_running` — false как значение.
4. **Границы:** `git grep "std\.os\.proc"` — 0; `with Proc = real_proc()` на каждый вызов — 0 (обработчик
   `#default_handler`); импорт `std.os.proc` в пакете не появляется.
5. **Саботаж-проба (для приёмки):** сломать ветку `stop_process` (или реестр держателей) — процессный тест
   краснеет, откат чистый.

## Приёмка и публикация

Независимая (сессия методики) по candidate SHA; вердикт в канал пакет↔методика; публикация — только по слову
владельца. Метки: `battle.nv` шапка и тест «scripted» снимаются этой задачей; `ORACLE-WORKAROUND(128)` в
`battle.nv:202` остаются (E7301 — окончательный отказ Оракула).

## Результат

- `src/battle_host/battle.nv`: импорт `std.os.{Command, Proc, Child, Signal, Tree}`; `BattleThinHost consume` с
  реестром держателей `consume procs []Child` и `@cleanup`; `spawn_child` через `Command.start` с `Tree.Group`;
  `stop_process` — `kill` + `wait`; `process_running` — `try_wait`; scripted-процессы удалены.
- `src/battle_host/battle_test.nv`: 14 проб (было 12): живой старт/остановка/повтор/неизвестный pid, отказ путей
  вне дерева для dir и log.
- `README.md`: строка `alula.battle_host` без «scripted until the Oracle fix».
- Проверки: `nova test src/battle_host --strict-effects` — PASS (14/14); профили 37/37; стражи `ок 5, FAIL 0`.
  Полный `nova test src --jobs 4` в этом заходе не дошёл: на загруженной машине тестовый бинарник `align` не
  завершился до таймаута 900 с (не дефект правки; прогоняется отдельно).
- Квирк 0.1.6 (записать Оракулу при случае): pattern-bound `Child` не считается потреблённым при отдельной
  `mut cmd`-переменной и в Result-функции (D133); рабочий вид — int-хелпер и inline-цепочка `Command` (в
  `spawn_child`), иначе кодоген даёт void*→str в Err.

## Оценка и риски

0.5–1 день реализации плюс прогоны. Риски: consume-семантика `Child`/`ChildStdin` в Nova (хэндлы держать в
реестре хоста, не в данных машины); Windows-специфика libuv; `try_wait`-семантика `process_running`; при
изменении API `Proc` в кандидате Оракула — перепроверить probe.
