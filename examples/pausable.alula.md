# Machine: Pausable

- machine: Pausable
- machine_version: 1
- format: 2.22
- language: en

The fragment `Pause` (spec 9): a human stops the machine in the middle of the work of the agent, the open request is cancelled and the machine waits in `Pause`; `continue` enters the state it was stopped
in again, with a new request; `halt` ends the machine with the code `pause_halt`. The fragment brings the state `Pause`, the common events and the party `enhanced`; the table writes only its own work. The scenarios: `pause-*`.

## Data

| name | type | initial | non_decreasing | writes |
|---|---|---|---|---|
| reply | ?str | none | — | rows |
| stop_reason | "" \| "failed" \| "pause_halt" \| "cancel_request" | "" | — | rows_and_fragment |
| worker_attempt | int>=0 | 0 | yes | mechanics |
| enhanced_attempt | int>=0 | 0 | yes | mechanics |

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| worker | worker | agent(result str) | — | — | worker_attempt |
| enhanced | enhanced | enhanced(result GateOutcome) | — | continue { human_word str, author str, source str }, halt | enhanced_attempt |

- Request limit: 1

## Includes

```
Pause(halt_signal: halt, halt_code: "pause_halt", nested: [], cancel_requests: mechanics, reenter: nothing, write_right: "the machine writes nothing in the pause")
```

## States

Initial state: Work

### Work — appeal
- Party: worker
- Idle term: 5000
- Request:

| request_field | expression | reads |
|---|---|---|
| prompt | "the work" | party |

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | response(text) | — | reply = text; journal("worked", text: text) | Done |
| 2 | failure(reason) | — | stop_reason = "failed"; journal("work_lost", reason: text(reason)) | Halted |

### Done — end
- Reads: reply

### Halted — end
- Reads: stop_reason
- Except: stop_reason in [""]

### Errored — end
- Reads: all_data
- On entry:
  - journal(transition_note);
  - journal(all_data)

## Ends

- Result: str

| end | № | when | response |
|---|---|---|---|
| Done | 1 | true | Response(require(reply)) |
| Errored | 1 | true | Refusal(FailCode.NoResult, "a defect of the machine") |
| Halted | 1 | stop_reason == "failed" | Refusal(FailCode.NoResult, stop_reason) |
| Halted | 2 | stop_reason == "pause_halt" | Refusal(FailCode.StoppedByHuman, stop_reason) |
| Halted | 3 | stop_reason == "cancel_request" | Refusal(FailCode.Cancelled, stop_reason) |
