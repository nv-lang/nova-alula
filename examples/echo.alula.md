# Machine: Echo

- machine: Echo
- machine_version: 1
- format: 2.25
- language: en

A chat in the quiet: the party `user` is a human with a free input (spec AL-51, AL-52: no gate, no request, no counter). Every signal of the user is journaled and counted, the row stays in the
state (`same`: the actions of the row only, no new entry); the signal `close` ends the machine. The scenarios: `echo-*`.

## Data

| name | type | initial | non_decreasing | writes |
|---|---|---|---|---|
| messages | int>=0 | 0 | yes | rows |
| last | str | "" | — | rows |
| stop_reason | "" \| "closed" | "" | — | rows |

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| user | user | human(result GateOutcome) | — | message { content str }, close | — |

## States

Initial state: Idle

### Idle — appeal
- Party: user

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | signal(message { content: word }) | — | journal("echoed", text: word); messages += 1; last = word | same |
| 2 | signal(close) | — | journal("closed_by_user"); stop_reason = "closed" | Closed |

### Closed — end
- Reads: messages, last

## Ends

- Result: int

| end | № | when | response |
|---|---|---|---|
| Closed | 1 | true | Response(messages) |
