"""Executable probes for the in-memory event protocol model (not the runtime)."""

from __future__ import annotations

import copy
import unittest

from event_protocol_model import Instance, TERMINAL, transitions_from_spec


class EventProtocolModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = Instance(
            "run-1", "contract-a", "artifact-a",
            gates={"gate-1": {"closed": False, "version": 0}},
            signal_specs={("party.signal", "reviewer", "approve"): {"ok": bool}},
        )

    def event(self, event_id: str, *, data: dict | None = None, **extra) -> dict:
        return {
            "event_id": event_id,
            "instance_id": "run-1",
            "contract_id": "contract-a",
            "kind": "party.signal",
            "party": "reviewer",
            "signal": "approve",
            "data": {"ok": True} if data is None else data,
            **extra,
        }

    def key(self, event_id: str, producer: str = "producer-a"):
        return "tenant-a", "run-1", producer, event_id

    def submit(self, event_id: str, *, producer: str = "producer-a", actor: str = "agent", **kwargs):
        return self.machine.submit("tenant-a", producer, self.event(event_id, **kwargs), actor=actor)

    def test_contract_status_table_is_model_source(self):
        self.assertEqual(
            transitions_from_spec(),
            {
                ("none", "submit", "queued"), ("queued", "admit", "accepted"),
                ("queued", "reject", "rejected"), ("queued", "cancel", "cancelled"),
                ("accepted", "apply", "applied"), ("accepted", "replace", "superseded"),
                ("accepted", "cancel", "cancelled"),
            },
        )

    def test_instance_pins_contract_and_artifact(self):
        self.machine.assert_pinned("run-1", "contract-a", "artifact-a")
        with self.assertRaisesRegex(ValueError, "pinned instance"):
            self.machine.assert_pinned("run-1", "contract-a", "artifact-b")

    def test_valid_qualified_typed_signal_and_commit(self):
        receipt = self.submit("e1", gate_id="gate-1")
        self.assertEqual(receipt.status, "queued")
        key = self.key("e1")
        self.machine.admit(key, decision="yes")
        gate_version = self.machine.gates["gate-1"]["version"]
        applied = self.machine.apply(key, expected_inbox_version=1, expected_gate_version=gate_version, gate_id="gate-1")
        self.assertEqual(applied.status, "applied")
        self.assertEqual(self.machine.state[key], {"ok": True})

    def test_wrong_type_unknown_qualification_and_extra_fields_reject_before_queue(self):
        with self.assertRaisesRegex(ValueError, "typed data"):
            self.submit("wrong-type", data={"ok": "yes"})
        wrong = self.event("wrong-party")
        wrong["party"] = "other"
        with self.assertRaisesRegex(ValueError, "unknown qualified signal"):
            self.machine.submit("tenant-a", "producer-a", wrong)
        extra = self.event("extra", unexpected=1)
        with self.assertRaisesRegex(ValueError, "unknown envelope"):
            self.machine.submit("tenant-a", "producer-a", extra)
        self.assertEqual(self.machine.receipts, {})

    def test_dedup_returns_current_receipt_and_payload_conflict_is_rejected(self):
        first = self.submit("e1")
        key = self.key("e1")
        self.machine.admit(key)
        repeated = self.submit("e1")
        self.assertIsNot(first, repeated)
        self.assertEqual(first.key, repeated.key)
        self.assertEqual(repeated.status, "accepted")
        with self.assertRaisesRegex(ValueError, "event_id_conflict"):
            self.machine.submit("tenant-a", "producer-a", self.event("e1", data={"ok": False}))

    def test_dedup_fingerprint_ignores_json_object_member_order(self):
        original = self.event("e1")
        first = self.machine.submit("tenant-a", "producer-a", original)
        reordered = dict(reversed(list(original.items())))
        repeated = self.machine.submit("tenant-a", "producer-a", reordered)
        self.assertEqual(first.key, repeated.key)
        self.assertIsNot(first, repeated)

    def test_trusted_producer_scopes_dedup(self):
        first = self.submit("e1")
        other = self.machine.submit("tenant-a", "producer-b", self.event("e1"))
        self.assertIsNot(first, other)
        first_key = self.key("e1", "producer-a")
        other_key = self.key("e1", "producer-b")
        self.assertEqual(set(self.machine.pending), {first_key, other_key})
        self.machine.admit(first_key)
        self.machine.admit(other_key)
        self.machine.apply(first_key, expected_inbox_version=2)
        self.machine.apply(other_key, expected_inbox_version=2)
        self.assertEqual(self.machine._receipt(first_key).status, "applied")
        self.assertEqual(self.machine._receipt(other_key).status, "applied")
        with self.assertRaisesRegex(ValueError, "trusted tenant"):
            self.machine.submit("tenant-a", "", self.event("e2"))

    def test_human_before_agent_admission_blocks_late_agent(self):
        human = self.submit("human", actor="human", gate_id="gate-1")
        human_key = self.key("human")
        self.machine.admit(human_key, decision="continue")
        self.submit("late-agent", gate_id="gate-1")
        result = self.machine.admit(self.key("late-agent"), decision="agent")
        self.assertEqual(result.status, "rejected")
        self.assertEqual(self.machine.selected["gate-1"], human_key)

    def test_human_replaces_accepted_agent_before_commit(self):
        self.submit("agent", gate_id="gate-1")
        agent_key = self.key("agent")
        self.machine.admit(agent_key, decision="agent")
        self.submit("human", actor="human", gate_id="gate-1")
        human_key = self.key("human")
        self.machine.human_priority("gate-1", human_key)
        self.assertEqual(self.machine._receipt(agent_key).status, "superseded")
        with self.assertRaisesRegex(ValueError, "only accepted"):
            self.machine.apply(agent_key, gate_id="gate-1", expected_inbox_version=2, expected_gate_version=1)
        gate_version = self.machine.gates["gate-1"]["version"]
        self.machine.apply(human_key, gate_id="gate-1", expected_inbox_version=2, expected_gate_version=gate_version)
        self.assertEqual(self.machine._receipt(human_key).status, "applied")

    def test_queued_human_decision_blocks_agent_commit_even_with_current_versions(self):
        self.submit("agent", gate_id="gate-1")
        agent_key = self.key("agent")
        self.machine.admit(agent_key, decision="agent")
        self.submit("human", actor="human", gate_id="gate-1")
        human_key = self.key("human")
        current_gate_version = self.machine.gates["gate-1"]["version"]
        with self.assertRaisesRegex(ValueError, "queued human gate decision"):
            self.machine.apply(agent_key, expected_inbox_version=self.machine.inbox_version,
                               expected_gate_version=current_gate_version, gate_id="gate-1")
        self.machine.human_priority("gate-1", human_key)
        self.assertEqual(self.machine._receipt(agent_key).status, "superseded")
        self.machine.apply(human_key, expected_inbox_version=self.machine.inbox_version,
                           expected_gate_version=self.machine.gates["gate-1"]["version"], gate_id="gate-1")
        self.assertEqual(self.machine._receipt(human_key).status, "applied")

    def test_gate_link_is_mandatory_at_apply(self):
        self.submit("e1", gate_id="gate-1")
        key = self.key("e1")
        self.machine.admit(key)
        gate_version = self.machine.gates["gate-1"]["version"]
        with self.assertRaisesRegex(ValueError, "requires its saved gate link"):
            self.machine.apply(key, expected_inbox_version=1, expected_gate_version=gate_version)
        self.assertEqual(self.machine._receipt(key).status, "accepted")
        self.assertFalse(self.machine.gates["gate-1"]["closed"])
        self.machine.apply(key, expected_inbox_version=1, expected_gate_version=gate_version, gate_id="gate-1")
        self.assertTrue(self.machine.gates["gate-1"]["closed"])

    def test_wrong_gate_arguments_are_checked_before_mutating_any_operation(self):
        self.machine.gates["open-other"] = {"closed": False, "version": 4}
        self.machine.gates["closed-other"] = {"closed": True, "version": 7}
        self.submit("human", actor="human", gate_id="gate-1")
        key = self.key("human")
        initial_gates = copy.deepcopy(self.machine.gates)
        initial_selection = dict(self.machine.selected)

        for wrong_gate in ("closed-other", "open-other", "missing-other"):
            with self.assertRaisesRegex(ValueError, "gate link mismatch"):
                self.machine.admit(key, gate_id=wrong_gate)
            with self.assertRaisesRegex(ValueError, "gate link mismatch"):
                self.machine.human_priority(wrong_gate, key)
            self.assertEqual(self.machine._receipt(key).status, "queued")
            self.assertIn(key, self.machine.pending)
            self.assertEqual(self.machine.selected, initial_selection)
            self.assertEqual(self.machine.gates, initial_gates)

        with self.assertRaisesRegex(ValueError, "human event gate link mismatch"):
            self.machine.human_priority(None, key)
        self.assertEqual(self.machine._receipt(key).status, "queued")
        self.assertEqual(self.machine.gates, initial_gates)

        self.machine.admit(key)
        gate_version = self.machine.gates["gate-1"]["version"]
        admitted_gates = copy.deepcopy(self.machine.gates)
        committed_state = self.machine.state
        for wrong_gate in ("closed-other", "open-other", "missing-other"):
            with self.assertRaisesRegex(ValueError, "gate link mismatch"):
                self.machine.apply(key, expected_inbox_version=1,
                                   expected_gate_version=gate_version, gate_id=wrong_gate)
            self.assertEqual(self.machine._receipt(key).status, "accepted")
            self.assertIn(key, self.machine.pending)
            self.assertEqual(self.machine.state, committed_state)
            self.assertEqual(self.machine.gates, admitted_gates)
        with self.assertRaisesRegex(ValueError, "requires its saved gate link"):
            self.machine.apply(key, expected_inbox_version=1, expected_gate_version=gate_version)
        self.assertEqual(self.machine._receipt(key).status, "accepted")
        self.assertEqual(self.machine.state, committed_state)

    def test_submit_pending_state_and_returned_values_are_detached_snapshots(self):
        event = self.event("e1")
        returned = self.machine.submit("tenant-a", "producer-a", event)
        key = self.key("e1")
        event["data"]["ok"] = "invalid-after-validation"
        pending_view = self.machine.pending
        pending_view[key]["data"]["ok"] = "mutated-pending-view"
        returned.status = "applied"
        receipt_view = self.machine.receipts
        receipt_view[key].status = "rejected"
        repeated = self.machine.submit("tenant-a", "producer-a", self.event("e1"))
        self.assertEqual(repeated.status, "queued")
        self.machine.admit(key)
        self.machine.apply(key, expected_inbox_version=1)
        state_view = self.machine.state
        state_view[key]["ok"] = "mutated-state-view"
        self.assertEqual(self.machine.state[key], {"ok": True})

    def test_second_human_decision_for_same_opening_is_rejected_without_replacing_first(self):
        self.submit("human-one", actor="human", gate_id="gate-1")
        first_key = self.key("human-one")
        first = self.machine.human_priority("gate-1", first_key)
        self.assertEqual(first.status, "accepted")
        self.submit("human-two", actor="human", gate_id="gate-1")
        second_key = self.key("human-two")
        second = self.machine.human_priority("gate-1", second_key)
        self.assertEqual(second.status, "rejected")
        self.assertEqual(self.machine._receipt(first_key).status, "accepted")
        self.assertEqual(self.machine.selected["gate-1"], first_key)
        self.assertEqual(self.machine.gates["gate-1"]["candidate"], first_key)

    def test_second_human_decision_after_apply_is_rejected(self):
        self.submit("human-one", actor="human", gate_id="gate-1")
        first_key = self.key("human-one")
        self.machine.human_priority("gate-1", first_key)
        gate_version = self.machine.gates["gate-1"]["version"]
        self.machine.apply(first_key, expected_inbox_version=1, expected_gate_version=gate_version, gate_id="gate-1")
        self.submit("human-two", actor="human", gate_id="gate-1")
        second = self.machine.human_priority("gate-1", self.key("human-two"))
        self.assertEqual(second.status, "rejected")
        self.assertEqual(self.machine._receipt(first_key).status, "applied")

    def test_human_after_commit_is_rejected_without_rollback(self):
        self.submit("agent", gate_id="gate-1")
        agent_key = self.key("agent")
        self.machine.admit(agent_key)
        gate_version = self.machine.gates["gate-1"]["version"]
        self.machine.apply(agent_key, gate_id="gate-1", expected_inbox_version=1, expected_gate_version=gate_version)
        self.submit("human", actor="human", gate_id="gate-1")
        human_key = self.key("human")
        result = self.machine.human_priority("gate-1", human_key)
        self.assertEqual(self.machine._receipt(agent_key).status, "applied")
        self.assertEqual(result.status, "rejected")

    def test_inbox_change_invalidates_stale_commit_snapshot(self):
        self.submit("e1")
        self.machine.admit(self.key("e1"))
        snapshot = self.machine.inbox_version
        self.submit("e2")
        with self.assertRaisesRegex(ValueError, "inbox changed"):
            self.machine.apply(self.key("e1"), expected_inbox_version=snapshot)

    def test_admission_and_applied_are_distinct_and_pause_keeps_pending_event(self):
        self.submit("e1")
        key = self.key("e1")
        self.machine.admit(key)
        self.assertEqual(self.machine._receipt(key).status, "accepted")
        self.assertIn(key, self.machine.pending)  # pause/recovery do not erase admission
        self.machine.apply(key, expected_inbox_version=1)
        self.assertEqual(self.machine._receipt(key).status, "applied")

    def test_rejected_queued_and_cancelled_receipts_are_terminal(self):
        self.submit("reject")
        reject_key = self.key("reject")
        self.machine.admit(reject_key, valid=False)
        self.assertEqual(self.machine._receipt(reject_key).status, "rejected")
        self.submit("cancel")
        cancel_key = self.key("cancel")
        self.machine.cancel(cancel_key)
        for key in (reject_key, cancel_key):
            with self.assertRaisesRegex(ValueError, "terminal receipt is immutable"):
                self.machine.cancel(key)
            self.assertIn(self.machine._receipt(key).status, TERMINAL)

    def test_retention_expires_receipt_but_tombstone_blocks_reuse(self):
        self.submit("e1")
        self.machine.admit(self.key("e1"), valid=False)
        self.machine.expire_completed("tenant-a", "producer-a", "e1")
        self.assertEqual(self.machine.status("tenant-a", "producer-a", "e1"), "status_gone")
        with self.assertRaisesRegex(ValueError, "status_gone"):
            self.submit("e1")

    def test_repeated_signal_rejected_after_gate_closed(self):
        self.submit("e1", gate_id="gate-1")
        key = self.key("e1")
        self.machine.admit(key)
        version = self.machine.gates["gate-1"]["version"]
        self.machine.apply(key, expected_inbox_version=1, expected_gate_version=version, gate_id="gate-1")
        self.submit("e2", gate_id="gate-1")
        rejected = self.machine.admit(self.key("e2"))
        self.assertEqual(rejected.status, "rejected")
        self.assertNotIn(self.key("e2"), self.machine.state)


if __name__ == "__main__":
    unittest.main()
