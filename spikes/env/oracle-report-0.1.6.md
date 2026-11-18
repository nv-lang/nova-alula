# Report to the Oracle: three open defects on 0.1.6

2026-11-18. Package `nova-alula` (the commit that adds this report; the survey items are the 0.1.6 probe of 2026-11-17).
Toolchain: **Oracle 0.1.6** (canonical install `C:/work/nova/oracle-016-6/nova-oracle-0.1.6-windows-x86_64/`,
`. .\setup-env.ps1`; Clang from `C:\Program Files\LLVM\bin`), Windows x86_64. The release notes of 0.1.6 name none of
these three items ("the known limitations carry over from 0.1.5").

| Item | State on 0.1.6 | Reproduction | Package impact |
|---|---|---|---|
| 128 `fixarr_to_vec_arg` | **RED** — the checker refuses | `nova build src/fixarr_to_vec_arg_direct.nv` | 3 workaround marks; the boxed form is the dodge |
| 129 (a) const-pool clobber | **GREEN** (closed by 0.1.4) | `nova test src/const_pool_clobber.nv` | none (the sample stays) |
| 129 (b) method/effect resolver in a merged unit | **RED** under `--strict-effects` — a reproducible case (probe below) | two-module probe below | the mark in `src/host_contract/contract.nv` |
| 129 (c) `std.os.proc` | **the path-form import is broken; the module form builds** | two-module probe below | the scripted processes of `battle_host` are removable (our change) |
| embed→Fs | **a symptom of 129 (b), not of embed** — RED under `--strict-effects` only | `nova test src/alula_cli --strict-effects` | none needed once the effect lookup is fixed |

The exact messages and commands are below. The reproductions of 128 and 129 (a) live in `spikes/env/repro_engine/`
(a Nova package of its own: `nova build src/<name>.nv`).

## 128. `[N]T` returned by a std function cannot be an argument of a `[]T` parameter

```
cd spikes/env/repro_engine
nova build src/fixarr_to_vec_arg_direct.nv
→ src/fixarr_to_vec_arg_direct.nv:24:37: error: [E7301] cannot pass `[32]u8` as argument `data` of type `[]u8`
```

The A side passes `Sha256.hash(data)` straight into a function taking `[]u8`. The B side copies the bytes out by index
first (`bytes_of`) and is green:

```
nova build src/fixarr_to_vec_arg_boxed.nv   → built (8.3 s)
./fixarr_to_vec_arg_boxed.exe               → null digest = ea86c4d2…b10d42aa
```

Asked: either accept a fixed array as a slice argument (the C emits the struct where the Vec pointer is expected), or
make the checker say so at the call — it does now (E7301, 0.1.6; on 0.1.4 the same A side went through the checker and
broke the C instead).

Package: three marks, all `ORACLE-WORKAROUND(128)` — `src/battle_host/battle.nv:202`, `src/machine_typed/typed.nv:1356`,
`src/thin_host/thin_host.nv:369`; the helper is `bytes_of` in `typed.nv`.

Oracle (2026-11-18): confirmed. **E7301 stays the final refusal** — no implicit `[N]T` → `[]T` (a value/view design
item); the diagnostic gets a hint/fixit with the supported forms (copy by index, an explicit view helper) and is
documented. The three marks stay.

## 129. `const_pool_clobber` — three independent manifestations

**(a) the 0.1.0 literal/assert clobber of a peer file — closed by 0.1.4.** The sample stays green on 0.1.6:
`nova test src/const_pool_clobber.nv` → PASS 1 / FAIL 0.

**(b) the resolver of a merged unit — a method call and an effect lookup — RED on 0.1.6, reproducible.** In a merged
unit of several files a DIRECT call of a method of another module's type with a constructor as an argument emits the
arguments as `void*` and the C does not build (`@engine.submit_event(Incoming.incoming(...), …)`, the host-contract
unit, the 0.29 result F); the method resolver with equal arity may also pick a WRONG method. The dodge: bind the
constructor to a typed local, or route the call through a free function IN THE OWNER'S module; the package names the
operations free functions over the handle (`submit_admission` of `engine.nv`). Mark: `src/host_contract/contract.nv:174`.

The same lookup shows on the effect side: `--strict-effects` takes the callee by NAME over every declaration of the
merged unit, ignoring arity, module and types (`sig.fn_decls.get(name)`; `check_callee_effects` →
`check_transitive_effect_strict`). Two modules with a same-name function, one pure and one `Fs`, make a call of the pure
one "require Fs". Minimal probe (three modules of one package; built on 0.1.6):

```
// puremod.nv:  module overloadprobe.puremod
export fn f() -> int => 1
export fn call() -> int => f()

// effmod.nv:   module overloadprobe.effmod
import std.fs.{Fs}
fn f(x str, y str, n int) Fs -> int => n
export fn g() -> int => 0

// mainmod.nv:  module overloadprobe.mainmod
import std.io.{Io}
import overloadprobe.puremod.{call}
import overloadprobe.effmod.{g}
fn main() Io -> () { println("${g()}"); println("${call()}") }
```

`nova build src/mainmod/mainmod.nv --strict-effects` → `E_UNDECLARED_TRANSITIVE_EFFECT: call to f requires effect Fs`
— and the false `Fs` leaks into the standard library: the lambda parameter `f` of `std/src/collections/vec_iter/core.nv`
(672, 756) is checked against the same overload too. Without the flag the program builds and prints `0` / `1`.

In `alula` the two declarations are `alula.examples.library_files()` (pure, `src/examples/data.nv:147`) and
`alula.alula_cli.library_files(text, file, Args) Fs` (private, `src/alula_cli/cli.nv:163`). The report's first version
blamed `embed_str`; that was wrong (see the next section).

Oracle (2026-11-18): **taking 129 (b) and the "embed" symptom as ONE item** — the effect lookup of a call must account
for arity, module and types; the minimal probe becomes a regression fixture; then the `contract.nv:174` mark and the
free-function dodges are removable. 129 (b) is raised: it now has a reproducible case.

**(c) `std.os.proc` — corrected on 0.1.6: the path-form import is the trigger, not the module.** `std/src/os/proc.nv`
declares `module std.os` and sits beside `os.nv` of the same module. Importing the FILE PATH as if it were a module
name breaks:

```
# probe A: /tmp/procprobe, nova.toml + src/proc_import/proc_import.nv
import std.os.proc.{real_proc}
nova build src/proc_import/proc_import.nv
→ std/src/os/proc.nv:408/411/437/446/455: [E_UNKNOWN_TYPE] unknown type `ExitStatus` / `Command` / `Child`
  (these types are declared in the sibling os.nv of the same module — the import merged proc.nv alone)
```

The module form builds and runs:

```
# probe B: the same package, the import changed
import std.os.{Proc, real_proc}
fn main() { with Proc = real_proc() { println("proc import") } }
nova build src/proc_import/proc_import.nv   → built (118.6 s)
./proc_import.exe                           → proc import, exit 0
```

Reading: there is no module `std.os.proc`; the compiler accepts the path as an import name, merges the one file and
reports the missing types in the standard library, not at the user's line. Earlier probes (0.1.4/0.1.5) with the same
path form saw codegen `undefined identifier dedupe_envs` / `env_blob_of` at `proc.nv:414–415`; on 0.1.6 the same wrong
import stops earlier, in the checker. Either way the path form is the trigger.

Asked: reject an import name that is not a module (the file's `module` line wins; a path alias needs its own form) and
point the error at the import line. **Package consequence:** the scripted process primitives of `battle_host` were based
on this path import; with `import std.os` they can be real processes. That is our change, not the Oracle's; the survey
item 129 (c) is corrected by this section.

Oracle (2026-11-18): confirmed (0.1.6; in their probe the module form built in 34 s). Taken: the import resolver must
refuse a name that is not a declared module, with the error at the import line and a `std.os` hint, and must not merge
one file as a module; the minimal probe is pinned. Package: switching `battle_host` to `import std.os` and the real
processes is our task.

## The `--strict-effects` symptom on `library_files` (129 (b), not embed)

```
cd <package>
nova test src/alula_cli --strict-effects
→ CODEGEN-FAIL   src/alula_cli/check_test
  src/examples/data.nv:155:14: error: [E_UNDECLARED_TRANSITIVE_EFFECT] call to `library_files` requires effect `Fs`,
  not declared in the enclosing function's signature and not handled by an enclosing `with Fs = …` block
  (--strict-effects; D62 §Правило 1 — without this flag this is only a warning).
  Hint: add `Fs` to the enclosing fn's effect-row, or install `with Fs = handler { … }` around this call.
```

The first version of this report blamed `embed_str`: the chain is `library_files_in(dir)` → `library_files()` →
`embed_str(...)` at `src/examples/data.nv:147–157`. That was wrong. `embed_str`/`embed_dir` are resolved before the
type check (step 3 of the pipeline) and add no effect row. The `Fs` comes from the OTHER `library_files`
(`src/alula_cli/cli.nv:163`, 3 arguments, `Fs`) through the name-only lookup of 129 (b). A normal build and the normal
test suite are green; only `--strict-effects` is red.

Oracle (2026-11-18): the embed request is **withdrawn** — this is the same 129 (b) item; fixing the effect lookup clears
the site. The wording of `docs/prerelease-0.29.0.md` ("embed_str asks for Fs") is superseded by this section; the survey
carries the same correction.

## Workarounds and their removal conditions

| Item | Place | Remove when |
|---|---|---|
| 128 | `battle_host/battle.nv:202`, `machine_typed/typed.nv:1356`, `thin_host/thin_host.nv:369` | the fixed array is accepted as a slice argument (E7301 is final for now: keep the marks) |
| 129 (b) | `host_contract/contract.nv:174` + the free-function routes | the resolver accounts for arity, module and types (the method and the effect lookups; the `library_files` strict-effects site clears) |
| 129 (c) | `battle_host` scripted process primitives | our own import change to `std.os` (no Oracle fix needed) |
| embed→Fs | — (the site is 129 (b), no package workaround) | — |

Survey: `spikes/env/README.md` — items 128, 129, the 0.1.6 part of 1a; this report supersedes 129 (c).
