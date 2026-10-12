# pokie users' guide

This guide covers the current development scaffold and its validation commands.
Pokie's interpreter and command-line interface are not implemented. The
language preview is in `README.md`; proposed user behaviour belongs to
`docs/pokie-design.md` and `docs/design-contracts.md`, pending delivery through
`docs/roadmap.md`.

## Run the scaffold

From the repository root, install development dependencies and run the existing
greeting API:

```bash
uv sync --group dev
uv run python -c 'from pokie import hello; print(hello())'
```

Expected output is `hello from Python`. The current package requires Python
3.14 or newer. This example verifies the scaffold rather than any planned
record-processing behaviour.

## Quality gates

Generated projects use `make all` as the standard local quality gate. It runs
build, formatting, lint, type-check, test, Markdown, audit, and Makefile
validation targets in order:

- `build`: create the local virtual environment and install development
  dependencies with `uv sync --group dev`.
- `check-fmt`: check Python formatting with Ruff and Markdown formatting with
  mdtablefix 0.6.1; when Rust is enabled, it also checks `cargo fmt`.
- `lint`: run Python, repository-wide dead-code and duplication, and GitHub
  Actions checks, plus `lint-rust` when Rust is enabled.
- `typecheck`: run `ty check` over discovered Python files.
- `test`: run pytest and, when Rust is enabled, Rust tests.
- `markdownlint`: lint Markdown and run spelling checks over Markdown and code.
- `nixie`: validate Mermaid diagrams.
- `audit`: run `pip-audit` and, when Rust is enabled, `cargo audit`.
- `validate`: validate the Makefile with `mbake`.

Python targets include tracked and non-ignored, untracked `.py` and `.pyi`
files across production code, tests, scripts, and local GitHub actions. Ruff,
Interrogate, Pylint, and `ty` use this set; Interrogate enforces 100% docstring
coverage across it. The shared `df12-python-lints` v0.4.0 package provides the
Skylos dead-code and duplication helpers. Skylos classifies test paths as entry
points, so pinned Vulture 2.16 also checks test helpers at its 60% minimum
confidence, exempting only `test_*` and `pytestmark` names while checking their
bodies. The duplication checks cover supported source files under `pokie/`,
`tests/`, `scripts/`, and `.github/`; documentation is outside these roots.
`ambrleaks` checks tests, while `yamllint` and `action-validator` validate
workflow and action YAML. Actionlint checks workflows and adapted local
actions, including shell steps through ShellCheck.

Ruff 0.16.8 and ty 0.0.56 are pinned consistently in the Makefile, development
dependencies, and CI. Pylint runs as a pinned release (`PYLINT_VERSION`) through
`uv tool run` on the managed interpreter named by `PYLINT_PYTHON`
(`pypy@3.12`), and a module PyPy cannot parse fails the lint rather than being
skipped.

The spelling target regenerates `typos.toml` from the live shared dictionary
and the `typos.local.toml` overlay on every run, then checks the whole
repository with `--scope all`. Therefore, `typos.toml` is never drift checked
in continuous integration. Run `make spelling` directly when updating
documentation; an ignored local cache remains usable when the shared source is
temporarily offline.

Pytest discovery is limited to the top-level `tests/` tree. Keep generated
project unit tests there rather than in package module directories or
`unittests/` subdirectories, because CI coverage runs through xdist-backed
SlipCover support.

When the Rust extension is enabled, `lint-rust` runs:

- `cargo doc` with warnings denied;
- `cargo clippy` with the generated Clippy configuration; and
- Whitaker with `whitaker --all`.

The generated Makefile never installs Whitaker; it fails with a clear error
when the wrapper is missing. Install Whitaker with `whitaker-installer` (see
<https://github.com/leynos/whitaker>) before running local Rust linting.

## Dependency Auditing

Run `make audit` to check generated project dependencies for known
vulnerabilities. All generated projects run `pip-audit` against the Python
environment created by `uv sync --group dev`. CI skips `make audit` for
Dependabot pull requests; a weekly scheduled audit on the default branch is the
compensating control. Rust-enabled projects also run `cargo audit` from the
`rust_extension` crate directory.

## Scheduled Mutation Testing

The `.github/workflows/mutation-testing.yml` workflow runs mutation testing
daily at 09:30 UTC and can also be started manually from GitHub Actions. Adjust
the generated cron schedule to stagger it against other repositories.

For projects whose minimum Python version is 3.13 or newer, the workflow runs
mutmut against `pokie/`. The Python mutation job is omitted for older baselines
because the shared workflow helpers require Python 3.13 or newer.

## Rust Test Behaviour

Rust-enabled projects use `cargo nextest run` when `cargo-nextest` is
available. If `cargo-nextest` is not installed, the generated `test` target
falls back to `cargo test`. Rust documentation tests still run through
`cargo test --doc`.

If cargo is missing from the local environment, generated Rust test targets
fail early with a clear error instead of falling through to an unusable `cargo`
invocation.

## Local GitHub Actions Validation

The generated Makefile supports optional local workflow validation using
[`act`](https://github.com/nektos/act). When `act` is installed and Docker is
available, pass `WITH_ACT=1` to the `test` target:

```bash
make test WITH_ACT=1
```

Pytest runs first, then the target runs the dedicated wheel smoke workflow
through `make test-act`. The smoke workflow builds a pure Python wheel with the
local action and imports the built package. Static workflow checks run
separately as part of `make lint`; the act validation workflow does not repeat
those checks or the regular test suite. Omitting `WITH_ACT` (or setting it to
`0`) skips act validation; the rest of the test suite runs unchanged.

The runner image defaults to `ghcr.io/catthehacker/ubuntu:act-24.04`. Pass
`ACT_IMAGE=...` to Make to use another compatible local image. The explicit
platform mapping keeps act noninteractive in CI.

## Cleaning Local State

Run `make clean` to remove local build and cache outputs, including `.venv`,
`.uv-cache`, `.uv-tools`, Python cache directories, coverage outputs, and Rust
`target` output when the Rust extension is enabled.
