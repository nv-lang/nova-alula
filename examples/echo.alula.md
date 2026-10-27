# Machine: Echo

- machine: Echo
- machine_version: 1
- format: 2.26
- language: en

A chat in the quiet: the party `user` is a human with a free input (spec AL-51, AL-52: no gate, no request, no counter). Every signal of the user is journaled and counted, the row stays in the
state (`same`: the actions of the row only, no new entry); the signal `close` ends the machine. The tests: `echo-*`.

## Data

| name | type | initial | non_decreasing |
|---|---|---|---|
| messages | int>=0 | 0 | yes |
| last | str | "" | — |
| stop_reason | "" \| "closed" | "" | — |

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| user | user | human(result GateOutcome) | — | message { content str }, close | — |

## States

Initial state: Idle

### Idle — appeal
- Party: user

| Event | Condition | Actions | To |
|---|---|---|---|
| signal(message { content: word }) |  | journal("echoed", text: word); messages += 1; last = word | same |
| signal(close) |  | journal("closed_by_user"); stop_reason = "closed" | Closed |

### Closed — end

## Output

- Result: int

| end | when | response |
|---|---|---|
| Closed | true | Response(messages) |
