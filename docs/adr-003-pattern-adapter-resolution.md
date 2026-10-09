# ADR 003: Resolve adapters through an explicit registry

## Status

Proposed. Custom registration syntax remains open under terms-of-reference Q4.

## Date

2026-10-09.

## Context and problem statement

The chat proposes `int(uid)` as a conversion pattern, but Python already uses
callable-shaped syntax for class patterns. Dynamic guessing would make matching
depend on runtime rebinding. Treating all exceptions as rejection would hide
extension defects.

## Proposed direction

Freeze an explicit adapter registry before compilation. Registered names take
precedence in pattern position; other class patterns retain Python meaning.
Expression calls retain ordinary name lookup. An adapter returns `Match(value)`
or `NoMatch`, with false-like values remaining valid successes. Built-in
wrappers convert only documented input rejection into `NoMatch`.

The canonical interface is `docs/design-contracts.md` §3; operational semantics
are in `docs/pokie-design.md` §6. A registration spike must avoid executing the
program preamble before static validation. An explicit API or manifest is a
candidate; `@pattern` in program source is deferred.

## Alternatives considered

Replacing every class pattern with coercion breaks Python structural matching.
Guessing based on runtime callable type makes compiled meaning unstable. Using
`None` or truthiness for failure loses valid converted values.

## Consequences

Compilation records adapter identities, so later expression-name rebinding does
not alter pattern meaning. Catalogue additions need explicit subject, output,
and rejection contracts. Predicate preservation and coercion stay distinct.
Public registration cannot ship until phase ordering is resolved.
