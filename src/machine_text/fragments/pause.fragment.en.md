# Fragment: Pause

- fragment: Pause
- format: 2.14
- language: en

> The English twin of `pause.fragment.md` (Alula 2.14, section 9): the common events and the state Pause. In the text a parameter stands as `<parameter>` and is put in before the reading.
> The list of nested machines `nested` is a parameter of the kind `[]machine`: an empty list makes `pass` and `cancel_open(except: nested)` plain (there is no nested machine
> to pass anything to); a non-empty list makes them the passing of signals to those machines (task 119).

## Parameters

| name | kind | allowed_values |
|---|---|---|
| halt_signal | signal | the party signal of the party "enhanced" |
| halt_code | text | a value of the set `stop_reason` of the machine |
| nested | []machine | the machines that get the signals of the chain (rule 35, item 8) |
| cancel_requests | behavior | `mechanics`, `without_return_to_send`, `stop_transport_turn` |
| reenter | behavior | `nothing`, `requests_from_to_send` |
| write_right | note | text |

## Data

| name | type | initial | non_decreasing | writes |
|---|---|---|---|---|
| previous | ?State | none | — | fragment |
| call_request_id | text | "" | — | mechanics |
| open_requests | []text | [] | — | mechanics |

## Common events

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | signal(human_stop(human_word, author, source)) | not end(state) and state != Pause | journal(human_stop, author: author, source: source, event: event.id); previous = state; pass(nested, stop); cancel_open(except: nested) | Pause |
| 2 | signal(parent_stop(id)) | not end(state) and state != Pause and id == call_request_id | journal(pause_by_parent_stop, request: id, event: event.id); previous = state; pass(nested, stop); cancel_open(except: nested) | Pause |
| 3 | signal(cancel_request(id)) | id != call_request_id | journal(cancel_discarded_foreign_request, request: id, event: event.id) | same |
| 4 | signal(cancel_request(id)) | id == call_request_id and end(state) | journal(cancel_discarded_already_replied, request: id, event: event.id) | same |
| 5 | signal(cancel_request(id)) | id == call_request_id and not end(state) | journal(request_cancelled, request: id, event: event.id); stop_reason = "cancel_request"; pass(nested, cancel); cancel_open | Halted |
| 6 | signal(cancel_request(id)) | else | machine_error("cancel_parse_no_match") | — |

## States

### Pause — appeal
- Party: enhanced
- Request:

| request_field | expression | reads |
|---|---|---|
| previous | require(previous) | party |
| call_request_id | call_request_id | party |

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | signal(continue(author, source)) | — | journal(human_continue, previous: text(require(previous)), author: author, source: source, event: event.id); pass(nested, continue) | previous |
| 2 | signal(<halt_signal>) | — | stop_reason = <halt_code>; pass(nested, halt) | Halted |
| 3 | signal(parent_continue(id)) | id == call_request_id | journal(parent_continue, previous: text(require(previous)), request: id, event: event.id); pass(nested, continue) | previous |
| 4 | signal(parent_halt(id)) | id == call_request_id | stop_reason = <halt_code>; pass(nested, halt) | Halted |
