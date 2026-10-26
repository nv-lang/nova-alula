# Machine: Stamp

- machine: Stamp
- machine_version: 1
- format: 2.25
- language: en

The probe of the task 225 (Alula 2.25, AL-133, AL-134): `event.at` is the stamp of the event, milliseconds of the epoch; the functions `time_to_text` and `text_to_time` are pure. The test: `stamp.alula.test.json`.

## Data

| name | type | initial | non_decreasing | writes |
|---|---|---|---|---|
| started | int | 0 | — | rows |
| seen | int | 0 | — | rows |
| same_read | bool | false | — | rows |
| seen_text | str | "" | — | rows |
| back | ?int | none | — | rows |
| epoch_text | str | time_to_text(0) | — | rows |
| lo_text | str | time_to_text(-62135596800000) | — | rows |
| hi_text | str | time_to_text(253402300799999) | — | rows |
| leap_text | str | time_to_text(951782400000) | — | rows |
| milli_text | str | time_to_text(1500) | — | rows |
| hi_back | ?int | text_to_time("9999-12-31T23:59:59.999Z") | — | rows |
| lo_back | ?int | text_to_time("0001-01-01T00:00:00Z") | — | rows |
| bad_back | ?int | text_to_time("yesterday") | — | rows |
| no_zone | ?int | text_to_time("2026-10-25T14:20:00") | — | rows |

## Parties

| name | id | kind | profile | signals | counter |
|---|---|---|---|---|---|
| user | user | human(result GateOutcome) | — | message { content str }, close | — |

## States

Initial state: Start

### Start — operation
- On entry: let moment = event.at

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | immediate | — | started = moment | Idle |

### Idle — appeal
- Party: user

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | signal(message { content: word }) | — | seen = event.at; same_read = event.at == event.at; seen_text = time_to_text(event.at); back = text_to_time(time_to_text(event.at)) | same |
| 2 | signal(close) | — | — | Closed |

### Closed — end
- Reads: seen

## Ends

- Result: int

| end | № | when | response |
|---|---|---|---|
| Closed | 1 | true | Response(seen) |
