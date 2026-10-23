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

The language is called **Alula** (the owner, 2026-10-21: "Alula - ОК"; the history of the choice is in [docs/history.md](docs/history.md)). Two meanings: the
star Alula in the paw of the Great Bear, from the Arabic "first leap" (a leap is the move of a machine from a state to a state), and the English *alula*, the small group of
feathers on the first digit of a bird's wing (from the Latin *ala*, "wing") that helps the bird to steer at a low speed. Until the format 2.14 the language was called Portolan. <!-- guard-allow(legacy-name): the history of the name -->

The program is `alula`, the files of machines are `*.alula.md` (`.txt`) and `*.alula.json`, the key of the version of a tree is `alula_version`, the line of the version of
a machine is `machine_version: alula-2.22`, the table of the words is a copy of [spec/alula-keywords.tsv](spec/alula-keywords.tsv). There is no transition period (the owner, 2026-10-20):
a file of the format 2.14 or older, a tree with the key of the former name and the former file names are refused with a message.

The format read here is **2.22** (the last of the line 2.18 - 2.22; the text of the specification is [spec/alula-spec.md](spec/alula-spec.md): the text of 2.22 after the clarifications AL-103 ... AL-112, which were written from this package; since version 0.3.2 the file lives here, it came from the methodology at the commit `0d95919`). Since task 148 the package has the name and the number of the format of the methodology; since task 149 it read the notation of 2.14 by the rules of 2.13 (AL-38 ... AL-49); since task 151 it reads and writes the formats 2.15 - 2.17 of the methodology (AL-51 ... AL-64): the JSON name of a name that leaves the machine is built by itself (the row of the section `## Имена`, the Latin name, the dictionary of the methodology of the version 11 pinned by the hash `60383c370415` of its normative part, the transliteration) and the brackets after a name are an error; ten spaces of the distinctness of the JSON names; a party of the kind `human` with `—` in the column `счётчик` is a party of a free input (no key `counter` in the tree); `—` in the table `Запрос` is "the same name"; the row `иначе` of a fork is needed only where the type does not prove the exhaustion. The table of the words is the table of the methodology of 2.17 as it is (219 rows), the samples of the methodology 2.17 (the agent step in both languages, the machine "Meeting") are the data of the tests and give the numbers and the JSON names of the methodology. Since task 152 (version 0.3.0) it reads and writes the syntax of the formats 2.18 - 2.22 (AL-65 ... AL-102): blocks `{ … }` in the actions and in the expressions, `=>` in the body of a function, a branch of `выбор` and a lambda, the word `функция` (`fn`), the types `строка`/`str`, `вещественное`/`f64`, `булево`, the ranges `a..b` and `a..=b`, the macros as methods of a list, the insertions `"${x}"` (the new function of the catalog `concat`), `в […]`, the map `[k: v]` and `[]` by the expected type, the patterns of the events in braces, the bare names of the elements, `тип Имя перечисление …`, the comments `//`, the numbers `1_000` and `1e-7`, the closed list of escapes, and a new lossless lexer. The table of the words is that of 2.22 (218 rows). The tree `machine/2` and the hash of the dictionary are the same as in 2.17; the former forms are errors that name the new way. The 15 machines, the samples of the methodology and the 626 scenarios (621 and the 5 of the program) went through without a change of the trees or of the expectations. The details are in [src/machine_text/README.md](src/machine_text/README.md) and [src/machine/README.md](src/machine/README.md).
Open questions to the methodology (a field with two JSON names named without its owner, the JSON name of a nested machine, the `title` of a tree) are in the logs of the tasks 149, 151, 152 and 154 of the CrewHarness repository. Task 154 aligned the package with the clarified text of the specification (AL-104 ... AL-111): the label of a form with fields is "формы", the bare names of the elements, the places of the empty `[]`, `новый_ид`, `то же, запуск заново`.

The package has no dependencies except Nova's `std` (`std.io`, `std.os` and `std.fs` are used only in `src/alula_cli/` and `src/alula.nv`).
Built and tested with **Nova Oracle 0.1.0** and Clang, see [spikes/env/README.md](spikes/env/README.md).

## What is here

One folder under `src/` is one module `alula.<folder>` and one unit of tests (Oracle 0.1.0 does not take a module in a folder below that).

| Module | What it is |
|---|---|
| `alula.engine` | the state machine engine: `Machine[S]`, `Engine`, the effects `Journal`, `Store`, `Link`, the journal line and the snapshot, in-memory handlers ([README](src/engine/README.md)) |
| `alula.machine` | the core of the machines: the dynamic `Value`, the types, the tree of an expression, the pure evaluator, the registry of the primitives of the host, the table of the journal codes, and the data compiled in: `schema/`, `machines/` (15 machines as JSON, 10 of them also as tables), `scenarios/` (621 scenarios) ([README](src/machine/README.md)) |
| `alula.machine_table` | the model of a machine, the decoder of the tree `machine/2`, the type syntax, the checks of a table |
| `alula.machine_text` | the translator of tables (Russian and English, format 2.22) to the JSON and the reverse generator ([README](src/machine_text/README.md)) |
| `alula.machine_run` | the interpreter `AlulaMachine`, the state, the host of the primitives, nested machines (`machine` parties), the runner of scenarios |
| `alula.alula_cli`, program `alula` | the commands `compile`, `render`, `convert`, `check`, `summary`, `run`, `test`, `version` ([README](src/alula_cli/README.md)); `src/alula.nv` is the program |
| `alula.alula_scenarios`, `alula.alula_eq` | tests only: a folder of scenarios through the program; the circles of the program equal the library |
| `alula.machine_*` (the rest) | tests only: the proofs that run the machines of `src/machine/machines/` (the agent step, the cycle check, the session start, the task runner, the dialog, the nested pairs) through the translator and the interpreter |

## The map of the folders

| Folder | What it is |
|---|---|
| `spec/` | the source of the language: [alula-spec.md](spec/alula-spec.md) (Russian, normative), [alula-spec.en.md](spec/alula-spec.en.md) (the English translation), [alula-keywords.tsv](spec/alula-keywords.tsv) (the table of the words of both file languages); `spec/samples/` - the samples of the notation: the agent step in Russian and in English, the machine "Meeting" with its notes |
| `tools/` | the checks of the language, plain Python: `check-alula-keywords.py` (the table of words and the samples against it; the dictionary of the methodology is read from `--glossary <path>` or `ALULA_GLOSSARY`, without it that part is skipped with a message), `check-alula-samples.py` (the two samples of the agent step against each other), `check-alula-translation.py` (the English text of the specification against the Russian) |
| `docs/` | for readers: [overview.md](docs/overview.md), [data-types.md](docs/data-types.md), [debugging.md](docs/debugging.md), [history.md](docs/history.md) (the history of the language and its name), `diagrams/` (five SVG) |
| `assets/` | `logo/`: the mark, the wordmarks, the social picture ([README](assets/logo/README.md)) |
| `src/` | the package: one folder is one module `alula.<folder>` and one unit of tests |
| `scripts/` | the build of the program, the guards (`scripts/guards/`), the generators of the files of the package |
| `spikes/` | the notes and the reproductions of the defects of Oracle 0.1.0 ([env](spikes/env/README.md)) |

The specification, the samples and the table of words were kept by the methodology (`unitcraft/ai-dev-methodology`) until version 0.3.1; since version 0.3.2 the
language is kept here, and the methodology keeps what is not the language: the journal, the glossary of the names, the specification of machines, the protocol of calls.
The copies that the tests embed (`src/machine_text/alula-keywords.tsv`, `src/machine_agent/cases/`) are checked against `spec/` by `scripts/guards/check-spec-copies.py`.

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
sh scripts/guards/run-all.sh                         # the guards: the marks of the Oracle workarounds, the border of the package, the former name, the copies of spec/
python tools/check-alula-keywords.py --glossary <path>/state-machine-glossary.md   # the table of words, the samples and the dictionary (the glossary stays in the methodology)
python tools/check-alula-samples.py --glossary <path>/state-machine-glossary.md    # the two samples of the agent step against each other
python tools/check-alula-translation.py             # the English text of the specification against the Russian
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
