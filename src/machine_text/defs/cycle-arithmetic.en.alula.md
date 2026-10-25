# Functions: cycle_arithmetic

- functions_version: 1
- format: 2.25
- language: en

## Types
—

## Constants
—

## Functions

fn ceiling_reached(pass_number int>=1, origin int>=1, limit int>=0) -> bool =>
  (pass_number - 1) - origin + 1 >= limit
