# Machine: Agent step

- machine: agent_step
- machine_version: alula-2.22
- format: 2.22
- language: en

This is an **illustration**: the "Agent step" machine in full, written in the Alula format, format version 2.22 ([state-machine-alula-spec.md](state-machine-alula-spec.md); it is the only definition of the notation). It is the English-language twin of [state-machine-agent-step.alula.md](state-machine-agent-step.alula.md): the same machine, row for row, with the English keywords of the [word table](alula-keywords.tsv) (spec, section 1a); the JSON tree `machine/2` is the same for both files up to the internal names (constants, parameters, functions, party names, bindings). The file lets a reader open and see a real machine: types, data, parties, functions, all 37 transition rows, the ends with the "end to response" table, the attached "Pause" fragment; what the fragment brings (parameters, common events COMMON 1-6, the Pause state with events PAUSE 1-4) is described in section 9 of the specification.

**Status.** The equivalence of this notation to the automaton by journal has not been checked: the "Agent step" interpreter was not run, scenarios were not compared. **The first source is this Alula record; the old tables are in the archive and are not updated.** The former notation is the state tables [archive/state-machine-agent-step-states.md](archive/state-machine-agent-step-states.md) and the automaton code [archive/state-machine-agent-step-automaton.md](archive/state-machine-agent-step-automaton.md). The "Pause" fragment is [archive/state-machine-pause-states.md](archive/state-machine-pause-states.md), the journal codes are [state-machine-journal.md](state-machine-journal.md), the names are [state-machine-glossary.md](state-machine-glossary.md). The equivalence of this file with the Russian sample is checked by [check-alula-samples.py](check-alula-samples.py).

**How the notation is laid out.** Sections follow the order of section 1 of the format. The `№` of a state row equals the label `NAME #n` in the tables and in the automaton code (the label of a fork default is the next number; the `else` rows are written out and equal the default). The key lines of states are list items (`- Party: …`), tables stand at block level; paragraphs of prose outside tables and code blocks are comments for the reader, the parser skips them. Text values (`turn`, `stop_reason`, decisions) are the words of the automaton code (Latin). There are 37 transition rows: Start 1, AgentTurn 9, Retry 4, Continuation 3, ReplyValidation 5, Policy 4, Permission 2, Budget 5, Accounting 1, StepOutcome 3; the rows PAUSE 1-4 and COMMON 1-6 come from the fragment. The "Ends" table has 13 rows: End 1, Errored 1, Halted 11. The names are English and Latin, so each name is its own JSON name (spec, section 1a, "JSON name"); the Russian sample gets the same JSON names automatically (the glossary, then transliteration) and lists in its section `## Имена` only the names whose automatic name is wrong (2 rows); this file needs no `## Names` section. In the "Request" tables a field whose expression is the same name carries `—` in the column `expression` (`| turn | — | party |`).

## Types

```
type CallerKind enum Lens | CycleSession | ChatTurn | Gatekeeper
type ActionKind enum
  | Read = "read"
  | Write = "write"
  | Delete = "delete"
  | Move = "move"
  | Search = "search"
  | Execute = "execute"
  | Network = "network"
  | Think = "think"
  | SwitchMode = "switch_mode"
  | Other = "other"
type ReplyCheck enum Valid | Violated | Empty
type FailCode enum
  | NoResult = "no_result"
  | ModelRefused = "model_refused"
  | ConnectionLost = "connection_lost"
  | FormNotFixed = "form_not_fixed"
  | Timeout = "timeout"
  | StoppedByHuman = "stopped_by_human"
  | CeilingReached = "ceiling_reached"
  | Cancelled = "cancelled"
  | MaxTokens = "max_tokens"
  | MaxTurnRequests = "max_turn_requests"

type AgentModel { id str, provider str, variant ?str }
type TokenUsage { input ?int, output ?int, reasoning ?int, cache_read ?int, cache_write ?int }
type AgentProfile { family str, model str, effort ?str }
type AgentLimits { silence_term ?int, token_budget ?int, cost_budget ?f64, turn_limit ?int }
type AgentRequest { kind CallerKind, profile AgentProfile, session str, dialog_kind str, context str,
                    limits AgentLimits, trace str, step int }
type TransportUsage { model AgentModel, tokens TokenUsage, cost ?f64, context_used ?int, request_started int }
type Usage { session str, result str, family str, model AgentModel, tokens TokenUsage, cost ?f64,
             created int, updated int, context_used ?int, trace str, step int }
type AgentReply { text ?str, artifact ?str, usage Usage, request_started ?int }
type PermissionRequest { action ActionKind, description str }

type TurnResult enum
  | Finished { text ?str, artifact ?str, transport_usage TransportUsage }
  | Truncated { transport_usage TransportUsage }
  | TurnRequestLimit { transport_usage TransportUsage }
  | ModelRefusal { transport_usage TransportUsage }
  | Stopped { transport_usage TransportUsage }
  | TransientError
  | PermanentError
  | NeedsPermission { permission_request PermissionRequest }
```

The envelope types (request, response, refusal) are not declared: the executor builds them; the machine writes only `Response(value)` and `Refusal(code, text)` (section "Ends"). The source calls "float" non-negative; the format does not express a bound on a float, so the `?f64` fields have no bound, as in the code. The values of `ActionKind` and `FailCode` (the texts in quotes) are the texts of the journal and of the wire; `CallerKind` and `ReplyCheck` have no values in the source, in the data they go by the JSON name of the element.

## Constants

| name | type | value |
|---|---|---|
| RETRIES | int>=0 | 3 |
| CONTINUATIONS | int>=0 | 1 |
| FORM_RETURNS | int>=0 | 1 |
| TURN_LIMIT | int>=0 | 20 |

## Parameters

| name | type | default | project_override |
|---|---|---|---|
| RETRY_PAUSE | int>=0 | 2000 | — |
| PERMISSION_POLICY | full map[ActionKind, "allow" \| "deny" \| "ask"] | [ActionKind.Read: "ask", ActionKind.Write: "ask", ActionKind.Delete: "ask", ActionKind.Move: "ask", ActionKind.Search: "ask", ActionKind.Execute: "ask", ActionKind.Network: "ask", ActionKind.Think: "ask", ActionKind.SwitchMode: "ask", ActionKind.Other: "ask"] | — |

The sources call both values a project parameter but give no project key: the column holds `—`. The value of `RETRY_PAUSE` was accepted by the owner in the source, it is not a stub. The values of `PERMISSION_POLICY` are `"allow"`, `"deny"`, `"ask"`: the set of literals stands in the type argument of the map.

## Input

| name | type | note |
|---|---|---|
| kind | CallerKind | the caller kind |
| profile | AgentProfile | the agent profile; at the caller — the column `profile` of its "Parties" |
| session | str | the agent session |
| dialog_kind | str | the dialog kind |
| context | str | the turn context |
| limits | AgentLimits | the step limits |
| trace | str | the trace of the caller |
| step | int | the step number of the caller |

The input fields are exactly the fields of `AgentRequest`: the callers name the party `machine agent_step(input AgentRequest, result AgentReply)`, and the fields of their request are the fields of this type (the format, section 1, "The input of a called machine"). The record `agent_request` as a whole is built by `initial` in "Data". The input has no invariant. The call request identifier (`call_request_id`) is not in the input: the executor supplies it.

## Data

The data of the "Pause" fragment (`previous`, `call_request_id`, `open_requests`) comes from the fragment and is not repeated here (section "Includes"); in `all_data` it comes first. The executor's data (`state`, `trace`, `step`, the event counter, the step reason, accepted requests, the journal) and the store's data (`human_words`, failure texts) are not entered in the table.

| name | type | initial | non_decreasing | writes |
|---|---|---|---|---|
| agent_request | AgentRequest | AgentRequest { kind: input.kind, profile: input.profile, session: input.session, dialog_kind: input.dialog_kind, context: input.context, limits: input.limits, trace: input.trace, step: input.step } | — | rows |
| turn | "first" \| "retry" \| "continue" \| "fix" \| "permission" | "first" | — | rows |
| retry_count | int>=0 | 0 | yes, <= RETRIES | rows |
| continuation_count | int>=0 | 0 | yes, <= CONTINUATIONS | rows |
| return_count | int>=0 | 0 | yes, <= FORM_RETURNS | rows |
| turn_count | int>=0 | 0 | yes | rows |
| turn_before_retry | ?("first" \| "retry" \| "continue" \| "fix" \| "permission") | none | — | rows |
| transport_usage | ?TransportUsage | none | — | rows |
| reply_text | ?str | none | — | rows |
| reply_artifact | ?str | none | — | rows |
| permission_request | ?PermissionRequest | none | — | rows |
| permission_decision | ?("allow" \| "deny") | none | — | rows |
| started | ?int | none | — | rows |
| usage | ?Usage | none | — | rows |
| stop_reason | "" \| "no_result" \| "model_refused" \| "connection_lost" \| "form_not_fixed" \| "timeout" \| "max_tokens" \| "cost_limit" \| "max_turn_requests" \| "stopped_by_agent" \| "pause_halt" \| "cancel_request" | "" | — | rows_and_fragment |
| agent_attempt | int>=0 | 0 | yes | mechanics |
| gatekeeper_attempt | int>=0 | 0 | yes | mechanics |
| enhanced_attempt | int>=0 | 0 | yes | mechanics |

The bound `turn_count <= turn limit` is not written: when the limit is below 1, Start sets 1, and the bound in the source is wrong for part of the values. The machine does not read `turn` to branch (the transport branches on it); `turn_before_retry` keeps the turn that is repeated after a transient error. `stop_reason` is written by the rows of the machine and by the "Pause" fragment (`pause_halt`, `cancel_request`). The name `transport_usage` serves both the data and the field of the `TurnResult` forms (the glossary calls the form field `usage`, which would clash with the data `usage`).

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| agent | agent | agent(result TurnResult) | — | — | agent_attempt |
| gatekeeper | gatekeeper | human or agent by setting elevated_attention_executor(result GateOutcome) | — | allow, deny | gatekeeper_attempt |
| enhanced | enhanced | enhanced(result GateOutcome) | — | continue { human_word str, author str, source str }, halt | enhanced_attempt |

- Request limit: 1

The agent profile lies inside `agent_request.profile` and goes to the party as part of that field; the request of the code has no separate field `profile`, so the column holds `—`. The gatekeeper is a human by default, an agent by the project setting `elevated_attention_executor`; the enhanced party is the party of the Pause state (a human by default, an enhanced gatekeeper by the owner's permission).

## Functions

```
fn sum_ints(a ?int, b ?int) -> ?int =>
  if has(a) and has(b) then { (a ?? 0) + (b ?? 0) } else { a ?? b }

fn sum_floats(a ?f64, b ?f64) -> ?f64 =>
  if has(a) and has(b) then { (a ?? 0.0) + (b ?? 0.0) } else { a ?? b }

fn add_tokens(a TokenUsage, b TokenUsage) -> TokenUsage =>
  TokenUsage { input: sum_ints(a.input, b.input), output: sum_ints(a.output, b.output),
               reasoning: sum_ints(a.reasoning, b.reasoning),
               cache_read: sum_ints(a.cache_read, b.cache_read), cache_write: sum_ints(a.cache_write, b.cache_write) }

fn add_usage(previous ?TransportUsage, new TransportUsage) -> TransportUsage =>
  if has(previous)
  then { let p = require(previous);
        TransportUsage { model: new.model, tokens: add_tokens(p.tokens, new.tokens),
                         cost: sum_floats(p.cost, new.cost),
                         context_used: new.context_used, request_started: new.request_started } }
  else { new }

fn tokens_spent(tu ?TransportUsage) -> int =>
  if has(tu)
  then { let p = require(tu); (p.tokens.input ?? 0) + (p.tokens.output ?? 0) + (p.tokens.reasoning ?? 0) }
  else { 0 }

fn cost_spent(tu ?TransportUsage) -> f64 =>
  if has(tu) then { require(tu).cost ?? 0.0 } else { 0.0 }

fn token_limit_reached(req AgentRequest, tu ?TransportUsage) -> bool =>
  has(req.limits.token_budget) and tokens_spent(tu) >= (req.limits.token_budget ?? 0)

fn cost_limit_reached(req AgentRequest, tu ?TransportUsage) -> bool =>
  has(req.limits.cost_budget) and cost_spent(tu) >= (req.limits.cost_budget ?? 0.0)

fn turn_limit_reached(req AgentRequest, turns int>=0) -> bool =>
  turns >= (req.limits.turn_limit ?? TURN_LIMIT)

fn interactive(call_kind CallerKind) -> bool =>
  call_kind == CallerKind.CycleSession or call_kind == CallerKind.ChatTurn

fn needs_elevated_attention(action ActionKind) -> bool =>
  match action {
    ActionKind.Delete | ActionKind.Move | ActionKind.Execute | ActionKind.Network | ActionKind.SwitchMode => true
    else => false
  }

fn decision_by_policy(action ActionKind, call_kind CallerKind) -> "allow" | "deny" | "ask" {
  let by_table = if needs_elevated_attention(action) then { "ask" } else { PERMISSION_POLICY[action] };
  if by_table == "ask" and not interactive(call_kind) then { "deny" } else { by_table }
}

fn retry_pause(n int>=0) -> int =>
  (1..n).fold(RETRY_PAUSE, (m, _) => m * 2)

fn turn_term(req AgentRequest, request_turn str, retries int>=0) -> int {
  let extra = if request_turn == "retry" then { retry_pause(retries) } else { 0 };
  let term = req.limits.silence_term;
  if has(term) then { (term ?? 0) + extra } else { 0 }
}

fn collect_usage(req AgentRequest, stopped str, tu ?TransportUsage, began ?int, updated int) -> Usage {
  let step_result = if stopped == "" then { "reply" } else { stopped };
  Usage {
    session: req.session, result: step_result, family: req.profile.family,
    model: (if has(tu) then { require(tu).model }
            else { AgentModel { id: req.profile.model, provider: "", variant: req.profile.effort } }),
    tokens: (if has(tu) then { require(tu).tokens }
             else { TokenUsage { input: none, output: none, reasoning: none, cache_read: none, cache_write: none } }),
    cost: (if has(tu) then { require(tu).cost } else { none }),
    created: began ?? updated, updated: updated,
    context_used: (if has(tu) then { require(tu).context_used } else { none }),
    trace: req.trace, step: req.step }
}

fn usage_event(u Usage) -> JournalEvent =>
  journal_event("agent_usage", session: u.session, result: u.result, model: u.model.id,
                input: text(u.tokens.input), output: text(u.tokens.output), reasoning: text(u.tokens.reasoning),
                cache_read: text(u.tokens.cache_read), cache_write: text(u.tokens.cache_write), cost: text(u.cost))
```

Correspondence to the automaton code: the names of the functions are the names of the code (`sum_ints`, `sum_floats`, `add_tokens`, `add_usage`, `tokens_spent`, `cost_spent`, `token_limit_reached`, `cost_limit_reached`, `turn_limit_reached`, `interactive`, `needs_elevated_attention`, `decision_by_policy`, `retry_pause`, `turn_term`, `usage_event`, `collect_usage`); `project_policy` is the parameter `PERMISSION_POLICY`; `action_kind_word` is `text(ActionKind)` (the values are in the enum), `number_word` and `float_word` are `text(x)` (none is `none`). `record_end_usage` and `journal_machine_data` are not functions but actions in the "On entry" of the ends; `reply_validation`, `close_agent_turn`, `time_now` are primitives (section "Primitives").

## Includes

```
Pause(halt_signal: halt, halt_code: "pause_halt", nested: [],
      cancel_requests: stop_transport_turn, reenter: nothing,
      write_right: "files the agent edits; the pause does not touch their rights")
```

## States

Initial state: Start

### Start — operation
- On entry: let moment = call(time_now)

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | immediate | — | started = moment; turn_count = 1 | AgentTurn |

### AgentTurn — appeal
- Party: agent
- Idle term: turn_term(agent_request, turn, retry_count)
- Form returns: 0
- Request:

| request_field | expression | reads |
|---|---|---|
| agent_request | — | party |
| turn | — | party |
| retry_count | — | party |
| turn_before_retry | — | party |
| permission_decision | — | party |
| transport_usage | — | executor |

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | response: Finished { text, artifact, transport_usage: received } | — | transport_usage = add_usage(transport_usage, received); reply_text = text; reply_artifact = artifact | ReplyValidation |
| 2 | response: Truncated { transport_usage: received } | — | transport_usage = add_usage(transport_usage, received) | Continuation |
| 3 | response: TurnRequestLimit { transport_usage: received } | — | transport_usage = add_usage(transport_usage, received); stop_reason = "max_turn_requests"; journal(turn_requests_exhausted) | Accounting |
| 4 | response: ModelRefusal { transport_usage: received } | — | transport_usage = add_usage(transport_usage, received); stop_reason = "model_refused"; journal(model_refused) | Accounting |
| 5 | response: Stopped { transport_usage: received } | — | transport_usage = add_usage(transport_usage, received); stop_reason = "stopped_by_agent"; journal(turn_cancelled) | Accounting |
| 6 | response: TransientError | — | — | Retry |
| 7 | response: PermanentError | — | stop_reason = "no_result"; journal(agent_permanent_error) | Accounting |
| 8 | response: NeedsPermission { permission_request: request } | — | permission_request = request | Policy |
| 9 | failure(reason in [FailCode.ConnectionLost, FailCode.Timeout, FailCode.NoResult]) | — | stop_reason = text(reason); journal(turn_failed, reason: text(reason)) | Accounting |

The appeal has no "On accept" (in the code `on_accept` is empty). A form fix goes not as a return within the same request but as a new turn "fix" by the rows of ReplyValidation, hence `Form returns: 0`. A failure code outside the list of row 9 is brought by the executor to `NoResult`, which is in the list.

### Retry — fork
- Reads: retry_count, turn

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | retry_count < RETRIES and turn != "retry" | retry_count += 1; turn_before_retry = turn; turn = "retry"; journal(agent_transient_error, retry: text(retry_count)) | Budget |
| 2 | retry_count < RETRIES and turn == "retry" | retry_count += 1; journal(agent_transient_error, retry: text(retry_count)) | Budget |
| 3 | retry_count >= RETRIES | stop_reason = "no_result"; journal(agent_transient_error_exhausted, retries: text(RETRIES)) | Accounting |
| 4 | else | machine_error("fork_no_match", fork: "Retry") | — |

### Continuation — fork
- Reads: continuation_count

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | continuation_count < CONTINUATIONS | continuation_count += 1; turn = "continue"; journal(output_truncated_continue) | Budget |
| 2 | continuation_count >= CONTINUATIONS | stop_reason = "max_tokens"; journal(output_truncated_again) | Accounting |
| 3 | else | machine_error("fork_no_match", fork: "Continuation") | — |

### ReplyValidation — fork
- Reads: return_count, reply_text, reply_artifact, agent_request
- On entry: let validation = call(reply_validation)

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | validation == ReplyCheck.Valid | — | Accounting |
| 2 | validation == ReplyCheck.Empty | stop_reason = "no_result"; journal(agent_no_result) | Accounting |
| 3 | validation == ReplyCheck.Violated and return_count < FORM_RETURNS | return_count += 1; turn = "fix"; journal(reply_form_violated) | Budget |
| 4 | validation == ReplyCheck.Violated and return_count >= FORM_RETURNS | stop_reason = "form_not_fixed"; journal(reply_form_not_fixed) | Accounting |
| 5 | else | machine_error("fork_no_match", fork: "ReplyValidation") | — |

### Policy — fork
- Reads: agent_request, permission_request
- On entry:
  - let request = require(permission_request);
  - let decision = decision_by_policy(request.action, agent_request.kind)

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | decision == "allow" | permission_decision = "allow"; turn = "permission"; journal(permission_auto_allowed, action: text(request.action)) | Budget |
| 2 | decision == "deny" | permission_decision = "deny"; turn = "permission"; journal(permission_auto_denied, action: text(request.action)) | Budget |
| 3 | decision == "ask" | — | Permission |
| 4 | else | machine_error("fork_no_match", fork: "Policy") | — |

### Permission — appeal
- Party: gatekeeper
- Request:

| request_field | expression | reads |
|---|---|---|
| agent_request | — | party |
| permission_request | require(permission_request) | party |

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | signal(allow) | — | permission_decision = "allow"; turn = "permission"; journal(permission_human_allowed, action: text(require(permission_request).action)) | Budget |
| 2 | signal(deny) | — | permission_decision = "deny"; turn = "permission"; journal(permission_human_denied, action: text(require(permission_request).action)) | Budget |

The request field `permission_request` is named as the data but with another expression: when building the request the code applies `require`, the rows read the data and take `require` themselves.

### Budget — fork
- Reads: agent_request, transport_usage, turn_count
- On entry:
  - let tokens_exhausted = token_limit_reached(agent_request, transport_usage);
  - let cost_exhausted = cost_limit_reached(agent_request, transport_usage);
  - let turns_exhausted = turn_limit_reached(agent_request, turn_count)

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | tokens_exhausted | stop_reason = "max_tokens"; journal(token_limit, spent: text(tokens_spent(transport_usage))) | Accounting |
| 2 | not tokens_exhausted and cost_exhausted | stop_reason = "cost_limit"; journal(cost_limit, spent: text(cost_spent(transport_usage))) | Accounting |
| 3 | not tokens_exhausted and not cost_exhausted and turns_exhausted | stop_reason = "max_turn_requests"; journal(turn_limit, sent: text(turn_count)) | Accounting |
| 4 | not tokens_exhausted and not cost_exhausted and not turns_exhausted | turn_count += 1 | AgentTurn |
| 5 | else | machine_error("fork_no_match", fork: "Budget") | — |

### Accounting — operation
- Reads: agent_request, stop_reason, transport_usage, started
- On entry:
  - let now = call(time_now);
  - let collected = collect_usage(agent_request, stop_reason, transport_usage, started, now)

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | immediate | — | usage = collected; journal(usage_event(collected)) | StepOutcome |

### StepOutcome — fork
- Reads: stop_reason

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | stop_reason == "" | — | End |
| 2 | stop_reason != "" | — | Halted |
| 3 | else | machine_error("fork_no_match", fork: "StepOutcome") | — |

The Pause state is brought by the "Pause" fragment (section "Includes"); it is not declared here, its rows PAUSE 1-4 and the common events COMMON 1-6 are in section 9 of the specification.

### End — end
- Reads: transport_usage, reply_text, reply_artifact, usage

### Halted — end
- Reads: usage, agent_request, stop_reason, transport_usage, started
- On entry:
  - let now = call(time_now);
  - call(close_agent_turn);
  - if not has(usage) then { journal(usage_event(collect_usage(agent_request, stop_reason, transport_usage, started, now))) };
  - journal(agent_step_stopped, reason: stop_reason)
- Except: stop_reason in [""]

### Errored — end
- Reads: all_data
- On entry:
  - let now = call(time_now);
  - call(close_agent_turn);
  - if not has(usage) then { journal(usage_event(collect_usage(agent_request, stop_reason, transport_usage, started, now))) };
  - journal(transition_note);
  - journal(all_data)

Errored is entered from the `else` rows of the forks (`machine_error("fork_no_match", …)`), from COMMON 6 (`machine_error("cancel_parse_no_match")`) and by a machine error of the executor; on all paths `transition_note` is defined. The usage in Halted and Errored is written only if Accounting was not passed (entry by a common event or a defect): then `usage` is none.

## Ends

- Result: AgentReply

| end | № | when | response |
|---|---|---|---|
| End | 1 | true | Response(AgentReply { text: reply_text, artifact: reply_artifact, usage: require(usage), request_started: if has(transport_usage) then { require(transport_usage).request_started } else { none } }) |
| Errored | 1 | true | Refusal(FailCode.NoResult, "agent step defect: " + transition_note.code) |
| Halted | 1 | stop_reason == "no_result" | Refusal(FailCode.NoResult, stop_reason) |
| Halted | 2 | stop_reason == "model_refused" | Refusal(FailCode.ModelRefused, stop_reason) |
| Halted | 3 | stop_reason == "connection_lost" | Refusal(FailCode.ConnectionLost, stop_reason) |
| Halted | 4 | stop_reason == "form_not_fixed" | Refusal(FailCode.FormNotFixed, stop_reason) |
| Halted | 5 | stop_reason == "timeout" | Refusal(FailCode.Timeout, stop_reason) |
| Halted | 6 | stop_reason == "max_tokens" | Refusal(FailCode.MaxTokens, stop_reason) |
| Halted | 7 | stop_reason == "cost_limit" | Refusal(FailCode.MaxTokens, stop_reason) |
| Halted | 8 | stop_reason == "max_turn_requests" | Refusal(FailCode.MaxTurnRequests, stop_reason) |
| Halted | 9 | stop_reason == "stopped_by_agent" | Refusal(FailCode.Cancelled, stop_reason) |
| Halted | 10 | stop_reason == "pause_halt" | Refusal(FailCode.StoppedByHuman, stop_reason) |
| Halted | 11 | stop_reason == "cancel_request" | Refusal(FailCode.Cancelled, stop_reason) |

The set of `stop_reason` has 12 values; Halted covers 11, the twelfth (`""`) is taken off by the `Except` line. The values `pause_halt` and `cancel_request` are required by the "Pause" fragment; both rows exist (No. 10 and No. 11). The cost limit has no code of its own (`cost_limit` leads to `MaxTokens`, decision 7 of the source).

## Primitives

| name | parameters | result | class | reads | writes |
|---|---|---|---|---|---|
| time_now | — | int | reading | — | — |
| reply_validation | — | ReplyCheck | reading | reply_text, reply_artifact, agent_request; objects: session files | service record "form remarks" (read by turn "fix") |
| close_agent_turn | — | — | irreversible | — | — |

`time_now` is milliseconds of the epoch. `reply_validation` is measured by the executor before the ReplyValidation fork: the form of the reply is valid, violated, or the reply is empty; the form remarks stay with the executor and do not enter the data. `close_agent_turn` tells the transport about the cancellation of the open turn, including one held until the permission decision; it runs as the last stage of fixation and may be repeated without harm.
