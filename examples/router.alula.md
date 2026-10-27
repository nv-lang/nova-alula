# Machine: Router

- machine: Router
- machine_version: 1
- format: 2.26
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

| name | type | initial | non_decreasing |
|---|---|---|---|
| mode | Mode | input.mode | — |
| size | int>=0 | input.size | — |
| route | str | "" | — |
| verdict | str | "" | — |

## States

Initial state: Pick

### Pick — fork

| Condition | Actions | To |
|---|---|---|
| mode == Mode.A |  | Alpha |
| mode == Mode.B |  | Beta |

### Alpha — operation

| Actions | To |
|---|---|
| route = "alpha" | Measure |

### Beta — operation

| Actions | To |
|---|---|
| route = "beta" | Measure |

### Measure — fork

| Condition | Actions | To |
|---|---|---|
| size < 10 | verdict = "small"; journal("measured", verdict: "small") | Small |
| size < 100 | verdict = "large"; journal("measured", verdict: "large") | Large |
| else | machine_error("fork_no_match", fork: "Measure") |  |

### Small — end

### Large — end

### Errored — end
- On entry:
  - journal(transition_note);
  - journal(all_data)

## Output

- Result: str

| end | when | response |
|---|---|---|
| Small | true | Response("${route}:${verdict}") |
| Large | true | Response("${route}:${verdict}") |
| Errored | true | Refusal(FailCode.NoResult, "the size is out of the table") |
