# Machine: Pausable

- machine: Pausable
- machine_version: 1
- format: 2.26
- language: en

The fragment `Pause` (spec 9): a human stops the machine in the middle of the work of the agent, the open request is cancelled and the machine waits in `Pause`; `continue` enters the state it was stopped
in again, with a new request; `halt` ends the machine with the code `pause_halt`. The fragment brings the state `Pause`, the common events and the party `enhanced`; the table writes only its own work. The tests: `pause-*`.

## Data

| name | type | initial | non_decreasing |
|---|---|---|---|
| reply | ?str | none | — |
| stop_reason | "" \| "failed" | "" | — |

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| worker | worker | agent(result str) | — | — | worker_attempt |
| enhanced | enhanced | enhanced(result GateOutcome) | — | continue { human_word str, author str, source str }, halt | enhanced_attempt |

- Request limit: 1

## Includes

### Pause
- File: libs/pause.en.alula.md
- Hash: d254e6297f61

| parameter | value |
|---|---|
| halt_signal | "halt" |
| nested | [] |
| request_cancel | "mechanics" |
| reentry | "nothing" |
// write right: the machine writes nothing in the pause

## States

Initial state: Work

### Work — appeal
- Party: worker
- Idle term: 5000
- Request:

| request_field | expression |
|---|---|
| prompt | "the work" |

| Event | Condition | Actions | To |
|---|---|---|---|
| response(text) |  | reply = text; journal("worked", text: text) | Done |
| failure(reason) |  | stop_reason = "failed"; journal("work_lost", reason: text(reason)) | Halted |

### Done — end

### Halted — end
- Except: stop_reason in [""]

### Errored — end
- On entry:
  - journal(transition_note);
  - journal(all_data)

## Output

- Result: str

| end | when | response |
|---|---|---|
| Done | true | Response(require(reply)) |
| Errored | true | Refusal(FailCode.NoResult, "a defect of the machine") |
| Halted | stop_reason == "failed" | Refusal(FailCode.NoResult, stop_reason) |
| Halted | Pause.reason == PauseReason.Halted | Refusal(FailCode.StoppedByHuman, "pause_halt") |
| Halted | Pause.reason == PauseReason.Cancelled | Refusal(FailCode.Cancelled, "cancel_request") |
