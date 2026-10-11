# Developer guide

This guide explains the contributor workflow for pokie's development scaffold.
The interpreter is not implemented. Begin with the
[technical design](pokie-design.md), `docs/pokie-design.md`, the
[design contracts](design-contracts.md), `docs/design-contracts.md`, and the
[repository layout](repository-layout.md), `docs/repository-layout.md`. The
[contents](contents.md) indexes proposed decision records and the roadmap.

## Design and interface maintenance

Record semantics and compiler boundaries live in the design and structured
contracts, not in generated scaffold modules. Proposed ADRs require explicit
ratification and evidence; do not describe their capabilities as delivered.
Update the users' guide when a roadmap slice ships user-visible behaviour.

Before adding runtime helpers, search for existing equivalents. New helpers
must serve a defined compiler or execution feature, with scope and reuse policy
documented in the design/contracts. Keep extension registration interfaces
synchronized with ADR 003 and this guide when they are selected.

## Local workflow

The public entrypoint for formatting, linting, type checking, tests, Markdown
checks, dependency auditing, and Makefile validation is `make all`. It runs
these targets in sequence. Narrower Make targets may be used while
investigating a failure, then reconcile the changes with the aggregate gate.

The lint standards follow
[`leynos/episodic` at `e43240306dec55437547c8f43cf0c6a5ed040fd2`](https://github.com/leynos/episodic/tree/e43240306dec55437547c8f43cf0c6a5ed040fd2),
using the shared `df12-python-lints` v0.4.0 package and its `df12-skylos` and
`df12-duplication` helper commands. Keep those helpers as shared tools; do not
copy their implementation scripts into this repository. The `df12-duplication`
helper installs the configured Nose 0.20.0 detector before running its
repository checks.

`PYTHON_TARGETS` discovers tracked and non-ignored, untracked `.py` and `.pyi`
files across the repository, including tests, scripts, and local GitHub
actions. Ruff, Interrogate, Pylint, the DF12 Pylint rules, and `ty` cover those
Python files. Interrogate requires 100% docstring coverage across that full
target set. `ambrleaks` checks the test suite.

The shared Skylos command scans the checkout for dead code. Skylos 4.33.2
classifies test paths as entry points, so pinned Vulture 2.16 also checks
`tests/` at its 60% minimum confidence. It exempts only `test_*` and
`pytestmark` names, while still checking their bodies. The shared duplication
command checks supported source files under `pokie/`, `tests/`, `scripts/`, and
`.github/`; documentation is outside its roots. These source tools do not
analyse YAML syntax. `yamllint` checks YAML under `.github`, `action-validator`
checks local action manifests, and Actionlint checks workflows plus adapted
local actions; Actionlint also checks shell steps through ShellCheck. The local
`scripts/action_workflow.py` adapter converts composite action inputs and steps
into a workflow for Actionlint validation. Reuse it for this conversion
purpose; it is not a source scanner or replacement for the shared lint tools.
Its PEP 723 metadata declares the Cyclopts and PyYAML dependencies; run it with
`uv run --script scripts/action_workflow.py ACTION` outside the project
environment.

Ruff and `ty` are pinned to `0.16.8` and `0.0.56`, respectively, in the
Makefile, development dependencies, and Continuous Integration (CI). Bump
either deliberately and update all locations together, then resolve any new
diagnostics in the same change.

Mutation runs copy `scripts/`, `.github/`, `Makefile`, and `pyproject.toml`
through `[tool.mutmut] also_copy` so the tooling-contract tests retain their
inputs in the isolated mutation tree.

`make check-fmt` checks Python formatting with Ruff and Markdown formatting with
`mdtablefix` v0.6.1. CI installs that formatter through the shared
`install-mdtablefix` action. Run `make fmt` to apply both formatters.

Run `make audit` as the dependency vulnerability gate. It runs `pip-audit` for
Python dependencies, and Rust-enabled projects also run `cargo audit` from the
`rust_extension` crate directory.

## Automation scripts

The [Scripting standards](scripting-standards.md) document provides guidance
for adding or updating helper scripts. New and updated scripts are expected to
use `Cyclopts` for command-line interfaces, `cuprum` for typed and
catalogue-bound external command execution, `pathlib` for filesystem paths, and
`cmd-mox` for tests that mock external executables.

Script changes should update the scripting guide when they introduce a new
convention, command catalogue, testing pattern, or operational expectation that
future contributors need to follow.

## GitHub Actions

The generated repository includes GitHub Actions workflows and local composite
actions under `.github/`.

- `.github/workflows/ci.yml` runs on pushes to `main` and on pull requests. It
  sets up Python 3.14, installs `uv`, validates the Makefile with `mbake`, and
  runs the formatting, lint, type-check, Markdown, spelling, and dependency
  audit gates. Ruff 0.16.8 and ty 0.0.56 are pinned in the workflow to match
  the Makefile and development dependencies. Markdown formatting is checked
  with mdtablefix 0.6.1, installed through the shared `install-mdtablefix`
  action. The audit is skipped for Dependabot pull requests via
  `if: github.actor != 'dependabot[bot]'`; a scheduled workflow provides the
  compensating check. Coverage generation is delegated to the shared coverage
  action.
- `.github/workflows/audit.yml` runs `make audit` against the default branch
  weekly as the compensating control for the Dependabot CI bypass.
- `.github/workflows/act-validation.yml` installs `act`, checks Docker
  availability, and runs only the dedicated wheel smoke workflow through
  `make test-act`. `make test WITH_ACT=1` also selects this smoke test locally
  after pytest. Static workflow checks already run in `make lint`, so the act
  workflow does not repeat the CI lint and test suite. `ACT_IMAGE` defaults to
  `ghcr.io/catthehacker/ubuntu:act-24.04` and is passed explicitly to act so
  noninteractive CI never prompts for a runner image.
- `.github/workflows/act-smoke.yml` builds a pure Python wheel using the local
  wheel action and imports the built package. This isolates the behaviour that
  act validates from the rest of CI.
- `.github/workflows/release.yml` publishes wheels when a `v*.*.*` tag is
  pushed. It builds a pure Python wheel, creates a GitHub release with
  generated release notes, downloads wheel artefacts, and uploads them to the
  tag release.
- `.github/workflows/build-wheels.yml` is a reusable workflow for extension
  builds. It accepts a Python version and builds wheels across Linux, Windows,
  and macOS architectures via `.github/actions/build-wheels`.
- `.github/workflows/get-codescene-sha.yml` is manually dispatched. It fetches
  the CodeScene coverage CLI installer, computes its SHA-256 digest, and writes
  the result to the `CODESCENE_CLI_SHA256` repository variable.

- `.github/workflows/mutation-testing.yml` runs daily at 09:30 UTC and supports
  manual dispatch. It delegates to reusable workflows from
  `leynos/shared-actions`; stagger the generated cron schedule before adopting
  it alongside other repositories.

  The mutmut job is generated only when the minimum Python version is 3.13 or
  newer because the shared workflow helpers require Python 3.13 or newer.

- `.github/actions/build-wheels` wraps `cibuildwheel` with `uvx` and uploads
  architecture-specific wheel artefacts.
- `.github/actions/pure-python-wheel` builds a pure Python wheel with
  `uv build --wheel` and uploads the resulting artefact.
- `.github/dependabot.yml` enables dependency update pull requests for GitHub
  Actions and Python packages. Rust-enabled projects also receive Cargo updates.

The `CS_ACCESS_TOKEN` secret must be configured when CodeScene coverage upload
is required. The `CODESCENE_CLI_SHA256` variable should be populated using the
refresh workflow, so CI can verify the downloaded CodeScene installer before
upload.

## Shared spelling configuration

Run `make spelling` to enforce en-GB-oxendict spelling in Markdown and code.
The shared `typos-config-builder` v0.1.2 gate regenerates `typos.toml` from the
live estate dictionary and the `typos.local.toml` overlay, then checks the
whole repository with `--scope all`. A word added to the shared dictionary
therefore needs no change here, and `typos.toml` must never be drift checked in
continuous integration. It is a generated artefact and is ignored by Git, as is
the local cache that keeps the gate usable when the authority is temporarily
unreachable. Add only narrow project-specific terms and exclusions to
`typos.local.toml`; its `markdown_only` patterns apply only to Markdown, so
they do not narrow code checking. Never edit generated `typos.toml` by hand.
