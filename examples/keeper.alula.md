# Machine: Keeper

- machine: Keeper
- machine_version: 1
- format: 2.23
- language: en

A gate (spec 1, 4.2: the party `human or agent by setting`, the executor decides who answers). The gatekeeper says `allow` or `deny`; the machine counts the signals that allow and ends when it has had `NEEDED` of them, a signal
that denies ends it with a refusal. Every request to the gate carries the number of the signals so far. The scenarios: `keeper-*`.

## Constants

| name | type | value |
|---|---|---|
| NEEDED | int>=0 | 2 |

## Data

| name | type | initial | non_decreasing | writes |
|---|---|---|---|---|
| allowed | int>=0 | 0 | yes | rows |
| stop_reason | "" \| "denied" | "" | — | rows |
| gatekeeper_attempt | int>=0 | 0 | yes | mechanics |

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| gatekeeper | gatekeeper | human or agent by setting keeper_executor(result GateOutcome) | — | allow, deny | gatekeeper_attempt |

## States

Initial state: Wait

### Wait — appeal
- Party: gatekeeper
- Request:

| request_field | expression | reads |
|---|---|---|
| allowed | — | executor |

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | signal(allow) | — | allowed += 1; journal("signal_allowed", count: text(allowed)) | Count |
| 2 | signal(deny) | — | stop_reason = "denied"; journal("signal_denied") | Denied |

### Count — fork
- Reads: allowed

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | allowed >= NEEDED | — | Opened |
| 2 | else | — | Wait |

### Opened — end
- Reads: allowed

### Denied — end
- Reads: stop_reason
- Except: stop_reason in [""]

## Ends

- Result: int

| end | № | when | response |
|---|---|---|---|
| Opened | 1 | true | Response(allowed) |
| Denied | 1 | stop_reason == "denied" | Refusal(FailCode.StoppedByHuman, stop_reason) |
