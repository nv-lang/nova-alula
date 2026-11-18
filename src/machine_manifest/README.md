# machine_manifest: the public manifest of a machine and the identities of the integration

Module `alula.machine_manifest`, a SIBLING of `alula.machine`, `alula.machine_table` and
`alula.machine_typed` (one folder is one module and one unit of tests). The norm is
[spec/alula-value-codec.md](../../spec/alula-value-codec.md), the section "Canonical manifest и
идентичности" (task 017, the epic 0.29 result B); the model reference is `tools/typed_value_codec.py`
(`canonical_manifest_bytes`, `contract_id`, `_manifest_projection`, `SUPPORTED_CODEC`,
`SUPPORTED_EVENT_ENVELOPE`). The fixed vectors are literals in `manifest_test.nv`: the manifest vector
of the contract (`sha256:4f1c2bb4…`), the projection of a real-shaped machine (`sha256:830f6998…`,
computed once by the model), and the artifact vectors of the framing of the result B.

## What is here

| Function | What it does |
|---|---|
| `manifest_of(def)` | the public projection of a CHECKED machine (the model of `machine_table`): the keys `alula_version`, `machine`, `revision`, `types` (aliases/records/variants), `parties` (`{name, kind, inputs, result}`), `signals` (`{name, party, fields}`, the machine signals with `party: null`), `queries` (empty for a machine of the tree `machine/2`), `codec`, `event_envelope`; the machine types are mapped onto the contract descriptors (`int>=n` → `{"int_min": "N"}`, `?T` → `{"optional": D}`, `[]T` → `{"list": D}`, `{K: V}` → `{"map": [DK, DV]}`, `full {K: V}` → `{"full_map": [enum, D]}`, a literal set → `{"literal_set": [...]}`, a tuple → `{"tuple": [...]}`) |
| `codec_projection()`, `envelope_projection()` | the FIXED semantic tables of the contract; any other value is refused by the validation, even valid JSON |
| `validate_manifest(m)` | the projection checked key by key: exactly the public keys (no `contract_id`, no `artifact_id`, no locator, no timestamps), the arrays in the normative order (the canonizer does NOT sort), the descriptors validated by `typed_validate` of `machine_typed` against the declared types of the same manifest, no floats, the integers inside the safe JSON range |
| `canonical_manifest_bytes(m)` | the validation first, then the compact canonical JSON bytes (the object keys sorted by the code point) |
| `contract_id(m)` | `sha256:` + SHA-256 over the canonical manifest bytes |
| `manifest_from_json(text)` | the manifest as the consumer reads it: the strict parse (a repeated key is refused by the parser), then the full validation |
| `artifact_id(executor, tree, libraries, registry_text, journal_text)` | the identity of the BUILD. The framing is the decision of the result B (the contract fixes what artifact_id identifies, not the bytes): the canonical JSON of `{"executor", "journal", "libraries", "machine", "registry"}`, where `machine` is the digest of the canonical bytes of the compiled tree, `libraries` is `{"hash", "name"}` sorted by the name, `registry`/`journal` are the digests of the host texts (an empty text = no file). No storage address, no instance pin |

## The program

`alula compile <file.alula.md> --manifest <file>`: after a successful compile (the checks are not
bypassed: `--no-check` with `--manifest` is a wrong use) the manifest goes to the file in the canonical
form, and the identities are the notes of the standard error:

```
alula: note: manifest contract sha256:…
alula: note: manifest artifact sha256:…
```

The manifest file holds no identities: the consumer computes `contract_id` from the manifest itself, so
a manifest copied from another storage is verified by its content.

## Tests

```
nova test src/machine_manifest --timeout 600
```
