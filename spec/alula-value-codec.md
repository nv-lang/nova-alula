# Общий контракт типизированных значений и JSON-codec

**Статус: кандидат интеграционного контракта.** Этот документ задаёт общую область
передаваемых типизированных значений Алулы; профиль интеграции может сузить её, но
объявляет такое ограничение явно. Здесь не определяется жизненный цикл события,
идентификаторы envelope, дедупликация, receipts или хранение.

## Область и два уровня

Общий домен — передаваемые значения языка: `null`, `bool`, `i64`, `f64`, `str`, `id`,
списки, словари, записи, кортежи, optional, перечисления и формы с полями. Внутренние
объекты runtime, которые не являются передаваемыми значениями (например, функции,
closures и ресурсы хоста), в домен не входят.

Текущий runtime JSON-codec — существующий codec `Value` из `src/machine/value.nv`:
он передаёт конечные числа как JSON-числа, нечисловые `f64` — тегами
`{"$float":"NaN"}`, `{"$float":"Infinity"}` и `{"$float":"-Infinity"}`;
runtime `text` наблюдает знак `-0.0`, но roundtrip `-0.0` через JSON в этой задаче не
проверялся; payload NaN не сохраняется. Код и проверки описывают runtime, но не
доказывают соответствие интеграционному контракту.

Общий типизированный контракт задаёт семантику независимых интеграций и digest.
Профиль выбирает транспортное представление и может ограничить допустимый домен
(например, только конечные `f64`). Такое ограничение не меняет общий домен и не
применяется молча. Определение codec входит в manifest интеграции и, следовательно,
в её `contract_id`; смена codec не может сохранять прежний `contract_id` или pin при
изменившихся данных/digest. Самостоятельная версия codec или wire-профиля не вводится.
`alula_version` относится к языку/формату, `revision` — к машине; `artifact_id` остаётся
идентичностью сборки. Публикация прежних pins не переинтерпретируется.

## Типизированное представление

Проверка типа предшествует канонизации: значение не приводится к ожидаемому типу.
У записи обязательны все поля; отсутствие optional представляется явно. Повторные
JSON-ключи, неизвестные поля/теги, некорректная форма тегированного значения и
значение вне типа отклоняются. Строки не обрезаются и Unicode не нормализуется.

| Тип | Типизированный JSON-codec общего контракта |
|---|---|
| `str`, `bool` | JSON-строка и JSON-булево |
| `i64` | каноническая десятичная JSON-строка знакового 64-битного числа; без `+`, ведущих нулей и `-0` |
| `int>=n` | та же JSON-строка `i64`, проверяется включительная нижняя граница `n` из schema descriptor |
| конечный `f64` | JSON-число, которое при разборе возвращает тот же binary64; сохраняется знак нуля |
| NaN, `+Inf`, `-Inf` | теги `$float` со значениями `NaN`, `Infinity`, `-Infinity`; payload NaN не сохраняется |
| `id` | строка UUID в формате 8-4-4-4-12 строчных шестнадцатеричных знаков |
| запись | объект полей по техническим именам, без runtime-тегов |
| кортеж | JSON-массив фиксированной длины |
| список | JSON-массив в исходном порядке |
| словарь | массив пар `[ключ, значение]`; одинаковые ключи запрещены |
| `full_map` | массив пар, ключ — форма перечисления без полей; каждая форма встречается ровно один раз |
| набор литералов | JSON-строка из объявленного закрытого набора, не произвольный `str` |
| optional | `{"none":true}` либо `{"some":значение}`; вложенность сохраняется |
| перечисление / форма | `{"case":"техническое_имя","fields":{...}}`, включая пустой `fields` |

### Грамматика схемы

Дескриптор схемы — ровно одно из следующих значений:

```text
"null" | "bool" | "i64" | "f64" | "str" | "id"
{"list": D}
{"tuple": [D, D, ...]}         # не менее двух позиций; порядок значим
{"map": [D, D]}               # тип ключа, тип значения
{"optional": D}
{"int_min": "N"}              # N — canonical decimal string в диапазоне i64, включительная нижняя граница
{"literal_set": [S, S, ...]}  # не менее двух различных строк, по Unicode code point
{"full_map": [QualifiedEnumName, D]} # все значения fieldless enum как ключи, тип значения D
{"record": QualifiedName}
{"variant": QualifiedName}
{"named": QualifiedName}      # объявленный alias
```

`D` — рекурсивный дескриптор; object-конструктор содержит ровно один ключ из списка.
`QualifiedName` — один или несколько ASCII-сегментов `[A-Za-z_][A-Za-z0-9_]*`, разделённых
точкой; имя разрешается точным совпадением с объявлением. Имя поля/case — непустая строка
Unicode scalar values без нормализации; повторения имён запрещены. Таблица объявлений
задаётся точно такими формами: alias `{kind:"alias", type:D}`, record
`{kind:"record", fields:{имя:D,...}}`, variant
`{kind:"variant", cases:{имя:{поле:D,...},...}}`; дополнительные/отсутствующие ключи
отклоняются. Variant имеет хотя бы один case; record может быть пустой; tuple содержит не менее
двух типов. `int_min` задаёт включительную нижнюю границу i64; N записывается canonical decimal
string, чтобы сохранить все 64 бита в JSON manifest. Значения literal set — разные строки,
дескриптор перечисляет их по Unicode code point. `full_map` ссылается только на variant без полей;
значение содержит каждый его case ровно один раз. Рекурсивные
ссылки record/variant допустимы; циклы, состоящие только из aliases, запрещены.

Полная таблица объявлений и весь корневой дескриптор разрешаются и проверяются **до чтения
значения**, даже если список/map/full_map пуст или optional равен `none`.
JSON-значение по схеме: list — массив; tuple — массив длины не менее двух и точно по схеме;
map/full_map — массив ровно двухэлементных пар; bounded `int>=n` — canonical string `i64` не меньше
`n`; literal set — одна из перечисленных строк; full_map — все case-key fieldless enum ровно по одному;
optional — ровно `{"none":true}` с JSON boolean true (число `1` не подходит) или
`{"some":value}`; record — object ровно с объявленными полями; variant — object ровно с ключами
`case` и `fields`, где `case` объявлен, а fields точно соответствуют его схеме. Тип не выводится
из формы JSON, coercion и неизвестные ключи запрещены.

Manifest задаёт ограничения строковых наборов, числовых границ и полноту `full_map`;
словарь не становится JSON-object даже при строковых ключах. Типовая принадлежность
каждого узла входит в typed canonical representation для digest: одинаковый JSON-текст
разных типов не означает одинаковый digest.

Это типизированный профиль интеграций, а не описание текущего dynamic `Value` JSON.
Текущий runtime отличается: `i64` кодируется JSON integer, текстовые map keys могут
кодироваться JSON object, tuple/record/variant имеют `$` tags, а `Null` не различает
отсутствующее значение и присутствующий `null`. В частности, общий профиль сохраняет
вложенные optional, которые текущая untyped форма `Value` не представляет однозначно.
Эта разница не скрывается адаптером: интеграция должна зафиксировать это определение
codec в новом `contract_id` до включения. Проверки текущего runtime не доказывают
поддержку общего профиля.

## `f64`

Общий домен `f64` включает конечные binary64, `-0`, `+0`, NaN и обе бесконечности.
Профиль вправе отклонять NaN/бесконечности, но не вправе молча нормализовать `-0`
в `+0`. Требуется точный binary64 roundtrip для конечных чисел, включая subnormal,
минимальное положительное subnormal (`5e-324`), максимальное конечное число и
соседние представимые значения. Недостаточная точность и переполнение/underflow при
переносе через профиль не превращаются в иное значение без явного отказа.

Payload NaN не является частью передаваемой семантики: все NaN эквивалентны для codec
и digest; текущий runtime уже не хранит payload при JSON roundtrip. Знак нуля является
частью значения: `-0` и `+0` различаются в typed canonical digest. Десятичные записи,
которые разбираются в один binary64 одного объявленного типа `f64` (например, `1`,
`1.0`, `1e0`), имеют одно каноническое typed представление и digest.

## Канонические байты и digest

Канонизация применяется после проверки и типизации. Используются UTF-8 без BOM, без
пробелов вне строк; строки не ASCII-экранируются, кроме кавычки, обратной косой и
управляющих U+0000–U+001F (для них строчное `\\u00xx`, кроме коротких escape JSON).
Ключи JSON-object сортируются по Unicode code point; массивы сохраняют порядок.
Unicode-нормализация не выполняется; строки, имена и ключи должны быть последовательностями
Unicode scalar values (одиночный суррогат отклоняется). Короткий набор JSON escape ровно
`\\"`, `\\\\`, `\\b`, `\\f`, `\\n`, `\\r`, `\\t`; остальные U+0000–U+001F кодируются
строчным `\\u00xx`. `/` не экранируется. Целые метаданные вне точного целочисленного
диапазона выбранного JSON-парсера нельзя кодировать как JSON number без потери.

### Typed canonical bytes

Для digest используется отдельное двоичное представление, а не JSON. Все длины и количества
— беззнаковые 64-битные big-endian. `blob` — длина в байтах `u64` и затем ровно столько
байтов; `text` — `blob(UTF-8)` без BOM. Переполнение длины отклоняется. После проверки
схемы каждый узел кодируется так:

| Схема / значение | Байты |
|---|---|
| `null` | `4e` (`N`) |
| `bool` | `42 00` / `42 01` (`B`, false/true) |
| `i64` | `49` (`I`) + 8 байтов two's-complement big-endian |
| bounded `int>=n` | `4a` (`J`) + `blob(canonical JSON descriptor)` + 8 байтов two's-complement big-endian |
| `f64` | `46` (`F`) + `blob(ASCII canonical-f64)` |
| `str` | `53` (`S`) + `text` |
| literal set | `43` (`C`) + `blob(canonical JSON descriptor)` + `text(value)` |
| `id` | `55` (`U`) + 16 байтов UUID в сетевом порядке; дефисы сняты |
| list | `4c` (`L`) + `blob(canonical JSON descriptor типа элемента)` + `u64(count)` + элементы по порядку |
| tuple | `54` (`T`) + `blob(canonical JSON descriptor упорядоченного списка типов)` + `u64(arity≥2)` + элементы по позициям |
| optional none | `4f` (`O`) + `blob(canonical JSON descriptor типа содержимого)` + `00` |
| optional some | `4f` (`O`) + `blob(canonical JSON descriptor типа содержимого)` + `01` + значение |
| map | `4d` (`M`) + `blob(canonical JSON descriptor типа ключа)` + `blob(canonical JSON descriptor типа значения)` + `u64(count)` + для каждой пары `blob(key-bytes)`, `blob(value-bytes)` |
| full_map | `47` (`G`) + `blob(canonical JSON descriptor)` + `u64(count)` + отсортированные `blob(key-bytes)`, `blob(value-bytes)` для всех enum cases |
| record | `52` (`R`) + `text(qualified declared type name)` + `u64(field count)` + поля |
| variant | `56` (`V`) + `text(qualified declared type name)` + `text(case name)` + `u64(field count)` + поля |
| alias | `59` (`Y`) + `text(qualified declared alias name)` + `blob(typed bytes базового значения)` |

Каждое поле record/variant — `text(technical field name)` + typed bytes значения;
поля сортируются по Unicode code point имени. Схема задаёт ожидаемый тип до чтения значения:
массив под list не становится tuple и наоборот; optional разбирается по схеме в `none` либо
`some`, поэтому его маркер не может столкнуться с полем record; variant выбирает объявленный
case. Record обязана содержать ровно все объявленные поля. Descriptor bounds/literal-set/full-map
включают ограничения и имена enum в canonical bytes. Дескриптор типа — компактные UTF-8
JSON bytes по тем же правилам сортировки ключей/escaping, без пробелов; это описание схемы,
не значение и не самостоятельный hash. Он входит в bytes list/tuple/optional/map/full_map даже для
пустого контейнера или `none`, поэтому тип содержимого не теряется при отсутствии узла-значения.
Разные объявления record/variant с одинаковой формой различаются `qualified declared type name`.
Map-пары сортируются по
лексикографическому unsigned-порядку полных canonical key bytes; дублирующиеся typed key
отклоняются. Объявленные псевдонимы, если они допускаются manifest, должны быть раскрыты до
базового типа и сохранить своё qualified имя отдельным `Y` + `text(name)` + `blob(typed bytes)`;
их определение включено в manifest. Неизвестные/необъявленные имена отклоняются.

### Canonical `f64`

ASCII-токен для NaN и бесконечностей — в точности `NaN`, `Infinity`, `-Infinity`; любой NaN
сводится к `NaN`, `-0` и `+0` — к `-0.0` и `0.0`. Конечное ненулевое число записывается
кратчайшей последовательностью десятичных значащих цифр, roundtrip-ящейся в исходный binary64.
Если кратчайших записей несколько, выбирается ближайшая к точному значению; при точном равенстве
выбирается запись с чётной последней значащей цифрой. Убираются ведущие и завершающие нули
значащих цифр. Пусть `e` — десятичный порядок первой значащей цифры: при `-6 <= e < 21`
используется fixed notation, иначе scientific notation. В scientific notation — одна цифра до
точки, точка и хотя бы одна цифра после неё; `e` строчная, положительный порядок имеет `+`,
знак порядка всегда явный, ведущих нулей в порядке нет. Для интегрального fixed значения
суффикс `.0` обязателен. Такое правило фиксирует tie-break и экспоненту независимо от host
форматтера.

Typed digest строится из описанных выше canonical bytes; это представление является
schema-aware: typed bytes включают distinct markers контейнеров и qualified имя объявленного
record/variant-типа, поэтому одинаковые JSON-значения разных типов и разные объявления одной
формы не совпадают. Digest значения не включает manifest, envelope, `contract_id`,
`artifact_id` или адрес артефакта. Он включает типы узлов по правилам выше. Рекомендуемый
алгоритм — SHA-256 с представлением `sha256:` + 64 строчных hex-цифры; хешируется
`ASCII("alula-value-digest") || 00 || typed-canonical-bytes`. Это новое решение этапа 2,
не ранее утверждённое правило: владелец подтвердил алгоритм и framing в чате задачи 017
2026-10-31. Digest строится из
типизированного канонического представления, а не из raw JSON, текстового равенства
или правил равенства host-языка. Словари сравниваются по значениям, не по порядку
вставки; их пары для digest упорядочиваются по canonical bytes ключа, с запретом
дубликатов typed-ключей. Порядок списков и полей tuple значим; поля record упорядочены
по имени.

### Canonical manifest и идентичности

Публичный manifest — объект ровно с ключами `alula_version` (строка), `machine` (техническое
имя), `revision` (целое `0..2^53−1`), `types`, `parties`, `signals`, `queries`, `codec`,
`event_envelope`. Никакие прочие поля не входят в projection; в частности, запрещены
`contract_id`, `artifact_id`, instance/pin, адрес/locator, timestamps, title и presentation
metadata. `types` содержит ровно
`aliases`, `records`, `variants`: массивы объявлений с точными ключами соответственно
`name,type`; `name,fields`; `name,cases`. Поле — `{name,type}`, case — `{name,fields}`.
`party` — `{name,kind,inputs,result}`; `signal` — `{name,party,fields}` (общий signal имеет
`party:null`); query — `{name,inputs,result}`. `inputs` и `fields` — массивы `{name,type}`;
`result` — типовой дескриптор или `null` только для party без результата. Неизвестные ключи,
дубликаты и несовпадающие типы отклоняются.

`codec` — точный объект с ключами `domain`, `json`, `type_forms`, `typed_bytes`, `i64`, `int_min`,
`literal_set`, `full_map`, `f64`, `digest`. `domain` — отсортированный набор поддерживаемых
дескрипторов: `alias`, `bool`, `f64`, `full_map`, `i64`, `id`, `int_min`, `list`, `literal_set`,
`map`, `null`, `optional`, `record`, `str`, `tuple`, `variant`; `typed_bytes.markers` содержит
ровно по одному различному маркеру для каждого элемента. `json` фиксирует UTF-8, `bom:false`,
отсутствие Unicode normalization, сортировку object keys, сохранение позиционных массивов, точные
JSON escapes, отказ на duplicate/unknown fields и safe integer range `−2^53..2^53−1`.
`i64` фиксирует wire-строку и диапазон `[-9223372036854775808,9223372036854775807]` строками,
не неточными JSON integers. `int_min` фиксирует `int>=n` и включительную нижнюю границу;
`literal_set` — минимум два уникальных значения и порядок; `full_map` — только fieldless enum
и все его случаи по одному разу. `type_forms` задаёт JSON-форму каждого дескриптора, включая
bounded integer, literal set и full_map. `f64` фиксирует shortest-roundtrip, tie-break, порог
notation, JSON number/tag representation, NaN payload discard, NaN/Inf и signed zero.
`digest` фиксирует алгоритм, domain, separator и output.

Точные значения codec-проекции: `json={encoding:"UTF-8",bom:false,unicode_normalization:"none",object_key_order:"Unicode code point",arrays:"preserve",string_escaping:"JSON-short-escapes; other-U+0000-001F-lowercase-u00xx; slash-literal",duplicate_keys:"reject",unknown_fields:"reject",safe_integer_range:"-9007199254740992..9007199254740991"}`;
`type_forms` сопоставляет каждый элемент `domain` его JSON-форме; например, `i64` — `canonical-decimal-json-string`, `int_min` — такая же строка с lower bound, `tuple` — массив fixed arity ≥2, `full_map` — пары всех enum cases.
Полное значение: `{alias:"declared-name-wraps-base",bool:"json-boolean",f64:"json-number-or-float-tag",full_map:"array-of-all-enum-pairs",i64:"canonical-decimal-json-string",id:"lowercase-uuid-text",int_min:"canonical-decimal-json-string-with-lower-bound",list:"json-array-ordered",literal_set:"json-string-in-closed-set",map:"array-of-key-value-pairs",null:"json-null",optional:"none-some-object",record:"json-object-with-exact-fields",str:"json-string",tuple:"json-array-fixed-arity-at-least-two",variant:"case-fields-object"}`.
`typed_bytes={length:"u64-big-endian",text:"length-prefixed-UTF-8",f64:"length-prefixed-ASCII",markers:{alias:"Y",bool:"B",f64:"F",full_map:"G",i64:"I",id:"U",int_min:"J",list:"L",literal_set:"C",map:"M",null:"N",optional:"O",record:"R",str:"S",tuple:"T",variant:"V"}}`;
`i64={wire:"canonical-decimal-json-string",minimum:"-9223372036854775808",maximum:"9223372036854775807"}`;
`int_min={form:"int>=n",bound:"inclusive-lower-bound"}`;
`literal_set={minimum_values:2,unique:true,order:"Unicode code point"}`;
`full_map={key_type:"fieldless-enum",coverage:"all-cases-exactly-once"}`;
`f64={finite:"shortest-roundtrip-decimal",tie_break:"nearest-then-even",fixed_exponent_min:-6,fixed_exponent_max:20,nan:"NaN",positive_infinity:"Infinity",negative_infinity:"-Infinity",negative_zero:"-0.0",positive_zero:"0.0",json_finite:"number-same-binary64",json_specials:"$float-tag",nan_payload:"discard"}`;
`digest={algorithm:"SHA-256",domain:"alula-value-digest",separator_hex:"00",representation:"sha256:lowercase-hex-64"}`.
Projection validation rejects any other semantic value (including a different hash algorithm, marker,
separator, JSON escape rule, zero form or envelope field rule), even if that value is valid JSON.
Changing the supported profile requires changing this normative table, the projection validator and
its fixed manifest vectors together; the permissive generic JSON canonicalizer is not a supported
contract-manifest encoder.

`event_envelope` — точное semantic projection правил раздела 4 [протокола событий](alula-event-protocol.md):
обязательные поля и запрет неизвестных полей; семантика `event_id`, `instance_id`, привязка
`contract_id` к pin, объектная форма `data`; записи `event_kinds` с именем, обязательными и
условными полями и формой `data` для каждого вида. Все четыре вида представлены: `machine.control`,
`party.signal`, `request.failure`, `request.reply`. Записи projection производятся из
нормативного раздела протокола, а не поддерживаются отдельным ручным источником. Поэтому изменение
правил codec или envelope изменяет содержимое manifest и его `contract_id`; отдельная версия codec
или протокола не вводится.

Для тестового экспортёра projection envelope имеет такую форму; строки-значения условий являются
семантическими идентификаторами, не prose-подсказками:

```json
{"required_fields":["contract_id","data","event_id","event_kind","instance_id"],"unknown_fields":"reject","event_id":"logical-event-not-rpc-call","instance_id":"non-reusable","contract_binding":"contract_id-equals-instance-contract-pin","data":"object-selected-by-event-kind-schema","event_kinds":[{"name":"machine.control","required_fields":["signal"],"conditional_fields":{"pause_id":"parent-continue-only","request_id":"parent-owned-control-only"},"data_shape":"control-data"},{"name":"party.signal","required_fields":["party","signal"],"conditional_fields":{"gate_id":"gate-signal-only","subject_id":"subject-bound-gate-only"},"data_shape":"declared-signal-fields"},{"name":"request.failure","required_fields":["party","request_id"],"conditional_fields":{},"data_shape":"code-and-message"},{"name":"request.reply","required_fields":["party","request_id"],"conditional_fields":{},"data_shape":"result-only"}]}
```

Для изменений envelope-семантики, не выраженных полями/схемами projection, экспортёр обязан
изменить `alula_version`; одинаковое значение `alula_version` запрещено для разных правил
интерпретации envelope. Это зависимость от существующей версии формата, не новый version field.

Record/alias/variant
объявления упорядочиваются по qualified name; поля и cases — по техническому имени; parties и
queries — по name; signals — по паре `(party-or-empty, name)`. Канонизатор **не сортирует**
массивы, а отвергает projection с ненормативным порядком. Позиционные tuple descriptors и любые
значения list сохраняют свой исходный порядок. Object keys сортируются по Unicode code point.
Дубликатные исходные JSON-ключи должны отвергаться parser-ом до projection; числа ограничены
safe integer `−2^53..2^53−1`, JSON float запрещён.

Канонические manifest bytes хешируются как `SHA-256(canonical-manifest-bytes)`; `contract_id` —
`sha256:` и нижний hex digest. Manifest содержит codec definition, поэтому изменение codec,
event-envelope projection, версии формата, типов, ограничений или публичных деклараций меняет вход для `contract_id`. Он не содержит
`artifact_id`, адрес расположения, instance pin или конкретное envelope-событие.

`contract_id` идентифицирует публичный контракт (canonical manifest); `artifact_id`
идентифицирует сборку с машиной, библиотеками, реестрами и семантикой исполнителя, но не её
адрес хранения. Pin экземпляра — пара `(contract_id, artifact_id)` на весь срок экземпляра;
это не digest значения и не hash manifest. Envelope ссылается на `contract_id` и проверяет
его против pin; конкретный envelope не входит в manifest и value digest, его semantic projection
входит в manifest. Событийный digest
dedup/content — отдельная композиция, определённая в [протоколе событий](alula-event-protocol.md),
и включает отдельно typed digest данных и нужные поля события; он не заменяется `contract_id`
или `artifact_id`. Старые pins/dedup остаются связанными с прежним контрактом и
не переинтерпретируются.

### Контрольные векторы

Векторы должны хранить ожидаемые typed bytes и хеши как литералы, не вычисленные проверяемым
encoder; независимый verifier только сверяет полученный результат с ними. Базовые примеры
для `SHA-256(ASCII("alula-value-digest") || 00 || bytes)`:

| Тип/значение | Typed bytes (hex) | Digest |
|---|---|---|
| `null` | `4e` | `sha256:ea86c4d25a8869b9d585b0b8ea94c8bde13675774d82d9ede17af430b10d42aa` |
| `bool true` | `4201` | `sha256:9efe53517fd0b46dfb21dbd5f6552dfb6f02174c453789aa545a45b37a318803` |
| `i64 1` | `490000000000000001` | `sha256:f126d51495c11d6233a6a018928a1ad62a344de07eaaf9775ffd3888135fae4e` |
| `str "1"` | `53000000000000000131` | `sha256:8546005a741bdb09df588b4daa0ebf0abe3f81d1fd53fae393c5f254d52f72d8` |
| list of `i64` `[1]` | `4c000000000000000522693634220000000000000001490000000000000001` | `sha256:6de946c6f9fc52edb75bc7df8d2fdffd2d86396b6d0e230b313aa2466eb157bc` |
| tuple `[i64,str]` `[1,"a"]` | `54000000000000000d5b22693634222c22737472225d000000000000000249000000000000000153000000000000000161` | `sha256:c728f34ab735bff907988def54b8fa023f8cca810972ad7f555b899d23e5fc80` |
| optional `i64 none` | `4f0000000000000005226936342200` | `sha256:43326dc8abcac04352fec30ffd178ada5827e428c26186ce3a748b4ceb9c13f1` |
| record `pkg.A{x: 1}` | `520000000000000005706b672e410000000000000001000000000000000178490000000000000001` | `sha256:c18a00bd335b1c2e769edd475e6a6b2f1715b4833156619fcf15f65c89aa1fd0` |
| record `pkg.B{x: 1}` | `520000000000000005706b672e420000000000000001000000000000000178490000000000000001` | `sha256:f2f0376516c294c44bfa493b13cc45d8baeb5997a9e58da182b173a16fda17e1` |
| `f64 -0` | `4600000000000000042d302e30` | `sha256:e2fcecc4e56d14a2049e1797484760e3364868f950c5bb1ac17d7831cf648704` |
| `f64 +0` | `460000000000000003302e30` | `sha256:2b80404fb011ead8ae5cb9545a2a89a1b1f1f48455b1529c7700d9b9249ee516` |

Хеши в таблице получены отдельным одноразовым SHA-256 расчётом из вручную заданных literal
bytes; они не вычисляются проверяемым encoder. Набор принятия дополнительно фиксирует
`str`/`i64` различие, list/tuple,
отсутствующий/присутствующий optional, record с полем `none`, две одноформенные записи,
две одноформенные variants, `-0`/`+0`, NaN с payload и ±Inf, f64 границы/экспоненту,
перестановку map и manifest key order. Дополнительные литералы:

| Тип/значение | Typed bytes (hex) | Digest |
|---|---|---|
| optional `i64 some(1)` | `4f0000000000000005226936342201490000000000000001` | `sha256:eb12a5ad84315deba619ff967a352897e68fc09947f9d0b618d85c961d513d63` |
| bounded `int>=1`, value `1` | `4a000000000000000f7b22696e745f6d696e223a2231227d0000000000000001` | `sha256:c2fefc80109beb5c07151a390e0d325484b8947615fe5265b42b4ab89a360d3c` |
| literal set `{"a","b"}`, value `"a"` | `4300000000000000197b226c69746572616c5f736574223a5b2261222c2262225d7d000000000000000161` | `sha256:722ddc641d5492aa837b80fc1c785dc05039b4d77fbb4247feb8f49f203d6de5` |
| full_map `pkg.Mode -> str`, `A:a, B:b` | `47000000000000001f7b2266756c6c5f6d6170223a5b22706b672e4d6f6465222c22737472225d7d00000000000000020000000000000022560000000000000008706b672e4d6f64650000000000000001410000000000000000000000000000000a530000000000000001610000000000000022560000000000000008706b672e4d6f64650000000000000001420000000000000000000000000000000a53000000000000000162` | `sha256:5fcc7efd21a9b158818eaf8aa50e8cf6c46c298eb20ed28d113a7c7cba68a823` |
| map `str -> i64`, `[("a",1)]` | `4d00000000000000052273747222000000000000000522693634220000000000000001000000000000000a530000000000000001610000000000000009490000000000000001` | `sha256:94c94f53b028c8150506f07afe04ed57faac5184062ec865b55bc07749e3caee` |
| variant `pkg.V1::Some{x:none}` | `560000000000000006706b672e56310000000000000004536f6d6500000000000000010000000000000001784f0000000000000005226936342200` | `sha256:0d08faee15cc92ab8267c0e48e5626adb0d32d3e1249393244bcf6d954c5d0f7` |
| `f64 NaN` (любой payload) | `4600000000000000034e614e` | `sha256:fe4460b654e3b3d2c376686bc5de8263df70332f22a23237bb4a468a0c2e4ae8` |
| `f64 +Infinity` | `460000000000000008496e66696e697479` | `sha256:d611988263ab0d000d5648b694c66436b82edd3e6e31d8fae810a408a6142be5` |
| `f64 -Infinity` | `4600000000000000092d496e66696e697479` | `sha256:f3f40eaf25087768bf640b3970c98daad123b3db2ea24c509df6876d835fd19b` |

Manifest vector: projection с `alula_version="0.29"`, `machine="Example"`, `revision=1`, пустыми
`aliases/records/variants/parties/signals/queries` и точными `codec`/`event_envelope` projections,
заданными выше;
после сортировки object keys её canonical JSON bytes захешированы как
`sha256:0f1ff7f8cfcb7541b8c3a72074ca2d1aea0b3fdeeb5d52dc81067947015f8792`. Полные ожидаемые
байты и SHA хранятся литералами в `tools/test_value_codec_contract.py`; проверяемый код их
не порождает.

## Граница проверок

Проверки текущего runtime codec доказывают только поведение проверенных функций в
проверенном runtime. Проверки модели или спецификации не являются runtime conformance.
Кандидат этапа 2 задаёт и модельно проверяет encoder/canonicalizer; decoder в кандидате не
реализован и не проверен. Для заявления соответствия реализации нужны отдельные положительные
и отрицательные пробы на каждом заявленном encoder/decoder: границы i64, типы/теги и duplicate
keys, точный binary64 roundtrip, signed zero, эквивалентные записи f64, NaN/±Inf, порядок
словаря и digest. Ни одно из этих модельных доказательств не объявляется runtime conformance.
