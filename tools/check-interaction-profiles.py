#!/usr/bin/env python3
"""Validate the structured interaction-profile model and adversarial mutations."""
import copy
import itertools
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = ROOT / "spec" / "alula-interaction-profiles.json"
STATUS = "project-model-not-runtime"
PROFILE_FOR_KIND = {
    "agent": "call", "human": "decision", "enhanced": "decision",
    "gatekeeper": "decision", "machine": "managed-call",
    "free_input": "input-only", "service": "call",
}
PROFILE_FIELDS = {
    "call": {"request": ("T", True), "result": ("R", True), "progress": ("P", False), "counter": ("Counter", False)},
    "decision": {
        "opening_id": ("OpeningId", True), "subject": ("T", True),
        "admissibility": ("Admissibility", True), "candidate": ("Choice", True),
        "principal": ("PrincipalId", True), "selected_version": ("Version", True),
        "applied_version": ("Version", True),
    },
    "managed-call": {"input": ("T", True), "result": ("R", True), "child_id": ("ChildId", True)},
    "input-only": {"signal": ("DeclaredSignal", True), "fields": ("DeclaredFields", True)},
}
KIND_FIELDS = {
    "agent": {"request": "T", "result": "R", "progress": "P"},
    "human": {"subject": "T", "candidate": "Choice", "principal": "PrincipalId", "selected_version": "Version"},
    "enhanced": {"subject": "T", "candidate": "Choice", "principal": "PrincipalId", "selected_version": "Version"},
    "gatekeeper": {"subject": "T", "candidate": "Choice", "principal": "PrincipalId", "selected_version": "Version"},
    "machine": {"input": "T", "result": "R", "child_id": "ChildId"},
    "free_input": {"signal": "DeclaredSignal", "fields": "DeclaredFields"},
    "service": {"request": "T", "result": "R", "counter": "Counter"},
}
KIND_BINDINGS = {
    "agent": {"host_provider"}, "human": {"human_principal"},
    "enhanced": {"human_principal", "policy_authorized_agent"},
    "gatekeeper": {"setting_resolved_principal"},
    "machine": {"compatible_child_machine"}, "free_input": {"human_input_endpoint"},
    "service": {"host_provider"},
}
KIND_POLICIES = {
    "agent": {"timeout", "retry", "declared_progress"},
    "human": {"admissibility", "human_priority_before_commit", "kind_specific_gate"},
    "enhanced": {"admissibility", "human_priority_before_commit", "kind_specific_gate"},
    "gatekeeper": {"admissibility", "human_priority_before_commit", "kind_specific_gate"},
    "machine": {"typed_input_result_compatibility", "declared_child_control"},
    "free_input": {"active_state_admissibility", "declared_signal_fields"},
    "service": {"narrow_call"},
}
PROFILE_POLICIES = {
    "call": {"allowed": {"timeout", "retry", "declared_progress", "narrow_call"}, "forbidden": {"implicit_compensation"}},
    "decision": {"allowed": {"admissibility", "human_priority_before_commit", "kind_specific_gate"}, "required": {"human_priority_before_commit"}, "forbidden": set()},
    "managed-call": {"allowed": {"typed_input_result_compatibility", "declared_child_control"}, "forbidden": {"implicit_timeout_on_pause"}},
    "input-only": {"allowed": {"active_state_admissibility", "declared_signal_fields"}, "forbidden": {"deferred_delivery", "synthetic_request"}},
}
PROFILE_BINDINGS = {
    "call": ({"host_provider"}, "host"),
    "decision": ({"human_principal", "policy_authorized_agent", "setting_resolved_principal"}, "authenticated_principal"),
    "managed-call": ({"compatible_child_machine"}, "host_registry"),
    "input-only": ({"human_input_endpoint"}, "authenticated_principal"),
}
RIGHTS_SOURCE = {"call": "host_permissions", "decision": "authenticated_principal_and_policy", "managed-call": "declared_child_controls", "input-only": "declared_signal_and_state"}
CORRELATION_KEYS = {
    "call": {"instance_id", "party_id", "request_id"},
    "decision": {"opening_id", "subject_id", "principal_id", "version"},
    "managed-call": {"parent_instance_id", "request_id", "child_id"},
    "input-only": {"instance_id", "active_state", "signal_name"},
}
LIFECYCLE_STATES = {
    "call": ({"prepared", "sent", "accepted", "applied", "withdrawn", "failed", "expired"}, {"applied", "withdrawn", "failed", "expired"}, "prepared"),
    "decision": ({"opened", "candidates", "selected", "committed", "withdrawn", "superseded"}, {"committed", "withdrawn", "superseded"}, "opened"),
    "managed-call": ({"created", "running", "paused", "completed", "failed", "cancelled"}, {"completed", "failed", "cancelled"}, "created"),
    "input-only": ({"received", "accepted", "rejected"}, {"accepted", "rejected"}, "received"),
}
LIFECYCLE_EDGES = {
    "call": {("prepared", "sent"), ("sent", "accepted"), ("accepted", "applied"), ("prepared", "withdrawn"), ("sent", "withdrawn"), ("accepted", "failed"), ("accepted", "expired")},
    "decision": {("opened", "candidates"), ("candidates", "selected"), ("candidates", "superseded"), ("selected", "committed"), ("selected", "superseded"), ("opened", "withdrawn"), ("candidates", "withdrawn"), ("selected", "withdrawn")},
    "managed-call": {("created", "running"), ("running", "paused"), ("running", "completed"), ("running", "failed"), ("running", "cancelled"), ("paused", "running"), ("paused", "completed"), ("paused", "failed"), ("paused", "cancelled")},
    "input-only": {("received", "accepted"), ("received", "rejected")},
}
OPERATIONS = {
    "call": {"withdrawal": "stop_waiting", "cancel": "request_stop", "compensation": "domain_operation"},
    "decision": {"withdrawal": "close_uncommitted_opening", "cancel": "request_execution_stop", "compensation": "separate_domain_operation"},
    "managed-call": {"withdrawal": "withdraw_parent_wait", "cancel": "send_child_cancel", "compensation": "separate_domain_operation"},
    "input-only": {"withdrawal": "withdraw_unaccepted_input", "cancel": "not_applicable_without_execution", "compensation": "not_applicable_without_domain_effect"},
}
RUNTIME_STATUS = {
    "agent": "implemented_existing", "human": "gate_signals_only", "enhanced": "gate_constraints_existing",
    "gatekeeper": "setting_resolution_existing", "machine": "nested_runner_existing",
    "free_input": "signal_input_existing", "service": "not_implemented",
}
SERVICE_FORBIDDEN = {"signals", "progress", "streaming", "subscriptions", "profile_override"}
CODEC_SCOPES = {"typed_values", "encoding", "canonicalization", "requests", "responses", "signals", "external_functions"}
CODEC_FIELDS = {"planned_reference", "status", "covers", "single_source", "duplicate_codec_here", "requires_json", "requires_network", "requires_durable_inbox_for_each_binding", "event_envelope_and_receipts", "event_protocol_planned_reference"}
PROFILE_KEYS = {
    "call": {"contract", "lifecycle", "correlation", "binding", "rights", "policy", "operations", "recovery"},
    "decision": {"contract", "lifecycle", "correlation", "binding", "rights", "policy", "commit", "operations", "recovery"},
    "managed-call": {"contract", "lifecycle", "correlation", "binding", "rights", "policy", "operations", "recovery"},
    "input-only": {"contract", "lifecycle", "correlation", "binding", "rights", "policy", "admissibility", "operations", "recovery"},
}
KIND_KEYS = {kind: {"profile", "types", "bindings", "policy", "rights_source", "runtime_status"} for kind in PROFILE_FOR_KIND}
KIND_KEYS["service"] |= {"required_types", "forbidden_features"}


def validate_graph(name, lifecycle):
    errors = []
    states, terminal, initial = LIFECYCLE_STATES[name]
    got_states = lifecycle.get("states", [])
    got_terminal = lifecycle.get("terminal", [])
    edges = lifecycle.get("transitions", [])
    if set(got_states) != states or len(got_states) != len(states):
        errors.append(f"profiles.{name}.lifecycle:state_set_incomplete_or_invalid")
    if set(got_terminal) != terminal or lifecycle.get("initial") != initial:
        errors.append(f"profiles.{name}.lifecycle:initial_or_terminal_set_invalid")
    if not edges:
        errors.append(f"profiles.{name}.lifecycle:transition_graph_empty")
    parsed = set()
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != {"from", "to"}:
            errors.append(f"profiles.{name}.lifecycle:malformed_transition")
            continue
        source, target = edge["from"], edge["to"]
        if source not in states or target not in states:
            errors.append(f"profiles.{name}.lifecycle:transition_endpoint_unknown")
        if source in terminal:
            errors.append(f"profiles.{name}.lifecycle:terminal_state_has_outgoing_transition")
        parsed.add((source, target))
    if parsed != LIFECYCLE_EDGES[name]:
        errors.append(f"profiles.{name}.lifecycle:transition_graph_incomplete_or_invalid")
    reachable = {initial}
    changed = True
    while changed:
        changed = False
        for source, target in parsed:
            if source in reachable and target not in reachable:
                reachable.add(target)
                changed = True
    if reachable != states:
        errors.append(f"profiles.{name}.lifecycle:unreachable_state")
    return errors


def validate(model):
    errors = []
    allowed_top_level = {"status", "planned_alula_release", "profiles", "kinds", "shared_integration_codec", "provenance"}
    if set(model) != allowed_top_level:
        errors.append("top_level_fields_invalid")
    if model.get("status") != STATUS:
        errors.append("status:must_remain_project_model_not_runtime")
    if model.get("planned_alula_release") != "0.29.0-alpha.1":
        errors.append("planned_alula_release:must_not_be_presented_as_current_runtime")
    profiles, kinds = model.get("profiles", {}), model.get("kinds", {})
    if set(profiles) != set(PROFILE_FIELDS):
        errors.append("profile_registry:must_define_exact_profiles")
    if set(kinds) != set(PROFILE_FOR_KIND):
        errors.append("kind_registry:must_cover_exact_kinds")
    for name, field_spec in PROFILE_FIELDS.items():
        profile = profiles.get(name, {})
        if set(profile) != PROFILE_KEYS[name]:
            errors.append(f"profiles.{name}:profile_fields_invalid")
        contract = profile.get("contract", {})
        if set(contract) != set(field_spec):
            errors.append(f"profiles.{name}.contract:field_set_invalid")
        for field, (type_name, required) in field_spec.items():
            declaration = contract.get(field, {})
            if declaration.get("type") != type_name or declaration.get("required") is not required:
                errors.append(f"profiles.{name}.contract.{field}:type_or_required_invalid")
        if name == "call" and contract.get("progress", {}).get("terminal") is not False:
            errors.append("profiles.call.contract.progress:must_be_nonterminal")
        errors.extend(validate_graph(name, profile.get("lifecycle", {})))
        correlation = profile.get("correlation", {})
        if correlation.get("is_authority") is not False:
            errors.append(f"profiles.{name}.correlation:is_not_authority")
        keys = correlation.get("keys", [])
        if not isinstance(keys, list) or len(keys) != len(CORRELATION_KEYS[name]) or set(keys) != CORRELATION_KEYS[name]:
            errors.append(f"profiles.{name}.correlation:required_keys_invalid")
        allowed_bindings, identity_source = PROFILE_BINDINGS[name]
        binding = profile.get("binding", {})
        rights = profile.get("rights", {})
        if set(binding.get("allowed", [])) != allowed_bindings or binding.get("identity_source") != identity_source:
            errors.append(f"profiles.{name}.binding:binding_or_identity_allowlist_invalid")
        if rights.get("authority_source") != RIGHTS_SOURCE[name] or rights.get("binding_name_grants_authority") is not False:
            errors.append(f"profiles.{name}.rights:authority_must_not_come_from_binding_name")
        policy_spec = PROFILE_POLICIES[name]
        policy = profile.get("policy", {})
        for key, expected in policy_spec.items():
            if set(policy.get(key, [])) != expected:
                errors.append(f"profiles.{name}.policy.{key}:fixed_policy_set_invalid")
        if set(policy) != set(policy_spec):
            errors.append(f"profiles.{name}.policy:unknown_policy_fields")
        if profile.get("operations") != OPERATIONS[name]:
            errors.append(f"profiles.{name}.operations:withdrawal_cancel_compensation_invalid")

    decision = profiles.get("decision", {})
    contract = decision.get("contract", {})
    if contract.get("subject", {}).get("required") is not True:
        errors.append("profiles.decision.contract.subject:must_be_required")
    commit = decision.get("commit", {})
    if commit.get("requires_version_match") is not True or commit.get("stale_selected_version") != "reject" or commit.get("atomic") is not True:
        errors.append("profiles.decision.commit:stale_selection_must_be_rejected_atomically")
    if commit.get("arbitration") != "human_priority_before_commit":
        errors.append("profiles.decision.commit:human_priority_required")
    if "human_priority_before_commit" not in decision.get("policy", {}).get("required", []):
        errors.append("profiles.decision.policy:human_priority_must_be_required")
    corr = decision.get("correlation", {})
    if corr.get("one_opening_per_logical_decision") is not True or corr.get("ui_sessions_share_principal") is not True:
        errors.append("profiles.decision.correlation:one_opening_per_principal_required")
    if "committed" in decision.get("lifecycle", {}).get("supersede_from", []):
        errors.append("profiles.decision.lifecycle:committed_must_not_be_supersedable")
    if set(decision.get("lifecycle", {}).get("supersede_from", [])) != {"candidates", "selected"}:
        errors.append("profiles.decision.lifecycle:supersede_source_set_invalid")
    recovery = decision.get("recovery", {})
    if any(recovery.get(field) is not True for field in ("opening_durable", "candidates_durable", "selection_durable", "version_durable")):
        errors.append("profiles.decision.recovery:opening_candidates_selection_and_version_must_be_durable")

    managed = profiles.get("managed-call", {}).get("recovery", {})
    if managed.get("child_identity_preserved") is not True or managed.get("result_durable") is not True or managed.get("restart_creates_new_child") is not False:
        errors.append("profiles.managed-call.recovery:same_child_and_result_required")
    if managed.get("pause_is_timeout") is not False:
        errors.append("profiles.managed-call.recovery:pause_must_be_false")
    input_only = profiles.get("input-only", {})
    admissibility = input_only.get("admissibility", {})
    if admissibility.get("requires_active_state") is not True or admissibility.get("late_input") != "reject" or admissibility.get("deferred_delivery") is not False:
        errors.append("profiles.input-only.admissibility:active_state_and_late_rejection_required")
    if input_only.get("recovery", {}).get("rejected_input_replayed_later") is not False:
        errors.append("profiles.input-only.recovery:rejected_input_must_not_be_replayed")
    if input_only.get("correlation", {}).get("request_id_required") is not False:
        errors.append("profiles.input-only.correlation:request_id_must_be_optional")
    call_correlation = profiles.get("call", {}).get("correlation", {})
    if call_correlation.get("is_authority") is not False:
        errors.append("profiles.call.correlation:correlation_must_not_grant_authority")
    call_recovery = profiles.get("call", {}).get("recovery", {})
    if call_recovery.get("retry_is_new_request") is not True or call_recovery.get("effect_idempotency_required") is not True:
        errors.append("profiles.call.recovery:retry_and_effect_idempotency_must_be_explicit")

    for kind, expected_profile in PROFILE_FOR_KIND.items():
        entry = kinds.get(kind, {})
        if set(entry) != KIND_KEYS[kind]:
            errors.append(f"kinds.{kind}:kind_fields_invalid")
        if entry.get("profile") != expected_profile:
            errors.append(f"kinds.{kind}.profile:mapping_invalid")
            continue
        if entry.get("types") != KIND_FIELDS[kind]:
            errors.append(f"kinds.{kind}.types:exact_typed_contract_invalid")
        if set(entry.get("bindings", [])) != KIND_BINDINGS[kind]:
            errors.append(f"kinds.{kind}.bindings:kind_specific_binding_invalid")
        if set(entry.get("policy", [])) != KIND_POLICIES[kind]:
            errors.append(f"kinds.{kind}.policy:kind_specific_policy_invalid")
        if entry.get("rights_source") != RIGHTS_SOURCE[expected_profile]:
            errors.append(f"kinds.{kind}.rights_source:authority_source_invalid")
        if entry.get("runtime_status") != RUNTIME_STATUS[kind]:
            errors.append(f"kinds.{kind}.runtime_status:runtime_boundary_invalid")
    service = kinds.get("service", {})
    if set(service.get("required_types", [])) != {"result", "counter"}:
        errors.append("kinds.service.required_types:result_and_counter_required")
    if set(service.get("forbidden_features", [])) != SERVICE_FORBIDDEN:
        errors.append("kinds.service.forbidden_features:fixed_set_invalid")
    if service.get("enabled_features", []):
        errors.append("kinds.service.enabled_features:must_be_empty")
    if set(service.get("types", {})) & SERVICE_FORBIDDEN:
        errors.append("kinds.service.types:forbidden_field_enabled")
    if "declared_progress" in service.get("policy", []):
        errors.append("kinds.service.policy:progress_policy_forbidden")

    codec = model.get("shared_integration_codec", {})
    if set(codec) != CODEC_FIELDS or codec.get("planned_reference") != "../spec/alula-value-codec.md" or codec.get("event_protocol_planned_reference") != "../spec/alula-event-protocol.md" or codec.get("status") != "planned_dependency_not_yet_published":
        errors.append("shared_integration_codec:coordination_fields_invalid")
    if (ROOT / "spec/alula-value-codec.md").exists() or (ROOT / "spec/alula-event-protocol.md").exists():
        errors.append("shared_integration_codec:planned_paths_exist_update_dependency_status_before_integration")
    if set(codec.get("covers", [])) != CODEC_SCOPES or codec.get("single_source") is not True or codec.get("duplicate_codec_here") is not False:
        errors.append("shared_integration_codec:single_common_source_scope_invalid")
    if any(codec.get(field) is not False for field in ("requires_json", "requires_network", "requires_durable_inbox_for_each_binding")):
        errors.append("shared_integration_codec:transport_or_inbox_must_not_be_required")
    if codec.get("event_envelope_and_receipts") != "specialized_event_protocol_not_generic_codec_lifecycle":
        errors.append("shared_integration_codec:event_protocol_boundary_invalid")
    provenance = model.get("provenance", {})
    if provenance.get("service_design") != "e7769b0599bd6bef85cf070be6ca2e043af123f9" or "not imported" not in provenance.get("service_status", ""):
        errors.append("provenance:local_service_must_remain_unimported")
    return errors


def reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_model():
    return json.loads(MODEL.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)


def runtime_smoke_check():
    """A text smoke-check only; semantic preservation is proved by the empty runtime diff."""
    source = (ROOT / "src/machine_table/model.nv").read_text(encoding="utf-8")
    return not ("export type PartyKind enum" not in source or "ServiceParty" in source)


def runtime_diff_is_empty():
    return subprocess.run(["git", "diff", "--quiet", "origin/main...HEAD", "--", "src"], cwd=ROOT, check=False).returncode == 0


def main():
    failures = 0
    checks = 0

    def check(label, passed, why=""):
        nonlocal failures, checks
        checks += 1
        if passed:
            print(f"PASS {label}")
        else:
            failures += 1
            print(f"FAIL {label}: {why}")

    try:
        model = load_model()
    except (ValueError, json.JSONDecodeError) as error:
        print(f"FAIL model JSON: {error}")
        return 1
    positive_errors = validate(model)
    check("structured positive model", not positive_errors, positive_errors)

    def reverse(label, mutate, expected):
        mutant = copy.deepcopy(model)
        mutate(mutant)
        errors = validate(mutant)
        check(f"reverse {label}", any(expected in error for error in errors), f"expected {expected}; got {errors}")

    reverse("principal type Id is not PrincipalId", lambda m: m["profiles"]["decision"]["contract"]["principal"].update(type="Id"), "type_or_required_invalid")
    reverse("human cannot bind an agent", lambda m: m["kinds"]["human"].update(bindings=["policy_authorized_agent"]), "kind_specific_binding_invalid")
    reverse("gatekeeper cannot bind a human directly", lambda m: m["kinds"]["gatekeeper"].update(bindings=["human_principal"]), "kind_specific_binding_invalid")
    reverse("service progress field cannot be hidden", lambda m: m["kinds"]["service"]["types"].update(progress="P"), "exact_typed_contract_invalid")
    reverse("service progress policy cannot be hidden", lambda m: m["kinds"]["service"].update(policy=["narrow_call", "declared_progress"]), "kind_specific_policy_invalid")
    reverse("service progress field and policy cannot jointly bypass prohibition", lambda m: (m["kinds"]["service"]["types"].update(progress="P"), m["kinds"]["service"].update(policy=["narrow_call", "declared_progress"])), "exact_typed_contract_invalid")
    reverse("service counter must remain required", lambda m: m["kinds"]["service"].update(required_types=["result"]), "result_and_counter_required")
    reverse("decision recovery cannot be omitted", lambda m: m["profiles"]["decision"].pop("recovery"), "opening_candidates_selection_and_version_must_be_durable")
    reverse("decision subject must be required", lambda m: m["profiles"]["decision"]["contract"]["subject"].update(required=False), "subject:must_be_required")
    reverse("decision graph cannot be empty", lambda m: m["profiles"]["decision"]["lifecycle"].update(transitions=[]), "transition_graph_empty")
    reverse("transition endpoint must exist", lambda m: m["profiles"]["decision"]["lifecycle"]["transitions"][0].update(to="missing"), "transition_endpoint_unknown")
    reverse("compatibility duplicate cannot override constraints", lambda m: (m["kinds"]["human"].update(bindings=["policy_authorized_agent"]), m.update(compatibility={"kind_bindings_must_be_subset_of_profile_bindings": False})), "top_level_fields_invalid")
    reverse("human priority remains required", lambda m: (m["profiles"]["decision"]["policy"].update(required=[]), m["kinds"]["human"].update(policy=["admissibility", "kind_specific_gate"])), "kind_specific_policy_invalid")
    reverse("managed pause is not timeout", lambda m: m["profiles"]["managed-call"]["recovery"].update(pause_is_timeout=True), "pause_must_be_false")
    reverse("rejected input is not replayed", lambda m: m["profiles"]["input-only"]["recovery"].update(rejected_input_replayed_later=True), "rejected_input_must_not_be_replayed")
    reverse("call correlation is not authority", lambda m: m["profiles"]["call"]["correlation"].update(is_authority=True), "correlation:is_not_authority")
    reverse("call correlation retains request id", lambda m: m["profiles"]["call"]["correlation"].update(keys=["instance_id", "party_id"]), "correlation:required_keys_invalid")
    reverse("decision correlation retains opening and version", lambda m: m["profiles"]["decision"]["correlation"].update(keys=["principal_id"]), "correlation:required_keys_invalid")
    reverse("managed correlation retains child id", lambda m: m["profiles"]["managed-call"]["correlation"].update(keys=["parent_instance_id", "request_id"]), "correlation:required_keys_invalid")
    reverse("input correlation retains active context", lambda m: m["profiles"]["input-only"]["correlation"].update(keys=["instance_id"]), "correlation:required_keys_invalid")
    reverse("progress remains nonterminal", lambda m: m["profiles"]["call"]["contract"]["progress"].update(terminal=True), "progress:must_be_nonterminal")
    reverse("top-level runtime status is fixed", lambda m: m.update(status="implemented-runtime"), "status:must_remain_project_model_not_runtime")
    reverse("decision commit checks selected version", lambda m: m["profiles"]["decision"]["commit"].update(requires_version_match=False, stale_selected_version="accept"), "stale_selection_must_be_rejected_atomically")
    reverse("input-only requires active state", lambda m: m["profiles"]["input-only"]["admissibility"].update(requires_active_state=False, late_input="accept", deferred_delivery=True), "active_state_and_late_rejection_required")
    reverse("service streaming forbidden", lambda m: m["kinds"]["service"].update(enabled_features=["streaming"]), "enabled_features:must_be_empty")
    reverse("binding name grants no authority", lambda m: m["profiles"]["decision"]["rights"].update(binding_name_grants_authority=True), "authority_must_not_come_from_binding_name")
    reverse("committed cannot be superseded", lambda m: m["profiles"]["decision"]["lifecycle"].update(supersede_from=["candidates", "selected", "committed"]), "committed_must_not_be_supersedable")
    reverse("withdrawal differs from cancel", lambda m: m["profiles"]["decision"]["operations"].update(withdrawal="request_execution_stop"), "withdrawal_cancel_compensation_invalid")
    reverse("withdrawal differs from compensation", lambda m: m["profiles"]["decision"]["operations"].update(withdrawal="separate_domain_operation"), "withdrawal_cancel_compensation_invalid")
    reverse("cancel differs from compensation", lambda m: m["profiles"]["decision"]["operations"].update(cancel="separate_domain_operation"), "withdrawal_cancel_compensation_invalid")
    reverse("service cannot be marked implemented", lambda m: m["kinds"]["service"].update(runtime_status="implemented_existing"), "runtime_boundary_invalid")
    try:
        duplicate_text = MODEL.read_text(encoding="utf-8").replace('"status": "project-model-not-runtime",', '"provenance": {},\n  "status": "project-model-not-runtime",', 1)
        json.loads(duplicate_text, object_pairs_hook=reject_duplicate_pairs)
        check("duplicate JSON keys rejected", False, "duplicate key accepted")
    except ValueError as error:
        check("duplicate JSON keys rejected", "duplicate JSON key: provenance" in str(error))
    reverse("extra provenance record rejected", lambda m: m.update(provenance_duplicate={}), "top_level_fields_invalid")
    reverse("codec does not require transport", lambda m: m["shared_integration_codec"].update(requires_network=True), "transport_or_inbox_must_not_be_required")

    check("runtime smoke-check (not semantic proof)", runtime_smoke_check())
    check("runtime diff empty against origin/main", runtime_diff_is_empty())
    print(f"{checks - failures} of {checks} checks passed; {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
