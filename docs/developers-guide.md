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
Store architectural decision records as `docs/adrs/adr-nnnn-title-slug.md` and
requests for comments as `docs/rfcs/rfc-nnnn-title-slug.md`, where `nnnn` is
the four-digit, zero-padded sequence number and `title-slug` is the title in
kebab case; the [documentation style guide](documentation-style-guide.md)
defines the required sections. Update the user's guide when a roadmap slice
ships user-visible behaviour.

Before adding runtime helpers, search for existing equivalents. New helpers
must serve a defined compiler or execution feature, with scope and reuse policy
documented in the design/contracts. Keep extension registration interfaces
synchronized with ADR 0003 and this guide when they are selected.

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
`.github/`; documentation is outside its roots. A considered duplication
exception is recorded in `[[tool.duplication_gate.allow]]` in `pyproject.toml`,
naming every location in its family and why the copy stays; add one only when
the repeated call is a public entry point used in genuinely different roles,
never to avoid extracting shared logic. These source tools do not analyse YAML
syntax. `yamllint` checks YAML under `.github`, `action-validator` checks local
action manifests, and Actionlint checks workflows plus adapted local actions;
Actionlint also checks shell steps through ShellCheck. The local
`scripts/action_workflow.py` adapter projects composite action inputs and steps
into a workflow for Actionlint. The `lint-actions` loop runs `action-validator`
for every action, then pipes the adapter's output to Actionlint only when it
contains a composite workflow; valid Node and Docker actions produce no
projection. The adapter reports file, YAML, and minimal-shape errors with the
manifest path. Its pure projection helper is scoped to this Actionlint bridge,
not a general action schema validator. PEP 723 metadata declares its Cyclopts
and PyYAML dependencies; run it with
`uv run --script scripts/action_workflow.py ACTION` outside the project
environment.

Ruff and `ty` are pinned to `0.16.8` and `0.0.56`, respectively, in the
Makefile, development dependencies, and Continuous Integration (CI). Bump
either deliberately and update all locations together, then resolve any new
diagnostics in the same change.

Mutation runs copy `scripts/`, `.github/`, `Makefile`, `pyproject.toml`,
`docs/`, and the committed coverage baseline through `[tool.mutmut] also_copy`
so the tooling-contract tests retain their inputs in the isolated mutation tree.

`make check-fmt` checks Python formatting with Ruff and Markdown formatting with
`mdtablefix` v0.6.1. CI installs that formatter through the shared
`install-mdtablefix` action. Run `make fmt` to apply both formatters.

Run `make audit` as the dependency vulnerability gate. It runs `pip-audit` for
Python dependencies, and Rust-enabled projects also run `cargo audit` from the
`rust_extension` crate directory.

## Corpus harness

The representative corpus harness lives under `tests/job_corpus/`. Its frozen
values and pure policies describe corpus evidence. `policy.py` provides the
validation interface; `register_policy.py` owns decision-register deadlines,
owners, and evidence-set checks, re-exported through `policy.py`. This feature
split keeps the documented interfaces within the code-file size limit.

Reuse these helpers within the corpus harness. Keep document parsing and
process execution in adapters, and supply loaded values to `audit_corpus`. The
domain boundary test includes every implemented policy module, including
`register_policy.py`, and rejects adapter dependencies through absolute or
relative imports. The checker normalizes `pathlib` import aliases before
inspecting access: `pl.PurePosixPath` remains valid after
`import pathlib as pl`, while `pl.Path.cwd()` is rejected under the same
pure-path restriction.

The session-scoped `reference_implementation` fixture selects a loaded job and
its reference by script kind, and shares that pair across policy, comparison,
and audit tests. Keep this fixture within the corpus tests.

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
- `.github/workflows/coverage-main.yml` is the one CodeScene publisher; see
  "CodeScene coverage publication" below.

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

The `CS_ACCESS_TOKEN` secret belongs in the `codescene` environment, whose
deployment policy admits `main` alone. Without it the publisher skips the
upload, writes a warning and still succeeds. If a repository- or
organization-level `CS_ACCESS_TOKEN` also exists, move it into the environment
and delete the broader copy: GitHub makes broader secrets available to
workflows outside the environment, and the publisher falls back to them when
the environment has none.

### Coverage baseline

The coverage ratchet compares each run with a committed, one-line percentage.
`.coverage-baseline-v2.python` records the Python line coverage measured on the
branch that introduced the representative job corpus. The earlier
`.coverage-baseline.python` was seeded at 98.88% by the near-empty scaffold on
`main`, and the harness could not hold that figure once real test code existed.
Both `.github/workflows/ci.yml` and `.github/workflows/coverage-main.yml` pass
the new file as `baseline-python-file`, and `tests/test_workflow_contracts.py`
holds both workflows to that path.

The shared coverage action derives its baseline cache version from the
configured baseline paths, so naming a new path restores no cached archive and
starts the ratchet from the committed figure. That is the supported way to
bootstrap a baseline: add a versioned file (`-v2`, `-v3`, and so on), point
every ratchet workflow at it, and commit the measured value in the same change.
Do not rewrite the previous baseline in place: its cache entry would still
match and would override the committed value. No workflow may name a retired
path again.

Re-measure with the hosted command before committing a new baseline:

```sh
uv run --with slipcover python -m slipcover --branch --xml \
  --out coverage.xml -m pytest -v -n auto
```

Filter the report to the first-party directories before counting. The XML
records every imported file, and an existing project `.venv` can appear because
`uv run --with` adds it to the import path, while the action's private
`.venv-coverage` does not appear in its report. Count `<line>` elements under
`<class>` entries whose `filename` starts with `pokie/`, `scripts/`, or
`tests/`, then quantize the covered-to-total ratio half-up to two decimal
places. The action tolerates a one-point fall, so ordinary runner variation
does not fail a pull request.

### Hosted CI and act diagnostics

The Act validation workflow pins `act` v0.2.89 and checks the release archive's
SHA-256 digest before installation. The upstream
[command-injection advisory](https://github.com/advisories/GHSA-xmgr-9pqc-h5vw)
and
[cache-injection advisory](https://github.com/advisories/GHSA-x34h-54cw-9825)
set v0.2.86 as the minimum fixed release. The wheel smoke workflow uses the
absolute path `${PWD}/smoke-env/bin/python` to normalize the virtual
environment prefix without resolving the interpreter symlink.
`UV_LINK_MODE=copy` lets `uv` use cached files across the container's cache and
target filesystems.

The successful
[CI run 38180404469](https://github.com/leynos/pokie/actions/runs/38180404469)
and
[Act run 38180404428](https://github.com/leynos/pokie/actions/runs/38180404428)
show these diagnostics alongside passing jobs:

- `SlipCover` is imported before pytest loads its assertion-rewrite hook when
  coverage starts pytest through `python -m slipcover`. The resulting rewrite
  warning describes instrumentation order; passing tests remain the test result.
- Node 20 runtime notices, `DEP0040`, and `DEP0169` come from pinned external
  JavaScript actions and their dependencies. Keep the warning visible rather
  than filtering it broadly.
- The pinned
  [shared coverage action](https://github.com/leynos/shared-actions/blob/5a99aed78ce68dcebd3052b75c31e6f173162b1e/.github/actions/generate-coverage/action.yml#L345)
  caches `~/.cache/uv`, while setup-uv supplies a different effective
  `UV_CACHE_DIR`. That mismatch can omit the cache. Its restore and post-job
  save also reserve the same key; an explicit save can succeed before the
  post-job reservation warning. Both are cache issues owned by
  `leynos/shared-actions`. They affect caching, not the coverage ratchet
  result; see the action's
  [restore](https://github.com/leynos/shared-actions/blob/5a99aed78ce68dcebd3052b75c31e6f173162b1e/.github/actions/generate-coverage/action.yml#L246)
  and
  [save](https://github.com/leynos/shared-actions/blob/5a99aed78ce68dcebd3052b75c31e6f173162b1e/.github/actions/generate-coverage/action.yml#L450)
  steps.
- Act may not resolve GitHub's synthetic pull-request merge commit to a branch
  or tag because checkout leaves it detached. Identify the tested candidate
  from workflow run metadata and verified merge parents, not the displayed
  branch name; the warning does not by itself indicate a failed smoke test.

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

## CodeScene coverage publication

Main owns CodeScene (CV-005). Nothing a pull request can start talks to
CodeScene or holds its credential.

- **Pull requests** (`.github/workflows/ci.yml`) run the tests, then measure
  coverage and ratchet it with the shared `generate-coverage` action over the
  whole tree, as it measured before the move. The report is not uploaded
  anywhere.
- **Main** (`.github/workflows/coverage-main.yml`) is the one publisher. It
  runs on each push to `main` and on manual dispatch (which must target `main`:
  the `codescene` environment, whose deployment policy admits `main` alone,
  refuses a dispatch from any other branch before the job runs). It generates
  the same coverage, writes the ratchet baseline that pull requests compare
  against, and uploads through the shared `upload-codescene-coverage` action.
  With no `CS_ACCESS_TOKEN` in the environment, the upload step is skipped and
  a separate step writes a warning, so the run still succeeds and the publisher
  works before a CodeScene project exists.
- **Known exception.** Merges made with `GITHUB_TOKEN`, such as Dependabot
  automerge, fire no push event, so they reach the publisher only through a
  later push or a manual dispatch. A manual dispatch uploads coverage but does
  not save the ratchet baseline, which the shared action writes only on a push
  to `main`; pull requests keep comparing against the older baseline until a
  later push advances it.

The `generate-coverage` selection in both workflows must match field for field
(format and interpreter), and `.github/cv005.toml` names the interpreter.

### The CV-005 contract check

`make test-workflow-contracts` runs the shared `cv005-contracts` checker
against this repository's workflows. `make all` includes it, and CI runs it.
The checker is fetched from the `leynos/shared-actions` commit named by
`CV005_CONTRACTS_REF` in the `Makefile`, so the first run needs network access.
Always pin a full 40-character commit: a fix to the contract arrives as a pin
bump, never as a local copy of the rules. The command exits 0 when every clause
holds, 1 with one `clause: message` line per violation, and 2 when the tree or
the configuration cannot be read.
