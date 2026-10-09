# ADR 002: Preserve one program scope and ordered lifecycle

## Status

Proposed. Ratification requires terms-of-reference Q5's semantic corpus.

## Date

2026-10-09.

## Context and problem statement

Record actions share accumulators and import Python libraries. Separate frames
require explicit synchronization; a function wrapper changes global name lookup.
`next` and `exit` must cross nested user loops without changing ordinary Python
`break` and `continue`.

## Proposed direction

Use one module-like program namespace. Run preamble and `start:` once, rules in
source order for each record, and `end:` once after EOF or pokie `exit`. Abort
without `end:` after unexpected failures. Emit private control signals for
`next` and `exit`, caught at the driver boundary, so Python `finally` blocks
still participate in unwinding.

Accumulate case bindings privately and commit only after guard acceptance. Only
name bindings are transactional; external object mutations persist. See
`docs/pokie-design.md` §§4–5 for exact constraints.

## Alternatives considered

Per-rule frames fragment persistent state. One generated function reduces
frames but changes the scope of imports and definitions. Direct `break` and
`continue` cannot represent record control inside nested user loops.
Unconditional `end:` after errors risks publishing partial aggregates as
complete results.

## Consequences

Module state persists, and ordinary definitions see program globals. Generated
control signals remain observable through broad `BaseException` catches;
trusted programs must not suppress them. Resource cleanup belongs in context
managers. Assignment expressions in guards and record references inside nested
definitions are initially rejected to keep visibility explicit.
