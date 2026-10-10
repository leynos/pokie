# Repository layout

This document describes the current checkout and the responsibilities of its
major paths. Compiler directories have not been created; proposed components
are defined in `docs/pokie-design.md` §7.

| Path               | Responsibility and current status                                                                                      |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| `pokie/`           | Generated package; exports `hello()` through the Python fallback. No interpreter or compiler yet.                      |
| `tests/`           | Top-level scaffold and tooling-contract tests. Future language fixtures, behavioural tests, and snapshots belong here. |
| `docs/`            | Product scope, vocabulary, proposed design/contracts/ADRs, roadmap, and operational guides.                            |
| `.github/`         | Generated CI workflows and local actions.                                                                              |
| `.rules/`          | Detailed development conventions referenced by `AGENTS.md`.                                                            |
| `Makefile`         | Local build, formatting, validation, test, and audit commands.                                                         |
| `pyproject.toml`   | Current Python version, dependency groups, and quality-tool configuration.                                             |
| `typos.local.toml` | Project-specific spelling overlay; `typos.toml` is generated.                                                          |
| `README.md`        | Public entry point with honest readiness and a scaffold example.                                                       |
| `LICENSE`          | ISC licence terms.                                                                                                     |

Table 1: Current paths and ownership boundaries.

Keep tests in `tests/`, group future implementation by feature, and document
new runtime interfaces in the design/contracts and developer guide. Generated
environments, caches, builds, and diagram outputs are not authoritative
sources. The optional Rust import in the scaffold does not establish a Rust
compiler or extension implementation.
