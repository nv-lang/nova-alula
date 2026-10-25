# Machine: Verdict

- machine: Verdict
- machine_version: 1
- format: 2.22
- language: en

An enumeration with fields (spec 2, AL-99, AL-102): the answer of the judge is a `Verdict`, one of three forms, two of them with fields. The event `response: Form { field: name }` binds the fields of the
form that came; a form without fields is written without brackets. The scenarios: `verdict-*`.

## Types

```
type Verdict enum
  | Accepted { score int>=0 }
  | Rejected { reason str }
  | Unsure
```

## Data

| name | type | initial | non_decreasing | writes |
|---|---|---|---|---|
| total | int>=0 | 0 | — | rows |
| note | str | "" | — | rows |
| judge_attempt | int>=0 | 0 | yes | mechanics |

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| judge | judge | agent(result Verdict) | — | — | judge_attempt |

## States

Initial state: Judge

### Judge — appeal
- Party: judge
- Idle term: 5000
- Request:

| request_field | expression | reads |
|---|---|---|
| prompt | "the work" | party |

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | response: Accepted { score: points } | — | total = points; journal("verdict_accepted", score: text(points)) | Passed |
| 2 | response: Rejected { reason: why } | — | note = why; journal("verdict_rejected", reason: why) | Failed |
| 3 | response: Unsure | — | journal("verdict_unsure") | Doubt |
| 4 | failure(reason) | — | note = text(reason); journal("verdict_lost", reason: text(reason)) | Failed |

### Passed — end
- Reads: total

### Failed — end
- Reads: note

### Doubt — end

## Ends

- Result: str

| end | № | when | response |
|---|---|---|---|
| Passed | 1 | true | Response("accepted with ${total}") |
| Failed | 1 | true | Refusal(FailCode.NoResult, note) |
| Doubt | 1 | true | Refusal(FailCode.NoResult, "unsure") |
