# Machine: Batch

- machine: Batch
- machine_version: 1
- format: 2.26
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

| name | type | initial | non_decreasing |
|---|---|---|---|
| names | []str | input.names | — |
| to_send | []str | [] | — |
| jobs | map[str, Job] | input.names.dict(n => n, n => Job { name: n, attempt: 0 }) | — |
| answered | []str | [] | — |
| lost | []str | [] | — |

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| job | — | machine callee(input JobInput, result CallOutput) | "job:" + party | — | jobs[*].attempt |
| enhanced | enhanced | enhanced(result GateOutcome) | — | continue { human_word str, author str, source str }, halt | enhanced_attempt |

- Request limit: LIMIT

## Includes

### Pause
- File: libs/pause.en.alula.md
- Hash: d254e6297f61

| parameter | value |
|---|---|
| halt_signal | "halt" |
| nested | ["callee"] |
| request_cancel | "without_return_to_send" |
| reentry | "requests_from_to_send" |
// write right: the batch writes nothing in the pause

## States

Initial state: Prepare

### Prepare — operation

| Actions | To |
|---|---|
| to_send = names | Split |

### Split — fork

| Condition | Actions | To |
|---|---|---|
| length(names) == 0 |  | Done |
| else |  | Jobs |

### Jobs — appeal
- Party: job; set: names
- Request:

| request_field | expression |
|---|---|
| label | party |
| count | 1 |

| Event | Condition | Actions | To |
|---|---|---|---|
| response(result) |  | answered += [party]; journal("job_answered", party: party, answer: result.answer) | Join |
| failure(reason) |  | lost += [party]; journal("job_lost", party: party, code: text(reason)) | Join |

### Join — fork

| Condition | Actions | To |
|---|---|---|
| length(answered) + length(lost) >= length(names) |  | Done |
| else |  | Jobs |

### Done — end

### Halted — end

### Errored — end
- On entry:
  - journal(transition_note);
  - journal(all_data)

## Output

- Result: int

| end | when | response |
|---|---|---|
| Done | true | Response(length(answered)) |
| Errored | true | Refusal(FailCode.NoResult, "a defect of the batch") |
| Halted | Pause.reason == PauseReason.Halted | Refusal(FailCode.StoppedByHuman, "pause_halt") |
| Halted | Pause.reason == PauseReason.Cancelled | Refusal(FailCode.Cancelled, "cancel_request") |
