# Definitions: cycle_arithmetic

- definitions_version: 1
- format: 2.12
- language: en

## Types
—

## Constants
—

## Definitions

define ceiling_reached(pass_number int>=1, origin int>=1, limit int>=0) -> bool =
  (pass_number - 1) - origin + 1 >= limit
