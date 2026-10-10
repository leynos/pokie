# pokie context

Status: draft v0.1. Updated: 2026-10-09. Audience: project owner, implementers,
and reviewers.

This document defines the vocabulary shared by `docs/terms-of-reference.md`,
`docs/pokie-design.md`, and `docs/roadmap.md`. Definitions describe the
intended product; they do not imply implemented features. The repository
currently contains a generated greeting package.

## 1. Evidence and authority

- **Established:** explicitly stated in the supplied conversation or
  verified in the repository or a cited primary source.
- **Agreed basis:** the documentation scope approved for drafting, including
  Python-fluent shell users, sequential execution, and CPython lowering.
- **Assumption:** a proposition that still needs evidence, with a recorded
  consequence if it fails.
- **Proposed contract:** a precise design choice awaiting implementation
  validation and ratification. Agreement to draft does not certify it.
- **Open question:** an unresolved choice with a named resolution criterion.
- **Deferred:** excluded from the initial release; promotion requires a
  decision backed by evidence.

The terms of reference govern product scope. The design explains proposed
mechanisms. `docs/design-contracts.md` is the canonical structured contract for
the design. ADRs record individual choices; their status is explicit. The
roadmap sequences evidence and delivery rather than changing scope.

## 2. Domain vocabulary

| Term                   | Meaning                                                                                                               |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Program                | A pokie source file or inline source argument, containing Python statements and pokie constructs.                     |
| Record                 | One input unit delivered by the record reader; initially a decoded line with its line terminator removed.             |
| Field                  | A string derived by splitting a record; `$1` is the first field.                                                      |
| Record text            | `$0`, the entire record, independent of any regex match.                                                              |
| Rule                   | A `when` predicate paired with an action or case suite. Several rules can fire for a record.                          |
| Action                 | Ordinary Python statements executed when a rule predicate succeeds.                                                   |
| Lifecycle block        | `start:` before record processing or `end:` after normal termination.                                                 |
| Regex predicate        | A regular expression searched against record text; success also produces a match.                                     |
| Match                  | The regex result, including the matched substring, positions, and captures.                                           |
| Capture                | A parenthesized regex group's value, normally a string; an unmatched optional group is `None`.                        |
| Capture view           | Either the ordered group tuple or the named-group mapping offered to a case. The whole match is excluded.             |
| Case                   | An ordered structural pattern and optional guard. At most one case action runs within a rule.                         |
| Guard                  | A Python expression checked after a structural match, before bindings are committed.                                  |
| Binding                | An association between a pattern name and a value produced by matching.                                               |
| Pattern adapter        | A registered operation returning an explicit success value or no-match result.                                        |
| Predicate adapter      | Validates a subject and preserves it on success.                                                                      |
| Coercion adapter       | Validates a subject and returns a converted value on success.                                                         |
| Transformation pattern | A proposed pattern that transforms most or all subjects; deferred because it may make later cases unreachable.        |
| No-match               | An ordinary pattern rejection that allows the next case to be attempted.                                              |
| Candidate bindings     | Temporary bindings accumulated during one case attempt, before guard acceptance.                                      |
| Binding transaction    | Commit all candidate bindings after acceptance or discard them after rejection; external side effects are not undone. |
| Persistent scope       | One Python program namespace surviving across records and lifecycle blocks.                                           |
| `next`                 | Pokie control transfer that skips remaining rules for the current record.                                             |
| `exit`                 | Pokie control transfer that stops record processing normally.                                                         |

Table 1: Normative domain vocabulary for the proposed design.

## 3. Compiler vocabulary

| Term                             | Meaning                                                                                                  |
| -------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Source span                      | Source identity and start/end coordinates belonging to a token or node.                                  |
| Intermediate representation (IR) | Pokie's explicit representation of lifecycle blocks, rules, predicates, patterns, and control transfers. |
| Abstract syntax tree (AST)       | Python's structured representation of expressions and statements, used as the compilation target.        |
| Lowering                         | Translation from validated pokie IR into Python AST nodes.                                               |
| Generated name                   | A compiler-owned identifier inaccessible through normal pokie identifiers.                               |
| Source map                       | Association between generated positions and original pokie spans for diagnostics.                        |
| Reference evaluator              | A deliberately simple interpretation of pokie IR used as an independent oracle for lowering checks.      |
| Differential check               | Run the same bounded program and input through two implementations and compare observable results.       |

Table 2: Compiler and verification vocabulary.

## 4. Boundaries worth preserving

A record is not a regex match. Captures are not fields. A predicate adapter is
not a coercion adapter. Case rejection is not an unexpected exception.
Sequential execution is not a promise of bounded aggregate memory: a user can
deliberately accumulate every record in a Python collection.

The input reader owns input consumption. Python library support means execution
in the selected Python environment, subject to its installed packages and
platform compatibility. It does not imply a package manager, an isolation
boundary, or support for every Python interpreter.
