# engine: the state machine engine

The engine is the part of the package `alula` that runs a machine: its events are self-contained: an event carries everything a
machine may use, a machine step is a pure function of the state and the event, and everything that touches the world
(journal, snapshots, the agent, the clock) is done by the engine through effects. This directory is the skeleton of
the engine on Nova, built by **Nova Oracle 0.1.0 on Windows (Clang)**, with tests. Task 091
(`doc/tasks/091-product-engine/` of the CrewHarness repository, where the engine was written and where the numbered tasks below are kept). The real handlers of the effects
(the ACP client and the handler of `Link`, the file `Journal` and `Store`, the PostgreSQL ones) and the chat session machine `ChatSession` that the examples below
use stay in the CrewHarness product (task 144 moved the engine here); this package has the in-memory handlers only (`memory.nv`).
Task 102 (`doc/tasks/102-align-glossary/`) brought the names to the dictionary of the methodology (version 6): `Incoming`, `Link`,
`Transition`, `Environment`, `Waiting`, the journal event with a code and parameters, and the typed state of the machine. Task 099
(`doc/tasks/099-session-server/`) is the session server (`src/server/`): it runs one engine per session and took three small things from the engine (below).

The engine is a SUBSET of the methodology (`unitcraft/ai-dev-methodology`, `state-machine-engine-automaton.md` and the
norms `state-machine-spec.md`, rules 12-25, 31, 35) for the MVP "a chat session with an agent". The dictionary
methodology term -> identifier is [GLOSSARY.md](GLOSSARY.md). The methodology describes the engine in Nova code with
Russian names and says that the code was never compiled; here it is English and compiled, and where Oracle 0.1.0
could not take the methodology as written, the difference is named below.

## Build and run the tests (Windows)

Everything for Oracle 0.1.0 (download, SHA-256, `setup-env.ps1`, Clang) is in
[`spikes/env/README.md`](../../spikes/env/README.md), section 1. In short, in PowerShell, once per session:

```powershell
. C:/work/nova/nova-oracle-0.1.0-windows-x86_64/setup-env.ps1     # the leading dot matters
cd C:/work/alula                                           # the root of the repository (nova.toml is there)

nova test src/engine                # the engine only (types, codec, history, nested calls)
nova test src --jobs 4              # all units of the package
nova test --strict-effects src      # the same, and an effect used without being declared in a signature is an error
```

`nova test` prints one line per unit (`PASS src/engine/codec`), and the checks of a unit only when one fails. To see them all,
run with `--keep-artifacts` and start the test binaries from the newest `nova_tests-<pid>` directory in `%TEMP%` (`t-*/codec.exe`): each prints one line per check and `NN/NN passed`. The first build in a new `target/` also builds libuv (about 30 s); after that a full `nova test src`
takes 12-15 s on the survey machine (47 s with the PostgreSQL units on a container). Lint warnings of dependency packages are not printed here: the package has no dependencies.

## Layout

All `.nv` files are under `src/` (owner's rule 2026-09-07, as in `claude-limits`); tests are `*_test.nv` beside the sources.

| File | What it is |
|---|---|
| `src/engine/types.nv` | `FailCode`, `PartyRequest[T]`, `Reply[R]`, `Rejection`, `PartyResponse[R]`, `EventKind`, `Incoming`, `Transition[S]`, `SendOrder`, `CancelOrder`, `Conclusion`, `JournalParam`, `JournalEvent`, `JournalEntry`, `Snapshot`, `Waiting`, `OpenRequest`, `EngineState[S]` |
| `src/engine/machine.nv` | the protocols `Machine[S]` (`name`, `initial`, `state_name`, `step`, `encode_state`, `decode_state`) and `Environment` (`write_journal`, `order_send`, `order_cancel`, `order_save`, `order_finish`); `Order` and `StepEnvironment`, the environment that records the orders of a step |
| `src/engine/effects.nv` | the effects `Journal` (`write`, `read_all`), `Store` (`save`, `load`), `Link` (`send`, `receive`, `cancel`, `ack`); the clock is the standard `Time` |
| `src/engine/codec.nv` | the journal line and the snapshot as JSON (`journal_line`, `parse_journal_line`, `encode_snapshot`, `decode_snapshot`) |
| `src/engine/engine.nv` | `Engine[M, S]`: `start_engine`, `resume_engine`, `on_arrival`, `dispatch`, `feed`, `pump` |
| `src/engine/memory.nv` | in-memory handlers for tests: `MemoryWorld`, `memory_journal`, `memory_store`, `memory_link`, `memory_time` |
| `src/engine/types_test.nv`, `codec_test.nv` | 23 checks of the types, the environment and the text forms (the old forms of a line and of a snapshot are read) |

The engine does not import any machine: it knows a machine only through the protocol. The demo machine `ChatSession` (module `chat`), the
real handlers of the effects (file journal and snapshots, the ACP link, PostgreSQL) live in the CrewHarness product and come in at the point of start by
`with Journal = ..., Store = ..., Link = ... { ... }`. The engine changed for them in one place only: the effect `Link` got the
operation `ack` (see "Acknowledgement" below).

## The names

The names of the engine are the names of the dictionary of the methodology (version 6); [GLOSSARY.md](GLOSSARY.md) is the list
"term -> identifier -> where", and `doc/tasks/102-align-glossary/mapping.md` the table of every difference with the reason. Short:
the envelope of an event is `Incoming` (the event of a machine is its own `Event`, here `ChatEvent`); the effect of the party is `Link`;
a step returns `Transition[S]` and gives its orders to the `Environment`; a request waits as `Waiting { sent, term }`; the state is typed
(`EngineState[S].state`) and is encoded only at the border of the snapshot; the line of the journal has an `event` (a code and
parameters) and no text.

## How a step goes

`Engine.on_arrival(event)` is one step; the order is the order of rule 13 of the specification:

1. **Stamp.** The creator of an `Incoming` event fills `kind`, `name`, `request` (the request the event answers), `input`;
   the engine adds `id` (`<kind>-<number by the event counter>`), `trace`, `step`, `at` (the clock). After that the event is
   self-contained: nothing is read from outside.
2. **Check.** An event that belongs to a request (`Progress`, `Answered`, `Refused`, `Expired`) must find that request open.
   If not (closed, cancelled, never opened), the event is discarded: the step is its own commit with a `discarded` line, the
   machine does not see it (rule 17; one request - one answer, rule 15).
   A `Progress` event renews the idle term of its request; `Answered`, `Refused`, `Expired` close it.
3. **Step.** `machine.step(state, event, environment)` returns the `Transition[S]` (`Go(state)` or `Stay`); what it wants done it
   gives to the `Environment`, which only records the orders. `step` takes nothing but its arguments: its signature has no effects,
   and Oracle rejects a raw effect call inside it at compile time.
4. **Apply.** The new state is kept in `EngineState.state`; then the orders in the order of giving: `order_send` opens a request
   (`<party>-<attempt>`, the counter of the party only grows, rule 15) and queues it; `order_cancel` closes the open request of the party
   and queues the cancel; `write_journal` and `order_save` become journal lines; `order_finish` records the outcome and cancels what is
   still open (rule 22).
5. **Commit.** The journal lines of the step are written, THEN the snapshot is saved (the snapshot is the commit point).
   Step numbers go 1, 2, 3... without gaps; every line carries the trace, the step, the cause (the id of the event), the name of
   the state after the step, the request id and the time.
6. **Dispatch.** Only after the commit the queued requests and cancels are sent through `Link`, and each send is marked in
   the journal (`request_sent`, `cancel_sent`). `feed` is `on_arrival` + `dispatch`; `pump` sends the pending orders, takes the incoming
    events of the link in the order of arrival (at most 16 per call; fewer when `receive` returns `None`), then makes an
    `Expired` event for each open request whose idle term passed. The finite scheduling quantum lets the server drain visible
    events, service page commands and move to another session even while one link has a backlog; it does not limit a response.

A line of the journal (one JSON object per line, UTF-8 as it is); what happened is an `event`: a code and parameters (a name -> a
string), never a ready text. The Russian text of a line is built from the template of the code by whoever shows the journal
(`state-machine-journal.md` of the methodology); the codes of the product are in [GLOSSARY.md](GLOSSARY.md):

```
{"trace":"t1000-chat-1","step":2,"cause":"input-2","state":"Awaiting","request":"agent-1","at":1000,"event":{"code":"request_ordered","params":{"party":"agent","attempt":"1"}}}
{"trace":"t1000-chat-1","step":2,"cause":"dispatch","state":"Awaiting","request":"agent-1","at":1000,"event":{"code":"request_sent","params":{"attempt":"1"}}}
```

A line of the old form (`"kind":"sent","text":"attempt 1"`) is still read: the code is the one the engine writes now for that kind (`sent` -> `request_sent`,
`restart` -> `engine_resumed`, ...; a `note` stays `note`), the text is the parameter `text`, the key at the end of an `event` text (` src=<key>`) is the parameter `source` -
so a restart reads the marks of a journal that the old engine wrote and sends nothing again. A snapshot keeps
the state of the machine as an object under `state`; a snapshot of the old form (`machine_state` as an encoded text, `idle_term` and `deadline`
of an open request) is still read.

## What the session server took from the engine (task 099)

- **The input in the journal.** The journal event `event_accepted` carries the input of the event as the parameter `input` (only when it is not
  empty; a journal written before reads the same, with an empty input). The journal stays a structure, a code and parameters, with no text of
  its own; and with the input the journal alone tells the whole conversation again after a restart.
- **`Engine.take_events()`** hands out the events accepted since the last call, stamped (id, trace, step, time), in the order of acceptance; a
  discarded event (rule 17) is not among them. The server turns them into the lines of the page.
- **`Engine.history()`** (effect `Journal`) rebuilds the same stamped events from the committed journal: the `event_accepted` lines of the trace,
  without the events the engine discarded (`reply_discarded`) and without the lines of a step that never committed (a restart took its number over,
  or it is newer than the snapshot). `EventKind.parse` is the inverse of `EventKind.name`.
- **A many-turn machine.** `dialog_session` (module `chat`) goes back to `Idle` after an answer, a refusal, a timeout or a cancel of the turn and never
  gives `order_finish`; the next message opens `agent-2`. Tests with the deaths of rules 13 and 34(e): `src/server/dialog_test.nv`.
- **`MemoryWorld.journal_entries()`** was `entries()`; the name collided with `EmbeddedDir.entries` of the prelude (see `spikes/env/README.md`, "Also met in task 099").

## Restart by a repeated entry

`resume_engine[S, M](machine, id)` loads the snapshot, reads the journal, and makes one more step (`restart-<n>`, its own number and
journal line `engine_resumed`; the trace stays). It re-sends nothing that was already sent (rule 12): the open requests with a `sent` mark in the
journal are not sent again. A request that was committed but never sent (the process died between the commit and the send) has no
mark and is sent by the next `dispatch`/`pump`, once. Open requests stay open across the restart, so the answer of the agent is
accepted after it; a repeated answer to a closed request is discarded and journaled.
Journal lines of a step newer than the snapshot (the process died between the journal write and the snapshot save) are the lines of
a step that did not commit; they are ignored and counted in the `restart` line.
The restart is a step of its own and takes the number of the step that died, so the dead lines and the restart line share a number; the
restart line stands after them, and a later restart ignores every line that stands before a restart line and has its number or a
greater one (task 095: without that, an event line of a dead step counted as committed after the second restart and its
acknowledgement lost the event).

Tests: after the request was opened; after the answer; between the commit and the send; the attempt counter; no snapshot.

## Writing another machine

A machine is any type with the methods of `Machine[S]` (the match is structural, no `impl`); `S` is its typed state:

```nova
type Machine[S] protocol {
    @name() -> str
    @initial() -> S
    @state_name(state S) -> str                    // for the journal
    @step(current S, event Incoming, mut environment Environment) -> Transition[S]
    @encode_state(state S) -> str                  // the border of the snapshot
    @decode_state(text str) -> Option[S]
}
```

The engine keeps the typed state (`EngineState[S].state`) and asks the machine for its text only to save a snapshot and for its
decoding when it resumes. `ChatSession.step` maps the `Incoming` event to a `ChatEvent`, calls the typed core `chat_step` and returns the
`Transition[ChatState]`. The orders go to the environment: `write_journal(journal_event(code, params))`, `order_send(SendOrder)`,
`order_cancel(CancelOrder)`, `order_save()`, `order_finish(Conclusion)`. The free functions of the engine are called with their type arguments
written out: `start_engine[ChatState, ChatSession](chat_session(), "chat-1")` (see "Oracle 0.1.0").

## What is covered of the methodology, and what is not

Covered (the numbers are the rules of `state-machine-spec.md`):

- 6, types as detailed as the machine uses them; 8, only the executor writes the journal and the snapshot, a step returns a transition and gives orders;
- 11 in part: a step reads only the state and the event - by the signature of `step` (no effects) and by the tests (a different
  envelope or clock of the same content gives the same result);
- 12, a repeated entry sends nothing to a party whose request is open; 13, the commit order (journal, snapshot, then the send),
  numbers of steps without gaps; 14 in part, a reply is checked against the open requests at arrival; 15, request id
  `<party>-<attempt>`, a counter that is never reset; 16, three outcomes (answer, refusal, no answer in time) and the closed list
  of failures; 17, a foreign or late reply is discarded and journaled; 18 in part, cancel of a request (without "restart request");
- 22 in part, the snapshot keeps the open requests, the counters and the trace; the end cancels what is open;
- 31, the trace envelope: trace, step number, event counter, cause, request id, time in every journal line;
- 35 in part, the end of the machine is an `Answer` or a `Refusal` with a code of the list.

Not in the MVP (the list for the next tasks):

- 19-21 and 28: gates of a human, sets of requests to several parties, the limit of simultaneous requests;
- 23-24 and 36: "stop of a human", "continue", the PAUSE state and its fragment; the signals are not there, `StoppedByHuman` comes
  only from the user's `Cancel` word of the chat machine;
- 35 beyond the end: calling a machine from another machine, passing stop/continue/cancel down, `Cancelled` (cancelled by the
  parent) is in the list and never produced;
- 14 beyond the acceptance at arrival: the split into open and accepted requests, the fingerprint of the object a result is written
  to, finishing an accepted file after a crash; 18: "restart request" with a new id; 27: the end ERROR for a defect of a machine (a
  machine that cannot decode its state leaves a note and does not move); the preparation at resume; irreversible actions of
  the machine (archive, write permission);
- 22 as written for parties that are roles: there open requests of a dead executor are cancelled at restart; here they stay open,
  as the task fixes (the agent lives outside the process). Nested machines are resumed by repeating their request: not here;
- (done in task 095) a persisted queue of incoming events: see "Acknowledgement of incoming events" below;
- failures of the handlers: `Journal.write`, `Store.save` return plain values; a real handler that cannot write stops the process,
  the step is then not committed (rule 13);
- `FormNotFixed`, `MaxTokens`, `MaxTurnRequests`, `CeilingReached` are in the closed list and are not produced by the chat machine;
- the `order_save` order is accepted and leaves a `snapshot_ordered` journal event, but every commit saves the snapshot anyway: in the MVP the
  order adds nothing (doubtful; it is kept because the task lists it among the outputs);
- the model usage accounting, the real clock cycle, the sets of parties, security.

## Oracle 0.1.0: what shaped the code

What the engine uses and Oracle compiled without a workaround: records, sum types, generic records `PartyRequest[T]`, `Reply[R]`,
`PartyResponse[R]`, `Engine[M, S]`, `EngineState[S]`, `Transition[S]`, a structural protocol with a bound `M Machine[S]` (with the type
arguments of the free functions written out), a protocol parameter `mut environment Environment`, effects with handlers captured over mutable
memory (`with Journal = ..., Store = ..., Link = ..., Time = ... { ... }`), the standard `Time` effect with a hand-made
handler, `std.encoding.json` (writes Cyrillic as it is), `?` on `Option`, test blocks in peer files, `--strict-effects`.

What needed a workaround (reproductions: `spikes/env/repro_engine/`, items 8-13 of `spikes/env/README.md`):

- a generic sum type with a `str` variant does not compile -> the sum types of the engine are not generic;
- a generic function bounded by a protocol with type parameters (`Machine[S, B]`, even `Machine[S]`) generates broken C when the type
  arguments are left to be inferred (items 12, 13) -> **since task 102 they are written out** (`start_engine[ChatState, ChatSession](...)`,
  `typed_state_explicit`, item 26), and the machine state is typed; in task 091 it crossed the protocol as encoded text;
- the operator `?` on an `Option` of a sum type inside a generic function breaks the C (`option_try_generic_enum`, item 27) -> `decode_snapshot`
  uses `match`;
- a record literal in the head of a `match` is a syntax error -> a name is bound before the `match`;
- a protocol-typed record field cannot be called through -> `Engine[M, S]` is generic over the machine type;
- a user type named `Outcome` clashes with the prelude's -> the type is called `PartyResponse` (it was `Response`, as in the methodology's own "Types on Nova", until `http` took that name too, below);
- user types named `Request` and `Response` clash with the types of `http`, which every program with Polaris has -> `PartyRequest` and `PartyResponse` (task 099, `spikes/env/repro_server/`, `user_request_vs_http`);
- a user type named `Output` clashes with `std.os.Output` as soon as a module of the program imports `std.os` (the ACP client
  does) -> the type was called `StepOutput` (task 095, `spikes/env/repro_acp/`, `user_output_vs_std_os`); task 102 removed it (the machine
  gives its orders to the `Environment`);
- the nested pattern `Some(Answer(reply))` over a generic payload compiles to a NULL pointer -> two nested `match`es in the tests;
- `Request[str] { ... }` (a generic type with arguments in a record literal) is not parsed, and some anonymous record literals
  (`push({ ... })`) are rejected by the code generator -> small constructor functions (`request_of`, `reply_of`);
- error text is cut to 600 characters unless `NOVA_DEBUG_RUN_DUMP=1` is set; `str.len()` is gone (`byte_len()`), `"a" + "b"` is
  rejected (`"${a}${b}"`), a handler operation must be fully typed (`name(args) -> T { ... }`), a protocol method comment must be `//`;
- a file in a folder is one module with its peers, the module name is the path from the source root with the package prefix
  (`alula.engine`), tests are peers and are compiled with the module they test (an importer compiles them too).

## Acknowledgement of incoming events (task 095)

An event that `Link.receive` returns is the handler's until the engine confirms it. The creator of an incoming event may put a
source key into `Incoming.id` (`Incoming.from_source(key, event)`; the engine stamps its own id as before). `pump` accepts the event
(journal lines, snapshot: the commit) and only then calls `Link.ack(key)`; the key is kept in the journal event of the step
(`event_accepted`, the parameter `source`). A restart (`resume_engine`) collects the keys of the committed `event_accepted` events and
`dispatch` tells the handler again (`ack` is idempotent) - the process may have died between the commit and the `ack`. A handler
that keeps what it handed out (the ACP client, with its inbox file) hands out again after a restart exactly what was not
acknowledged: an event is taken once. An event without a key is never acknowledged. The memory handler remembers the keys
(`MemoryWorld.acked`) and the number of saved snapshots at each ack (`saves_at_ack`, for the test of the order). Details and
tests: [`src/acp/README.md`](https://github.com/unitcraft/crew-harness/blob/main/src/acp/README.md), "How an event is acknowledged".

## Where it goes next

1. (done in task 095) `src/acp/` and `src/storage/`.
2. (done in task 099) The session server (`src/server/`, [README](https://github.com/unitcraft/crew-harness/blob/main/src/server/README.md)): HTTP and WebSocket on Polaris, one `Engine` per session, restart of the
   service by `resume_engine` for every session with a snapshot.
3. From the "not in the MVP" list in the order the product needs it: stop/continue of a human (rules 23-24), a set of parties,
   nested machines.
