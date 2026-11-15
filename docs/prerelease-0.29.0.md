# Prerelease notes: alula 0.29.0 (Алула 0.29)

Кандидат: `b7c231e` (33334b2 + acceptance-fix; ядро A–E опубликовано как 3a788a9). Статус: принят независимой приёмкой готовности (2026-11-16, сессия методики); выпуск — по явному слову владельца (push 33334b2 и b7c231e, тег v0.29.0 на b7c231e).

## Включено

- Язык **0.29** (AL-153…AL-157): таблицы и деревья 0.29; шов 2.25 читается; файлы 0.28 и старше отвергаются с подсказкой `tools/migrate-alula-229.py`.
- Runtime typed value codec: typed encode/decode, canonical bytes, digest — по контракту `spec/alula-value-codec.md`, векторы контракта литералами (`src/machine_typed`).
- Manifest и идентичности: публичный manifest машины, `contract_id`/`artifact_id`, `alula compile --manifest` (`src/machine_manifest`).
- Профили сторон на границе машины: матрица kind→profile→bindings, проверка в `alula check` (`src/machine_profiles`).
- Executor lifecycle/recovery: dedup admission по (producer, event_id) с fingerprint-конфликтом; `withdraw` (закрытие ожидания без отмены исполнения); pinned restore с отказом на чужих пинах (`src/engine`, AC-D1/D4/D5).
- Локальный контракт хоста: `contract.get`, instance open/submit/status/describe с различением schema-error vs receipt (`src/host_contract`).
- Outbox-хост эффектов: интенты с устойчивой идентичностью, trusted context вне payload, права на submit/replay, unknown ≠ успех (`src/host/outbox.nv`).
- Библиотеки 0.29: «Пауза» 413396f18517/31b869a4f7cc, «арифметика_цикла» 8dd3bc954085/3b3321c87caa.
- Примеры и образцы спецификации — 0.29 (перенесены `tools/migrate-alula-229.py`); примеров 107 (68 + 39 chat).

## НЕ включено (не заявлять)

- Production-аутентификация; durable store; сетевые binding (JSON-RPC/HTTP/WS/stdio — transport-адаптеры вне scope без отдельного решения).
- Exactly-once внешних эффектов НЕ обещается: unknown-исход держится честно (outbox), повторяемость — требование к хозяину.
- Миграция машин методики (G эпика) — отдельное поручение методики, в alpha/0.29.0 не заявлена.
- Conformance внешних transport-адаптеров.

## Известные ограничения

- Эффекты инстансов — in-memory (пакетные хэндлеры памяти); реальный durable backend не выбран.
- `nova test src --strict-effects` красен в одном известном месте: `src/examples/data.nv:153` (embed_str требует Fs — вопрос Оракулу; обхода в коде нет намеренно).
- Oracle 0.1.4 медленнее 0.1.0 на крупных юнитах: `machine_run/accepts` и `machine_text_unicode` могут требовать таймаут >1200 с при параллельном прогоне под нагрузкой (наблюдено: 3721 s / 3757 s при jobs=4; отдельные прогоны тех же юнитов зелёные за 86 с / 68 с) — при таймауте прогоняйте юнит отдельно.
- Дефекты компилятора 0.1.4 задокументированы в survey (spikes/env/README.md): item 128 (фиксированный массив в параметр-срез — красный и на 0.1.4), item 129 переоткрыт (в слитом CU аргументы-конструкторы прямого вызова метода чужого модуля эмитятся как void*; резолвер методов равной арности выбирает чужой метод) — обходы в коде помечены.

## Команды проверок

```
nova test src --jobs 4 --timeout 3600     # PASS 24 / FAIL 0 / SKIP 1 (медленные юниты: при TIMEOUT в параллельном прогоне — отдельный прогон юнита с большим таймаутом, зелёный)
./target/alula.exe test examples           # 107 of 107
python -m unittest discover -s tools       # 65 OK
python tools/check-interaction-profiles.py # 37/37
sh scripts/guards/run-all.sh               # ок 4, FAIL 0
```

## Гейты выпуска (план эпика, гейт 0.29.0)

Проверены независимой приёмкой 2026-11-16: AC-E1–E4 (цепочка машина→компиляция→manifest→codec→submit→receipt; окна человека; snapshot/restore + dedup после restore + чужие пины; миграция и версия сборки), prerelease notes сверены с реальностью, саботаж-проба на manifest-валидации поймана тестом, сборка воспроизводима из чистого дерева (37.7 s). Production auth / durable store / сетевой binding вне scope — выпуск не называет себя production-ready.
