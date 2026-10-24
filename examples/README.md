# examples: the examples of the language

The examples of the package `alula` (task 158): small machines that show one construct of the language each, with the scenarios that prove them. They are the corpus of regression of the translator and of the interpreter
(the tests embed them through the module `alula.examples`) and the first thing to read.

```powershell
. C:/work/nova/nova-oracle-0.1.0-windows-x86_64/setup-env.ps1
nova build src/alula.nv -o target/alula.exe
target/alula.exe test examples        # 66 of 66 scenarios passed
```

`registry.md` and `journal.md` are the host "examples": the program takes them from the folder of the machines (spec 7a, AL-113; the form is in [src/machine/README.md](../src/machine/README.md)). The language itself holds
two primitives (`time_now`, `new_id`) and 35 journal codes; the host of the examples adds the primitive `close_agent_turn` and 44 codes of the machines below (24 of the former examples and 20 of the new tables).

| Machine | File | What it shows | Scenarios (`scenarios/`) |
|---|---|---|---|
| `Calc` | `calc.alula.json` | operations, forks, every kind of action, a definition, a parameter of the project | `calc-*` 4 |
| `Gate` | `gate.alula.json` | an agent turn, the fragment "Pause", a stop and a halt of a human | `gate-*` 5 |
| `Lenses` | `lenses.alula.json` | a set of parties | `lenses-*` 3 |
| `Variants` | `variants.alula.json` | answers by the forms of an enumeration, a retry, a term | `variants-*` 5 |
| `actions` | `actions.alula.json` | the actions of the rows, the primitive `close_agent_turn` of the class `irreversible` | the tests of `machine_run` |
| `caller`, `callee` | `caller.alula.md`, `callee.alula.md` | a nested machine called by a parent: the protocol of the call, restarts, a stop, a cancel | `nested-call-*` 17 |
| `fan` | `fan.alula.md` | a set of nested calls with a limit | `nested-set-*` 9 |
| `Echo` | `echo.alula.md` | a party of a free input (no gate, no request), the destination `same` | `echo-*` 3 |
| `Retry` | `retry.alula.md` | `same, rerun` of an agent and of a gate against `same` | `retry-*` 4 |
| `Verdict` | `verdict.alula.md` | an enumeration with fields: the forms `Accepted { score }`, `Rejected { reason }`, `Unsure` | `verdict-*` 3 |
| `Router` | `router.alula.md` | the exhaustion of a fork by the type and the row `else` with `fork_no_match` | `router-*` 4 |
| `Pausable` | `pausable.alula.md` | the fragment "Pause": stop, continue, halt | `pause-*` 3 |
| `Keeper` | `keeper.alula.md` | a gate (`human or agent by setting`) with two words | `keeper-*` 3 |
| `Batch` | `batch.alula.md` | a set of nested calls to the machine `callee`, the limit 2 | `batch-*` 3 |

The new tables (`Echo` ... `Batch`) are written in English; the scenarios are `scenario/0`. Run one: `target/alula.exe run examples/echo.alula.json examples/scenarios/echo-words.scenario.test.json`.
The machines of the product CrewHarness and of the methodology are not here: they are the data of their owners (the CrewHarness repository, `machines/`).
