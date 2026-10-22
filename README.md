<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo/alula-wordmark-mono-dark-en.svg">
    <img alt="alula" src="assets/logo/alula-wordmark-mono-light-en.svg" height="80">
  </picture>
</p>

# alula

The core of the language of state machines written as data, on [Nova](https://github.com/nv-lang/nova): a machine is a table of states and
rows (a file in Russian or in English, or its JSON tree `machine/2`); one interpreter runs it, and a scenario (`scenario/0`) proves it. The package
was written inside the CrewHarness product (`unitcraft/crew-harness`, tasks 106-126) and extracted from it by task 144 of that repository; the
product now depends on this package.

## The name

The language is called **Alula** (the owner, 2026-10-21: "Alula - ОК"; the methodology keeps the history of the choice in its `doc/alula-history.md`). Two meanings: the
star Alula in the paw of the Great Bear, from the Arabic "first leap" (a leap is the move of a machine from a state to a state), and the English *alula*, the small group of
feathers on the first digit of a bird's wing (from the Latin *ala*, "wing") that helps the bird to steer at a low speed. Until the format 2.14 the language was called Portolan. <!-- guard-allow(legacy-name): the history of the name -->

The program is `alula`, the files of machines are `*.alula.md` (`.txt`) and `*.alula.json`, the key of the version of a tree is `alula_version`, the line of the version of
a machine is `machine_version: alula-2.14`, the table of the words is a copy of `alula-keywords.tsv` of the methodology. There is no transition period (the owner, 2026-10-20):
a file of the format 2.12 or older, a tree with the key of the former name and the former file names are refused with a message.

The format read here is **2.14**: since task 148 the package takes the name and the number of the format of the methodology 2.14 (a rename of the language, of the files and of
the keys). The notation itself is still that of 2.12: the simplifications of 2.13 of the methodology (a signal of a party instead of a gate word, `Запрос` and `Читает` instead
of `Вход`, ASCII signs of operators, "values" of an enum, no section of the expansion of a fragment) are not read yet, so the files of the package are not the samples of the
methodology 2.14 character for character (the table of the words and the hash of the Russian sample of the definitions differ for that reason).

The package has no dependencies except Nova's `std` (`std.io`, `std.os` and `std.fs` are used only in `src/alula_cli/` and `src/alula.nv`).
Built and tested with **Nova Oracle 0.1.0** and Clang, see [spikes/env/README.md](spikes/env/README.md).

## What is here

One folder under `src/` is one module `alula.<folder>` and one unit of tests (Oracle 0.1.0 does not take a module in a folder below that).

| Module | What it is |
|---|---|
| `alula.engine` | the state machine engine: `Machine[S]`, `Engine`, the effects `Journal`, `Store`, `Link`, the journal line and the snapshot, in-memory handlers ([README](src/engine/README.md)) |
| `alula.machine` | the core of the machines: the dynamic `Value`, the types, the tree of an expression, the pure evaluator, the registry of the primitives of the host, the table of the journal codes, and the data compiled in: `schema/`, `machines/` (15 machines as JSON, 10 of them also as tables), `scenarios/` (621 scenarios) ([README](src/machine/README.md)) |
| `alula.machine_table` | the model of a machine, the decoder of the tree `machine/2`, the type syntax, the checks of a table |
| `alula.machine_text` | the translator of tables (Russian and English, format 2.14) to the JSON and the reverse generator ([README](src/machine_text/README.md)) |
| `alula.machine_run` | the interpreter `AlulaMachine`, the state, the host of the primitives, nested machines (`machine` parties), the runner of scenarios |
| `alula.alula_cli`, program `alula` | the commands `compile`, `render`, `convert`, `check`, `summary`, `run`, `test`, `version` ([README](src/alula_cli/README.md)); `src/alula.nv` is the program |
| `alula.alula_scenarios`, `alula.alula_eq` | tests only: a folder of scenarios through the program; the circles of the program equal the library |
| `alula.machine_*` (the rest) | tests only: the proofs that run the machines of `src/machine/machines/` (the agent step, the cycle check, the session start, the task runner, the dialog, the nested pairs) through the translator and the interpreter |

## The samples

The machines that the tests run are the samples of the package, and they live where the compiler can embed them (`embed_str` reads a file relative to its module):
`src/machine/machines/` (tables `*.alula.md`/`.txt` and the compiled `*.alula.json`) and `src/machine/scenarios/` (`*.scenario.test.json`). The agent step
(`agent_step`), the caller and the callee (`caller`, `callee`), the pair `dialog_steps`, the chat (`chat`) and the dialog (`dialog`) are the smallest samples to start from;
`alula test src/machine` runs all 621 scenarios.

## Build and check

```powershell
. C:/work/nova/nova-oracle-0.1.0-windows-x86_64/setup-env.ps1     # the leading dot matters
cd C:/work/alula

nova test src --jobs 4 --timeout 600                 # all units (the heavy ones: machine_runner about 7 minutes, alula_scenarios about 3)
nova test src --jobs 4 --timeout 600 --strict-effects
powershell -File scripts/build-alula.ps1 -Test    # builds target/alula.exe and runs it on src/machine
sh scripts/guards/run-all.sh                         # the guards: the marks of the Oracle workarounds, the border of the package, the former name
```

Tests are `*_test.nv` beside the sources. The output of a unit must stay under 4 KB (item 20 of the notes), hence the short names of the tests.

## Use as a dependency

In `nova.toml` of the consumer:

```toml
[dependencies]
alula = { git = "<the repository of alula>", version = "0.1" }
```

and `import alula.machine.{...}`, `import alula.engine.{...}` and so on. The modules of the package are the ones in the table above; a consumer takes the library only (the tests of the
package are not compiled into the consumer). The repository is not published yet: until it is, the consumer may point the dependency at a local folder.

## The marks of the Oracle workarounds

Every place that goes round a defect or a limit of Oracle 0.1.0 carries `// ORACLE-WORKAROUND(N): ...`; the index is [spikes/env/workarounds.md](spikes/env/workarounds.md) (generated by
`python scripts/oracle-workarounds.py --index`, checked by `scripts/guards/check-oracle-workarounds.py`). The numbers of the items are those of the survey in the CrewHarness repository.

## Licence

`MIT OR Apache-2.0`: [LICENSE](LICENSE), [LICENSE-MIT](LICENSE-MIT), [LICENSE-APACHE](LICENSE-APACHE).
