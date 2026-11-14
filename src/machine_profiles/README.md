# machine_profiles: the interaction profiles of the parties at the machine border

Module `alula.machine_profiles` (the epic 0.29 result C, R3). The model and the checked matrix are
[spec/alula-interaction-profiles.json](../../spec/alula-interaction-profiles.json) (the executor of
the model checks: `tools/check-interaction-profiles.py`); this module carries the same
correspondences into the package as code, so that the check of a party and the check of its BINDING
speak of one and the same profile. The profile does not replace the kind: a machine declares the kind
it declares (spec 1); the profile names the lifecycle and the allowed bindings of the next
implementation stages ([docs/interaction-profiles.md](../../docs/interaction-profiles.md)).

| Function | What it does |
|---|---|
| `profile_of_kind`, `party_kind_of_word` | agent → `call`, human/enhanced/gatekeeper → `decision`, machine → `managed-call`, free_input → `input-only`; the locally accepted kind `service` of another project names no kind here (the model: `not_implemented`, not carried) |
| `binding_kinds_of_profile`, `kinds_of_binding`, `default_binding_of_kind` | the binding kinds of the matrix (`host_provider`, `human_principal`, `policy_authorized_agent`, `setting_resolved_principal`, `compatible_child_machine`, `human_input_endpoint`) and their inverse; the binding kind names the ROLE of the binder, not the authority |
| `check_party_profile` | the contract of the profile over the declaration of the party: a typed result for `call`/`managed-call` (none for `input-only`), a counter for `decision` (none for `input-only`), the signals of the gates and of a free input (a call takes none), the progress parts only of a `call` that declares them, the child machine only of `managed-call`. Beside the checks of the table (`check_parties` of `machine_table`), which keep their place; the tests walk every kind so the two do not drift apart |
| `check_party_bindings` | the party declarations against the bindings of the host: every declared party is bound by an allowed binding kind of its profile, nothing else is bound; the refusals of the card: an unbound party, an extra capability (a binding of an undeclared party), a binding outside the profile (the NAME of a binding grants no authority — a gate bound as a host provider is refused even when the target names a real provider), a binding named with a word that is no kind of the package (`service`) |
| `default_bindings`, `check_no_service` | the bindings of a test host (every declared party with its default binding kind); the refusal of the word `service` where it arrives |

The border: `alula check` runs `check_party_profile` over the parties of a translated machine of 0.29
after the checks of the table (a profile refusal is an error at 1:1; the seam of 2.25 keeps its own
forms). The runtime binding of a party to a provider is the work of the result E (the host effects);
this module is the contract the compiler and the host border agree on.

## Tests

```
nova test src/machine_profiles --timeout 600
```
