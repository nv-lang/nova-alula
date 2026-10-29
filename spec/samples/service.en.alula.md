# Machine: ServiceCall

- machine: ServiceCall
- revision: 1
- alula_version: 0.28
- language: en

## Input

| name | type | note |
|---|---|---|
| operation_key | str | stable business operation key supplied by the caller |

## Data

| name | type | initial | non_decreasing |
|---|---|---|---|
| result | str | "" | — |

## Parties

| name | id | kind | setting | parse | profile | signals | counter |
|---|---|---|---|---|---|---|---|
| external | external | service(result str) | — | — | — | — | external_attempt |

## States

- Initial state: Wait

### Wait — appeal
- Party: external
- Idle term: 5000
- Request:

| request_field | expression |
|---|---|
| operation_key | input.operation_key |

| Event | Condition | Actions | To |
|---|---|---|---|
| response(reply) |  | result = reply | Done |
| failure |  |  | Unknown |

### Done — end

### Unknown — end

## Output

- Result: str

| end | when | response |
|---|---|---|
| Done | true | Response(result) |
| Unknown | true | Refusal(FailCode.NoResult, "the external operation outcome must be reconciled by the host") |
