# Machine: Batch

- machine: Batch
- machine_version: 1
- format: 2.25
- language: en

A set of nested calls (spec 4.2, `set:`; the party of the kind `machine`): one request to the machine `callee` for every name of the input `names`, no more than `LIMIT` at once (`Request limit`). The answers
and the losses are collected in the order they come; the fork `Join` waits for all of them, the fork `Split` sends an empty set straight to the end. The pair is checked as a whole by `alula test` (the callee is found in the folder). The tests: `batch-*`.

## Types

```
type Job { name str, attempt int>=0 }
type JobInput { label str, count int>=0, profile str }
type CallOutput { answer str, score int>=0 }
```

## Constants

| name | type | value |
|---|---|---|
| LIMIT | int>=1 | 2 |

## Input

| name | type | note |
|---|---|---|
| names | []str | the names of the jobs |

## Data

| name | type | initial | non_decreasing | writes |
|---|---|---|---|---|
| names | []str | input.names | — | rows |
| to_send | []str | [] | — | rows_and_mechanics |
| jobs | map[str, Job] | input.names.dict(n => n, n => Job { name: n, attempt: 0 }) | — | rows |
| jobs[*].attempt | int>=0 | — | yes | mechanics |
| answered | []str | [] | — | rows |
| lost | []str | [] | — | rows |
| stop_reason | "" \| "pause_halt" \| "cancel_request" | "" | — | rows_and_fragment |
| enhanced_attempt | int>=0 | 0 | yes | mechanics |

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| job | — | machine callee(input JobInput, result CallOutput) | "job:" + party | — | jobs[*].attempt |
| enhanced | enhanced | enhanced(result GateOutcome) | — | continue { human_word str, author str, source str }, halt | enhanced_attempt |

- Request limit: LIMIT

## Includes

```
Pause(halt_signal: halt, halt_code: "pause_halt", nested: [callee], cancel_requests: without_return_to_send, reenter: requests_from_to_send, write_right: "the batch writes nothing in the pause")
```

## States

Initial state: Prepare

### Prepare — operation
- Reads: names

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | immediate | — | to_send = names | Split |

### Split — fork
- Reads: names

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | length(names) == 0 | — | Done |
| 2 | else | — | Jobs |

### Jobs — appeal
- Party: job; set: names
- Request:

| request_field | expression | reads |
|---|---|---|
| label | party | party |
| count | 1 | party |
| answered | — | executor |
| lost | — | executor |

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | response(result) | — | answered += [party]; journal("job_answered", party: party, answer: result.answer) | Join |
| 2 | failure(reason) | — | lost += [party]; journal("job_lost", party: party, code: text(reason)) | Join |

### Join — fork
- Reads: answered, lost, names

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | length(answered) + length(lost) >= length(names) | — | Done |
| 2 | else | — | Jobs |

### Done — end
- Reads: answered, lost

### Halted — end
- Reads: stop_reason
- Except: stop_reason in [""]

### Errored — end
- Reads: all_data
- On entry:
  - journal(transition_note);
  - journal(all_data)

## Ends

- Result: int

| end | № | when | response |
|---|---|---|---|
| Done | 1 | true | Response(length(answered)) |
| Errored | 1 | true | Refusal(FailCode.NoResult, "a defect of the batch") |
| Halted | 1 | stop_reason == "pause_halt" | Refusal(FailCode.StoppedByHuman, stop_reason) |
| Halted | 2 | stop_reason == "cancel_request" | Refusal(FailCode.Cancelled, stop_reason) |
