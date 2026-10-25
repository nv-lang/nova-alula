# Machine: Retry

- machine: Retry
- machine_version: 1
- format: 2.25
- language: en

The destination `same` and the destination `same, rerun` (spec 4.1, AL-111). The agent that is silent is asked again by the row `same, rerun` of its appeal: the state is entered anew, the open request is cancelled and a new one is sent
(the counter of the attempts of the party is one more). The reviewer, a gate of a human, shows the other signal: the row `same` only runs its actions (a note is taken, the open request stays), the row `same, rerun`
opens the gate again with a new request. The scenarios: `retry-*`.

## Data

| name | type | initial | non_decreasing | writes |
|---|---|---|---|---|
| reply | ?str | none | — | rows |
| notes | int>=0 | 0 | yes | rows |
| rounds | int>=0 | 0 | yes | rows |
| stop_reason | "" \| "rejected" \| "failed" | "" | — | rows |
| agent_attempt | int>=0 | 0 | yes | mechanics |
| reviewer_attempt | int>=0 | 0 | yes | mechanics |

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| agent | agent | agent(result str) | — | — | agent_attempt |
| reviewer | reviewer | human(result GateOutcome) | — | note { content str }, again, accept, reject | reviewer_attempt |

## States

Initial state: Ask

### Ask — appeal
- Party: agent
- Idle term: 5000
- Request:

| request_field | expression | reads |
|---|---|---|
| prompt | "the question" | party |

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | response(answer) | — | reply = answer; journal("got_reply", text: answer) | Review |
| 2 | failure(reason in [FailCode.Timeout]) | — | journal("asked_again_silent") | same, rerun |
| 3 | failure(reason) | — | stop_reason = "failed"; journal("gave_up", reason: text(reason)) | Stopped |

### Review — appeal
- Party: reviewer
- Request:

| request_field | expression | reads |
|---|---|---|
| round | rounds | executor |

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | signal(note { content: word }) | — | notes += 1; journal("noted", text: word) | same |
| 2 | signal(again) | — | rounds += 1; journal("review_again") | same, rerun |
| 3 | signal(accept) | — | journal("accepted") | Accepted |
| 4 | signal(reject) | — | stop_reason = "rejected"; journal("rejected") | Stopped |

### Accepted — end
- Reads: reply

### Stopped — end
- Reads: stop_reason
- Except: stop_reason in [""]

## Ends

- Result: str

| end | № | when | response |
|---|---|---|---|
| Accepted | 1 | true | Response(require(reply)) |
| Stopped | 1 | stop_reason == "rejected" | Refusal(FailCode.StoppedByHuman, stop_reason) |
| Stopped | 2 | stop_reason == "failed" | Refusal(FailCode.NoResult, stop_reason) |
