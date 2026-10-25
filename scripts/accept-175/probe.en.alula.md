# Machine: Probe

- machine: Probe
- machine_version: 1
- format: 2.25
- language: en

## Types
—

## Constants
—

## Parameters
—

## Input
—

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

## Functions
@FUNCTIONS@

## Includes
—

## States

Initial state: Idle

### Idle — appeal
- Party: user

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | signal(message { content: word }) | — | journal("echoed", text: word); messages += 1; last = word@ACTION@ | same |
| 2 | signal(close) | — | journal("closed_by_user"); stop_reason = "closed" | Closed |

### Closed — end
- Reads: messages, last

## Ends

- Result: int

| end | № | when | response |
|---|---|---|---|
| Closed | 1 | true | Response(messages) |

@EXTERNAL@
