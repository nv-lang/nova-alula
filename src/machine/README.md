# machine: the core of the machines as data

The goal of the owner of the CrewHarness product (2026-10-19): every ability of the current plugin and the state machines of the methodology are written as TABLES that one
interpreter on Nova runs inside the bare product; the user writes no Nova. Since task 144 of the CrewHarness repository the core lives in this package (`alula`) and the product depends on it;
the numbered tasks named in this file are the tasks of that repository (`doc/tasks/NNN-.../` there). This directory is the first stage, the CORE that does not
depend on the final syntax of the tables: the dynamic value, the tree of an expression, a pure evaluator, the types of the data and the registry of the
primitives of the host. Task 106 (`doc/tasks/106-expr-evaluator/`). Task 107 (`doc/tasks/107-table-machine/`) added the interpreter of the table of states on top of this core (see "The interpreter of a machine that is data" below); the next tasks are the translator of the tables of the methodology into the JSON and the transfer of the agent step and of the other machines.

The source of the language is Alula, the format of the methodology, version 2.5 (`spec/alula-spec.md` of the package; until version 0.3.2 the text lived in `unitcraft/ai-dev-methodology`), the pilots
"Agent step" and "Meeting" (the markup of the 80 functions of the meeting, the primitives of the agent step) and the dictionary of the methodology (English names).
Where the format is silent the choice is marked "decision" below and in `doc/tasks/106-expr-evaluator/analysis.md` and `doc/tasks/107-table-machine/analysis.md`.

Task 107 (`doc/tasks/107-table-machine/`) built the interpreter on top of this core. It lives in three more folders, because one folder is one module and one unit of
tests under Oracle 0.1.0 and the output of a unit must stay under 4 KB:

| Folder | Module | What it is |
|---|---|---|
| `src/machine/` | `alula.machine` | the core (task 106), the registry and the journal of the host as data (`host.nv`, `journal_language.md`, task 158), the types syntax `parse_spec` (`spec.nv`) and the schemas `schema/` compiled into the binary |
| `src/examples/` | `alula.examples` | tests only (task 158): the machines, the tables, the scenarios, the registry and the journal of the host "examples" (`examples/` of the package) and the registry of the samples (`spec/samples/registry.md`) compiled into the tests |
| `src/machine_table/` | `alula.machine_table` | the model of a machine, the decoder of the JSON tree `machine/2`, the type syntax, the checks of a table |
| `src/machine_run/` | `alula.machine_run` | the interpreter `AlulaMachine`, the state, the host of the primitives, the scenario runner `scenario/0` |
| `src/machine_text/` | `alula.machine_text` | the translator of Alula (the tables in Russian or English, format 2.24 only) into the JSON `machine/2` and the reverse generator JSON -> Alula ([README](../machine_text/README.md), tasks 108, 113) |
| `src/machine_text_eq/` | `alula.machine_text_eq` | tests only: the pilot "Agent step" (the sample of the specification), the examples of the format, the definitions of the meeting |
| `src/machine_agent/` | `alula.machine_agent` | tests only: the samples of the methodology (`spec/samples/`, copies in `cases/`) go through the translator whole, in both languages, with the numbers and the JSON names of the reference (tasks 110, 151, 152, 154); the agent step as a machine of the methodology is tested in the product (task 158) |
| `src/machine_text_lang/` | `alula.machine_text_lang` | tests only (task 113): the two languages of Alula - an English file gives the JSON of the Russian one, a word of the other language is an error with its line, the news of 2.9 - 2.11 |
| `src/machine_text_render/` | `alula.machine_text_render` | tests only (task 113): the reverse generator - the canonical form, the circles "tree - file - tree" in both languages on every machine |
| `src/machine_agent_en/` | `alula.machine_agent_en` | tests only (task 113): the English sample of the agent step of the methodology goes through the translator and equals the Russian one (the 75 scenarios are run in the product, task 158) |
| `src/machine_text_fmt/` | `alula.machine_text_fmt` | tests only (task 110): format 2.7 in the translator - prose and warnings, the expansion of a fragment, sets of literals, separators and `\|`, enum words, the hash of the sample of definitions |
| `src/machine_nested/` | `alula.machine_nested` | tests only (task 119): the nested machines in the translator, the checks and the reverse generator (the examples of the meeting, the party kind `machine`, `Signal`, `State`, the profile, the edits, the form returns, the set limit) |
| `src/machine_nested_run/` | `alula.machine_nested_run` | tests only (task 119): the scenarios of the pairs "parent + nested machine" of the examples (`nested-call-*` 17, `nested-set-*` 9, `batch-*` 3), the events of the protocol of a call, the registry, the runner |

Task 158 (`doc/tasks/158-alula-split/`) split the package and the product. The units `machine_runner`, `machine_session`, `machine_cycle`, `machine_dialog`, `machine_nested_eq`, `machine_agent` (the tests of the machine), `machine_registry` and the parts of the other units that run a machine of the product or of the methodology live in the product repository (`src/machine_*`, `src/*_machines`); this package keeps the language, the examples (`examples/`) and the samples of the specification. The sections below that tell the history of the tasks 109-126 keep the names of their time (`standard_registry()`, `standard_types()`, `machines/`, `scenarios/` of this folder): the machines of the product and of the methodology, their scenarios and their registry are in the CrewHarness repository since 0.4.0.

The proofs that need the hand-written chat machine on Nova (`machine_chat`: the chat machine as data equals it; `machine_dialog_eq`: the dialog equals it, with the failure injection) import the module `chat` of
the CrewHarness product and stay in the product repository; they read the machines and the scenarios of this package through `alula.machine`.

## The registry and the journal of the host are data (task 158, AL-113)

The language names two primitives, `time_now` and `new_id` (`language_registry()`), and 35 journal codes (`journal_language.md`, `language_journal()`; spec 7a): the codes of the format (5), of the fragment "Pause" (8), of the engine and of the executor (22). Everything else a host registers as data in two Markdown files beside its machines:

- `registry.md` (`parse_registry_table`): the table of the primitives `name | parameters | result | class | reads | writes` (spec 7; the names are the JSON names; a parameter is `name: type`, several are separated by `;`, `—` is none; the types are written as the tree `machine/2` writes them, `parse_spec`; a bar inside a cell is `\|`), and the tables of the types `type | kind | members` (`record`: `field: type; field: type`, `variant`: `Case; Case(field: type, field: type)`) under `## Types` or `## Types: <set>` (`host_types(data, set)`). The header cell tells the table (`name`/`имя`, `type`/`тип`); a table `primitive | role | result | reads` (the table by role) is an error since 2.24 (AL-131).
- `journal.md` (`parse_journal`): the table `Machine | Code | Russian template | Parameters` of the form of `journal_language.md`.

`host_registry(data, journal)` and `load_host(registry_text, journal_text)` join them with the language: a primitive or a code of the host that repeats one of the language, a name twice are errors (`registry.md:<line>: ...`, `journal.md: ...`), and the check of a table runs against the union. `without_journal(registry)` is the same registry with the codes not checked (the samples of the specification). The program `alula` reads the two files beside the file of its command (in the folder, for `test`) or from `--registry` and `--journal`. The hosts of this package: `examples/` (the example machines; `registry.md`: `close_agent_turn`; `journal.md`: 44 codes of the machines of the examples), `spec/samples/registry.md` (the 22 primitives of the pilots that the samples of the specification call, with the three parse functions by role). The registry of the methodology (54 primitives, the roles, the sets of the types) and the journals of the methodology (73 codes) and of the product (10) are the data of their owners (`machines/methodology/`, `machines/product/` of the CrewHarness repository).

## Alula 2.14 in the core (task 149)

The rules AL-38 ... AL-49 of the format 2.13 touch the core as follows (the translator is described in `src/machine_text/README.md`):

| What | Change |
|---|---|
| the tree (AL-38, AL-41) | a party has `signals` (`words` is refused by name), the event of a row of the kind `signal` (the kind `word` is refused), an enum has `values` (`words` is refused), the argument of the fragment is `halt_signal` (`halt_word` is refused); the model has `PartyDef.signals`, `EventPat.SignalEv`, `VariantDef.values`; the schema `machine-2.schema.json` says the same keys, its `$id` is the package `nova-alula`. |
| names (AL-46) | the checks of the tree take a constant, a parameter, a definition and a party of any identifier (they are internal names, written as they are), and only Latin names for a datum, a state, an id of a party, a type and a field (the names that leave the machine). |
| a call (AL-47, AL-48) | `check_nested`: `int` and `int>=n` fit each other in the fields of the input and of the result at any depth, two bounds fit only when equal; a field of the input of the type `?T` that the request does not give is `none`, the refusal `missing` is for a required field only. |
| a scenario (AL-38) | the step `word` is gone; the step `signal` has the optional `party` (the party that owns the signal; a party that did not declare the signal is a scenario error); the event kind `word` in a scenario is refused. The engine event is still `Input` and `Incoming.signal(...)` is its constructor (code, not format). |

## Run the tests (Windows, Nova Oracle 0.1.0)

```powershell
. C:/work/nova/nova-oracle-0.1.0-windows-x86_64/setup-env.ps1     # the leading dot matters
cd C:/work/alula
nova test src/machine                # the core: 170 tests
nova test src/machine_table          # the decoder and the checks: 85 tests
nova test src/machine_run            # the interpreter and the scenarios (the 83 of the agent step too): 164 tests
nova test src/machine_text           # the translator of Alula and its table of words: 199 tests
nova test src/machine_text_eq        # the proofs of the translator: 45 tests
nova test src/machine_agent          # the proofs of the agent step and of the sample of the methodology: 29 tests
nova test src/machine_text_fmt       # format 2.7 in the translator: 65 tests
nova test src/machine_text_lang      # the two languages of Alula, the news of 2.9 - 2.12: 83 tests
nova test src/machine_text_render    # the reverse generator JSON -> Alula and its circles: 49 tests
nova test src/machine_agent_en       # the English sample of the agent step (83 scenarios too): 14 tests (slow, about a minute)
nova test src/machine_nested         # the nested machines in the translator, the checks, the generator: 89 tests
nova test src/machine_nested_run     # the pairs "parent + nested machine", the protocol, the registry: 27 tests
nova test src/machine_nested_eq      # the agent step called by a session equals the agent step run alone: 6 tests
nova test src/machine_cycle          # the cycle check: the table, the rows of the methodology, the journal, the 101 scenarios: 48 tests (about a minute and a half)
nova test src/machine_session         # the session start: the table, the registry, the 55 scenarios with the agent step, the journal, the automaton of the methodology: 89 tests (about a minute and a half)
nova test --strict-effects src       # the same, and an effect used without being declared in a signature is an error
nova test src --jobs 4               # the whole package
```

Everything for Oracle 0.1.0 is in [`spikes/env/README.md`](../../spikes/env/README.md). `src/machine/` is ONE module, `alula.machine`; a module in a folder UNDER `src/machine/`
is refused by Oracle 0.1.0 (item 25 there), so the interpreter's units are sibling folders `src/machine_*`. The output of a unit must stay under 4 KB (item 20), hence the short names of the tests.

## Layout

| File | What it is |
|---|---|
| `value.nv` | `Value` (`Null`, `Bool`, `Int`, `Float`, `Text`, `List`, `Dict`, `Record`, `Variant`), builders, equality and order, `text(x)`, JSON both ways |
| `types.nv` | `TypeSpec`, `TypeDefs` (named records and variants), `check_value` with the path of the first mismatch |
| `expr.nv` | `Expr`, the tree of an expression, its JSON form (`expr_from_json`, `expr_to_json`), builders, `expr_depth` |
| `eval.nv` | `eval(expr, scope)`, `eval_with(expr, scope, host)`, `EvalError`, the protocol `PrimitiveHost` |
| `registry.nv` | `Primitive`, `Registry` (the primitives and the table of the codes of the journal; no table "by role" since 2.24), the class of a primitive in the position of a call, `language_registry()` (the two primitives of the language, `time_now` and `new_id`, and the 35 codes) and `without_journal` |
| `host.nv` | the registry and the journal of a host as data (task 158): `parse_registry_table` (`registry.md`), `host_registry`, `load_host`, `host_types`; the form of the files is in the section below |
| `spec.nv` | `parse_spec`: a type as the tree `machine/2` writes it (`int>=0`, `?text`, `[]Finding`, `"a" \| "b"`), the reverse of `spec_text` (it lived in `alula.machine_table` until 0.3.2) |
| `journal.nv`, `journal_language.md` | the codes of the journal that a machine may write (format 5 and 10, 2.12, AL-31; spec 7a, AL-113): the table of the language as data (35 codes), `parse_journal` for the table of a host, `language_journal()`, `journal_union(host)`, `journal_find`, `journal_table_issues(language, host)` (a code of a host that repeats a code of the language, a bad word, a code twice) |
| `data.nv` | the schemas `schema/` compiled in (`embed_str`), `schema_files()`, `data_dir_names("schema")`, `text_of_file`; the names: a machine in Alula is `*.alula.md` (or `.alula.txt`; `is_table_name` takes them), the compiled tree is `*.alula.json` (`is_machine_json_name`); the machines and the scenarios of the examples are embedded by `alula.examples` (since 0.4.0) |
| `*_test.nv` | 173 tests, more than 750 checks (the `assert` lines; loops repeat them) |

## The value

One sum type, no generics (Oracle 0.1.0 breaks the C of generic functions with inferred type arguments, items 12 and 13 of the survey): a typed list or a typed dict is a
`Value`, and the check against a type is `check_value`.

- `Dict` keeps its entries in the order of insertion (`keys` and `values` give the order of the first record of a key); its key is any value (text, int, enum value, tuple, record).
  Two dicts with the same entries in a different order are equal and have the same place in the order of values.
- `Record { name, fields }` keeps its fields sorted by name. A tuple is the anonymous record (name `""`) with the fields `0`, `1`, ... (`t.0`, `t.1`: from zero, as in Nova, format 2.3); `make_tuple`.
- `Variant { type_name, name, fields }` is a case of a sum type; an enum value is a case without fields (`enum_value`).
- Equality is structural, the order of values is total (null < bool < int < float < text < list < dict < record < variant). An int and a float are never equal.
- `text(x)`: an int is the decimal form; a float is the shortest decimal form that reads back, `1.0` and `0.0` for whole values, no exponent for
  1e-4 <= |x| < 1e16, else `1e-7`, `1.5e20`; an enum value is the word of its code (`StoppedByHuman` -> `stopped_by_human`); `none` for `Null`; `true`/`false`; a text
  is itself. A list, a dict, a record and a case with fields have no text. NaN and infinities have none.

JSON form, lossless (`value_to_json`, `value_json`, `value_from_json`, `parse_value`, written with `std.encoding.json`, UTF-8 as it is, 4-byte letters and surrogate escapes read):
null, bool, int, float (always with a fraction or an exponent: `1.0`), text and list are the JSON ones; a dict with text keys none of which starts with `$` is a JSON
object in the order of insertion; the rest is tagged with one `$` key: `{"$dict":[[k,v],...]}`, `{"$tuple":[a,b]}`, `{"$record":"Name","fields":{...}}`,
`{"$variant":"Type","name":"Case","fields":{...}}`, `{"$float":"NaN"}`. The reader refuses an unknown tag, an integer beyond `int`, a repeated key, a value deeper than 64.

## The tree of an expression

One JSON object per node, the key `op` (the full list with the keys is at the top of `expr.nv`): `lit`, `name`, `field`, `index`, `call` (a function or a list function of the language,
a `lambda` is an argument), `primitive_call`, `match`, `let`, `if`, `record`, `with_field` (a record with changed fields), `variant`, `list`, `tuple`, `dict`, the operators
`+ - * / % == != < <= > >= and or ??` (their symbols are the `op`), `not`, `neg`. The draft form of a lambda `{"lambda":["x"],"body":E}` is read too. A tree deeper than 64 is refused
by the reader and by the evaluator. An error of the reader is `{ path, message }` with the path in the tree (`$.args[1].body`).

## The evaluator

`eval(expr, scope) -> Result[Value, EvalError]` is a pure function: it reads its two arguments, writes nothing, has no effects in its signature (`nova test --strict-effects` is green) and gives the
same result on every run. The only door to the world is a primitive of the host: a `primitive_call` node goes to the `PrimitiveHost` that the caller passes to `eval_with`
(`eval` passes a host that refuses every primitive); the core does not know what a primitive does.

- Order: strict, left to right (the arguments of a call, the fields of a record, the items of a list). Lazy are `if`, `and`, `or`, `??` only: the part that is not needed is not evaluated.
- `match` is exhaustive: no arm accepts the value - `NoMatchArm`. An arm has alternatives (`A | B`), patterns `any`, a literal, a case (by name, and by type when given) that binds fields to names, and an optional guard
  (evaluated after a pattern accepted, with the bound names).
- Numbers: `+ - *` on two ints are checked (`Overflow`); `/` and `%` on ints truncate toward zero (decision: the format is silent), a zero divisor is `DivisionByZero`, `min / -1` is `Overflow`;
  floats `+ - * /`, a result that is not finite is `Overflow`, `/ 0.0` is `DivisionByZero`; an int and a float never mix (`float(x)`, `int(x)`); `<`, `<=`, `>`, `>=` take two ints or two floats.
  `+` also joins two texts and two lists (the left first). `==` and `!=` are structural on any two values.
- The index of a dict by an absent key and the index of a list out of its bounds are `none` (owner, 2026-10-19), not an error. A field of a record that is not there is `UnknownField`.
- Errors are values: `EvalError { kind, message, path }`, the kinds `TypeMismatch`, `UnknownName`, `UnknownField`, `UnknownFunction`, `BadArity`, `Overflow`, `DivisionByZero`, `NoMatchArm`, `Unreachable`,
  `DuplicateKey`, `LambdaMisplaced`, `TooDeep`, `OutOfBudget`, `PrimitiveFailed`; the path is the place in the tree (`$.args[1].body.left`). `Unreachable` is the DEFECT of the format (`require(none)`):
  the executor stops, it is not a machine error with an ERROR end.
- Totality: the language has no loops and no recursion; a list function walks a finite list. A run is bounded all the same: the depth of a tree (`MAX_EXPR_DEPTH` 64), the number of nodes evaluated
  (`MAX_STEPS` 50000) and the length of a list built by `range`, `+` (`MAX_ITEMS` 10000) - `TooDeep`, `OutOfBudget`.

List functions and functions (the `fn` of a `call` node; the catalog of the format, section 12; every one is pure):

| Name | Meaning |
|---|---|
| `filter(list, x -> bool)`, `map(list, x -> v)` | the items that pass; the list of results |
| `any`, `all` | with a predicate; stop at the first item that decides; `false` and `true` on the empty list |
| `count(list, x -> bool)`, `first_where(list, x -> bool)` | the number of items that pass; the first one or `none` |
| `fold(list, start, (acc, x) -> v)` | from the left; the start on the empty list |
| `dict(list, x -> key, x -> value)` | a dict from a list; a repeated key is `DuplicateKey` |
| `range(a, b)` | `[a, b)`, empty when `b <= a`; longer than `MAX_ITEMS` is `OutOfBudget` |
| `keys(dict)`, `values(dict)` | in the order of the first record of a key |
| `length(x)` | the items of a list or a dict; a text is `TypeMismatch` (format 2.23: `length` is for a list and a dict only, a text has no length in the language) |
| `has(x)`, `require(x)` | `x` is not `none`; the value, or the defect `Unreachable` on `none` |
| `remove(list, item)` | the list without ALL items equal to `item` (owner, 2026-10-19) |
| `without_key(dict, key)` | the dict without the key (an absent key: the same dict) |
| `text(x)`, `float(n)`, `int(f)` | `text(x)` as above; the conversions are explicit, `int` cuts the fraction toward zero, outside the range of `int` is `Overflow` |
| `max(a, b)`, `min(a, b)` | two ints or two floats |
| `journal_event(code, name, text, ...)` | the record `JournalEvent { code, params }`, `params` a list of tuples (name, text) |

Task 107 added to the evaluator: `eval_defs(expr, scope, table, host)` with a `DefTable { fns, types, globals, registry, checked }` - the definitions of a machine (`DefFn`: typed parameters, a typed result, a body that sees its parameters and the globals only, never the names of the caller), and, when `checked` is true, the check of the arguments and the result of every primitive call against the registry; the catalog got `record_text(e)` (`event <code>` or `event <code>: name=value, ...`, format 2.2) and `require_non_empty(x)` (a text that is not `""`, else the defect `Unreachable`).

Not here (the interpreter's, `src/machine_run`): `конец(state)` of the catalog (it needs the states of a machine), the names of the executor (`вход`, `событие`, `состояние`, ...), the actions (`поле = выр`, `журнал`, `для каждого`),
the check "an `if` does not nest in the branch of another `if`", the sets of values of a closed text (3.2 of the format).

## The types

`TypeSpec`: `IntType`, `IntMin(n)` (`int>=n`), `FloatType`, `TextType`, `TextSet(words)` (the set of literals `"a" | "b"`, two or more; format 2.5), `IdType` (`id`, a text of the form 8-4-4-4-12 lower case hexadecimal digits, format 2.5), `BoolType`, `NothingType` (the type of "no result", the value is `none`), `OptionalType(T)` (`?T`:
`none` or a `T`, which is the lifting of `T` to `?T`), `ListType(T)`, `DictType { key, value }`, `FullDictType { key, value }` (the key is an enum and every one of its values is a key),
`TupleType(items)`, `RecordType(name)`, `VariantType(name)`. The named types are declared in `TypeDefs`. `check_value(spec, value, defs)` gives the first mismatch with a path
(`$.findings[2].severity`, `$["key"][1]`, `$.1` for a tuple field); a record or a case needs every declared field and no other.

## The registry of the primitives of the host

`Primitive { name, params: []ParamSpec, result: TypeSpec, class, reads, writes }`; `class` is `Pure`, `Volatile` or `Acting` (the owner, 2026-10-25, through the methodology, AL-116: before there were four, `Reading`, `Writing` and `Irreversible`; a function of the author has no class, it is always pure). `register` refuses an empty name, a second primitive of a name, a repeated
parameter name, and a pure primitive with a non-empty `reads` or `writes` (a pure primitive reads its arguments only; the loader of `registry.md` refuses it with the line). `check_call_position(registry, name, position)` and `check_expr_positions(registry, tree, position)` (it walks a tree and gives the path of the first call that does not fit) say whether the class is
allowed in the place (section 7 of the format):

| Class | Where a call may stand |
|---|---|
| `Pure` | everywhere |
| `Volatile` (the result depends on the world: the clock, a file, a store) | `InputPos` (the table "Input" of an appeal), `ProfilePos`, `ForkEntryPos`, `OperationEntryPos`, `EndEntryPos`, `AcceptPos`, `ActionPos` (the actions of the chosen row run once); not in a condition (`ConditionPos`) |
| `Acting` (changes the world) | `OperationEntryPos`, `EndEntryPos`, `ActionPos`; not in a condition, not in "Input", not in the profile, not in "On entry" of a fork, not in "On accept" (the expressions of the actions of a block have the position of the block, so `x = acting(...)` in "On accept" is refused too) |

An acting primitive without a result is not a value: its call is an action, and `check_expr_positions` refuses it in an expression and on the right of a binding (the message names the primitive and the class). A volatile call as an action with no binding has no effect, `check_call_actions` refuses it.

An honest retreat from the format (section 5: an acting call is the last stage of a commit): an acting function is called at once, in its place in the actions, BEFORE the step is written (the `PrimitiveHost` is called from the action, `machine_run/step.nv`). Repeatability without harm is a requirement to the host. A step that fails after such a call is rolled back, and the call has been made. A queue run after the step is written is built when a real host with files and processes appears, or at the first case of a double call.

`check_call_args` and `check_call_result` check the count and the types of the arguments and the type of the result of a call against the signature. `reads` and `writes` name what a primitive reads or writes without an
argument (rule 11 of the specification): they join the "Input" of the state of the call.

The registry of the pilots (23 primitives of the meeting and of the agent step: the name, the types and the class are the methodology's, the body is the host's) was `standard_registry()` until 0.3.2; since 0.4.0 it is data: the 22 primitives that the samples of the specification need are `spec/samples/registry.md`, all 54 of the methodology are `machines/methodology/registry.md` in the CrewHarness repository (section "The registry and the journal of the host are data").

| Primitive | Parameters | Result | Class |
|---|---|---|---|
| `party_profile` | `party: text` | `AgentProfile` | volatile |
| `role_context` | `context: RoleContext` | `text` | volatile |
| `call_trace` | - | `text` | volatile |
| `call_step` | - | `int>=0` | volatile |
| `parse_witness_reply` | `reply: AgentReply` | `[]WitnessAnswer` | volatile |
| `parse_author_reply` | `reply: AgentReply` | `EditResult` | volatile |
| `parse_lens_reply` | `reply: AgentReply` | `LensResult` | volatile |
| `proposal_read` | - | `bool` | volatile |
| `proposal_with_fingerprint` | - | `text` | volatile |
| `proposal_changed_since_attempt` | - | `bool` | volatile |
| `count_in_model_tally` | `finding: Finding` | nothing | acting |
| `journal_findings` | `findings: []Finding` | nothing | acting |
| `journal_machine_data` | - | nothing | acting |
| `journal_decision` | `decision: text, source: text, passes: int>=0, open: []Finding` | nothing | acting |
| `remove_unsound` | `number: int>=0` | nothing | acting |
| `build_summary` | `number: int>=0` | `?Summary` | acting |
| `close_for_writing` | `object: text` | nothing | acting |
| `open_for_writing` | `object: text` | nothing | acting |
| `move_to_archive` | `number: int>=0, suffix: int>=0` | nothing | acting |
| `time_now` | - | `int` | volatile |
| `new_id` | - | `id` | volatile |
| `reply_validation` | - | `ReplyCheck` | volatile |
| `close_agent_turn` | - | nothing | acting |
| `check_cache` | `dialog_kind: "main" \| "delivery"` | nothing | acting |
| `stop_agent_group` | - | nothing | acting |

The first 17 are the 17 functions of the meeting that its markup (`functions-markup.md`) makes primitives of the host: 8 volatile, 9 acting (6 writing and 3 irreversible before AL-116); the next four are the agent step (`check_cache` is the
check of the cache that the specification of the step puts after every accepted result of a turn; the pilot's code does not have it); the last is the one primitive of the cycle check (task 122): `stop_agent_group`, the group
of processes of the agent is stopped as a whole when the check ends in HALTED or ERRORED. No pure primitive: `fingerprint` stays inside `proposal_with_fingerprint`.

## Decisions where the format is silent

- Division and remainder of ints truncate toward zero (the sign of the remainder is the sign of the dividend), as C and Nova do.
- `<`, `<=`, `>`, `>=` take numbers only (the format says so); `==` of an int and a float is `false`, not an error (the check of the table would refuse it earlier).
- Missing optional fields of a record are not allowed in `check_value`: every declared field is there (`none` for an absent `?T`).
- A repeated key in a dict literal and in `dict(...)` is `DuplicateKey` (the format says so for `dict`); `make_dict` (the Nova API) keeps the place of the first record and takes the last value, like `d[k] = v`.
- A field of a variant is read only through `match`; `x.f` needs a record.
- Order of text: `value_compare` compares texts by bytes (UTF-8), which is the order of code points.

## Oracle 0.1.0: limits met and the ways round them

<!-- ORACLE-WORKAROUND(25, 20): the interpreter and its proofs are sibling folders (`src/machine`, `src/machine_table`, `src/machine_run`, `src/machine_dialog`, `src/machine_agent`, ...), one module and one unit each: a module in a folder under a module's folder is refused (25) and the output of a unit must stay under 4 KB (20), so the tests have short names and a big proof is a unit of its own; one module tree and units of any size would do when items 25 and 20 are fixed -->

The rules of the language that cost a compile and the three new defects (items 33-35, with reproductions in `spikes/env/repro_engine/`) are in the survey README. What shaped this code:

- No generics with inferred arguments, no protocols with type parameters: `Value`, `Expr`, `TypeSpec` are plain sum types; the door to the host is the protocol `PrimitiveHost` without parameters, passed as `mut host PrimitiveHost` (as the engine passes `Environment`).
- An `Option[Expr]` field in a record declared before the enum breaks the C (item 34): the guard of an arm is a list of zero or one expression.
- `for x in [A, B]` over an enum literal list breaks the codegen (item 33): the tests take the list from a function.
- One folder is one module and one unit (item 25): the tests carry short names so that the output of the unit stays under 4 KB (item 20).

# The interpreter of a machine that is data (task 107)

`src/machine_table/` reads and checks a machine, `src/machine_run/` runs it. A machine is ONE JSON file, `format: "machine/2"`; the interpreter gives the protocol
`Machine[AlulaState]` of the engine, so `start_engine[AlulaState, AlulaMachine](machine, id)` runs it with the journal, the snapshots and the link of the product,
and a restart resumes it. The examples are `machines/*.alula.json` (chat, calc, actions, gate, lenses, variants), their scenarios `scenarios/*.scenario.test.json`.

## The file `machine/2`

The keys are English, the structure is the format 2.5 of the methodology (sections 1-9, 12, 13) in a tree; the JSON Schema is
[`schema/machine-2.schema.json`](schema/machine-2.schema.json), the reference is the decoder `src/machine_table/json.nv` (a key the schema does not know is refused; a test compares the
key lists and the kinds of the schema with the decoder's). Expressions are the trees of the core (`{"op":"name","name":"x"}`, `{"op":"+","left":E,"right":E}`, see the top of `expr.nv`);
the types are written as the format writes them (`int>=0`, `?text`, `[]Finding`, `{text: int}`, `"a" | "b"` (under `?` and `[]` in parentheses, `?("a" | "b")`), `id`, `full {K: V}`, `(text, int)`).

| Key of the root | Meaning (format section) |
|---|---|
| `format`, `machine`, `version`, `title` | the header: `machine/2`, the Latin name (the name in the journal), the version |
| `types` | `records`, `variants` (an enum is a variant without fields; the key `values` of a variant is the list of the pairs `["Name", "value"]` of its values, formats 2.7 and 2.13 (AL-41; `words` before, refused by name)); `FailCode`, the closed list of the ten failure causes, is built in (2) |
| `constants`, `params` | `name`, `type`, `value` / `default` (+ `project_key`: the key after `проект.` of the column "project override", format 2.7); evaluated in order when the machine is built (1, 8) |
| `input` | `fields`, `invariants` - the input of a call; the event `start` carries it as an object (1) |
| `data` | `name`, `type`, `initial` (`{"expr": E}` or `{"from_input": "field"}`), `monotonic` (`true`, or `{"bound": E}` for `<= E`), `writes` (`rows`, `mechanics`, `rows_and_mechanics`, `fragment`, `rows_and_fragment`); a name `x[*].f` is a path datum that carries only the marks (2) |
| `parties` | `name`, `id`, `kind` (`agent`, `human`, `enhanced`, `gatekeeper`, `machine`), `signals` (the signals of the party: `name`, `fields`; `words` before, AL-38, refused by name), `progress` (parts of an answer), `result` (the type of the answer, required for agent and machine), `counter` (the datum of the attempt counter, required), `profile`, `setting`, `nested` (1) |
| `signals` | signals of the machine that belong to no party (stop, cancel) (4.3 `signal`) |
| `definitions`, `includes` | pure functions `name(params) -> result = body`; the lines `definitions: <name> version <N> hash <hex12>` (8) |
| `initial`, `error_end` | the initial state; the end ERROR (A4) |
| `common_events` | the rows of signals tried before the rows of a state - the fragment "Pause", expanded in the tree (9) |
| `states` | the states (4) |
| `ends` | `result` and the rows `{state, n, when, answer}`, `answer` is `{"kind":"answer","value":E}` or `{"kind":"refusal","code":E,"text":E}` (4.7) |
| `primitives` | the primitives of the host that the machine calls (7) |

A state: `name`, `kind` (`appeal`, `operation`, `fork`, `end`), `reads` (the line `Input:`), `reads_all` (the end ERROR), and by kind:
an appeal - `party`, `inputs` (the table "Input": `{field, value, reads: party|executor}`), `silence` (the term, ms), `set` (a list of party ids: a request to each), `accept` ("On accept"), `rows`;
an operation / a fork - `entry` ("On entry": `bind` and `call`), `rows` (`{"kind":"now"}`; a fork row may have `cond` or `else`);
an end - `entry` (actions with the journal), `except` (`{field, values}` of the format's "Except").
A row: `n`, `event`, `cond`, `else`, `actions`, `to` (a state, `@previous`, `@same`, `@prepare_return`; absent when the actions end in `machine_error`), `restart`.
An event: `answer` (`bind`), `answer_variant` (`variant`, `bind` {field: name}), `failure` (`reasons`, `bind`), `timeout`, `progress` (`name`, `bind`), `signal` (`name`, `bind`: the signal of a party that the party of the appeal declares, or a signal of the machine; the kind `word` of 2.12 is refused by name, AL-38), `now`.
An action (`do`): `assign`, `add` (`+=`), `journal` (`code`, `params`), `journal_value`, `journal_all`, `for_each`, `let`, `bind`, `if`, `call`, `machine_error`, `cancel_open`, `pass`;
the target of `assign` and `add` is a datum or `{"name": "x", "path": [{"key": E}, {"field": "f"}]}` (`x[key].f = v` is one path).

## The checks of a table (`check_machine`, format section 10)

`load_machine(text, registry)` decodes and checks; `check_machine(def, registry)` gives every issue as `<path in the JSON>: <message>`, in a fixed order. Checked: the names (Latin, unique, no shadowing of
a datum, a constant or a parameter by a binding); the shape of each kind of a state; the events against the signals and progress of the party, the cases of the result variant, the `FailCode` cases;
the targets; **the reads against the "Input" of the state (rule 11)** - every datum an expression reads is in the Input table of the appeal or the `reads` line of the state, and so are the hidden reads of a primitive
(`reads` in the registry); `input`, `all_data`, `transition_note`, `trace`/`step` only where they are defined; **the writes against the data** (a root that is not a datum, a datum whose `writes` is not rows,
a path with `writes: mechanics`); the entry of a state changes no data (rule 29); **the class of every primitive in the place of its call** (`check_expr_positions`), a primitive that is not registered or not listed in `primitives`;
**the reachability of the states** (a return to `@previous` reaches every appeal); **the exhaustiveness of the ends** (a row with `when: true`, or a chain of `field == "..."` that covers the closed set of the datum minus `except`; no overlap);
the definitions (no recursion, no catalog name, the number of arguments); an `if` does not nest in a branch of another `if`; the journal codes and parameters are lower case Latin; the includes (a 12-digit hash); the counters of the parties; the set is the datum `to_send`.

## The interpreter

`alula_step(machine, state, event, environment, host)` is the whole `step` (`Machine[AlulaState].step` calls it with the default `ScriptedHost`). It reads its arguments only; the clock is the stamp of the event (`time_now` of the default
host), any other primitive goes to the `PrimitiveHost` that is passed in. The state is `AlulaState { name, started, input, data }` - values of the core, written as one JSON object under `state` of the snapshot.

The order of a step: the event of the engine is read as the event of the machine (`Input` - a signal by name, with the fields decoded from `input`: one field is the text itself or a number or a JSON value by its type, several fields are a JSON object;
`Progress` - a part of an answer; `Answered` - the answer, its type is the `result` of the party of the appeal (a text, or a JSON value of the core); `Refused` - a failure with the case of `FailCode`; `Expired` - the term). A name no party and no signal knows is the journal event
`event_unknown`, a text that does not fit the fields is `event_malformed`. Then the common events, then (for an answer, a failure, a timeout) "On accept", then the first row of the state that fits (pattern, then `cond`); a failure that no row names is read as `NoResult`
(format 4.3); no row: `event_ignored` (`event`, `state`). The actions run in the order of writing and each sees the results of the previous; every write is checked against the type of the datum (a violation is a machine error `bound_violation`). The chain goes on through
operations and forks to an appeal (it orders `SendOrder` to the party - to each id of the `set`, and the datum `to_send` is emptied - with the text of its one field, or the JSON of the fields, and the term of `silence`) or to an end (it orders `Conclusion` by the first row of the table
"Ends"; a value that is not a text is written as JSON). After the chain `monotonic` and its bound are checked, and a snapshot is ordered when a row was taken (the convention of the MVP of the engine).

- **Start.** A machine with an `input` section, or whose initial state would order something, waits for the event `start` (a signal named `start`, its input is the object of the input; `input_rejected` with `reason` `json`, `missing`, `type` or `invariant` finishes it with `NoResult`). A machine whose initial state is
  an appeal to a gate is started at once. Events before the start are `event_ignored`.
- **Machine errors** (an overflow, a division by zero, a repeated key, a missing key, a list index, a bound): the event `machine_error` with `reason` (or the event of the `machine_error` action, or `fork_no_match` with `fork`), then the end `error_end` (its entry runs with `transition_note` defined, then the table "Ends"); without an `error_end` the machine finishes with `NoResult`.
  A **defect** (`require(none)`, `require_non_empty("")`, a type that the checks would have refused, a primitive that fails): `machine_defect`, the machine finishes with `NoResult`, the state stays as it was, and only those two orders are given.
- **Orders** are collected and given to the environment at the end of the step, in the order of giving: journal events, `order_send`, `order_cancel` (the action `cancel_open`), `order_finish`, then `order_save`.
- **Determinism.** The step is a pure function of the state and the event; two runs give the same journal and data (tested on every scenario).

## Scenarios (`scenario/0`)

A scenario is a file of data - events and what they must leave ([`schema/scenario-0.schema.json`](schema/scenario-0.schema.json); the top of `src/machine_run/scenario.nv` has an example). `parse_scenario(text)` reads it, `run_scenario(machine, scenario)` runs it on the
engine of the product over the in-memory handlers and compares after every step the name of the state, the structural journal (code and parameters of the lines the MACHINE wrote), a subset of the data, the queue, the open requests, the requests sent and cancelled, the outcome;
a part the file does not name is not compared. `report_text(run)` is empty for a run that agrees, else the name and one line per difference: `step 2 (feed): state: expected Failed, got Awaiting`. `drive_scenario[S, M](machine, scenario)` runs any `Machine[S]` (the Nova chat machine too) and gives
the traces, which is how the equality below is proved. The operations of a step: `feed`, `accept` (the process dies before the send), `dispatch`, `pump`, `deliver`, `advance`, `restart`.

## The chat machine as data and the proof of equality

`machines/chat.alula.json` is the machine of `src/chat/chat.nv` of the CrewHarness product (Idle, Awaiting, Done, Failed; the signals `user_message`, `cancel`; the part `agent_chunk`; the answer, the failure, the term) written by hand. `src/machine_chat/equal_test.nv` runs the SAME scenarios on both machines -
the 39 files `scenarios/chat-*.scenario.test.json`, which reproduce every case of `chat_test.nv` and `chat_engine_test.nv` (the ten failure codes and an unknown one, the cancel in both states, the term, ignored and unknown events, tool and permission parts, Cyrillic, the discarded replies, the pump, the three restarts, the
acknowledgement of the source key, the cancel in the window between the commit and the send) - and compares at the level of the engine, step by step: the name of the state, the data both machines hold, the events of the machine, ALL journal lines with the envelope (trace, step, cause, state, request, time), the open, sent and cancelled
requests, the queue, the acknowledged keys, the outcome and the number of the step; and at the level of the machine (one `step`, no engine): the orders in order (journal event with parameters, send, cancel, finish with the text, save), the transition (`Go`/`Stay`) and the data. A deliberate change in the JSON machine turns the tests red (checked).
The data view is the one both can show: `Awaiting` the message and the reply, `Done` the reply, `Failed` the code (the table machine keeps the rest too).

## Decisions where the format is silent or the engine differs

- **Events.** The format has `answer`, `failure(reason)`, `signal` (since 2.13 the word of a party is its signal, AL-38). The engine of the product also has parts of an answer that keep the request open (`Progress`) and a term made by the executor (`Expired`); both are events of the JSON (`progress`, `timeout`) and a failure row names the refusals of the party only. A
  signal is the same `Input` event by name (the engine event is still called `Input`, `Incoming.signal(...)` is its constructor in the code): a signal of a party is declared by the party of the appeal, a signal of the machine in `signals`; a signal may stand in the rows of any appeal (the format keeps signals for the common events and the pause).
- **Events that no row takes**: `event_ignored` / `event_unknown` / `event_malformed` are written by the interpreter itself (the format: "the executor discards and journals, rule 17"); the label of an ignored event is its name.
- **Request text**: a request with one field of text is that text, with none is empty, else the JSON of a record of the fields. The identifier of a request is the engine's `<party id>-<attempt>`; the party of an answer is the id without the attempt.
- **`order_save`** is ordered after a step that took a row (the chat machine on Nova does it at every state change; the engine saves a snapshot at every commit anyway).
- **A step that fails**: no rollback of the writes made before the error (the format: the ERROR end sees the data as they are); only a defect leaves the state as it was.
- **Enum values** (format 2.7, P-7; the key `values` since 2.13, AL-41): `text(x)` of an enum value is its value from the key `values` of the type; a value without a word is the code word of the case (`StoppedByHuman` - `stopped_by_human`, as before; `FailCode` has the words of the engine). `all_data` is written by section 5 of the format (below, task 110).
- **`record_text`** (`text_of_record` of the format) writes the English prefix `event `.

## Not implemented (and why)

- The last stage of a commit for an acting call (section 5, rule 13): the call is made at once, before the step is written; the queue after the write is built when a real host with files and processes appears or at the first case of a double call (see "The registry of the primitives of the host").
- `@prepare_return` (rule 24: the preparation is the executor's) - refused by the checks.
- An acting primitive that changes data of the machine (`writes` in the registry): `PrimitiveHost` gives back a value only.
- `includes` are checked for shape (name, version, 12-digit hash); the file of definitions is not read; a fragment is the expanded tree.
- The qualified `answer: Type.Variant`.
- Nested machines (task 119, section below): (task 123: the answers that come while the machine is on pause are held, rule 14, and the pair runner is recursive); the result table "by role" of a party is gone since 2.24 (one function per role); the modes `nothing` / `no_return` of a nested call are not told apart; a machine has ONE party of a set; a hand-written Nova machine cannot be nested (only a machine that is data); the hub does not run a nested machine on the server (the memory runner `alula test` does).

## Oracle 0.1.0: more limits met in task 107

The rules that cost a compile and the four reproductions (items 36-39, `spikes/env/repro_engine/src/`) are in the survey README. What shaped this code: a type of the program has a global name (`Next`, `Reading`, `Slot`, `Pair` clash with the standard library, with a case of another enum or with a record of another
module - the records here are `Goto`, `EventRead`, `ReqField`); `embed_str` reads a file relative to the source; a variable named `b` of a list type can leak into the prelude; a record literal after `=>` of its own type is a "redundant type prefix"; a mutable copy of a field of a `ro` parameter is `E_READONLY_COERCE` (the chain of a step is a recursion over `ro` values).

# Format 2.5 and the translator (task 108)

Task 108 (`doc/tasks/108-table-translator/`) brought the interpreter from the format 2.2 of task 107 to **2.5** and wrote the translator of the tables in Russian ([`src/machine_text/`](../machine_text/README.md)). What changed here:

- **A set of literals** `"a" | "b"` replaces `text from {"a", "b"}` (2.5, T-1): two values or more, under `?` and `[]` in parentheses (`?("a" | "b")`); `spec_text` and `parse_spec` follow; a literal outside the set assigned
  to a datum, or an initial value outside it, is an issue of the table; at run time every write is checked against the type (`bound_violation`).
- **`id`** (`IdType`, 2.5, T-2): a text 8-4-4-4-12 of lower case hexadecimal digits (`is_uuid`); checked in `check_value`, so also for a datum, a signal, the input of the machine (`input_rejected`, `reason=type`) and the arguments of a primitive.
- **`new_id`** (volatile, no parameters, result `id`), in `language_registry()` (since 0.4.0; before in `standard_registry()`). The check of the table: it may stand only in a binding of the entry of an operation and the binding must be written to the data by a row of that state.
  `ScriptedHost` answers it with `Uuid.v7()` under `with Time = th.fixed_ms(at), Random = th.seeded(...)` (the stamp of the event and the number of the call in the step): the same step gives the same ids; a scripted reply of the host wins.
  The host of the product that wants real random ids is another `PrimitiveHost`.
- **Tuple fields from zero** (2.3): `t.0`, `t.1`; `make_tuple` names them `0`, `1`, ...; the lossless JSON `{"$tuple": [...]}` is the same.
- The root key **`alula_version`** (optional, `"2.17"` only since task 151; absent means 2.17; the version of the language Alula that the tree follows; task 113 renamed the key from `table_format`, the old name is a key the schema does not know and the loader refuses it). The built-in record **`JournalEvent`** (`СобытиеЖурнала`, section 2) beside `FailCode`. The name of an included file of definitions is a name of the registry (any letters, not a path).
- **Common events (the fragment "Pause", section 9)** read the data of a fragment (the marks `fragment`, `rows_and_fragment`, `mechanics`) without an Input and write the data with the marks `fragment` and `rows_and_fragment`.
- The record `Child` of `expr.nv` is `ExprChild` (item 40 of the survey of Oracle 0.1.0: a program with `import std.os` could not be built).
- `machines/chat.alula.md` is the chat machine in Alula (as tables); its translation equals `chat.alula.json` (a test compares the trees without `title` and `alula_version`) and runs the 39 scenarios of the chat in the same way.
- `machines/dialog.alula.md` (task 114) is the MANY-turn chat in Alula 2.12 (`Idle`, `Awaiting`, the end `Closed`; after an answer, a refusal, a term and a cancel the session returns to `Idle`); its translation `dialog.alula.json` is what the session server runs (`src/server`, [README](https://github.com/unitcraft/crew-harness/blob/main/src/server/README.md)). The idle term is the parameter `IDLE_TERM` with the key of the project `проект.срок_бездействия` (`load_alula_machine_with` of `src/machine_run` takes the table of the project). Its 37 scenarios are `scenarios/dialog-*` (28 moved from the chat scenarios, 8 new, 1 for the way only the table has: the signal `close_session`; the generator is `doc/tasks/114-*/tools/gen_dialog_scenarios.py`); `src/machine_dialog` takes every row of the table by a scenario, `src/machine_dialog_eq` runs them on the machine in Nova (`dialog_session`) and on this one and compares everything. Since task 126 the signal `отмена` is declared once, as a signal of the machine (it is no more a signal of the party `пользователь`; the scenario `dialog-cancel-idle` gives the signal), and the field of the signals `сообщение_пользователя` and `кусок_ответа` of the dialog and of the chat is `содержание` (`content` in the tree); `AlulaMachine.accepts_signal(state, name)` (`src/machine_run/accepts.nv`) answers "does the state take this signal?" for the hub, which therefore names no state of the table. The dictionary of the signals between the table and the code is in the [README of the server](https://github.com/unitcraft/crew-harness/blob/main/src/server/README.md), "The border of the table and the code".
- `data.nv`: `table_files()`, `chat_table_text()`; `data_dir_names("tables")`.

# The agent step as data (task 109)

`machines/agent_step.alula.txt` (since task 110 with the extension `.txt`, as the copy of the sample: its prose has the relative links of the folder of the methodology and the guard of the links reads `.md` only) is the machine "Agent step" of the methodology in Alula (as tables, format 2.6, the key lines are list items, the fragment "Pause" is a connection); `machines/agent_step.alula.json`
is its translation by the program `alula` (`alula compile`, `src/alula.nv`; a test compares them byte by byte). It passes the checks of the load without a note `unsupported`: 14 states (37 rows of the states, 4 of the pause,
6 common events), 13 rows of the ends, 16 definitions, 3 parties, 21 data. The machine is run by the same interpreter as the chat; the user writes no Nova.

What the interpreter got for it (decisions are in `doc/tasks/109-agent-step-machine/analysis.md`):

- **`Предел запросов` (`request_limit`)**: the value is evaluated at the build (an int, at least 1; `AlulaMachine.limit`, 0 when the line is not written). An appeal that would pass the limit of the requests that
  the machine holds open is a defect `request_limit`. A machine with a limit and a set of parties is refused at the build (the counters of the elements are the engine's).
- **The mechanics of the contract** (rules 14, 15, 18, 21): the counter of the attempts of a party (`counter`, a plain datum) grows at every send, the request id is `<id>-<counter>`; the datum `open_requests` gets the id
  when the request is sent and loses it at the outcome (answer, failure, term), at a cancel and at an end; the datum `call_request_id` is the request that started the machine (the field `request` of the event `start`).
  A machine that has not got these data does not get them (the chat machine is as it was). Requests to a human (a gate) do not exist in the engine: a gate waits for a signal, so `open_requests` holds the requests to agents.
- **`отменить_открытые`** (`cancel_open`) cancels the open requests of the datum `open_requests`: all, or those of the named party; a machine without the datum cancels the request of the party of the state as before.
- **A term that passed** is read as the failure `Timeout` by an appeal whose rows do not name the term (the event `timeout`): the failure rows of the format (`сбой(причина ∈ {…НетОтветаВСрок…})`) take it (format 4.3, rule 16).
- **The mark `taken`** of `AlulaState`: the rows the last step took (`State#n`, `common#n`, `end:State#n`); it is the proof of the coverage of the rows by the scenarios, not data of the machine.
- **Scenarios**: the step key `host` (the answers of the primitives of the host from this step on, in the lossless JSON of the core: `reply_validation`, `close_agent_turn`), the file key `params` (the values of the parameters
  of the machine that the project gives, `alula_machine_with`), the field `request` of the event `start`. `scenarios/agent-step-*` are 83 files (75 + the 8 of task 125, a start without one of the eight fields of the request): a scenario for every row that can be taken (`agent-step-<state>-<n>`,
  `agent-step-common-<n>`, `agent-step-end-<end>-<n>`) and the flows (`agent-step-flow-*`). Seven rows cannot be taken by any events (the rows `else` of the forks and the row 6 of the common events); the test names them.
- Not run at task 109 (still `unsupported`): the profile of a party, `Возвратов формы` above zero, `Правит`, nested machines, `вход_заново: запросы_из_к_отправке`. Task 119 runs all of them (section "Nested machines" below).

# Format 2.7 (task 110)

Task 110 (`doc/tasks/110-format-27/`) brought the tree, the interpreter and the translator to format 2.7 of the methodology (marks P-1...P-9 of section 0 of the changelog of the format). The sample of the agent step of the methodology
(`spec/samples/agent-step.alula.md`, 2.7) is translated whole and with no hand edit; the table of the product (`machines/agent_step.alula.txt`) is that sample with the two keys of the project in the column "project override".

- **The tree.** `alula_version` may be `2.7`. A variant that is an enum has the optional key **`values`** (it was `words` before 2.13), the list of the pairs `["Name", "word"]` in the order of the declaration (only the values that have a word; a
  word is lower case Latin letters, digits and `_`, once in the enum, the case has no fields): `VariantDef.values` (`EnumValue { name, value }`). The schema [`machine-2.schema.json`](schema/machine-2.schema.json) and
  a test of the unit `machine_table` say the same keys. `text(x)` takes the value (`enum_word(defs, type, case)`); the core `value_text` does not know the types and stays as it was.
- **`все_данные`** (`журнал(все_данные)`, the event `machine_data` with the one parameter `data`, section 5 of the format): `name=value; ...` in the order of the table of data (the data of the fragments first, the paths
  `x[*].f` are not among them). An integer is decimal, a float is `text(x)`, a text and a set of literals are as they are (an empty one is nothing after `=`), a bool is `yes`/`no`, an absent optional value is `none`, an enum value
  is its WORD (without a word - the name of the value as the tree has it, `FailCode` - the word of the engine). A list, a dict, a record, a variant with fields and a tuple are compact JSON (`src/machine_run/encode.nv`:
  no spaces, UTF-8, the quote, the backslash and the control signs escaped by RFC 8259 with lower case `\u00xx`): `none` is `null`, a bool is `true`/`false`, a record is an object with the fields in the order of its type,
  a variant with fields is `{"Name":{fields}}`, an enum value and a variant without fields are a string, a dict is an object (text keys) or the array of the pairs `[[key,value],...]`, a tuple is an array.
- **The table of the project (P-9).** `alula_machine_with(def, registry, params)` takes `[]ProjectValue { key, value }`: the key is `проект.<ключ>` (`PROJECT_PREFIX`), `<ключ>` is the `project_key` of a parameter
  (the column "project override"). A key that has no such parameter, a key twice, a key not of the form `проект.…` refuse the machine (`Err` before anything is evaluated); the value is checked against the type of the
  parameter like a default (a full dict by the rules of section 2); a parameter that is not named keeps its default. `alula_machine(def, registry)` is `alula_machine_with(def, registry, [])`. A scenario (`scenario/0`)
  carries the same table as `params` (`"params": {"проект.политика_разрешений": {...}}`); a key of another form is a mistake of the file.
- **P-8, the data of an event of a scenario.** A signal with ONE field has the value of the field as the `input` (a text: `"ivan"`, `"other-1"`), with several fields an object `{field: value}`, with none no `input`
  (it was so since task 109; the schema `scenario/0` and tests of the unit `machine_run` say it).
- **Names by the dictionary.** The field `идентификатор_запроса` of a signal is `id` (it was `request_id`, which is not a name of the dictionary); the datum `call_request_id` of the mechanics is the dictionary's `запрос_вызова`.
- Tests of the task: `nova test src/machine_table` (85 tests), `src/machine_run` (111), `src/machine_agent` (29), `src/machine_text_fmt` (65).

# Alula 2.11, two languages, the reverse generator (task 113; the version is 2.14 since task 148, see the end of this file)

Task 113 (`doc/tasks/113-*/`). The names: the interpreter is `AlulaMachine` (`AlulaState`, `alula_machine`, `alula_machine_with`, `load_alula_machine`, `alula_step`; they were `TableMachine`, `TableState`,
`table_machine`, `table_machine_with`, `load_table_machine`, `table_step`). The key of the tree is `alula_version` with the value `2.14` only (the decoder has `alula_versions()`; the old `table_format` is refused as an unknown key). There is no
transitional period for the former names of the files (Alula 2.11, AL-22): `is_table_name` takes `*.alula.md` and `*.alula.txt`, `is_machine_json_name` takes `*.alula.json`, nothing else. The translator reads a file in Russian or in English by the line
`- language: ru|en` and writes the same tree (`src/machine_text`, [README](../machine_text/README.md)); the reverse generator writes a tree back as a file of Alula in either language. The tests: `nova test src/machine_table` (85), `src/machine_run` (111),
`src/machine_text` (162), `src/machine_text_lang` (53), `src/machine_text_render` (49), `src/machine_agent_en` (14).

# Nested machines (task 119)

Task 119 (`doc/tasks/119-nested-machines/`, the decision and the numbers are in its `analysis.md`) runs the constructs that the interpreter refused before: a party of the kind `machine` (rule 35), the profile of a party, `Предел запросов` of a set, `Возвратов формы` above zero, `Правит`, the counters of the elements of a set (`lenses[*].attempt`), `вход_заново: запросы_из_к_отправке` with the return of the cancelled parties to `to_send`, and the built-in types `Signal` and `State`.

- **The call.** A nested machine is a separate engine (`Engine[AlulaMachine, AlulaState]`) in the same process: its own journal and store, its engine id `<parent id>/<request id>`, its trace `<parent trace>/<request id>`. The request of the parent to a party of the kind `machine` is a `SendOrder`; the nested machine starts with the event `start` (the field `request` is the request, the input is the record of the party's `input_type`, the column `профиль` of the parties table is its field `profile`). When it ends, its answer is the event `Answered` of the parent, its refusal (any code) is `Refused` with the code; a result that the parent reads as text goes through the optional `parse` of the party (a primitive failure is a bad form). A request sent again (rule 22, a restart) does not start the nested machine again; an answer that is ready is delivered again (rule 35.4).
- **The signals.** The action `передать(сторона, сигнал)` (`pass`) orders a signal for the open requests of a party; the engine holds it (`Engine.pending_signals`, journal `signal_ordered`) until the runner or the hub passes it (`signals_passed`, journal `signal_passed` of the methodology) - a signal ordered in the window between the commit and the send is not lost by a death. A nested machine gets `stop`, `continue`, `halt` as the events `parent_stop`, `parent_continue`, `parent_halt` and a cancelled request as `cancel_request` (the input is the request id); the fragment "Пауза" with the list `вложенные` handles them, and `отменить_открытые(кроме: вложенные)` leaves the nested requests open on a pause.
- **The registry.** `NestedRegistry` (`src/machine_run/nested.nv`) maps the name in the cell `вид` to a machine; `check_registry(parent, registry)` is the check of a pair (the machine is in the registry; the input type of the party is the record of the input of the machine and the result of the party is its result: `check_nested` of `src/machine_table`). The runner `run_nested_scenario` (`nested_scenario.nv`) keeps one engine and one memory world per nested machine and, after every step, passes between them the requests, the signals, the cancels and the replies. The files are `scenario/0` with two more step keys: `on` (the id of the nested request the step acts on; the parent when absent) and `also` (what the other engines must leave: `parent` or a request id; each value is an `expect`). The `host` answers of a step of the parent hold for the nested machines too.
- **Sets.** A set party (`id` empty) sends `to_send` ∩ the set, at most `Предел запросов` − the open requests; each element has its counters (`lenses[*].attempt` is bumped for the element that is sent); the request id is `<element>-<attempt>`. A cancelled element returns to the front of `to_send` (`вход_заново: запросы_из_к_отправке`). The entry into a state again sends nothing when the request is open (rule 12); a restart cancels the open ones and sends again (rule 18).
- **The rest.** `Правит`: when the answer is read by an expression that sets a bool primitive, the answer is rejected, a new attempt is made (journal `answer_edited`); `Возвратов формы`: the hidden datum `$form_used` counts the returns (journal `form_returned`), the next one is the failure `FormNotFixed`; no idle term on a call of a machine; the names of a step and of a trace come from the incoming event.
- **Product-only journal codes**: `signal_ordered`, `answer_edited`, `form_returned`, `request_repeated` (the methodology has `signal_passed` only); they stood in the table of the product until 0.3.2 and are codes of the language since 0.4.0 (`journal_language.md`, the engine and the executor).
- **Scenarios.** `scenarios/nested-call-*` (17: success, refusal, term, cancel, restart, death between the changes, another party in the window, an answer after a cancel, a duplicate answer, stop/continue/halt), `nested-set-*` (9: a lens set with one refusal, `Предел запросов`, a restart, a cancel), `nested-steps-*` (6: the chat session `dialog_steps` calling the agent step). The machines are `caller`, `callee`, `fan`, `dialog_steps`; they are generated by `doc/tasks/119-nested-machines/tools/gen_nested_scenarios.py` (the scenarios) and written in Alula (the machines).
- **Equality.** `src/machine_nested_eq`: 72 of the 75 scenarios of the agent step are run alone and as the nested machine of `dialog_steps` (the chat session of the meeting, "Шаг агента" is its turn), and after every step the state, the data, the journal and the requests of the two runs are equal.
- **Where it is not wired.** The hub of the server does not run a nested machine; the memory runner (`alula test <folder>`) does. A machine that is a hand-written Nova machine cannot be nested.

# The cycle check as data (task 122)

Task 122 (`doc/tasks/122-cycle-check/`) wrote the machine "Cycle check" of the methodology (`task-runner-review-states.md` and the code of its automaton: 23 states, 71 rows in 19 states) as a table of Alula 2.11:
[`machines/cycle_check.alula.md`](machines/cycle_check.alula.md) (Russian) and its translation `cycle_check.alula.json` (`alula compile`); the English file is `alula convert --language en`, the circles
`compile -> render -> compile` and `ru -> en -> ru` give the same tree. The machine repeats "review -> fix" of one artifact of a task (analysis, plan, implementation, delivery) until a series of clean passes, and for the
stage "meeting" it calls the nested meeting. The runner (task 123) calls it as a party of the kind `machine cycle_check(вход ВходПроверки, итог ИтогПроверки)`: the 14 fields of the contract are its `## Вход`, the answer
is the verdict (`clean`, `requirements`, `plan`, `question`, `restart`, `stopped`) with the source, the counters of the cycle and the findings "out of scope", or a refusal (`NoResult`, `StoppedByHuman`, `Cancelled`).

| What | Where |
|---|---|
| the parties | `session_launch` (nested machine `session_start`, task 121; input `ВходЗапускаСессии`, result `ИтогЗапускаСессии`), `meeting` (nested machine `meeting`, task 124; input `ВходСовещания`, result `ИтогСовещания`), `gatekeeper` (the gates 13, 3 and 9: the human, or an agent by the setting `исполнитель_повышенного_внимания`), `enhanced` (the gate 15 and the pause) |
| the types | the types of the layer of the methodology (`Цикл`, `Находка`, `Свод`, `Счётчик`, `Вердикт`, `ИтогСессии`, ...); the findings of the meeting are `MeetingFinding` (they differ from the findings of the review); the callee must declare the same fields (pinned by `src/machine_cycle/fit_test.nv`) |
| the data | 35 data (the variables of the table of the data of the methodology and the fields of the input kept as data) and the 3 of the fragment; `свод[номер_захода]` and `находки_проверки[номер_захода]` are dicts written by "On accept" of ЗАПУСК_СЕССИИ (rules 8 and 14); the datum of the source of the launch is `launch_source` (the dictionary name `source` is the binding of the pause) |
| the definitions | `потолок_исчерпан` is from the included file `арифметика_цикла` (hash `fad927a77d32`); `проверяющий`, `правщик`, `обновить_счётчики`, `наибольший_счётчик`, `сбросить_достигших`, `без_достигших_потолка`, `записи_сужения`, `есть_находка_уровня`, `находки_цикла` are in the table |
| the primitive | `stop_agent_group` (acting) at the entry of HALTED and ERRORED; the scenarios answer it with `"host": {"stop_agent_group": null}`; there is no real executor (`ir_proc_kill`, `ir_agent_close` of the plan 105 are a later task) |
| the pause | the fragment "Пауза" with the nested machines `[session_start, meeting]`: stop, continue, halt and cancel go to them as signals; their request stays open on a pause |

**Differences from the table of the methodology** (the details are in the analysis of the task): the verdict is an enumeration with words (the proposal of the methodology, "What the engine did not cover", item 12); the stop reasons and the mark of the
continuation are sets of literals (the words of the code of the automaton); the numbers below the minimums are the rows 2 and 3 of ReviewEntry with the journal codes `clean_needed_below_min` and `probes_min_below_min`.
The mode "show and continue" of the gate 3 and the answer of the gates by an agent are the mechanics of the executor of the gates and are not in the table; the simplified gates of the alpha and pre-release releases are a norm, not a mechanism.

**Scenarios.** `scenarios/cycle-*.scenario.test.json` are 101 files: 73 named after a row of the table (`cycle-<state>-<n>`: `review-entry`, `pass`, `meeting`, `launch`, `failure`, `after-session`, `summary`, `no-probes`, `retry`,
`gate3`, `outcome`, `criterion`, `gate15`, `narrowing`, `ceiling`, `gate9`, `stop-stage`, `levels`, `fix-outcome`, `pause`, `common`, `end-end`, `end-halted`, `end-errored`) and 28 flows (`cycle-flow-*`: a clean cycle, a rework, the refusals, the
restarts, the death between the commit and the send, the pause, the cancel, the ceiling, the narrowing, the verdicts of the stages). They are generated by `doc/tasks/122-cycle-check/tools/gen_cycle_scenarios.py` (the expectations are written by hand in it).
Thirteen rows are defensive and no sequence of events takes them: the rows "иначе" of twelve forks and the row 6 of the common events (the test names them); the row 3 of ОТКАЗ_СЕССИИ is taken by a failure with the code `Timeout`.

**`"standalone": true`.** A scenario of this machine plays the nested parties itself: the answer of the session launch is a step `answer` or `failure` with the id `session_launch-N`, the answer of the meeting is the same with `meeting-N`
(as for an agent). The key is new in `scenario/0` (`src/machine_run/scenario.nv`, the schema): a scenario with it runs on the plain runner, `alula run` takes it and `alula test <folder>` needs no nested machine in the folder
(without the key a parent is run with the nested machines of the folder, as before). The reason: the nested machines of the cycle check are the work of the tasks 121 and 124, and the runner of pairs holds one level of nesting (task 119); the
pair "runner + cycle check + session launch" is the task 123.

**Equality with the methodology.** `src/machine_cycle`: the table of the 71 rows of the methodology is copied as data and compared row by row (the number of the rows of each state, where each row leads, the kind of each state, the party of
each appeal, the signals of the gates); the codes and the parameters of the journal (11 codes of the check, 8 of the pause, `machine_data`, `machine_error`) are those of the table of the journal of the methodology, statically and on the scenarios; every
row has a scenario and the mark `taken` proves it.

**Not supported (and why).** (Task 123 lifted the two limits that stood here: the pair runner is recursive and an answer that comes on the pause is held, scenario `cycle-flow-pause-answer-held`; see "The task runner as data (task 123)" at the end.) The hub of the server does not run a nested machine. The nested machines `session_start` and `meeting` are not in the folder yet: the types of the call are pinned by `fit_test.nv`, their tasks (121, 124) declare the same
fields. The primitives `rd_task_document`, `pure_doc_status` and `rd_tree_diff` of the plan 105 belong to the runner (task 123): the cycle check gets the findings and the summary in the answer of the session launch and reads no file of the task.

# The session start as data (task 121)

Task 121 (`doc/tasks/121-session-start/`, the analysis with the numbers is its `analysis.md`) wrote the machine "Запуск сессии" of the methodology (`task-runner-session-states.md`, ten states) as a table of Alula 2.11: `machines/session_start.alula.md` (Russian; the machine is `session_start`), its tree `session_start.alula.json` (what `alula compile` makes of it, byte for byte), the English view is `alula convert --language en` (the circle `compile -> render -> compile` is equal in both languages, `src/alula_eq/session_test.nv`). The user writes no Nova. The runner of tasks (task 123) calls it; it calls the agent step as a nested machine.

- **The states.** B2 (`Gate2`, the keeper confirms the profile and the price) -> SCOPE (`Scope`, a fork on the volume) -> SESSION (`Session`, the nested machine `agent_step`) -> RESULT PARSING (`ResultParsing`, an operation) -> END; B1 (`Gate1`, the volume does not fit: repeat or halt) and B13 (`Gate13Session`, the agent step refused: repeat with a new request, `Gate13Session#1` is "restart", or halt); PAUSE from the fragment "Pause" with `вложенные: [шаг_агента]`; the ends END, HALTED (the stop reasons `gate1_halt`, `gate13_halt`, `pause_halt`, `cancel_request`), ERRORED. 26 rows: 11 of the states, 6 common events, 4 of the pause, 5 of the table "Ends".
- **The input and the answer.** The input is the ten fields of `ВходЗапускаСессии` (an absent field of an optional type is `none`: the interpreter took it for a missing field before this task); the answer is `ИтогЗапускаСессии` (`result`, `summary`, `findings`: the last two only for a check session, by the number of the pass). The refusals: `StoppedByHuman` (a halt at B1, B13 or in the pause), `Cancelled` (the cancel of the request of the call), `NoResult` (the end ERRORED).
- **The primitives of the host** (the methodology's `registry.md` of the CrewHarness repository since 0.4.0, 27 then): `launch_scope` (the volume fits or does not), `launch_profile` and `session_context` (the profile and the prompt of the request of the agent step, read in its table "Input"), `parse_session_artifact` (the stop word, the summary line and the findings of the artifact), `stop_agent_group` (acting, in the entry of HALTED and ERRORED). Their types are the set `session` of that `registry.md` (the meeting has types of the names `Finding`, `Severity` and `Summary` with other fields: each machine declares its own). The host of the tests is the `ScriptedHost`; there is no real executor. The names of the session codes are those of the code of the methodology (`s1`, `s7`, `commit`, ...): `session_dialog_kind` gives `delivery` for `s7`, `s7_fix`, `s8`, `commit`, `push`, else `main`.
- **The registry of the callable machines.** `product_registry()` (`src/machine_run/nested.nv`) loads `agent_step` and `session_start` from the compiled files; the words `шаг_агента` and `запуск_сессии` of the table of the names of the machines (`names_format.tsv`, kind `machine`) are their names. `check_registry(session_start, product_registry())` is empty and `check_nested(cycle_check, "session_start", ...)` is empty too (the cycle check of task 122 calls it with the same ten fields: the number of the pass is `?число` in both, a bound `int>=0` on one side would be another type for the pair check); a caller of the session start (the runner, task 123) is two levels deep, which `check_registry` still names an error until the runner of the pairs is recursive.
- **The gates are signals.** A gate (B2, B1, B13, the pause) is not a request of the engine: the keeper answers by a signal (`confirm`, `repeat`, `halt`), so a gate opens no request and the counter of the keeper stays 0 (as in the agent step).
- **Scenarios.** `scenarios/session-*` (55): `session-<state>-<n>` for each row (23: `gate2`, `scope`, `gate1`, `session`, `result-parsing`, `gate13`, `pause`, `common`, `end-end`, `end-halted`) and `session-flow-*` (32: the runner and the review, the four stop words, the volume, the retries of the session, the failures of the agent, the pause and the stop at a gate, the cancel in the middle, after the answer and at a gate, the restart of the parent / of the nested machine / after the answer, the death between the commit and the send, the input, a signal that is not waited for, a second answer, the request of the agent step). They are written by `doc/tasks/121-session-start/tools/gen_session_scenarios.py` and run by the pair runner (`alula test` finds the agent step in the folder). Two rows no sequence of events takes (`Scope#3`, `common#6`) and the end ERRORED is taken only by a changed table (`errored_test.nv`).
- **Equality with the methodology.** The journal codes and parameters of the scenarios are those of the table of the journal (`session_not_finished`, `session_launch_stopped`, `session_result`, the codes of the pause and of the forks); the branches of the function `step` of the hand-written automaton (11 rows) and the table "end -> reply" are compared with the rows and the outcomes of the runs (`journal_test.nv`, `methodology_test.nv`).
- **Not supported.** The text of the refusal of the agent step is not carried into the failure event (the engine passes the code), so `текст_отказа` that B13 shows stays empty (as in the automaton of the methodology, item 13a); the hook "stop the group of the agent processes when the pause is entered" does not exist (the group is stopped in the ends); the mode of B2 "show and continue" is the executor's; (task 123 holds the answers that arrive in the pause and runs two levels of nesting).

# Alula 2.12 (task 125)

Task 125 (`doc/tasks/125-*/`, the analysis with the numbers is its `analysis.md`) moved the product to the version 2.12 of the language (the methodology commit `255fe28`, the marks AL-23 ... AL-37 of section 0 of the changelog of the specification). There is no transition period (the owner, 2026-10-20): the translator, the decoder of the tree, the schema and the program read `2.12` and refuse `2.11` and every older version. What changed in the interpreter side:

- **The version.** `alula_versions()` is `["2.12"]`, `ALULA_VERSION` is `"2.12"`; the schema lists only `2.12`. Every machine of `machines/` says `format: 2.12` / `alula_version: "2.12"` and was built again by `alula compile`.
- **The flat input of the agent step (AL-30).** The input of a nested machine is the record of the fields of its `## Вход`. The agent step has the eight fields of `ЗапросАгента` (`kind`, `profile`, `session`, `dialog_kind`, `context`, `limits`, `trace`, `step`; its datum `agent_request` is built by the record constructor), `dialog_steps` and `session_start` call it with `machine шаг_агента(вход ЗапросАгента, итог ОтветАгента)`: seven fields in the table "Input" of the appeal, the profile by the column of the party. A start without a field is `input_rejected` with the name of the field (the 8 scenarios `agent-step-flow-input-without-*`). The starts of the 83 scenarios of the agent step and of the 6 of `nested-steps-*` are the flat fields (the generators: `doc/tasks/109-agent-step-machine/tools`, `119-nested-machines/tools`, `121-session-start/tools`).
- **The journal tables (AL-31, AL-113).** `Registry.journal` holds the union of the table of the language (`journal_language.md`, 35 codes: the format, the fragment "Pause", the engine and the executor, `language_journal()`) and the table of the host (`journal.md`, read by `parse_journal`); `language_registry()` and `load_host(registry_text, journal_text)` fill it, `new_registry()` leaves it empty (no table, no check). `check_machine` compares the code and the parameters of every `журнал(...)` and `ошибка_машины(...)` with the union: a code in neither table, a missing parameter, a parameter the row does not name are issues. A code of a host does not repeat a code of the language: `journal_table_issues(language, host)` says so, a test pins it. The tables of the methodology and of the product are the data of their owners (`machines/methodology/journal.md`, `machines/product/journal.md` of the CrewHarness repository); their tests (the codes the machines write and the scenarios see against the union) are there.
- **The failure of the parse and the table "by role" (AL-33).** An answer that the parse refuses (`PrimitiveFailed`) goes back by `Возвратов формы` and then is the failure `FormNotFixed` (no change); a value that is not of the type of the parse is a DEFECT of the host (`machine_defect` with the kind `type_mismatch`), no longer a return of the form. Until 2.23 `Registry.roles` held the rows `RoleRow { primitive, role, result, reads }` (`add_role`, `find_role`, `has_roles`): for `разбор: имя("роль") -> Тип` of a primitive that had a table the role had to be in it and `Тип` its result. Since 2.24 (AL-131, task 181) the mechanism is gone: each role of the parse has its own function, `parse_witness_reply` gives `[]WitnessAnswer`, `parse_author_reply` `EditResult`, `parse_lens_reply` `LensResult`, each with the one parameter `reply: AgentReply`; the check compares the type after `->` with the result of the function, what the function reads (the column `reads`) joins the "Input" of the state (rule 11), and a literal of a role is an error of the translator.
- **The key `fragments` (AL-32).** The decoder takes `fragments` (the connection of the fragment `Pause` with the six arguments, the behavior words are checked) and keeps it in `MachineDef.fragments`; the schema has `fragment_use`. The interpreter does not use it: the fragment is substituted in the ordinary keys. The key is the product's; its form and the questions to the methodology are in the analysis of the task.
- **The hand-written trees** (`calc`, `gate`, `actions`, `lenses`, `variants`, `chat`) say `alula_version: "2.12"`; `gate` now writes `human_continue` with the parameter `event` as the table of the methodology asks.
- **Not done (named by the methodology as open):** the common file of the types of the call (AL-34, the types of the input and the result of a nested machine are in both machines and `check_registry` compares them), the file of the fragment Pause in Alula (AL-35, the fragment is compiled into the translator).


# The task runner as data (task 123)

Task 123 (`doc/tasks/123-task-runner/`, the analysis with the numbers is its `analysis.md`) wrote the machine "Раннер задачи" of the methodology (`task-runner-states.md`, 75 states) as a table of Alula 2.12:
`machines/task_runner.alula.md` (Russian; the machine is `task_runner`), its tree `task_runner.alula.json` (`alula compile`, byte for byte), the English view is `alula convert --language en` (the circle `compile -> render -> compile`
is equal in both languages, `src/machine_runner/table_test.nv`). The runner calls the nested machines `session_start` (task 121) and `cycle_check` (task 122); the first calls `agent_step`, so the pair runner runs several levels.

- **The states.** 76: the 75 of the methodology (27 forks, 15 operations, 30 appeals with the pause of the fragment, 3 ends) and the fork ReviewVerdict. The format allows a condition only in the rows of a signal, and the verdict of a review is a field of the
  record `ИтогПроверки`, so each of the four reviews (AnalysisReview, PlanReview, ImplementationReview, DeliveryReview) has two rows (`answer`, `failure`) and the 18 rows "answer: clean / requirements / question / plan / restart" of the methodology are the rows of
  ReviewVerdict (19 with the row "иначе"). 251 rows in all (233 of the states and of that fork, 4 of the pause, 6 common events, 8 of the ends); 22 of them no sequence of events takes (named in `cover_test.nv`).
- **The route.** `маршрут` is `""` (not chosen), `"полный"` or `"быстрый"`: the classification (RouteClassification) proposes, the gate 14 chooses, RouteCheck checks the settings of the project against the minimums of the methodology, RouteRecording writes the numbers of the cycle,
  BriefCheck and BriefCopy make the approved copy of the brief on the fast route (the record of the approval first, the file last: `create_approved_copy` is acting), FullPathReturn goes back to the full route by the word "full path" (gates 5, 8, 10a) or by the rule.
- **The primitives of the host** (the methodology's `registry.md` of the CrewHarness repository since 0.4.0, 56 then): volatile `specification`, `task_plan`, `implementation_report` (one per document: the answer of the `ScriptedHost` is chosen by the name of the primitive), `route_features`, `project_settings`, `source_list`, `brief_complete`,
  `copy_approval`, `approval_by_document`, `source_with_specification_marks`, `last_implementation_review`, `has_unresolved_line`, `customer_letter`, `round_letters`, `secrets_report`, `tree_diff`, `commit_message`, `commit_text`, `feedback_route`; acting `run_preparation`,
  `write_answers`, `write_decisions`, `write_owner_marks`, `save_round_notes`; also acting `write_draft_status`, `create_approved_copy`, `rename_letter`, `release_lock`, `show_human` (and `stop_agent_group` of task 122). The documents and the files are the host's objects; in the data of the machine
  there is the dict `утверждения` (the record of the approval: the date, who, the hash of the text; the approval is valid when the hash equals that of the document now). There is no real executor.
- **The pair runner is recursive.** `run_nested_scenario` keeps a tree of nested machines (each with its world, journal and store; the engine id is `<parent id>/<request id>`); a step names a machine of the tree by the path of the requests
  (`session_launch-1/agent_step-1`, or by its own id when only one machine has it) in `on` and in `also`; the answers of the host of a step of the root hold for the whole tree. `check_registry` checks every level; a machine that a machine below the first level calls and
  the registry lacks is not an issue but a gap named by `registry_gaps` (today: `meeting`, task 124). `product_registry()` has `agent_step`, `session_start`, `cycle_check`.
- **Answers on the pause are held (rule 14).** An answer or a refusal of an open request that comes while the state does not wait for it (the pause) is kept in the hidden datum `$held` (journal `answer_held`), the request stays among the open ones, and the return into the appeal by "continue"
  sends nothing and takes the kept outcome as if it had just come (journal `answer_replayed`). An answer for a request the machine does not keep open (a machine without `open_requests`, or after the end) is dropped as before.
- **The destination `возврат_подготовки`** is translated, checked (the machine needs the datum `preparation_return`) and run: the target is read before the actions of the row and the jump empties the datum. The datum is written by the preparation of the executor at a restart, so no sequence of events takes
  the row PreparationOutcome 2; `prep_test.nv` runs a probe machine that takes the datum from its input.
- **Scenarios.** `scenarios/runner-*` are 257 files: 229 named after a row (`runner-<state>-<n>`: the state in the kebab case of its Latin name, `runner-gate10a-1`, `runner-review-verdict-13`, `runner-common-5`, `runner-halted-6`) and 28 flows (`runner-flow-*`: the two routes, reworks, the gates 14, restarts,
  the death between the commit and the send, the cancel, a stranger in the window, the held answers, and five flows with the real nested machines, up to four levels deep). They are written by `doc/tasks/123-task-runner/tools/gen_runner_scenarios.py` (`rl.py`, `gold.py`: the golden path of the full route and of the fast route; the expectations are written by hand in `sc_a.py` ... `sc_flows.py`).
  Most run with `"standalone": true` (the nested machines are played by steps); the flows `runner-flow-nested-*` run with the machines of the folder.
- **Equality with the methodology.** `src/machine_runner`: the 228 rows of the methodology (`methodology_rows.tsv`, made by `extract_rows.py` from the file of the methodology) are compared row by row (the number of the rows, where each leads, the kinds, the sides of the gates, the signals); the codes and the parameters of the journal are
  those of the table of the journal of the methodology (30 codes of the runner), statically and on the scenarios; every row has a scenario and the mark `taken` proves it; the 42 "Checks of the implementation" are listed with what the scenarios cover (18), what another machine covers (10), what a unit covers (2) and what is not covered and why (12).
- **Not supported.** The preparation at a restart, the lock, the files of the task, the documents and the letters are the host's (no real executor); the modes "show and continue" of the gates 4 and 6, the answer of the gates by an agent and the check of the profile of the gatekeeper are the executor of the gates; the meeting is not called (task 124); the hub of the server does
  not run nested machines (a task after 123); the machine "Совещание" is not in the folder yet, so `registry_gaps` names it.

# Alula 2.14 (task 148)

Task 148 renamed the language Portolan to Alula, the format 2.14 of the methodology (the commit `7b59336`: only the name of the language and the names of the files; the owner, <!-- guard-allow(legacy-name): the history of the name -->
2026-10-21; no transition period, the owner, 2026-10-20), and moved the package to it. What changed here, and nothing else:
- **The version.** `alula_versions()` is `["2.14"]`, `ALULA_VERSION` is `"2.14"`; the schema lists only `2.14`; every machine of `machines/` says `format: 2.14` and `alula_version: "2.14"`; the machines of the methodology say `machine_version: alula-2.14`.
- **The names.** The files are `*.alula.md`, `*.alula.txt`, `*.alula.json`; the modules `alula.alula_cli`, `alula.alula_scenarios`, `alula.alula_eq`, the program `alula` (`src/alula.nv`), the types `AlulaMachine`, `AlulaState`, the functions `load_alula_machine(_with)`, `alula_step`, `alula_machine_with`; the marks of the changes of the format are `AL-NN` (they were `Я-NN` and `Ya-NN`, the number is the same).
- **The refusals.** A file of 2.12 or of an older version, a tree with the key of the former name of `alula_version`, a version of a tree other than 2.14: each is an error with its own message (tests `alula_version_test.nv`, `marker_test.nv`, `render_test.nv`).
- **The hashes** of the files of definitions are recomputed for the new header: the Russian sample `2aa456d75044`, the English `8f309d17b896` (the same as in the methodology 2.14), the definitions of the meeting `2b2db96998f6`.
- **Not changed:** the trees `machine/2` (but for the name of the key and the value of the version), the 621 scenarios and their expectations, the table of the words, the notation of 2.12 (see the README of the package: the simplifications of 2.13 are not read yet).

# Alula 2.17 (task 151)

The semantics of the formats 2.15 - 2.17 (the marks AL-51 ... AL-64; the analysis is `doc/tasks/151-alula-semantics-215-217/analysis.md` of the CrewHarness repository).

- **The version.** `alula_versions()` is `["2.17"]`, `ALULA_VERSION` is `"2.17"`; the schema lists only `2.17`; every machine of `machines/` says `format: 2.17` and `alula_version` `2.17`; the package and the program were then at an internal step of the version (published only as `0.3.0` with the task 152).
- **The names.** The tree holds the JSON names; how a file gets them (the section `## Имена`, the dictionary of the methodology pinned by the hash `60383c370415`, the transliteration, ten spaces of the distinctness) is in [src/machine_text/README.md](../machine_text/README.md). The 90 rows of `## Имена` of the machines of `machines/` keep the JSON names that the brackets of 2.14 gave: the trees are equal to the trees of 2.14 (a test of the task compares them).
- **A party of a free input (AL-51, AL-52).** The key `counter` of a party is required for every kind but `human`. A party `human` without it takes the signal by its name in the current state: the interpreter does not change (the gates of a human were never requests of the engine), the checks refuse for an appeal to such a party a table `Запрос`, a set, an idle term, `Правит`, returns of the form, `При приёме` and the events `ответ`, `сбой`. The machines `chat` and `dialog` write their user so (`—` in the column `счётчик`); the data `user_attempt` stay in the tables and stay 0; `dialog_steps` keeps the gates of its user, because its state `ЖДУ` reads data through a table `Запрос` of the executor. Scenarios: `free-input-*`.
- **The fork (AL-57).** A fork without the row `else` is an error unless the rows prove the exhaustion by the type (`check_forks`, `fork_proved`); `machine_warnings` gives the warning about a row `else` that cannot be reached. Two such rows of the machines (`Scope` of `session_start`, `PhaseSwitch` of `task_runner`) were removed.
- **The hashes** of the files of definitions: the Russian sample `1e30254f66f9` (the number of the methodology), the English `8a2c2d564899`.

# Alula 2.22 (task 152)

The syntax of the formats 2.18 - 2.22 (the marks AL-65 ... AL-102; the analysis is `doc/tasks/152-alula-syntax-218-222/analysis.md` of the CrewHarness repository, the translator is described in [src/machine_text/README.md](../machine_text/README.md), the schemas in [schema/README.md](schema/README.md)).

- **The version.** `alula_versions()` is `["2.22"]`, `ALULA_VERSION` is `"2.22"`; the schema lists only `2.22`; every machine of `machines/` says `format: 2.22`, `machine_version: alula-2.22` and `alula_version` `2.22`; the package and the program are `0.3.0`.
- **The catalog.** The function `concat` (`склеить`) is new: `concat(a, b, …)` joins two texts or more (`fn_concat` in `eval.nv`, `catalog_names` in `machine_table/check.nv`); the insertion `"ход ${номер}"` of a file is unfolded by the translator into `concat` of the parts and `text(x)` of the inserted values. A range `a..=b` is `range(a, b + 1)`; the eight list functions are called as methods in a file and as calls with the list first in the tree. The tree has no new node.
- **The number (AL-101).** `int` is a signed 64 bit number: `+`, `-`, `*` are checked and an overflow is the error `overflow` of the evaluator; a float whose result is not finite is `overflow` too; `/` and `%` of ints truncate toward zero. The JSON reader refuses an integer beyond 64 bits.
- **The machines.** The 15 tables, the fragment "Pause", the files of functions (`defs/`), the cases of the equality and the samples of the methodology (`machine_agent/cases/`) are written in 2.22; their trees are equal to those of 2.17 but for the version, the hashes of the files of functions are the Russian sample `642e1f78f0f7`, the English `928cd807453a`, the functions of the meeting `36b3b4c585c6`. The 626 scenarios (621 of the folder and 5 of the program) pass without a change of the expectations.

# Alula 2.23 (task 170, version 0.5.0)

The marks AL-115 ... AL-122 (the changelog is [spec/alula-changelog.md](../../spec/alula-changelog.md), the translator is described in [src/machine_text/README.md](../machine_text/README.md)).

- **The version.** `alula_versions()` is `["2.23"]`, `ALULA_VERSION` is `"2.23"`; the schema lists only `2.23`; the tree `machine/2` has no new node; the package and the program are `0.5.0`. There is no transition period: a tree of 2.22 and a table with `format: 2.22` are refused.
- **The classes of the host functions (AL-116, AL-117).** `pure`, `volatile`, `acting` (`host.nv`); the words `reading`, `writing` and `irreversible` are refused with the new word; a volatile call may stand in the actions of a row.
- **The dict and `length` (AL-118, AL-119).** The order of a dict is the order of writing; a repeated key is the error `duplicate_key`; `length` is for a list and a dict only.
- **The hashes.** The line `format` is a part of the hash of a file of functions, so the hashes of the samples became the Russian `ebb7658048b2`, the English `a9af85407c2b`, the functions of the meeting `5dbdd898d25d`; the hash of the dictionary `60383c370415` is the same.

# Alula 2.24 (task 181, version 0.6.0)

The marks AL-123, AL-128 ... AL-132 (the changelog is [spec/alula-changelog.md](../../spec/alula-changelog.md)); the external functions are described in [src/host/README.md](../host/README.md) (task 179) and in [src/machine_text/README.md](../machine_text/README.md) (tasks 175 and 181).

- **The version.** `alula_versions()` is `["2.24"]`, `ALULA_VERSION` is `"2.24"`; the schema lists only `2.24`; the package and the program are `0.6.0` (`alula version` prints `alula 0.6.0 (Alula 2.24, machine/2)`). There is no transition period: a tree of 2.23 and a table with `format: 2.23` are refused with the version named.
- **The parse by role (AL-131).** `ParseDef { primitive, result }`: the tree holds no literal of a role (the key `role` is not in the schema); `Registry` is `{ primitives, journal }`, `RoleRow`, `find_role`, `has_roles`, `add_role` are gone, a table by role in `registry.md` is an error; the executor calls the function of the parse with the answer only (`apply_parse` in `machine_run/chain.nv`).
- **The hashes.** The line `format` is a part of the hash of a file of functions, so the hashes of the samples became the Russian `818a4aaeef4f`, the English `431e7018e2bb`, the functions of the meeting in the tests `cf2a79073e96`; the hash of the dictionary is `35c571ccda17` (the dictionary of the version 13, 1270 pairs; the one of the version 11 went with the format 2.23).
- **The data.** The examples, the samples of the methodology (the agent step in both languages, the machine "Meeting"), the cases, the files of functions and the fragments say `format: 2.24`; the machine "Meeting" names the three parse functions by role in `разбор:` and declares them in `## Внешние функции`.
