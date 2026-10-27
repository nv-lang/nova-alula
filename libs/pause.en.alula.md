# Library: Pause

- library: pause
- format: 2.26
- language: en

## Parameters

| name | type | comment |
|---|---|---|
| halt_signal | str | the party signal of the party "enhanced" by which the machine stops |
| halt_code | str | a value of the set `stop_reason` of the machine |
| nested | []str | the names of the machines to which the signals of the chain go (rule 35, item 8) |
| request_cancel | "mechanics" \| "without_return_to_send" \| "stop_transport_turn" | the effects: the table of section 9 of the specification |
| reentry | "nothing" \| "requests_from_to_send" | the effects: the table of section 9 of the specification |

## Requires

| name | type |
|---|---|
| stop_reason | "cancel_request" \| halt_code |
| enhanced | party enhanced with the signals continue { human_word str, author str, source str } and halt_signal |
| Halted | end |
| Errored | end |

## Data

| name | type | initial |
|---|---|---|
| previous | ?State | none |

## Common events     // parsed before the rows of the states (rule 23)

| Event | Condition | Actions | To |
|---|---|---|---|
| signal(human_stop { human_word, author, source }) | not end(state) and state != Pause | journal("human_stop", author: author, source: source, event: event.id)<br>previous = state<br>pass(nested, stop)<br>cancel_open(except: nested) | Pause |
| signal(parent_stop { id }) | not end(state) and state != Pause and id == call_request_id | journal("pause_by_parent_stop", request: id, event: event.id)<br>previous = state<br>pass(nested, stop)<br>cancel_open(except: nested) | Pause |
| signal(cancel_request { id }) | id != call_request_id | journal("cancel_discarded_foreign_request", request: id, event: event.id) | same |
| signal(cancel_request { id }) | id == call_request_id and end(state) | journal("cancel_discarded_already_replied", request: id, event: event.id) | same |
| signal(cancel_request { id }) | id == call_request_id and not end(state) | journal("request_cancelled", request: id, event: event.id)<br>stop_reason = "cancel_request"<br>pass(nested, cancel)<br>cancel_open | Halted |
| signal(cancel_request { id }) | else | machine_error("cancel_parse_no_match") |  |

## States

### Pause — appeal
- Party: enhanced
- Request:

| request_field | expression |
|---|---|
| previous | require(previous) |
| call_request_id |  |

| Event | Condition | Actions | To |
|---|---|---|---|
| signal(continue { author, source }) |  | journal("human_continue", previous: text(require(previous)), author: author, source: source, event: event.id)<br>pass(nested, continue) | previous |
| signal(halt_signal) |  | stop_reason = halt_code<br>pass(nested, halt) | Halted |
| signal(parent_continue { id }) | id == call_request_id | journal("parent_continue", previous: text(require(previous)), request: id, event: event.id)<br>pass(nested, continue) | previous |
| signal(parent_halt { id }) | id == call_request_id | stop_reason = halt_code<br>pass(nested, halt) | Halted |
