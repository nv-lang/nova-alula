# Machine: Retry

- machine: Retry
- revision: 1
- alula_version: 0.28
- language: en

The destination `same` and the column `rerun` (spec 4.1, AL-111, AL-150). The agent that is silent is asked again by the row `same` with `yes` in the column `rerun` of its appeal: the state is entered anew, the open request is cancelled and a new one is sent
(the counter of the attempts of the party is one more). The reviewer, a gate of a human, shows the other signal: the row `same` only runs its actions (a note is taken, the open request stays), the row with `rerun`
opens the gate again with a new request. The tests: `retry-*`.

## Data

| name | type | initial | non_decreasing |
|---|---|---|---|
| reply | ?str | none | — |
| notes | int>=0 | 0 | yes |
| rounds | int>=0 | 0 | yes |
| stop_reason | "" \| "rejected" \| "failed" | "" | — |

## Parties

| name | id | kind | setting | parse | profile | signals | counter |
|---|---|---|---|---|---|---|---|
| agent | agent | agent(result str) | — | — | — | — | agent_attempt |
| reviewer | reviewer | human(result GateOutcome) | — | — | — | note { content str }, again, accept, reject | reviewer_attempt |

## States

- Initial state: Ask

### Ask — appeal
- Party: agent
- Idle term: 5000
- Request:

| request_field | expression |
|---|---|
| prompt | "the question" |

| Event | Condition | Actions | To | rerun |
|---|---|---|---|---|
| response(answer) |  | reply = answer<br>journal("got_reply", text: answer) | Review |  |
| failure(reason in [FailCode.Timeout]) |  | journal("asked_again_silent") | same | yes |
| failure(reason) |  | stop_reason = "failed"<br>journal("gave_up", reason: text(reason)) | Stopped |  |

### Review — appeal
- Party: reviewer

| Event | Condition | Actions | To | rerun |
|---|---|---|---|---|
| signal(note { content: word }) |  | notes += 1<br>journal("noted", text: word) | same |  |
| signal(again) |  | rounds += 1<br>journal("review_again") | same | yes |
| signal(accept) |  | journal("accepted") | Accepted |  |
| signal(reject) |  | stop_reason = "rejected"<br>journal("rejected") | Stopped |  |

### Accepted — end

### Stopped — end
- Except: stop_reason in [""]

## Output

- Result: str

| end | when | response |
|---|---|---|
| Accepted | true | Response(require(reply)) |
| Stopped | stop_reason == "rejected" | Refusal(FailCode.StoppedByHuman, stop_reason) |
| Stopped | stop_reason == "failed" | Refusal(FailCode.NoResult, stop_reason) |
