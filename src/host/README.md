# host: the contract of the host of the external functions (AL-130)

Module `alula.host`, folder `src/host/`; the reference implementations are in the separate module `alula.host_impls`, folder `src/host_impls/`. The norm is the specification, section 7a, version 2.24 (`spec/alula-spec.md`, `spec/alula-spec.en.md`); the label is AL-130.

## The contract

The host binds the implementations of external functions one function at a time, by the class of the function: `bind_pure`, `bind_volatile`, `bind_acting`. At load every declared external function is bound (an unbound one is a load error). The class of an external function is told by the type of its environment: a pure one gets none, a volatile one gets an environment without write methods, an acting one gets a writable environment; the compiler checks it. Not proven by types: that the implementation does not use output, files, clock or network behind the environment, or capture outside mutable state; this is covered by the import guard, `--strict-effects` (partly) and the test host. The contract belongs to the host, not to the machine file: it cannot be written in a file.

The invariant in one sentence: a volatile implementation does not write the environment; a pure one does not read it.

```nova
export type Host { ... }                                              // the tables of the bindings, the world, the counters
export fn Host mut @bind_pure(name str, f fn([]Value) -> Value) -> ()
export fn Host mut @bind_volatile(name str, f fn(ReadEnv, []Value) -> Value) -> ()
export fn Host mut @bind_acting(name str, f fn(mut ActEnv, []Value) -> Value) -> ()
export fn Host mut @call_primitive(name str, args []Value) -> Result[Value, EvalError]   // the protocol PrimitiveHost: alula_step and eval_with take a Host
export fn Host @check_bindings(reg Registry) -> []str                 // every function of the registry is bound, by the class of the registry; nothing else is bound
```

`ReadEnv` and `ActEnv` are two different records with a private field, not one protocol (Oracle 0.1.0 compares the function types that take a protocol loosely, and a wrong class would compile). `ReadEnv` has read methods only; `ActEnv` has the same reading and `write`. Only the host makes an environment; a literal outside the module is an error.

## What is proven by what

| Door of the invariant | Closed by |
|---|---|
| a write through `ReadEnv` | types: no method (`E7320`), the field is private (`E_FIELD_MODULE_PRIVATE`) |
| an `ActEnv` made outside the host | types: `E_FIELD_MODULE_PRIVATE`, and the field does not take a `ReadEnv` (`E7301`) |
| a function of one class bound by the binding of another | types: `E_NO_MATCHING_OVERLOAD` |
| a closure that captured a mutable world and wrote it | the test host: the version of the world is compared before and after every pure and volatile call; a changed version fails the call (`PrimitiveFailed`) and is kept in `violations_list()` |
| a direct import of an effectful module, output, raw `Io`/`Fs`/`Time`/..., `with <Effect>`, `extern`, `unsafe`, `spawn`/`detach`/`parallel for` | the guard `scripts/guards/check-impl-effects.py` on `src/host_impls/` (in `scripts/guards/run-all.sh`); the list of effectful `std` modules is derived from the `std` sources |
| an effect in a signature | `nova check --strict-effects`; `nova info src/host_impls` shows an empty effect surface |
| a pure function that only READS the world through a capture | not seen by the version (reading does not change it): the guard and a review; the test "known limit pure read" keeps the fact written |
| a global state of a module | the review (a `const` is fine); not caught by a tool |

The negative compilations are in `scripts/negative-179/` (each file names its expected code in a line `// expect: <CODE>`); `scripts/accept-179.sh` checks them in a copy of the package.

## The test host

`Host` is the test host as it stands: `stats()` gives the counters by class (`pure`, `volatile`, `acting`) and the number of broken contracts; `world_version()` is the version of the world; `host_over(world)` builds a host over a world the caller keeps, so a test can hand a closure the same world and see the host catch it (`host_test.nv`, tests "closure ..."). The world of the reference host is a store of values by a text key (`World`, `env.nv`); a host of a product has its own world and its own environment types by the same pattern.

## Implementations

The module `alula.host_impls` (`impls.nv`) holds the bodies as named `export fn`, not closures: the standard `new_id` (it reads the key `next_id` of the world; since 2.25 the time is the stamp of the event, `event.at`, not a function) and a few small ones, one per class (`advance_clock` moves the key `clock` of the world and `lookup` reads it: a host may keep a clock for other things than the time of a machine). The rules for a body are in the head of the file. `bind_reference(host)` binds them all.

## Not here (task 181)

The check of the bindings against the declarations of a machine FILE (the section `## External functions` of the file, the name, the class and the signature agree with the registry; a mismatch is an error naming the function) is made when a file is loaded and belongs to the integration of the release (task 181, with the external functions of task 175). Here `check_bindings(registry)` checks the bindings against the registry of the host: every registered function is bound, by the class of the registry; the signature (parameters and result) is not compared, an implementation takes `[]Value`.

## Tests

```
nova test src/host --jobs 2          # the contract and the test host
nova test src/host_impls --jobs 2    # the reference implementations through the host
sh scripts/accept-179.sh             # the criterion of the task: the specification, the negative compilations, the test host, the guard, --strict-effects
```
