# Machine: Router

- machine: Router
- machine_version: 1
- format: 2.25
- language: en

The exhaustion of a fork (spec 4.1, AL-57). The fork `Pick` compares one datum with all the values of its enumeration and has no row `else`: the type proves that a row is always found. The fork `Measure` compares
a number, the type proves nothing, so its last row is `else` and it writes `machine_error("fork_no_match", fork: "Measure")` and leads nowhere: the machine ends in `Errored`, the executor
journals `fork_no_match`. The tests: `router-*`.

## Types

```
type Mode enum A | B
```

## Input

| name | type | note |
|---|---|---|
| mode | Mode | the way |
| size | int>=0 | the size to measure |

## Data

| name | type | initial | non_decreasing | writes |
|---|---|---|---|---|
| mode | Mode | input.mode | — | rows |
| size | int>=0 | input.size | — | rows |
| route | str | "" | — | rows |
| verdict | str | "" | — | rows |

## States

Initial state: Pick

### Pick — fork
- Reads: mode

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | mode == Mode.A | — | Alpha |
| 2 | mode == Mode.B | — | Beta |

### Alpha — operation

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | immediate | — | route = "alpha" | Measure |

### Beta — operation

| № | Event | Condition | Actions | To |
|---|---|---|---|---|
| 1 | immediate | — | route = "beta" | Measure |

### Measure — fork
- Reads: size

| № | Condition | Actions | To |
|---|---|---|---|
| 1 | size < 10 | verdict = "small"; journal("measured", verdict: "small") | Small |
| 2 | size < 100 | verdict = "large"; journal("measured", verdict: "large") | Large |
| 3 | else | machine_error("fork_no_match", fork: "Measure") | — |

### Small — end
- Reads: route, verdict

### Large — end
- Reads: route, verdict

### Errored — end
- Reads: all_data
- On entry:
  - journal(transition_note);
  - journal(all_data)

## Ends

- Result: str

| end | № | when | response |
|---|---|---|---|
| Small | 1 | true | Response("${route}:${verdict}") |
| Large | 1 | true | Response("${route}:${verdict}") |
| Errored | 1 | true | Refusal(FailCode.NoResult, "the size is out of the table") |
