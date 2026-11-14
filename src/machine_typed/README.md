# machine_typed: the general typed value contract of the integration

Module `alula.machine_typed`, a SIBLING of `alula.machine` (one folder is one module and one unit of
tests). The norm is [spec/alula-value-codec.md](../../spec/alula-value-codec.md) (task 017, the epic
0.29 result A); the model reference is `tools/typed_value_codec.py` (Python), this module is the runtime
half. The unit exists as a separate folder because of the Oracle 0.1.0 defect of the merged compilation
unit (the survey item 129, `const_pool_clobber`): inside the machine unit the vectors build C that does
not compile; the small unit is green on 0.1.0 AND on 0.1.4.

| File | What it is |
|---|---|
| `typed.nv` | `typed_validate` (the table of declarations alias/record/variant and the root descriptor, checked BEFORE any value is read), `typed_json_encode` / `typed_json_decode` (the typed JSON of the contract: an i64 is the canonical decimal STRING, NaN/±Inf are the `$float` tags, an optional is `{"none": true}` / `{"some": v}` with full nesting, a map and a full_map are arrays of pairs, records are objects by the declared fields, no coercion), `typed_bytes` / `typed_digest` (the schema-aware canonical bytes with the markers N B I J F S C U L T O M G R V Y and the u64 big-endian lengths; the digest is `sha256:` + SHA-256 over `ASCII("alula-value-digest") || 00 || bytes`; `std.crypto.sha256`, see `nova.toml`) |
| `typed_test.nv` | the fixed vectors of the contract as LITERALS (19 vectors of the spec table plus the f64 canonical tokens computed once by the model), the JSON roundtrips, the f64 edges (the subnormal `5e-324` and the maximum finite decoded exactly from the text, the refusal of `1e999`, the `$float` tags), and the negatives of the validation (an unknown primitive, a one-element tuple, an unsorted literal set, an alias cycle, a full_map over a variant with fields, the schema checked before an empty value) |

The language codec of the answer of a party `agent` (AL-153) stays in `alula.machine/decode.nv`: there an
int is a JSON number and the specials are refused; that narrowing is the declared profile of the language,
this module is the integration contract.

## Tests

```
nova test src/machine_typed --timeout 600
```
