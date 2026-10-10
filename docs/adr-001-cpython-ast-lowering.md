# ADR 001: Lower pokie through Python ASTs

## Status

Proposed. The drafting basis selects this direction; semantic and packaging
evidence remain required before implementation ratification.

## Date

2026-10-09.

## Context and problem statement

Pokie adds record rules and semantic capture patterns to Python-shaped
programs. Python library reuse is part of the product concept. A bespoke
execution engine would create additional compatibility obligations before the
language demonstrates value.

## Options considered

The comparison in `docs/pokie-design.md` §2 covers Python source templates, AST
lowering, a Rust state machine, and RustPython execution.

## Proposed direction

Implement the initial compiler in Python. Preserve pokie constructs in an
explicit IR, lower validated IR to Python ASTs, and compile/execute through
CPython. Python documents AST compilation into code objects.[^1]

## Consequences

The compiler owns lexical boundaries, binding analysis, generated-name hygiene,
and source maps. CPython owns ordinary execution and imports. This saves
implementing Python semantics, but does not eliminate pokie's semantic
verification obligations. Native acceleration requires profiles and equivalence
evidence; the runtime version matrix requires a separate distribution decision.

[^1]: [Python AST documentation](https://docs.python.org/3.14/library/ast.html),
    accessed 2026-10-09.
