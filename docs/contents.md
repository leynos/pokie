# Documentation contents

[Documentation contents](contents.md) is the index for pokie's documentation
set.

## Product definition and delivery

- [Terms of reference](terms-of-reference.md) defines users, goals,
  non-goals, assumptions, and success evidence.
- [Context](context.md) defines domain vocabulary and evidence statuses.
- [Technical design](pokie-design.md) specifies the proposed language,
  compiler, execution semantics, and verification decisions.
- [Design contracts](design-contracts.md) supplies canonical proposed IR,
  adapter, CLI, example, and pipeline artefacts.
- [Roadmap](roadmap.md) sequences GIST delivery slices and decision gates.

## Proposed decision records

- [ADR 001: CPython AST lowering](adr-001-cpython-ast-lowering.md)
  records the initial compiler/execution direction and alternatives.
- [ADR 002: Execution scope and lifecycle](adr-002-execution-scope-and-lifecycle.md)
  records persistent scope, binding commit, and control/finalization policy.
- [ADR 003: Pattern adapter resolution](adr-003-pattern-adapter-resolution.md)
  records registry resolution and explicit rejection outcomes.

## Project guides

- [Repository layout](repository-layout.md) describes current paths and
  separates the scaffold from proposed compiler components.
- [User guide](users-guide.md) explains how to use the generated project and
  its public build and test commands.
- [Developer guide](developers-guide.md) explains the contributor workflow and
  points maintainers to script automation standards.
- [Documentation style guide](documentation-style-guide.md) defines the
  spelling, structure, Markdown, Architecture Decision Record (ADR), Request
  for Comments (RFC), and roadmap conventions used by this documentation set.

## Engineering practice

- [Complexity antipatterns and refactoring strategies](complexity-antipatterns-and-refactoring-strategies.md)
  explains cognitive complexity, the bumpy-road antipattern, and refactoring
  approaches for maintainable code.
- [Local validation of GitHub Actions with act and pytest](local-validation-of-github-actions-with-act-and-pytest.md)
  explains how to validate workflow behaviour locally before relying on remote
  Continuous Integration (CI) runs.
- [Scripting standards](scripting-standards.md) explains the preferred Python
  scripting stack, command execution patterns, and test expectations for helper
  scripts.
