"""Small in-memory executable model for spec/alula-event-protocol.md.

This models receipt/admission/commit rules only. It is not durable storage,
the production codec, an authorization system, or a runtime conformance test.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import re
import struct
from typing import Any


EventKey = tuple[str, str, str, str]  # tenant, instance, trusted producer, event
SPEC = Path(__file__).resolve().parents[1] / "spec" / "alula-event-protocol.md"
PROFILES = SPEC.with_name("alula-interaction-profiles.json")
TERMINAL = {"applied", "rejected", "superseded", "cancelled"}
ALLOWED_KINDS = {"party.signal", "machine.control", "request.reply", "request.failure"}


def transitions_from_spec(path: Path = SPEC) -> set[tuple[str, str, str]]:
    """Read the normative transition table; don't keep a second transition list."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"<!-- receipt-transitions -->\s*(.*?)\s*<!-- /receipt-transitions -->", text, re.S)
    if not match:
        raise ValueError("receipt transition table markers missing")
    rows = []
    for line in match.group(1).splitlines():
        if not line.strip().startswith("|") or re.fullmatch(r"\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|", line.strip()):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if cells == ("from", "operation", "to"):
            continue
        if len(cells) != 3 or not all(cells):
            raise ValueError(f"malformed receipt transition row: {line}")
        rows.append(cells)
    valid = ({"none", "queued", "accepted"}, {"submit", "admit", "reject", "cancel", "apply", "replace"},
             {"queued", "accepted", "rejected", "cancelled", "applied", "superseded"})
    if any(value not in allowed for row in rows for value, allowed in zip(row, valid)):
        raise ValueError("unknown receipt transition value")
    if not rows or len(rows) != len(set(rows)):
        raise ValueError("empty or duplicate receipt transition row")
    return set(rows)


def decision_transitions(path: Path = PROFILES) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    model = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    decision = model["profiles"]["decision"]
    graphs = (("opening", decision["lifecycle"]), ("candidate", decision["candidate"]["lifecycle"]))
    result = []
    for graph_name, graph in graphs:
        states, terminal, edges = graph["states"], graph["terminal"], graph["transitions"]
        if len(states) != len(set(states)) or len(terminal) != len(set(terminal)) or not set(terminal) <= set(states):
                raise ValueError(f"invalid {graph_name} lifecycle states")
        parsed = []
        for edge in edges:
            if (not isinstance(edge, dict) or set(edge) != {"from", "to"}
                    or edge["from"] not in states or edge["to"] not in states or edge["from"] in terminal):
                raise ValueError(f"invalid {graph_name} lifecycle transition")
            parsed.append((edge["from"], edge["to"]))
        if not parsed or len(parsed) != len(set(parsed)):
            raise ValueError(f"empty or duplicate {graph_name} lifecycle transition")
        reachable = {graph["initial"]}
        while True:
            extended = reachable | {target for source, target in parsed if source in reachable}
            if extended == reachable:
                break
            reachable = extended
        if reachable != set(states):
            raise ValueError(f"unreachable {graph_name} lifecycle state")
        result.append(set(parsed))
    return result[0], result[1]


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
OPENING_TRANSITIONS, CANDIDATE_TRANSITIONS = decision_transitions()


def _transition_object(edges, current, target, obj):
    if (current, target) not in edges:
        raise ValueError(f"{obj} transition not allowed: {current} -> {target}")


@dataclass
class Receipt:
    event_id: str
    instance_id: str
    key: EventKey
    status: str
    version: int = 0
    seq: int = 0
    code: str | None = None
    replaced_by: EventKey | None = None
    candidate_id: EventKey | None = None


@dataclass
class Candidate:
    candidate_id: EventKey
    opening_id: str
    event_key: EventKey
    sender: str
    role: str
    decision: Any
    status: str = "proposed"
    selected_version: int | None = None
    supersede_from: tuple[str, ...] = ()
    applied_version: int | None = None


@dataclass
class Opening:
    opening_id: str
    subject: Any = None
    admissibility: Any = None
    status: str = "open"
    candidates: dict[EventKey, Candidate] = field(default_factory=dict)
    selected_candidate_id: EventKey | None = None
    selection_version: int = 0
    applied_version: int | None = None


@dataclass
class Instance:
    instance_id: str
    contract_id: str
    artifact_id: str
    gates: dict[str, Opening | dict[str, Any]] = field(default_factory=dict)
    _state: dict[EventKey, Any] = field(default_factory=dict)
    inbox_version: int = 0
    seq: int = 0
    _receipts: dict[EventKey, Receipt] = field(default_factory=dict)
    fingerprints: dict[EventKey, tuple[Any, ...]] = field(default_factory=dict)
    _pending: dict[EventKey, dict[str, Any]] = field(default_factory=dict)
    actors: dict[EventKey, str] = field(default_factory=dict)
    gate_links: dict[EventKey, str] = field(default_factory=dict)
    committed_events: set[EventKey] = field(default_factory=set)
    active: bool = True
    signal_specs: dict[tuple[str, str, str], dict[str, type]] = field(default_factory=dict)
    human_choices: set[str] = field(default_factory=set)
    tombstones: set[EventKey] = field(default_factory=set)
    outbox_intents: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        for opening_id, value in tuple(self.gates.items()):
            if not isinstance(value, Opening):
                self.gates[opening_id] = Opening(opening_id, status="committed" if value.get("closed") else "open",
                                                  selection_version=value.get("version", 0))

    def _opening(self, opening_id: str) -> Opening:
        opening = self.gates.get(opening_id)
        if not isinstance(opening, Opening):
            raise ValueError("opening is unknown")
        return opening

    @property
    def selected(self) -> dict[str, EventKey]:
        """Read-only projection; each opening remains the sole selection source."""
        return {opening_id: opening.selected_candidate_id for opening_id, opening in self.gates.items()
                if isinstance(opening, Opening) and opening.selected_candidate_id is not None}

    def open_decision(self, opening_id: str, *, subject: Any, admissibility: Any) -> Opening:
        if not opening_id or opening_id in self.gates:
            raise ValueError("opening id must be new and nonempty")
        opening = Opening(opening_id, copy.deepcopy(subject), copy.deepcopy(admissibility))
        self.gates[opening_id] = opening
        return copy.deepcopy(opening)

    @property
    def state(self) -> dict[EventKey, Any]:
        return copy.deepcopy(self._state)

    @property
    def receipts(self) -> dict[EventKey, Receipt]:
        return copy.deepcopy(self._receipts)

    @property
    def pending(self) -> dict[EventKey, dict[str, Any]]:
        return copy.deepcopy(self._pending)

    def snapshot(self) -> dict[str, Any]:
        names = ("gates", "_state", "inbox_version", "seq", "_receipts", "fingerprints", "_pending",
                 "actors", "gate_links", "committed_events", "active", "signal_specs",
                 "human_choices", "tombstones", "outbox_intents")
        return {"format": "event-model-snapshot/1", "instance_id": self.instance_id,
                "contract_id": self.contract_id, "artifact_id": self.artifact_id,
                **{name: copy.deepcopy(getattr(self, name)) for name in names}}

    @classmethod
    def restore(cls, snapshot: dict[str, Any]) -> "Instance":
        required = {"format", "instance_id", "contract_id", "artifact_id", "gates", "_state", "inbox_version",
                    "seq", "_receipts", "fingerprints", "_pending", "actors", "gate_links",
                    "committed_events", "active", "signal_specs", "human_choices", "tombstones", "outbox_intents"}
        if set(snapshot) != required or snapshot["format"] != "event-model-snapshot/1":
            raise ValueError("invalid event model snapshot")
        result = cls(snapshot["instance_id"], snapshot["contract_id"], snapshot["artifact_id"],
                     gates=copy.deepcopy(snapshot["gates"]))
        for name in required - {"format", "instance_id", "contract_id", "artifact_id", "gates"}:
            setattr(result, name, copy.deepcopy(snapshot[name]))
        result.assert_pinned(snapshot["instance_id"], snapshot["contract_id"], snapshot["artifact_id"])
        return result

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
        required = {"event_id", "instance_id", "contract_id", "event_kind", "data"}
        if "event_kind" not in snapshot:
            raise ValueError("event_kind is required")
        if set(snapshot) - (required | {"party", "signal", "gate_id", "subject_id", "request_id", "pause_id"}):
            raise ValueError("unknown envelope field")
        if not required <= snapshot.keys() or not isinstance(snapshot["data"], dict):
            raise ValueError("event requires all envelope fields and object data")
        if snapshot["event_kind"] not in ALLOWED_KINDS:
            raise ValueError("unknown event_kind")
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
        if snapshot["event_kind"] == "party.signal":
            if not all(isinstance(snapshot.get(name), str) and snapshot[name] for name in ("party", "signal")):
                raise ValueError("party.signal requires qualified party and signal")
            fields = self.signal_specs.get((snapshot["event_kind"], snapshot["party"], snapshot["signal"]))
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
        if (receipt.status, "admit", "accepted") not in TRANSITIONS:
            raise ValueError("receipt admission transition is not configured")
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
            if not isinstance(gate, Opening) or gate.status != "open":
                self.transition(receipt, "reject", "rejected", code="gate_closed")
                self._pending.pop(key, None)
                return copy.deepcopy(receipt)
            proposed_subject = event.get("subject_id")
            if gate.subject is not None and proposed_subject != gate.subject:
                self.transition(receipt, "reject", "rejected", code="subject_mismatch")
                self._pending.pop(key, None)
                return copy.deepcopy(receipt)
            actor = self.actors[key]
            previous = self.selected.get(gate_id)
            if previous is not None and self.actors[previous] == actor:
                self.transition(receipt, "reject", "rejected", code=f"duplicate_{actor}_decision")
                self._pending.pop(key, None)
                return copy.deepcopy(receipt)
            if actor == "human":
                self._replace_selection(gate_id, key)
                self.human_choices.add(gate_id)
            elif gate_id in self.human_choices:
                self.transition(receipt, "reject", "rejected", code="human_priority")
                self._pending.pop(key, None)
                return copy.deepcopy(receipt)
            opening = self._opening(gate_id)
            if opening.subject is None:
                opening.subject = copy.deepcopy(proposed_subject)
            candidate = Candidate(key, gate_id, key, key[2], actor,
                                  copy.deepcopy(event["data"] if decision is None else decision))
            opening.selection_version += 1
            _transition_object(CANDIDATE_TRANSITIONS, candidate.status, "selected", "candidate")
            candidate.status = "selected"
            candidate.selected_version = opening.selection_version
            opening.candidates[key] = candidate
            opening.selected_candidate_id = key
            receipt.candidate_id = key
            self.gate_links[key] = gate_id
        self.transition(receipt, "admit", "accepted")
        return copy.deepcopy(receipt)

    def _replace_selection(self, gate_id: str, replacement: EventKey) -> None:
        previous = self._opening(gate_id).selected_candidate_id
        if previous and previous != replacement:
            old = self._receipt(previous)
            if old.status == "accepted":
                candidate = self._opening(gate_id).candidates.get(previous)
                if candidate is not None:
                    _transition_object(CANDIDATE_TRANSITIONS, candidate.status, "superseded", "candidate")
                    candidate.status = "superseded"
                    candidate.supersede_from = ("selected",)
                self.transition(old, "replace", "superseded", replaced_by=replacement)
                self._pending.pop(previous, None)
            self._opening(gate_id).selected_candidate_id = None

    def apply(self, key: EventKey, *, expected_inbox_version: int | None = None, expected_selection_version: int | None = None, gate_id: str | None = None) -> Receipt:
        receipt = self._receipt(key)
        if receipt.status != "accepted":
            raise ValueError("only accepted events can apply")
        if expected_inbox_version is None:
            raise ValueError("commit requires an inbox version")
        if expected_inbox_version != self.inbox_version:
            raise ValueError("inbox changed before commit")
        if (receipt.status, "apply", "applied") not in TRANSITIONS:
            raise ValueError("receipt apply transition is not configured")
        event = self._pending.get(key)
        if event is None:
            raise ValueError("accepted event has no pending record")
        linked_gate = self.gate_links.get(key)
        if linked_gate is not None:
            if gate_id is None:
                raise ValueError("accepted gate event requires its saved gate link")
            if gate_id != linked_gate:
                raise ValueError("gate link mismatch")
            gate = self._opening(linked_gate)
            if expected_selection_version is None:
                raise ValueError("gate commit requires a decision version")
            candidate = gate.candidates.get(key)
            if (candidate is None or expected_selection_version != gate.selection_version
                    or candidate.selected_version != gate.selection_version
                    or gate.selected_candidate_id != key):
                raise ValueError("gate decision changed before commit")
            if any(
                pending_key != key
                and self.actors[pending_key] == "human"
                and pending_event.get("gate_id") == linked_gate
                and self._receipt(pending_key).status == "queued"
                for pending_key, pending_event in self._pending.items()
            ):
                raise ValueError("queued human gate decision must be admitted before commit")
        elif gate_id is not None or expected_selection_version is not None:
            raise ValueError("event has no saved gate link")
        if linked_gate is not None:
            opening = self._opening(linked_gate)
            _transition_object(OPENING_TRANSITIONS, opening.status, "committed", "opening")
            _transition_object(CANDIDATE_TRANSITIONS, opening.candidates[key].status, "applied", "candidate")
        self._state[key] = copy.deepcopy(event["data"])
        self.committed_events.add(key)
        self._pending.pop(key, None)
        self.outbox_intents.append({"event_key": key, "effect": "apply", "status": "pending"})
        if linked_gate is not None:
            opening = self._opening(linked_gate)
            opening.status = "committed"
            opening.applied_version = opening.selection_version
            opening.candidates[key].status = "applied"
            opening.candidates[key].applied_version = opening.selection_version
            for pending_key, pending_event in list(self._pending.items()):
                if pending_key != key and pending_event.get("gate_id") == linked_gate:
                    pending_receipt = self._receipt(pending_key)
                    if pending_receipt.status == "queued":
                        self.transition(pending_receipt, "reject", "rejected", code="opening_committed")
                    self._pending.pop(pending_key, None)
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
        if not isinstance(gate, Opening):
            raise ValueError("saved gate link is unknown")
        if gate.status != "open":
            receipt = self._receipt(key)
            self.transition(receipt, "reject", "rejected", code="gate_closed")
            self._pending.pop(key, None)
            return copy.deepcopy(receipt)
        return self.admit(key)

    def cancel(self, key: EventKey) -> Receipt:
        receipt = self._receipt(key)
        if receipt.status in TERMINAL:
            raise ValueError("terminal receipt is immutable")
        if (receipt.status, "cancel", "cancelled") not in TRANSITIONS:
            raise ValueError("receipt cannot be cancelled in its current state")
        opening_id = self.gate_links.pop(key, None)
        if opening_id is not None:
            opening = self._opening(opening_id)
            if opening.selected_candidate_id == key:
                opening.selected_candidate_id = None
                opening.selection_version += 1
            candidate = opening.candidates.get(key)
            if candidate is not None:
                _transition_object(CANDIDATE_TRANSITIONS, candidate.status, "withdrawn", "candidate")
                candidate.status = "withdrawn"
        self.transition(receipt, "cancel", "cancelled")
        self._pending.pop(key, None)
        return copy.deepcopy(receipt)

    def withdraw_opening(self, opening_id: str) -> Opening:
        opening = self._opening(opening_id)
        if opening.status != "open":
            raise ValueError("only open openings may be withdrawn")
        for candidate in opening.candidates.values():
            receipt = self._receipt(candidate.event_key)
            if receipt.status == "accepted":
                self.transition(receipt, "cancel", "cancelled", code="opening_withdrawn")
            elif receipt.status == "queued":
                self.transition(receipt, "reject", "rejected", code="opening_withdrawn")
            if candidate.status in {"proposed", "selected"}:
                _transition_object(CANDIDATE_TRANSITIONS, candidate.status, "withdrawn", "candidate")
                candidate.status = "withdrawn"
            self._pending.pop(candidate.event_key, None)
            self.gate_links.pop(candidate.event_key, None)
        for event_key, event in list(self._pending.items()):
            if event.get("gate_id") == opening_id:
                receipt = self._receipt(event_key)
                if receipt.status == "queued":
                    self.transition(receipt, "reject", "rejected", code="opening_withdrawn")
                self._pending.pop(event_key, None)
        _transition_object(OPENING_TRANSITIONS, opening.status, "withdrawn", "opening")
        opening.status = "withdrawn"
        if opening.selected_candidate_id is not None:
            opening.selection_version += 1
        opening.selected_candidate_id = None
        return copy.deepcopy(opening)

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
