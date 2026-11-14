# Ratify the compiler and execution proposals against the corpus

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
`Tolerances (exception triggers)`, `Risks`, `Progress`,
`Surprises & discoveries`, `Decision log`, `Outcomes & retrospective`,
`Conformance basis`, and `Verification plan` must be kept up to date as work
proceeds.

Status: DRAFT

Roadmap item: `docs/roadmap.md` task 1.1.2, "Ratify the compiler and execution
proposals against the corpus". It requires task 1.1.1.

## Purpose / big picture

Pokie is a proposed language for Python-fluent command-line users. It combines
awk-like ordered record processing with Python statements, regex capture
dispatch, and explicit validating or converting patterns. No interpreter exists
yet. Phase 1 of the roadmap asks whether the proposed contracts survive contact
with representative jobs before anyone builds a parser. Its idea is
falsifiable: "Reject the foundation if representative examples cannot be
specified without incompatible rules."

Task 1.1.1 built the evidence base: an executable job corpus and a register of
open decisions. This task, 1.1.2, uses that evidence to settle five contract
areas that every later slice depends on:

1. Scope: what one program namespace is, which statements may appear in each
   section, and which names are reserved.
2. Input ownership: who reads input, how bytes become records, and what
   happens when user code competes for the input stream.
3. Control transfer: how `next` and `exit` cross user loops, `try`, and
   `finally`, and which constructs would silently defeat them.
4. Binding visibility: when capture-pattern bindings become visible, what
   guards and helper functions see, and where record-scoped names may be read.
5. Finalization: when the `end:` block runs, what each failure does to it,
   and which process status results.

A *contract* here means a precise statement of observable behaviour in
`docs/pokie-design.md`, `docs/design-contracts.md`, or an architectural
decision record (ADR). To *ratify* a contract means that the project owner
accepts it, its ADR status changes from `Proposed` to `Accepted`, and later
roadmap tasks may build on it without reopening it. A *counterexample* is a
concrete program, input, or host-Python behaviour that breaks, or
disambiguates, a proposed contract. The roadmap's success criterion for this
task is that "scope, input ownership, control transfer, binding visibility, and
finalization are decided; counterexamples update the contracts".

After this change, a reader can do four things that they cannot do today.

First, they can open `tests/contract_ratification/register.toml` and find every
ratified decision. Each entry has a stable identifier such as `CONTROL-3`, the
contract area, the exact rule, whether the corpus upheld or amended the
original proposal, the counterexamples that forced the change, the executable
evidence, the downstream roadmap tasks that must implement it, and the project
owner's verdict and date.

Second, they can run `make test` and watch that register be checked. Every
decision must cite evidence that exists and passes. Every counterexample must
have a disposition. Every *witness* (a probe showing that the chosen rule is
feasible on CPython 3.14) must pass. Every *control* (a probe running the
rejected alternative) must fail in the predicted way, which proves the evidence
is not vacuous. The ratification verdict is `ratified` only when the owner has
accepted every decision.

Third, they can read ADR 0001 and ADR 0002 as `Accepted`, and a new ADR
(expected to be numbered 0005) that gives the record reader sole ownership of
program input. `docs/pokie-design.md` §§2–5, 7, 9, and 10 and
`docs/design-contracts.md` will state the ratified rules. A rendered decision
table in `docs/design-contracts.md` is kept identical to the register by a test.

Fourth, they can run three new corpus jobs that would have exposed the
ambiguities this task resolves. For example, `aggregate-port-changes` prints
`a 80`, `a 443`, then `2` under the ratified guard rule. It would print only
`0` if helpers called from a guard could see uncommitted candidate bindings.

Success is observable:

- `make test` passes and includes tests named, for example,
  `test_register_decisions_cover_every_area` and
  `test_signal_unwinding_matches_model`, plus the scenario
  `Scenario: Every contract area is ratified`.
- Changing any decision's `owner_verdict` from `accepted` to `pending` makes
  `test_ratification_verdict_is_ratified` fail, naming that decision.
- Changing the lowering sketch so that pokie control signals derive from
  `Exception` instead of `BaseException` makes the control-transfer property
  fail with a shrunk program containing `except Exception:`.
- Deleting a row from the rendered table in `docs/design-contracts.md` makes
  `test_contract_table_matches_register` fail.

No product behaviour ships. `pokie/` is untouched, and no document may claim
that pokie can run a program.

## Constraints

- Entry precondition: task 1.1.1 must be complete before any milestone after
  EP-M0 starts. Completion means that its roadmap checkbox is ticked,
  `docs/job-corpus.md` and `docs/decision-register.md` exist, the corpus holds
  the eleven planned jobs, and the audit verdict is `proceed`. At the time of
  drafting (2026-11-14), only EP-M0 and EP-M1 of the 1.1.1 plan have merged.
  The corpus holds one job, and neither document exists. If the precondition
  does not hold when execution begins, set this plan to `BLOCKED` and escalate
  (see `Tolerances`).
- No product behaviour is introduced. `pokie/` must not change. Documents
  must describe ratified rules as contracts for future implementation, never as
  delivered capability.
- Decisions belong to the project owner. The only established role is the
  project owner, `@leynos` (terms of reference §4 Table 2), who owns Q3 and Q5
  in the decision register. The implementer prepares recommendations and
  evidence, but may not record `owner_verdict = "accepted"` without the owner's
  explicit acceptance in the conversation or the pull request.
- Contracts must not drift silently. A counterexample that cannot be resolved
  by a contract amendment is recorded with effect `falsifies`, which flips the
  ratification verdict to `revise-contracts`. The plan is then set to `BLOCKED`
  and escalated. This is the falsification outcome that phase 1 exists to
  detect.
- No runtime or development dependency is added. `pytest-bdd`, `syrupy`, and
  `hypothesis` are already present in the `dev` group of `pyproject.toml`.
- All new code is test-only and lives under `tests/`. The wheel packages only
  `pokie` (`[tool.hatch.build.targets.wheel] packages = ["pokie"]`).
- Hexagonal boundaries: the domain modules in `tests/contract_ratification/`
  (`model.py`, `policy.py`, `render.py`, and the four `*_model.py` semantic
  models) perform no input/output (I/O) and do not call `exec`, `compile`, or
  `subprocess`. They import nothing from `adapters/`, `tomllib`, `os`, `io`,
  `shutil`, `tempfile`, or `sys`. Only adapters execute host Python, read
  files, or run processes. An abstract syntax tree (AST) test enforces this,
  extending the pattern in `tests/test_job_corpus_boundaries.py`.
- Host-execution sketches are verification oracles, not compiler prototypes.
  They build Python source from small, already-structured shape values, and
  they never parse pokie source text. Roadmap task 1.2.2 owns the IR contract
  and reference evaluator, and tasks 2.1.x own lowering. Sketch modules carry a
  module docstring saying so.
- Every code file stays under 400 lines. Functions respect the Ruff and
  Pylint limits in `pyproject.toml`: `max-complexity = 8`, `max-args = 4`,
  `max-locals = 10` (Ruff) and 20 (Pylint), and `max-bool-expr = 2`. Pylint
  `max-args = 4` counts pytest fixtures, so a test can take at most two
  fixtures beyond `parametrize` arguments.
- Subprocess probes run through the existing `ProcessRunner`
  (`tests/job_corpus/adapters/process_runner.py`). They use argument lists,
  never `shell=True`, and an explicit environment allowlist. Python children
  run as `sys.executable -I`. No probe uses the network or writes outside its
  temporary directory.
- Data that would otherwise be large inline literals lives in data files:
  the register in `tests/contract_ratification/register.toml`, and tables of
  witness/control cases in `tests/data/`.
- Prose and identifiers use en-GB-oxendict spelling ("-ize", "-yse",
  "-our"), except external API names. Markdown wraps at 80 columns, and code
  blocks wrap at 120 columns.
- ADR edits follow `docs/documentation-style-guide.md` "Architectural decision
  records": the required sections in order, `Accepted` with a date and a
  decision summary, the next free four-digit number, and no renumbering.

## Tolerances (exception triggers)

ExecPlan files are excluded from every size limit below, including when this
plan is edited in the same change. Counts compare against the merge base with
`main` at the start of execution, recorded in `Progress` as `BASE`.

- Code: no more than 3,400 net Python lines (additions minus deletions) and 30
  Python files under `tests/`, excluding `tests/job_corpus/jobs/`. Measure with
  `git diff --numstat BASE -- 'tests/**/*.py' ':!tests/job_corpus/jobs/**'`.
- Corpus content: no more than 700 net lines and 15 files under
  `tests/job_corpus/jobs/`, covering the three new job directories and nothing
  else.
- Configuration and data: no more than 600 net lines across
  `tests/contract_ratification/register.toml`, `tests/data/*.json`,
  `tests/features/*.feature`, snapshot files under `__snapshots__/`, and
  `pyproject.toml`. Changes to `pyproject.toml` are limited to dead-code,
  duplication, and lint-scope settings, 40 lines at most. Any change to
  `[project]`, dependency groups, or `uv.lock` breaches this limit.
- Documentation: no more than 1,200 net lines under `docs/`, excluding
  `docs/execplans/`, plus `README.md`.
- Each category is enforced independently. Spare capacity in one category
  never offsets another.
- Interface: if anything under `pokie/` must change, stop and escalate.
- Dependencies: if any new dependency is needed, stop and escalate.
- Precondition: if task 1.1.1 is incomplete when EP-M1 would start, stop and
  ask the owner whether to (a) wait for 1.1.1, or (b) run EP-M1 and EP-M2 only,
  which do not depend on the eleven jobs, and hold EP-M3 onwards.
- Falsification: if a counterexample has effect `falsifies`, or a witness
  fails on CPython 3.14, set `BLOCKED` and escalate.
- Vacuity: if a control passes (that is, the rejected alternative behaves like
  the chosen rule), the evidence for that decision is vacuous. Stop, record it,
  and escalate rather than deleting the control.
- Owner verdict: if the owner rejects a recommended disposition, change only
  what the owner directs, then re-run EP-M2's evidence for the affected area.
  If the redirection changes more than five decisions, re-plan EP-M5's
  documentation budget before continuing.
- Overlap: if a semantic model or sketch needs to parse pokie source, evaluate
  pokie IR, or grow past 250 lines, it is turning into roadmap task 1.2.2. Stop
  and escalate.
- Runtime: if the new tests add more than 30 seconds to `make test` on this
  machine, reduce Hypothesis `max_examples` for the in-process properties
  through the existing profiles in `tests/conftest.py`. If that is not enough,
  stop and escalate.
- Tooling: if a lint gate rejects the new code and the only fix is to exclude
  `tests/` or `tests/contract_ratification/` from that gate, stop and escalate.
- Coverage: if the coverage ratchet (`.coverage-baseline-v2.python`) falls,
  restructure the code or add boundary tests. Never lower or bypass the ratchet.
- Iterations: if a gate still fails after three fix attempts, stop and
  escalate.

## Risks

- Risk: task 1.1.1 is incomplete (EP-M2 to EP-M5 outstanding), so this task
  cannot be ratified "against the corpus" yet. Severity: high. Likelihood:
  certain at drafting time. Mitigation: EP-M0 checks the precondition, and the
  tolerance offers the owner a choice between waiting and partial execution.
  EP-M1 and EP-M2 are designed to depend only on the merged harness
  (`ProcessRunner`, `toml_values`, `Observation`).
- Risk: the 1.1.1 file and line budget was exhausted. It hit its 4,800-line
  cap exactly, and its file limit doubled from 45 to 92. Any EP-M2 to EP-M5
  work on 1.1.1 still to land will change helper module names that this plan
  reuses. Severity: medium. Likelihood: medium. Mitigation: EP-M0 re-surveys
  the harness, and `Interfaces and dependencies` names the capabilities needed,
  not private symbols.
- Risk: the semantic models restate the rule they verify, which makes the
  evidence vacuous. Severity: high. Likelihood: medium. Mitigation: every model
  is checked differentially against real CPython execution of a lowering
  sketch, and every decision with a rejected alternative has a control that
  must fail (see `Verification plan`).
- Risk: the sketches drift into a second compiler or evaluator. Severity:
  medium. Likelihood: medium. Mitigation: the overlap tolerance; the sketches
  accept only structured shapes; their docstrings forbid promotion; and task
  1.2.2 is named as the owner of evaluator work.
- Risk: the owner disagrees with several recommendations, causing re-work.
  Severity: medium. Likelihood: medium. Mitigation: EP-M4 presents options and
  trade-offs per decision before any document is rewritten, and EP-M5 starts
  only after the verdicts are recorded.
- Risk: `mdtablefix` (run by `make fmt`) re-pads the rendered Markdown table,
  so a byte-exact comparison with the renderer fails. It also rewrites `...` to
  `…` inside inline code. Severity: low. Likelihood: high. Mitigation: compare
  normalized cells (trimmed, with column padding ignored), and keep ellipses
  out of rendered cells.
- Risk: Python 3.14's PEP 765 `SyntaxWarning` for `break`/`continue` in
  `finally` reaches test output, or `-W error` turns it into an error.
  Severity: low. Likelihood: medium. Mitigation: the swallow probe compiles its
  source under `warnings.catch_warnings(record=True)` and asserts the warning
  as part of the evidence.
- Risk: Vulture and Skylos flag pytest-bdd steps, Hypothesis strategies, and
  enum members reached only from TOML. Severity: low. Likelihood: high.
  Mitigation: extend the whitelist pattern of 1.1.1
  (`tests/job_corpus/vulture_whitelist.py`, guarded in both directions by
  `tests/test_job_corpus_dead_code.py`) to the new package. Do not use
  `ignore_names`.
- Risk: awk alternatives for the new jobs behave differently under mawk (on
  CI) and GNU Awk (locally). Severity: low. Likelihood: low. Mitigation: use
  POSIX features and explicit character classes only, as 1.1.1 learned.
- Risk: the coverage ratchet falls because adapter error branches are
  unreachable. Severity: medium. Likelihood: medium. Mitigation: loader
  rejection tests are table-driven from `tests/data/`, as in
  `tests/test_job_corpus_toml.py`.

## Progress

- [x] (2026-11-14) Branch renamed to
  `1-1-2-ratify-compiler-and-execution-proposals`, tracking the same name on
  `origin`.
- [x] (2026-11-14) Leta workspace registered. Leta's Python language server
  (basedpyright) is not installed, so symbol navigation fell back to file reads.
- [x] (2026-11-14) Wyvern reconnaissance: the 1.1.1 plan's state, corpus,
  register specification, and budget history; the harness architecture, schema,
  tooling limits, and extension points; and contract tensions across the
  design, contracts, context, terms of reference, and ADRs 0001–0002.
- [x] (2026-11-14) Prior-art and host-semantics research with Firecrawl: the
  POSIX awk `exit`/`next`/`getline`/`END` rules, the Python 3.14 `match`,
  `try`, and `exec`/`compile` contracts, PEP 765, and PAWK.
- [x] (2026-11-14) Scratch CPython 3.14.7 probes under `/tmp/pokie-112-probes/`
  confirmed eight load-bearing host behaviours (see `Artefacts and notes`).
- [x] (2026-11-14) Draft ExecPlan written.
- [ ] Expert-panel review and revision.
- [ ] Plan approved by the project owner.
- [ ] EP-M0: entry precondition and baseline.
- [ ] EP-M1: ratification register domain, loader, verdict, and scenarios.
- [ ] EP-M2: host evidence (witnesses, controls, and properties).
- [ ] EP-M3: counterexample corpus jobs.
- [ ] EP-M4: owner ratification gate.
- [ ] EP-M5: contract documents, ADRs, and roadmap completion.

## Surprises & discoveries

- Observation: task 1.1.1 is only partly delivered. Evidence: its plan's
  `Progress` marks EP-M2 partial and EP-M3 to EP-M5 undelivered.
  `tests/test_job_corpus_alternatives.py` pins `EXPECTED_JOB_COUNT = 1`.
  `docs/job-corpus.md` and `docs/decision-register.md` do not exist. Impact:
  the entry precondition and the precondition tolerance.
- Observation: Python's native `match` leaks candidate bindings when a guard
  is false. Evidence: the scratch probe printed `guard-false leak: ada 7` for
  `case (name, uid) if False`. The Python reference says "do not rely on
  variables remaining unchanged after a failed match". Impact: confirms 1.1.1
  OBS-08. The lowering must bind into private storage and commit after the
  guard (BIND-1).
- Observation: a `break` in `finally` silently swallows a `BaseException`
  signal, and CPython 3.14 emits a PEP 765 `SyntaxWarning`. Bare `except:` and
  `contextlib.suppress(BaseException)` swallow it too, while
  `except Exception:` does not. Impact: CONTROL-3 turns "trusted programs must
  not suppress signals" into static rules plus a documented residual.
- Observation: executing a program in a plain `dict` namespace breaks
  `pickle` for program-defined classes (`PicklingError`). A namespace
  registered in `sys.modules` pickles correctly. Impact: SCOPE-1 makes the
  program namespace a real module object.
- Observation: a `from __future__ import annotations` in one compilation unit
  does not affect another unit that shares the same globals. Impact: SCOPE-2,
  one compilation unit.
- Observation: a generator expression that reads a record-scoped global sees
  the value current when it is consumed, not when it was created (`['b']`
  rather than `['a']`). List comprehensions are eager. Impact: BIND-5.
- Observation: text-mode universal newlines split a lone `\r` into two
  records, and `str.splitlines` also splits on U+2028, U+0085, `\v`, and `\f`.
  Impact: resolves 1.1.1 OBS-01 through INPUT-2.
- Observation: when the record loop is generated at module level, a bare
  `break` in an action leaves the record loop, so CPython would accept a
  program that the design rejects. Impact: CONTROL-5 must be a static pokie
  rule, not a Python compile error.
- Observation: a helper function called from a guard reads the committed
  global, not the guard's candidate parameter. Impact: BIND-2 and the
  `aggregate-port-changes` job.
- Observation: `-F ''` is a usage error (status 2) in
  `docs/design-contracts.md` §4, but an empty `FS` "fails initialization"
  (status 1) in `docs/pokie-design.md` §4.1. Impact: INPUT-7 separates the two
  sources.
- Observation: `next` and `exit` are Python builtins (`exit` comes from
  `site`). `exit()` raises `SystemExit`, which would skip `end:` silently in a
  program that meant pokie `exit`. Impact: CONTROL-1.
- Observation: ADR 0002 deviates from the current ADR template. It has
  `Consequences` and `Alternatives considered` instead of
  `Known risks and limitations` and `Options considered`, and it has no
  `Outstanding decisions`. Impact: EP-M5 restructures it while accepting it.

## Decision log

- Decision: deliver ratification as an executable register with evidence,
  not as prose alone. Rationale: the phase 1 idea is falsifiable only if a
  changed contract or a broken host assumption fails a test. The register makes
  "decided" checkable (owner verdict and date), and makes "counterexamples
  update the contracts" checkable (each amendment cites counterexamples, and
  each counterexample has a disposition). Date: 2026-11-14.
- Decision: pair every chosen rule that rejects an alternative with a control
  that runs the alternative and must fail. Rationale: models written by the
  same author as the rule can pass vacuously. A control that fails for the
  predicted reason shows that the evidence discriminates. Date: 2026-11-14.
- Decision: put the ratification code in a new package,
  `tests/contract_ratification/`, and reuse the 1.1.1 harness's
  `ProcessRunner`, strict TOML value helpers, and `Observation` vocabulary
  rather than duplicating them. Rationale: the AGENTS.md abstraction policy
  says to sweep for existing helpers first. The duplication gate (`nose`) would
  reject copies. Date: 2026-11-14.
- Decision: the private TOML helpers in
  `tests/job_corpus/adapters/toml_values.py` (for example `_table`, `_strings`,
  and `_member`) are promoted to public names in one atomic change that updates
  every caller, if the new loader needs them. No aliases or re-exports are
  kept. Rationale: the execplans skill forbids compatibility shims for private,
  test-only APIs. Date: 2026-11-14.
- Decision: input ownership gets its own ADR (expected 0005). Scope, control,
  binding, and finalization stay in ADR 0002. Rationale: ADR 0002 is titled for
  scope and lifecycle, and input ownership is a separate decision tied to Q3.
  Mixing them would make a later Q3 expansion (task 6.1.1) supersede unrelated
  rules. Date: 2026-11-14.
- Decision: recommend accepting ADR 0001 for the compiler and lowering
  direction only, and route its runtime-matrix and packaging consequences to Q2
  (task 5.1.1) explicitly. Rationale: roadmap 1.1.2 names ADRs 0001–0002.
  Packaging evidence belongs to Q2, which ADR 0001's own status already
  separates. The owner may instead keep ADR 0001 `Proposed`; EP-M4 asks. Date:
  2026-11-14.
- Decision: static-validation rules (for example "reject `next` inside a
  nested `def`") are ratified as contracts, but their implementation is
  discharged by later tasks (2.1.1, 2.1.2, 2.2.1, and 3.2.1). The register
  records `discharged_by` for each. Rationale: no parser exists, and phase 1
  "supplies decisions and evidence inputs, not a parser layer". Host evidence
  shows why each rule is needed; it cannot show the rule is enforced. Date:
  2026-11-14.
- Decision: `docs/users-guide.md` is not changed by this task, unless the
  owner directs otherwise. Rationale: the users' guide describes delivered
  behaviour, and no behaviour ships. The developers' guide gains the register
  workflow. Date: 2026-11-14.

## Outcomes & retrospective

Not started. On completion, record which decisions were ratified, amended, or
deferred; which counterexamples changed contracts; whether any control exposed
a vacuous model; and the final size of each budget category.

## Context and orientation

The repository is a Python 3.14 project managed by `uv`. `pokie/` contains only
a generated greeting package. The language exists as documents:

- `docs/terms-of-reference.md` defines goals G1–G5 and open questions Q1–Q8.
  Q3 asks whether fields are mutable and whether libraries can own structured
  input. Q5 asks whether the guard-binding and lifecycle-failure proposals meet
  expectations.
- `docs/context.md` defines the vocabulary: record, field, capture, rule,
  case, guard, adapter, binding, candidate bindings, binding transaction,
  persistent scope, `next`, and `exit`.
- `docs/pokie-design.md` is the technical design. §2 records the AST-lowering
  choice. §3 covers program structure and lexical boundaries. §4 covers input,
  fields, state, lifecycle, and control transfer. §5 covers capture and
  structural-pattern semantics. §7 covers compilation boundaries. §9 is the
  failure and trust model. §10 sets the verification strategy.
- `docs/design-contracts.md` holds canonical structured contracts: the
  representative program (§1), the IR envelope (§2), the adapter protocol (§3),
  the command-line interface (CLI) and status table (§4), and the pipeline
  diagram (§5).
- `docs/adrs/adr-0001-lower-pokie-through-python-asts.md` (Proposed) and
  `docs/adrs/adr-0002-preserve-one-program-scope-and-ordered-lifecycle.md`
  (Proposed) are the decisions under ratification.
  `docs/adrs/adr-0003-resolve-adapters-through-an-explicit-registry.md` is out
  of scope, because roadmap 4.1.1 owns it.
- `docs/execplans/1-1-1-establish-the-representative-job-corpus-and-decision-register.md`
  is the predecessor plan. Its "Corpus specification" lists eleven jobs. Its
  "Phase 1 verdict input" expects verdict `proceed`, with OBS-01, OBS-02, and
  OBS-03 as the agenda for this task. OBS-08 (native `match` leaks) is also
  routed here through Q5.

The executable harness lives under `tests/job_corpus/`:

- `model.py` holds frozen domain values: `Failure` (`none`, `static`,
  `initialization`, `input`, `guard`, `adapter`, `action`, `end`,
  `broken-pipe`), `ObservationKind` (`contradiction`, `ambiguity`,
  `ergonomic-smell`, `host-divergence`), `CorpusJob`, `JobCase`,
  `ScriptImplementation`, `Observation`, and `RegisterEntry`.
- `policy.py` and `register_policy.py` hold pure checks. `derive_verdict`
  returns `revise-contracts` exactly when some observation has kind
  `contradiction`.
- `ports.py` defines `ProgramRunner.run(implementation, case)` and
  `EvidenceFormatError(message, path=..., key=...)`.
- `adapters/process_runner.py` defines `ProcessRunner`. It materializes case
  inputs in a temporary directory, runs references as `sys.executable -I` with
  only `PATH` and `LC_ALL`, and enforces a 10-second timeout.
- `adapters/toml_jobs.py` loads `job.toml` (schema 1, with unknown keys
  rejected at every level) using the helpers in `adapters/toml_values.py`.
- `jobs/validate-user-records/` is the only job so far: `job.toml`,
  `program.pokie` (proposed, not executable), `reference.py` (a Python model of
  the proposed semantics), and `alternative.awk`.
- Tests: `tests/test_job_corpus_*.py`, the behavioural feature
  `tests/features/job_corpus.feature` with steps in
  `tests/test_job_corpus_scenarios.py`, Hypothesis properties in
  `tests/test_job_corpus_properties.py`, and the domain-purity AST test
  `tests/test_job_corpus_boundaries.py`. `tests/conftest.py` registers
  Hypothesis profiles: no deadline by default, and `derandomize` under `CI`.

Tooling and gates come from `Makefile` and `pyproject.toml`. `make all` runs
`build check-fmt lint typecheck test markdownlint nixie audit validate
test-workflow-contracts`.
`make lint` runs Interrogate at 100% docstring coverage, Ruff, Pylint (on PyPy
3.12), the DF12 lints, ambrleaks, Skylos plus Vulture (`dead-code`), `nose`
duplication, and actionlint/yamllint. `make test` runs `pytest -v -n auto` with
`pythonpath = ["tests"]`, a 30-second per-test timeout, and
`empty_parameter_set_mark = "fail_at_collect"`. The coverage ratchet compares
against `.coverage-baseline-v2.python` (98.04).

Survey for budgets. The 1.1.1 plan began with 45 files and 4,800 net Python
lines outside job directories. The owner raised the file limit to 92 on
2026-11-01, after case tables moved to `tests/data/`. The line cap never moved,
but the work reached 4,800 exactly several times and was compacted each time,
including once from 4,859 down to 4,792. Its final measurement was 4,797 lines
across 26 Python files. That history shows repeated underestimation of support
code (loaders, runner boundary tests, and coverage controls) and of
review-driven repairs: six CodeRabbit rounds during EP-M0. This plan therefore
estimates code bottom-up and adds about 15% contingency:

- register domain (model, policy, render): about 450 lines;
- semantic models: about 4 × 110 lines;
- host sketches and adapters: about 4 × 120 lines;
- register loader and Markdown trace adapter: about 300 lines;
- subprocess probe scripts: about 6 × 30 lines;
- tests, properties, scenario steps, and whitelist: about 1,100 lines.

That totals about 2,950 lines, so the limit is 3,400. Three corpus jobs at
about 200 lines each, across five files, give a limit of 700 lines and 15
files. Documentation covers two accepted ADRs restructured to the template, one
new ADR, design and contract amendments, and register, terms-of-reference,
context, developers'-guide, layout, and contents updates. That is estimated at
about 1,000 lines, so the limit is 1,200.

## Conformance basis

Upstream artefacts, at `main` commit `7311a47`:

- Terms of reference, draft v0.1 (2026-10-09): G1–G5, Q3, Q5, and §6.2
  non-goals. Identifiers: `TOR-G1`…`TOR-G5`, `TOR-Q3`, `TOR-Q5`.
- Technical design, proposed v0.1 (2026-10-10): §§2–5, 7, 9, and 10.
  Identifiers: `DES-2`, `DES-3.1`, `DES-3.2`, `DES-4.1`, `DES-4.2`, `DES-4.3`,
  `DES-5`, `DES-7`, `DES-9`, and `DES-10`.
- Design contracts, proposed v0.1 (2026-10-10): §1 (`DC-1`), §2 (`DC-2`), and
  §4 (`DC-4`).
- ADR 0001 (Proposed, 2026-10-09), `ADR-0001`; ADR 0002 (Proposed,
  2026-10-09), `ADR-0002`.
- The 1.1.1 ExecPlan (Status APPROVED) and, once present,
  `docs/job-corpus.md` and `docs/decision-register.md`. Identifiers: corpus
  observations `OBS-01`, `OBS-02`, `OBS-03`, and `OBS-08`; register rows `Q3`
  and `Q5`.
- Roadmap task `RM-1.1.2`, with downstream tasks that consume the decisions:
  `RM-1.2.1`, `RM-2.1.1`, `RM-2.1.2`, `RM-2.1.3`, `RM-2.2.1`, `RM-2.2.2`, and
  `RM-3.2.1`.
- Governing standards: `AGENTS.md`, `docs/documentation-style-guide.md`,
  `docs/developers-guide.md`, `docs/scripting-standards.md`, and
  `docs/complexity-antipatterns-and-refactoring-strategies.md`.

Trace chains (upstream → decision area → milestone → acceptance evidence):

- `TOR-Q5 → DES-4.2, ADR-0002 → SCOPE-* → EP-M2, EP-M5 →
  test_registered_namespace_pickles, test_contract_table_matches_register`
- `TOR-Q3 → DES-4.1 → INPUT-* → EP-M2, EP-M3, EP-M5 →
  test_record_splitting_matches_model, aggregate-csv-by-header cases`
- `TOR-G5, DES-4.3, ADR-0002 → CONTROL-* → EP-M2, EP-M3 →
  test_signal_unwinding_matches_model, filter-first-bad-token cases`
- `TOR-G2, DES-5, DC-1, OBS-08 → BIND-* → EP-M2, EP-M3 →
  test_binding_transaction_preserves_prior_state, aggregate-port-changes cases`
- `TOR-G5, DES-4.2, DC-4 → FINAL-* → EP-M2 →
  test_lifecycle_outcomes_match_model`
- `RM-1.1.2 success → all areas → EP-M4, EP-M5 → test_ratification_verdict_is_ratified,
  Scenario: Every contract area is ratified`

## Ratification agenda

This section is the proposal that EP-M4 puts to the owner. Each decision has a
stable identifier, a recommended rule, a recommended disposition, and the
counterexamples that motivate it. The dispositions are:

- `ratified`: the proposal stands as written;
- `amended`: the proposal changes or gains a rule;
- `deferred`: the question is routed to a named later task.

`CX-nn` identifiers refer to the `Counterexample catalogue` below. "Static
error" means a compile-time diagnostic with status 2 and no user code run.

### Scope

- SCOPE-1 (amended; CX-01). The program namespace is a fresh module object
  with `__name__ == "__main__"`. It is installed as `sys.modules["__main__"]`
  for the duration of the run and restored afterwards, as `runpy.run_path` does
  with `run_name="__main__"`. For a file program, `__file__` is the program
  path. Inline programs have no `__file__`. Preamble, `start:`, rules, guards,
  and `end:` all use its dictionary as globals. The original proposal ("one
  dedicated module-like globals dictionary") broke `pickle` for program-defined
  classes.
- SCOPE-2 (amended; CX-02). A program is one compilation unit.
  `from __future__` imports may appear only at the start of the preamble, and
  they apply to every section. Elsewhere they are a static error.
- SCOPE-3 (ratified, clarified). The preamble is any Python suite: imports,
  definitions, assignments, expression statements, and loops. It runs once,
  after the whole program has passed static validation and before `start:`.
  Ordinary top-level statements after the first lifecycle block or rule are a
  static error.
- SCOPE-4 (amended; CX-03). Statements that are invalid at module level
  (`return`, `yield`, `await`, `async for`, `async with`, and `nonlocal`) are
  static errors in every section, reported at the pokie source span. `global`
  declarations are permitted. They are redundant at section level and refer to
  the program namespace inside definitions.
- SCOPE-5 (amended; CX-04). These names are reserved: the `__pokie_` prefix,
  `NR`, `NF`, `MATCH`, and `FS` (except in `start:`). They may not be
  assignment, augmented-assignment, `del`, `for`, `with ... as`, `import … as`,
  `except … as`, `global`, or capture-pattern targets. Violations are static
  errors. Access through `globals()` is not prevented: reservation is hygiene,
  not isolation (design §7).
- SCOPE-6 (ratified). Definitions inside rule actions are allowed and
  re-executed for each record that runs the action.

### Input ownership

- INPUT-1 (ratified; Q3 for v1). One driver-owned reader consumes the input
  operands. Fields, `$0`, `NF`, and `NR` are read-only. Mutable fields and
  library-owned structured input are deferred to task 6.1.1 under Q3.
- INPUT-2 (amended; CX-05, OBS-01). Records are split on `\n` only. A `\r`
  immediately before `\n`, or at the end of an unterminated final record, is
  removed. A lone `\r`, `\v`, `\f`, U+0085, U+2028, or U+2029 is record
  content. A final unterminated line is a record, and an empty input has none.
- INPUT-3 (amended; CX-06, OBS-02). Strict decoding is incremental. Every
  record before the first undecodable byte is delivered, and its effects and
  output are kept. Reaching the bad record is an input failure that names the
  operand and record number `NR + 1`. This matches the 1.1.1
  `filter-error-lines/invalid-utf8` expectation (`ok ERROR one` is printed).
- INPUT-4 (amended; CX-07). Operands are opened lazily, in order, when the
  previous operand is exhausted. A missing or unreadable later operand is an
  input failure when it is reached, after earlier output.
- INPUT-5 (amended; CX-08). When standard input is an input source (no
  operands, or `-`), the driver replaces `sys.stdin` with a guard object for
  the duration of the run. Any read through it is an input failure, with a
  diagnostic that names input ownership. When standard input is not an input
  source, `sys.stdin` is untouched, so a program may read configuration from
  it. Direct reads of file descriptor 0 remain outside the contract. The
  original proposal left the outcome undefined: a `readline` in `start:` would
  silently steal buffered records.
- INPUT-6 (amended; CX-09). A program with no rules and no `end:` block opens
  no input. This matches awk's BEGIN-only rule and prevents an inline program
  from blocking on a terminal.
- INPUT-7 (amended; CX-10). `-F` is validated as a usage argument: an empty
  separator is a usage error (status 2). `FS` may be assigned only in `start:`
  (a static error elsewhere). An invalid value at the end of `start:` is an
  initialization failure (status 1). The value is frozen before the first
  operand opens.
- INPUT-8 (ratified, clarified; CX-11). `NR` is readable everywhere: it is 0
  in the preamble and `start:`, and the total of delivered records in `end:`.
  `$0`, `$n`, `NF`, and `MATCH` are record-scoped, and are valid only in rule
  predicates, guards, and actions (a static error elsewhere). Unlike awk,
  `end:` has no last record: programs keep it in a variable.
- INPUT-9 (ratified, clarified). Pokie `exit` stops reading and closes every
  driver-owned operand before `end:` runs.

### Control transfer

- CONTROL-1 (amended; CX-12). `next` and `exit` are pokie statements only when
  the whole simple statement is the bare name, inside a rule action. Calls such
  as `next(iterator)` keep their Python meaning. A call to the site builtins
  `exit(...)` or `quit(...)` anywhere in the program is a static error. The
  diagnostic points to pokie `exit`, or to `sys.exit` for a deliberate host
  exit. The owner may choose a warning instead; EP-M4 asks.
- CONTROL-2 (ratified; evidence INV-CTL-1). The lowering raises
  compiler-owned signals that derive from `BaseException` and not from
  `Exception`. Only the driver boundary catches them. Every enclosing `finally`
  runs exactly once, innermost first, and `with` exits run.
- CONTROL-3 (amended; CX-13, CX-14). Within one rule action, a static error
  rejects any `try` statement whose body lexically contains `next` or `exit` if
  one of its handlers is a bare `except:`, names `BaseException` (alone or in a
  tuple), or is an `except*` clause, or if its `finally` contains `break` or
  `continue`. These cases are statically complete, because `next` and `exit`
  cannot occur inside nested definitions (CONTROL-4), so every enclosing
  handler is visible in the same action. Suppression by a context manager whose
  `__exit__` returns true (for example `contextlib.suppress(BaseException)`)
  cannot be detected statically, and remains a documented residual.
- CONTROL-4 (ratified, clarified). `next` and `exit` are static errors in the
  preamble, `start:`, `end:`, and nested `def`, `lambda`, or `class` bodies.
  Unlike awk, `exit` in `start:` is rejected (CX-15). A program that should not
  read input omits rules and `end:` (INPUT-6).
- CONTROL-5 (ratified; CX-16). `break` and `continue` in an action are valid
  only inside a user-written loop. Otherwise they are static errors, because
  the generated record loop would make them legal Python.
- CONTROL-6 (amended). An exception raised while a signal unwinds (for
  example, from a `finally` block) replaces the signal and is an action
  failure. Diagnostics hide the private signal from the displayed exception
  context.

### Binding visibility

- BIND-1 (ratified; CX-17, OBS-08). Candidate bindings are private until the
  pattern and guard both succeed. The first accepted case commits all its names
  to the program namespace together. Rejected attempts leave it unchanged. The
  lowering must not let Python's native `match` bind program names directly.
- BIND-2 (ratified, clarified; CX-18). A guard evaluates with the candidates
  as local parameters and the program namespace as globals. A function the
  guard calls sees committed program state, not the candidates.
- BIND-3 (ratified, clarified). An assignment expression (`:=`) anywhere
  inside a guard, including nested comprehensions and lambdas, is a static
  error.
- BIND-4 (amended). Guards may read the current record's `$0`, `$n`, `NF`,
  `NR`, and, in regex rules, `MATCH`.
- BIND-5 (amended; CX-19). Record-scoped names (`$0`, `$n`, `NF`, and `MATCH`)
  are static errors inside nested scopes. These are `def`, `lambda`, and
  `class` bodies, and generator expressions, except a generator expression's
  outermost iterable, which Python evaluates eagerly. List, set, and dictionary
  comprehensions are allowed.
- BIND-6 (ratified, clarified). `MATCH` exists only within a regex rule: its
  guards and its action. It is a static error in expression rules. The runtime
  unbinds it when the rule finishes.
- BIND-7 (ratified; CX-20). Accepted bindings persist until rebound. A name
  bound only by an earlier record's case keeps its value in later records.
  There is no automatic unbinding.

### Finalization

- FINAL-1 (ratified, clarified). Initialization means running the preamble,
  running `start:`, and validating `FS`. `end:` runs exactly once after
  end-of-file (EOF) or pokie `exit`, if and only if initialization succeeded,
  including on empty input.
- FINAL-2 (amended). Any initialization, input, guard, adapter, action, or
  unwinding failure skips `end:` and gives status 1. Output already written is
  kept. The driver flushes standard output before writing the diagnostic to
  standard error.
- FINAL-3 (ratified). A failure in `end:` gives status 1 and is not retried.
- FINAL-4 (ratified, clarified; CX-21). `SystemExit` and `KeyboardInterrupt`
  keep host semantics in every section. `sys.exit(n)` from a rule ends the run
  with status `n` and does not run `end:`. `sys.exit(n)` as the last statement
  of `end:` is the supported way to report a status after printing a summary.
- FINAL-5 (ratified, clarified; CX-22). No hook spans the lifecycle. A
  resource opened in `start:` is closed by `end:` on success. After a failure
  it is left to interpreter finalization, or to the program's own
  `contextlib.ExitStack` or `atexit` use. A lifecycle-spanning `finally:` block
  is a deferred candidate (design §11).
- FINAL-6 (deferred to 2.2.2). The broken-pipe row of `docs/design-contracts.md`
  Table 2 keeps status 1, and `end:` does not run after a broken pipe that is
  raised before or inside `end:`. Whether to adopt awk's terminate-by-`SIGPIPE`
  status is decided with the CLI in task 2.2.2.

### Routed corpus observations

- OBS-03 (lexical ambiguity of `$9.isascii()`): deferred to task 1.2.1 with a
  recommended rule. The scanner reads `$` followed by the longest run of ASCII
  digits, and a following `.` begins attribute access. The register records
  this as `LEX-1` with disposition `deferred`.

## Counterexample catalogue

Each counterexample has an identifier, the decision it informs, its effect
(`upholds`, `clarifies`, `amends`, or `falsifies`), and its evidence. A
*witness* is evidence that the chosen rule works on CPython. A *control* runs
the rejected alternative and must fail in the stated way. Probe identifiers are
defined in `Verification plan`.

- CX-01 (SCOPE-1, amends): a program-defined `@dataclass` cannot be pickled
  from a plain-dictionary namespace. Witness `PRB-SCOPE-MODULE`, control
  `PRB-SCOPE-DICT`.
- CX-02 (SCOPE-2, amends): a preamble `from __future__ import annotations`
  does not stringify annotations in a separately compiled rule section. Witness
  and control `PRB-SCOPE-FUTURE`.
- CX-03 (SCOPE-4, amends): `when /x/:` with the action `return` is a Python
  `SyntaxError` at module level, but it would silently leave a generated driver
  function. Host axiom `PRB-SCOPE-TOPLEVEL`.
- CX-04 (SCOPE-5, amends): a preamble `NR = 5`, or `del MATCH` in an action,
  would corrupt driver-owned names. Host evidence that globals are writable:
  `PRB-SCOPE-TOPLEVEL`.
- CX-05 (INPUT-2, amends): the bytes `a\rb\n` give two records under
  universal newlines but one under awk. Property `INV-IN-1`, with
  `str.splitlines` as control.
- CX-06 (INPUT-3, amends): a text-mode loop decodes in chunks, so an invalid
  byte on line 2 fails before line 1 is processed. Witness and control
  `PRB-INPUT-DECODE`; corpus case `filter-error-lines/invalid-utf8`.
- CX-07 (INPUT-4, clarifies): GNU Awk warns about a missing second file and
  continues with status 2. Pokie fails when it reaches that file. Evidence: the
  decision text, and the `aggregate-csv-by-header` case `missing-second-file`
  (if the runner supports a missing operand; see EP-M3).
- CX-08 (INPUT-5, amends): `start:` with `header = sys.stdin.readline()`
  while records come from standard input steals buffered records. Witness
  `PRB-INPUT-STDIN-GUARD`, control `PRB-INPUT-STDIN-RACE`.
- CX-09 (INPUT-6, amends): `pokie 'print("hi")'` would wait for a terminal
  end-of-file before printing. Evidence: the POSIX awk BEGIN-only rule
  (research note) and the decision text; the rule is discharged by task 2.2.2.
- CX-10 (INPUT-7, clarifies): `-F ''` is a usage error in `DC-4`, but an
  initialization failure in `DES-4.1`. Evidence: the document conflict.
- CX-11 (INPUT-8, upholds): awk keeps `$0` and `NF` in `END`. Pokie does not.
  Evidence: the POSIX awk research note.
- CX-12 (CONTROL-1, amends): an action that calls `exit()` raises
  `SystemExit`, so `end:` silently does not run. Host axiom `PRB-CTL-BUILTINS`.
- CX-13 (CONTROL-3, amends): `try: next` with `except: pass`, or with
  `except BaseException: pass`, swallows the signal. So does
  `with contextlib.suppress(BaseException):`. Witness `PRB-CTL-SWALLOW`.
- CX-14 (CONTROL-3, amends): `for ...: try: next` with `finally: break`
  swallows the signal, and CPython 3.14 emits `SyntaxWarning`. Witness
  `PRB-CTL-SWALLOW`.
- CX-15 (CONTROL-4, upholds): awk allows `exit` in BEGIN to skip input and
  still run END. Pokie rejects it. Evidence: the POSIX awk research note.
- CX-16 (CONTROL-5, upholds): a bare `break` in an action, lowered inside the
  generated record loop, stops all input. Witness `PRB-CTL-BARE-BREAK`.
- CX-17 (BIND-1, upholds): native `match` with a false guard leaves its
  candidates bound. Property `INV-BIND-1` (control: native-match lowering),
  OBS-08, and corpus case `validate-last-good-uid/rejections-keep-last-good`.
- CX-18 (BIND-2, clarifies): a helper called from a guard reads the
  committed value. Witness `PRB-BIND-HELPER`; corpus case
  `aggregate-port-changes/consecutive-ports`.
- CX-19 (BIND-5, amends): `rows.append(($1 for _ in range(1)))` yields a later
  record's field when consumed in `end:`. Witness and control
  `PRB-BIND-GENEXPR`.
- CX-20 (BIND-7, upholds): a name bound by case A in record 1 is still bound
  in record 2 when case B runs. Corpus case
  `aggregate-port-changes/consecutive-ports` (port persists across a rejected
  record).
- CX-21 (FINAL-4, clarifies): `sys.exit(0)` in a rule gives status 0 with no
  `end:` output. Witness `PRB-FINAL-SYSEXIT`.
- CX-22 (FINAL-5, clarifies): a `with open(...)` in `start:` closes before the
  first record, because lifecycle blocks are separate suites. Evidence: the
  design text (§3.1) and the decision text.

## Verification plan

The verification target is the ratification itself. The domain code checks that
the register is complete and coherent. The host evidence checks that the
ratified rules are feasible on CPython 3.14 and that each rejected alternative
really fails. Python's own semantics are axioms; this plan does not verify
CPython.

### Axioms

- AX-1: CPython 3.14.x behaves as documented in the Python 3.14 language
  reference for `try`/`finally`, `match`, and `with`, and in the library
  reference for `exec`, `compile`, `pickle`, and `io`. Exercised by every
  in-process sketch and by `PRB-SCOPE-TOPLEVEL`.
- AX-2: `BaseException` subclasses that are not `Exception` subclasses pass
  through `except Exception:` handlers. Exercised by `INV-CTL-1`.
- AX-3: CPython 3.14 emits `SyntaxWarning` for `break`, `continue`, or
  `return` that exits a `finally` block (PEP 765, Final). Exercised by
  `PRB-CTL-SWALLOW`.
- AX-4: the POSIX awk specification (Open Group Base Specifications, Issue
  8) defines `exit` in BEGIN, `next` in BEGIN/END as undefined, and the
  availability of `$0`, `NF`, and `NR` in END. This is cited prior art, not
  executed.
- AX-5: `ProcessRunner` runs probes as documented in
  `docs/developers-guide.md` "Corpus harness". Its own tests already exercise
  the boundary.

### Invariants and lemmas

- INV-REG-1 (register completeness): each of the five areas (`scope`,
  `input-ownership`, `control-transfer`, `binding-visibility`, and
  `finalization`) has at least one decision. Every decision id is unique and
  matches `AREA-n`. Every `amended` decision cites at least one counterexample.
  Every counterexample is cited by at least one decision and has an effect.
  Every evidence reference resolves: a `probe:` reference to a register probe, a
  `case:` reference to a loaded corpus case, an `obs:` reference to a loaded
  observation, and a `property:` reference to a test function. Every
  `discharged_by` entry is a roadmap task id that exists in `docs/roadmap.md`.
  Method: example tests plus a Hypothesis property over generated registers,
  using an independent model, as in
  `tests/test_job_corpus_properties.py::test_register_gaps_match_model`.
  Artefacts: `tests/contract_ratification/policy.py` and
  `tests/test_contract_ratification_policy.py`. Discharge: tests pass, and each
  seeded defect yields exactly one finding naming the subject. Non-vacuity: the
  generator must produce, in the recorded `hypothesis.event` statistics, at
  least one register with each defect kind and at least one defect-free
  register. Mutating `find_register_gaps` to ignore one defect kind makes the
  property fail.
- INV-REG-2 (verdict): the verdict is `ratified` if and only if INV-REG-1
  holds, every probe agrees with its expectation, every control disagrees with
  its witness, no counterexample has effect `falsifies`, and every decision has
  `owner_verdict = "accepted"` and an ISO date. It is `revise-contracts` if any
  counterexample falsifies or any witness fails. Otherwise it is
  `pending-owner`. Method: a parameterized truth table, one row per input
  combination class, plus the Hypothesis model. Discharge: the table passes.
  Non-vacuity: rows exist where each condition alone flips the outcome.
- INV-DOC-1 (document trace): every decision id appears in at least one of
  its `documents`. The rendered table between the
  `<!-- ratified-contracts:start -->` and `<!-- ratified-contracts:end -->`
  markers in `docs/design-contracts.md` equals `render_decision_table` of the
  register, after cell normalization. Method: example test plus a syrupy
  snapshot of the rendered table. Discharge: the test and snapshot pass.
  Non-vacuity: deleting one row from the document, or changing one disposition
  in the register, fails the test (seeded in the red step).
- INV-CTL-1 (signal unwinding, CONTROL-2 and CONTROL-5): for every action
  *shape* built from at most four levels of `for` loops, `while` loops,
  `try`/`finally`, `try`/`except Exception`, non-suppressing `with`, and `if`,
  containing one `next`, `exit`, user `break`, or user `continue` at a
  generated position, the CPython trace equals the model trace. A shape is a
  small tree value, not source text. The model says: `next` runs every enclosing
  `finally` and `__exit__` exactly once, innermost first, skips later rules
  for that record, and continues with the next record. `exit` does the same,
  then reads no further records and runs `end:` once. User `break` and
  `continue` affect only the innermost user loop. Method: Hypothesis over
  shapes, with records drawn from 0 to 3, compared differentially. Artefacts:
  `control_model.py` (domain), `adapters/host_control.py` (renders a shape with
  the proposed `BaseException` lowering and runs it in a fresh module
  namespace), and
  `tests/test_contract_control.py::test_signal_unwinding_matches_model`.
  Discharge: the property passes at the CI profile's example count.
  Non-vacuity: (a) `hypothesis.event` labels show shapes with each statement
  kind at depth 1 and at depth 3 or more, and with `exit` on the first and last
  records; (b) control `test_exception_signal_is_caught_by_user_handler` finds
  a counterexample (via `hypothesis.find`) when the sketch derives the signal
  from `Exception`; (c) control `test_continue_lowering_breaks_in_nested_loops`
  finds one when `next` is lowered to a plain `continue`.
- INV-BIND-1 (binding transaction, BIND-1 and BIND-7): for any prior program
  namespace, and any sequence of case attempts (each a binding map, a
  pattern-success flag, and a guard result), the namespace after the sketch
  runs equals the prior namespace updated with only the first accepted
  attempt's bindings. If none is accepted, it equals the prior namespace.
  Method: Hypothesis, compared differentially. Artefacts: `binding_model.py`,
  `adapters/host_binding.py` (commit-after-guard sketch: candidates bound in a
  generated guard function's locals, committed by one `dict.update`), and
  `tests/test_contract_binding.py::test_binding_transaction_preserves_prior_state`.
  Non-vacuity: generator statistics must include overlapping names between
  prior state and candidates, false guards, and failed patterns. Control
  `test_native_match_lowering_leaks_candidates` uses `hypothesis.find` to get a
  counterexample from a sketch that lowers to native `match` with a guard.
- LEM-BIND-2 (guard visibility, BIND-2): a helper function called from a
  guard returns the committed value. Method: subprocess probe
  `PRB-BIND-HELPER`, plus corpus case `aggregate-port-changes`. Non-vacuity:
  the corpus case's expected output differs from the tentative-commit
  interpretation (`0` versus `a 80`, `a 443`, `2`), recorded in the job as a
  declared alternative interpretation in its observation.
- INV-IN-1 (record splitting, INPUT-2): for any byte string over the alphabet
  `{a, é, \n, \r, \x0b, \x0c, U+0085, U+2028}` (UTF-8 encoded), the reader
  sketch's records joined by `\n` equal the decoded text with every `\r\n`
  replaced by `\n`, one trailing `\n` removed, and a trailing lone `\r` removed
  from the final unterminated record. The record count equals the number of
  `\n`, plus one if the text is non-empty and does not end in `\n`. Method:
  Hypothesis. Artefacts: `records_model.py` and `adapters/host_reader.py` (a
  binary reader that decodes per record), and
  `tests/test_contract_input.py::test_record_splitting_matches_model`.
  Non-vacuity: statistics show inputs containing each separator. Control
  `test_universal_newlines_split_lone_carriage_return` asserts that
  `io.TextIOWrapper` default newline handling disagrees with the model on
  `a\rb\n`.
- LEM-IN-2 (incremental decoding, INPUT-3): with input `ok\n\xff\nlater\n`,
  the reader sketch delivers `ok`, then raises a decode failure carrying record
  number 2. Method: parameterized example test. Control: `TextIOWrapper`
  iteration fails before delivering `ok` (`PRB-INPUT-DECODE` records both).
- INV-FIN-1 (lifecycle outcomes, FINAL-1 to FINAL-4 and INPUT-9): for every
  event script in the finite product of initialization {success, `start:`
  failure}, termination {EOF, `exit` at record k, action failure at record k,
  input failure at record k, `SystemExit(3)` at record k}, end {success,
  failure}, and k in {1, 2} with two records, the driver sketch's outcome
  (whether `end:` ran, how many records were delivered, the status, and the
  failure category) equals the lifecycle model's outcome. Method: exhaustive
  parameterization (40 rows), not Hypothesis, because the domain is finite and
  small. Artefacts: `lifecycle_model.py`, `adapters/host_lifecycle.py`, and
  `tests/test_contract_lifecycle.py::test_lifecycle_outcomes_match_model`.
  Non-vacuity: every row's expected outcome is asserted against the status
  values in `docs/design-contracts.md` Table 2. Control
  `test_end_in_finally_driver_publishes_partial_results`: a driver variant that
  runs `end:` in `finally` disagrees on every failure row.
- Host axioms for static rules (SCOPE-4, SCOPE-5, CONTROL-1, CONTROL-3,
  CONTROL-5, and BIND-5): these are not invariants that 1.1.2 can discharge,
  because no validator exists. The probes show only that each hazard is real on
  CPython, which justifies the rule. Discharge moves to the `discharged_by`
  tasks, which must add a failing static-validation test for each rule id. The
  register makes that obligation visible.

### Probes

Subprocess probes live in `tests/contract_ratification/probes/`. Each is a
standalone standard-library script, declared in the register with expected
standard output and exit status, and run through `ProcessRunner`:

- `PRB-SCOPE-MODULE` (witness) and `PRB-SCOPE-DICT` (control): pickle a
  program-defined dataclass from a registered `__main__` module (prints
  `pickled`), or from a plain dictionary (prints `PicklingError`).
- `PRB-SCOPE-FUTURE`: compile the preamble and rules as one unit
  (`one-unit: str`), and as two units (`two-units: type`).
- `PRB-SCOPE-TOPLEVEL`: compiling `return`, `yield`, `await`, and `nonlocal`
  at module level raises `SyntaxError`. `global` compiles, and `NR = 5`
  executes (showing that reservation must be static).
- `PRB-INPUT-DECODE`: per-record decoding prints `ok` then
  `decode-error record 2`. `TextIOWrapper` iteration prints only `decode-error`.
- `PRB-INPUT-STDIN-GUARD` (witness) and `PRB-INPUT-STDIN-RACE` (control): with
  three records on standard input, a guard on `sys.stdin` reports
  `ownership-error`. Without it, a `readline` before the record loop leaves the
  driver two records, not three.
- `PRB-CTL-BUILTINS`: `exit()` in an action exits with status 0 and skips
  the simulated `end:` output.
- `PRB-CTL-SWALLOW`: each swallowing construct (bare `except`,
  `except BaseException`, `except (ValueError, BaseException)`,
  `contextlib.suppress(BaseException)`, and `finally: break`) prints
  `swallowed`. `except Exception` and a non-suppressing `with` print
  `propagated`. The `finally: break` source compiles with one `SyntaxWarning`.
- `PRB-CTL-BARE-BREAK`: a bare `break` in a module-level record loop stops
  after record 1.
- `PRB-BIND-HELPER`: a guard function with candidate `port = 80` calls a
  helper reading committed `port = None`, and prints `None`.
- `PRB-BIND-GENEXPR`: a stored generator expression reading a record global
  yields the later record (control, prints `b`). A list comprehension and a
  generator whose only record reference is in the outermost iterable yield the
  current record (witness, prints `a a`).
- `PRB-FINAL-SYSEXIT`: `sys.exit(0)` from a rule gives status 0 and no
  `end:` output. `sys.exit(3)` at the end of `end:` gives status 3 after the
  summary.

Probe scripts that would duplicate one another are parameterized through
command-line arguments instead, so the duplication gate stays clean.

### Residual gaps

Sampling does not prove all Python behaviour. The shape grammar excludes
`async` constructs (static errors under SCOPE-4), `match` statements inside
actions, and generators (CONTROL-4 forbids signals inside nested definitions).
Context-manager suppression is unverifiable statically, and is recorded as a
residual under CONTROL-3. File-descriptor-level stdin reads remain outside
INPUT-5. No formal prover is used. The obligations are contract feasibility,
not program correctness, and the finite lifecycle domain is enumerated
exhaustively.

## Plan of work

### Stage A: entry precondition and baseline (EP-M0)

Check the precondition: roadmap 1.1.1 is ticked, `docs/job-corpus.md` and
`docs/decision-register.md` exist, `tests/job_corpus/jobs/` holds eleven job
directories, and running the audit gives `proceed`. Record the merge base as
`BASE`. Run the full gate set once through the `scrutineer` agent to record a
green baseline. Re-survey `tests/job_corpus/` for helpers that landed after
this plan was drafted (EP-M2 of 1.1.1 adds `adapters/markdown_docs.py` and
`report.py`). Reuse them instead of the adapters planned here where they match.
Update `Interfaces and dependencies` before writing code.

### Stage B: register domain (EP-M1)

Red: write `tests/test_contract_ratification_policy.py` and
`tests/test_contract_ratification_render.py` against non-existent modules. Also
write the feature file `tests/features/contract_ratification.feature`, with
steps in `tests/test_contract_ratification_scenarios.py`. Run them and confirm
that they fail with import errors and missing-step errors. Green: add
`tests/contract_ratification/__init__.py`, `model.py`, `policy.py`, and
`render.py`, then `adapters/toml_register.py` and `adapters/markdown_trace.py`.
Seed `register.toml` with every decision in `Ratification agenda`, all with
`owner_verdict = "pending"`, and every counterexample, with evidence references
limited to those that already exist (OBS ids and the existing corpus case).
Unresolved references are expected findings at this stage. The scenario that
asserts verdict `pending-owner` passes. Extend the boundary AST test to the new
domain modules, and extend the dead-code whitelist and its two-way guard.
Refactor: share loader helpers with `toml_jobs.py` (see `Decision log`).

### Stage C: host evidence (EP-M2)

For each area, write the property or example test first, with
`@pytest.mark.xfail(strict=True, reason="sketch not implemented")`, and observe
the strict failure. Then add the pure model, the host sketch adapter, and the
subprocess probe, and remove the marker. Write each control at the same time as
its witness, and confirm the control's failure in the predicted way before the
witness turns green. Add each probe to `register.toml` with its expected
output. At the end of the stage, every `probe:` and `property:` reference
resolves, and the only remaining findings are the `case:` references for EP-M3
and the pending owner verdicts.

### Stage D: counterexample corpus jobs (EP-M3)

Add three jobs under `tests/job_corpus/jobs/`, following the 1.1.1 schema. Each
has `job.toml`, `program.pokie` (proposed, not executable), a `reference.py`
that models the ratified rule explicitly, and an `alternative.awk` that uses
only POSIX features. Update the job and case counts pinned in
`tests/test_job_corpus_alternatives.py`. Each job records an observation that
names the decision it bears on. The audit verdict must stay `proceed`. The jobs
are specified under `Corpus additions` below.

### Stage E: owner ratification gate (EP-M4)

Render the decision table with the evidence summary, and present it to the
owner in the pull request and in the conversation. Give each decision's
recommendation, the alternative, the counterexamples, and the evidence. Set
this plan's status to `BLOCKED (awaiting owner verdicts)`. Record each verdict
as given: `owner_verdict = "accepted"` and `decided_on = "YYYY-MM-DD"`, or a
revised rule if the owner chooses an alternative. If a rule changes, update its
model, sketch, probe expectations, and corpus case before proceeding. Stage E
ends when the verdict test reports `ratified`.

### Stage F: contract documents (EP-M5)

Apply the documentation changes listed below. Add the rendered table between
markers in `docs/design-contracts.md`, and turn on
`test_contract_table_matches_register`. Tick roadmap 1.1.2, set this plan to
`COMPLETE`, and fill in `Outcomes & retrospective`.

## Corpus additions

`filter-first-bad-token` (filtering; G1, G5; Q5; CONTROL-2, CONTROL-5). The
program:

```plaintext
start:
    checked = 0
    rejected = 0

when NF > 0:
    for token in $0.split():
        try:
            if not token.isalnum():
                rejected += 1
                next
        finally:
            checked += 1

when True:
    print($0)

end:
    print(checked, rejected, NR)
```

- Case `mixed-tokens` (tags `next-record`, `multiple-rules`): input
  `ab cd\nef g!h ij\n\nkl\n`. Expected `ab cd\n\nkl\n5 1 4\n`, status 0. The
  `finally` counts the token that triggered `next`, and the second rule does
  not run for record 2.
- Case `empty-input` (tags `empty-input`): expected `0 0 0\n`, status 0.
- Alternatives: awk with a field loop and `next` (counting before the test,
  which is equivalent for ASCII input); status quo, a Python loop with a
  `for`/`else` flag.

`aggregate-port-changes` (aggregation; G2, G3; Q5; BIND-1, BIND-2, BIND-7). The
program:

```plaintext
def changed(candidate):
    return candidate != port

start:
    port = None
    changes = 0

when /^svc=(\w+) port=(\S+)$/:
    case name, int(port) if changed(port):
        changes += 1
        print(name, port)

end:
    print(changes)
```

- Case `consecutive-ports` (tags `binding-isolation`, `guard-rejection`,
  `adapter-rejection`): input
  `svc=a port=80\nsvc=a port=80\nsvc=a port=x\nsvc=a port=443\n`. Expected
  `a 80\na 443\n2\n`, status 0. Inside the guard, `port` is the candidate, while
  `changed` reads the committed `port`. Under a tentative-commit reading, the
  output would be `0\n`. The job records this as an observation of kind
  `ambiguity`, resolved by BIND-2.
- Alternatives: awk with an explicit `prev` variable; status quo, a Python
  loop with `try`/`except ValueError`.

`aggregate-csv-by-header` (aggregation; G1, G4; Q3, Q5; INPUT-1, INPUT-5,
INPUT-7, INPUT-8). The program:

```plaintext
from collections import Counter

start:
    FS = ","
    teams = Counter()

when NR == 1:
    next

when NF >= 2:
    teams[$2] += 1

end:
    for team, total in sorted(teams.items()):
        print(team, total)
```

- Case `roster` (tags `stdin`, `next-record`; operands `["-"]`): input
  `name,team\nada,core\nlin,ops\nsam,core\n`. Expected `core 2\nops 1\n`,
  status 0.
- Case `header-only`: input `name,team\n`. Expected empty output, status 0.
- Case `empty-input`: expected empty output, status 0.
- Case `missing-second-file` (tags `input-failure`): operands
  `["a.csv", "b.csv"]` with only `a.csv` supplied, containing
  `name,team\nada,core\n`. Expected empty output (the aggregate is printed only
  by `end:`), status 1, failure `input`. The awk and shell alternatives declare
  a divergence on this case, because awk reports a missing operand with status
  2. Add this case only if `ProcessRunner` accepts an operand with no matching
  input. Otherwise record the gap in `Surprises & discoveries`, and leave
  CX-07's evidence as the decision text.
- Observation (ambiguity, resolved by INPUT-5): reading the header with
  `sys.stdin.readline()` in `start:` competes with the reader. The pokie form
  uses `NR == 1` and `next`.
- Alternatives: awk with `-F,` and `NR == 1 { next }`; shell
  `tail -n +2 | cut -d, -f2 | sort | uniq -c` with `LC_ALL=C` and
  `comparison = "sorted-lines"`; status quo, `csv.DictReader`.

## Behavioural specification

Feature file `tests/features/contract_ratification.feature`, with steps in
`tests/test_contract_ratification_scenarios.py`:

```gherkin
Feature: Ratify pokie's compiler and execution contracts
  The project owner ratifies scope, input ownership, control transfer,
  binding visibility, and finalization against executable evidence.

  Scenario: Every contract area is ratified
    Given the repository ratification register
    When the register is audited against its evidence
    Then the verdict is "ratified"
    And every contract area has at least one accepted decision

  Scenario: A pending owner verdict blocks ratification
    Given the repository ratification register
    And decision "CONTROL-3" has owner verdict "pending"
    When the register is audited against its evidence
    Then the verdict is "pending-owner"
    And a finding names "CONTROL-3"

  Scenario: An amendment without a counterexample is rejected
    Given the repository ratification register
    And decision "SCOPE-1" cites no counterexamples
    When the register is audited against its evidence
    Then a finding names "SCOPE-1"

  Scenario: A falsifying counterexample demands contract revision
    Given the repository ratification register
    And counterexample "CX-17" has effect "falsifies"
    When the register is audited against its evidence
    Then the verdict is "revise-contracts"

  Scenario: A control that agrees with its witness is vacuous
    Given the repository ratification register
    And probe "PRB-SCOPE-DICT" expects the witness output
    When the register is audited against its evidence
    Then a finding names "PRB-SCOPE-DICT"

  Scenario: Nested-loop next runs finally blocks and skips later rules
    Given the corpus job "filter-first-bad-token"
    When its reference runs case "mixed-tokens"
    Then standard output is "ab cd\n\nkl\n5 1 4\n"
```

Until EP-M4 records the verdicts, the first scenario is marked
`@pytest.mark.xfail(strict=True, reason="awaiting owner verdicts (EP-M4)")`
through its scenario binding. EP-M4 removes the marker. The other scenarios
pass from EP-M1 or EP-M3 onwards.

## Milestones and plateaus

- EP-M0 (assigned to `RM-1.1.2` precondition). End state: the precondition is
  verified, `BASE` is recorded, and the baseline gates are green. Acceptance:
  the scrutineer report and the precondition evidence recorded in `Progress`.
  Conformance check: the 1.1.1 verdict is `proceed`, and OBS-01, OBS-02,
  OBS-03, and OBS-08 exist in `docs/job-corpus.md`. Recovery: none needed,
  because nothing changes. Remaining gaps: everything else.
- EP-M1 (INV-REG-1, INV-REG-2, and INV-DOC-1's renderer). End state: the
  register package, loader, verdict, renderer snapshot, and scenarios 2–5 pass.
  The seeded register audits as `pending-owner`, with findings limited to
  unresolved evidence and pending verdicts. Acceptance:
  `make check-fmt typecheck lint test` all pass, and
  `test_register_decisions_cover_every_area` passes. Conformance check: the
  domain-purity test covers the new modules, and no adapter code is in the
  domain. Recovery: revert the milestone commits; nothing depends on them yet.
  Remaining gaps: evidence, corpus jobs, verdicts, and documents.
- EP-M2 (INV-CTL-1, INV-BIND-1, LEM-BIND-2, INV-IN-1, LEM-IN-2, INV-FIN-1, and
  every probe). End state: every `probe:` and `property:` reference resolves
  and passes, and every control fails as predicted. Acceptance: the four gates
  pass, plus the new tests named in `Verification plan`. Conformance check: no
  sketch parses pokie text or exceeds 250 lines (overlap tolerance), and every
  witness agrees with the agenda's recommended rule. Recovery: each area is a
  separate commit, so a failing area can be reverted alone. Remaining gaps:
  corpus `case:` evidence, verdicts, and documents.
- EP-M3 (CX-07, CX-17, CX-18, and CX-20 corpus evidence). End state: three
  jobs pass under the reference and awk alternatives, and the corpus audit
  remains `proceed`. Acceptance: the four gates pass, and
  `test_reference_reproduces_expected[aggregate-port-changes/consecutive-ports]`
  passes. Conformance check: no observation of kind `contradiction` was
  needed. Recovery: delete a job directory and restore the pinned counts.
  Remaining gaps: verdicts and documents.
- EP-M4 (owner decision gate). End state: every decision has an owner verdict
  and date, revised rules are reflected in the evidence, and the verdict is
  `ratified`. Acceptance: the first scenario passes without its `xfail` marker,
  and the four gates pass. Conformance check: no decision was recorded without
  explicit owner acceptance. Recovery: verdicts are data in `register.toml` and
  can be reverted per decision. Remaining gaps: documents.
- EP-M5 (INV-DOC-1 and `RM-1.1.2` success). End state: ADRs, design,
  contracts, context, terms of reference, decision register, job-corpus
  findings, developers' guide, repository layout, contents, and roadmap are
  updated. The document-sync test passes. Acceptance:
  `make check-fmt typecheck lint test markdownlint nixie` all pass, and the full
  `make all` gate passes through the scrutineer. Conformance check: every
  `amended` decision appears in the design or contracts; ADR statuses match the
  verdicts; and the precondition, falsification, and owner constraints held
  throughout. Recovery: documentation commits are separate per document group.
  Remaining gaps: none for 1.1.2. Downstream obligations are listed in the
  register's `discharged_by` fields.

## Documentation changes

- `docs/adrs/adr-0002-preserve-one-program-scope-and-ordered-lifecycle.md`:
  restructure to the current template. Set Status to
  `Accepted (YYYY-MM-DD):
  one module namespace registered as __main__ and compiled as one unit;
  BaseException control signals with static anti-suppression rules;
  commit-after-guard bindings; end: only after EOF or exit`.
  Add `Decision drivers`, `Options considered` (keeping the existing
  alternatives), a decision outcome listing SCOPE-*, CONTROL-*, BIND-*, and
  FINAL-* by id, `Known risks and limitations` (context-manager suppression,
  `globals()` access, stale bindings), and `Architectural rationale`. Since the
  ADR is still `Proposed`, the body is edited directly and no amendment banner
  is needed.
- New `docs/adrs/adr-0005-give-the-record-reader-sole-ownership-of-input.md`
  (the next free number at execution time; 0004 is reserved by 1.1.1's plan).
  Status `Accepted (YYYY-MM-DD)`. It covers INPUT-1 to INPUT-9, options (shared
  stdin, guarded stdin, injected reader object, and structured readers), Q3 v1
  scope, and the 6.1.1 deferral.
- `docs/adrs/adr-0001-lower-pokie-through-python-asts.md`: Status
  `Accepted (YYYY-MM-DD)` for the compiler and lowering direction, adding the
  lowering constraints from SCOPE-1, SCOPE-2, BIND-1, and CONTROL-2. State that
  the runtime and distribution matrix is decided by Q2 (task 5.1.1). Use this
  wording only if the owner accepts it in EP-M4; otherwise, add the constraints
  and keep `Proposed`.
- `docs/pokie-design.md`: update the status line to ratified v0.2 with the
  date. Amend §3.1 (SCOPE-2, SCOPE-3, SCOPE-4, and INPUT-6), §3.2 (CONTROL-1
  keyword recognition), §4.1 (INPUT-2 to INPUT-5, INPUT-7, and INPUT-8), §4.2
  (SCOPE-1, FINAL-1 to FINAL-5, and the flush order), §4.3 (CONTROL-2 to
  CONTROL-6), §5 (BIND-1 to BIND-7), §7 (SCOPE-5 reserved names), §9 (CONTROL-3
  residual and INPUT-5), §10 (point Table 2 rows at the register's evidence),
  and §11 (add the lifecycle-spanning cleanup candidate). Cite the decision ids
  inline.
- `docs/design-contracts.md`: update the status line. Add §6 "Ratified
  semantic decisions", with the rendered table between markers and a caption.
  Amend §4 (the `-F` usage row, the no-input program, `SystemExit` semantics,
  and the broken-pipe `end:` column) and §2 (`Control` placement, with a
  pointer to CONTROL-4).
- `docs/context.md`: add control signal, initialization, record-scoped name,
  program namespace, ratified contract, counterexample, witness, and control
  (evidence), and fix the "after normal termination" wording for lifecycle
  blocks to include pokie `exit`.
- `docs/terms-of-reference.md` §9 Table 5: mark Q5 "Decided in task 1.1.2
  (ADR 0002 accepted)" and Q3 "v1 decided in task 1.1.2 (ADR 0005); expansion
  open for 6.1.1".
- `docs/decision-register.md`: Q5 status `Decided`, with the date and links.
  Q3 status `Partially decided`. Keep the table rows on single lines.
- `docs/job-corpus.md` "Phase 1 findings": record the dispositions of
  OBS-01, OBS-02, and OBS-08 (decided by INPUT-2, INPUT-3, and BIND-1), and
  OBS-03 (deferred to 1.2.1 as LEX-1). List the three new jobs.
- `docs/developers-guide.md`: add a "Contract ratification register" section
  covering the package layout, the register schema, how to add a decision,
  counterexample, or probe, the witness/control rule, the verdict values, that
  `owner_verdict` is set only on explicit owner acceptance, and the
  `discharged_by` obligation for later tasks.
- `docs/repository-layout.md`: add `tests/contract_ratification/`.
- `docs/contents.md`: add ADR 0005 and this ExecPlan.
- `docs/roadmap.md`: tick 1.1.2 at completion.
- `docs/users-guide.md`: no change (see `Decision log`).

## Concrete steps

Run every command from the repository root. Formatting comes before checking,
so every later gate describes one fixed tree. Use `tee` to keep the full logs:

```bash
BRANCH=$(git branch --show-current)
make fmt 2>&1 | tee /tmp/fmt-pokie-$BRANCH.out
make check-fmt 2>&1 | tee /tmp/check-fmt-pokie-$BRANCH.out
make typecheck 2>&1 | tee /tmp/typecheck-pokie-$BRANCH.out
make lint 2>&1 | tee /tmp/lint-pokie-$BRANCH.out
make test 2>&1 | tee /tmp/test-pokie-$BRANCH.out
make markdownlint 2>&1 | tee /tmp/markdownlint-pokie-$BRANCH.out
make nixie 2>&1 | tee /tmp/nixie-pokie-$BRANCH.out
```

Prefer delegating the full sequence to the `scrutineer` agent, which runs the
gates sequentially and returns a bounded report.

To run only this task's tests during red-green cycles:

```bash
uv run pytest -v -n 0 tests/test_contract_*.py tests/test_contract_ratification_*.py
```

Expected after EP-M1, before evidence exists (abridged):

```plaintext
tests/test_contract_ratification_scenarios.py::test_a_pending_owner_verdict_blocks_ratification PASSED
tests/test_contract_ratification_scenarios.py::test_every_contract_area_is_ratified XFAIL (awaiting owner verdicts (EP-M4))
```

Expected after EP-M4:

```plaintext
tests/test_contract_ratification_scenarios.py::test_every_contract_area_is_ratified PASSED
tests/test_contract_ratification_policy.py::test_ratification_verdict_is_ratified PASSED
```

To update the syrupy snapshot after an intended renderer change (serially,
because syrupy can corrupt snapshots under xdist):

```bash
uv run pytest -n 0 tests/test_contract_ratification_render.py --snapshot-update
```

To measure the budgets:

```bash
git diff --numstat BASE -- 'tests/**/*.py' ':!tests/job_corpus/jobs/**' \
  | awk '{a+=$1; d+=$2; n++} END {print n " files, " a-d " net lines"}'
git diff --numstat BASE -- 'tests/job_corpus/jobs/**' \
  | awk '{a+=$1; d+=$2; n++} END {print n " files, " a-d " net lines"}'
git diff --numstat BASE -- docs ':!docs/execplans/**' README.md \
  | awk '{a+=$1; d+=$2} END {print a-d " net lines"}'
```

Commit after each green step, with gates passing, using imperative subjects
such as "Add ratification register domain (1.1.2)".

## Validation and acceptance

The task is complete when all of the following hold:

- `make check-fmt`, `make typecheck`, `make lint`, `make test`,
  `make markdownlint`, and `make nixie` pass, and `make all` passes through the
  scrutineer.
- `test_ratification_verdict_is_ratified` passes against the repository
  register, and every decision has an owner verdict of `accepted` with a date.
- Each control test passes because its rejected alternative fails in the
  stated way. Turning a control into a witness (for example, making the sketch
  derive signals from `Exception`) makes the corresponding property fail with a
  shrunk example.
- `test_contract_table_matches_register` passes, and editing either side
  breaks it.
- ADR 0002 and ADR 0005 are `Accepted`. ADR 0001 is `Accepted` or remains
  `Proposed` according to the owner's verdict.
- Roadmap 1.1.2 is ticked.

## Idempotence and recovery

Every step is re-runnable. The register and corpus are data, loaded fresh on
each test run. Probes write only inside `ProcessRunner`'s temporary directory.
Sketches execute in fresh module objects. The one probe that installs a
`__main__` module runs in a subprocess, so the test process's `sys.modules` is
never changed. If a milestone fails halfway, revert to the last green commit
with `git revert` (never a destructive reset on a shared branch) and re-run the
milestone's red step. Snapshot updates are deterministic and serial.

## Artefacts and notes

Scratch probe transcript (CPython 3.14.7, 2026-11-14, from
`/tmp/pokie-112-probes/probes.py` and `p2.py`; not committed):

```plaintext
P1 failed-match leaves a: False None
guard-false leak: ada 7
P2 warnings: ['SyntaxWarning']
P2 swallowed, out= [0]
P3 except Exception passes signal
P3 bare except swallows
P4 suppress(BaseException) swallows, hit= 1
P5 genexpr sees ['b']
P6 plain dict pickle: PicklingError hints: ok
P6 registered module pickle: ok hints: ok
same unit: {'x': 'int'}
split unit: {'x': <class 'int'>}
P8 SyntaxError: return 1 - 'return' outside function
P8 SyntaxError: yield 1 - 'yield' outside function
P8 SyntaxError: await x - 'await' outside function
P8 SyntaxError: nonlocal x - nonlocal declaration not allowed at module level
P8 ok: global x
P9 helper in guard sees committed n -> guard False
P10 context: _Next
P12 lone CR split: ['a\n', 'b\n'] newline='': ['a\r', 'b\r\n', 'c']
P13 walrus in comprehension global y= 2
bare break in action stops record loop: ['a']
```

Research notes (Firecrawl, 2026-11-14):

- POSIX awk (Issue 8): "The exit statement shall invoke all END actions in
  the order in which they occur in the program source and then terminate the
  program without reading further input. An exit statement inside an END action
  shall terminate the program without further execution of END actions." `next`
  and `nextfile` in BEGIN or END are undefined. Inside END, `$0`, `NF`, and
  `NR` keep the last record's values.
- Python 3.14 reference, `match`: "Do not rely on bindings being made for a
  failed match. Conversely, do not rely on variables remaining unchanged after
  a failed match." Guards are evaluated in order and may have side effects.
- Python 3.14 reference, `try`: "If the finally clause executes a return,
  break or continue statement, the saved exception is discarded."
- PEP 765 (Final, 3.14): CPython emits `SyntaxWarning` for
  `return`/`break`/`continue` that exits a `finally` block.
- Python 3.14 `exec`: separate globals and locals execute "as if it were
  embedded in a class definition", and `return` and `yield` may not be used
  outside function definitions.
- PAWK: `-B`/`-E` statements, with per-line exceptions ignored unless
  `--strict` is given. This contrasts with FINAL-2's abort-without-`end:` rule.

## Interfaces and dependencies

No new dependencies. New test-only interfaces, under
`tests/contract_ratification/`:

```python
class ContractArea(enum.StrEnum):
    SCOPE = "scope"
    INPUT_OWNERSHIP = "input-ownership"
    CONTROL_TRANSFER = "control-transfer"
    BINDING_VISIBILITY = "binding-visibility"
    FINALIZATION = "finalization"
    LEXICAL = "lexical"  # routed items only, never counted as an area


class Disposition(enum.StrEnum):
    RATIFIED = "ratified"
    AMENDED = "amended"
    DEFERRED = "deferred"


class Effect(enum.StrEnum):
    UPHOLDS = "upholds"
    CLARIFIES = "clarifies"
    AMENDS = "amends"
    FALSIFIES = "falsifies"


class OwnerVerdict(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class RatificationVerdict(enum.StrEnum):
    RATIFIED = "ratified"
    PENDING_OWNER = "pending-owner"
    REVISE_CONTRACTS = "revise-contracts"


@dataclasses.dataclass(frozen=True, slots=True)
class Decision:
    id: str  # "CONTROL-3"
    area: ContractArea
    rule: str
    disposition: Disposition
    proposal: str  # where the original proposal lived, e.g. "DES-4.3"
    documents: tuple[str, ...]
    counterexamples: tuple[str, ...]
    evidence: tuple[str, ...]  # "probe:PRB-CTL-SWALLOW", "case:job/case", "obs:OBS-08", "property:name"
    discharged_by: tuple[str, ...]  # roadmap task ids
    owner_verdict: OwnerVerdict
    decided_on: str  # "" or YYYY-MM-DD


@dataclasses.dataclass(frozen=True, slots=True)
class Counterexample:
    id: str  # "CX-17"
    area: ContractArea
    summary: str
    effect: Effect
    evidence: tuple[str, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class Probe:
    id: str  # "PRB-SCOPE-DICT"
    role: typ.Literal["witness", "control", "axiom"]
    script: pathlib.PurePosixPath
    args: tuple[str, ...]
    stdin: str
    expected_stdout: str
    expected_status: int
    pairs_with: str  # the witness a control opposes, else ""


def audit_register(
    register: Register, evidence: EvidenceIndex
) -> RatificationReport: ...
def render_decision_table(register: Register) -> str: ...
```

`Register` groups decisions, counterexamples, and probes. `EvidenceIndex` holds
the sets of resolvable ids (probe outcomes, corpus case ids, OBS ids, property
names, and roadmap task ids) supplied by adapters. `RatificationReport` holds
the verdict and sorted findings, reusing `job_corpus.findings.Finding` if its
kinds can be extended without breaking the 1.1.1 policies. Otherwise it gets a
sibling type; decide at EP-M1 and record the choice. Semantic models expose
pure functions such as `expected_trace(shape, records) -> tuple[str, ...]`,
`expected_namespace(prior, attempts) -> dict[str, object]`,
`expected_records(data: bytes) -> tuple[str, ...]`, and
`expected_outcome(script) -> LifecycleOutcome`. Each adapter exposes the host
counterpart with the same signature, so tests compare them directly.

Register file shape (TOML, schema 1, unknown keys rejected):

```toml
schema = 1

[[decisions]]
id = "BIND-2"
area = "binding-visibility"
rule = "A guard sees candidates as locals; functions it calls see committed program state."
disposition = "ratified"
proposal = "DES-5"
documents = ["docs/adrs/adr-0002-preserve-one-program-scope-and-ordered-lifecycle.md", "docs/pokie-design.md"]
counterexamples = ["CX-18"]
evidence = ["probe:PRB-BIND-HELPER", "case:aggregate-port-changes/consecutive-ports"]
discharged_by = ["2.1.2", "3.2.1"]
owner_verdict = "pending"
decided_on = ""

[[counterexamples]]
id = "CX-18"
area = "binding-visibility"
summary = "A helper called from a guard reads the committed value, not the candidate."
effect = "clarifies"
evidence = ["probe:PRB-BIND-HELPER"]

[[probes]]
id = "PRB-BIND-HELPER"
role = "witness"
script = "probes/guard_helper.py"
args = []
stdin = ""
expected = { stdout = "None\n", exit_status = 0 }
pairs_with = ""
```

Reused from the 1.1.1 harness: `ProcessRunner` and `EvidenceFormatError`
(`tests/job_corpus/ports.py`), the strict TOML helpers in
`tests/job_corpus/adapters/toml_values.py` (promoted to public names if needed),
`model.Observation` and the corpus loader for `case:` and `obs:` resolution,
and, if 1.1.1's EP-M2 delivers it, `adapters/markdown_docs.py` for document
reads.

## Skills and documentation signposts

Load these skills during implementation:

- `execplans`, to maintain this plan;
- `hexagonal-architecture`, for the domain, port, and adapter split in
  `tests/contract_ratification/`;
- `python-router`, then `python-testing` (fixtures, parametrization, syrupy,
  pytest-bdd), `hypothesis` (shape strategies, `hypothesis.find` controls, and
  `event` statistics), and `python-verification` if a control's adequacy is in
  doubt;
- `python-data-shapes` and `python-types-and-apis`, for the frozen register
  values and `StrEnum` choices;
- `python-errors-and-logging`, for loader errors (reuse
  `EvidenceFormatError`);
- `skylos` and `ruff-016`, for dead-code and lint findings;
- `leta`, for navigation (install basedpyright, or fall back to reads);
- `en-gb-oxendict-style`, for prose;
- `commit-message` and `pr-creation`, for commits and the pull request.

Read these documents first: `AGENTS.md`; `docs/developers-guide.md` "Corpus
harness"; `docs/documentation-style-guide.md` "Architectural decision records";
`docs/complexity-antipatterns-and-refactoring-strategies.md` §4.A (single
responsibility, early abstraction, and guard clauses) and §5.C (structural
pattern matching and dispatch tables, for the sketch renderers);
`docs/scripting-standards.md` for probe-script conventions; and the 1.1.1
ExecPlan's `Surprises & discoveries` for tooling traps (the Ruff/Pylint
`except (A, B)` conflict, Interrogate covering private helpers, Vulture and
pytest-bdd, and the coverage-ratchet filtering).

## Revision note

2026-11-14: initial draft. It records the 1.1.1 precondition gap, the
ratification agenda (34 decisions and one routed lexical item), the
counterexample catalogue (CX-01 to CX-22), the witness/control verification
design, three corpus additions, and the owner decision gate. Expert-panel
review follows.
