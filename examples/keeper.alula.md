# Machine: Keeper

- machine: Keeper
- revision: 1
- alula_version: 0.28
- language: en

A gate (spec 1, 4.2: the party of the kind `gatekeeper`, the column `setting` names the project setting whose value decides who answers). The gatekeeper says `allow` or `deny`; the machine counts the signals that allow and ends when it has had `NEEDED` of them, a signal
that denies ends it with a refusal. Every request to the gate carries the number of the signals so far. The tests: `keeper-*`.

## Constants

| name | type | value |
|---|---|---|
| NEEDED | int>=0 | 2 |

## Data

| name | type | initial | non_decreasing |
|---|---|---|---|
| allowed | int>=0 | 0 | yes |
| stop_reason | "" \| "denied" | "" | — |

## Parties

| name | id | kind | setting | parse | profile | signals | counter |
|---|---|---|---|---|---|---|---|
| gatekeeper | gatekeeper | gatekeeper | keeper_executor | — | — | allow, deny | gatekeeper_attempt |

## States

- Initial state: Wait

### Wait — appeal
- Party: gatekeeper

| Event | Condition | Actions | To |
|---|---|---|---|
| signal(allow) |  | allowed += 1<br>journal("signal_allowed", count: text(allowed)) | Count |
| signal(deny) |  | stop_reason = "denied"<br>journal("signal_denied") | Denied |

### Count — fork

| Condition | Actions | To |
|---|---|---|
| allowed >= NEEDED |  | Opened |
| else |  | Wait |

### Opened — end

### Denied — end
- Except: stop_reason in [""]

## Output

- Result: int

| end | when | response |
|---|---|---|
| Opened | true | Response(allowed) |
| Denied | stop_reason == "denied" | Refusal(FailCode.StoppedByHuman, stop_reason) |
