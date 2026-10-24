# alula_cli: the program `alula`

Task 116 (`doc/tasks/116-*/`). One program for the machines that are data: it compiles a machine written in Alula (a Markdown file of tables, in Russian or in English) to the JSON `machine/2`,
turns the JSON back into Alula, converts a file from one language to the other, checks a file, and runs the scenarios of a machine. The user writes no Nova. It replaces the former command `machine-translate`
(`src/machine_translate.nv`; there is no transitional name).

The entry point is `src/alula.nv` (it only ends the process with the exit code). The commands are in this folder, as a module that the tests run without a process: `cli.nv` (the program over its effects `Os Fs Io`),
`commands.nv` (a command is a function from the text of its file to a `CmdResult`: standard output, standard error, exit code), `options.nv` (the arguments), `help.nv` (the texts). The translator is `src/machine_text/`
(`translate_checked`, `render_machine`, `render_summary`), the interpreter and the runner of scenarios are `src/machine_run/`, the checks of the table are `src/machine_table/`. The folder is not called `alula`
because the file `src/alula.nv` and a folder `src/alula/` make one module name twice (the compiler refuses it).

## Build

```powershell
. C:/work/nova/nova-oracle-0.1.0-windows-x86_64/setup-env.ps1      # the leading dot matters; Nova Oracle 0.1.0 and Clang, spikes/env/README.md
cd C:/work/alula
powershell -File scripts/build-alula.ps1                          # builds target/alula.exe and prints its path
powershell -File scripts/build-alula.ps1 -Test                    # builds, then `alula test examples`
```

The same by hand: `nova build src/alula.nv -o target/alula.exe` (a fresh tree needs `nova update` once). The script installs nothing and does not touch `PATH`; the program is the one file `target/alula.exe`, and it can
be copied where the user wants it. The first build takes about a minute.

## Commands

```
alula compile <file.alula.md> [-o <file.alula.json>] [--lenient] [--no-check] [--force] [--registry <file>] [--journal <file>]
alula render  <file.alula.json> [--language ru|en] [-o <file.alula.md>] [--lenient] [--force] [--registry <file>] [--journal <file>]
alula convert <file.alula.md> --language ru|en [-o <file.alula.md>] [--no-check] [--lenient] [--force] [--registry <file>] [--journal <file>]
alula check   <file.alula.md | file.alula.json> [--no-check] [--registry <file>] [--journal <file>]
alula summary <file.alula.md | file.alula.json> [--no-check] [--registry <file>] [--journal <file>]
alula run     <machine.alula.json | machine.alula.md> <scenario.scenario.test.json> [--registry <file>] [--journal <file>]
alula test    <folder> [-v] [--registry <file>] [--journal <file>]
alula version
alula --help | alula <command> --help | alula help [<command>]
```

| Command | What it does |
|---|---|
| `compile` | Alula -> the JSON `machine/2`, on the standard output (or into the file of `-o`). The language of the file is read from its header (`- language: en`; none is Russian). The translator and the checks of the table against the primitives of the host (`--no-check` leaves the checks out). With errors there is no JSON; `--lenient` prints the JSON of what could be translated all the same (the code is still 1). |
| `render` | the JSON `machine/2` -> a file of Alula in the canonical form of the specification (section 1b), Russian by default. What the file cannot say is a note on the standard error and the code 1 (`--lenient` prints the text all the same). |
| `convert` | a file of Alula in the other language: `compile`, then `render`. The meaning is kept (the tree of the machine is the same); the comments (paragraphs of free text, lines starting with `>` or `//`) do not go through the JSON, and the program says so on the standard error (`alula: note: ...`). |
| `check` | the translation and the checks of the table of a file of Alula, or the decoding and the checks of a JSON. Prints `ok` (`ok (2 warnings)`) and the code 0 when there are no errors; the errors and the warnings (P-1) go to the standard error. |
| `summary` | the summary of a machine: the states with their kinds, the rows, the actions, the data, the parties. |
| `run` | one scenario (`scenario/0`) on a machine (a machine that calls nested machines is refused with the code 1 and the hint to use `alula test <folder>`, because the nested machines are found in a folder; a scenario with the key `"standalone": true` plays the nested parties itself and is run, task 122): `ok`, or the report of the differences (the step, the part, what was expected and what came) and the code 1. The machine can be a JSON or a file of Alula. The scenario names its machine; another name is an error. |
| `test` | every `*.scenario.test.json` of the folder (and of the folders under it) on the machine that the scenario names; prints a report of each scenario that differs and `N of M scenarios passed`. The machines are the `*.alula.json` files of the folder; a machine that has no JSON file is read from `*.alula.md` (`*.alula.txt`) when a scenario asks for it. `-v` also prints `ok <file>` for every scenario that passed. The code is 1 when one differs. A machine with a party of the kind `machine` (task 119) is run together with the machines it calls: they are found in the same folder by the name in the cell `вид` (a JSON file, else a file of Alula), the pair is checked first (`the nested machines do not fit: ...`, a machine that is not in the folder is `the machine X of the party Y is not in the registry`), and the steps `on` / `also` of its scenarios act on and compare the nested machines. A scenario with `"standalone": true` (task 122) is not run so: the steps play the nested parties and no nested machine is looked for in the folder. |
| `version` | `alula 0.4.0 (Alula 2.22, machine/2)`. Since task 152 the program reads the version 2.22 only (and writes it; the syntax of 2.18 - 2.22 is described in `src/machine_text/README.md`): a file of 2.12 or of an older version is refused by `compile`, `convert` and `check` with "версия не известна ... читает формат 2.22", a JSON tree of another version or with the key of the former name by `render` (code 1); there is no transition period. |

`-o` (`--output`) writes the product into a file instead of the standard output; an existing file is not overwritten without `--force`, and nothing is written when the command has errors (except with `--lenient`). There is no
default name of the output file: a file is written only for an explicit `-o`. A file of Alula is read with CR LF or LF line ends. The extension of a file of Alula is not looked at (`compile`, `convert`); `check` and
`summary` take a name ending in `.json` for a JSON and any other name for a text of Alula.

## The host: the registry and the journal as data (0.4.0, spec 7a, AL-113)

The language names two primitives (`time_now`, `new_id`) and 35 journal codes (`src/machine/journal_language.md`). Everything else is the data of the host that owns the machine, two Markdown files (the form is in [src/machine/README.md](../machine/README.md), "The registry and the journal of the host are data"):

| File | What it holds |
|---|---|
| `registry.md` | the primitives of the host (`name \| parameters \| result \| class \| reads \| writes`), the roles of a parse primitive, the records and the variants that the signatures use |
| `journal.md` | the codes of the journal of the host (`Machine \| Code \| Russian template \| Parameters`) |

Every command that reads a machine (`compile`, `render`, `convert`, `check`, `summary`, `run`, `test`) takes the host from the folder of its file (for `test`, from the folder it is given): `registry.md` and `journal.md` beside the machine; the options `--registry <file>` and `--journal <file>` (also `--registry=<file>`) name the files and win over the ones beside. No file is a host that gives nothing: the language only, and the check of a table finds a primitive that is not registered or a code that is in neither table (the language and the host); a file that is named by an option and is not there, or a file with an error (`registry.md:<line>: ...`), is a wrong use (code 2). A primitive or a code of the host that repeats one of the language is an error. `render` uses the registry only for the class of a primitive in the table "Primitives" of the file it writes.

```powershell
& $p test examples                                                  # the registry.md and the journal.md of the folder are the host "examples"
& $p check my/machine.alula.md --registry my/registry.md --journal my/journal.md
```

## Errors and exit codes

An error is `file:line:column: kind: message` and, under it, the quoted line (the form of the translator); the checks of the table put their issues at the line of the row they come from. The warnings (kind `warning`,
format 2.7) follow in the same form and do not change the exit code. A JSON file has no lines: its issues are at `1:1` (`file:1:1: check: $.states[0].rows[1]: ...`), the notes of `render` as `file:1:1: render: ...`.
A wrong use is `alula <command>: <reason>`.

| Code | Meaning |
|---|---|
| 0 | success (warnings are allowed); also `alula` with no arguments, which prints the help (`nova test src` runs every program of the folder once with none) |
| 1 | errors in a file; a scenario that differs from its machine; a note of `render` |
| 2 | a wrong command or arguments; a file that cannot be read or written; a file of `-o` that exists without `--force`; a folder with no scenarios |

## Examples

Check a machine written in Russian, make the JSON, make the English file, check that, come back to Russian, run the scenarios:

```powershell
$p = "target/alula.exe"
& $p check examples/callee.alula.md                                                    # ok (examples/registry.md and examples/journal.md are beside it)
& $p compile examples/callee.alula.md -o target/callee.alula.json                      # the JSON machine/2
& $p render target/callee.alula.json --language en -o target/callee.en.alula.md        # the same machine in English, canonical form
& $p check target/callee.en.alula.md --registry examples/registry.md --journal examples/journal.md   # ok
& $p convert target/callee.en.alula.md --language ru -o target/callee.ru.alula.md --registry examples/registry.md --journal examples/journal.md   # back to Russian (through the JSON)
& $p summary target/callee.alula.json                                                   # the states, the rows, the actions
& $p run examples/echo.alula.json examples/scenarios/echo-signals.scenario.test.json     # ok
& $p test examples                                                                       # 66 of 66 scenarios passed
```

An error in a file (a transition leads to a state that is not there; the quoted line is cut here):

```
> alula check broken.alula.md
broken.alula.md:58:1: check: $.states[0].rows[0].to: ОЖИДАНИЕ_НЕТ is not a state
    | 1 | сигнал(сообщение_пользователя(содержание: сообщение)) | — | журнал(user_message, text: сообщение); ... | ОЖИДА…
broken.alula.md:58:156: name: состояния `ОЖИДАНИЕ_НЕТ` нет в этой машине; возможно, `ОЖИДАНИЕ`
    | 1 | сигнал(сообщение_пользователя(содержание: сообщение)) | — | журнал(user_message, text: сообщение); ... | ОЖИДА…
> echo $LASTEXITCODE
1
```

## Tests

Each unit is a folder; `nova test` runs a unit with all its `*_test.nv` files (the commands run in them over the memory handlers `mock_os`, `mock_fs`, `mock_io`, with the file system of the test in memory):

```powershell
nova test src/alula_cli --timeout 600            # 174 tests (task 152: the program of 0.3.0 and the files of 2.22, 15 of them new): help, version, compile, render, convert, check, summary, run, test on a small machine (Russian and English), the errors and the codes, the scenarios with `standalone` (task 122)
nova test src/alula_eq --timeout 600             # 89 tests (every table says 2.22 since task 152, `compile` makes the JSON of the product, 2.12 and 2.11 are refused, the line of connection of the fragment Pause in both languages): compile -> render -> compile and convert ru -> en -> ru give an equal JSON on the 7 machines of the product and on the 4 of the nested machines (task 119: `caller`, `callee`, `fan`, `dialog_steps`), the commands are the functions of the translator
nova test src/alula_scenarios --timeout 600      # 22 tests: `test` passes the 364 scenarios of src/machine (the 32 of the nested machines and the 101 of the cycle check too; a parent with its callee from JSON and from a table, a callee that is missing or does not fit, `run` of a parent refused), `run` passes the 75 of the agent step one by one, the chat, the small machines
```

`--timeout 600`: on a loaded machine `nova test` kills a unit after about 100 seconds (`spikes/env/README.md`, task 113); the units of the circles take 60-90 s. The program itself is checked on real files in the log of the task.

## What goes round the compiler

The places in the code that go round a defect of Oracle 0.1.0 carry the mark `// ORACLE-WORKAROUND(N)` (`git grep ORACLE-WORKAROUND`; the items are in `spikes/env/README.md`): the type `CmdResult` is not called
`Outcome` (item 9), the list of lists of the test of the usage errors is bound before the loop (item 52), the first file of a unit imports `std.fs` first (item 32), and the function of the folder scan is not called `collect_names` (item 53).
