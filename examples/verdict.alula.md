# Machine: Verdict

- machine: Verdict
- revision: 1
- alula_version: 0.28
- language: en

An enumeration with fields (spec 2, AL-99, AL-102): the answer of the judge is a `Verdict`, one of three forms, two of them with fields. The event `response: Form { field: name }` binds the fields of the
form that came; a form without fields is written without brackets. The tests: `verdict-*`.

## Types

```
type Verdict enum
  | Accepted { score int>=0 }
  | Rejected { reason str }
  | Unsure
```

## Data

| name | type | initial | non_decreasing |
|---|---|---|---|
| total | int>=0 | 0 | — |
| note | str | "" | — |

## Parties

| name | id | kind | setting | parse | profile | signals | counter |
|---|---|---|---|---|---|---|---|
| judge | judge | agent(result Verdict) | — | — | — | — | judge_attempt |

## States

- Initial state: Judge

### Judge — appeal
- Party: judge
- Idle term: 5000
- Request:

| request_field | expression |
|---|---|
| prompt | "the work" |

| Event | Condition | Actions | To |
|---|---|---|---|
| response: Accepted { score: points } |  | total = points<br>journal("verdict_accepted", score: text(points)) | Passed |
| response: Rejected { reason: why } |  | note = why<br>journal("verdict_rejected", reason: why) | Failed |
| response: Unsure |  | journal("verdict_unsure") | Doubt |
| failure(reason) |  | note = text(reason)<br>journal("verdict_lost", reason: text(reason)) | Failed |

### Passed — end

### Failed — end

### Doubt — end

## Output

- Result: str

| end | when | response |
|---|---|---|
| Passed | true | Response("accepted with ${total}") |
| Failed | true | Refusal(FailCode.NoResult, note) |
| Doubt | true | Refusal(FailCode.NoResult, "unsure") |
