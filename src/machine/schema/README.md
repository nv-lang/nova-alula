# The schemas of the Alula tree: `machine/2` and `scenario/0`

> The schemas of the package `alula` at the language **Alula 2.23**, the state of the specification `spec/alula-spec.md` (the text of 2.23 of this repository, changelog AL-115 ... AL-122). The text was
> written by the methodology and finished with the package: every tree below was compiled and run by the program `alula` of the
> package (version 0.5.0), the questions that were left to the package are answered at the end ("Answered and open points").

## What is here

| File | What it describes |
|---|---|
| `machine-2.schema.json` | the tree `machine/2`: a compiled machine, the file `<name>.alula.json` (spec AL-19). A hand-written tree is Alula too, written in the JSON form |
| `scenario-0.schema.json` | a scenario `scenario/0`: the file `<name>.scenario.test.json` (spec AL-20) — events and what each step must leave |

Who is the authority for what:

- **The structure of the tree** — this schema (spec, section 6: "the schema is the first source of the structure of the tree"); the
  **reference** is the decoder `src/machine_table/json.nv`: a key the schema does not list is refused, and a test compares the key lists
  of the schema with the decoder's.
- **The rules of the record and the correspondence "word of the file → key of the tree"** — the specification of the language (sections
  1–12) and its word table `spec/alula-keywords.tsv`.
- **What a schema cannot say** (reads against `Request`/`Reads`, writes against the data, reachability, the classes of the primitives, the
  exhaustiveness of the ends, the namespaces of JSON names) — the checks of `src/machine_table/check.nv` (spec, section 10).
- Expressions are validated by the decoder, not by the schema: the schema requires only the key `op` of a node.

## Versions

| What | Value | Where it is written |
|---|---|---|
| tree format | `machine/2` | the root key `format` of the tree (a constant; it does not change with the language version, spec AL-19) |
| scenario format | `scenario/0` | the root key `format` of a scenario (does not change with the language version, spec AL-50) |
| language version | **2.23** | `- format: 2.23` in the header of a machine file, a functions file and a fragment file; the root key `alula_version` of the tree (the schema accepts only `"2.23"`); the recommended `- machine_version: alula-2.23` (spec 1), which becomes the root key `version` |
| package `alula` | `0.5.0` | `alula version` prints `alula 0.5.0 (Alula 2.23, machine/2)` |
| glossary of automatic names | hash **`60383c370415`** | pinned by the format (spec AL-62); the translator recomputes it from its copy of the normative part of the glossary |
| word table | `spec/alula-keywords.tsv` of 2.23 (218 rows, 17 kinds) | the words of both file languages; the tree does not hold them |

One package version reads exactly one language version: there is no transition period (the owner's word, 2026-10-20). A file with
`format` other than 2.23 and a tree with another `alula_version` are refused with a message that names the version. The versions 2.15–2.23
added **no node** to the tree (spec, section 6); the key changes of the whole line are those of 2.13 (`values`, signals) and the optional
party `counter` of 2.15 (see "Answered and open points").

## The tree does not depend on the language of the file

A machine file is written in Russian (`- language: ru`, the default) or in English (`- language: en`); the keywords of both languages map
to the same keys and the same values (spec 1a, AL-1). Therefore **a Russian file and its English form give one tree**, with two
exceptions that the specification names:

1. **Internal names enter the tree as written** (spec 1a, AL-46/AL-60): the names of parties (`parties[].name`, `states[].party`,
   `cancel_open.party`), constants, parameters (and `project_key`), functions (`definitions[].name`, `call.fn` of an author function) and
   their parameters, event bindings (`bind`), `let` names, lambda parameters, the variable of `for`. A Russian file has them in Cyrillic, an
   English file in Latin.
2. **String values** — text literals, refusal texts, journal parameter values — are kept as the author wrote them (spec AL-10).

Everything that leaves the machine — state names, data, input fields, types, fields, variants, enumeration elements, party signals and
their fields, primitives, the gatekeeper setting — enters the tree by its **JSON name** (below), which is Latin and the same for both
files. The keywords themselves never enter the tree: type words become the tree words `int`, `int>=n`, `text`, `float`, `bool`, `id`
(the file says `str`/`строка` and `f64`/`вещественное`, spec AL-94…AL-96), catalog functions become their English name
(`строка(x)` → `text`, `длина(x)` → `length`, `склеить`/insertion → `concat`), and so on (the mapping table below).

## Names

**A JSON name** is the name in the tree, in the journal, in `all_data` and on the wire. It is built so (spec 1a, AL-53, AL-60):

1. a row of the section `## Names` (Russian `## Имена`, table `| name | json_name |`) — **the only way** to set a JSON name other than the
   automatic one; parentheses after a name in a declaration are an error (removed in 2.16);
2. otherwise a Latin name (`[A-Za-z_][A-Za-z0-9_]*`) is itself;
3. otherwise the English name of the methodology glossary for the **whole** name (`текст_ответа` → `reply_text`, `ХОД_АГЕНТА` →
   `AgentTurn`); the glossary is pinned by the hash `60383c370415` (the normative pairs "Russian → English" of the glossary, 1268 pairs;
   12 signs of SHA-256; spec AL-62) — another hash is the error "the glossary changed without a format change";
4. otherwise the transliteration by the table of spec 1a: type-like names (state, type, variant, enumeration element) in `PascalCase`
   (`ХОД_АГЕНТА` would give `KhodAgenta`), value-like names (datum, input field, field, signal and its field, primitive, setting) in
   `snake_case` (`оставить правку` → `ostavit_pravku`).

The glossary lookup is by the whole name whatever its kind, so an automatic name can be Latin but not the intended one (`ВОПРОС` gives
`AuthorQuestion`, the type `Утверждение` gives `Approval`): the author writes a `## Names` row (`| ВОПРОС | Ask |`). A `## Names` row that
changes nothing is an error ("redundant row"), and so are a row for an internal or undeclared name, a repeated name, a non-Latin JSON
name and a collision. A name declared in several places is qualified by a dotted path (`Type.field`, `Type.Variant`, `party.signal`).
The section has **no node** in the tree: the tree holds only the resulting JSON name. Equal JSON names inside one namespace are an
error (spec AL-58: states, data, input fields, top-level types, the fields of one record or variant, the variants of one type, the
elements of one enumeration, the signals of one party and the fields of one signal, machine signals, primitives, parameters/constants/
settings, and the call namespace of AL-81).

Readable names of the executor and the contract data take the `en` word of the word table (`причина` → `reason`, `остановка` →
`stop_reason`, `все_данные` → `all_data`).

## `machine/2`: the nodes and their keys

"Req." is "required by the schema". Types (the column "type") are the **type strings** of the tree: `int`, `int>=N`, `float`, `text`,
`bool`, `id`, `nothing`, a literal set `"a" | "b"` (under `?` and `[]` in parentheses: `?("a" | "b")`), `?T`, `[]T`, `{K: V}` (a map; the
file says `map[K, V]`/`словарь[K, V]`), `full {K: V}`, `(T1, T2)`, or the JSON name of a declared record or variant. An expression
(`E`) is a node of the next section.

### Root

| Key | Type | Req. | Meaning (spec section) |
|---|---|---|---|
| `format` | `"machine/2"` | yes | the tree format |
| `alula_version` | `"2.23"` | no | the language version; absent means the version of the package `]` |
| `machine` | string `^[A-Za-z][A-Za-z0-9_]*$` | yes | the Latin name of the machine (`- machine:`; the name in the journal, `machine_started`) |
| `version` | string | no | `- machine_version:` |
| `title` | string | no | the text of the header line `# Machine: <text>` (see "Answered and open points") |
| `types` | object `{records, variants}` | no | `## Types` (spec 2) |
| `constants` | `[]constant` | no | `## Constants` |
| `params` | `[]param` | no | `## Parameters` |
| `input` | object `{fields, invariants}` | no | `## Input`: `fields` (req.) `[]field`, `invariants` `[]E` (the lines `- Invariant:`) |
| `data` | `[]datum` | no | `## Data` |
| `parties` | `[]party` | no | `## Parties` |
| `request_limit` | E | no | `- Request limit:` under `## Parties` (absent: 1) |
| `signals` | `[]signal_def` | no | machine signals outside the contract (stop, cancel) — a product key, see "Answered and open points" |
| `definitions` | `[]definition` | no | `## Functions` (the key keeps its name, spec AL-83: "the JSON keys of the tree do not change") |
| `includes` | `[]include` | no | the lines `functions: <name> version <N> hash <hex12>` of `## Includes` |
| `fragments` | `[]fragment_use` | no | the include lines of fragments (a product key, spec 1b (м)); the fragment itself is substituted into the tree |
| `initial` | string | yes | `Initial state: NAME` (the JSON name of the state) |
| `error_end` | string | no | the end entered on a machine error: the end whose JSON name is `Errored` (Russian `ОШИБКА`) — a rule of the package |
| `common_events` | `[]row` | no | `## Common events` of a substituted fragment (tried before the rows of a state) |
| `states` | `[]state` (min 1) | yes | `## States` |
| `ends` | object `{result, rows}` | yes | `## Ends`: `result` (req.) the type of `- Result:`; `rows` (req.) `[]end_row` |
| `primitives` | `[]string` | no | `## Primitives`: the JSON names of the host primitives the machine calls |

### Types: `types.records[]`, `types.variants[]`, `field`

| Node | Key | Type | Req. | Meaning |
|---|---|---|---|---|
| record | `name` | string | yes | `type Name { … }` |
| | `fields` | `[]field` | yes | the fields in the order of the declaration |
| variant (also an enumeration) | `name` | string | yes | `type Name enum …` — one node kind for every enumeration, with or without fields at its forms (AL-99); there is no `enum` node |
| | `cases` | `[]{name, fields?}` (min 1) | yes | the forms; a form without fields has no `fields` |
| | `values` | `[][name, value]` | no | the element values `El = "value"`: pairs [JSON name of the element, value], value `^[a-z][a-z0-9_]*$`, in the order of the declaration; only forms without fields; absent when no element has a value (spec AL-41, П-7) |
| field | `name` | string | yes | the JSON name of the field |
| | `type` | type string | yes | |

`FailCode` (the ten failure causes: `NoResult`, `ModelRefused`, `ConnectionLost`, `FormNotFixed`, `Timeout`, `StoppedByHuman`,
`CeilingReached`, `Cancelled`, `MaxTokens`, `MaxTurnRequests`) is built in and is not declared in the tree.

### `constant`, `param`, `datum`

| Node | Key | Type | Req. | Meaning |
|---|---|---|---|---|
| constant | `name`, `type`, `value` | string, type, E | yes | `| name | type | value |` of `## Constants`; the name is internal (as written) |
| param | `name`, `type`, `default` | string, type, E | yes | `## Parameters`; the name is internal |
| | `project_key` | string | no | the key after `project.`/`проект.` of the column "project override"; absent for `—` |
| datum | `name` | string | yes | the JSON name of the datum, or a path `name[*].field` (it carries only the marks) |
| | `type` | type | yes | |
| | `initial` | `{expr: E}` or `{from_input: "field"}` | no | the column "initial": an expression or `input.<field>`; absent for a path |
| | `monotonic` | `true` or `{bound: E}` | no | "non_decreasing": `yes` → `true`, `yes, <= expr` → `{"bound": E}`; `—` → absent |
| | `writes` | `rows` \| `mechanics` \| `rows_and_mechanics` \| `fragment` \| `rows_and_fragment` | no (default `rows`) | the column "writes" |

### `party`, `signal_def`

| Key | Type | Req. | Meaning |
|---|---|---|---|
| `name` | string | yes | the party name — internal, as written (`агент` in a Russian file) |
| `id` | string | no | the Latin id (the request id `<id>-<number>`); empty for a party used with a set |
| `kind` | `agent` \| `human` \| `enhanced` \| `gatekeeper` \| `machine` | yes | the column "kind"; `human or agent by setting <name>` is `gatekeeper` (AL-4) |
| `profile` | E | no | the column "profile" (`—` → absent) |
| `signals` | `[]signal_def` | no | the party signals of the column "signals" (`human`, `enhanced`, `gatekeeper`; AL-38) |
| `progress` | `[]signal_def` | no | the parts of an answer of an agent or a machine (a product key) |
| `setting` | string | no | the setting name of a `gatekeeper` (a JSON name) |
| `nested` | string | no | `machine <name>(…)`: the name of the nested machine in the registry of the caller |
| `input_type` | type | no | `machine …(input Type, …)` |
| `result` | type | no | `agent(result T)`, `machine …(…, result T)` (the checks require it for `agent` and `machine`) |
| `parse` | `{primitive, role?, type}` | no | `; parse: primitive("role") -> Type` of a `machine` party |
| `counter` | string | no | the datum of the attempt counter (the column "counter"); **absent for a `human` party with free input** (`—`, AL-52) |

`signal_def` (`$defs/signal_def`): `name` (req., the JSON name of the signal), `fields` (`[]field`) — the
declaration `s` or `s { field T, … }`.

### `definition`, `include`, `fragment_use`

| Node | Key | Type | Req. | Meaning |
|---|---|---|---|---|
| definition | `name` | string | yes | `fn name(…)`/`функция имя(…)` — the name is internal (as written) |
| | `params` | `[]field` | yes | the parameters (internal names) |
| | `result` | type | yes | `-> Type` |
| | `body` | E | yes | `=> expr`, or a block body `{ let …; expr }` as nested `let` nodes |
| include | `name`, `version`, `hash` | string, string, `^[0-9a-f]{12}$` | yes | `functions: <name> version <N> hash <hex12>`; the tree also carries a copy of the types, constants and functions of the file |
| fragment_use | `name` | `"Pause"` | yes | the include line of the fragment "Pause" |
| | `args` | object | yes | `halt_signal`, `halt_code`, `nested`, `cancel_requests`, `reenter`, `write_right` — each an E (literals) |

### `state`

| Key | Type | Req. | Meaning |
|---|---|---|---|
| `name` | string | yes | the JSON name of the state (`### NAME — kind`) |
| `kind` | `appeal` \| `operation` \| `fork` \| `end` | yes | |
| `reads` | `[]string` | no | `- Reads:` of an operation, a fork, an end (the JSON names); an end without the line has `[]` (as the translator writes it) |
| `reads_all` | bool | no | `- Reads: all_data` (the end ERROR) |
| `party` | string | no | `- Party:` (the party name, internal) |
| `set` | E | no | `; set: <expr>` |
| `silence` | E | no | `- Idle term:` (ms) |
| `edits`, `edit_check` | string | no | `- Edits: <datum>; check: <primitive>` |
| `form_returns` | int ≥ 0 | no | `- Form returns:` |
| `inputs` | `[]{field, value, reads?}` | no | the table of `- Request:`: `field` (req.), `value` (req., E; the cell `—` gives the name node of the field, AL-56), `reads` `party` (default) \| `executor` |
| `accept` | `[]{event, actions?}` | no | `- On accept:` |
| `entry` | actions | no | `- On entry:` (`let` outside a block is `bind`) |
| `rows` | `[]row` | no | the table of rows |
| `except` | `{field, values}` | no | `- Except: field in [v, …]` (both req.; `values` strings) |

### `row`, `event`

| Key | Type | Req. | Meaning |
|---|---|---|---|
| `n` | int ≥ 1 | yes | the column `№` |
| `event` | event | yes | the column "Event" |
| `cond` | E | no | the column "Condition" (signals of common events, forks) |
| `else` | bool | no | the condition `else` |
| `actions` | actions | no | the column "Actions" |
| `to` | string | no | the column "To": a state, `@previous`, `@same`, `@prepare_return`; absent when the actions end in `machine_error` |
| `restart` | bool | no | the suffix `, rerun` (`, запуск заново`) |

| `event.kind` | Other keys | File |
|---|---|---|
| `answer` | `bind` (string) | `response`, `response(name)` |
| `answer_variant` | `variant` (req.), `bind` `{field: name}` | `response: Var`, `response: Var { field, field: name }` |
| `failure` | `reasons` (`[]string`, the JSON names of `FailCode`), `bind` (string; `reason` for `причина`) | `failure`, `failure(reason)`, `failure(reason in [A, B])` |
| `timeout` | — | the term of silence (a product event, see "Answered and open points") |
| `progress` | `name` (req.), `bind` `{field: name}` | a part of an answer (a product event) |
| `signal` | `name` (req.), `bind` `{field: name}` | `signal(s)`, `signal(s { field: name })` — a party signal and a machine signal are one kind (AL-38) |
| `now` | — | `immediate` (`сразу`) |

### Actions (`do`)

| `do` | Keys (req. in bold) | File |
|---|---|---|
| `assign` | **`target`**, **`value`** | `x = e`, `x[k] = e`, `x[k].f = e`; `target` is a datum name or `{name, path: [{key: E} \| {field: "f"}]}` |
| `add` | **`target`**, **`value`** | `x += e` |
| `journal` | **`code`**, `params` `[]{name, value: E}` | `journal("code", name: e, …)` |
| `journal_value` | **`value`** | `journal(value)` (`journal_event(…)`, `transition_note`) |
| `journal_all` | — | `journal(all_data)` |
| `for_each` | **`var`**, **`in`**, **`body`** (actions) | `for x in xs { … }` (Russian `для x из xs { … }`) |
| `let` | **`name`**, **`value`**, **`body`** (actions) | a binding with a scope: `{ let x = e; actions }` (verified: an action block with `let` gives this node, as the former `let … in` did) |
| `bind` | **`name`**, **`value`** | `let x = e` in "On entry" / "On accept" (outside a block) |
| `if` | **`cond`**, **`then`**, `else` (actions) | `if e then { … } else { … }` |
| `call` | **`primitive`**, `args` `[]E` | `call(primitive, …)` as an action |
| `machine_error` | **`code`**, `params` | `machine_error(code, name: e)` |
| `cancel_open` | `party`, `except` `[]E` | `cancel_open`, `cancel_open(except: nested)`; `party` is a product key |
| `pass` | **`nested`** (E), **`signal`** | `pass(nested, signal)` (fragment only) |

### `end_row`

| Key | Type | Req. | Meaning |
|---|---|---|---|
| `state` | string | yes | the column "end" |
| `n` | int ≥ 1 | yes | the column `№` |
| `when` | E | yes | the column "when" (`true` is `{"op":"lit","value":true}`) |
| `answer` | `{kind: "answer", value: E}` or `{kind: "refusal", code: E, text: E}` | yes | `Response(e)` / `Refusal(FailCode.X, text)` |

### Expressions

One object per node with the key `op` (the list is the top of `src/machine/expr.nv`):

| `op` | Keys | Note |
|---|---|---|
| `lit` | `value` | the lossless JSON form of a value of the core; `null` is `none`; a float is written with a fraction or an exponent (`1.0`) |
| `name` | `name` | a datum (JSON name), a constant/parameter/binding (as written), a readable name (`en` word) |
| `field` | `of`, `name` | `e.f`; a tuple field `t.0` |
| `index` | `of`, `index` | `e[k]` |
| `call` | `fn`, `args` | a catalog function or list function (English name), an author function (as written); a lambda is an argument |
| `lambda` | `params`, `body` | only as a list function argument |
| `primitive_call` | `name`, `args` | `call(primitive, …)` in an expression |
| `match` | `on`, `arms: [{patterns, guard?, body}]` | patterns: `{"kind":"any"}` (`else`), `{"kind":"lit","value":V}`, `{"kind":"case","type"?,"name","bind"?:{field: name}}` |
| `let` | `name`, `value`, `body` | a binding of a block expression |
| `if` | `cond`, `then`, `else` | |
| `record` | `type`, `fields` `{f: E}` | `Type { f: e }` |
| `with_field` | `of`, `fields` | `{ ...e, f: e }` |
| `variant` | `type`, `name`, `fields?` | `Type.Var { f: e }`, `Type.El`, a bare `El` |
| `list`, `tuple` | `items` | `[a, b]`, `(a, b)` |
| `dict` | `entries: [{key, value}]` | `[k: v]` |
| `+ - * / % == != < <= > >= and or ??` | `left`, `right` | the operator symbol is the `op` |
| `not`, `neg` | `operand` | `not e`, `-e` |

## Mapping: Alula construct → tree node

| Construct (English form / Russian form) | Tree |
|---|---|
| record `type Name { f T }` / `тип Имя { п Т }` | `types.records[]` `{name, fields}` |
| enumeration `type Name enum A \| B` / `тип Имя перечисление А \| Б` | `types.variants[]` `{name, cases: [{name: "A"}, {name: "B"}]}` |
| enumeration with values, header `type Name enum` and lines `\| El = "value"` | the same node plus `values: [["El", "value"], …]` (the key only at a node with values) |
| enumeration with fields (a variant) `\| Var { f T }` | `cases: [{name: "Var", fields: [{name, type}]}]` |
| datum row of `## Data` | `data[]` `{name, type, initial, monotonic, writes}` |
| party row of `## Parties` | `parties[]`; signals of the column "signals" → `signals[]` |
| state `### NAME — kind` | `states[]` `{name: <JSON name>, kind}` |
| transition row | `rows[]` `{n, event, cond, else, actions, to, restart}` |
| literal `12`, `1_000`, `1.5e-3`, `"a"`, `true`, `none` | `{"op":"lit","value":12}`, `1000`, `0.0015`, `"a"`, `true`, `null` (`_`, exponents and escapes do not enter the tree, AL-91, AL-92) |
| name `x` | `{"op":"name","name":"x"}` (JSON name for data, as written for internal names) |
| `f(a)` — catalog function | `{"op":"call","fn":"<en>","args":[…]}`: `строка(x)`/`text(x)` → `fn: "text"`, `вещественное(x)`/`float(x)` → `"float"`, `число(x)`/`int(x)` → `"int"` (the call names did not change, AL-94…AL-96) |
| `f(a)` — author function | `{"op":"call","fn":"<name as written>","args":[…]}` |
| `call(p, a)` in an expression | `{"op":"primitive_call","name":"p","args":[…]}` |
| method `xs.filter(x => e)` (the 8 list functions) | `{"op":"call","fn":"filter","args":[xs, {"op":"lambda","params":["x"],"body":e}]}` — the receiver is the first argument (AL-78) |
| `xs.fold(s, (m, x) => e)` | `call fn=fold args=[xs, s, lambda params ["m","x"]]` |
| range `a..b` | `{"op":"call","fn":"range","args":[a, b]}` (AL-76) |
| range `a..=b` | `call fn=range args=[a, {"op":"+","left":b,"right":{"op":"lit","value":1}}]` (AL-86) |
| insertion `"a${x}"` | `call fn=concat args=[{"op":"lit","value":"a"}, call fn=text args=[x]]`; a single `"${x}"` is `call fn=text args=[x]`; empty text parts are dropped (AL-80) |
| `x in [a, b]` (Russian `x в [a, b]`) in "when" and other expressions | `(x == a) or (x == b)` as `==` and `or` nodes (left-nested); in `failure(reason in […])` → `event.reasons`; in `Except:` → `state.except` (verified; an empty set gives `false`) |
| `if c then { a } else { b }` | `{"op":"if","cond":c,"then":a,"else":b}` (a block of one expression is the expression) |
| block `{ let x = e; y }` | `{"op":"let","name":"x","value":e,"body":y}` (nested for several bindings; AL-75: "the tree does not change") |
| `match e { A \| B => 1, Var { f: v } if g => 2, else => 3 }` | `{"op":"match","on":e,"arms":[{"patterns":[{"kind":"case","type":"T","name":"A"},…],"body":…},{"patterns":[{"kind":"case","name":"Var","bind":{"f":"v"}}],"guard":g,"body":…},{"patterns":[{"kind":"any"}],"body":…}]}`; a literal alternative is `{"kind":"lit","value":V}` |
| bare element name `Done` (AL-88) | the same node as `Type.Done` (`variant` / `case` with the type found by the expected type) (verified: a `variant` node and a `case` pattern carry `type`, the translator finds it by the declared types; `answer_variant` has the key `variant` only) |
| `Type { f: e }`, `{ ...r, f: e }`, `Type.Var { f: e }` | `record`, `with_field`, `variant` |
| `[a, b]`, `[k: v]`, `[]`, `(a, b)` | `list`, `dict`, `list` or `dict` by the expected type, `tuple` |
| `unreachable` | `{"op":"call","fn":"require","args":[{"op":"lit","value":null}]}` (as the package writes it today) |
| `journal_event(code, name: v)` | `call fn=journal_event` with positional args `[code, "name", v, …]` (as in the trees of `main`) |
| action `x = e`, `x += e`, `x[k].f = e` | `assign`, `add`, `assign` with a path |
| `for x in xs { … }` / `для x из xs { … }` | `{"do":"for_each","var":"x","in":xs,"body":[…]}` |
| `let x = e` in "On entry"/"On accept" | `{"do":"bind","name":"x","value":e}` |
| `journal("c", k: v)`, `journal(value)`, `journal(all_data)` | `journal`, `journal_value`, `journal_all` |
| `response(t)` / `ответ(т)` | `{"kind":"answer","bind":"t"}` (`"т"` in a Russian file) |
| `failure(reason)` / `сбой(причина)` | `{"kind":"failure","bind":"reason"}` in both languages (AL-49) |
| `Response(e)`, `Refusal(FailCode.X, t)` | `end_row.answer` |
| the comment `//`, the section `## Names`, prose | nothing (they do not enter the tree) |

## `scenario/0`: the keys

| Node | Key | Type | Req. | Meaning |
|---|---|---|---|---|
| root | `format` | `"scenario/0"` | yes | |
| | `machine` | string | yes | the Latin name of the machine (`machine` of the tree) |
| | `name` | string | no | a description |
| | `start_at` | int (default 1000) | no | the clock of the in-memory world, ms |
| | `standalone` | bool (default false) | no | the steps play the parties of the kind `machine` |
| | `params` | object, keys `^проект\.` | no | parameter overrides: `проект.<key>` → value (spec П-9) |
| | `steps` | `[]step` | yes | |
| step | `do` | `feed` (default) \| `accept` \| `dispatch` \| `pump` \| `deliver` \| `advance` \| `restart` | no | |
| | `event` | event | for feed, accept, deliver | |
| | `ms` | int ≥ 0 | for advance | |
| | `host` | object | no | answers of host primitives from this step on |
| | `expect` | expect | no | what the engine the step acts on must leave |
| | `on` | string | no | the request id of a nested machine the step acts on |
| | `also` | `{parent \| <request id>: expect}` | no | what other engines must leave |
| event | `kind` | `signal` \| `progress` \| `answer` \| `failure` \| `timeout` \| `start` | yes | |
| | `name` | string | for signal, progress | the JSON name of the signal |
| | `party` | string | no | for a signal: the party that declared it (AL-38) |
| | `request` | string | no | the request id (`agent-1`); for `start` the id of the call |
| | `input` | string or object | no | one field → its value, several → `{field: value}`, none → absent (П-8); for `start` the input object |
| | `code` | string | no | the `FailCode` case of a failure |
| | `source` | string | no | the key of the source, acknowledged after the commit |
| expect | `state`, `journal` `[]{code, params?}`, `data`, `queue`, `open`, `outcome`, `sent`, `cancelled` | | no | `outcome`: `none`, `answer:<text>`, `refusal:<Code>`; `queue`: `send <id>`, `cancel <id>`, `in <name>`; a part not named is not compared |

A signal of a party with free input (AL-51) is fed as an ordinary `signal` event without `request`.

## Example

A minimal machine: it asks an agent once and ends with the answer, or with the failure code in the text. The Russian file uses
glossary names (`ХОД_АГЕНТА` → `AgentTurn`, `КОНЕЦ` → `End`, `текст_ответа` → `reply_text`, `попытка_агента` → `agent_attempt`),
so it needs no `## Имена`; the text literals are the same in both files so that the trees are equal up to internal names.

### `ask.alula.md` (Russian)

```
# Машина: ask

- machine: ask
- machine_version: alula-2.23
- format: 2.23

## Данные

| имя | тип | начальное | не убывает | пишет |
| текст_ответа | строка | "" | — | действия |
| попытка_агента | число>=0 | 0 | да | механика |

## Стороны

| имя | идентификатор | вид | профиль | сигналы | счётчик |
| агент | agent | agent(итог строка) | — | — | попытка_агента |

## Состояния

Начальное состояние: ХОД_АГЕНТА

### ХОД_АГЕНТА — обращение
- Сторона: агент
- Срок тишины: 60_000

| № | Событие | Условие | Действия | Куда |
| 1 | ответ(т) | — | текст_ответа = т; журнал("callee_answered", label: т) | КОНЕЦ |
| 2 | сбой(причина) | — | текст_ответа = "failed: ${причина}"; журнал("callee_failed", reason: строка(причина)) | КОНЕЦ |

### КОНЕЦ — конец
- Читает: текст_ответа

## Концы

- Результат: строка

| конец | № | когда | ответ |
| КОНЕЦ | 1 | истина | Ответ(текст_ответа) |
```

### `ask.en.alula.md` (English)

```
# Machine: ask

- machine: ask
- machine_version: alula-2.23
- format: 2.23
- language: en

## Data

| name | type | initial | non_decreasing | writes |
| reply_text | str | "" | — | rows |
| agent_attempt | int>=0 | 0 | yes | mechanics |

## Parties

| name | id | kind | profile | signals | counter |
| agent | agent | agent(result str) | — | — | agent_attempt |

## States

Initial state: AgentTurn

### AgentTurn — appeal
- Party: agent
- Idle term: 60_000

| № | Event | Condition | Actions | To |
| 1 | response(t) | — | reply_text = t; journal("callee_answered", label: t) | End |
| 2 | failure(reason) | — | reply_text = "failed: ${reason}"; journal("callee_failed", reason: text(reason)) | End |

### End — end
- Reads: reply_text

## Ends

- Result: str

| end | № | when | response |
| End | 1 | true | Response(reply_text) |
```

The separator rows (`|---|`) are omitted here for room; the file that the program reads has them (the canonical form of 1b writes
them and also writes every section, an empty one as `—`). The journal codes `callee_answered` and `callee_failed` are two codes of the table of the host "examples" (`examples/journal.md`); the table of the language is `src/machine/journal_language.md` (35 codes).

### `ask.alula.json` — the tree of the Russian file (the output of `alula compile`)

```json
{
  "format": "machine/2",
  "alula_version": "2.23",
  "machine": "ask",
  "version": "alula-2.23",
  "title": "ask",
  "data": [
    { "name": "reply_text", "type": "text", "initial": { "expr": { "op": "lit", "value": "" } }, "writes": "rows" },
    { "name": "agent_attempt", "type": "int>=0", "initial": { "expr": { "op": "lit", "value": 0 } }, "monotonic": true, "writes": "mechanics" }
  ],
  "parties": [
    { "name": "агент", "id": "agent", "kind": "agent", "result": "text", "counter": "agent_attempt" }
  ],
  "initial": "AgentTurn",
  "states": [
    {
      "name": "AgentTurn", "kind": "appeal", "party": "агент",
      "silence": { "op": "lit", "value": 60000 },
      "rows": [
        { "n": 1, "event": { "kind": "answer", "bind": "т" },
          "actions": [
            { "do": "assign", "target": "reply_text", "value": { "op": "name", "name": "т" } },
            { "do": "journal", "code": "callee_answered", "params": [ { "name": "label", "value": { "op": "name", "name": "т" } } ] }
          ],
          "to": "End" },
        { "n": 2, "event": { "kind": "failure", "bind": "reason" },
          "actions": [
            { "do": "assign", "target": "reply_text", "value":
              { "op": "call", "fn": "concat", "args": [
                { "op": "lit", "value": "failed: " },
                { "op": "call", "fn": "text", "args": [ { "op": "name", "name": "reason" } ] } ] } },
            { "do": "journal", "code": "callee_failed", "params": [ { "name": "reason", "value":
              { "op": "call", "fn": "text", "args": [ { "op": "name", "name": "reason" } ] } } ] }
          ],
          "to": "End" }
      ]
    },
    { "name": "End", "kind": "end", "reads": [ "reply_text" ] }
  ],
  "ends": {
    "result": "text",
    "rows": [
      { "state": "End", "n": 1, "when": { "op": "lit", "value": true },
        "answer": { "kind": "answer", "value": { "op": "name", "name": "reply_text" } } }
    ]
  }
}
```

The tree of the English file is the same except the internal names: `"name": "agent"` of the party and `"party": "agent"` of the
state, `"bind": "t"` and `{"op": "name", "name": "t"}` instead of `т`. `title` is the text of the header line `# Машина: ask`; the `concat`/`text` unfolding and `60_000` → `60000` follow spec AL-80 and AL-91.

Check it (run with the program `alula 0.5.0`: the two files compile to the two trees, the converted English file gives the English tree, both trees pass the scenario below):

```
alula compile ask.alula.md -o ask.alula.json
alula compile ask.en.alula.md -o ask.en.alula.json
alula convert ask.alula.md --language en -o ask.conv.alula.md
alula run ask.alula.json ask-answer.scenario.test.json
```

### `ask-answer.scenario.test.json`

```json
{
  "format": "scenario/0",
  "machine": "ask",
  "name": "the agent answers: the machine ends with the answer",
  "start_at": 1000,
  "steps": [
    { "do": "feed", "event": { "kind": "start" },
      "expect": { "state": "AgentTurn", "sent": ["agent-1"], "open": ["agent-1"] } },
    { "do": "feed", "event": { "kind": "answer", "request": "agent-1", "input": "hello" },
      "expect": { "state": "End", "journal": [ { "code": "callee_answered", "params": { "label": "hello" } } ],
                  "data": { "reply_text": "hello" }, "open": [], "outcome": "answer:hello" } }
  ]
}
```

The same scenario runs on the tree of either file: it names only JSON names (`AgentTurn`, `End`, `reply_text`) and the party id
(`agent-1`).

## Answered and open points

The thirteen questions that the methodology left to the package when it wrote the first text of this file are answered from the code and the tests of
the package; what only the methodology can decide is marked **open**. The numbers follow the order in which the questions stood.

| # | Question | Answer | State |
|---|---|---|---|
| 1 | Does an action block with `let` give the node `let`? | Yes: `{ let x = e; actions }` is `{"do":"let","name":"x","value":e,"body":[actions]}`; a block without `let` is flattened into the list of actions (no node of its own); a statement `let x = e` outside a block is `bind` | solved (`machine_text/v222_action_test.nv`) |
| 2 | Is `x in [a, b]` unfolded into `==` and `or`? | Yes, left-nested; `failure(reason in […])` is `event.reasons`, `Except: f in […]` is `state.except`; an empty set is `false` | solved (`machine_text/v222_expr_test.nv`) |
| 3 | Is `type` always filled at a bare element name? | The `variant` node and the `case` pattern of `match` always carry `type`; `answer_variant` has the key `variant` only (the type is the result type of the party). The translator finds the type of a bare name by the declared types, with no expected type (AL-88, AL-104): a name that two types have, and a name that is also a datum, a constant, a parameter or a binding, is an error that asks for `Type.El` | solved (AL-104) |
| 4 | `alula_version` or `table_format`? | The package keeps `alula_version` (the schema, the decoder, `alula version`, the scenarios of the product); the specification says so since AL-108: the key is optional, its value is `"2.22"`, another version is an error that names it, there is no `table_format` | solved (AL-108) |
| 5 | The sections `## Сигналы`, `## Части ответа`, the events `срок` (`timeout`), `часть` (`progress`), the key `party` of `cancel_open`, the end `Errored`, `*.alula.txt` | Product extensions of the package, kept in `keywords_product.tsv` (the words) and not in `spec/alula-keywords.tsv`; the tree keys `signals`, `progress`, the event kinds `timeout`, `progress`, `cancel_open.party`, `error_end` are marked so in the schema | **open** (the methodology may take them into the table of words or leave them to the product) |
| 6 | The names `cancel_requests`, `reenter` of the fragment "Pause" against `request_cancel`, `reentry` of the specification | A deliberate tree name of the package (`keywords_product.tsv`, `fragment_param`); the machines and the scenarios of the product use them | **open** |
| 7 | `event.party` of a scenario is a name, so a scenario of a Russian file does not fit an English one | The runner accepts the name **or the id** of the party (`ScEvent.party`); a scenario that names the id fits both files | solved |
| 8 | The prefix `проект.` of the scenario `params` | The prefix is one in both languages (`PROJECT_PREFIX`); the English file writes `project.<key>` in the column, the tree holds `project_key` = `<key>` | solved for the package; **open** for the methodology whether an English scenario has its own prefix |
| 9 | `title` or the Latin name? | `title` is the text after `# Машина:`/`# Machine:` (the whole line), `machine` is the Latin name of the line `- machine:`; the specification 1b (а) says otherwise | **open** (a correction of the text for the methodology) |
| 10 | The names of the request fields | The JSON name of a request field is taken in this order: the field of a declared type, form or signal; the field of the input; a datum or constant; the field of the event (`событие.идентификатор`); the glossary; a Latin name as it is; else an error | solved (the rule is in `parse.nv`, `tr_field_name`); the list is **open** for the specification 1a |
| 11 | The unfolding of `in […]` for 2.22 | Kept (see 2) | solved |
| 12 | Bare names in the tree | See 3 | solved |
| 13 | Blocks of actions | See 1 | solved |

Further differences between the specification and the package, and what is done about them:

1. **The keys of 2.13** (`values`, `signals`, the event kind `signal`, the argument `halt_signal`, the scenario key `party`) are in the schemas and in the decoder.
2. **`counter`** is optional in the schema and in the checks for a `human` party with free input (AL-52); every other party needs it.
3. **The wording** of the descriptions of the schema is brought to 2.22 (`Reads:`/`Request:` instead of `Input:`); the key `definitions` keeps its name (AL-83: the keys of the tree do not change), `functions_version` is a header key of a functions file and in the tree it is `includes[].version`.
4. **The result type of an agent.** Solved by AL-109: the result of an `agent` party is a type of `## Types` or a built-in type (`text`, `int`, `bool`, …), the result of a `machine` party is a type of `## Types`. The translator accepts a built-in type for an `agent` and refuses a name that no type declares; for a `machine` party it does not tell a built-in type from a declared one (the check compares the result with the result of the called machine), which is wider than the text.
5. **`same` in "To".** Solved by AL-111: `то же` (`same`) stays in the state and runs the actions of the row only; `то же, запуск заново` (`same, rerun`) enters the state again, cancels the open request of the appeal and sends a new one (the tree: `"to": "@same"` with `"restart": true`); both are allowed in the rows of an appeal and in the common events. The check says nothing about the mark `restart` at a target that is no appeal (the methodology: a check of its own, by a task of the consumer, is to come).
6. **`$id`** of both schemas points to `nv-lang/nova-alula`.
