# Alula: specification of the language for writing state machines as tables, version 0.27

Translation of [spec/alula-spec.md](alula-spec.md); the Russian text is normative: on any difference the Russian text is correct.

Changelog: [spec/alula-changelog.en.md](alula-changelog.en.md) (Russian: [spec/alula-changelog.md](alula-changelog.md)) — what changed in each version, open items, correspondence to the methodology rules. This file holds only the rules of the language in force.

The name of the notation is **“Alula”** (`Alula`; the owner's word, 2026-10-21: «Alula - ОК»). It is read with the stress on the second syllable (Russian «Алу́ла»); in Russian the word is feminine and is declined like «Луна». Alula is a star in the paw of Ursa Major (a name in the IAU catalogue), from Arabic *al-qafza al-ūlā*, “the first leap” (the stars of “the three leaps of the gazelle”: Alula, Tania, Talitha); a leap is a transition of the machine from state to state. A second, independent meaning is the English *alula*, “a little wing” (Latin *ala*, “wing”, and the diminutive suffix *-ula*): a small group of feathers on the first digit of a bird's wing (the “bastard wing”) with which the bird controls its flight at low speed. A machine file is a “machine table” in Alula. The name's availability was checked on 2026-10-21: no ALULA trademark for languages or development tools was found (ALULA marks in classes 9/42 belong to a few narrow companies: security systems, insurance, oncology; in Russia there are none in classes 9/42, TMview); the `alula-lang` namespaces (GitHub, domains, packages) are free; a manual check of the Rospatent registry is an open item. The former name of the language (versions 2.7–2.13) and why it was dropped are in the history [doc/alula-history.md](../docs/history.md), section 10; the reasons, goals and history of the language are there too.

Format version: 0.27, 2026-10-28. Status: **experimental format; version 2.2 was implemented by an interpreter in another language; equality with the automaton by journal is confirmed on 39 tests of one small machine (the chat machine); the expressibility of “Agent step” and “Meeting” was checked by pilots; not implemented: nested machines, `Edits`, the party profile, `Request limit`, `Form returns`, `pass`.** The rules for writing machines are in [state-machine-spec.md](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-spec.md); this file sets the formal notation of the same tables: types, expressions, actions, parties, libraries. The journal is [state-machine-journal.md](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-journal.md); the glossary of English names is [state-machine-glossary.md](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-glossary.md) (the dictionary of automatic JSON names, section 1a). On a difference with the rules of the specification the specification is correct, and this file is corrected after it.

Goal: a machine is described by one file without code in Nova; from the description an engine gives the same behavior as the automaton in Nova: the same transitions, the same structured journal, the same data and queue. Checked by the expressibility of the automata rows (which rows are written without workarounds) and by running one small machine through an interpreter (comparison with the automaton by journal, the header).

The examples are taken from the pilots (excerpts of “Agent step” and “Meeting”). A construct used in an example is defined in sections 2–5, 7–9 or in the catalog (section 12). The examples are excerpts: the section `## Names` (1a) is not shown in them, except the example in section 1a; where a name of an example would get in a Russian machine file a JSON name other than the automatic one, the `## Names` row is named under the example (the samples carry the whole section). The examples of this English version are written in the English form of the language (section 1a): the keywords come from the `en` column of the word table [alula-keywords.tsv](alula-keywords.tsv), and the names invented by an author are English (Latin), so each of them is its own JSON name.

## 1. Machine file

The keywords of this section (section headings, column names, key lines, party kinds) are quoted here in their English form; in the Russian form of a file they are the Russian words, and in the English form they are written by the [word table](alula-keywords.tsv); the rules are in section 1a.

**Extension.** A machine file in Alula is called `*.alula.md` (the machine name is Latin, as in `- machine:`; for example `agent_step.alula.md`); the former names `*.table.md` and `*.table.txt` are not used, there is no transition period (the owner's word, 2026-10-19: “there is no transition period”; version 2.11). Parsing does not check the extension: the extension is checked only by the formatting check script. A library (in particular, a functions file) is a file of the format `library` with the header `# Library:` (section 9), also `*.alula.md`. **A compiled tree** (JSON of the machine tree, section 6) is called `<name>.alula.json`: `agent_step.alula.md` ↔ `agent_step.alula.json`; it is not a separate format but the executable form of the language itself — a hand-written tree is also Alula, written in the JSON form; the root key of the tree `"kind": "machine"` does not change. The former `*.machine.json` is not used, there is no transition period. The revision of the machine (`- revision:`) is set by the author of the file; it is the revision of the machine itself: an integer, `1` by default; the author raises it when the behavior of the machine changes. A string such as `alula-2.24` does not fit a revision: the error “a revision is an integer” (section 10). The version of the Alula language is written separately (`- alula_version:`) and is not a revision; the caller compares the `revision` of the called machine only for equality with the entry of the host registry (call protocol, section B, item 6).

Markdown, sections in order:

| Section | Contents |
|---|---|
| header | `# Machine: <Name>`; list items `- machine: <latin_name>`, `- revision: <number>`, `- alula_version: 0.27`, optionally `- language: ru` or `- language: en` (1a; the marker `- ` is optional in parsing; in writing it is required: markdown glues consecutive lines together) |
| `## Types` | records and enumerations, including those with fields at their forms (section 2) |
| `## Names` | optional: the table `\| name \| json_name \|` — JSON names other than the automatic ones (1a); no such names — no section |
| `## Constants` | `name`, `type`, `value` |
| `## Parameters` | `name`, `type`, `default`, `project_override` (`project.<key>`); the default value is required: if the source gives a stub, it is written with the note “source stub”; a project key that the source does not name is `—`; passing values from outside — below |
| `## Input` | the call input fields: `name`, `type`, note; lines `Invariant: <bool expression over the fields>`; the input value is the name `input` |
| `## Data` | `name`, `type`, `initial`, `non_decreasing` (section 2) |
| `## Parties` | see below |
| `## Includes` | libraries: a subheading `### Name` with `- File:`, `- Hash:`, `- Name:` and a table of parameters (section 9); without prose |
| `## External functions` | declarations of the host external functions that the machine calls: `name(arg type, …) [<class>] [-> type]` without a body (section 7) |
| `## Functions` | pure functions of the author, the declaration `fn` (section 8) |
| `## States` | the first line `Initial state: NAME`, then the states (section 4) |
| `## Output` | `- Result: <type>` and the table “end → response” (4.7) |

**An empty section is not written**: there is no section with the single line `—`.

**Tables**. The separator row under a table heading (`|---|---|`, `|:---|---:|`) is a row of the signs `-`, `:`, spaces and `|`; parsing skips it. The sign `|` inside a cell is written `\|` (a literal set `"a" \| "b"`, the alternatives of `match`); parsing removes the escaping. In the examples of the format the separator is omitted.

**The comment `//`** (as the bare `//` of Nova, D104). In a code block (between ``` fences) and in a heading line `##` or `###` — after the heading text (`## Common events     // parsed before the state rows`) — the sign `//` outside a text literal starts a comment to the end of the line: parsing and the checks do not read it, it does not enter the tree, the generator does not write it (1b). `//` inside a literal is text (`"http://x"`): a comment is looked for after the literals of the line are parsed. A code cell of a table (the code columns: actions, expression, condition, “when”, “response”, “value”, “initial”, “default”, “profile”, “non_decreasing”; the event cell) and a key line (`- Except: …`) have no comment: `//` outside a literal there is a check error; in the prose columns (“note”) `//` is ordinary text, links `https://…` are allowed; an explanation of a table row is the column “note” or a prose paragraph (4.1). The language has no operator `//` (division is `/`, 3.1). The doc comments of Nova `///` and `//!` are not introduced: `///` is an ordinary comment too.

**`## Parameters`: passing values from outside**. The engine accepts parameter overrides as a “key → value” table: the key is `project.<key>` from the column “project override”; the value is checked against the parameter type (a full map — by the rules of section 2), a key that is not in the column is a load refusal. This is the passing mechanism; where the engine takes the table from (project settings, the test `params`, section 11) the format does not define. The keys `project.<key>` are named by the product, they are not part of the language; the column “project override” of the sample stays `—` because the source names no keys. A default value that depends on an external key applies only when the key is present in the override table; otherwise the default value works.

**`## Input`.** The input type is a record made of the fields of this section (rule 35, item 1); `initial: input.<field>` takes the value from the input. An optional field (of type `?T`) that is absent from the input equals `none`. The invariant is checked by the engine when it accepts a request; a violation is a call refusal: the engine writes the journal event `input_rejected` and finishes the call with the refusal `NoResult` with the text `input rejected: <reason>`; the machine state does not change. The same refusal — when parsing the input. The event parameters (journal, subsection “Events of the table format”): `reason` — a closed list `json` (the input is not JSON), `missing` (a required input field is absent; an optional one gives no refusal), `type` (a field of another type, outside the type bound, outside a literal set, or not an `id` of UUID format, for example `int>=0` at −1), `invariant` (an input invariant is violated); `field` — the input field name (for `missing` and `type`); `index` — the invariant number from zero (for `invariant`). `field` and `index` are optional: with `json` they are absent, and the template skips them. Examples: `input_rejected(reason=json)`, `input_rejected(reason=missing; field=label)`, `input_rejected(reason=type; field=start)`, `input_rejected(reason=invariant; index=0)`. The call request identifier (`call_request_id`) does not lie in the input: the engine gives it (section 9).

**The input and result of a called machine**. A party `machine <name>` names no types: the check takes the input type and the result type from the entry of the called machine in the host registry (the fields of its `## Input` and `- Result:`). The fields of the `Request` of an appeal to this party are exactly the input fields of the called machine: the same names, the expression of each field fits by type the type of the field of the called machine, the order is not significant; the field `profile` is by 4.2. Therefore an input that the callers pass by fields (`kind`, `session`, `context`, …) is declared by the called machine with the same fields, not with one record field; the record as a whole, if it is needed in the data, is built by `initial` with a record constructor (`AgentRequest { kind: input.kind, … }`, the “Agent step” sample). The result of the appeal is read with the result type of the called machine; the name of this type (for example `SessionStartResult`) is visible in the caller as a type from the registry entry, is included implicitly, and the caller declares no copies of the input and result types. The field types are compared by the compatibility of section 2: `int` and `int>=n` are compatible both ways — an expression of type `int` for a field `int>=0` of the called machine (or the reverse) are one field, the bound is checked by the called machine when it accepts the input (`input_rejected`, `reason=type`). The comparison of the registry entry with the file of the called machine is the product's (see the [changelog](alula-changelog.en.md), “Open items”).

**`## Parties`.** The table `| name | id | kind | profile | signals | counter |`.

| Kind | What it is |
|---|---|
| `agent(result Type)` | an agent; `result` is the party's result type |
| `human(result GateOutcome)` | a human: at a gate (with a counter) or with free input (`—` in the column `counter`) |
| `enhanced(result GateOutcome)` | an enhanced gatekeeper |
| `human or agent by setting <name>(result GateOutcome)` | a gatekeeper: a human or an agent, by the project setting (rule 19); `<name>` is the key of the project setting, it leaves the machine: its JSON name is built by 1a, and where it is wrong it is set by a `## Names` row (`\| исполнитель_повышенного_внимания \| elevated_attention_executor \|`: the transliteration would give `ispolnitel_povyshennogo_vnimaniya`); the Russian record is `human или agent по настройке <имя>(итог ИсходВорот)`; in the JSON tree this kind is called `gatekeeper` |
| `machine <name>[; parse: <external function> -> Type]` | a nested machine (rule 35): a name from the host registry (rule 35, [call protocol](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-call-protocol.md), section J, item 6), without parentheses and types: the request input type and the response result type are taken from the entry of the called machine in the registry; an optional result parse (see below) |

- `id` is the Latin word of the party: for the parties of the methodology machines — a value “request party” of the glossary ([state-machine-glossary.md](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-glossary.md), section 2.14: `agent`, `gatekeeper`, `enhanced`, `witness`, `author`, `session_launch`, `review`, `meeting`, `agent_step`), a party not listed there takes its own Latin word (the example of a party with free input below — `human`); it goes into the envelope of the request and the response and into the request identifier (`<id>-<number>`), therefore it gets into the journal. For a party with a set (4.2) it is `—`: the identifier is the element of the set. The party identifiers of a machine are distinct.
- **`result`** is the party's result type: for `agent` — a type from `## Types` or a built-in type (a type word of section 2: `str`, `int`, `bool`, …; the Russian `строка`, `число`, `булево`), for `machine` there is no result in the entry: it is the result type of the called machine from the host registry entry; for `human`, `enhanced` and the gatekeeper — the built-in enumeration with fields `GateOutcome`, whose forms are the signals of the column “signals” (a signal without data is a form without fields, `signal { field type }` is a form with fields, the same record; rule 19), the event `signal(…)` of the party is a form of `GateOutcome`. `response: Form` is resolved by the party's `result` (for `machine` with `parse` — by the parse result); the qualified form `response: TurnResult.Finished { … }` is allowed, the type in it being the party's result type; an unqualified form name is searched only in this type.
- `profile` is an expression or `—`; **the only source of the profile**: the request field `profile` is taken by the engine from here, a `profile` line in the “Request” is a check error. The column reads the machine data, constants, parameters, `input` and (for a set) `party`; a call `name(arg)` of a volatile external function is allowed (section 7), its hidden reads (by the host registry) are machine data; the column does not read the names of a state's `Request`: the table of “Parties” is one per machine, rule 11 does not apply to it. If the profile lies inside the request (for the party `agent` — `agent_request.profile`), the party has no separate field and `—` is written.
- `counter` (rule 15) is **required for every party except a party with free input**: the datum where the party's attempt counter lies — a datum name (`agent_attempt`) or, for a party with a set, the path of a field of the element record (`lenses[*].attempt`). The datum is made by the loader itself (`int>=0`, initial `0`, `non_decreasing: yes`): no row for it is written in `## Data`; it may be read and may not be written from actions (a write from a table row, an “On accept” or an acting function is a check error, section 10); for a path the field stays a field of the element record, the record type declares it and the record constructor gives `0` (`attempt: 0` in `lenses`, section 2); the attempt number of a request equals the counter value after the increase (mechanics, before sending; at a gate of a human — before the gate is shown, rule 19), the request identifier is `<id>-<number>` (for a set — `<set element>-<number>`). The check of section 10 verifies the datum.
- **A party with free input** (rule 19) is a party of the kind `human` with `—` in the column `counter` (`—` is the “no value” sign in the “Parties” table): it has no gates; a human answers it with a **word of free input** — a party signal without gates: it carries no gate identifier, is accepted by the signal name by a row of the current state and leads a transition (what a word is — below, `signals`); there is no gate record and no counter; the agent gatekeeper does not answer it, therefore `—` is allowed only for the kind `human`. A `human` party with a counter is gates (rule 19). Example: `| interlocutor | human | human(result GateOutcome) | — | message { content str, author str, source str } | — |`.
- `signals` — for the kinds `human`, `enhanced`, the gatekeeper: the **party signals** — what the party says to the machine at a gate: a signal or `signal { field type, … }` — a signal with data (the fields in braces, as at a form of an enumeration; the former record `signal(field type)` is an error); the signals are written as in the machine tables (including those of several words: `halt meeting`); the JSON name of a signal and of its fields is built by 1a, and where it is wrong it is set by a `## Names` row: for `засчитан { находки []Находка }` the glossary gives the signal `counted`, the field `находки` — `findings`, no rows are needed; a signal field is declared in braces through a space, `counted { findings []Finding }`, and in a transition row it is bound as `signal(counted { findings: new_findings })` (3.1). The declaration itself names which party may give the signal: these are **all signals of the party**; the signals of a state are the signals of its rows (4.3). A party signal is an event of the party from its declared set (for `human`, `enhanced` and the gatekeeper — a form of `GateOutcome`); it belongs to the open request of that party, and when a human answers — to its open gate and carries its identifier, as rules 15–19 of the specification say (the attempt counter, the acceptance of the response, the words of a human); the gate identifier `<identifier>-<number>` names the party, and the signal is checked against the signals of that party: one it did not declare or one that came from another party is discarded (“a word of a foreign party”, rules 17, 19); a signal of a party with free input carries no gate identifier and is accepted by name in the current state (rule 19). It differs from a machine signal (common events, section 9) by being declared at the party and by who may give it. A **word** is the text a human writes to answer; a word carries one of the party signals: at a gate a word is one of the party signals, carries the gate identifier and is accepted once; for a party with free input a word is accepted by the signal name by a row of the current state, there is no gate identifier. For the other kinds — `—`.
- **`parse`** — only for the kind `machine`: a volatile external function (section 7) with the single parameter of the type `result` and a result of the given type; it is written as a bare name without parentheses and arguments (`parse_author_reply`): each role has its own function, there is no second role argument. The engine calls it when it accepts the response (rule 14), after the “Edits” check (4.2) and before “On accept”, and the **response value** for `response(name)`, `response: Form { … }` and “On accept” becomes the parse result; without `parse` it is the `result` itself. The event `response: Form` requires that the response value be a value of an enumeration. The function's hidden reads (`reads` in the host registry) enter the reads of the state (they are derived, rule 11); the parse is called once per response, the result is stored with the accepted event. A parse by role is a separate function per role (section 7).
- **A parse failure**. A parse either gives a value of the given type or refuses: a response not by form (the artifact is unreadable, there are no excerpts, the comparison did not converge); the remarks of the refusal are a service record that the return of the party reads. A parse refusal is a response not by form (rule 18): no event arises, “On accept” is not executed, the response is not written in `accepted_requests`; while the returns are fewer than “Form returns” (4.2), the engine returns the response to the party (for `machine` — with a new request of the same party with a remark); after exhaustion, and with `Form returns: 0` at once, the request is closed by the event `failure` with the code `FailCode.FormNotFixed` (a code outside the state's list the engine brings to `NoResult`, 4.3). The return and its journal record are engine mechanics (product journal codes — section 5). A value of another type than the one named after `->` is a host defect, that is a program defect (3.3), not a response not by form.
- Under the table — a list item `- Request limit: <int>=1 expression>` (one per machine, rule 21; if not written — 1).

Example (pilots; `human or agent by setting` and the signals — “Agent step”, `machine`, the parse and the signals with data — “Meeting”). The party signals — the column “signals”, the signal fields — in braces; the signals of the enhanced gatekeeper — by the “Pause” library (section 9); the agent's profile is inside `agent_request`, therefore `—`.

```
| name | id | kind | profile | signals | counter |
| agent | agent | agent(result TurnResult) | — | — | agent_attempt |
| gatekeeper | gatekeeper | human or agent by setting elevated_attention_executor(result GateOutcome) | — | allow, deny | gatekeeper_attempt |
| enhanced | enhanced | enhanced(result GateOutcome) | — | continue { human_word str, author str, source str }, halt | enhanced_attempt |

- Request limit: 1

| witness | witness | machine agent_step; parse: parse_witness_reply -> []WitnessAnswer | party_profile("witness") | — | witness_attempt |
| author | author | machine agent_step; parse: parse_author_reply -> EditResult | party_profile("author") | — | author_attempt |
| lens | — | machine agent_step; parse: parse_lens_reply -> LensResult | party_profile(party) | — | lenses[*].attempt |
| gatekeeper | gatekeeper | human or agent by setting elevated_attention_executor(result GateOutcome) | — | repeat, not counted, counted { findings []Finding }, another pass { decision str }, answered { answer str } | gatekeeper_attempt |
| enhanced | enhanced | enhanced(result GateOutcome) | — | continue { human_word str, author str, source str }, halt meeting | enhanced_attempt |

- Request limit: REQUEST_LIMIT
```

## 1a. File language and keywords

The Alula language is bilingual: a file `*.alula.md` is written either in Russian or in English. The Russian form is the base one; all examples of the Russian specification are written in it. The English form is the same constructs with English keywords; the examples of this English version are written in it. An English sample machine is a separate work and does not affect this section.

**Keywords** are the words that the specification defines: the headings of sections and of the header, key lines, table column headings, state kinds, the words of events and of “To”, the words of expressions, actions, catalog functions, the literals `true`/`false`/`none`, the kinds of word parties. They are written **entirely in one language — the language of the file**. Mixing is not allowed: a file with Russian headings and the English action `journal(…)` is an error.

**There are two languages, declared by a header line:** `- language: ru` or `- language: en`. The line is optional, `ru` by default. The parsing rules:

- the check does not guess and does not switch silently: the language is taken only from the `language` line or by default;
- a file with an English header (`# Machine:`, `# Library:`) without `- language: en` is a check error (“the header language is English, and language is not declared”); the same for a Russian header with `- language: en`;
- a keyword not of the file language is a check error with the line number of the first foreign word.

**Free, in any language and mixed** (these are not keywords; mixed — by words, not inside a word): the names that an author invents — data, states, functions, types, fields, party signals, library parameters and their values; prose comments outside tables (4.1); string values inside data and journal event codes (in Latin by convention, rule 34(б)); the names of external functions (as written in the host registry); party identifiers (`agent`, `human`, etc.). The header keys (`machine`, `revision`, `alula_version`, `library`, `language`) are Latin in both languages; the class words of an external function — `volatile` and `acting` (Russian `изменчивая`, `действующая`) — are taken from the word table by the file language (kind `enum_value`, section 7); a pure external function has no class word in the file (the Latin `pure` is a class word of the host registry, not of the machine file).

**JSON.** The machine tree (section 6) does not depend on the file language: the keywords of both languages correspond to the same keys and values, names enter the tree by their JSON names (below), string values (refusal texts, messages, text literals) — as the author wrote them. Therefore files of the two languages with the same JSON names and string values give one tree up to the internal names (below). The sample comparison ([tools/check-alula-samples.py](../tools/check-alula-samples.py)) compares the JSON names of declarations (for the Russian sample — automatic and from `## Names`) and does not compare string values.

**JSON name** — one rule and one place. A JSON name is the name in the machine tree, in the journal, in `all_data` and on the wire. It belongs to a name that an author declares and that leaves the machine: a state (the journal field `state`, the parameter `fork`, `text(State)`), a datum (`all_data`, `machine_data`), an input field, a type, a field of a record and of a form, a form of an enumeration with fields, an enumeration element (the wire, `all_data`), a party signal and its field (the wire, a test), an external function (the JSON name is the host registry name), the name of the gatekeeper setting (a project setting key). The JSON name is a row of the section `## Names` (below), and for a name without a row it **is built automatically**:

1. a Latin name (`[A-Za-z_][A-Za-z0-9_]*`) — the name itself;
2. otherwise, if the glossary (below) names the whole name, — the English name of the glossary (`число_повторов` → `retry_count`, `ПОВТОР` → `Retry`, `Токены` → `TokenUsage`);
3. otherwise — the transliteration of the name by the table below with the case rule (`оставить правку` → `ostavit_pravku`); each word is transliterated separately, a Latin word stays (`запрос_Agent` → `ZaprosAgent` for a type-like name).

**The section `## Names`** (Russian `## Имена`) is **the only way** to set a JSON name other than the automatic one. The table `| name | json_name |` (Russian `| имя | JSON-имя |`): the first column is a name declared in this file (in any language, a Latin one included), the second a Latin JSON name `[A-Za-z_][A-Za-z0-9_]*`. A row sets the JSON name of every declaration with this name in the file; if one name is declared in several places and only some need the JSON name, the first column is a **qualified name**: the path of declared names through dots from the top-level namespace — `Type.field`, `Type.Form`, `Type.Form.field`, `Type.Element`, `party.signal`, `party.signal.field`; a row with a qualified name is stronger than a row with a plain one. A name without a row gets the automatic JSON name. The table lists **only** the names whose automatic name is wrong. Check errors (section 10): a row that changes nothing (its JSON name equals the name the declaration gets without it) — “redundant row”; a row for a name or path that is not among the declarations of this file that leave the machine (an internal name, a readable name, a typo) — “name not declared”; a name repeated in the first column; a non-Latin JSON name; equal JSON names in one namespace (below). An automatic name that did not come out Latin (a sign outside the transliteration table) is an error too: such a name needs a row. **There are no parentheses after names in declarations** (`### ОТКРЫТИЕ — операция`, `| расход | ?РасходТранспорта | …`, `тип Утверждение { … }`): there is one way to write it; parentheses `name (X)` of versions 2.9–2.15 are a check error. The section is written by a machine file and a library — after `## Types` (in a library without `## Types` — after the last of the sections `## Requires …`); each file for its own declarations: an included file defines its JSON names itself. No rows — no section. Not written in `## Names`: a field path `name[*].field` (it is made of declared names); keywords and readable names, including the contract data and the data of the “Pause” library (`reason`, `to_send`, `open_requests`, `previous`, `call_request_id`) and the binding `reason`, — their JSON name is the `en` word of the word table; **internal names** that do not leave the machine — constants, parameters (their external name is `project.<key>`), functions and their parameters, party names (their external name is `id`), event bindings and `let`, lambda parameters, the variable of `for` — enter the tree as written. There are no other ways to set a JSON name.

Example (the “Meeting” sample, Russian form; `Вопрос` is a form of both `ИтогПравки` and `КонтекстРоли`, so the name is qualified; `расход` is from the “Agent step” sample: a plain row sets the name of the datum and of the field of five forms).

```
## Имена

| имя | JSON-имя |
| Утверждение | Claim |
| ИтогПравки.Вопрос | Asked |
| КонтекстРоли.Вопрос | QuestionContext |
| КонтекстРоли.Свидетель.находки | lens_findings |
| оставить правку | keep_edit |
| расход | transport_usage |
```

**Namespaces**. JSON names inside one namespace are distinct; a coincidence is a check error, and one JSON name in different namespaces is allowed. The namespaces: (1) the states of the machine — together with the states of included libraries after substitution (the library names enter the state namespace of the machine); (2) the data of the machine (together with the library data); (3) the input fields; (4) the top-level types — records and enumerations (with fields and without) together; (5) the fields of one record or one form; (6) the forms of one enumeration with fields; (7) the elements of one enumeration; (8) the signals of one party and, separately, the fields of one signal; the common events of the machine (machine signals) are a separate namespace; (9) the external functions of the machine file; (10) parameters, constants and the gatekeeper setting names; functions — each name in its own namespace. (11) **The call namespace**: catalog functions (section 12), author functions and external functions; the name of a function or an external function (as written, the English name by 1a, for an external function also the JSON name) does not coincide with a word of a catalog function in either language nor with `range`, and the names in it are distinct: an author function does not coincide with an external function — otherwise a check error; the exception is the standard external function `новый_ид`/`new_id` (7a): it stands also in the kind `catalog` of the word table (section 12), so a function or an external function with this name is not compared with the catalog words; data, fields and other names are not in it (3.1). Journal codes (`journal("code")`) and the numbers of common events are not in these namespaces.

**Mixed names**. A word of a name — the part between `_` and spaces — is written in the letters of one script: Cyrillic only or Latin only; digits are allowed in any word (`В3`, `v2`). A word that mixes Cyrillic and Latin (`ЗапросAgent`, `ХодV2`) is a check error: such a word has no unambiguous boundary for transliteration and case. Mixing is allowed only between words, through `_` or a space (`запрос_Agent`, `ход_v2`): each word is transliterated separately, a Latin word stays as it is (step 3).

**The glossary for names** is the methodology glossary of English names [state-machine-glossary.md](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-glossary.md) (version 11). Only its part “Russian name → English name” is normative for names: the rows of the tables of sections 2.1–2.9, 2.11, 2.12 and 2.16 (the first column is the Russian name, the second the English one, both in backquotes) and the records `` `Russian` → `English` `` of section 2.10. The lookup is by the whole name, by an exact match of the string (with case, underscores and spaces). **Caution:** the lookup is by the whole name regardless of the kind of the name, so the automatic name is Latin but may be not the intended one (the type `Утверждение` gives `Approval`, a state `ИТОГ` gives `Totals`, a field `ошибка` gives `failure_error`); for a machine with an English twin the sample comparison finds the difference, otherwise the author checks the name and writes a `## Names` row where needed. Not included: the string literals (2.14), the context exceptions (2.15), the conventions, notes and history; a name to which these tables give two different English names (there is one — `расход`: `usage` and `transport_usage`) has no record: its JSON name is built by transliteration, and the wanted one is written in `## Names`.

**The glossary hash**. The normative part of the glossary is pinned by a hash, not by a version number. The text for the hash: the pairs of the normative part in file order (the rows of the tables of sections 2.1–2.9, 2.11, 2.12, 2.16 — by the first two columns; the records of section 2.10 — in their order in the line), each one is a line `Russian → English` (the Russian name, a space, the sign `→`, a space, the English name, without backquotes), the lines are joined by LF (`\n`), there is no LF after the last one, the encoding is UTF-8; the hash is the first 12 signs of the SHA-256 of this text, in lower case. Format 0.27 pins the **glossary hash `35c571ccda17`** of version 13 (2.16–2.23 had `60383c370415` for glossary version 11: in version 13 three functions by role replaced `parse_agent_reply`). The check ([tools/check-alula-keywords.py](../tools/check-alula-keywords.py)) recomputes the hash from the glossary file; another hash is the error “the glossary changed without a format change”: a new or changed pair changes automatic names, and the same machine would give another tree. The format version and the hash change only together; an edit outside the normative part (the literals 2.14, the exceptions 2.15, the columns “Where”, “Source”, “Note”, the conventions, the history) does not change the hash and needs no new format. The version number in the glossary header is for people. An “Alula → JSON” translator needs a copy of the normative part with the same hash.

**Transliteration**: a Cyrillic letter (lower or upper case) is replaced by Latin by the table; Latin letters, digits, `_` and a space stay, the case is by the rule below; a word that mixes Cyrillic and Latin is an error (above).

| Letter | Latin | Letter | Latin | Letter | Latin |
|---|---|---|---|---|---|
| а | a | б | b | в | v |
| г | g | д | d | е | e |
| ё | e | ж | zh | з | z |
| и | i | й | y | к | k |
| л | l | м | m | н | n |
| о | o | п | p | р | r |
| с | s | т | t | у | u |
| ф | f | х | kh | ц | ts |
| ч | ch | ш | sh | щ | shch |
| ъ | — (dropped) | ы | y | ь | — (dropped) |
| э | e | ю | yu | я | ya |

**Case** of the transliteration (step 3). The words of a name are separated by `_` or a space; `_` and spaces at the start, at the end and in a row give no empty words and do not pass into the name (`_ход__агента` → `khod_agenta`). **Type-like names** — a state, a type, a form of an enumeration with fields, an enumeration element — are written together, each word with a capital letter (`PascalCase`): in a word written without lower-case letters (`ХОД`, `В3`) all letters but the first first become lower-case; a capital Cyrillic letter gives Latin with a capital first letter (`Ж` → `Zh`, `Щ` → `Shch`); the first letter of every word is capital: `ХОД_АГЕНТА` → `KhodAgenta`, `ВидВызывающего` → `VidVyzyvayushchego`, `НетОтветаВСрок` → `NetOtvetaVSrok`. **Value-like names** — a datum, an input field, a field of a record and of a form, a party signal and its field, an external function, the name of the gatekeeper setting — are written in lower case, the words through `_` (`snake_case`): `оставить правку` → `ostavit_pravku`, `находки_В3` → `nakhodki_v3` (if there were no glossary). The rule is taken from the samples and convention 1 of the glossary: types and forms are `PascalCase`, fields, data and functions are `snake_case`.

**The word table is the single normative source:** [alula-keywords.tsv](alula-keywords.tsv). Rows `kind`, `ru`, `en` (tab), the first row is the heading; the word kind (`kind`) is from a closed list:

| `kind` | Words |
|---|---|
| `header` | header words: `Machine`, `Library` and the header keys |
| `section` | headings of `##` sections (including `Requires data`, `Requires parties`, `Requires ends`, `Engine data`, `Party events`, `Common events` of a library file) |
| `column` | table column headings |
| `kind_state` | state kinds: appeal, operation, fork, end |
| `key` | key lines (`Party`, `Request`, `Edits`, `check`, `set`, `Except`, etc.), the words of an include (`File`, `Name`, `Hash`), the prefix `project` |
| `kind_party` | party kinds and the words of their record (`parse`, `result`, `input`, `human or agent by setting`) |
| `event` | event words (`response`, `failure`, `signal`, `part`, `timeout`), `reason`, `else` |
| `destination` | the words of “To”: `previous`, `preparation_return`, `same`, the suffix `rerun` |
| `decl` | declaration words: `type`, `enum` (the kind word after the type name), `fn` |
| `type` | type words and built-in types (section 2) |
| `expr` | expression words, literals, the constructors `Response`, `Refusal` |
| `operator` | ASCII operators and signs: one spelling in both languages, `ru` and `en` coincide, except the membership sign: Russian `в`, English `in` |
| `action` | action words and their arguments (including `for`) |
| `readable` | engine readable names, contract data and the binding `reason` |
| `enum_value` | `yes` of the column “non_decreasing”, the values of `Signal`, the class words of external functions (`volatile`, `acting`; `pure` is a class word of the host registry) |
| `catalog` | catalog functions (section 12) |

A word that fits two kinds is written as two rows (`else` — in `event`, `expr`, `action`; `end` — in `kind_state` and `catalog`). Within a kind the `ru` words do not repeat and the `en` words do not repeat: a word that is the same in the English form for two Russian words belongs to different kinds. Parsing reads a word by the `kind` of the position and the file language. The check of the table and of the sample is [tools/check-alula-keywords.py](../tools/check-alula-keywords.py) (section 10).

**Operators and signs — ASCII only**. The signs are written the same in both languages (the kind `operator` of the word table: `ru` and `en` coincide), except the membership sign: the Russian word `в`, the English `in`; there are no other spellings:

| Sign | Where |
|---|---|
| `>=` | comparison; the type bound `int>=n` (Russian `число>=n`) |
| `<=` | comparison; `yes, <= expr` of the column “non_decreasing” |
| `!=` | comparison |
| `->` | the result type `-> Type`: a function header, `parse: external function -> Type` of a party `machine`, the catalog signatures and the function type of a lambda parameter `fn(T) -> R` in them (section 12) |
| `=>` | the body of a function of one expression `-> Type => expr` (a block body `-> Type { … }` is without `=>`), a `match` branch, a lambda |
| `...` | the spread `{ ...expr, field: expr }` |
| `..` | the range `a..b` — half-open `[a, b)`; `..` after a number or a name is the range sign, not a part of a fractional literal: `1..n` is `1`, `..`, `n` |
| `..=` | the inclusive range `a..=b` — `a..(b + 1)`; written without spaces; the longest match is `...`, then `..=`, then `..` |
| `in` (Russian `в`) | `failure(reason in […])`, `stop_reason in […]` (“when” of ends, `Except`); the set is a list literal `[…]` |
| `??`, `_` | a default value; an unneeded lambda parameter |

The ellipsis `…` in the grammar description (3.1) and in the text of the specification is a meta-sign of omission, not a sign of the language.

**English record of types and signs.** `число`→`int`, `число>=n`→`int>=n`, `вещественное`→`f64`, `строка`→`str`, `булево`→`bool` (the words of Nova), `словарь[K, V]`→`map[K, V]` (in JSON a map is `{K: V}`; types have no synonyms, `HashMap[K, V]` is not accepted), `полный словарь[K, V]`→`full map[K, V]`, `ид`→`id`; `?T`, `[]T`, the tuple `(T1, T2)`, `—` is the same in both languages (operators — above); the value “nothing” is `none` (the literal `пусто`), the type “nothing” in JSON is `nothing`; the catalog functions `строка(x)`, `вещественное(x)`, `число(x)` are `text(x)`, `float(x)`, `int(x)` (section 12; their words do not change); in the tree the types are named by the words `int`, `text`, `float`, `bool` (section 6). For example, `выбор … { альт | альт если выр => выр, иначе => выр }` is `match … { alt | alt if expr => expr, else => expr }`, `для x из xs { … }` is `for x in xs { … }`, `ответ: Форма { … }` is `response: Form { … }`, `засчитан { находки []Находка }` is `counted { findings []Finding }`, `Вар { поле, поле: имя } =>` is `Var { field, field: name } =>`, `сбой(причина в […])` is `failure(reason in […])`, `xs.фильтр(x => выр)` is `xs.filter(x => expr)`, `функция f(x число) -> число { … }` is `fn f(x int) -> int { … }`; the map literal `[k: v]` and `a..=b` are the same in both languages.

## 1b. Canonical form (recommended for generators)

A “tree → file” generator (the reverse conversion of the JSON of the machine tree to Alula) is bound by one thing: the text it writes translates back to a tree equal to the original — the cycle “md → JSON → md → JSON” gives an equal tree. The rules of this section are the **recommended** canonical form of such a text: with it the result is predictable, and two generators write one text; a generator that writes otherwise does not break the requirement if the tree is equal. The reverse conversion loses comment paragraphs, formatting (alignment, line breaks inside declarations) and the names that are not in the tree (the tree holds one JSON name, automatic or from `## Names`, 1a); the meaning is not lost. A file written by a person in another way (the order of key lines, prose, line breaks) stays valid — parsing accepts it.

- **(а) Header.** `# Machine: <Name>` (the Russian form — `# Машина: <Имя>`), where `<Name>` is the Latin name of the machine (`machine` of the tree); an empty line; a list of four items in this order: `- machine: <name>`, `- revision: <number>`, `- alula_version: <version>`, `- language: <ru|en>`; the line `language` is always written, the default is not used. `revision` is `revision` of the tree (the revision of the machine itself: an integer, `1` by default; not the language version); `alula_version` is the version of the Alula language in which the source was written (the root key `alula_version` of the tree, section 6; if it is absent — the language version of the generator).
- **(б) Sections.** The sections of section 1 in order — `## Types`, `## Constants`, `## Parameters`, `## Input`, `## Data`, `## Parties`, `## Includes`, `## External functions`, `## Functions`, `## States`, `## Output` — are written once each and only non-empty: an empty section is not written; the optional section `## Names` (1a) stands after `## Types` and is written only if it has rows; one empty line between sections. The key lines of sections are list items: `- Invariant: <expression>` (one per invariant) — after the `## Input` table; `- Request limit: <expression>` (if `request_limit` is set in the tree) — after the `## Parties` table; `- Result: <Type>` — before the `## Output` table.
- **(в) States.** The first line of `## States` is `Initial state: NAME` (the Russian form — `Начальное состояние: ИМЯ`), not a list item, then an empty line; states are in the order of `states` of the tree. The key lines of a state are list items, one after another, in this order: `Party`, `Idle term`, `Edits`, `Form returns`, `Request`, `On accept`, `On entry`, `Except` (the Russian ones — `Сторона`, `Срок тишины`, `Правит`, `Возвратов формы`, `Запрос`, `При приёме`, `При входе`, `Кроме`); a key the state does not have or whose value is empty is not written; a key with a real default value (`Idle term: 0`, `Form returns: 0`) may be written by the generator. An item with a table (`Request:` of an appeal, `On accept:`) stands before its table, and an empty line stands between a table and the next block; the body of “On entry” of several actions is a nested list, one action per item (4.1).
- **(г) Tables.** The header and the rows have one space on each side of `|`, with no alignment of column widths; the separator row is `|---|` by the number of columns; an empty cell is two spaces between `|` (`|  |`; in the transition rows and in the `Request` the “no condition”, “no actions” and “the same name” are written only so, `—` there is an error; in the tables of “Parameters”, “Data” and “Parties” the sign “no value” stays `—` — a deliberate exception: an empty cell would be lost there, as the column `counter` of a party with free input, section 1); `|` inside a cell is `\|`. In the `Request` table an expression equal to the field name is written as an empty cell. The actions in a cell are in the order of the tree, joined by `<br>` (for two actions `; ` is allowed); blocks are in braces with a space inside: the branches of a conditional action `if expr then { a; b } else { c }`, of a conditional expression `if expr then { expr } else { expr }`, the body `for x in xs { a; b }`, an action block `{ let l = expr; a }`; an event pattern is `response: Var { field, field: name }`, a signal with fields is `signal(s { field })`; the declaration of a signal with fields in the column “signals” is `s { field type, field type }`, a signal without fields — by name. The words of the column headings come from the word table of the file language.
- **(д) Declarations.** Types, functions and external functions are written in code blocks under `## Types`, `## Functions` and `## External functions`, in the order of the tree, **one declaration per line**: `name(parameter type) [class] [-> Type]` (without a body), `type Name enum A | B`, with values — the header `type Name enum` and the lines `| El = "value"`, `type Name { field type, field type }`, `fn name(parameter type) -> Type =>` and the body of the function on the next line with an indent of two spaces (as one line); a block body: `{` at the end of the header without `=>` (`fn name(parameter type) -> Type {`), the bindings `let name = expr;` and the last expression — one per line with an indent of two spaces, `}` — on its own line. An enumeration (as D406 of Nova): on one line — `type Name enum A | B`, only if all forms are bare names (without values and fields) and the line is not longer than 100 signs; otherwise on several lines — the header line `type Name enum`, then one form per line with an indent of two spaces: `  | El`, `  | El = "value"`, `  | Var { field type, field type }`; the generator writes no empty lines and no comments between forms (parsing allows them, section 2). A `match` alternative on a form with fields is `Var { field, field: name } =>`. In a `## Types` block empty lines between declarations are not required and are not written by the generator (parsing allows them; the samples separate groups of declarations by an empty line); between functions — one empty line.
- **(е) Operators.** ASCII only in both languages: `->` before a result type; `=>` before the body of a function of one expression (a block body is without `=>`), in `match` branches and in lambdas; `>=`, `<=`, `!=`, `==` in comparisons; `...` in a spread; `..` in a range `a..b`, `..=` in an inclusive range `a..=b`; `match` branches — through `, ` on one line, by a line break in a multi-line `match`: the generator writes `match` on one line when it fits — the line where `match` stands is not longer than 100 characters from its start to its end and no branch has a block `=> { … }`; otherwise multi-line: `{` at the end of the header line, each branch on its own line indented two spaces more than the header line, without a comma at the end, `}` on its own line at the indent of the header line; in a table cell `match` is always one-line; the map literal `[k: v, k: v]`, an empty map is `[]`; `in` (Russian `в`) with a list literal in `failure(reason in […])`, “when” and `Except`; a catalog list function as a list method `xs.filter(x => expr)`; `int>=n` (`число>=n`); `yes, <= expr` (`да, <= выр`). The signs are in the word table, the kind `operator` (1a).
- **(ж) Names.** The generator writes every name as it lies in the tree: for a name with a JSON name only the JSON name lies in the tree; internal names lie as written; so such a generator writes no section `## Names` (1a) — `### Retry — fork`, `| retry_count | int>=0 | …`; a generator that writes other names (for example the author's preserved Russian names) writes `## Names` for every name whose automatic name is not the JSON name of the tree, and only for them; the same state name stands in `Initial state` and in the “To” column. The kinds are the words `appeal`, `operation`, `fork`, `end` (the Russian ones — `обращение`, `операция`, `развилка`, `конец`).
- **(з) File language.** The generator chooses the language by a parameter (`ru` or `en`); all keywords come from [alula-keywords.tsv](alula-keywords.tsv) by this language (1a), with no mixing; the names invented by an author (data, types, fields, functions) and the enumeration values are carried over from the tree as they are.
- **(и) String values and journal codes** are carried over as they are, with no translation or normalization; a string literal is in double quotes, inside are escaped `"` (`\"`), `\` (`\\`), `$` before `{` (`\$`), a line feed, a tab, a carriage return and the null sign (`\n`, `\t`, `\r`, `\0`), other control signs — `\u{HEX}` (a closed list). A number — by a decimal record: an integer without `_`, a float — by the record of `text(x)` (3.3; `1e-7`, `1.5e20`); the generator does not write `//` comments. A call `concat(…)` all of whose arguments are non-empty text literals and calls `text(x)`, with no two literals in a row, is recommended to be written by the generator as an insertion (`concat("turn ", text(n))` is `"turn ${n}"`), another call `concat` as a call; `text(x)` as a call; the requirement is one — an equal tree.
- **(к) Prose.** Comments and prose are not generated. It is allowed to write `title` of the tree, if there is one, as one paragraph under the header (after the header list); nothing more.
- **(л) The file** ends with exactly one line feed (no empty lines at the end), encoding UTF-8 without BOM, line endings LF.
- **(м) Includes.** The tree carries a library already substituted (section 9) and an include node with the instance name, the hash and the parameters (section 6). The generator writes an include in `## Includes` as a subheading `### Name` (the instance name), the key lines `- File:` and `- Hash:` (and `- Name:` only if the instance name differs from the library name) and the table `| parameter | value |` with all the parameters, in the order of the table `## Parameters` of the library (section 9): `### Pause`, `- File: libs/pause.alula.md`, `- Hash: …`, the table row `| halt_signal | "halt" |`, …; a record in one line of the form `Pause(…)` is the old form, an error (section 10). The generator does not write the states, data and common events of the library as its own: a repetition would be “declared twice”, and without the include record the values of the parameters (`request_cancel`, `reentry`) would be lost — they are not expressed by substitution into the text, their effect lies on `cancel_open` and `To: previous`. A library of functions, types and constants: the tree carries both the reference (`includes`) and a copy of its types, constants and functions (section 6); the generator writes either the include (and then does not write the copies) or the copies (and then there is no include) — otherwise the names are declared twice (section 8); the choice is a generator parameter, by default the include.

The samples [spec/samples/agent-step.alula.md](samples/agent-step.alula.md) and [spec/samples/agent-step.en.alula.md](samples/agent-step.en.alula.md) are written by a person and are not brought to the recommended form: they carry prose (к), includes of libraries with comments (м), line breaks inside declarations and multi-line bodies of functions (д); the Russian sample, besides, has Russian names whose JSON names are built automatically, with the section `## Имена` where the automatic name is wrong (ж), and has no `language` line (а). The rest (the header, the order of sections and key lines, tables, operators) corresponds in the samples to the canonical form. The cycle “md → JSON → md → JSON” is checked by the consumer product; the methodology scripts do not check the canonical form (see the [changelog](alula-changelog.en.md), “Open items”).

## 2. Types and data

| Type | Record | Notes |
|---|---|---|
| integer | `int`; `int>=n` (n is an integer literal: `int>=0`, `int>=1`) | a signed 64-bit integer (i64); `int>=n` is the same with the lower bound n; going outside the bound, like overflow, is a machine error; `int>=n` and `int` are compatible both ways (the bound at assignment is checked by the engine), also when the input type of a nested machine is compared (section 1) |
| float | `f64` | a double-precision IEEE 754 floating-point number (f64); not mixed with int: `float(x)`, `int(x)` are explicit; the format does not express bounds for `f64` (the source “non-negative” remains in the description, the engine does not check the bound) |
| text | `str` | comparison letter by letter |
| literal set | `"first" \| "retry" \| "continue"` — two or more text literals; optional — `?("first" \| "retry")` | a closed set of text values; allowed **wherever a type is expected**: the cell “type” of the tables “Input”, “Parameters”, “Data”, a type argument (`map[str, "allow" \| "deny" \| "ask"]`, `full map[ActionKind, "allow" \| "deny"]`), the result and the parameter of a function (`fn decision(…) -> "allow" \| "deny" =>`); the parentheses are required under `?` and `[]`, in other positions they are optional and allowed when ambiguous; in a table cell `\|` (section 1); assigning a value outside the set is a table check error; a `match` over a set is exhausted by the rules of enumerations (all values are named or there is `else`); `text(x)` gives the literal itself; in the JSON schema — a list of strings |
| identifier | `id` | a built-in type: text of UUID format; details below |
| boolean | `bool` | |
| optional | `?T` | `?` and `[]` apply to the whole type on the right; a literal set under them is written in parentheses: `?("allow" \| "deny")`, `[]("a" \| "b")`; the record `?"a" \| "b"` is not defined |
| list, map | `[]T`, `map[K, V]` | key: text, int, enumeration, tuple or a record of such (structural equality); **the traversal order of a map** (`keys`, `values`, the encoding of `all_data`) is the order of writing the keys: a new key goes to the end, replacing the value of an existing key does not change the order, `without_key` removes the key (writing the same key again afterwards puts it at the end); the order is visible in `keys`, `values` and the text of a record, but the equality `==` of maps does not take the order into account; **a repeated key is an error**: constant keys of a literal — a check error (parsing), keys that became equal when evaluated and a repeat in `xs.dict(…)` — the machine error `duplicate_key` (3.3) |
| full map | `full map[K, V]` | `K` is an enumeration: the keys are all its values, indexing gives `V`, not `?V`; an incomplete literal or a project override is a check error |
| tuple | `(T1, T2, …)` — from two fields | an anonymous record with positional fields; the value `(a, b)`, the field `t.0`, `t.1` (from zero, as in Nova) |
| record | `type Name { field T, … }` | |
| enumeration, also with fields at its forms (an enumeration with fields) | `type Name enum A \| B` — only bare names, the line not longer than 100 signs; with values or fields — the header `type Name enum`, then a line per form started with `\|`: `\| El = "value"`, `\| Var { field T, … }`, `\| Var`; empty lines and comment lines `//` are allowed between forms and between the header and the first form, the indent of the form lines is free; an enumeration ends at the first line that is not a form `\|`, not empty and not a comment; a `## Types` block holds only declarations, so such a line is the next declaration (as D406 of Nova) | an element is a name (`El`) and an optional **value** — a text in quotes after `=`; a type has either values at the elements or fields at the forms — a mix is a check error; a **form** is one alternative of an enumeration (a line `\|` or a name between `\|`), a form of an enumeration without fields is an element; an enumeration that has fields at least at one form is an **enumeration with fields**, its form without fields is written `Var` without braces; `text(Name.El)` gives the value; `text` of an enumeration without values is forbidden; values may be given not for all elements; an element without a value enters a data record (section 5) by its JSON name (1a) |
| state | `State` | a built-in enumeration of the machine's state names (a literal is a state name); the text is the JSON name of the state (1a); the type `State` holds only state names (the readable name `state` is the current state); everything the instance saves (the current state, the data, the event queue, the open and accepted requests, the open gates, the attempt counters) is the engine's internal record (rule 22): as a whole it is not available in expressions, the data are read by their names (“Lifetime of data”) |
| signal | `Signal` | a built-in enumeration `stop`, `continue`, `halt`, `cancel`; `Signal` is a kind of event: a control signal to the machine (common events, section 9); party signals (`allow`, `counted` …) are another thing: they are declared at the party in the column “signals” (section 1) and arrive at gates |
| journal event | `JournalEvent` | a record `{ code str, params []Param }`, where `Param` is a tuple `(str, str)`: name, value |
| gate outcome | `GateOutcome` | a built-in enumeration with fields, the result of the parties `human`, `enhanced`, the gatekeeper: its forms are the signals of the party's column “signals” (section 1) |

**Case**: built-in word types and types with arguments are written in lower case (`int`, `str`, `id`, `map`), built-in and author-declared named types — with a capital letter (`State`, `Signal`, `AgentRequest`); `signal` (an event word of a party) and `Signal` (a type — a machine signal) are different words.

**Literal set or enumeration**. A literal set — when the set is small, local to one machine, the values are not needed by the journal as enumeration values and do not cross the machine boundary (`turn`, `stop_reason` of “Agent step” — so in the source). An enumeration with values (`type Name enum` and the lines `| El = "value"`) — when the set is common to several machines or libraries, crosses the call boundary (input, response, failure code — `FailCode`), the values are needed for the journal and `text(x)`, or the elements have fields (then it is an enumeration with fields). **The values of a set** are any text, including Cyrillic and a space (`"наблюдалось" | "не наблюдалось" | "вывод"` — the words of a role artifact): rule 34(б) allows Latin in the text literals of closed sets but does not require it; the values are written as in the source (the words of the automaton code — in Latin, the words of an artifact — as in the artifact). The restriction `[a-z][a-z0-9_]*` applies only to the values of an enumeration.

**The type `id`**. Text of UUID format: 8-4-4-4-12 hexadecimal signs through hyphens, lowercase (`0192f3a0-7c1e-7b2a-9d4e-5a6b7c8d9e0f`). The check is at data load and at input parsing: a violation of the input is the refusal `input_rejected`, `reason=type`, `field` is the field name (section 1); a violation of data is a load error by the format rules. The format does not fix the UUID version; for the identifiers of sessions, host requests and runs version 7 is preferable (by time, sortable). `id` is assigned to a datum and a parameter of type `str` (the type is forgotten, as with a literal set); the reverse — only a literal of UUID format. `==` is structural, `text(x)` gives the text itself. The value is issued by the standard external function `new_id` (sections 7, 7a). **Not changed:** the request identifier `<party>-<attempt>` (rule 15, [call protocol](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-call-protocol.md)) and the trace envelope (`trace`, `step`, rule 31) remain as in the specification — `id` serves the data of machines (identifiers of sessions, runs, etc.), not the envelope.

**Enumeration values**. Values may be given not for all elements; a value is `[a-z][a-z0-9_]*`. An element without a value is shown in `text(x)` and in `all_data` by its JSON name (1a): in the file the element name is in the file language, in the tree, in `machine_data` and `all_data` it is the JSON name; the `machine_data` comparison goes by the JSON name (for `FailCode` — by the value, as in the engine).

**The declaration notation is as in Nova** (decision of the owner, 2026-10-19): a declaration is `name type` through a space (a field of a record and of a form, a parameter of a function and of a catalog function, a parameter of a party signature and a signal field, a registry parameter); the result is after `->`, the body of a function is after `=>` or a block `{ … }`. A colon stands only in a record literal `Type { field: expr }`, in a named argument of the journal forms `name: expr` (3.1), in a map literal pair `[k: v]` and in a pattern field binding `field: name` (4.3). The sign `=` in a declaration stands only at the value of an enumeration element `El = "value"`, there is none after the type name. **Brackets**: the fields of a record, a form and a party signal are in braces (`type Name { field T }`, `Var { field T }`, `counted { findings []Finding }`), and so are an event pattern and a `match` alternative (`Var { field, field: name }`); the parameters of a function, a catalog function, a party signature and a registry entry are in parentheses (`fn name(p T)`, `agent(result Type)`): parentheses after a name are a function, braces are the fields of a record or a form. Tables with a separate column “type” (`## Input`, `## Parameters`, `## Data`) do not change. **Declarations only in a code block**: `type` (including an enumeration `type Name enum …`), `fn` and the declaration of an external function are written inside a code block (``` fences) under `## Types`, `## Functions` and `## External functions`; a declaration line outside a code block is a comment (a paragraph) and a check warning: markdown would distort `|`, `{}`, `->`.

**A style rule: the name of a field does not coincide with the name of its type** (a recommendation, not a check error). The rule covers the fields of records and forms and the machine data (the “Data” table). A field names the role of the value in the record, a type — the kind of the value: `tokens Tokens`, `check Check` read as a repeat and do not say what the field is for; better `reply str`, `token_usage Tokens`. A coincidence is the equality of the field name and the name of its type ignoring case, after removing `?` and `[]` (`check ?Check` is a coincidence). The field names of the samples (“Agent step”, “Meeting”) are not changed: they are names of the tree and code of the consumer product, a renaming would break them. A check warning — later (see the [changelog](alula-changelog.en.md), “Open items”).

**Type records and Nova** (checked against the language specification and the automata code): as in Nova — `[]T`, the tuple `(T1, T2)` (in a type position), `map[K, V]` (in Nova `HashMap[K, V]`; the literal `[k: v]` as in Nova), the record `type Name { field T }`, the enumeration `type Name enum A | B`, with values and fields at the forms — on several lines with `|` (as `type Name enum …` of Nova, D406; in Nova a value is an integer `El = 0`); the translation of names — `int`, `str`, `f64`, `bool` (as in Nova). **Extensions of the format** that Nova does not have: `?T` (in Nova `Option[T]`), `int>=n`, the literal set `"a" | "b"`, `id`, `full map[K, V]`; the other differences are in the list “Open items” of the [changelog](alula-changelog.en.md).

Example (the “Agent step” pilot; the codes of `FailCode` are declared in the library `contract`, 7a, and are not repeated in a machine; a product adds its own codes by a separate enumeration of its library — the first declaration below, the values for the journal as in `fail_code_word` of the engine).

```
type ProductFailCode enum
  | QuotaExhausted = "quota_exhausted"
  | TransportUnavailable = "transport_unavailable"

type TurnResult enum
  | Finished { text ?str, artifact ?str, usage TransportUsage }
  | Truncated { usage TransportUsage }
  | TurnRequestLimit { usage TransportUsage }
  | ModelRefusal { usage TransportUsage }
  | Stopped { usage TransportUsage }
  | TransientError
  | PermanentError
  | NeedsPermission { permission_request PermissionRequest }
```

**Data.** The table `| name | type | initial | non_decreasing |` (the column `non_decreasing` may be omitted).

- `name` is a datum or a **field path** inside a map: `name[*].field` (`*` is any key; for a nested one `name[*].field.field`). A row with a path carries only `non_decreasing` and acts on every value of the map; `type` is the field type, `initial` is `—` (the value is set by the row of the datum itself).
- `initial` is an expression or `input.<field>`.
- `non_decreasing` is `—`, `yes` or `yes, <= expr`; the expression may be any expression over constants, parameters and the input (`max(1, limit)`); the bound is checked by the engine after the transition (for a path — at the write; a violation is a machine error). If the bound in the primary source is wrong for some values, it is not written.
- **Writes into data.** Data are changed by the actions of the machine tables (the row actions, the “On accept” block, acting functions called from the tables) and by included libraries (section 9); the table has no mark for it. Data that only the engine writes — the party attempt counters (the column `counter` of “Parties”, section 1), `open_requests`, `call_request_id` — are declared in the library `contract` (section 9); a write into them from table rows, “On accept” and acting functions is a check error. A datum written by both the actions and the engine (`to_send`) may be written from the tables.
- **Contract data** enter `all_data`: `open_requests` (`[]str`, initial `[]`) and `call_request_id` are declared in the library `contract` (section 9), their rows are not written in the machine table, and a repeated declaration is a name conflict (rule 36), a check error; they are read by `pass` and `cancel_open`; `to_send` (`[]str`) is declared by the machine with an ordinary row: the row actions write it (Lock, LensRefusal), the engine moves the parties to `open_requests` (rule 21); the party attempt counter is a datum made by the loader from the column `counter` of “Parties” (section 1).
- **The composition of `all_data`**: **every** datum named in the `## Data` tables of the machine and of the included libraries, and the contract data (the previous item); a field path is inside its datum. The sign is one and is checked by the tables: named in a table — included; there are no exceptions among the named. Therefore data that the source relates to external objects and the assignment are also included (for “Meeting” `proposal`, `copy`, `copy_fingerprint`, `witness_answers`, `lens_findings`, `summary`, `archive`, `author_question`, `lens_order`), and the copy of the input (`agent_request` of “Agent step”): the primary source gives for ERROR “all variables and stores”, rule 11 of the specification — “all data of the machine”. Only what is not in the tables is not included: engine data and the envelope (`state`, `trace`, `step`, `event_counter`, `cause`, `accepted_requests`, the journal) and the stores of rule 31 (`human_words`, `failure_texts`; a human's word and a failure text are not written to the journal in full). Encoding — section 5.

Example (pilots; the bounds are as in the pilots).

```
| name | type | initial | non_decreasing |
| agent_request | AgentRequest | AgentRequest { kind: input.kind, profile: input.profile, session: input.session, dialog_kind: input.dialog_kind, context: input.context, limits: input.limits, trace: input.trace, step: input.step } | — |
| turn | "first" \| "retry" \| "continue" \| "fix" \| "permission" | "first" | — |
| retry_count | int>=0 | 0 | yes, <= RETRIES |
| turn_count | int>=0 | 0 | yes |
| turn_before_retry | ?("first" \| "retry" \| "continue" \| "fix" \| "permission") | none | — |
| stop_reason | "" \| "no_result" \| "max_tokens" | "" | — |
| number | int>=1 | 1 | yes |
| lenses | map[str, Lens] | input.lens_order.dict(l => l, l => Lens { id: l, lost: 0, probes: 0, attempt: 0 }) | — |
| witness_answers | map[int>=0, []WitnessAnswer] | [] | — |
```
(The types `turn`, `turn_before_retry`, `stop_reason` are literal sets. The first six rows are “Agent step”, the rest are “Meeting”; `agent_request` is built by a constructor from the input fields (section 1); `open_requests` is declared by the library `contract`, its row is not written in the machine table. In `stop_reason` a part of the set is shown; the full set of the pilot is ten values. `turn_count` has no `<=` bound: with a turn limit below 1 the code gives 1. `number` is `int>=1`: in the code `Cycle.new()` and `MachineData.new()` give 1, it changes only by `+= 1` (the invariant “does not decrease”); `number - 1` is `int`, 3.2. The row `lenses` changes `lost` and `probes`, `attempt` is a party counter (section 1) written only by the engine: the record `lenses[k] = { ...l, field: expr }` that does not name `attempt` is a copy, not a write into it.)

### Lifetime of data

A summary of what is said in sections 1–5, 7–9 and in rules 4, 12, 13, 14, 19, 22, 31 of the [specification](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-spec.md); there are no new rules.

| Names | How long they live | Who sets and changes them |
|---|---|---|
| **machine data**: the rows of `## Data` of the machine and of the included libraries (library data enter the host machine, section 9), the contract data `open_requests`, `call_request_id`, `to_send`, the attempt counters of the parties (section 1) | the whole machine instance: the `initial` value (an expression or `input.<field>`) — at start; saved together with the machine state, they survive a pause and a restart (rule 22) | the actions of the machine tables and of included libraries; engine data (the party attempt counters, `open_requests`, `call_request_id`) only by the engine, a write into them from the tables is a check error; the `non_decreasing` bound is checked after the transition, for a path — at the write; the changes of a step are one commit, an unfinished step is rolled back (rule 13) |
| **engine data in the machine state**: `state`, `accepted_requests`, the event queue (rule 13) with accepted responses and words (rule 14), the records of open gates and their “accepted” marks (rules 13, 19), `step` and `event_counter` (rule 31) | the whole instance; saved together with the state, they survive a pause and a restart (rules 13, 22, 31) | only the mechanics; they are not written in `## Data` and do not enter `all_data` (above) |
| **the envelope** (rule 31): `trace`, `cause` | `trace` — the whole run: assigned at start, does not change; `cause` — one step (the identifier of the event the step started with) | the engine; `trace` and `step` are read only in the “Request” of a party `machine` (3.1) |
| **the journal and the stores of rule 31** (`human_words`, `failure_texts`) | external objects (rule 4): journal lines are written in the commit of a step (rule 13), a human's word and a failure text — at acceptance (rules 14, 31); the format does not set how long they are kept | the engine; neither a step nor a role reads the stores (rule 31); they do not enter `all_data` (above) |
| `input`, constants, parameters (sections 1, 8) | the whole instance | do not change: `input` is the input of the call, a parameter is the default value or the project override at load |
| `event.<field>`, the event field bindings (`response(name)`, `response: Form { field: name }`, `signal(s { field: name })`), `reason`, `party` of a set event (3.1, 4.3) | one step: the event row and the chain of operations and forks up to the next appeal or end (rule 13), and also the “On accept” block (4.4: a separate commit before the step, rule 14); after the step there is no event | the engine when it accepts the event; a binding named as a datum is an error (4.3) |
| `let` in “On entry” of an operation, a fork and an end (4.5–4.7) | one entry into the state: visible further in “On entry” and in all rows of the state. Re-entry happens only into an appeal and an end (rules 12, 22): for an end the binding is computed anew, for an appeal the “Request” is computed anew (4.2, section 7). An operation and a fork are not re-entered: an unfinished step is rolled back (rule 12); a nondeterministic value — `event.at` in Start (4.5) and `new_id()` (section 7) — is taken from the record of the step, saved together with the step, when the step is repeated (section 7, rules 12, 13) | the binding expression |
| `let` in “On accept” (4.4) | saved with the accepted event, that is, with the queue (rule 14); visible to the row of that event and its chain | the binding expression |
| `let` in a block `{ … }` (of actions or of an expression), a lambda parameter, the name of `for` (3.1, 5) | its own scope: the block up to the closing `}`, the lambda body, the loop body | — |

**Data “in memory”.** Rule 22 divides variables into those saved together with the state and variables “in memory”, which are lost on a restart; a machine with them enters after a restart not the “state” again but the start of the pass named in its “Terms”. In Alula a datum cannot be marked as “in memory”, and there is no “Terms” section and no start of a pass in a machine file: every `## Data` datum is saved with the state, and an Alula machine after a restart always re-enters the “state” (rule 12). The decision is in the section “Open items” of the [changelog](alula-changelog.en.md).

## 3. Expressions

The words of expressions (`if`, `then`, `else`, `and`, `or`, `not`, `let`, `match`, `true`, `false`, `none`, `unreachable`) and the readable names are quoted in the English form; the Russian form is in the [word table](alula-keywords.tsv), the kinds `expr` and `readable` (1a).

### 3.1 Grammar

```
expr := literal | true | false | none | unreachable | name | ( expr ) | expr.field | expr.N | expr[expr]
     | Type { field: expr, ... } | Type.Form { field: expr, ... } | Type.Form     record, form with fields, form without fields
     | { ...expr, field: expr, ... }                        copy of a record with fields replaced
     | (expr, expr, ...)                                  tuple (from two fields)
     | [expr, ...] | [expr: expr, ...]                       list; map (the key is an expression); [] is an empty list or map by the expected type
     | not expr | -expr | expr (+|-|*|/|%) expr | expr (==|!=|<|<=|>|>=) expr
     | expr (and|or) expr | expr ?? expr
     | expr..expr                                       a range: half-open [a, b)
     | expr..=expr                                      an inclusive range [a, b]: a..(b + 1)
     | if expr then { expr } else { expr }
     | { [let name = expr;]... expr }                     block expression: bindings and the last expression (the value of the block)
     | match expr { alt [| alt]... [if expr] => expr, ... , else => expr }       exhaustive; on one line branches through `,`, multi-line — each branch on its own line without `,`
     | name(expr, ...)                                 catalog function, author function (pure) or host external function (section 7: pure — everywhere, volatile and acting — by class); there are no named arguments (below)
     | journal_event("code", name: expr, ...)          a journal event value; named arguments only in the journal forms (below)
     | expr.function(name => expr) | expr.fold(expr, (name, name) => expr) | expr.dict(name => expr, name => expr)     a catalog list function is a list method
     | name(expr, ..., key: expr, ...)                 external function with a named tail `...name: Type`: positional arguments, then pairs `key: value` (below)
alt := Type.Value | Value | Form | Form { field, field: name, ... } | Type.Form { field, field: name, ... } | literal     Value is a bare element name, looked up among the declared enumerations
```

- **Precedence and associativity** (highest first; since version 2.24 brought in line with Nova, D49): parentheses `( )`, postfix `.` `[]` and call; unary `-` and `not` (a strong prefix, like `!` of Nova); `* / %` (left-associative); `+ -` (left-associative); `??` (right-associative: `a ?? b ?? c` is `a ?? (b ?? c)`; above comparisons, below `+ -`); `< <= > >=`; `== !=`; `and` (left-associative); `or` (left-associative); `..` and `..=` are the weakest: `a..b + 1` is `a..(b + 1)`, `0..n ?? 0` is `0..(n ?? 0)`, `a..b == c` is `a..(b == c)` (so a comparison with a range is written in parentheses); `..` and `..=` are not chained: `a..b..c`, `a..=b..c` are errors. Comparisons and equalities are not chained (below). `match` captures everything to the right; the branches of `if` and a block expression are blocks, their boundary is the closing `}`.
- **Check errors asking to put parentheses.** Any combination of two comparison or equality operators without parentheses: `a < b < c`, `a == b != c`, `a == b < c` (by precedence this is `a == (b < c)`, but Alula requires parentheses); one writes `a < b and b < c` or `(a < b) == c`. `not` over a comparison without parentheses: `not a == b` is an error (`not` binds stronger than a comparison, that is `(not a) == b`); one writes `(not a) == b` or `not (a == b)`.
- **A readability recommendation** (not an error): a mix of `??` with a comparison, `and` or `or` is parsed by precedence (`a ?? b == c` is `(a ?? b) == c`, `a and b ?? c` is `a and (b ?? c)`), but is written with parentheses.
- **Literals:** integer `12`, float `0.0`, text `"…"` (with insertions `"…${expr}…"`, below); `true`, `false`; `none` — the absence of a value of `?T`. **Numbers** (D44 of Nova, `decimal-int` and `float`): an integer is `[0-9] (_? [0-9])*` (`12`, `1_000`: the sign `_` only between two digits); a float is an integer, `.` and an integer (`0.5`, `1_000.25`) with an optional exponent, or an integer with an exponent; an exponent is `e` or `E`, an optional sign `+`/`-` and an integer (`1.5e-3`, `1e-7`, `2E5`, `1.5e+3`); hexadecimal, binary, octal literals and type suffixes are not introduced (as Nova rejected suffixes). **The lexing order of a number** (as the Nova lexer `novac/src/lex/lex.nv`): the digits of the integer part with `_` between digits; a dot enters the number only if a digit follows it right away — therefore `1..n` is `1`, `..`, `n`, `0..3` is `0`, `..`, `3`, `1_000..2_000` is `1_000`, `..`, `2_000`, and `1.` without a digit after the dot and `1..` are not a float; then an exponent, if a digit stands after `e`/`E` (and a sign) — `1e3` and `1.5e3` are one float number; no letter, digit or `_` of a name touches a number: `1__0`, `1_`, `1_e5`, `1.5_`, `1e`, `1e+`, `0x1F` are errors; `_1` is a name, not a number. **Escapes** in a text literal (a closed list, as D467 §2 of Nova): `\"` — a quote, `\\` — a backslash, `\$` — the sign `$` (`\${` is `\$` and `{`: no insertion), `\n`, `\t`, `\r` — a line feed, a tab, a carriage return, `\0` — the null sign, `\u{HEX}` — a Unicode sign by one to six hexadecimal digits (the surrogates `D800`…`DFFF` and values above `10FFFF` are an error); any other sign after `\` is a check error; `\xNN` of Nova is not taken (covered by `\u{…}`), there is no line continuation `\` + a line break — a literal stands in one line; in a table cell `\|` is the escaping of the cell, parsing removes it before parsing the literal. The word “no” (Russian `нет`) is not a literal (rule 30: the “no” of the specification is `none` of `?T`). `unreachable` is an expression of any type: a program defect, the evaluation is stopped by the engine, like `require(none)` (3.3); it stands in the `match` branch for a form that by the contract does not arrive.
- **Names.** A name is a datum, a constant, a parameter, a function, a binding. A state reads any name named in its expressions (the reads are derived by the check, 4.1; for an appeal — also in the `Request` table). An event field binding, `let` and a lambda parameter are visible only in their scope; an event field binding does not coincide with the name of a machine datum (4.3). A callable and a value lie in different namespaces: an author function occupies the call namespace together with the catalog functions and the external functions (1a, namespace 11), while data, constants, parameters and bindings are the value namespace; therefore a bound field `text` and a call `text(x)` do not interfere, and an author function coincides neither with a catalog function nor with an external function. **Reserved words** are never the name of a binding, a datum or a field: `in`, `then`, `else`, `and`, `or`, `not`, `let`, `match`, `if`, `for`, `true`, `false`, `none`, `unreachable`.
- **Field binding with a colon**. A field of a signal or a form is declared in the Nova notation through a space (`findings []Finding`, section 2); a binding in a pattern of a transition row is `field: name`, the colon is read “field → name” (`signal(counted { findings: new_findings })`, `response: Finished { text, artifact, usage: received }`, the alternative `Finished { text, usage: u } => …`); if the name coincides with the field, the single name is written.
- **A lambda** is unary (binary only in `fold`); a parameter that is not needed is written `_`; lambdas stand only in an argument of a list function. The record is `name => expr`, a binary lambda has its parameters in parentheses: `(m, _) => m * 2`; the body expression may be a block expression: `x => { let y = x * 2; y + 1 }` — as in a `match` branch and unlike the body of a function, where `=> {` is an error (a decision of the methodology for 2.21, confirmed by the owner (methodology chat, 2026-10-22: «по рекомендации»)); the sign `=>` is the same as in a `match` branch and the body of a function of one expression (as in Nova), and `->` stands only before a result type. Nova's record `|m, _| m * 2` is not taken: GitHub splits a table row at every sign `|`, even inside backquotes, and a lambda in a cell (`initial` of the data, actions) would need `\|`; besides, `|` already separates the values of a literal set and the alternatives of `match`.
- **Readable names of the engine** (not computations, rule 11): `input`; `event.id` (of any event); `event.at` (of any event: the stamp of the event, an integer — milliseconds since 1970-01-01 UTC at the moment the event arrived; the engine sets it once, when a step is repeated (rules 12–13) it is the same; for a held reply it is the stamp of the step that plays it; a field of a signal or form named `at` or with the JSON name `at` (for example the Russian `время`, if the glossary gives it `at`) is a check error: the name is taken); `event.<field>` (a field of the event data of a row or a chain, rule 13); `party` (for a set — the identifier of the event's party; in the “profile” and “Request” of a set — the current party); `reason` — the failure code of the event `failure(reason)` (4.3; visible to the row and the chain); `state` (section 9; type `State`); `transition_note` (type `JournalEvent`; in “On entry” and in the “response” of ends; defined when the machine has entered ERROR, and ERROR is entered in two ways: by `machine_error` — the record of this action and by an engine machine error (3.3) — the record `machine_error`; both ways give a record); `all_data` (a record of the machine data; the composition is in section 2; in the action `journal(all_data)` the same name is an abbreviation of the event `machine_data`, section 5). `previous` and `call_request_id` are not engine names but data of the “Pause” library (section 9). The JSON name of a readable name is the `en` word of the word table, the kind `readable` (`party`, `reason`; 1a). The names `trace` and `step` (the envelope, rule 31) are available **only** in the “Request” expressions of a party of kind `machine` — this is the envelope of a nested machine call (rule 35, item 1); in conditions and actions the envelope is not read.
- **Named arguments** are allowed in two places. (1) In the journal forms `journal("code", name: expr, …)`, `journal_event("code", name: expr, …)` and `machine_error("code", name: expr, …)` (the parameters of a journal event, section 5): the pairs `name: value` come after the positional arguments, the name of a pair is the name of a parameter of the event template, a repeated name in one call is a check error. (2) In a call of an external function with a named tail (the next item). In all other calls — catalog functions, author functions, external functions without a tail — a named argument is a check error, the message names the function and the argument name.
- **The named tail of an external function.** The last parameter of an external function may be written `...name: Type` (the Russian form is `...имя: Тип`): a named tail that takes pairs `key: value` (the declaration is in section 7: `write_status(code int, ...fields: str)`). The call is `f(a, b, key: value, …)`: positional arguments by the number of positional parameters, then pairs `key: expr` separated by commas. The type of the tail in the language is `map[str, Type]`; the order of writing the keys is kept (section 2), a repeated key name in one call is a check error. The host receives the tail as a separate last parameter — a list of pairs `[](name, value)` in the order of writing. A tail exists only for external functions; author functions and catalog functions have none. A call without pairs is allowed: the tail is empty (an empty map) and the host gets an empty list. In the tree a tail parameter is the record `{name, type, tail: true}` in `params` (`type` is the type of the tail values), a call has the field `named: [{name, value}]` in the order of writing; in the registry entry of the host a tail parameter is marked the same way (`tail`). Notations of their own, not function calls: an include of a library (a subheading `### Pause` with a table of parameter values, section 9), a record literal `Type { field: expr }` and `cancel_open(except: nested)` (section 5).
- **List functions with a lambda**. The eight catalog functions (`filter`, `map`, `any`, `all`, `count`, `first_where`, `fold`, `dict`, section 12) are called as a method of their first argument — a list: `xs.filter(x => expr)`, `xs.fold(initial, (m, x) => expr)`, `xs.dict(x => key, x => value)`; a chain is `xs.filter(…).count(…)`. The other catalog functions, author functions and external functions are called by a call `name(…)`. A name after a dot without `(` is a record field (`result.probes`), a list function name after a dot with `(` is a method call; a record or form field named as a list function is a check warning, not an error: the fields of the packages' machines have such a name (`count`), and the parentheses tell the method call `x.count(…)` from the field `x.count`. The former call of this function as an ordinary call with the list as the first argument (`filter(xs, x => expr)`) is an error. The tree is the former ordinary call of a list function, the receiver being the first argument (section 6).
- **A range**. `a..b` is a list of integers `[a, b)`: half-open, empty when `b <= a` (as the former `range(a, b)` and Nova's `a..b`; the inclusive one is `a..=b`, below); the operands are `int`. **Lexing:** `..` after a number or a name is always the range sign, never a part of a fractional literal: `1..n` is read `1`, `..`, `n`, and `0.5..2` is `0.5`, `..`, `2` (the type is an error: the operands are not `int`); `...` is the spread (the longest match). A method on a range is written in parentheses: `(1..n).fold(…)` (`.` binds tighter than `..`). In the tree — a call `range` (section 6).
- **An inclusive range**. `a..=b` is sugar for `a..(b + 1)`, as Nova's `a..=b` (the end `b + 1`): a list of integers from `a` to `b` inclusive, empty when `b < a`; the operands are `int`; the precedence and the rules are those of `..` (the lowest, `a..=b + 1` is `a..=(b + 1)`, not chained, a method in parentheses: `(1..=n).fold(…)`). **Lexing:** the longest match — `...` (spread), then `..=`, then `..`; `..=` is written without spaces: `a.. =b` (`..`, then `=`) and `a..==b` are errors. In the tree — a call `range` with the arguments `a` and `b + 1` (section 6), the same as for `a..b + 1`.
- **A map literal**. `[key: value, …]`, as Nova's `[k: v]` (`[ActionKind.Read: "ask", ActionKind.Write: "deny"]`, `["a": 1]`): after `[` the first expression is parsed; the next sign `:` means a map literal, then pairs `expr: expr` through commas; `,` or `]` means a list literal; the pair separator is the first `:` outside nested `()`, `[]`, `{}` (`[journal_event("x", name: "1")]` is a list: the `:` of a named argument stands inside the parentheses). `[]` is an empty list or an empty map by the **expected type**; the sources of the expected type: the type of a datum (the column “type”), a constant, a parameter; the type of a field — in a record or form literal, in a record copy and in the cell “expression” of the `Request` (the type of the input field of the called machine, otherwise of the datum of the same name); the result type of a function from its header (the body is `[]`); the type of a parameter of a function with a declared signature — an author function (an argument of a call); the type of the left side of an assignment; the type of the other operand of `==`, `!=`, `+` (`to_send != []`, `open_requests == []`); for the right operand of `??` — the type of the place, and without it the type of the left operand without `?` (`m[k] ?? []`); the value of an `if`/`match` branch and the last expression of a block — the type expected by the place; the initial value of `fold` — the result type of the call; the type of a parameter of an included library (`nested: []` — an empty list of machine names, section 9). The type of a call `xs.filter(…)`, `remove(xs, x)` and `without_key(m, k)` is the type of the first argument: by it the type of the other operand is known (`xs.filter(x => x > 0) == []`). A parameter of a catalog function by the signature of section 12 is not a source of the expected type; where there is no expected type (for example, `[] == []`), `[]` is a type check error. Keys and values are expressions evaluated left to right (3.3); a repeated constant key in a literal is a check error (parsing), keys that became equal only when evaluated are the machine error `duplicate_key` (3.3); the literal of a full map names all keys (section 2). There is no map literal in braces: `{expr: expr}` and `{}` are errors.
- **The set after `in`** (Russian `в`) is a list literal: `reason in [FailCode.A, FailCode.B]`, `stop_reason in [""]`; it stands only in `failure(reason in […])`, “when” of ends and `Except` (4.3, 4.7); the elements are values of a closed type (enumeration elements, literals without insertions); `in {…}` is an error.
- **Insertions in text literals**. `"…${expr}…"` — as in Nova (`"${file}:${line}"`, `"turn ${number} of ${limit}"`; the Russian form is the same). (a) Inside `${ … }` — any expression of a type for which `text(x)` is defined (int, f64, str, a literal set, `id`, an enumeration, `State` and `?A` of them, section 12); `bool` and composite types are a check error; the value is inserted as `text(x)` (3.3). (b) A literal with an insertion is a value of the type `str` (3.2), not a literal of a literal set: a set `"a" | "b"` (section 2) and `in […]` (Russian `в […]`) hold only literals without insertions. (c) The sign `${` in text is written `\${` (escaping with `\`, as for `"` and `\`, 1b); a single `$` needs no escaping; an empty insertion `${}` and an unclosed one are an error; literals, including ones with their own insertions, are allowed inside an insertion, the depth is not limited (`"${if has(x) then { "has ${require(x)}" } else { "none" }}"`); in a table cell the sign `|` inside an insertion, as everywhere in a cell, is written `\|` — an expression with `|` is better moved into a `let`. (d) The tree schema does not change: the parse unfolds a literal with insertions into a call of the catalog function `concat` (section 12; Russian `склеить`) by one rule: the parts of a literal are the text fragments and the insertions in order, empty fragments are dropped; a literal without insertions is the literal itself; a single insertion part (`"${x}"`) is `text(x)`; otherwise it is a call `concat(…)` with the parts in order, at least two arguments, an insertion being `text(x)`: `"${file}:${line}"` is `concat(text(file), ":", text(line))`, `"a${x}"` is `concat("a", text(x))` (section 6); the generator writes as an insertion only a call `concat` of the canonical form (1b, a recommendation). The sign `+` of text stays (3.2).
- **An alternative of a form with fields**. A `match` alternative on a form with fields is a pattern, as in the event cell (4.3) and in Nova: `match result { Finished { text, usage: u } if has(text) => …, Truncated { usage } | Cancelled { usage } => …, else => … }`; the fields are bound as names (`field: name` — with renaming, a single name — the same field), the bindings are visible in the guard and in the branch; a form without fields is a name without brackets. The form name is looked up in the type of the expression after `match` (as `response: Form` — in the type `result` of the party); the qualified record `Type.Form { field, field: name }` is allowed, as `response: Type.Var { … }` (4.3), and its `Type` is the type of the `match` expression, otherwise it is a type check error (`match result { TurnResult.Finished { text } => text, else => "" }`); `Name { … }` in an alternative is always a pattern, not a literal: the alternative stands before `=>`, and a value of a form with fields in an expression is written only with the type name `Type.Var { field: expr }`, therefore `Name { … }` without a dot in an expression is a record literal of the type `Name`. Alternatives joined by `|` have their own braces each. The former record `Form(field, field: name) =>` is an error; parentheses after a name are only a function call.
- **`match` branches** (by D452 of Nova: `match` arms on one line are separated by `,`, in the multi-line form only by a line break): on one line branches are separated by `,` — `match kind { Delete | Move => true, else => false }`; there is no comma after the last branch. A multi-line `match` (in a code block) separates branches by a line break: `{` stands at the end of the header line, each branch is on its own line, without `,` and `;` at the end, `}` is on its own line; a branch `=> { … }` may take several lines (line breaks inside a branch block do not split branches), the branch `else => …` the same. Branches are alternatives, not a sequence, therefore `;` between them is an error; `,` at the end of a branch line of a multi-line `match` is an error (D452 removed the comma in the multi-line form, the trailing one included); two branches on one line of a multi-line `match` and a branch on the line of `{` or `}` are errors (there is no mixed form). A table cell is one line, therefore `match` in a cell is always one-line. `;` inside a branch block (`=> { let x = expr; x }`) is the separator of the block and stays.
- **Bare names** (as rule 1 of D478 of Nova). The name of an enumeration element or of a form without fields is written without the type name: in a `match` alternative, in an element of `in […]`, in a key of a map literal and a full map literal and the index `expr[key]`, on a side of `==`, `!=` and in other places of an expression. A bare name is looked up among the enumerations declared in the machine, in the included libraries; the expected type of the place is not needed for the lookup; the type of a bare name is the type that declares it, the format 0.27 does not introduce a general check of operand types (see the [changelog](alula-changelog.en.md), “Open items”). A check error (the qualification `Type.El` is needed): the name is declared in two types; the name coincides with a datum, a constant, a parameter or a binding. The qualified form `Type.El` is always allowed. The choice between sums by the expected type (D478 of Nova) is not taken: the translator does not infer the type of every place. State names — the literals of the built-in enumeration `State` — were written so before too (`state != Pause`, section 9). A form with fields in an expression is only `Type.Var { field: expr }`: `Name { … }` without a dot is a record literal of the type `Name` (below). Example (the same meaning as the qualified record): `match kind { Delete | Move | Execute => true, else => false }`, `failure(reason in [ConnectionLost, Timeout, NoResult])`, `check == Valid`, `PERMISSION_POLICY[Read]` (a key of the type `ActionKind`); if `Valid` is declared both in `Check` and in another enumeration of the machine, one writes `check == Check.Valid`.
- **Not introduced from the methodology's count:** `contains`, slices, postfix `?`, sorting, loops and recursion outside `for`.

**The position of a block**. There is one block sign — `{ … }`; what it holds and whether it has a value is given by the position:

| Position | Where | Block content | Value |
|---|---|---|---|
| action | a row “Actions”, “On accept”, “On entry” of an operation and an end (4.5, 4.7), a branch of a conditional action, the body of `for`, a block `{ actions }`; not “On entry” of a fork (only `let` bindings there, 4.6) | actions joined by `;`, including `let name = expr` (visible up to `}`) | none |
| expression | a branch of a conditional expression, a block body of a function (after the result type, without `=>`), the right side of an assignment and of `let`, an argument, an expression cell | zero or more `let name = expr;`, lastly one expression | the last expression |

A block expression differs from the literals with braces so: a record and form literal stands after a type name (`Type { … }`), the pattern of a `match` alternative — after a form name, before `=>`; a record copy starts with `...`; otherwise `{` opens a block. There is no map literal in braces — a map is written `[k: v]`, so no look-ahead to `:` is needed; `{}` is an error: there is no empty block, an empty map is `[]`. After the result type in a function header `{` always opens a block body, and right after `=>` there is never a block.

Example of expressions (the “Agent step” pilot, functions).

```
fn needs_elevated_attention(action_kind ActionKind) -> bool =>
  match action_kind {
    ActionKind.Delete | ActionKind.Move | ActionKind.Execute | ActionKind.Network | ActionKind.SwitchMode => true
    else => false
  }

fn retry_pause(n int>=0) -> int =>
  (1..n).fold(RETRY_PAUSE, (m, _) => m * 2)
```

### 3.2 Expression types

| Rule | Record |
|---|---|
| Raising `T` to `?T` | in an assignment to a field `?T`, in a record constructor field, in a function argument with a parameter `?T`, in a branch of `if`/`match`, to the right of `??` |
| `if`, `match` | branches `T` and `?T` (or `none`) give `?T`; branches of one type — that type |
| `??` | `?T ?? T` is `T`; `?T ?? ?T` is `?T`: the right operand of either of the two types, the result is `T` only with the right `T` |
| `+` | int, float (cannot be mixed), text (concatenation), a list of one type (concatenation: the left first) |
| `==`, `!=` | structural for records, tuples, lists, maps, enumerations, including those with fields (a form without fields — `x == Type.Var` or a bare `x == Var`; a form with fields — `x == Type.Var { field: expr }`), literal sets, `?T`; `T` with `?T` — through raising (`none` is not equal to a value) |
| `<`, `<=`, `>`, `>=` | int, float |
| `expr[key]` | map: `?V`, an absent key is `none` (not an error); for a full map — `V`. List: `?T`, an index out of bounds is `none` |
| Literal set | the value of the expression is a **set of values**: a literal is one; `+` — pairwise concatenations; `if`/`match` — the union of the branches; `require(x)` — the set of `x` without `none`; `require_non_empty(x)` — the set of `x` without `""`; `text(x)` for an enumeration or its subset — their values; assignment and comparison with a datum of the “literal set” type check the inclusion of the set. A concatenated field with an “empty” beginning is declared by the source: the source gives “no” — `?("a" \| "b")` without `""`, `none` and `require`; the source gives `""` — `"" \| "a" \| "b"`, initial `""` and `require_non_empty`. One value is not replaced by another: in a data snapshot `""` and `none` are different |
| literal set → `str` | a set value is assigned to a datum and passed to a parameter of type `str`, the set is forgotten; the reverse — by the inclusion of the set |
| `id` → `str` | assigned to a datum and to a parameter of type `str`, the type `id` is forgotten; the reverse — only a literal of UUID format (section 2) |
| A literal with insertions `"…${x}…"` | `str`, not a literal set: the value of an insertion is not closed, therefore assigning it to a datum of a “literal set” type is a check error; `x` is a type for which `text(x)` is defined |
| `int>=n` | assigning a value that violates the bound is a machine error; statically checked only for literals and constants; `int>=n` is compatible with `int` both ways. The result of `+`, `-`, `*` over `int>=n` is `int` (without a bound): `number - 1` is `int`, passing it to a parameter `int>=0` is checked at the call |
| `unreachable` | any type: compatible with `T` and `?T`; in `match` it does not affect the result type |

Example (the “Agent step” and “Meeting” pilots; `failed_appeal` is declared `"" | "Witness" | "Lenses" | "AuthorFix" | "AuthorQuestion"` (a literal set), initial `""`, as in the source: the set after `require_non_empty` has no empty value).

```
stop_reason = text(reason)                                     // reason in [ConnectionLost, Timeout, NoResult]: the set "connection_lost" | "timeout" | "no_result"
stop_reason = require_non_empty(failed_appeal) + "_halt_meeting"      // the set: four values “..._halt_meeting”, all belong to the set stop_reason
refusal_text = "turn ${turn_count} of ${turn_limit}"          // insertions: the type str, not a set; the tree — concat("turn ", text(turn_count), " of ", text(turn_limit))
```

### 3.3 Evaluation

- Evaluation is strict, left to right: function arguments, record fields, list and map elements — in the order of writing; `match` branches — top to bottom, the `if` guard — after the alternative matches; a `let` binding in a block — first the value, then the rest of the block. **Lazy** are only `if`, `and`, `or`, `??`: an unselected branch and a right part that is not needed are not evaluated.
- **A call of a volatile function inside `if`/`match`**: the selected branch evaluates the call, the unselected one does not (laziness above); the read of the call enters the reads of the state unconditionally, by the `reads` list of the function. Calls in arguments are evaluated in the order of writing.
- **The language is not total.** Two kinds of partial operations.
  - **A program defect**: `require(x)` with an empty `x`, `require_non_empty("")` and `unreachable` — the process is stopped by the engine (not the table); there is no transition to ERROR, the machine state is not rolled back; the call response is an end with `NoResult`; the journal of the defect is at the engine's discretion (this is how `required` of the automata behaves).
  - **A machine error:** `int` overflow, division by zero, going outside `int>=n`, `int(x)` out of range, a repeated key in a map literal with computed keys and in `xs.dict(…)`, an absent key in `name[key].field = expr`, an index out of bounds when writing into a list. The engine writes the journal event `machine_error` with the parameter `reason` — a word from the closed list `overflow`, `division_by_zero`, `bound_violation`, `conversion_range`, `duplicate_key`, `missing_key`, `list_index` (journal, subsection “Events of the table format”) — and enters ERROR; this event is the `transition_note` (3.1).
  - Indexing a map and a list when reading is not a partial operation.
- `if` is not nested into a branch of another `if` (three or more outcomes — a `match` with guards or a fork).
- `text(x)`: an integer is a decimal record; a float is the shortest decimal record that is reversible to the same float; an integral value is written with `.0` (`1.0`, `0.0`); without an exponent `e` if `1e-4 <= |x| < 1e16`, otherwise an exponent of the form `1e-7`, `1.5e20` (lowercase `e`, without `+` and without leading zeros of the exponent); examples: `0.0`, `2.0`, `0.42`, `0.0001`, `1e-7`, `1.5e20` — each record is also a float literal (3.1), therefore the generator writes the value back with it; NaN and infinity are a machine error; an enumeration is the value of the element (for an element without a value — the JSON name); `State` is the JSON name; text is itself; `none` of any of these types is `none`. For `bool` and composite types `text` is not defined.

## 4. States

### 4.1 General

The heading `### NAME — kind`: kind is `appeal`, `operation`, `fork`, `end`; **the JSON name of the state** (1a) is Latin, for the journal and the envelope (the field `state`, the parameter `fork`, `text(State)`): automatic (Russian `ПОВТОР` → `Retry` by the glossary; for a Latin one the name itself, `### Retry — fork`) or, where it is wrong, a `## Names` row (Russian `| ОТКРЫТИЕ | Opening |`, `| Pass | Gate3 |`); there are no parentheses in the heading. The rows go in order; the **first** suitable row is selected. The initial state is the first line of the section `## States`: `Initial state: NAME`; the check 34(г) requires that it name a state of the section. **The reads of a state** (rule 11): they are derived by the check from the expressions of the rows, the “Request” (4.2), the “On accept” and the “On entry” of the state and from the hidden reads of external functions in the host registry (the `reads` list, section 7); for ERROR the reads are `all_data` (all data of the machine without engine data; the names are read as data). The reads need not be declared: rule 11 of the methodology (“a step reads only its input”) here means that the reads of a state are derived by the check and shown in its report; there is no key line `Reads:`, and a line `Reads:` in a file is a check error with the hint “since 2.26 the reads are derived”. An appeal without request fields writes no `Request:` line. In the examples of this English version the state names are the Latin names, so they are their own JSON names.

**State key lines** — `Party`, `Idle term`, `Edits`, `Form returns`, `Request`, `On entry`, `On accept`, `Except`, and in the sections `## Parties` and `## Output` — `Request limit` and `Result` — are **items of a bulleted list**: `- Party: agent`, `- Idle term: IDLE_TERM`, `- Form returns: 1`. The marker `- ` is required: a key line without it is a check error; the reason: markdown glues consecutive lines into one paragraph, and the preview shows “Party: agent Idle term: IDLE_TERM Request:” as one line. **Empty values are not written**: a key with an empty value (no request fields, no term, no work on entry) is not written, and an omitted key means the default. A key with a real default value (`- Idle term: 0`, `- Form returns: 0`) may stay written: so it shows that the value is chosen, not forgotten. The other rules of writing:

- a table (request field | expression of `Request`; event | actions of `On accept`; the state rows) stands **at the block level**, not inside a list item: between the last list item and the table, as between two tables, there is an empty line; the item itself (`- Request:`, `- On accept:`) remains the last in the list before its table;
- a value in one line is in the item itself (`- On entry: let moment = event.at`); the body of “On entry” of several actions is a nested list, one action per item (`  - let current_time = event.at;`), the sign `;` at the end of the item is kept, parsing glues the items into the same action list through `;`;
- the state heading `### NAME — kind` and the line `Initial state: NAME` (one per section) are not written as a list.

**Prose**. A paragraph — one or several lines of text between empty lines (an empty line is needed both before and after) outside tables, outside code blocks and outside key lines — is a comment for the reader: translators and checks skip it, the signs “`” and “« »” inside it are allowed. A text line pressed against a table, a heading or a list item without an empty line is not a paragraph (markdown glues it to the neighboring block): the formatting check warns, parsing reads it as an extra line of the neighboring block. Headings `#`, `##`, `###`, tables and the list items of key lines (`- Key: …`) are not prose. A key word without the marker is not a comment but an error: a line that begins with a word from the list of keys (`Party`, `Idle term`, `Request`, `Edits`, `Form returns`, `On entry`, `On accept`, `Result`, `Except`, `Request limit`) and a colon, without the marker `- ` or with a typo in it, is a check error; otherwise a typo in the marker would remain a silent comment.

**“To”:** a state name; `previous`; `preparation_return` (rule 24); `same` (stay in the state; allowed in the rows of an appeal and in common events; without a rerun only the actions of the row run — no re-entry, no request is sent; with a rerun — `same, rerun` — the state is entered anew: the open request of the appeal is cancelled and a new one is sent; example: `| signal(retry) |  | journal("retry_requested") | same, rerun |`); the suffix `, rerun` (rule 18); empty only for a row with `machine_error`.

**The fork default and `else`**. The `else` row is not required. A fork in which no row fits leads by itself to ERROR: the engine writes `machine_error("fork_no_match", fork: "<JSON_name>")` (the value of `fork` is the JSON name of the fork, the engine substitutes it; the journal and the codes are the same as the former `else` row gave), and no `To` is needed. The `else` row (rule 27) is written only if it has actions of its own: it is last, leads to a state and is not empty. **The exhaustion is proven by a type** when the condition of every row except `else` is a comparison of one and the same name `x` (a datum, a `let` binding, `event.<field>`) of a closed type with one of its values: `x == Type.El` for an enumeration `Type` (or a bare `x == El`), `x == Type.Var` for an enumeration whose forms all have no fields, `x == "label"` for a literal set (`"a" | "b"`, section 2) — and the rows name all values of the type (as for `match`, section 2). Then a fork cannot be left without a suitable row, and a written `else` is unreachable — a check **warning**, not an error. No exhaustion is proven by a condition over text — a name of the type `str` (`continuation == "…"`: however many labels there are, the type does not close them; to close the set, declare the type as a literal set or an enumeration), over two fields (a pair of enumerations: a product of types is not proven), over `?T` (`none` is not named), a condition with `and`, `not`, `!=`, `<`; in such forks an uncovered combination leads to ERROR by the rule above.

### 4.2 Appeal

```
### NAME — appeal
- Party: <name from “Parties”>[; set: <list expression of identifiers>]
- Idle term: <expression of type ?int>=0>   optional; an empty one is not written, not written — no term
- Edits: <datum>; check: <volatile function>   optional (rule 14)
- Form returns: <int>=0>                 optional, 0 by default (`0` may be written)
- Request:                               optional: no request fields — no line

| request_field | expression |       an empty expression cell — the same name

- On accept:                                  optional

| event | actions |
| <event> | <actions> |

| Event | Condition | Actions | To |
```

- **Request.** Everything named in the `Request:` table goes to the party as a request field. **The default expression**: an empty cell “expression” means “the same name” — the expression of the field equals the field name (`| number |  |` is the same as `| number | number |`); this is not “no value”. With an empty cell the field name must be a name that the “Request” expressions read (a datum, a constant, a parameter, `input`, `party` for a set, for a party `machine` — `trace`, `step`), otherwise a check error, as for any expression. An explicit expression equal to the field name is allowed but not recommended: the check warns, the canonical form writes an empty cell (1b). The column “expression” stays even with empty cells in all rows: table headers are not removed (markdown does not show a table without a header). The state rows, “On accept”, “Idle term” read the names from `Request`. The request field `profile` is not written in the “Request”: it is given by the column `profile` of “Parties”. The expressions read the machine data, constants, parameters, `input`, `party` (a set) and — for a party `machine` — `trace`, `step`; a call of a volatile external function is allowed (evaluated on entry, before sending, in the order of the rows). The request fields of a party `machine` are exactly the fields of its type `input`, except `profile` (it is given by the column of “Parties”). A request field may be named as a datum with a different expression (`previous` — `require(previous)` of Pause): the rows, the conditions and “On accept” read the **datum**, not the field, the field is visible only to the party; the expression of such a field is any “Request” expression, including a call of an external function and `if` (in Changed of “Meeting” the field `proposal` is `if proposal_read() then { proposal } else { none }`), the rows do not read it. The conditions, “On accept” and “Actions” read only the names from `Request`, `event.…`, bindings, constants and parameters (rule 11).
- **An appeal without request fields**. If the party needs no request fields (the gate “repeat / halt” without data), the line `Request:` and the table are not written: the request carries only what the engine gives (the envelope, `profile` from the column of “Parties”); the rows, “On accept” and “Idle term” of such a state do not read machine data — only `event.…`, bindings, constants and parameters. For a party `machine` a request without fields is allowed only if the called machine has no `## Input` fields (section 1).
- **An appeal with free input** (rule 19). `Party` is a party of the kind `human` without a counter (section 1): there are no gates and no request, the engine sends and shows nothing, the machine waits for a word. Therefore such an appeal has no `Request`, `set`, `Idle term`, `Edits`, `Form returns`, no rows `response` and `failure` (the check of section 10); the rows are by the signals of the party (`signal(message { content, author, source })`); a word is accepted by the signal name in the current state, a word for which there is no row is discarded (rule 17); “human stop” is a common event (rule 23).
- **Idle term.** A line not written (an empty value is not written), `none` or `0` mean no term ( a human has no term — an open gate, rule 19; a gatekeeper has no term written in the state: the term of an agent gatekeeper is a parameter of the gatekeeper, rule 19; a machine call has no term, rule 35, item 5). The expression reads the same names as the “Request” expressions (data, constants, parameters, `input`, `party` of a set), without calls of volatile external functions (pure functions and catalog functions are allowed); these names are named in the `Request` of the state. It is evaluated on entry, after the “Request”, before the request is sent.
- **Edits** (rule 14). `Edits: <datum>; check: <external function>` — the party's response edits an object that the datum reflects (`proposal`), and the result cannot be accepted if the object changed since the beginning of the attempt. `check` is a volatile external function without parameters with the result `bool`; the engine calls it when it accepts the response, after the check of the openness of the request and the form and before `parse` and “On accept”. `true` — the result is not accepted (it is not written to `accepted_requests`, “On accept” is not executed, there is no event), the request is cancelled and goes out again: a new attempt, the `Request` is evaluated again; the journal entry about this is engine mechanics. The “beginning of the attempt” and the comparison are owned by the engine, the function reads its service record and the object (`reads` in the host registry). A datum from `Edits` must be written in the “On accept” of this state (table check).
- **Set** (rule 21): `Party: lens; set: lens_order` — one request per identifier; `party` in the “Request” is the identifier for which the request is built; `Request limit` is a section of “Parties”. `to_send` is written by the actions and the engine, `open_requests` is engine data (section 2), the party attempt counter is the column `counter` of “Parties” (section 1).
- **Form returns** — how many times the engine returns to the party a response that is not by form or not by the comparison done by `parse` (for example, of excerpts; rule 18). For the kinds other than `machine` — in the same request. For a party `machine` — with a new request of the same party with a new identifier and a remark: the same identifier would return the ready response (rules 14, 35, item 4). The comparison (for example, of excerpts) is done by the external function `parse` on acceptance, the return itself is engine mechanics. When the returns are exhausted, the request is closed by the event `failure` with the code `FormNotFixed` (a parse failure, section 1).
- **Condition** in an event row — only for the common events and the signals of a library (rules 23, 35); for appeal rows empty. An event whose condition is false is dropped (rule 17, the journal entry is mechanics). The condition `else` is allowed for a signal: the last row of the same event, taken if the conditions of the previous rows of this event are not true; the other events have no `else`.

Example (the “Meeting” pilot, Lenses). An expression equal to the field name is an empty cell; the key of findings is a tuple; the names `trace`, `step` (not the volatile functions `call_trace`, `call_step`); there is no `profile` row; not all rows of the “Request” are shown.

```
### Lenses — appeal
- Party: lens; set: lens_order
- Idle term: 0
- Request:

| request_field | expression |
| kind | CallerKind.Lens |
| session | party |
| context | role_context(RoleContext.LensContext { proposal: proposal, witness_answers: witness_answers[number] }) |
| trace |  |
| step |  |
| number |  |
| to_send |  |
| lenses |  |
| responded |  |
```

### 4.3 Appeal events

A table of rows `| Event | Condition | Actions | To |`. The kinds of events:

| Event | Meaning |
|---|---|
| `response`, `response(name)` | the response value (the party's result or the result of its `parse`, section 1); `name` binds it as a whole |
| `response: Form { field, field: name, … }`, `response: Form`, `response: Type.Form { … }` | the response value is a form of the party's `result` type (for `machine` with `parse` — of the parse result); the fields are bound as names (`field: name` — with renaming); a form without fields — without parentheses |
| `failure`, `failure(reason)`, `failure(reason in […])` | a refusal or “no response” (rule 16); a closed subset of codes is the **list of the state**: the union of the sets of its `failure` rows (a row without a set — all `FailCode`). A code outside the list is brought by the engine to `FailCode.NoResult` (rule 16), the event already carries it; if `NoResult` is also outside the list — `unreachable` (the set is declared full for the state) |
| `signal(<signal>)`, `signal(<signal> { field, field: name, … })` | a **party signal** of the appeal (`human`, `enhanced`, the gatekeeper): the signal is from the column “signals” of the party, the fields and their types are from there too; or a **machine signal** outside the contract (stop, cancel, signals from a parent) — only in the common events and in Pause of a library (section 9); a machine signal row may have the condition `else` (4.2) |

- **A pattern and a call**. An event cell carries either a pattern or an event function of the format:

| Form | Record | Example |
|---|---|---|
| a pattern of a form with fields (a party response) | `response: Var { field, field: name }`, `response: Type.Var { … }` | `response: Finished { text, artifact, usage: received }` |
| a pattern of a signal with fields | `signal(s { field, field: name })` | `signal(counted { findings: new_findings })` |
| the declaration of a signal with fields (the column “signals” of “Parties”, not the event cell) | `s { field type, … }` | `counted { findings []Finding }` |
| a `match` alternative on a form with fields (a code place, not the event cell; 3.1) | `Var { field, field: name } => expr`, `Type.Var { … } => expr` | `Finished { text, usage: u } => text` |
| a form or a signal without fields | the name without brackets | `response: TransientError`, `signal(allow)` |
| an event function of the format | a call `name(…)` | `response`, `response(name)`, `failure`, `failure(reason)`, `failure(reason in […])`, `signal(…)` |

  An event pattern with braces stands in the event cell (the column “Event” of transition rows and common events, the column “event” of the “On accept” table), and a pattern of a form with fields also in a `match` alternative (before `=>`, 3.1); they do not intersect with a block: the event cell has no block, so `Name {` in it is always a pattern, and in `match` the pattern stands after a form name before `=>`, while after `=>` is the value of the branch (an expression, a block expression included). The former record of a pattern in parentheses (`response: Finished(…)`, `signal(counted(…))`) is an error. The declaration of a signal with fields in the column “signals” of “Parties” (`counted { findings []Finding }`) and a `match` alternative on a form with fields (`Finished { text } => …`, 3.1) are written in the same braces since 2.20, the former `counted(findings []Finding)` and `Finished(text) =>` are an error; the braces of an alternative stand in a code place, but before `=>` and after a form name, so they are not confused with a block (3.1, “The position of a block”). Parentheses after a name are only functions: the event functions of the format (the last row of the table), catalog functions, author functions, external functions and the response constructors `Response(…)`, `Refusal(…)` (4.7).
- **Bindings.** Any event field is available also as `event.<field>`; a binding is needed for brevity. A binding name that coincides with a machine datum name without renaming is a check error (there is no shadowing). A part of the fields may be bound. **A partial pattern without `..`**: in Nova a partial record pattern requires an explicit `..` (D486 §3), while in Alula an event pattern (`response: Finished { text }`) and a `match` alternative (`Finished { text } =>`) bind a part of the fields without `..`. The reason: the unbound fields of an event are read as `event.<field>`, a binding is needed only for brevity, and the sign `..` in a table cell would add nothing; a decision of the methodology accepted by the owner (the methodology chat, 2026-10-22: «по рекомендации», “as recommended”).
- **A field named as a datum**. A field of a signal or a form may be named as a machine datum (the signal `confirmed { confirmation str }` with the datum `confirmation`): it is the binding that shadows, not the field declaration; such a field is bound with renaming (`signal(confirmed { confirmation: confirmation_word })`) or read as `event.confirmation`. The machine data here are taken together with the data of the included libraries, and the check goes after the substitution of a library: the bindings of the rows of the “Pause” library (`human_word`, `author`, `source`, `id`; in a Russian file — the names of the Russian library file) coincide with no machine datum, therefore a machine datum is not named so (glossary version 10: `источник_запуска` → `launch_source`, not `source`).
- **Set.** The events of a set carry `party`; the chain of forks behind an event row reads it as `event.party` (rule 13).
- **Party signals**. The signals of a state are the signals of its rows. A party signal is accepted by a row of an appeal whose `Party` declared it; a signal of a human carries the identifier of the open gate, and with the identifier of a gate that is not open it is discarded (rules 17, 19); with gates of several parties in one state the signal belongs to the party named in the identifier, and a signal it did not declare or a signal from another party is discarded (“a word of a foreign party”, rule 19); a signal of a human on a gate accepted by the answer of the agent gatekeeper replaces that answer until the transition by it (window 2, rule 19); a word of free input (a `human` party without a counter, 4.2; rule 19) carries no gate identifier and is accepted by a row of the current state by the signal name, without a gate record; a signal the party did not declare is a row check error. A declared party signal for which the current state has no row is not accepted by a row of the state; it is discarded, and the gate stays open (rules 14, 17, 19). Every signal of a party is used in at least one row of the machine (or of a library); the signal of an event of an appeal row enters the list of signals of its party. A signal field is declared in the column “signals” in braces through a space (`counted { findings []Finding }`), and in a row it is bound as `field: name` (3.1).
- “On accept” — actions BEFORE the transition (rule 14), section 4.4.

Example (pilots). Signals with data — the record `signal(counted { findings: new_findings })`; fields that coincided with data are renamed; an excerpt of the “Parties” table is attached to Gate3: the signals `not counted` and `counted { findings []Finding }` are declared in the column “signals” of the gatekeeper, the party of the appeal (the fields in braces).

```
### AgentTurn — appeal       // an excerpt of the “Agent step” pilot
| Event | Condition | Actions | To |
| response: Finished { text, artifact, usage: received } |  | transport_usage = add_usage(transport_usage, received)<br>reply_text = text<br>reply_artifact = artifact | ReplyValidation |
| response: TurnRequestLimit { usage: received } |  | transport_usage = add_usage(transport_usage, received)<br>stop_reason = "max_turn_requests"<br>journal("turn_requests_exhausted") | Accounting |
| response: TransientError |  |  | Retry |
| response: NeedsPermission { permission_request: request } |  | permission_request = request | Policy |
| failure(reason in [FailCode.ConnectionLost, FailCode.Timeout, FailCode.NoResult]) |  | stop_reason = text(reason); journal("turn_failed", reason: text(reason)) | Accounting |

| name | id | kind | profile | signals | counter |
| gatekeeper | gatekeeper | human or agent by setting elevated_attention_executor(result GateOutcome) | — | not counted, counted { findings []Finding } | gatekeeper_attempt |

### Gate3 — appeal                      // an excerpt of the “Meeting” pilot
- Party: gatekeeper

| signal(not counted) |  | journal("pass_probes_not_probes", pass: text(number)); number += 1 | Pass |
| signal(counted { findings: new_findings }) |  | number += 1; gate3_findings = new_findings | Totals |
```

### 4.4 On accept

The appeal block `On accept:` is a table `| event | actions |`. The event is `response`, `response(name)`, `response: Form { … }` or `failure`; the event bindings and `party` are available; the response value is the result of the party's `parse` (section 1). The engine executes the block when it accepts the response, before the transition, in one commit with the record in `accepted_requests` (rule 14); the bindings of the block (`let`) are saved with the accepted event and are visible to its row and chain. The order of acceptance: the openness of the request and the form, “Edits” (4.2), `parse`, the block.

Allowed in the block: assignments to data, `+=`, `field[key] = expr`, `field[key].field = expr` (5), `for`, `if`, `let name = expr` (including one with a call of a volatile external function in any position of an expression, 3.1). Not allowed: `journal`, `machine_error`, a call of an acting function, a transition; calls of acting functions after acceptance (for example, a time mark and a cache check) are written in the row actions. The block writes machine data, but not engine data (2).

Example (the “Meeting” pilot, Lenses). The value of `result` is the result of the `parse` of the party `lens` (`LensResult`, section 1); the write into a lens is a copy of the record with fields replaced through `require(lenses[party])`: in the code `@lenses(lens_id)` for an absent lens is `unreachable` (the lenses are created at the start), that is a program defect, `require(none)` (3.3); the short record `lenses[party].field = expr` would give the machine error `missing_key` (3.3), differing from the code.

```
- On accept:

| event | actions |
| response(outcome) | { let l = require(lenses[party]); lenses[party] = { ...l, lost: 0, probes: outcome.probes } }<br>responded += 1<br>lens_findings[(party, number)] = outcome.findings |
| failure | { let l = require(lenses[party]); lenses[party] = { ...l, lost: l.lost + 1, probes: 0 } } |
```

Example (the “Meeting” pilot, AuthorFix): the property “Edits”, the parse into the enumeration with fields `EditResult`, the write on acceptance and the rows by form. The write on acceptance is by form, not a `match` over both: with `Done` the `author_question` is neither read nor written, as in the code. The type `EditResult` is defined in the example: the form fields are as in the table of the primary source (“done”: `proposal`; “question”: `proposal`, `question`); in the code `Done(str)` and `Asked(Asking)` with the fields `proposal`, `question` — the record `Asking` is expanded into the form fields.

```
type EditResult enum
  | Done { proposal str }
  | Question { proposal str, question str }
```

```
### AuthorFix — appeal
- Party: author
- Idle term: 0
- Edits: proposal; check: proposal_changed_since_attempt
- Form returns: 0
- Request:

| request_field | expression |
| context | role_context(RoleContext.FixContext { proposal: proposal, gate3_findings: gate3_findings, author_guidance: if author_guidance == "" then { none } else { author_guidance } }) |

- On accept:

| event | actions |
| response: Done { proposal: fix } | proposal = fix |
| response: Question { proposal: fix, question: question_text } | proposal = fix; author_question = question_text |

| Event | Condition | Actions | To |
| response: Done |  | author_guidance = "" | Pass |
| response: Question |  | author_guidance = "" | Gate7 |
```
(Not all rows of the “Request” and the failure rows are shown. The reads of the external functions `check` and `parse` enter the `Request` by their `reads` lists, section 7.)

### 4.5 Operation

```
### NAME — operation
- On entry: <let bindings and calls>

| Actions | To |
| <data changes, journal> | ... |
```

“On entry” is work with the outside world (rule 10): `let name = <expression>` (including one with a call of a volatile or acting external function), calls of acting functions without a result — the action `name(arg);`. A binding is visible further in “On entry” and in all rows of the state; it is evaluated once per entry. The write of an acting function (its `writes`) is visible to the bindings of “On entry” and the rows that follow it: the order of writing is the order of execution. Data changes and the journal are in the row of the operation (rule 29). An operation has one row, `| Actions | To |`: it has no event and no condition (rule 26).

Example (the “Agent step” pilot, Start and Accounting; “Meeting”, Lock, CopyRestore, Filter, SummaryBuilding). The write of data is in the row of the operation, not in “On entry”: the value in “On entry” is only bound (`let`), and the row writes it into data; in CopyRestore the conditional action is in the row; in Lock `copy` is the text of the proposal, `copy_fingerprint` is the fingerprint; in Filter the write into a lens is a copy through `require(…)`, as on acceptance in Lenses (4.4), and `lenses_without_critical` is an external function without a body in the source (section 7), the check takes its hidden reads from the registry; so it does in SummaryBuilding with the reads of `build_summary`.

```
### Start — operation
- On entry: let moment = event.at

| started = moment; turn_count = 1 | AgentTurn |

### Accounting — operation
- On entry:
  - let current_time = event.at;
  - let collected = collect_usage(agent_request, stop_reason, transport_usage, started, current_time)

| usage = collected; journal(usage_event(collected)) | StepOutcome |

### Lock — operation
- On entry: let fingerprint = proposal_fingerprint(); close_for_writing("proposal")

| copy = proposal<br>copy_fingerprint = fingerprint<br>to_send = lens_order<br>responded = 0 | Lenses |

### CopyRestore — operation

| if has(copy) then { proposal = require(copy) } else { journal("copy_restore_no_copy") } | Void |

### Filter — operation
- On entry:
  - remove_unsound(number);
  - let without_critical = lenses_without_critical()

| for l in without_critical { lenses[l] = { ...require(lenses[l]), probes: 0 } } | SummaryBuilding |

### SummaryBuilding — operation
- On entry: let outcome = build_summary(number)

| if has(outcome) then { summary[number] = require(outcome) } | ReviewParsing |
```

(`usage_event` and `collect_usage` are functions, the example is in section 8. In the Russian example the state СВОД gets the JSON name `Summary` by the row `| СВОД | Summary |` of `## Имена`, 1a.)

### 4.6 Fork

```
### NAME — fork
- On entry: let name = <expression, including one with a call of a volatile function in any position>      optional

| Condition | Actions | To |
```

A fork does nothing and waits for nothing (rule 9): “On entry” is only `let` bindings (an expression; a call of a volatile function is allowed in any position of an expression, including in a branch of `if`, 3.3), each evaluated once per entry; the row actions change data only in its transition. The conditions do not call volatile external functions: the result of a volatile function is read by a `let` binding of “On entry”; a pure external function (section 7) and an author function are called in a condition by a call `name(arg)`, and so are the catalog functions; an acting function does not stand in a condition anywhere (section 7).

Example (the “Agent step” pilot). There is no `else` row: the exhaustion is not proven by a type (the conditions are over a number and over a pair of fields), and an uncovered fork leads by itself to ERROR with `fork_no_match` (4.1); the Latin name of ReplyValidation is `ReplyValidation`, as in the glossary; the reads of `reply_validation` are named in the registry (section 7), the check includes them in the reads of the state.

```
### Retry — fork

| retry_count < RETRIES and turn != "retry" | retry_count += 1<br>turn_before_retry = turn<br>turn = "retry"<br>journal("agent_transient_error", retry: text(retry_count)) | Budget |
| retry_count < RETRIES and turn == "retry" | retry_count += 1; journal("agent_transient_error", retry: text(retry_count)) | Budget |
| retry_count >= RETRIES | stop_reason = "no_result"; journal("agent_transient_error_exhausted", retries: text(RETRIES)) | Accounting |

### ReplyValidation — fork
- On entry: let validation = reply_validation()

| validation == ReplyCheck.Valid |  | Accounting |
| validation == ReplyCheck.Empty | stop_reason = "no_result"; journal("agent_no_result") | Accounting |
| validation == ReplyCheck.Violated and return_count < FORM_RETURNS | return_count += 1<br>turn = "fix"<br>journal("reply_form_violated") | Budget |
| validation == ReplyCheck.Violated and return_count >= FORM_RETURNS | stop_reason = "form_not_fixed"; journal("reply_form_not_fixed") | Accounting |
```

(In ReplyValidation the third and fourth rows read both the enumeration `validation` and the number `return_count`: the exhaustion by a type is not proven, and an uncovered combination leads to ERROR by `fork_no_match`. If the conditions were only `validation == ReplyCheck.Valid`, `… .Empty`, `… .Violated` — a row per element — the exhaustion would be proven, and a written `else` would be a warning.)

Example of a nested call of a volatile function (the “Meeting” pilot, Comparison): the fingerprint is read only if the proposal is read; `proposal_fingerprint` for an unreadable proposal is `unreachable`, therefore the call stands in a branch of `if`, and the reads of Comparison include the reads of both external functions.

```
### Comparison — fork
- On entry:
  - let was_read = proposal_read();
  - let fingerprint = if was_read then { proposal_fingerprint() } else { none }

| was_read and fingerprint == copy_fingerprint |  | Filter |
| was_read and fingerprint != copy_fingerprint |  | Changed |
| not was_read |  | Changed |
```

Example of a fork of a set chain (the “Meeting” pilot, LensRefusal): `event.party` is from the event of the set Lenses. Two rows are shown; the others are in the sample.

```
### LensRefusal — fork

| require(lenses[event.party]).lost == 1 | journal("lens_dropped", party: event.party, pass: text(number)) | AllClosed |
| require(lenses[event.party]).lost == 2 | failed_appeal = "Lenses"; to_send = [event.party] + to_send | FailedRequest |
```

### 4.7 End

```
### NAME — end
- On entry: <actions>                     optional
- Except: <value in [...]>                optional
```

The “On entry” of an end is work with the outside world and the journal: `let` bindings, calls of external functions (volatile, acting), `journal`, conditional `if`, `for` with a body of `journal(…)` and `if`; an end does not change data (rule 29). An acting function in the “On entry” of an end must be harmlessly repeatable by the host: an end is entered again (rule 22). `Except:` — the values of the set with which this end is not entered: the exhaustion of the “Output” is checked by the set without them; an entry with such a value is `unreachable`.

**The `## Output` section** (rule 35, item 2, “end → response”): first a list item `- Result: <the machine response type>`, then (through an empty line) the table

```
| end | when | response |
```

- `when` is the entry condition: `true`, `stop_reason == "…"`, `stop_reason in […]`, for the reasons of a library — `Pause.reason == PauseReason.Halted`; the rows of one end are mutually exclusive and cover the set over which they branch (except `Except`); an uncovered value is a table check error.
- `response` is `Response(<a value of the result type>)` or `Refusal(<FailCode code>, <text>)`: these are response functions of the format with positional arguments, not forms with fields, so they keep their parentheses; the envelope of the response (request, party, trace, step) is assembled by the engine; the refusal code is taken from the constructor, there is no separate column.
- In the “response” are available data, `transition_note` (the fields `code`, `params`; the value is always there: ERROR is entered by `machine_error` or by an engine machine error, and both ways write a record, 3.3) and catalog functions; the text of the whole record is `record_text(transition_note)`.

Example (the “Agent step” pilot). In the code `Time.now()` is read inside a branch, here the time is taken from the stamp of the event `event.at` (a read of the stamp leaves no trace). The reads of ERROR are `all_data`: `usage`, `agent_request` and the other names in its “On entry” are read from `all_data` as data.

```
### Halted — end
- On entry:
  - let current_time = event.at;
  - close_agent_turn();
  - if not has(usage) then { journal(usage_event(collect_usage(agent_request, stop_reason, transport_usage, started, current_time))) };
  - journal("agent_step_stopped", reason: stop_reason)
- Except: stop_reason in [""]

### Errored — end
- On entry:
  - let current_time = event.at;
  - close_agent_turn();
  - if not has(usage) then { journal(usage_event(collect_usage(agent_request, stop_reason, transport_usage, started, current_time))) };
  - journal(transition_note);
  - journal(all_data)

## Output

- Result: AgentReply

| end | when | response |
| End | true | Response(AgentReply { text: reply_text, artifact: reply_artifact, usage: require(usage), request_started: if has(transport_usage) then { require(transport_usage).request_started } else { none } }) |
| Errored | true | Refusal(FailCode.NoResult, "agent step defect: " + transition_note.code) |
| Halted | stop_reason == "no_result" | Refusal(FailCode.NoResult, stop_reason) |
| Halted | stop_reason == "model_refused" | Refusal(FailCode.ModelRefused, stop_reason) |
| Halted | stop_reason == "cost_limit" | Refusal(FailCode.MaxTokens, stop_reason) |
| Halted | Pause.reason == PauseReason.Halted | Refusal(FailCode.StoppedByHuman, text(Pause.reason)) |
| Halted | Pause.reason == PauseReason.Cancelled | Refusal(FailCode.Cancelled, text(Pause.reason)) |
```

Example (the “Meeting” pilot). `journal_findings`, `journal_decision` and `journal_machine_data` of the code are ordinary journal rows (the codes `unclosed_finding`, `meeting_decision`, `open_finding`, `machine_data`, [state-machine-journal.md](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-journal.md), section 2, subsection “Events of the table format”); severity is a value of the enumeration `Severity` (`"critical"`, `"significant"`, `"desirable"`), yes/no is `yes_no_word` (a function: `if b then { "yes" } else { "no" }`).

```
### Halted — end
- On entry:
  - open_for_writing("proposal");
  - journal("meeting_stopped", reason: stop_reason);
  - for f in open { journal("unclosed_finding", severity: text(f.severity), evidence: f.evidence, repeat: yes_no_word(f.repeat), question: yes_no_word(f.question)) };
  - for f in not_included_in(gate3_findings, open) { journal("unclosed_finding", severity: text(f.severity), evidence: f.evidence, repeat: yes_no_word(f.repeat), question: yes_no_word(f.question)) }
- Except: stop_reason in [""]

### End — end
- On entry:
  - open_for_writing("proposal");
  - journal("meeting_decision", decision: proposal, source: confirmation, passes: text(number));
  - for f in open { journal("open_finding", severity: text(f.severity), evidence: f.evidence, repeat: yes_no_word(f.repeat), question: yes_no_word(f.question)) };
  - journal("older_findings_in_pass_files")

### Errored — end
- On entry:
  - open_for_writing("proposal");
  - journal(transition_note);
  - journal(all_data)

## Output

- Result: MeetingResult

| end | when | response |
| End | true | Response(MeetingResult { decision: proposal, source: confirmation, passes: number, open: open }) |
| Errored | true | Refusal(FailCode.NoResult, record_text(transition_note)) |
```

(Not all rows of Halted are shown in the “Output” table: “Agent step” has 11 of them (including two by the reasons of the library “Pause”; [archive/state-machine-agent-step-states.md](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/archive/state-machine-agent-step-states.md), “end → response”; the example shows five), “Meeting” has 10, by the number of values of `stop_reason` without `""`. For “Meeting” four rows `stop_reason == "Witness_halt_meeting"` … `"AuthorQuestion_halt_meeting"` lead to `Refusal(FailCode.StoppedByHuman, stop_reason)`, the values are computed by FailedRequest, section 3.2.)

## 5. Actions

The words of actions (`journal`, `machine_error`, `pass`, `cancel_open`, `for`) are quoted in the English form; the Russian form is in the [word table](alula-keywords.tsv), the kind `action` (1a).

The actions in a cell are in the order of writing (rule 29), one per line of the cell through `<br>` (an HTML line break) or through `;`; parsing takes `<br>` as `; `; **every action sees the results of the previous ones** (after `retry_count += 1` the journal reads the new value). An acting external function (a call `name(arg)` of a function of the class `acting`) is executed at once, when the step reaches the call, before the step is written; its arguments are evaluated at the point of writing. **A departure from rule 13 (the outbound queue).** Rule 13 puts irreversible external actions as the last stage of the commit, after the step is written; the format does not do this yet: the repeatability of an acting function when a step is repeated is a requirement on the host, and execution after the step is written (a queue) is not implemented until a real host appears or the first double call. This is a departure, not a norm.

| Action | Meaning | Where |
|---|---|---|
| `field = expr`; `field += expr` | assignment; addition (int, f64, str, list) | rows, “On accept” |
| `field[key] = expr` | map: insertion or replacement; list: an existing index, otherwise a machine error | rows, “On accept” |
| `field[key].field = expr` | a short record of `field[key] = { ...field[key], field: expr }`; no key — a machine error, the record is not created; a party counter field (engine data) — a check error. Where the source calls an absent key a program defect (`unreachable`, `required`), `field[key] = { ...require(field[key]), field: expr }` is written (4.4) | rows, “On accept” |
| `field = without_key(field, key)`; `field = remove(field, element)` | removing a key and elements | rows, “On accept” |
| `journal("code", name: expr, …)`; `journal("code")` | a journal event: `code` is a string literal in Latin `snake_case` from the template table, the parameter values are `str`; the former record `journal(code)` without quotes is an error with a hint, there is no transition period | rows, “On entry” of an end, the body of `for` in the “On entry” of an end |
| `journal(value)` | an event assembled by `journal_event("code", …)` or `transition_note`; here a value-event stands without quotes, not a code | rows, “On entry” of an end |
| `journal(all_data)` | an abbreviation of `journal("machine_data", data: <data record>)`: the event `machine_data` with **one** parameter `data`; the encoding is below; the composition is in section 2. The name `all_data` in an expression is a record value (3.1) | “On entry” of ERROR |
| `let name = expr` | a binding until the end of “On entry” and for all rows of the state; also with a call of an external function, `let name = name(arg)` | “On entry”, “On accept” |
| `{ actions }` | an action block: the actions in order; `let name = expr` inside is visible up to the closing `}`; the block is not empty | rows, “On accept”, “On entry” of an operation and an end (4.5, 4.7), the branches of a conditional action, the body of `for`; not “On entry” of a fork (only bindings there, 4.6) |
| `if expr then { actions } [else { actions }]` | conditional; the condition is an expression without calls of volatile and acting external functions (pure functions and catalog functions are allowed) | rows, “On accept”, “On entry” of an end |
| `for name in expr { actions }` | a finite list or a range `a..b`, `a..=b`; the body — assignments, `+=` and the short record (in rows, “On accept”); `journal(…)` and `if` (in the “On entry” of an end); **the boundary of the body**: the body is a block `for x in xs { a; b }`, an action after `}` does not enter the body | rows, “On accept”, “On entry” of an end |
| `name(arg, …);` | a call of an acting external function as an action (`close_agent_turn();`); for a function without a result — only so: the call does not stand in an expression or to the right of `let`; admissibility by class — section 7; executed at once, before the step is written (a departure from rule 13, above) | by class |
| `machine_error("code", name: expr, …)` | the journal `code` (a string literal) and the end ERROR; “To” is empty; the only entry into ERROR by the will of the table (the second is an engine machine error, 3.3); after both `transition_note` is defined | rows, common events |
| `pass(nested, signal)` | the signal `Signal` to the machines `nested` (a library parameter, section 9) from `open_requests` at the moment of the action (the addressees are taken at the point of writing, before the `cancel_open` of the same row), sent after the commit; the journal `signal_passed` for each | library only |
| `cancel_open[(except: nested)]` | cancel the open requests without an accepted response (rule 18): with `except: nested` — except the requests to the named nested machines, without an argument — all, including the nested ones; the effect is by the parameter `request_cancel` (section 9); returning the parties of the cancelled requests of a set to `to_send` is rule 18, for any value of the parameter; it is disabled only by `without_return_to_send`, and only in COMMON 1, 2; the change of `open_requests` and `to_send` is contract mechanics (rule 29), the check of writes into engine data does not count it as a row write | library only |

**A conditional action**. The branches of a conditional action are written in braces, as a block in Nova: `if has(copy) then { proposal = require(copy) } else { journal("copy_restore_no_copy") }`; a branch holds one action or a list joined by `;`; `else { … }` is optional. The word `then` is required: the condition is an expression, an expression may end with a type name (`if x == Type.Var`), and the record `if x == Type { … }` would read as a comparison with a record or form literal `Type { … }`; `then` marks the end of the condition. A branch is not empty: a block `{ }` without content is a check error; an unneeded `else` branch of a conditional action is not written (for a conditional expression `else` is required). The conditional **expression** also writes its branches as blocks, one expression per block: `if expr then { expr } else { expr }`, `else` is required (3.1); `then` is needed there for the same reason.

**The forms of `let`**:

| Form | What it is | Where | Scope |
|---|---|---|---|
| `let name = expr` | a binding action | “On entry” of an operation, a fork and an end, “On accept” (outside a block) | until the end of “On entry” and for all rows of the state; in “On accept” — with the accepted event, its row and chain (2, “Lifetime of data”) |
| `let name = expr` inside `{ … }` | a binding action in a block | any action block: rows, “On accept”, “On entry” of an end, the branches of a conditional action, the body of `for` | up to the closing `}` of the block |
| `let name = expr;` inside a block expression `{ …; expr }` | a binding in a block expression | any expression position: a block body of a function, the branches of a conditional expression, expression cells | up to the closing `}` of the block |

`let` has no word `in`: a local binding in actions is the block `{ let name = expr; actions }`, in an expression — the block expression `{ let name = expr; expr }`.

**Product journal codes**. The code in `journal("code", …)` and `machine_error("code", …)` is a string literal; it is taken from the template table of the [journal](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-journal.md) (section 2 and the subsection “Events of the table format”) — these are the methodology codes. A product that needs its own events (a record of engine mechanics: an edit of a response under “Edits”, a form return, a request repetition, an order of a signal — for example `answer_edited`, `form_returned`, `request_repeated`, `signal_ordered`) declares them by a **product template table** of the same form (`Machine | Event code | Russian template | Parameters`) next to the methodology table; where it lies is named by the host registry (as libraries, section 9). Rules: a product code is a Latin `snake_case` by the rules of a journal code; it does not repeat a methodology code (a coincidence is a check error, even with the same template); a code that the format itself or the contract mechanics writes (`signal_passed` of `pass`, `input_rejected`, `machine_error`, `machine_data`, the codes of the “Pause” library) is not replaced by the product with its own code: its own event (for example, `signal_ordered` when a signal is ordered before the commit) is written next to the methodology code, not instead of it. The check (section 10) compares the code and the parameters of a row with the union of the two tables; a code outside the union is an error. The methodology script [check-tables.py](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/check-tables.py) reads only the methodology table; the product table is read by the product check. Product codes are not entered into the methodology table.

**Encoding of `journal(all_data)`** (checked by an implementation). The event `machine_data` with **one** parameter `data`. The parameter value is pairs `name=value` (the name is the JSON name of the datum, 1a), the separator is `; ` (a semicolon and a space); the order is the order of the rows of the “Data” table of the machine (first the data of the included libraries in the order of inclusion, then the data of the machine); field paths inside a map (`name[*].field`) are not in the composition — they are part of the map value. The value of a pair:

| Value | Record |
|---|---|
| integer | decimal record |
| f64 | `text(x)` (the shortest reversible record, an integral one with `.0`; 3.3) |
| text, literal set, `id` | as is, without quotes; empty text is empty after `=` (`stop=`) |
| `bool` | `yes`, `no` |
| optional `none` | `none` |
| enumeration | the value of the element (the Latin text of the code); for an element without a value — its JSON name |
| `State` | the JSON name of the state |
| list | a JSON array `[…]`; empty is `[]` |
| map | a JSON object `{…}`; empty is `{}`; for a map with non-text keys — an array of pairs `[[key,value],…]` in the order of writing the keys (section 2) |
| record | a JSON object; the keys are the JSON names of the fields, the order is the order of the type's fields |
| enumeration with fields | a form with fields — `{"Var":{fields}}`; without fields — the string `"Var"` (JSON names) |
| tuple | an array; positions in order |

Composite values are encoded in JSON without loss: without spaces (the separators `,` and `:`), UTF-8, non-ASCII signs are not escaped, text escaping is by RFC 8259 (`\"`, `\\`, `\b`, `\f`, `\n`, `\r`, `\t`, other control signs — `\u00xx` in lowercase); inside a composite, text is a JSON string, `none` is `null`, `bool` is `true`, `false`, float is a number by `text(x)`, an enumeration and `State` are a string by the table rows. Encoding and parsing back and forth are without loss: Cyrillic and 4-byte letters are preserved, integer and float are distinguished (`1` and `1.0`). An integer (`int`, i64) in JSON is a number: values above 2^53 in magnitude may lose precision in JSON readers that store numbers as f64.

Examples (`data=` is the name of the event parameter): `data=count=0; label=abc; began=1000; log=[]; table={}; stop=` and `data=total=99; label=; log=[]; counts={}; items={}; p_attempt=0`; the map `lenses map[str, Lens]` (the fields of `Lens` with the JSON names `id`, `lost`, `probes`, `attempt`) — `lenses={"l1":{"id":"l1","lost":0,"probes":0,"attempt":2}}`; `turn_before_retry=none` — an empty optional `turn_before_retry` (in the Russian sample the datum `ход_до_повтора`, its JSON name is automatic).

## 6. JSON tree

**The file name of the tree**. A tree compiled from `<name>.alula.md` lies next to it in `<name>.alula.json` (`agent_step.alula.md` ↔ `agent_step.alula.json`). JSON is the executable form of the language itself, not another format: a hand-written tree is also Alula in the JSON form; the root key `"kind": "machine"` does not change. The former name `*.machine.json` is not used and loading does not accept it. The rules by which a tree is written back to an Alula file are in section 1b.

**The language version in the tree**. The root of the tree carries the key `alula_version` — the format version with which the tree was compiled (a string; for this version — `"0.27"`); the key is optional: without it the tree is of the version that the program reads. A program reads exactly one format version: a tree with another `alula_version` is an error whose message names the version (there is no transition period). The key `kind` (`"machine"`) is the kind of the root (for a test file — `"test"`, section 11); there is no schema number after a slash: the schema is bound to `alula_version`; there are no keys `format` and `table_format`. The key `revision` is the revision of the machine (an integer, `1` by default; in the file header — `- revision:`, 1b).

The JSON tree and its schema are outside this file: the schema of the machine tree and the schema of the test file live in the repository of the language, [nv-lang/nova-alula, folder `src/machine/schema/`](https://github.com/nv-lang/nova-alula/tree/main/src/machine/schema); the schema version is kept by the package `alula`, the keys in it are English; the schema is the first source of the structure of the tree, this file is the source of the rules of the record and of the correspondence of words to keys. The tree is the same for a Russian and an English file: the words of both languages correspond to one key and one value (the word table, 1a); the party kind “human or agent by setting” is called `gatekeeper` in the tree (section 1). Listed here are the constructs of versions 2, 2.1, 2.2 and 2.5 (versions 2.8–2.23 have no new nodes: the tree does not depend on the file language, 1a; `—` in the cell “expression” of the “Request” table gives the name expression of the field in the tree, as the former record; version 2.7 has one new key — `words`, in version 2.13 it is called `values`, below; versions 2.3, 2.4 and 2.6 have no new machine nodes: the result by role (before 2.24) is a record of the host registry; version 2.5's new nodes are the literal set and the type `id`) that need nodes (some of them had no nodes in version 1): `in` of `failure`, “when” and “Except” of ends, “On entry” of a fork, an operation and an end, the alternatives `|` in `match`, the literal sets `"a" | "b"` (in the JSON schema — a list of strings `enum`: a word of the schema, not a type node of the tree), the type `id` (a string of UUID format: `^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$`), `int>=n`, `?`, a tuple, a full map, `non_decreasing, <= expr`, the field path `name[*].field` in the “Data” and the short record `name[key].field = expr`, `unreachable`, grouping parentheses, a call with named arguments, a party identifier, `parse` of a party `machine`, `Edits` with `check`, `Initial state`, `for` with `journal` at the end, an include with parameters, `signal(…)` with fields (a party signal and a machine signal), a field binding with renaming, “On accept”, `let` in “On entry”, a conditional action, `journal_event`, `journal(value)`, a set of parties, a party `machine`, the `## Input` of a machine with invariants, the values of enumerations; from version 2.2 — `result` of a party and `GateOutcome`, the column `counter`, the qualified `response: Type.Form`, `cancel_open` without an argument, `require_non_empty`, the header of a library. **Version 2.19** introduces no new nodes: `a..b` is a call node `range` with the arguments `a`, `b`, the same as of the former `range(a, b)`; a list function method call `xs.filter(x => expr)` is a list function call node with the receiver as the first argument (`call fn=filter args=[xs, lambda]`), the same as of the former `filter(xs, x => expr)`; an event pattern `Var { … }` and a signal with fields `s { … }` are the former pattern nodes; the set after `in […]` is the former node of a set of values; a literal with insertions is a call node of the catalog function `concat` (section 12; the schema does not change, the catalog has a new name): the parts of a literal are the text fragments and the insertions in order, empty fragments are dropped; a literal without insertions is the literal itself; a single insertion part (`"${x}"`) is `text(x)`; otherwise it is a call `concat(…)` with the parts in order, at least two arguments, an insertion being `text(x)`: `"${file}:${line}"` is `concat(text(file), ":", text(line))`, `"a${x}"` is `concat("a", text(x))`; back, the generator writes as an insertion only a call `concat` of the canonical form (1b, a recommendation). **Version 2.20** introduces no new nodes: the declaration of a signal `s { field type }` is the former node of a party signal with fields, the alternative `Var { field, field: name }` is the former node of a form alternative with bindings (the same as for the former record `Var(…)`). **Version 2.21** introduces no new nodes: a function (`fn`/`функция`) is the former function node, the declaration word does not enter the tree; a block body `-> Type { … }` is the former body with a block expression (the same as for the former record `=> { … }`); a map literal `[k: v]` is the former map literal node (the same as for the former record `{k: v}`), `[]` with an expected map type is an empty map; `a..=b` is a node of the call `range` with the arguments `a` and `b + 1` (an addition node). **Version 2.22** introduces no new nodes: `match` branches through `,` or a line break are the former `match` node; a bare name of an element or of a form without fields is the former value node, the same as of the qualified `Type.El` (the type is taken from the enumeration that declares the name); an enumeration without `=` and the value `El = "value"` are the former type node in the array `variants` with the key `values`; the comment `//` does not enter the tree; a number literal is the former integer and float nodes by value (`1_000` is `1000`, `1e-7` is a float); an escape is a sign in the value of the string; the English type words of the file `str` and `f64` give the former words `text` and `float` in the tree (`int` and `bool` coincide), the English loop `for x in` is the former node of `for`; an enumeration `type Name enum …` is always a type node in the array `variants`, the forms have fields or not: the tree has no separate `enum` node; the element values are pairs of the key `values` on this node (below), the generator writes `= "value"` at the forms with a value in `values` and fields at the forms with fields; the membership sign `in` (Russian `в`) is the former node of a set of values. **Version 2.23** introduces no new nodes: the journal code in `journal("code", …)` is a string in the former field `code` of the node of the action `journal`, the pairs `name: value` are the former list `params`; the class of an external function is a word of the host registry entry and does not enter the tree (since 2.24 the class enters the tree, below); the column `writes` is removed since 2.26, the datum has no field `writes` in the tree. **Version 2.24** changes only the list of external functions, the other nodes are the former ones: instead of `primitives: ["name", …]` the tree carries `primitives: [{ "name", "params": [{ "name", "type" }], "result", "class" }]` — one entry for each declared external function (section 7): `name` is the JSON name (1a), `params` are the parameters in order (name and type, the type written by the type words of the tree), `result` is the result type (the key is absent if there is no result), `class` is the class, a word `en` of the word table (`pure` for a pure function, `volatile` and `acting` for the others); a call of an external function and an action-call are the former call and action nodes; the former form `call` is not in the tree; `parse` of a party `machine` no longer has a role literal (a parse function and the type after `->`); the root of the tree carries `"kind": "machine"` and the key `alula_version` is `"0.27"`. The pre-declared function (`new_id`, 7a) does not enter `primitives`: it belongs to the language and is not declared in the file; its calls are the same call nodes by name. The named tail `...name: Type` is written in `params` as the record `{name, type, tail: true}`. **Enumeration values**. For an enumeration with values (section 2) the type node in the array `variants` carries the key `values` (before version 2.13 — `words`) — a list of pairs “JSON name of the element → value” in the order of declaration (`[["NoResult", "no_result"], …]`); the key is only at a type node whose elements have values. The encoding of `all_data` (section 5) and `text(x)` take the value from `values`; an element without a value gives its JSON name. **Names in the tree** are JSON names (1a): automatic or from `## Names`, the tree does not depend on how the name was obtained; the section `## Names` has no node of its own in the tree. **The party counter**: the key of the party counter may be absent — so the tree carries a party of the kind `human` with free input (`—` in the column `counter`, section 1); how this is expressed in the schema is decided by the product. the `Request` table of an appeal is the key `inputs`; the reads of a state stay in the tree as the derived — the key `reads` is filled by the check (there is no `Reads` line in a file), and the request field key `to_party` means “the field goes to the party”. The include of a library of functions, types and constants is `includes: [{ "name", "hash" }]` and a copy of its types, constants and functions in the machine tree: the interpreter needs only one tree.

## 7. External functions and admissibility of classes

An **external function** is a function of the host that the machine calls: reading the world (a clock, files, a store, objects), parsing the text of a response, an external action. The machine file **declares** every external function it calls by a line of the section `## External functions` — without a body:

```
name(arg type, …) [<class>] [-> type]
```

The Russian notation is the same, `имя(арг тип, …) [<класс>] [-> тип]`; there are no words “external function” in the declaration. In the registry and below external functions are also called primitives: “primitive” and “external function” mean the same. **The internal functions of the author** (with a body in the language, section 8) are always pure and have no class.

- **The class** is the word after the parameter list: `volatile` (Russian `изменчивая`) or `acting` (`действующая`); a pure function has no word. Three classes: **pure** (reads only its arguments, neither reads nor changes the world), **volatile** (the result depends on the world), **acting** (changes the world).
- **The result** `-> type` may be absent; for an acting function without a result this is the only notation.
- **There is no body**: a declaration is one line in a code block under the heading `## External functions`; an empty section is not written. A declaration outside a code block is a comment (a paragraph) and a check warning (1a).
- The last parameter may be a **named tail** `...name: Type` (3.1).
- **The name.** An external function occupies the call namespace (1a, namespace 11); its JSON name is the name in the host registry: for a non-Latin name it is built automatically (1a; `профиль_стороны` → `party_profile` by the glossary), and if the registry name is different it is set by a `## Names` row.
- **The call** of an external function is an ordinary `name(arg)` in any allowed place; the position of a call is defined by the class in the declaration (the table below). A call of an acting function without a result is a row action `name(arg);` (section 5). There is no separate call form: the former notation `call(name, …)` is a check error (“the former notation `call(name, …)` is an error; write `name(…)`; there is no transition period”).
- **Pre-declared** function `new_id()` is not written in the file (7a); the machine reads the time as `event.at` (the readable names of the engine, rule 11).
- In a **library** (section 9) external functions are forbidden.

Pure functions over data may be written not here but in “Functions” (section 8); external remain text parsing, reading objects, time, closing a turn, effects and functions without a body in the source (below).

| Class (the word in a declaration) | What it does | The call `name(arg)` is allowed |
|---|---|---|
| pure (no word) | reads only its arguments, neither reads nor changes the world; machine data are passed to it as arguments | everywhere an expression is allowed, in conditions included |
| `volatile` | the result depends on the world — a clock, files, a store, objects; does not change the world (the former `reading`) | in the “Request” of an appeal, in `profile`, in the “On entry” of an operation, a fork and an end (in `let`), in “On accept” (in any position of an expression, 3.1) and in row actions; as `parse` of a party `machine` and `check` of the property “Edits” (4.2); not in row conditions; `new_id` — only in `let` of the “On entry” of an operation (below) |
| `acting` | changes the world — machine data, objects, a buffer, an external action (the former `writing` and `irreversible`) | in the “On entry” of an operation and an end (including `let name = name(arg)`) and in row actions; not in conditions, not in the “Request”, not in `profile`, not in the “On entry” of a fork, not in “On accept”; a call of an acting function without a result does not stand in an expression or to the right of `let` — it is a row action `name(arg);`; in the “On entry” of an end it must be harmlessly repeatable by the host (an end is entered again, rule 22) |

**The check against the host registry at load.** The host keeps a registry of its external functions: a registry entry is `name`, `parameters` with types, `result`, `class`, `reads`, `writes`, a note. At the load of a machine every external function declared in the file is checked against the registry: the name is found (by the JSON name of the declaration); the number and types of parameters; the result type; the class. A difference is a check error with the name of the function and the difference (an example of the text: “function write_status: parameter 2 in the file is int, in the registry str”); a function absent from the registry is an error; extra functions in the registry are allowed (the file declares only those it calls). The hidden reads and writes (`reads`, `writes`) are taken from the registry, not from the file: a declaration has none.

- `reads:` — machine data, objects, service records that the function reads hidden (not through arguments). These names enter the derived reads of the state at the point of the call (rule 11). For a pure function the column `reads` is empty (`—`): it reads only its arguments. For volatile and acting functions the column stays (in 2.24 this is narrow: narrowing `reads` to the world alone, with machine data passed as arguments, is a candidate, see the [changelog](alula-changelog.en.md), “Open items”).
- `writes:` for an acting function — the machine data that the function changes in place; the check “writes ⊆ data” counts it. For a volatile function — only service records of the engine (not machine data, not objects); the record names who reads it (the function or the turn mechanics) so that the dependence is visible (for example, the remarks of the form check for the turn “fix”).

**The execution of an acting function and rule 13 (the outbound queue).** An acting function is executed at once, when the step reaches the call, before the step is written; the repeatability when a step is repeated (an unfinished step is rolled back, rule 12) is a requirement on the host: execution after the step is written (a queue) is not implemented until a real host appears or the first double call. This is a departure from rule 13, not a norm; execution of irreversible calls as the last stage after writing is not a norm.

Example (pilots): the section `## External functions` of a machine file. The class stands after the parameter list, before `-> type`; `close_agent_turn` and `remove_unsound` have no result; `not_included_in` and `merge_unique` are pure (no class word); the three parse functions are one per role (below).

```
reply_validation() volatile -> ReplyCheck
close_agent_turn() acting
remove_unsound(number int>=1) acting
proposal_fingerprint() volatile -> str
proposal_changed_since_attempt() volatile -> bool
parse_witness_reply(result AgentReply) volatile -> []WitnessAnswer
parse_author_reply(result AgentReply) volatile -> EditResult
parse_lens_reply(result AgentReply) volatile -> LensResult
lenses_without_critical() volatile -> []str
not_included_in(findings []Finding, among []Finding) -> []Finding
merge_unique(first_list []Finding, second_list []Finding) -> []Finding
all_lens_findings(number int>=0) volatile -> []Finding
build_summary(number int>=1) volatile -> ?Summary
```

Example of the host registry for the same functions (pilots; `reads` and `writes` are only in the registry). For `reply_validation` the hidden reads and the write are named; for `remove_unsound` — the reads and the written data; `proposal_fingerprint` and `proposal_changed_since_attempt` — functions for a nested read and for `Edits` (4.2, 4.6); functions without a body of different classes, including the pure `not_included_in` and `merge_unique`, and `build_summary` (see below). The journal functions `journal_findings`, `journal_decision` are not in the registry: these are journal rows (4.7). The standard `new_id` (7a) is entered into the registry by the host itself.

```
| name | parameters | result | class | reads | writes |
| reply_validation | — | ReplyCheck | volatile | reply_text, reply_artifact, agent_request; objects: session files | service record “form remarks” (read by the turn “fix”) |
| close_agent_turn | — | — | acting | — | — |
| remove_unsound | number int>=1 | — | acting | lens_order, lens_findings, witness_answers | lens_findings |
| proposal_fingerprint | — | str | volatile | objects: proposal (not read — `unreachable`) | — |
| proposal_changed_since_attempt | — | bool | volatile | objects: proposal; service record: fingerprints of the attempt (written by the engine when the request is sent) | — |
| parse_witness_reply | result AgentReply | []WitnessAnswer | volatile | objects: reply artifact, proposal | service record: remarks of the excerpt comparison (read by the party return) |
| parse_author_reply | result AgentReply | EditResult | volatile | objects: reply artifact | — |
| parse_lens_reply | result AgentReply | LensResult | volatile | objects: reply artifact | — |
| lenses_without_critical | — | []str | volatile | lens_order, lens_findings, number | — |
| not_included_in | findings []Finding; among []Finding | []Finding | pure | — | — |
| merge_unique | first_list []Finding; second_list []Finding | []Finding | pure | — | — |
| all_lens_findings | number int>=0 | []Finding | volatile | lens_order, lens_findings | — |
| build_summary | number int>=1 | ?Summary | volatile | lens_order, lens_findings, lenses | — |
```

**`new_id`** (a standard external function of the language; the Latin name in the host registry and in JSON is `new_id`, a word of the word table, the kind `catalog`; the host implements it through `Uuid.v7()` with the time and randomness effects — this is a host detail). Without parameters, the result is `id` (section 2), class `volatile`, `reads` and `writes` are `—`; the result is non-deterministic: the value is issued by the engine. The non-determinism is removed like this (Start, section 4.5): the value enters a `let` binding and is fixed in the record of the step (saved together with the step); when a step is repeated (rules 12–13) it is taken from the saved value, not issued again. Therefore `new_id()` is allowed **only** in `let` of the “On entry” of an operation with the binding written into data by the row of the operation. A conservative decision: in the “Request” of an appeal it is not allowed even with `reads: engine` — the “Request” is evaluated again on re-entry and a new request (4.2, rule 12), and the value would change; in a fork, an end, conditions, actions, `profile` — also not (section 10).

Example (an illustration; the datum `session_id` is `?id`, initial `none`; a state not from a pilot; in the Russian form the state ОТКРЫТИЕ gets the JSON name `Opening` by the row `| ОТКРЫТИЕ | Opening |` of `## Имена`, the transliteration would give `Otkrytie`).

```
### Opening — operation
- On entry: let fresh_id = new_id()

| session_id = fresh_id | AgentTurn |
```

**A parse by role.** Each role of parsing a response has its own volatile external function: `parse_witness_reply` (the result `[]WitnessAnswer`), `parse_author_reply` (`EditResult`), `parse_lens_reply` (`LensResult`); a party `machine` names it in `parse:` without arguments (section 1). The check (section 10) compares the first parameter of the function with the `result` type of the party and the result with the type after `->` of `parse`: different types are a check error. The hidden reads of each function are its own (the witness function also reads the proposal): the reads of a state include the reads of the parse function of its party. The former single function `parse_agent_reply(result, role)` with the table `by role {…}` in the registry and a text role literal in `parse:` are a check error (“since 2.24 — a separate function per role”), there is no transition period.

The other external functions of the examples (`party_profile`, `role_context`, `close_for_writing`) are declared in the same way; the functions `add_usage`, `collect_usage` are not spelled out in the examples, their records are in the excerpts of the pilots. The hidden reads of `remove_unsound` are `lens_order`, `lens_findings`, `witness_answers`.

**A function without a body in the source** (decision of the methodology, 2026-10-19): a function that has no body in the source (in the automaton code only a signature) is written as a **host external function** with a class and a description by the tables of the primary source; it will become a function in the language when the body appears in the source (then the declaration is moved to `## Functions`). One rule for all such functions, pure or not; **the class is by the signature of the source**: a free function without `mut` and without `Objects` is pure (called as `name(arg)` everywhere); a method of machine data without `mut` or a function with `Objects` without `mut` is `volatile` (reads data or objects, changes nothing); with `mut` — `acting` (writes data, objects or a buffer, performs an external action); the former distinction of `writing` and `irreversible` is removed. This includes all such functions of the automata that the tables of “Meeting” call: pure — `merge_unique`, `not_included_in`, `has_critical`, `desirable`, `desirable_and_significant`, `desirable_and_significant_repeated`, `critical_and_significant_not_repeated`; `volatile` — `has_reviewer_questions`, `reviewer_questions`, `all_lens_findings`, `lenses_without_critical`, `build_summary` (the row of SummaryBuilding writes `summary[…]` by the result, the function itself does not change data), `proposal_changed_since_attempt`; `acting` — `remove_unsound` (writes `lens_findings`) and `count_in_model_tally` (the tables do not call it). The journal functions without a body (`journal_findings`, `journal_decision`, `journal_machine_data`) are written by the format as journal rows (4.7). The pilot count counts such functions as written as external functions. Bodies are not entered into the automata by this.

### 7a. Standard external functions, the host contract and journal codes of the language

The language names only what every host and every engine must provide; the rest the host registers itself (section 7), and the journal codes come from the tables of their owner (the journal of the methodology, the journal of the product).

**The standard external function** (pre-declared by the language, not written in a machine file; class `volatile`; without it an identifier cannot be written): `new_id()` (Russian `новый_ид()`) — `() -> id`, section 7 and the catalog (section 12). Time is not a function: the machine reads the stamp of the event `event.at` (an integer, milliseconds since 1970-01-01 UTC); it comes with the event and is the same when a step is repeated, so a step is reproducible and a test sets the time in the event itself. All other external functions are the host's data: the methodology supplies its own (54 in the registry of package 0.3.2: agent step, meeting, session start, task runner), the product its own.

**The host contract.** The host binds the implementations of external functions one function at a time: `bind_pure`, `bind_volatile`, `bind_acting` — by the class of the function; at load every declared external function is bound (an unbound one is a load error). The class of an external function is told by the type of its environment: a pure one gets none, a volatile one gets an environment without write methods, an acting one gets a writable environment; the compiler checks it. Not proven by types: that the implementation does not use output, files, clock or network behind the environment, or capture outside mutable state; this is covered by the import guard, --strict-effects (partly) and the test host. The contract belongs to the host, not to the machine file: it cannot be written in a file.

**Journal codes of the language** — the codes written by the format itself, by the library “Pause” and by the engine; a host does not redefine them. (a) the format: `signal_passed`, `input_rejected`, `machine_error`, `machine_data`, `fork_no_match`; (b) the library “Pause”: `human_stop`, `pause_by_parent_stop`, `cancel_discarded_foreign_request`, `cancel_discarded_already_replied`, `request_cancelled`, `cancel_parse_no_match`, `human_continue`, `parent_continue`; (c) the engine: `machine_started`, `event_accepted`, `reply_discarded`, `request_ordered`, `request_sent`, `request_repeated`, `request_closed`, `cancel_ordered`, `cancel_sent`, `cancel_without_request`, `snapshot_ordered`, `machine_finished`, `engine_resumed`, `signal_ordered`, `machine_defect`, `event_ignored`, `event_unknown`, `event_malformed`, `answer_held`, `answer_replayed`, `answer_edited`, `form_returned`. The parameters and text templates of these codes are in the journal table of the language in the package; codes of the methodology and of the product are not in this list.

**The library `contract`.** It is built into the language and included implicitly: it is not written in `## Includes`, it has no file (section 9). It names what every host and every engine gives to a machine; its names are visible in the machine without a prefix.

- **Types.** `FailCode` (Russian `КодСбоя`) is an enumeration of failure codes with values for the journal: `NoResult` = `no_result`, `ModelRefused` = `model_refused`, `ConnectionLost` = `connection_lost`, `FormNotFixed` = `form_not_fixed`, `Timeout` = `timeout`, `StoppedByHuman` = `stopped_by_human`, `CeilingReached` = `ceiling_reached`, `Cancelled` = `cancelled`, `MaxTokens` = `max_tokens`, `MaxTurnRequests` = `max_turn_requests`. A machine need not declare `FailCode` (a repeated declaration is an error: the name is taken); a product adds its own codes by its own library, not by extending this enumeration.
- **Engine data.** `call_request_id` (`str`, initial `""`: the identifier of the request by which the machine was started) and `open_requests` (`[]str`, initial `[]`). Only the engine writes them; a write to them from a table row, from “On accept” or from an acting function is a check error; they can be read by name. These data have no column `writes`.
- **Party events.** `response`, `failure(code)`, `part(fields)` and `timeout` (4.3). A `part` is a piece of the response that a party sends before the response: `part`, `part(name)` or `part { field, field: name, … }`. The type of a part is an ordinary type of the machine or of a library (`type ResponsePiece record { content str }`); what a party sends is named by the column `parts` in `## Parties` — by the pattern of the column `signals`; a part outside this column is a check error. A part without a row in the current state is dropped, like a superfluous party signal (rules 14, 17, 19). The silence timeout (4.2) is counted anew on every arrived `part` of the party.
- The words `part` and `timeout` and the action `party` are words of the language ([word table](alula-keywords.tsv)), not words of a product.

## 8. Functions, constants, parameters

**A function** (the declaration `fn`, Russian `функция`) is a pure function of the author (the internal author functions, with a body in the language, are always pure and have no class; the external host functions are in section 7), its body is one of two (as in Nova): `fn name(arg type, …) -> type => expr` is a body of one expression; `fn name(arg type, …) -> type { let name = expr; …; expr }` is a block body: zero or more bindings `let name = expr;` and lastly one expression, its value is the value of the function. `=>` and `{ … }` are not combined: `=> {` after a header is a check error; after `=>` stands one expression, a multi-line one included (`if … then { … } else { … }`, `match … { … }`), and `{` after the result type always opens a block body, so a record copy as the whole body is written in parentheses: `=> ({ ...r, field: expr })`; an empty block body is an error. A `match` branch is the exception, as Nova's `match` arm: `alt => expr`, `alt => { let …; expr }` included (3.1). A “function” without a qualifier in this specification is an author function; the functions of section 12 are catalog functions. Arity 0 is allowed; there is no recursion. A constant is a named value with a type. A parameter is a default value and a project override (`project.<key>`).

Example (pilots; `usage_event` instead of the event function of the code, a tuple key; `yes_no_word` — for the values of journal parameters, 4.7; `merge_unique` is a host external function: it has no body in the source, section 7).

```
fn sum_ints(a ?int, b ?int) -> ?int =>
  if has(a) and has(b) then { (a ?? 0) + (b ?? 0) } else { a ?? b }

fn yes_no_word(b bool) -> str =>
  if b then { "yes" } else { "no" }

fn usage_event(u Usage) -> JournalEvent =>
  journal_event("agent_usage", session: u.session, result: u.result, model: u.model.id,
                input: text(u.tokens.input), output: text(u.tokens.output), reasoning: text(u.tokens.reasoning),
                cache_read: text(u.tokens.cache_read), cache_write: text(u.tokens.cache_write), cost: text(u.cost))
```

**Libraries.** Functions common to several machines lie in an included file — a library (section 9) — and are included by a subheading of the section `## Includes`. A library may carry only `## Functions`, `## Types` and `## Constants` (the example is “cycle_arithmetic”, section 9); names from it are visible in the machine without a prefix.

## 9. Libraries

A library (rule 36) is an included file of the format `library`; the former “fragment” and “functions file” are its special cases. A library carries what several machines share: functions, types, constants and, if needed, data, common events and states.

**The file.** The header `# Library: <Name>`, list items `- library: <latin_name>`, `- alula_version: 0.27`, optionally `- language: ru`/`en` (1a). Sections in order, **all optional**, an empty section is not written: `## Parameters`, `## Requires data`, `## Requires parties`, `## Requires ends`, `## Types`, `## Names` (1a), `## Constants`, `## Data`, `## Functions`, `## Common events`, `## States`. `## External functions` are forbidden in a library (neither as a declaration nor as a call, the standard `new_id` included); there is no `## Includes` in it: a library does not include other libraries (there are no cycles by construction).

**Parameters** — a table `name | type | comment`. The type is an ordinary type (section 2); a closed set of words is written right in the type: `"mechanics" \| "without_return_to_send"`. There are no special kinds of parameters, a parameter is a value of an ordinary type: a party signal is a parameter of type `str` (a parameter name in the signal position of an event, `signal(halt_signal)`, is checked against the column `signals` of the party), a list of names of nested machines is `[]str`, a list of words is a literal set; a note for the reader is a `//` comment, not a parameter. Parameters are local constants of the library: in its text they are read by name (`halt_signal`), without `<…>`, and cannot be changed. An include names the value of every parameter; an omitted parameter, an extra parameter and a value of a wrong type are a check error.

**Requires** — what the library takes from the head machine; three sections, each optional. `## Requires data` — a table `name | type`: the data of the head machine that the library reads or writes; the type is an ordinary type of a datum of the machine. `## Requires parties` — a table in the form of `## Parties` (`name | kind | signals`, there are no columns profile and counter): the parties of the machine whose signals the library accepts; the kind is the same, and the signals named by the library are among the signals of the party of the same name in the machine. `## Requires ends` — a table `name`: the names of the ends of the machine (`Halted`, `Errored`) that the library uses. The types are checked for compatibility when the library is compiled (against these types, without a machine) and at the include; the existence of the name, the kind and signals of a party and the type of a datum in the machine — at the include; a mismatch is an error with a clear text (“library X requires the datum `name` of type …; the machine has none” or “… the machine has type …”; for a party and an end — “requires the party/end `name`”). The former single `## Requires` is an error with a hint (“since 0.27 three sections”). A library does not write into the data of the machine for the sake of its own values: it has its own data and enumerations for that, and the machine reads them with the instance prefix (so “Pause” keeps its own datum `reason` of type `PauseReason`, the machine reads `Pause.reason`). There are no names of parameters inside a type in `Requires data`. Every reason of the enumeration of a library that the machine gets through the end `Halted` must be named in the rows of `## Output` (section 10).

**Visibility.** The functions, types and constants of a library are visible in the machine without a prefix (`PauseReason.Halted`, `FailCode.NoResult`); a coincidence with a local name or with a name from another library is a check error; functions, types and constants do not use the parameters and the data of the library (they are the same for any instance; the needed value is passed as an argument) — otherwise an error when the library is compiled. Data and states carry the instance prefix: `Pause.previous`, `Pause.reason`, `To: Pause.Pause`. The default instance name is the name of the library (`# Library: <Name>`); `- Name:` in the include sets another. In the text of the library itself its data, types and states are written without a prefix. A library with states and common events is included once.

**The include.** In `## Includes` — a `###` subheading per library (the name is the name of the library), key lines and a table of parameter values:

```
## Includes

### Pause
- File: libs/pause.alula.md
- Hash: 429adaba4cec
- Name: Pause2             // optional

| parameter | value |
|---|---|
| halt_signal | "halt" |
```

- **File.** A path relative to the machine file; if not found there — searched in the folder of the `--lib` option or of the project setting. Only the library `contract` (7a) is built into the language: it is included implicitly, neither `File` nor `Hash` is written for it.
- **The English twin.** A library in Russian has a twin in English beside it: the name with `.en` before `.alula.md` (`libs/pause.alula.md` ↔ `libs/pause.en.alula.md`). A translation of a machine into another language (`alula convert --language en`) translates all its libraries too: it writes the twins beside, and in the translated machine it puts the path and the hash of the twin; if a library is not available for translation, it is an error with the list.
- **Hash** — the first 12 signs of the SHA-256 of the file content in UTF-8 after normalization: a leading BOM is dropped (a file with and without a BOM give one hash); line breaks are LF (CRLF and a lone CR are replaced by LF); trailing spaces and tabs are removed from every line; at the end of the file there is exactly one LF (empty lines at the end are removed, a missing LF is added); the 12 signs of the hash are hexadecimal, in lowercase. The normalization is unambiguous: a file without a final LF and a file with it give one hash. There is no library version in the include — the hash replaces it; a mismatch of the hash is a check error, not a warning.
- **The table of values** names all parameters of the library; a value is an expression of the type of the parameter, a literal included.
- The states, events and data of a library enter the machine and are not repeated in its sections: in `## Includes` there are **only** subheadings with keys and tables (prose is a check error); in `## States` writing the heading of a library state (`### Pause — appeal`) is forbidden — a repeat of a state that the library brought is an error (“declared twice”). There is no reference section with an expansion of a library: what it brings (parameters, requirements, data, events, states) is described by its file; in the section `## States` of a machine a paragraph-reference (prose, 4.1) stands if needed.
- **The old form.** An include line `functions: <name> version <N> hash <hex12>` and an include of the form `Pause(…)` are an error with a hint (“since 2.26 — a subheading `### Name` in `## Includes`”).

Includes of the pilots. “Agent step” has one library, “Meeting” two (the hash of the second is an example below; the hash of `Pause` is the value of version 0.27, the line `- alula_version: 0.27` is part of the hash, so it changes with every version of the format):

```
## Includes

### Pause
- File: libs/pause.alula.md
- Hash: 429adaba4cec

| parameter | value |
|---|---|
| halt_signal | "halt" |
| nested | [] |
| request_cancel | "stop_transport_turn" |
| reentry | "nothing" |
// write right: files that the agent edits; the pause does not touch their rights
```

```
## Includes

### Pause
- File: libs/pause.alula.md
- Hash: 429adaba4cec

| parameter | value |
|---|---|
| halt_signal | "halt meeting" |
| nested | ["agent_step"] |
| request_cancel | "without_return_to_send" |
| reentry | "requests_from_to_send" |

### cycle_arithmetic
- File: libs/cycle_arithmetic.alula.md
- Hash: 95c29f6d64ac
```

An example of a library of functions (“Meeting”: the arithmetic of a cycle is common to the meeting and the cycle check). The hash is the SHA-256 of the given file (12 signs): of the text of the block from the header line `# Library: cycle_arithmetic` to the closing fence after the normalization (above); it differs from the hash of the Russian sample because this file is in the English form and contains the line `- language: en`. The hash is the value of version 0.27.

````
# Library: cycle_arithmetic

- library: cycle_arithmetic
- alula_version: 0.27
- language: en

## Functions

```
fn ceiling_reached(pass_number int>=1, origin int>=1, limit int>=0) -> bool =>
  (pass_number - 1) - origin + 1 >= limit
```
````

**Closed sets of words of the parameters of “Pause”.** A value outside the set named by the type of the parameter is a check error. The effect is named formally and applied where indicated. “COMMON N” and “PAUSE N” are the N-th row of the table of common events and of the table of the state PAUSE in order (in order).

| Parameter | Word | Effect | Where it acts |
|---|---|---|---|
| `request_cancel` | `"mechanics"` | cancelling the open requests without an accepted response — only contract mechanics (requests to a human are closed); the parties of the cancelled requests of a set are returned to `to_send` (rule 18) | `cancel_open`: COMMON 1, 2 — except `nested`; COMMON 5 — all open ones, including the nested ones (the signal “cancel” went to them a row earlier), as the engine code and the library text |
| `request_cancel` | `"without_return_to_send"` | as `"mechanics"`, but the parties of the cancelled requests of a set are not returned to `to_send` (the library text: “by the pause”); in “Meeting” the Lenses requests are nested, COMMON 1, 2 do not cancel them, there is nothing to return | only COMMON 1, 2 (the pause); in COMMON 5 the word does not act: the parties of the set are returned to `to_send` by rule 18, like `cancel_open_without_accepted(false)` of the engine |
| `request_cancel` | `"stop_transport_turn"` | as `"mechanics"`; besides that, the turn at the agent transport is stopped; closing the held turn is not an effect of the parameter: it is done by `close_agent_turn()` in the ends of the machine | `cancel_open`: COMMON 1, 2, 5, as for `"mechanics"` |
| `reentry` | `"nothing"` | re-entry into the saved state — only by rule 12 (a new request if there is no accepted one for it) | `To: previous` (PAUSE 1, 3) |
| `reentry` | `"requests_from_to_send"` | after re-entry into the appeal of a set, the requests go to the parties listed in `to_send` | the same |

The definition of the “Pause” library in the format. Composed from the expansion in the “Meeting” pilot and the text of [archive/state-machine-pause-states.md](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/archive/state-machine-pause-states.md); the file itself in the format was not checked by a pilot, its comparison with the text of rules 23, 24, 35 is by rows. There is no library file in Alula (`*.alula.md` with the header `# Library: Pause`): the definition below is a sample, the include is not resolved by the methodology scripts (see the [changelog](alula-changelog.en.md), “Open items”). Features of the definition: `halt_signal` is a parameter, read by name; the events from a parent are `signal(…)`; the reasons of the stop are its own enumeration `PauseReason` and its own datum `reason` (the library does not write into the data of the machine, the machine reads `Pause.reason`); `pass(nested, …)`; COMMON 6 is `machine_error`; in the “Request” of PAUSE `require(previous)` (the field is visible only to the party, the rows of PAUSE read the datum `previous`, 4.2); COMMON 5 is `cancel_open` without an exception, as the code and the library text; returning the parties of a set to `to_send` in COMMON 5 is rule 18, for any value of `request_cancel`; `call_request_id` and `open_requests` are engine data of the library `contract` (7a), `human_words` is not entered into the table (section 2).

````
# Library: Pause

- library: pause
- alula_version: 0.27
- language: en

## Parameters

| name | type | comment |
|---|---|---|
| halt_signal | str | the party signal of the party "enhanced" by which the machine stops |
| nested | []str | the names of the machines to which the signals of the chain go (rule 35, item 8) |
| request_cancel | "mechanics" \| "without_return_to_send" \| "stop_transport_turn" | the effects: the table of section 9 of the specification |
| reentry | "nothing" \| "requests_from_to_send" | the effects: the table of section 9 of the specification |

## Requires parties

| name | kind | signals |
|---|---|---|
| enhanced | enhanced | continue { human_word str, author str, source str }, halt_signal |

## Requires ends

| name |
|---|
| Halted |
| Errored |

## Types

```
type PauseReason enum
  | Halted = "pause_halt"
  | Cancelled = "cancel_request"
```

## Data

| name | type | initial |
|---|---|---|
| previous | ?State | none |
| reason | ?PauseReason | none |

## Common events     // parsed before the rows of the states (rule 23)

| Event | Condition | Actions | To |
|---|---|---|---|
| signal(human_stop { human_word, author, source }) | not end(state) and state != Pause | journal("human_stop", author: author, source: source, event: event.id)<br>previous = state<br>pass(nested, stop)<br>cancel_open(except: nested) | Pause |
| signal(parent_stop { id }) | not end(state) and state != Pause and id == call_request_id | journal("pause_by_parent_stop", request: id, event: event.id)<br>previous = state<br>pass(nested, stop)<br>cancel_open(except: nested) | Pause |
| signal(cancel_request { id }) | id != call_request_id | journal("cancel_discarded_foreign_request", request: id, event: event.id) | same |
| signal(cancel_request { id }) | id == call_request_id and end(state) | journal("cancel_discarded_already_replied", request: id, event: event.id) | same |
| signal(cancel_request { id }) | id == call_request_id and not end(state) | journal("request_cancelled", request: id, event: event.id)<br>reason = PauseReason.Cancelled<br>pass(nested, cancel)<br>cancel_open | Halted |
| signal(cancel_request { id }) | else | machine_error("cancel_parse_no_match") |  |

## States

### Pause — appeal
- Party: enhanced
- Request:

| request_field | expression |
|---|---|
| previous | require(previous) |
| call_request_id |  |

| Event | Condition | Actions | To |
|---|---|---|---|
| signal(continue { author, source }) |  | journal("human_continue", previous: text(require(previous)), author: author, source: source, event: event.id)<br>pass(nested, continue) | previous |
| signal(halt_signal) |  | reason = PauseReason.Halted<br>pass(nested, halt) | Halted |
| signal(parent_continue { id }) | id == call_request_id | journal("parent_continue", previous: text(require(previous)), request: id, event: event.id)<br>pass(nested, continue) | previous |
| signal(parent_halt { id }) | id == call_request_id | reason = PauseReason.Halted<br>pass(nested, halt) | Halted |
````

- The signals “continue” and “halt” (and those from a parent) outside Pause are superfluous signals: the engine drops them with a journal entry (rule 17).
- `To: previous` leads by re-entry into the saved state (rule 12; the parameter `reentry`); `previous` is not written in this (rules 13, 24).
- JSON names of the library (1a): the datum `previous` and the engine data (`call_request_id`, `open_requests`) are readable names of the word table; the JSON names of the machine signals are named by glossary version 11 (section 2.16): `стоп человека` → `human_stop`, `стоп от родителя` → `parent_stop`, `отмена_запроса` → `cancel_request`, `продолжить от родителя` → `parent_continue`, `остановить от родителя` → `parent_halt` (the English example above uses them); the signal fields — `слово_человека` → `human_word`, `автор` → `author`, `источник` → `source`, `идентификатор_запроса` → `id` (sections 2.9, 2.12 of the glossary); they and the parameters of the library are built by the rule of 1a by the library file, overrides — by its section `## Names`; machine signals are a separate namespace (1a), the library states enter the state namespace of the machine (with the instance prefix, as in the machine).
- The bindings of the library rows (`human_word`, `author`, `source`, `id`) are internal names (1a): their Russian names are set by the Russian library file, they are not in the word table. A machine datum with such a name is a check error (4.3).
- The words of a human (`human_words`) are a store of rule 31, written by the contract mechanics (rule 19); it is not entered into the “Data” table (section 2) and is not included in `all_data`; it is not in the rows. `open_requests` is engine data of the library `contract` (7a): it is read by `pass` and `cancel_open`; neither the machine nor the library repeats the row (section 2).

## 10. Table checks

The word table and the language: the `ru` and `en` words of the table [alula-keywords.tsv](alula-keywords.tsv) are unique within a kind; the `language` line ∈ {`ru`, `en`}; the header language matches the declared one; a keyword not of the file language is an error with the line number of the first foreign word (1a); the script [tools/check-alula-keywords.py](../tools/check-alula-keywords.py) checks the table (the kinds of words, including `operator`), compares the sample machines with it and checks in them the operator signs (ASCII only), the JSON names (the automatic name; the section `## Names` — a redundant row, a name not declared, a repeat, a non-Latin JSON name; a collision in a namespace; a mixed word; parentheses after a name) and the glossary hash; [tools/check-alula-samples.py](../tools/check-alula-samples.py) compares the JSON names of the declarations of the two “Agent step” samples.

The extension of [check-tables.py](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/check-tables.py): names of fields, types and states; a name read by a row exists and is allowed (in the “Request” — the names named by its table); the reads of a state are derived (from the expressions of the rows, the “Request”, the “On accept”, the “On entry” and the `reads` lists of external functions, for ERROR — `all_data`) and shown in the report, they need not be declared; a write only into declared data (including the `writes` of acting functions), a write from a table into engine data (the party attempt counters, `open_requests`, `call_request_id`) is an error; a line `Reads:` is an error with the hint (“since 2.26 the reads are derived”); the bounds `int>=n`, `non_decreasing` and `<=`; reachability of states; completeness of forks: the `else` row is not required, an uncovered fork leads to ERROR with `fork_no_match` (4.1); after a proven exhaustion (an enumeration without fields at its forms, a literal set — all values named) a written `else` is a warning; exhaustion of the “Output” taking `Except` into account; the values of `To`; appeal events ⊆ machine events; party signals: the signal of an event of an appeal row ∈ the list of signals of the appeal's party, every signal of a party is used (a signal with no row in the current state is not accepted by a row and is discarded, rules 14, 17, 19); `failure(reason in …)` ⊆ `FailCode` from the library `contract`; the class of an external function (by its declaration) is allowed in the call position; literal sets (the inclusion of the computed set, a value outside the set is an error, `match` over a set is exhausted, 3.2); a literal of the type `id` is of UUID format; `new_id()` only in `let` of the “On entry” of an operation, and the binding is written by the row of the operation (section 7); an event field binding does not coincide with data (together with the data of libraries, after substitution); for an appeal without a `Request` line the rows, “On accept” and “Idle term” read no data; a full map; the types `T`/`?T`; the journal: code ↔ the methodology template table or the product table, a product code does not repeat a methodology code (section 5), parameter names ↔ template (`fork`), the values are `str`; enumeration values are `[a-z][a-z0-9_]*`; JSON names (1a): the final JSON name (a `## Names` row, otherwise the automatic one — glossary, transliteration) is Latin; a `## Names` row that changes nothing is the error “redundant row”; a row for a name that is not among the declarations of the file (internal, readable, a typo) is an error; a name repeated in `## Names`; a non-Latin JSON name of a row; parentheses after a name in a declaration are an error (parentheses are removed); the JSON names of one namespace are distinct (the namespaces — 1a: states together with library states; data; input fields; types; the fields of one record or form; the forms of one enumeration with fields; the elements of one enumeration; the signals of one party; the fields of one signal; machine signals; external functions; parameters, constants and setting names), different namespaces do not interfere, journal codes are in no namespace; a word of a name that mixes Cyrillic and Latin is an error; the hash of the normative part of the glossary equals the hash the format names (`glossary hash`, 1a), otherwise the error “the glossary changed without a format change”; the reference script [tools/check-alula-keywords.py](../tools/check-alula-keywords.py) checks the namespaces it sees in the declarations (states together with the state of the “Pause” library, data together with the JSON names of the contract and library data — `previous`, `call_request_id`, `open_requests`, `reason`, `to_send`, `human_words`, — input fields, types, fields, forms, elements, signals and their fields, external functions, setting names), and does not check constants and parameters (namespace 10) and the machine signals of the library — that is a check of the product's translator; the reasons of the library `Pause` are covered by the rows of `## Output`; no engine and envelope data in the reads of conditions (rule 31); `Initial state` is named; party identifiers are Latin and distinct; the JSON names of states are Latin and distinct; `Idle term` reads only the names of `Request`; an empty cell “expression” of `Request` — the field name is readable by the “Request” expressions (a datum, a constant, a parameter, a readable name), otherwise an error; an explicit expression equal to the field name is a warning (4.2); `parse` is a volatile external function with the single parameter of the type `result` and a result of the named type, `response: Form` — only for an enumeration; `Edits`: the function is a volatile external function without parameters, the result `bool`, the datum is written in the “On accept” of the state; a write by the path `name[*].field` is compared with the mark `non_decreasing` by the template `[*]`, a write from a row into a party counter field is an error; “Parties”: the column `counter` is named for every party except a party of the kind `human` with free input (`—`; `—` at a party of another kind is an error), the datum is made by the loader (`int>=0`, `non_decreasing: yes`), a row for it in `## Data` is an error (the name is declared twice); an appeal to a party without a counter has no `Request`, `set`, `Idle term`, `Edits`, `Form returns` and no events `response`, `failure` — the constructs of gates and requests; `result` is named for every party, the form of the event `response` belongs to the `result` type of the party (the result of `parse`), the signal of the event `signal` of a party belongs to its column “signals”; `open_requests` is declared once; a `failure` outside the state's list is brought to `NoResult` (4.3); `require_non_empty`: the argument is a set with `""`; the codes of the journal of the table format are in the template table (the subsection “Events of the table format” of the journal file).

- **Formatting**: a state key line (4.1) without the marker `- ` is an error; a warning — a table standing right next to a list item or to another table (without an empty line) also warns. Prose: a line that begins with a word from the list of keys (4.1) and a colon without the marker `- ` or with a typo in it (`-Party:`, `– Edits:`) is an error, otherwise the typo would remain a silent comment. The other prose causes no checks. A paragraph: a text line pressed against a table, a heading or a list without an empty line is a warning. A declaration (`type`, `fn`) outside a code block is a warning. The file extension is checked only by this script.
- **The call namespace** (1a, namespace 11): a name of a function or an external function (as written, the English name by 1a, for an external function the JSON name) that coincides with a word of a catalog function in either language or with `range` is an error; the name `новый_ид`/`new_id` (the standard external function, also a word of the kind `catalog`) is not compared with the catalog words; an author function named as an external function is an error.
- **Parties `machine`**: the name of the called machine is in the host registry (call protocol); the fields of the `Request` of an appeal to the party are exactly the `## Input` fields of the called machine (names, types of expressions by section 2); the result is read with the type `- Result:` of the called machine, the first parameter of the function `parse` is the type of this result; the form `machine name(input Type, result Type)` is an error with a hint (“since 0.27 the types are taken from the called machine”).
- **The record of 0.27**: `machine_version: alula-…` and any non-integer `revision` is an error (“a revision is an integer”); `machine_version` and `format` in the header is an error with a hint (“since 0.27 — `revision` and `alula_version`”); `format: "machine/2"` and `version` in the JSON of a tree is an error with a hint (“since 0.27 — `kind` and `revision`”); the single `## Requires` of a library is an error with a hint (“since 0.27 three sections: `## Requires data`, `## Requires parties`, `## Requires ends`”); `machine name(input Type, result Type)` is an error (“since 0.27 the types are taken from the called machine”).
- **The record of 2.26**: the line `Reads:` and the column `reads` in `Request` are an error with a hint (“since 2.26 the reads are derived”); the column `writes` in `## Data` is an error (“since 2.26 there is no column `writes`”); the column `№` in transition rows and `## Ends` are an error (“since 2.26 `## Output`, rows without `№`”); `—` as an empty cell of a condition, of actions and of `Request` is an error (“since 2.26 an empty cell”); an include line `functions: …` and `Pause(…)` are an error (“since 2.26 a subheading `### Name`”); the section `## Obligates` is an error (“since 2.26 `## Requires`”, since 0.27 — three sections `## Requires …`); `external fn` before a declaration in `## External functions` is an error (“since 2.26 there are no words `external fn`”); the word “fragment” in a header is an error (“since 2.26 a library”).
- **Clarifications after 2.22**: the language names one standard external function (two before 2.25) and 35 journal codes, the rest is the data of a host (subsection 7a); a record or form field named as a catalog list function is a warning, not an error; the name of a function or an external function `новый_ид`/`new_id` is not compared with the catalog words; a tree with another `alula_version` is a loading error; the `result` of a party `agent` is a type from `## Types` or a built-in type; the prose calls a party signal a signal, not a word.
- **Includes and libraries**: in `## Includes` — only subheadings `### Name` with key lines and tables of values (prose outside a subheading, a list are a check error); the file is found (next to the machine file, then in the folder of `--lib` or of the project setting), its hash matches the `Hash` of the include (the normalization is in section 9), instance names do not repeat; `## Requires data`, `## Requires parties`, `## Requires ends` of the library: every name is in the machine, a datum has the same type, a party has the same kind and the named signals are among its signals, an end is among the ends (section 9); there are no external functions (`## External functions`, their calls) and no `## Includes` in the library; all the parameters of the include are named, there are no extra ones, a value fits the type of the parameter, and a value outside the closed set of words named by the type is an error; the old include syntax (a line `functions: <name> version <N> hash <hex12>`, a record `Pause(…)`) is an error with a hint (“since 2.26 — a subheading `### Name` in `## Includes`”); a state of a library declared by a heading in the section `## States` of a machine is a “declared twice” error.

**Release for the interpreter**. `unreachable` and `require(none)` are a program defect: the process is stopped by the engine (not the table); the machine state is not rolled back; the call response is an end with `NoResult`; the journal of the defect is at the engine's discretion. This is not a machine error (3.3): a defect does not lead to ERROR. A call refusal on a wrong input is a separate case: the event `input_rejected` (section 1).

## 11. Tests

A test is events and an expectation: an event (`start` with input, `response`, `failure`, `signal` of a party or of the machine with data, a term) → the state, the structured journal (code and parameters, rule 31), a subset of data, the queue. The comparison is by these four; the runner is in the product; the same test is run on the methodology automaton. The form of a test record is in general not set here (the runner format is in the product); the format fixes three things. **The file name**: a test is called `<name>.alula.test.json`; the root of the test file carries the key `"kind": "test"` (there is no schema number after a slash: the schema is bound to `alula_version`). **Event data**: a signal (of a party or of the machine) with one data field carries the value of that field — text (for example, `continue` with the field `author` — the value `"ivan"`, not an object); with several fields — an object `{field: value}`; without fields — only the name. **Parameters**: a test may carry `params` — a “key → value” table with the keys `project.<key>` (section 1, “passing values from outside”); a parameter not named keeps its default value.

## 12. Catalog of built-in functions

The names of the catalog functions are quoted here in the English form (`has`, `require`, `require_non_empty`, `record_text`, `without_key`, `first_where`, `fold`, `new_id`, etc.); the Russian names are in the [word table](alula-keywords.tsv), the kind `catalog` (1a).

All catalog functions are of the class `pure`: they are called wherever an expression is allowed; the exception is the standard external function `new_id` (the last row). The list functions (`filter` … `fold`) are called as a method of their first argument — a list: `xs.filter(x => expr)` (3.1); in a signature the first parameter `xs []T` is the method receiver (every parameter of a signature has a name); a call of a list function as an ordinary call is an error. A lambda parameter is written in a signature by the function type `name fn(T) -> R` (Russian `имя функция(T) -> R`, as D20 of Nova): this is a record of documentation — the language has no function type, a lambda stands only as an argument of a list function (3.1). A range is the operators `a..b` and `a..=b`, there is no function `range` in a file. The other external functions are declared in the machine file (section 7), they are not in the catalog.

| Name | Signature | Class | Meaning |
|---|---|---|---|
| `has` | `(x ?T) -> bool` | pure | true if `x` is not `none` |
| `require` | `(x ?T) -> T` | pure | the value; with `none` — `unreachable` (3.3) |
| `require_non_empty` | `(x "" \| … ) -> the set of x without ""` | pure | a value different from `""`; on `""` — `unreachable`; the result set is the set of `x` without `""` (3.2) |
| `text` | `(x A) -> str` | pure | `A` is int, f64, str, a literal set, `id`, an enumeration, `State` or `?A`; the format is in 3.3 |
| `record_text` | `(e JournalEvent) -> str` | pure | `событие <код>` (the Russian word “event” and the code) if there are no parameters, otherwise `событие <код>: имя=значение, …` (through commas, in the order of writing) — the same display of the code without a template as in the [journal](https://github.com/unitcraft/ai-dev-methodology/blob/main/state-machines/state-machine-journal.md), section 3 |
| `float` | `(x int) -> f64` | pure | |
| `int` | `(x f64) -> int` | pure | the fractional part is dropped toward zero; out of range — a machine error |
| `length` | `(x []T \| map[K, V]) -> int>=0` | pure | only a list and a map; on a string — a type check error |
| `a..b` | `(a int, b int) -> []int` | pure | an operator: `[a, b)` — half-open, empty when `b <= a`; in the tree — a call `range` |
| `a..=b` | `(a int, b int) -> []int` | pure | an operator: from `a` to `b` inclusive — `a..(b + 1)`, empty when `b < a`; in the tree — a call `range(a, b + 1)` |
| `concat` | `(a str, b str, …) -> str` | pure | two or more arguments of the type `str` (an int and the rest — through `text(x)`); concatenation in order; a literal with insertions unfolds into it (3.1); `+` of text stays |
| `max`, `min` | `(a T, b T) -> T`, `T` is int or f64 | pure | |
| `keys`, `values` | `(m map[K, V]) -> []K`, `-> []V` | pure | the order is the order of writing the keys (section 2) |
| `without_key` | `(m map[K, V], k K) -> map[K, V]` | pure | no key — the same map |
| `remove` | `(xs []T, x T) -> []T` | pure | removes all elements equal to the second argument |
| `journal_event` | `(code literal, name: str, …) -> JournalEvent` | pure | an event value for `journal(value)`; `code` is a string literal, the pairs `name: value` are the event parameters (named arguments are allowed only here, in `journal` and in `machine_error`, 3.1) |
| `end` | `(s State) -> bool` | pure | true for states of the kind “end”; needed by libraries |
| `filter` | `(xs []T, f fn(T) -> bool) -> []T` | pure | a list function, the method `xs.filter(…)` |
| `map` | `(xs []T, f fn(T) -> U) -> []U` | pure | a list function |
| `any`, `all` | `(xs []T, f fn(T) -> bool) -> bool` | pure | list functions; on an empty list `false` and `true` |
| `count` | `(xs []T, f fn(T) -> bool) -> int>=0` | pure | a list function |
| `first_where` | `(xs []T, f fn(T) -> bool) -> ?T` | pure | a list function |
| `dict` | `(xs []T, k fn(T) -> K, v fn(T) -> V) -> map[K, V]` | pure | a list function: a map from a list; a repeated key is a machine error |
| `fold` | `(xs []T, init A, f fn(A, T) -> A) -> A` | pure | a list function; left to right |
| `time_to_text` | `(ms int) -> str` | pure | milliseconds since 1970-01-01 UTC into ISO 8601 text in UTC with the suffix `Z`: `"2026-10-25T14:20:00Z"`, with non-zero milliseconds `"2026-10-25T14:20:00.123Z"`; there are no time zones, so a step is reproducible; outside the range 0001-01-01…9999-12-31 — the machine error `overflow` |
| `text_to_time` | `(t str) -> ?int` | pure | the inverse: a text of the same form (seconds and the suffix `Z` are required; the fraction of a second is 1–3 digits) into milliseconds; empty for a text not of this form: without `Z` or with another zone, with the second 60, with a fraction longer than three digits, for the year 0000 |
| `new_id` | `() -> id` | volatile | **not a pure function**: a standard external function, non-deterministic; allowed only in `let` of the “On entry” of an operation, the value is fixed in the record of the step (section 7) |

Actions are section 5; their class: `journal`, `machine_error`, assignments are acting (a write into data and the journal in one commit with the step); `pass`, `cancel_open` are acting (after the commit); a call of an external function is by the class of the function.
