# spikes/env: the environment of the package alula on Nova

The notes on **Nova Oracle 0.1.0 on Windows x86_64** that the code of this package depends on: how to install the compiler and run the tests (part 1), and the defects and limits of
Oracle that the code goes round ("Known problems"), with the reproductions in `repro_engine/`. The items keep the numbers they have in the survey of the CrewHarness repository, where the package was
written (`spikes/env/README.md` there): the marks in the code (`ORACLE-WORKAROUND(N)`) name them, so a number is never reused here; the items that the package does not meet (the child process, the
WebSocket server, the ACP client, PostgreSQL, Polaris) are kept in that repository only.

| Directory | What it is |
|---|---|
| `repro_text_import/` | a program: `import std.text` and a pattern variable `text` of another module (item 32); `nova build src/text_import.nv` |
| `repro_engine/` | minimal reproductions of the Oracle 0.1.0 defects found while writing the engine, the evaluator, the interpreter, the translator and the program `portolan` (a Nova package of its own: `nova build src/<name>/<name>.nv`) |

## 1. Install Oracle 0.1.0 (no system changes)

Needs: Windows 10/11 x86_64, Clang (LLVM) installed on the machine, Node 22+ (global `WebSocket`), `gh` or `curl`.
Everything below uses PowerShell; the environment variables and `PATH` change for the current session only.

```powershell
# download and verify (SHA-256 must equal the line in SHA256SUMS)
mkdir C:/work/oracle-dl; cd C:/work/oracle-dl
gh release download oracle-v0.1.0 -R nv-lang/nova -p "nova-oracle-0.1.0-windows-x86_64.zip" -p SHA256SUMS
(Get-FileHash nova-oracle-0.1.0-windows-x86_64.zip -Algorithm SHA256).Hash   # compare with the next line
Get-Content SHA256SUMS                                                         # the line for the windows zip
# expected: 54093317b1474028f3e4ef5ace4ac2c59b38dd52074f2668cd425f5e2670141f

# unpack
Expand-Archive nova-oracle-0.1.0-windows-x86_64.zip -DestinationPath C:/work/nova

# every new PowerShell session: dot-source the setup script (the leading dot matters)
. C:/work/nova/nova-oracle-0.1.0-windows-x86_64/setup-env.ps1
nova --version        # nova 0.1.0
```

The archive name in the quickstart on the release tag (`nova-v0.1.0-windows-x64.zip`) is not the real name
(`nova-oracle-0.1.0-windows-x86_64.zip`).

### C compiler

`nova build` picks the compiler itself (`--toolchain auto`). On the survey machine that is **Clang from
`C:\Program Files\LLVM\bin`, which is not in `PATH`** - the compiler found it. Explicitly: `nova build x.nv --toolchain clang`
(or `--clang <path to clang.exe>`). `--toolchain msvc` fails on Oracle 0.1.0, see "Known problems". Whether Clang
alone (without any Visual Studio) can link on a clean machine was not isolated: the survey machine has Visual Studio 2022
Community and Build Tools 2026 installed.


## Known problems (for the Nova integrator)

8. **`enum_str_payload`**: a generic sum type with a `str` variant (`type Output[I] enum | Send(I) | Log(str)`) does not
9. **`prelude_outcome`** (with the helper module `prelude_outcome_def`): a user type named like a prelude type (`Outcome`,
10. **`nested_generic_pattern`**: the nested pattern `Some(Answer(reply))` over a generic payload binds `reply` to a NULL
    pointer in the C (`*(nova_str*)(NULL)`), the program does not link (`undefined symbol: Nova_str_method_eq`). Two nested
    `match`es, one level each, work.
11. **`protocol_typed_field`**: a record field whose type is a protocol cannot be called through (`e.machine.initial()`): the
    C passes a `NovaBox_Machine` where the method wants the concrete struct. A record generic over the machine type
    (`Engine[M]`, `M Machine`) works and is what the engine uses.
12. **`generic_protocol_inference`**: a generic function bounded by a protocol with two type parameters (`M Machine[S, B]`),
    called with `S`, `B` to be inferred, generates C with an undeclared variable (`use of undeclared identifier 'r'`).
13. **`generic_protocol_one_param`**: the same with one type parameter (`M Machine[S]`, `S` a sum type). The engine therefore
    uses a protocol without type parameters over concrete types, and the machine state crosses it as encoded text.
    **Task 102 found the way round (item 26): written out, the type arguments compile; the engine now has a typed state.**
20. **`output_over_4k`**: a test binary blocks on its stdout when its lines (`  PASS: <name>` per test) come to more than 4096 bytes and nobody reads
    the pipe. `nova test` of one unit reads it; `nova test <dir>` over several units that run at once did not, and killed the idle binary after
    about 70 s (`TIMEOUT`). Keep the output of a unit under 4 KB: split it, shorten the names.
25. **`nested_module`**: a module in a folder two levels under the source root (`src/nested_module/inner/inner.nv`, no `.nv` in the
    middle folder), declared as the path from the source root with the package prefix: E_D78_MODULE_PATH_MISMATCH although the
    "expected (rev-1 legacy)" text printed by the compiler equals the declared one.
26. **`typed_state_explicit`** (a working sample, PASS): the defects of items 12 and 13 are in the INFERENCE of the type arguments. With the arguments of the free
    functions written out (`start_engine[ChatState, ChatSession](...)`, `resume_engine[ChatState, ChatSession](...)`) the protocol `Machine[S]`, the records
    `Engine[M, S]` and `EngineState[S]` with a sum type `S` that has payloads, `Transition[S]` and a protocol parameter `mut environment Environment` all compile and
    run; methods of a generic record need no arguments (`e.on_arrival(...)`). The engine of the product uses this form since task 102 (the state is typed, encoded
    only at the border of the snapshot). Parsing detail met on the way: a record literal in the head of a `match` (`match f[A, B](Chat { ... }) { ... }`) is a
    syntax error (`expected ')', got '{'`), a name bound before the `match` works.
27. **`option_try_generic_enum`**: the operator `?` on an `Option` whose payload is a sum type, in a generic function instantiated with that type, writes the local
    with the type name `Nova_Mode_p`, which does not exist (`unknown type name`, then pointer/value mismatches). `match value { None => ..., Some(inner) => ... }` is
    fine; the engine's `decode_snapshot` uses it.
29. **`user_request_vs_http`, `user_session_vs_postgres`**: the table of type names is one for the whole program, **dependencies included**. A user generic record `Request[T]`
    (the engine had one) next to `http` (every program with Polaris has it) is taken for the `consume` record `Request` of `http`: `E_CONSUME_KEYWORD_MISSING` on a plain binding,
    `E7310` "type `Request` is not generic" where the user's type is spelled `Request[str]`; `Response[R]` the same way. A user record `Session` next to the driver nova-postgres,
    which has its own `Session`, stops the driver's own file (`E_MISSING_FIELD_IN_LITERAL`). The engine types are now `PartyRequest` and `PartyResponse`, the record of the hub is
    `Dialog`. Same family as items 9, 14, 21 and 22 (and 28 of task 102); the checker does not say that two types of one name exist.
32. **`repro_text_import`** (a program): `import std.text` in one module makes a variable named `text`, bound by a record pattern (`Garbage { text } => text.byte_len()`) in another module,
    mean the module: `E7401` no function `byte_len` in module `text`. The import is needed in `nova build` for `[]str.join` (a `nova test` build has it already, so tests do not show it);
    without it `join` is "no field or method `join` on type `Vec`", or, with `std.fs.Path` imported, `E_RECV_METHOD_MISMATCH` (it resolves to `Path.join`).
33. **`for_in_enum_literal`**: `for c in [Pure, Writing]`, an array literal whose items are variants of a user enum without payload, does not compile:
    CODEGEN-FAIL "for-in: cannot resolve iterator type for expression of C-type 'nova_unit'". A function that returns the list (`-> []Class`) and is
    iterated is fine, so is a literal list of texts or of ints.
34. **`option_enum_named_variants`**: an enum with a variant with named fields (`FieldOf { target, name }`) and another variant that holds a list of records with
    an `Option[ThatEnum]` field, the record declared BEFORE the enum, breaks the C: the generated equality reads the payload as `payload.FieldOf._0` while the
    struct has the members `target`, `name` (CC-FAIL "no member named '_0'"). The record declared after the enum compiles; so does `[]ThatEnum` instead of the option.
36. **`for_in_record_list_literal`**: `for s in [make(1), make(2)]`, an array literal whose items are records made by calls, does not compile: CODEGEN-FAIL "for-in: cannot resolve iterator type for expression of
    C-type 'nova_unit'" (the family of item 29). Bind the list first (`ro all = [make(1), make(2)]`, `for s in all`).
37. **`type_named_like_variant`** (with the helper module `type_named_like_variant_def`): a user type named like a CASE of an enum of another module (`type Reading enum | ...` here, `Class.Reading` there) makes
    every use of that case in the other module "E7330 `Reading` is a sum type, not a value" - the error is reported in a file the user did not touch (type names and case names share one table of the program).
38. **`user_type_next`**: a user record named `Next` breaks the compile of the STANDARD library (`E_BOUND_NOT_PROTOCOL` at `std/src/collections/vec_iter/core.nv`: its protocol `Next` is hidden by the record); the
    clash is not reported at the declaration. The same family: a user record `Slot` clashes with the one of `std/src/collections/hash_map` (`E7310 type Slot is not generic`), `Output` (items 14, 21).
39. **`same_type_name_two_modules`** (with the helper module `same_type_name_def`): two modules of one program that declare a record of the same name (`Pair`) are not isolated: a literal of the imported
    module's `Pair { name, value }` is checked against the fields of the importer's `Pair` - `E_MISSING_FIELD_IN_LITERAL` in the file of the imported module. Type names are global to the program (the units of
    task 107 keep the names of their types unique: `ReqField`, `Goto`, `EventRead`).
40. **`user_type_child`**: a user record named `Child` (the core of the machines had one, the node of a tree of an expression) next to any import of `std.os`, which has the consume record `Child` of a child
    process, breaks the compile of the program: `E_CONSUME_KEYWORD_MISSING` ("binding `c` holds a consume-required instance of type `Child`") in the reproduction, `E_MISSING_FIELD_IN_LITERAL` and
    `E_FIELD_MODULE_PRIVATE` in `std/src/os/proc.nv` when the program is built. The checker does not report the clash at the declaration (the family of items 9, 14, 21, 22, 29, 37-39). The tests of the core
    did not import `std.os`, so they passed; `nova build src/machine_translate.nv` (it needs `std.os.args`) failed. The record is `ExprChild` now.
41. **`same_name_other_type`**: a parameter named `list` of the type `[]Pair` in one function and a name `list` bound by a pattern (`Err(list)`) to a `[]Problem` in a test of the same module: the generated C reads the
    field of the second as a field of the first (`no member named 'code' in 'struct Nova_Pair'`). The two names are in different functions, the types are different and not generic. A different name
    (`problems`) compiles. The translator and its tests give every list a name of its own by its type (`problems`, `pairs_in`, `errors_in`, `tokens`, `found`).
42. **`split_index`**: indexing the result of `str.split(sep)` (`parts[0]`, the result is an iterator) passes the checker and the code generator stops with `[INTERNAL-PANIC] [E_CODEGEN_TYPE_UNKNOWN] Index element type unknown for
    obj_ty="NovaValue_SplitIter"` with the place of the generated expression, not of the source line. Read it with `for part in text.split(sep)` and push to a list.
43. **`user_fn_fence`**: a user function named `fence` is generated as the C function `nova_fn_fence`, which the runtime header already declares (an atomic fence with the argument `ord`); the checker does not
    report the clash at the declaration, the C compiler stops: "conflicting types for `nova_fn_fence`", "too few arguments to function call, single argument `ord` was not specified" (CC-FAIL; the family of items 9, 14, 21, 29,
    37-40: a name of the program against a name of the runtime). The helper of the tests that returned three backticks is `ticks` now.
44. **`record_after_enum_list`**: a sum type with a variant that holds a list of a record, the record declared AFTER the sum type and holding the sum type (`type Js enum | JsObj([]Pair)`, then `type Pair { key str, value Js }`), breaks the C of a `match`
    on it: the payload bound by the pattern (`JsObj(pairs)`) is a `Vec<nova_int>`, and `for q in pairs { q.key }` is CC-FAIL "member reference base type 'nova_int' is not a structure or union". The record declared BEFORE the sum type compiles (the `TxJ` and `TxKV` of the
    translator are written so); item 34 is the same family from the other side.
45. **`mut_of_ro_param`**: `mut out = items` with `items` a parameter without `mut` (or a `ro` binding) that holds a list or a text is `E_READONLY_COERCE`; a copy has to be built by hand in a loop. The translator does it in `sc_clone`, `p_copy` (task 108),
    `rn_copy`, `rn_with` (task 113). A plain copy of a value would do.
46. **`assign_mut_param`**: assigning a new list to a `mut` PARAMETER of a heap type (`items = []str.new()`) changes only the local name; the caller's list stays as it was (the compiler warns). The state of the classification of the lines
    keeps its lists in the fields of a `mut` record and assigns a field (`TxClsState` in `cls_flush`).
47. **`leak_ab`** (a working sample, PASS; the defect is not reduced): a unit that imports a module whose test files have a function with the parameters `a`, `b` of a record type gets the C of the prelude method `EmbeddedDir.merge` wrong (`no member named 'path' in 'struct Nova_StepTrace'`),
    when the program embeds a file; seen in the unit `src/machine_text_render`, which imports `machine_text_eq` (its `eq_test.nv` had `trace_diff(a StepTrace, b StepTrace)`; the parameters are `ta`, `tb` now). The family of item (b) of task 107 and of item 32/35 notes of task 099. Rename the parameters.
48. **`user_type_vs_driver_variant`**: a user record `Row` (the row of a table of states of the machines that are data, `src/machine_table`) in the same program as the driver nova-postgres, whose protocol enum has the variant
    `Message.Row { values }`, stops the driver's own file `session.nv` (`E_MISSING_FIELD_IN_LITERAL`: the literal `Row { values }` is read as the user's record). A variant name and a type name share one table (the family of items 29, 30, 37).
    The record is `TableRow` now; the hub is the first program that links the driver and the machines that are data.
50. **test helper `ev` next to the function `ev`** (no small reproduction; the reproduction is the unit): the test file `src/machine/eval_test.nv` had a helper `ev(e)` and the module has a private `ev(e, env, host, depth)` in
    `eval.nv`. The unit of the module itself passes; the unit `src/server`, which imports `crew_harness.machine` (through `portolan.nv`), stopped in C: "conflicting types for `nova_fn_12crew_harness7machine2ev`" (the mangled
    name has no parameters, and the test file of the imported module was compiled into the importer's unit). A small program with the same two functions and an importer PASSES (tried), so the trigger is something more in the graph.
    The helper is `ev_plain` now; to see the defect, rename it back and run `nova test src/server`.
51. **`match_record_literal_arg`**: a record literal inside a list literal (or directly) in the argument of the call that is the scrutinee of a `match` is a syntax error ("expected `,` or `]` in array literal, got `{`"): the parser takes
    the `{` for the block of the `match` (the note (e) of task 110 had the direct form). Bind the value with `ro` (or a function) before the `match`.
52. **`for_in_list_of_lists`**: `for item in [["a"], ["b", "c"]]`, an array literal whose items are arrays, does not compile: CODEGEN-FAIL "for-in: cannot resolve iterator type for expression of C-type nova_unit" (the family of items 29 and 36); in a unit that
    imports `std.encoding.json` the loop is read as an iteration over a JSON object and the C stops with "passing _NovaTuple_2_..._Nova_JsonValue_p to parameter of incompatible type Nova_Vec____nova_str *". Bind the list first (`ro all = [["a"], ["b", "c"]]`, `for item in all`).
53. **`same_fn_name_two_modules`** (with the helper module `same_fn_name_def`): two modules of one program that each declare a PRIVATE function of the same name are not isolated under `--strict-effects`: the call inside one module is checked against the OTHER module's function, 
    "E_UNDECLARED_TRANSITIVE_EFFECT: call to `scan` requires effect `Fs`" at a line of a file that did not change (without the flag the program builds and runs). Run `nova test src/same_fn_name_two_modules --strict-effects`. The family of items 37-39 for functions; rename one of them.
54. **`generic_literal_args`**: a record literal of a generic record with its type arguments written, `Holder[str] { id: "a", input: "b" }`, is a syntax error (E_STMT_SEP_MISSING at the `{`: `Holder[str]` is read as a complete expression). The literal has to be anonymous and typed by its context
    (`ro h Holder[str] = { id: "a", input: "b" }`) or made by a function that returns it. Met in task 091; the engine makes its `PartyRequest[str]` and `Reply[str]` by `request_of` and `reply_of`.
55. **`mock_fs_create_dir_all`**: `create_dir_all("/a/b/c")` on the memory file system (`mock_fs`) makes only the LAST folder: `try_exists("/a/b")` is false afterwards (`read_dir` of it works), the real file system makes every folder above. Met in task 116 (the note (d) of "Also met in task 116");
    the tests of the program `portolan` make the folders above a file one by one (`make_parents`).
60. **A protocol method that nothing calls is cut from the program, and the C of the program does not build** (no small reproduction: three attempts at one did not fail; the reproduction is the product: in `src/engine/engine.nv` build the environment with `StepEnvironment.new()` instead of `StepEnvironment.carrying(...)` and run `nova test src/crew_harness.nv`, or `nova build src/portolan.nv -o target/portolan.exe`). The protocol `Environment` got the method `mut @order_signal(order SignalOrder)`; the only call of it is in the interpreter of Portolan, and a program that links the engine but not that call (the hub `src/crew_harness.nv`) stopped in C: "returning 'int' from a function with incompatible result type 'nova_unit'" in the thunk of the vtable (the method itself is not emitted), while `nova test` of the unit that has the call stayed green. Worked round: the engine makes its environment by `StepEnvironment.carrying`, which calls the method, so every program that links the engine has a call site.
61. **`none_arg_generic_option`**: a literal `None` as the argument of a parameter of the type `Option[Wrap[str]]`, where `Wrap` is a generic sum type, is typed `Option[int]` by the code generator, and `Some(Two)` as an `Option` of the sum type without its argument: CC-FAIL "passing 'NovaOpt_nova_int' to parameter of incompatible type 'NovaOpt_Nova_Wrap____nova_str_p'". `None` for `Option[str]` is fine. Bind the value with its type first (`ro nothing Option[Wrap[str]] = None`) and pass the variable. Run `nova test spikes/env/repro_engine/src/none_arg_generic_option`.

## Marks of the workarounds

Every place of the package that goes round an item above is marked with a comment (`//` in Nova and Node, `#` in scripts, `<!-- -->` in Markdown):

```
// ORACLE-WORKAROUND(N[, M]): what is gone round; how to simplify when item N is fixed
```

`N` is the number of an item of "Known problems" (the first number is the main one); the text after the colon says what the code does instead of the plain form and what the plain form is, so that the mark alone is the instruction for the cleaning. A workaround that no item names gets an item first (with a reproduction in `repro_*/` when it can be reduced).
A text in prose ("item 29", "the driver has a Session") is not a mark: replace it by the mark.

- Where to look: `git grep ORACLE-WORKAROUND`; by item and with the line: `python scripts/oracle-workarounds.py --list`; a summary: `python scripts/oracle-workarounds.py`.
- The index: [workarounds.md](workarounds.md) (item, what, the files that go round it, the number of marks); it has no line numbers and is written by `python scripts/oracle-workarounds.py --index`. Items with no mark are listed as "no workaround in the code": a rule of the language, a limit of the tooling, or a defect the code does not meet.
- How to clean: when Nova fixes an item, take its row of the index, open the files, simplify the code as the mark says, remove the mark, run `nova test` (and `--strict-effects`) and rerun `--index`.
- The guard `scripts/guards/check-oracle-workarounds.py` (it runs with the others, `sh scripts/guards/run-all.sh`) fails when a mark has no `(N[, M]...)` or no text after the colon, when an `N` is not an item of this README, when a mark is not in a comment, or when the index differs from what `--index` writes.
  It warns when an item says "worked round in the code" and has no mark. The marks are searched in the tracked files of `src/`, `scripts/` and `spikes/` ().
