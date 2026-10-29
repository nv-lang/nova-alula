# Machine: Echo

- machine: Echo
- revision: 1
- alula_version: 0.28
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

| name | id | kind | setting | parse | profile | signals | counter |
|---|---|---|---|---|---|---|---|
| user | user | free_input | — | — | — | message { content str }, close | — |

## States

- Initial state: Idle

### Idle — appeal
- Party: user

| Event | Condition | Actions | To |
|---|---|---|---|
| signal(message { content: word }) |  | journal("echoed", text: word)<br>messages += 1<br>last = word | same |
| signal(close) |  | journal("closed_by_user")<br>stop_reason = "closed" | Closed |

### Closed — end

## Output

- Result: int

| end | when | response |
|---|---|---|
| Closed | true | Response(messages) |
