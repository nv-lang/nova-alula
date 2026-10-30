"""Small in-memory executable model for spec/alula-event-protocol.md.

This models receipt/admission/commit rules only. It is not durable storage,
the production codec, an authorization system, or a runtime conformance test.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import math
from pathlib import Path
import re
import struct
from typing import Any


EventKey = tuple[str, str, str, str]  # tenant, instance, trusted producer, event
SPEC = Path(__file__).resolve().parents[1] / "spec" / "alula-event-protocol.md"
TERMINAL = {"applied", "rejected", "superseded", "cancelled"}
ALLOWED_KINDS = {"party.signal", "machine.control", "request.reply", "request.failure"}


def transitions_from_spec(path: Path = SPEC) -> set[tuple[str, str, str]]:
    """Read the normative transition table; don't keep a second transition list."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"<!-- receipt-transitions -->\s*(.*?)\s*<!-- /receipt-transitions -->", text, re.S)
    if not match:
        raise ValueError("receipt transition table markers missing")
    rows = re.findall(r"^\|\s*(none|queued|accepted)\s*\|\s*(submit|admit|reject|cancel|apply|replace)\s*\|\s*(queued|accepted|rejected|cancelled|applied|superseded)\s*\|\s*$", match.group(1), re.M)
    return set(rows)


def _freeze(value: Any) -> Any:
    """Model a typed digest for already-decoded values, not a production codec."""
    if isinstance(value, dict):
        return tuple((key, _freeze(value[key])) for key in sorted(value))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if type(value) is float:
        if math.isnan(value):
            return ("float", "NaN")
        if math.isinf(value):
            return ("float", "+Inf" if value > 0 else "-Inf")
        return ("float", struct.pack(">d", value))
    return (type(value).__name__, value)


TRANSITIONS = transitions_from_spec()


@dataclass
class Receipt:
    event_id: str
    instance_id: str
    key: EventKey
    status: str
    version: int = 0
    seq: int = 0
    code: str | None = None
    replaced_by: str | None = None


@dataclass
class Instance:
    instance_id: str
    contract_id: str
    artifact_id: str
    gates: dict[str, dict[str, Any]] = field(default_factory=dict)
    _state: dict[EventKey, Any] = field(default_factory=dict)
    inbox_version: int = 0
    seq: int = 0
    _receipts: dict[EventKey, Receipt] = field(default_factory=dict)
    fingerprints: dict[EventKey, tuple[Any, ...]] = field(default_factory=dict)
    _pending: dict[EventKey, dict[str, Any]] = field(default_factory=dict)
    actors: dict[EventKey, str] = field(default_factory=dict)
    gate_links: dict[EventKey, str] = field(default_factory=dict)
    selected: dict[str, EventKey] = field(default_factory=dict)
    committed_events: set[EventKey] = field(default_factory=set)
    active: bool = True
    signal_specs: dict[tuple[str, str, str], dict[str, type]] = field(default_factory=dict)
    human_choices: set[str] = field(default_factory=set)
    tombstones: set[EventKey] = field(default_factory=set)

    @property
    def state(self) -> dict[EventKey, Any]:
        return copy.deepcopy(self._state)

    @property
    def receipts(self) -> dict[EventKey, Receipt]:
        return copy.deepcopy(self._receipts)

    @property
    def pending(self) -> dict[EventKey, dict[str, Any]]:
        return copy.deepcopy(self._pending)

    def _key(self, tenant: str, producer_id: str, event_id: str) -> EventKey:
        if not tenant or not producer_id:
            raise ValueError("trusted tenant and producer_id are required")
        return tenant, self.instance_id, producer_id, event_id

    def assert_pinned(self, instance_id: str, contract_id: str, artifact_id: str) -> None:
        """Reject recovery/submit against any identity other than the pinned triple."""
        if (instance_id, contract_id, artifact_id) != (self.instance_id, self.contract_id, self.artifact_id):
            raise ValueError("pinned instance, contract, or artifact mismatch")

    def submit(self, tenant: str, producer_id: str, event: dict[str, Any], *, actor: str = "agent") -> Receipt:
        """Durable-ingress stand-in; actor and producer are trusted context, not payload."""
        snapshot = copy.deepcopy(event)
        required = {"event_id", "instance_id", "contract_id", "kind", "data"}
        if set(snapshot) - (required | {"party", "signal", "gate_id", "subject_id", "request_id", "pause_id"}):
            raise ValueError("unknown envelope field")
        if not required <= snapshot.keys() or not isinstance(snapshot["data"], dict):
            raise ValueError("event requires all envelope fields and object data")
        if snapshot["kind"] not in ALLOWED_KINDS:
            raise ValueError("unknown kind")
        if snapshot["instance_id"] != self.instance_id or snapshot["contract_id"] != self.contract_id:
            raise ValueError("pinned instance or contract mismatch")
        if actor not in {"agent", "human"}:
            raise ValueError("unknown trusted actor")
        key = self._key(tenant, producer_id, snapshot["event_id"])
        content = _freeze({k: v for k, v in snapshot.items() if k != "event_id"})
        if key in self._receipts:
            if self.fingerprints[key] != content:
                raise ValueError("event_id_conflict")
            return copy.deepcopy(self._receipts[key])
        if key in self.tombstones:
            raise ValueError("status_gone: event id cannot be reused")
        if snapshot["kind"] == "party.signal":
            if not all(isinstance(snapshot.get(name), str) and snapshot[name] for name in ("party", "signal")):
                raise ValueError("party.signal requires qualified party and signal")
            fields = self.signal_specs.get((snapshot["kind"], snapshot["party"], snapshot["signal"]))
            if fields is None:
                raise ValueError("unknown qualified signal")
            if set(snapshot["data"]) != set(fields) or any(type(snapshot["data"][name]) is not typ for name, typ in fields.items()):
                raise ValueError("typed data does not match the signal schema")
        self.seq += 1
        receipt = Receipt(snapshot["event_id"], self.instance_id, key, "none", seq=self.seq)
        self.transition(receipt, "submit", "queued")
        self._receipts[key] = receipt
        self.fingerprints[key] = content
        self._pending[key] = snapshot
        self.actors[key] = actor
        self.inbox_version += 1
        return copy.deepcopy(receipt)

    def transition(self, receipt: Receipt, operation: str, status: str, *, code: str | None = None, replaced_by: str | None = None) -> None:
        if receipt.status in TERMINAL:
            raise ValueError("terminal receipt is immutable")
        if (receipt.status, operation, status) not in TRANSITIONS:
            raise ValueError(f"transition not allowed: {receipt.status} --{operation}--> {status}")
        receipt.status = status
        receipt.version += 1
        receipt.code = code
        receipt.replaced_by = replaced_by

    def admit(self, key: EventKey, *, valid: bool = True, decision: str | None = None, gate_id: str | None = None) -> Receipt:
        requested_gate_id = gate_id
        receipt = self._receipt(key)
        if receipt.status != "queued":
            raise ValueError("only queued events can be admitted")
        event = self._pending[key]
        saved_gate_id = event.get("gate_id")
        if requested_gate_id is not None and requested_gate_id != saved_gate_id:
            raise ValueError("gate link mismatch")
        if not valid:
            self.transition(receipt, "reject", "rejected", code="invalid_event")
            self._pending.pop(key, None)
            return copy.deepcopy(receipt)
        gate_id = saved_gate_id
        if gate_id is not None:
            gate = self.gates.get(gate_id)
            if gate is None or gate.get("closed"):
                self.transition(receipt, "reject", "rejected", code="gate_closed")
                self._pending.pop(key, None)
                return copy.deepcopy(receipt)
            actor = self.actors[key]
            if actor == "human":
                previous = self.selected.get(gate_id)
                if previous is not None and self.actors[previous] == "human":
                    self.transition(receipt, "reject", "rejected", code="stale_human_decision")
                    self._pending.pop(key, None)
                    return copy.deepcopy(receipt)
                self._replace_selection(gate_id, key)
                self.human_choices.add(gate_id)
            elif gate_id in self.human_choices:
                self.transition(receipt, "reject", "rejected", code="human_priority")
                self._pending.pop(key, None)
                return copy.deepcopy(receipt)
            gate["candidate"] = key
            gate["decision"] = decision
            gate["version"] = gate.get("version", 0) + 1
            self.selected[gate_id] = key
            self.gate_links[key] = gate_id
        self.transition(receipt, "admit", "accepted")
        return copy.deepcopy(receipt)

    def _replace_selection(self, gate_id: str, replacement: EventKey) -> None:
        previous = self.selected.get(gate_id)
        if previous and previous != replacement:
            old = self._receipt(previous)
            if old.status == "accepted":
                self.transition(old, "replace", "superseded", replaced_by=replacement[3])
                self._pending.pop(previous, None)

    def apply(self, key: EventKey, *, expected_inbox_version: int | None = None, expected_gate_version: int | None = None, gate_id: str | None = None) -> Receipt:
        receipt = self._receipt(key)
        if receipt.status != "accepted":
            raise ValueError("only accepted events can apply")
        if expected_inbox_version is None:
            raise ValueError("commit requires an inbox version")
        if expected_inbox_version != self.inbox_version:
            raise ValueError("inbox changed before commit")
        event = self._pending.get(key)
        if event is None:
            raise ValueError("accepted event has no pending record")
        linked_gate = self.gate_links.get(key)
        if linked_gate is not None:
            if gate_id is None:
                raise ValueError("accepted gate event requires its saved gate link")
            if gate_id != linked_gate:
                raise ValueError("gate link mismatch")
            gate = self.gates[linked_gate]
            if expected_gate_version is None:
                raise ValueError("gate commit requires a decision version")
            if expected_gate_version != gate.get("version") or self.selected.get(linked_gate) != key:
                raise ValueError("gate decision changed before commit")
            if any(
                pending_key != key
                and self.actors[pending_key] == "human"
                and pending_event.get("gate_id") == linked_gate
                and self._receipt(pending_key).status == "queued"
                for pending_key, pending_event in self._pending.items()
            ):
                raise ValueError("queued human gate decision must be admitted before commit")
        elif gate_id is not None or expected_gate_version is not None:
            raise ValueError("event has no saved gate link")
        self._state[key] = copy.deepcopy(event["data"])
        self.committed_events.add(key)
        self._pending.pop(key, None)
        if linked_gate is not None:
            self.gates[linked_gate]["closed"] = True
        self.transition(receipt, "apply", "applied")
        return copy.deepcopy(receipt)

    def human_priority(self, gate_id: str, key: EventKey) -> Receipt:
        """Admit a queued human decision and atomically supersede an uncommitted choice."""
        receipt = self._receipt(key)
        if receipt.status != "queued" or self.actors[key] != "human":
            raise ValueError("human priority requires a queued human event")
        saved_gate_id = self._pending[key].get("gate_id")
        if not saved_gate_id or gate_id != saved_gate_id:
            raise ValueError("human event gate link mismatch")
        gate = self.gates.get(saved_gate_id)
        if gate is None:
            raise ValueError("saved gate link is unknown")
        if gate.get("closed"):
            receipt = self._receipt(key)
            self.transition(receipt, "reject", "rejected", code="gate_closed")
            self._pending.pop(key, None)
            return copy.deepcopy(receipt)
        return self.admit(key)

    def cancel(self, key: EventKey) -> Receipt:
        receipt = self._receipt(key)
        self.transition(receipt, "cancel", "cancelled")
        self._pending.pop(key, None)
        return copy.deepcopy(receipt)

    def _receipt(self, key: EventKey) -> Receipt:
        try:
            return self._receipts[key]
        except KeyError:
            raise KeyError(key) from None

    def expire_completed(self, tenant: str, producer_id: str, event_id: str) -> None:
        """Drop receipt data while retaining a non-reusable event-id tombstone."""
        key = self._key(tenant, producer_id, event_id)
        receipt = self._receipts.get(key)
        if receipt is None or receipt.status not in TERMINAL:
            raise ValueError("only terminal receipts may expire")
        self.tombstones.add(key)
        del self._receipts[key]
        del self.fingerprints[key]

    def status(self, tenant: str, producer_id: str, event_id: str) -> Receipt | str:
        key = self._key(tenant, producer_id, event_id)
        if key in self.tombstones:
            return "status_gone"
        if key not in self._receipts:
            return "not_found"
        return copy.deepcopy(self._receipts[key])
