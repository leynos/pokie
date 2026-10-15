# Establish the representative job corpus and decision register

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
`Tolerances`, `Risks`, `Progress`, `Surprises & discoveries`, `Decision log`,
`Outcomes & retrospective`, `Conformance basis`, and `Verification plan` must
be kept up to date as work proceeds.

Status: DRAFT

Roadmap item: `docs/roadmap.md` task 1.1.1, "Establish the representative job
corpus and decision register".

## Purpose / big picture

Pokie is a proposed language for Python-fluent command-line users: awk-like
ordered record processing with Python statements, regex capture dispatch, and
explicit validating or converting patterns. No interpreter exists. Phase 1 of
the roadmap asks whether the proposed contracts survive contact with real
text-processing jobs before anyone builds a parser, and says to "reject the
foundation if representative examples cannot be specified without incompatible
rules". Task 1.1.1 supplies the evidence that task 1.1.2 (ratification) and
later phases are judged against.

After this change, a reader can open `docs/job-corpus.md` and find eleven
representative jobs grouped as filtering, capture validation, and aggregation,
together with a "Phase 1 findings" section that lists every contract tension
the corpus exposed and states whether task 1.1.2 may proceed. Each job lives in
`tests/job_corpus/jobs/<job-id>/` and records the proposed pokie program, exact
input records, the exact expected standard output, exit status, and failure
category, and the alternatives a user has today: an awk program, a shell
pipeline where one is natural, prior art such as PAWK, and the status quo. A
second document, `docs/decision-register.md`, assigns an accountable decision
owner, evidence tasks, a "decide before" deadline, and gated roadmap tasks to
each of the open questions Q1–Q8 in `docs/terms-of-reference.md` §9, and links
each question to the jobs that bear on it.

The corpus is executable evidence. Running `make test` loads every job,
executes each job's *reference implementation* (a Python script that models the
proposed pokie semantics, standing in for the interpreter that does not yet
exist) and its awk and shell alternatives as real subprocesses, and checks that:

- the reference reproduces every expected outcome exactly;
- each other alternative agrees, or diverges only on cases where the job
  declares a divergence with a reason;
- the corpus covers all three categories and every required edge case;
- the decision register gives exactly one owner to each of Q1–Q8 and agrees
  with the jobs; and
- every recorded contract tension appears in the Phase 1 findings.

The proposed pokie programs are recorded but deliberately not executed; task
1.1.2 ratifies them and tasks 2.1.3 onwards execute them.

Success is observable. `make test` passes and reports one passing test per job
case, for example
`test_reference_reproduces_expected[validate-user-records/design-example]`.
Editing `tests/job_corpus/jobs/validate-user-records/job.toml` so that the case
expects `1 3` makes that test fail naming expected `1 3` and observed `1 2`.
Deleting the Q5 row from `docs/decision-register.md` makes the register test
fail naming `Q5`. Adding an observation of kind `contradiction` to any job
changes the audit verdict from `proceed` to `revise-contracts`.

## Constraints

- No product behaviour is introduced. `pokie/` must not be modified, and no
  document may describe pokie as able to run a corpus program. Proposed
  programs are labelled "proposed, not executable".
- The corpus must not silently change a design contract. A job that cannot be
  specified without contradicting `docs/design-contracts.md`,
  `docs/pokie-design.md`, or ADRs 0001–0003 is recorded as an observation of
  kind `contradiction`, which flips the audit verdict; the implementer then
  sets this plan to `BLOCKED` and escalates. This is the falsification output
  the phase 1 idea asks for; it must not be smoothed over.
- Decision owners must be roles that exist today. The only established role is
  the project owner (`@leynos`, terms-of-reference §4 Table 2). Do not invent
  sponsors, teams, or people.
- No runtime dependencies are added; `pyproject.toml` `dependencies` stays
  empty. Only `pytest-bdd`, `syrupy`, and `hypothesis` may be added, to the
  `dev` group.
- The harness lives under `tests/` and is never packaged
  (`[tool.hatch.build.targets.wheel] packages = ["pokie"]`).
- Every code file stays under 400 lines; functions respect the Ruff limits in
  `pyproject.toml` (`max-complexity = 8`, `max-args = 4`, `max-locals = 10`,
  `max-bool-expr = 2`).
- Subprocesses run with argument lists, never `shell=True`; every child gets
  an explicit environment allowlist; the reference implementation runs as
  `sys.executable -I`; no alternative uses the network or writes outside its
  temporary directory.
- Domain modules (`model.py`, `findings.py`, `policy.py`, `comparison.py`,
  `audit.py`, `report.py`) perform no I/O and import nothing from `adapters/`,
  `tomllib`, `subprocess`, `os`, `io`, `shutil`, or `tempfile`. `pathlib` is
  allowed only for `PurePosixPath`.
- Corpus input bytes live inside `job.toml` as single-line TOML basic strings
  (`text`) or hexadecimal (`hex`); the repository holds no separate input
  files. This avoids the `.gitignore` rule for `*.log`, binary files, and
  `tomllib`'s line-ending normalization in multi-line strings.
- All prose and identifiers use en-GB-oxendict spelling, except external API
  names.

## Tolerances (exception triggers)

- Scope: if the change needs more than 45 files outside
  `tests/job_corpus/jobs/`, or more than 1,200 net lines of Python outside that
  directory, stop and escalate.
- Interface: if anything under `pokie/` must change, stop and escalate.
- Dependencies: if anything beyond the three approved development dependencies
  is needed, stop and escalate.
- Contracts: if any job's expected outcome contradicts a proposed contract,
  record the `contradiction` observation, set this plan to `BLOCKED`, and
  escalate.
- Ownership: if the project owner rejects the proposed owner assignment or
  interim defaults during review, change the register only as directed.
- Tooling: if a lint gate rejects the job scripts and the only fix is to
  exclude `tests/` or `tests/job_corpus/` from that gate, stop and escalate
  rather than weakening it.
- Coverage: if the continuous integration (CI) coverage ratchet falls because
  harness branches are unreachable on Linux, restructure the harness; do not
  lower or bypass the ratchet.
- Runtime: if the new tests add more than 60 seconds to `make test` on this
  machine, stop and reduce subprocess fan-out.
- Portability: if mawk (CI) and GNU Awk (local) disagree on any case that is
  not a declared divergence, stop and escalate; do not add implementation
  special cases.
- Iterations: if a gate still fails after three fix attempts, stop and
  escalate.

## Risks

- Risk: the corpus is mostly synthetic, so "representative" is an assumption,
  not user evidence (terms-of-reference §8.2 Table 4). Severity: high.
  Likelihood: high. Mitigation: every job records
  `evidence_status = "Assumption"` and a `provenance` list; four jobs draw on
  public sources (Eric Pement's "Handy One-Line Scripts for AWK" v0.28 and the
  Apache Common Log Format); the register keeps Q1 open with an explicit `gap`
  for user observation; `docs/developers-guide.md` documents how to add a
  user-sourced job.
- Risk: the reference implementation is mistaken for an "ordinary user
  script" in comparisons. Severity: medium. Likelihood: medium. Mitigation: the
  kind is named `reference`; `docs/job-corpus.md` states that reference scripts
  deliberately model pokie semantics and are lint-conformant, so their size and
  shape are not evidence for roadmap task 5.2.2; no line counts are recorded.
- Risk: CI's `awk` is mawk, not GNU Awk. Evidence: the Ubuntu 24.04 runner
  image's installed-software list (version 20261004.327.1) has no gawk, and
  stock Ubuntu installs mawk as `awk`. Severity: medium. Likelihood: certain.
  Mitigation: awk alternatives use POSIX features only and validate numbers
  with explicit regular expressions, never numeric-string coercion; every awk
  case was run under mawk 1.3.4 in an `ubuntu:24.04` container during planning;
  `JOB_CORPUS_AWK` overrides the executable; the version (from `awk -W version`
  or `awk --version`) is shown in the pytest report header.
- Risk: awk checks skip silently where no `awk` exists. Severity: medium.
  Likelihood: low. Mitigation: a missing `awk` skips only when the `CI`
  environment variable is unset; under CI it fails.
- Risk: the coverage ratchet counts `tests/`. `generate-coverage` runs
  `python -m slipcover --branch -m pytest -v -n auto` without `--source`.
  Severity: medium. Likelihood: medium. Mitigation: unit tests reach every
  harness branch (each `EvidenceFormatError` key, timeout, missing script, awk
  absent via constructor argument); EP-M0, EP-M2, and EP-M3 run the CI coverage
  command locally.
- Risk: the strict lint stack (Ruff preview, Interrogate 100%, Pylint on PyPy
  3.12, Skylos, Vulture at 60% confidence, nose duplication with
  `min-size = 24`, `ty`) rejects step functions, unread model fields, or
  near-duplicate job scripts. Severity: medium. Likelihood: high. Mitigation:
  EP-M0 proves the toolchain on realistic code (the full domain model, one
  complete job with reference and awk scripts, and one scenario); Vulture gains
  `ignore_decorators` for pytest-bdd step decorators; `StrEnum` members reached
  from TOML text and fields whose consumers arrive in later milestones are
  declared in `tests/job_corpus/vulture_whitelist.py`, which
  `tests/test_job_corpus_dead_code.py` checks against Vulture in both
  directions so it cannot rot into a blanket exemption. (EP-M0 falsified the
  original claim here — "every model field is read by policy or the report" —
  because a member resolved by `enum_type(text)` is invisible to Vulture
  however much consuming code exists; see `Surprises & discoveries`.)
- Risk: Hypothesis deadlines flake under slipcover instrumentation on CI.
  Severity: low. Likelihood: medium. Mitigation: `tests/conftest.py` registers
  a default profile with `deadline=None` and a `ci` profile adding
  `derandomize=True`.
- Risk: `coverage-main.yml` sets up Python 3.13 while `requires-python` is
  `>=3.14`. Severity: low. Likelihood: unknown. Mitigation: EP-M0 confirms
  which interpreter the coverage run uses and records it in
  `Surprises & discoveries`; the reference scripts must not rely on 3.14-only
  behaviour beyond what `uv` installs.
- Risk: the decision register drifts from the corpus. Severity: medium.
  Likelihood: medium. Mitigation: INV-REG-2 makes the register's corpus
  evidence column and the jobs' `decisions` lists mutually derivable.
- Risk: `make fmt` (mdtablefix) re-pads or rewraps the register table and
  turns three consecutive full stops, even inside inline code, into a single
  ellipsis character. Severity: low. Likelihood: high. Mitigation: the register
  parser strips cells and tolerates alignment rows; EP-M4 runs `make fmt`
  before its green run and an adapter test parses an mdtablefix-formatted table.
- Risk: the corpus is Linux-only: Windows newline translation and macOS BWK
  awk are untested. Severity: low. Likelihood: low. Mitigation: state the
  Linux-only scope in the developers' guide.

## Progress

- [x] (2026-10-15) Branch renamed to
  `1-1-1-establish-the-representative-job-corpus-and-decision-register`,
  tracking the same name on `origin`.
- [x] (2026-10-15) Reconnaissance of the terms of reference, design,
  contracts, context, ADRs, roadmap, tooling, and test conventions.
- [x] (2026-10-15) Prior-art and format research: PAWK, pyawk, the POSIX awk
  specification, Pement's awk one-liners, the Apache log formats, and Markdown
  Architectural Decision Records (MADR) 4.0.0.
- [x] (2026-10-15) Scratch prototypes of every case under CPython 3.14, GNU
  Awk 5.3.0, and mawk 1.3.4.
- [x] (2026-10-15) Draft ExecPlan written.
- [x] (2026-10-15) Expert-panel review (semantics, architecture and
  contracts, testing, operations, product) and revision.
- [x] (2026-10-15) Firecrawl re-verification of POSIX awk, the CI runner
  image, pytest-bdd, and syrupy after credits were restored.
- [ ] Plan approved by the project owner, including owner assignments and
  interim defaults.
- [x] (2026-10-15) EP-M0: toolchain proof on realistic code. The domain types,
  the first job (`validate-user-records`) with its oracle and awk alternative,
  the runner, the parameterized tests, and the first scenario all exist and
  pass. Every gate passes: `check-fmt`, `typecheck`, `lint` (all ten sub-gates,
  including the five pylint had previously aborted), `test` (44 passed, no
  skips), `markdownlint`, `nixie`, `audit`, `spelling`, `validate`, and the CI
  coverage command under CPython 3.14.7. Non-vacuity is enforced by
  `test_corpus_is_non_vacuous`, and the Vulture whitelist is guarded in both
  directions by `tests/test_job_corpus_dead_code.py`.
- [ ] EP-M1: domain policy, comparison, and audit with unit and property
  tests.
- [ ] EP-M2: adapters, runner, report snapshots, and unhappy scenarios.
- [ ] EP-M3: corpus content and executable alternatives.
- [ ] EP-M4: decision register document and register tests.
- [ ] EP-M5: documentation, ADR 0004, Phase 1 findings, and roadmap
  completion.

## Surprises & discoveries

- Observation: Firecrawl research first failed with "Insufficient credits",
  so prior-art pages were read with WebFetch. After credits were restored the
  same day, Firecrawl re-verified the load-bearing sources. Evidence and impact:
  - The POSIX awk specification says input not ending in a newline is read
    as if it did, so it still forms a final record, and that `for (key in
    array)` order is unspecified. It also lets implementations accept
    hexadecimal, infinity, and NaN spellings as numeric strings. This
    confirms the `sorted-lines` comparison and the rule that awk
    alternatives validate numbers with explicit regular expressions.
  - The installed-software list for runner image `ubuntu-24.04` version
    20261004.327.1 has no gawk entry, so CI's `awk` is Ubuntu's default,
    mawk.
  - The pytest-bdd 9.0.0 documentation confirms the `bdd_features_base_dir`
    option, `scenarios()`, Scenario Outline substitution, and
    `target_fixture`.
  - syrupy's README still states "Pytest >=5.1, <9", but the 6.1.1 PyPI
    metadata requires only `pytest>=8.0.0`, and the testing reviewer's
    experiment passed on pytest 9.1.1. The README also describes advisory
    file locks under xdist; the plan keeps the more conservative
    `-n 0` rule for `--snapshot-update` because 6.1.1 warned about it in
    practice.
- Observation: Python's `int(s, 10)` accepts Arabic-Indic digits, digit
  separators, and signs (`٤٢`, `1_000`, `+7`), so the design's `int` adapter
  accepts all three while an awk validator accepts only `+7`. Evidence:
  prototype printed `3 0` (reference) and `1 2` (awk). Impact: the first
  declared divergence and direct Q6 evidence (OBS-05).
- Observation: Python's native `match` statement leaks bindings from a case
  whose guard fails. Evidence: prototype printed `native match leak: -1`.
  Impact: the reference implementation must model the proposed binding
  transaction explicitly; lowering in task 2.1.2 inherits the same obligation
  (OBS-08).
- Observation: a Python script iterating a text-mode file decodes in chunks,
  so an invalid byte on line 2 fails before line 1 is printed. The design says
  only that the reader "yields decoded lines". Impact: the expected output of
  `filter-error-lines/invalid-utf8` rests on a reading the design does not fix;
  recorded as ambiguity OBS-02 for task 1.1.2.
- Observation: `$3.isascii()` is lexically ambiguous because `3.` is a Python
  float literal. Impact: programs write `($9).isascii()`; recorded as OBS-03.
- Observation: CI uses mawk. Evidence: `ubuntu:24.04` resolves `awk` to
  `/usr/bin/mawk` (mawk 1.3.4 20240123); every awk alternative produced the
  same output as GNU Awk 5.3.0.
- Observation: `.gitignore` ignores `*.log`. Impact: corpus inputs are inline
  in `job.toml`; input names such as `app.log` exist only in the temporary
  directory the runner creates.
- Observation: `tomllib` converts `\r\n` to `\n` inside multi-line strings.
  Impact: inputs use single-line escaped strings or hexadecimal.
- Observation: pytest-bdd 9.0.0, syrupy 6.1.1, and Hypothesis 6.169.4 work
  with pytest 9.1.1 on CPython 3.14 under `-n auto`; `bdd_features_base_dir`
  resolves against the root directory, and `target_fixture` works on `given` and
  `when`. syrupy warns that `--snapshot-update` under xdist can corrupt
  snapshot files. Vulture at 60% confidence reports every pytest-bdd step
  function as unused. Evidence: scratch experiment by the testing reviewer.
- Observation: `coverage-main.yml` and `audit.yml` declare
  `python-version: '3.13'` in their `actions/setup-python` step, while
  `pyproject.toml` requires `>=3.14` and `ci.yml` and `act-validation.yml`
  declare `'3.14'`. The coverage workflow's Python is only the default on
  `PATH`; `uv` reads `requires-python` and provisions its own 3.14 interpreter,
  so the test run is 3.14 in every workflow and the corpus's interpreter-
  dependent expectations (the `int` adapter, per-record decoding) are exercised
  on one version. Impact: none for this task, which is why it is recorded as an
  observation and not raised as a blocker. `coverage-main.yml` still runs the
  same `uv run python -m slipcover` command this plan verifies locally.
- **Falsified: the "Ruff 3.14 formatter and Pylint on PyPy 3.12 agree"
  toolchain hypothesis.** Stage A asks for one
  `except (ValueError, TypeError):` handler "to prove the Ruff 3.14 formatter
  and Pylint on PyPy 3.12 agree on its syntax". They do not agree, and the
  disagreement is an exact inversion. Evidence: with the parentheses written,
  `ruff format --check` reports "File would be reformatted" and its proposed
  edit is to *delete* them, because `target-version = "py314"` enables the PEP
  758 rewrite; `pylint` pinned to `pypy@3.12` (`Makefile:37`) then reports
  `E0001: Parsing failed: 'multiple exception types must be parenthesized'`.
  With the parentheses omitted, the reverse holds: pylint rates 10.00/10 and
  Ruff rewrites them back. The two tools cannot both be satisfied by the bare
  form. `PYTHON_TARGETS` is
  `git ls-files --cached --others --exclude-standard '*.py' '*.pyi'`
  (`Makefile:25`), so the oracle is in scope for both gates and cannot be
  excused by path. Impact and resolution: the parenthesized form is pinned with
  a trailing `# fmt: skip` and a comment giving both reasons, which is the
  narrowest escape hatch that satisfies each tool. This is the first such
  suppression in the repository, so it is recorded here rather than passed over
  silently. The underlying cause is the pinned pylint interpreter, not the
  handler: the corpus keeps the parenthesized form because `except` clauses
  with multiple types are ordinary Python, and the PEP 758 shorthand buys
  nothing here. A future change that moves pylint off PyPy 3.12 could adopt the
  shorthand directly and delete the `# fmt: skip`; recorded so that whoever
  does it knows why the comment exists.
- Observation: two lint gates the plan does not name are load-bearing. First,
  `make lint` runs `interrogate --fail-under 100` over every Python target
  (`Makefile:123`), so every function in the harness, including every private
  helper and every dunder, needs a docstring; `RUF067` is ignored only for
  `__init__.py`. Second, the same target runs `DF12_PYLINT`, `AMBRLEAKS`, the
  shared Skylos dead-code and duplication checks, and `lint-actions` in one
  recipe, so any earlier sub-gate that aborts leaves the rest unverified rather
  than passing. Evidence: the first full `make lint` failed at pylint and
  reported five later sub-gates as never having run. Impact: a lint failure
  must be recorded as "these sub-gates are unverified", never as a pass, and
  the gate must be re-run to completion after a fix.
- Observation: `ruff format` under `target-version = "py314"` rewrites
  `except (A, B):` to the PEP 758 `except A, B:`, while `DOC502`
  (`docstring-extraneous-exception`) counts only an exception raised *directly*
  in a function body, so a helper that raises via another function cannot
  document `Raises` at the call site. Evidence: both reproduced in isolation.
  Impact: the loader documents `EvidenceFormatError` once, on `_fail`, and
  describes the malformed values it reports inside each loader's `Returns`
  section instead — the same shape `scripts/action_workflow.py` uses for its
  propagated errors.
- Observation: `pytest-bdd` resolves each step function's annotations eagerly
  through `inspect.signature` when it collects the feature file, so a type-only
  annotation on a step function is evaluated at runtime and its import cannot
  be deferred into `if typ.TYPE_CHECKING:`. Evidence: deferring the import in
  `tests/test_job_corpus_scenarios.py` raised
  `NameError: name 'process_runner' is not defined` from a scenario that had
  otherwise passed. Quoting the annotation is not available either, because
  Ruff's `UP` rules flag it as `quoted-annotation`. Impact: the one deferred
  import in the step module carries a targeted
  `# ruff: ignore[typing-only-third-party-import]` with the reason inline.
- Observation: `ty` reports 15 diagnostics against the first `toml_jobs.py`
  draft, of which 13 stem from two causes: `_fail` lacked a `NoReturn`
  annotation, so the checker could not see that the `isinstance` guards
  terminate, and the `_member`/`_members` type parameter was bounded by
  `model.Failure` while the functions are also called with `QuestionId`,
  `CaseTag`, `JobCategory`, `Comparison`, `ObservationKind`, and
  `EvidenceStatus`. Bounding it by `enum.StrEnum`, the shared supertype,
  removes the nine-member union that had been written to fix it. Impact:
  recorded because a reviewer reading only the final code cannot see that the
  narrow bound was ever wrong, and the same mistake is easy to repeat.
- **Falsified: the mitigation this plan's own Risk entry relies on.** The Risk
  section says "every model field is read by policy or the report, so Vulture
  has nothing to flag" (line 1553). That is untrue in two different ways, and
  the `dead-code` gate reports 69 findings once Ruff, Interrogate, Pylint, and
  DF12_PYLINT pass. (a) The 47 `StrEnum` members are a *wire format*: a member
  is reached when a `job.toml` string names it, through `toml_values._member`,
  which calls `enum_type(text)`. Constructing a member from text is a runtime
  lookup, so no consumer that EP-M1 through EP-M5 adds can ever make Vulture
  see it. (b) The 19 dataclass fields and the `RegisterEntry` class are
  genuinely premature: `policy.py` and `report.py` read fields by attribute,
  which does clear Vulture, so those findings would have resolved on their own.
  Evidence: `Failures.RED`-style probes showed that a literal `Colour.RED`
  expression clears a member, while construction, keyword construction, and
  iteration all leave it reported; a `Thing(title=..., reason=...)`
  construction leaves every field reported, while an attribute read clears
  them. Impact and resolution: the permanent cases cannot be fixed by waiting,
  so the plan needs a mechanism the model cannot provide. Two candidate
  mechanisms were tested and rejected: dotted `ignore_names` entries
  (`"Colour.RED"`) match nothing, and bare names (`"RED"`) would exempt every
  same-named symbol repository-wide. The resolution is Vulture's own documented
  mechanism, a scanned whitelist module at
  `tests/job_corpus/vulture_whitelist.py`, written as tuple assignments of real
  attribute access so that `ty` fails the build if a whitelisted name is
  renamed or deleted. A stale whitelist would silently exempt dead code, so
  `tests/test_job_corpus_dead_code.py` closes the loop: it re-runs Vulture with
  the whitelist excluded and asserts the two name sets are *equal*, failing on
  an entry Vulture no longer reports as well as on a reported name the
  whitelist omits. That makes the list self-clearing as later milestones land
  their consumers. Both directions were falsification-tested: adding
  `model.Failure.NONE` and deleting `model.Failure.GUARD` each fail the guard
  with the offending name printed. A third hazard was found while writing the
  guard: Vulture matches by *name*, not by scope, so the guard's own local
  variable `owner` masked `RegisterEntry.owner` and made the entry look stale;
  the locals are now named `declaring` and `classes` to keep the scan honest.

## Decision log

- Decision: represent each job as a directory under `tests/job_corpus/jobs/`
  holding `job.toml`, `program.pokie`, `reference.py`, and, where useful,
  `alternative.awk` and `alternative.sh`. Rationale: `tomllib` needs no new
  dependency; separate script files keep Python, awk, and shell readable and
  let Ruff, `ty`, and Interrogate check the reference scripts as real code;
  `docs/repository-layout.md` reserves `tests/` for language fixtures.
  Date/Author: 2026-10-15, planning agent.
- Decision: the Python script that defines expected outcomes is a
  `reference` implementation that deliberately models proposed pokie semantics
  (per-record decoding, binding transactions, failure prefixes), not an
  "ordinary user script". Awk and shell alternatives are independent
  implementations whose disagreements must be declared. Rationale: two
  implementations in different languages make a wrong expectation hard to hide,
  while separating the oracle from user-facing alternatives keeps roadmap task
  5.2.2's comparison honest (panel finding). Date/Author: 2026-10-15, planning
  agent after panel review.
- Decision: keep a pure domain core and a single port, `ProgramRunner`,
  instead of separate source ports, a service layer, and three adapters.
  Loading uses plain functions composed in `tests/conftest.py`. Rationale: the
  panel showed the extra ports had one adapter each and no stand-in
  implementation, which is the over-abstraction that
  `docs/complexity-antipatterns-and-refactoring-strategies.md` warns about. The
  runner is a real seam: task 2.1.3 adds a pokie runner. Date/Author:
  2026-10-15, planning agent after panel review.
- Decision: failure categories mirror `docs/design-contracts.md` §4 Table 2
  (`none`, `static`, `initialization`, `input`, `guard`, `adapter`, `action`,
  `end`, `broken-pipe`), with the invariant that `none` implies status 0,
  `static` implies status 2, and every other category implies status 1.
  Rationale: tasks 2.2.2 and 2.2.3 need targets for every row. Date/Author:
  2026-10-15, planning agent after panel review.
- Decision: record contract tensions as typed `observations`
  (`contradiction`, `ambiguity`, `ergonomic-smell`, `host-divergence`) in
  `job.toml`. The audit derives a verdict (`proceed` or `revise-contracts`), and
  `docs/job-corpus.md` must mention every observation identifier. Rationale:
  the phase 1 idea needs an explicit go/no-go output to task 1.1.2, not notes
  buried in data. Date/Author: 2026-10-15, planning agent after panel review.
- Decision: the decision register is a Markdown table in
  `docs/decision-register.md` between HTML comment markers, parsed by a test
  loader. Rationale: it is a governance document the project owner edits, so
  one authoritative copy belongs in `docs/`. Date/Author: 2026-10-15, planning
  agent.
- Decision: every question's decision owner is the project owner, `@leynos`,
  following the MADR split between decision-makers and those who produce
  evidence. The register adds "decide before" and an interim default so an
  owner of everything still conveys when and what. Q1 and Q8 carry an explicit
  `gap` where no roadmap task produces the evidence. Rationale: the project
  owner is the only established role; Q8 itself asks who else should hold
  authority. Requires confirmation at plan approval. Date/Author: 2026-10-15,
  planning agent after panel review.
- Decision: ADR 0004 records only the corpus schema and the reference and
  divergence model; the register format and module boundaries go in the
  developers' guide. Rationale: the documentation style guide asks for one
  decision per ADR, and later tasks depend on the schema. Date/Author:
  2026-10-15, planning agent after panel review.
- Decision: reject the "executable Markdown corpus" alternative (fenced
  program, input, and expected-output blocks in `docs/job-corpus.md`).
  Rationale: it removes duplication and would serve 5.2.2's requirement that
  published examples execute from Markdown, but it loses Ruff, `ty`, and
  Interrogate coverage of reference scripts and cannot represent invalid UTF-8
  or unterminated lines without sidecar files. Revisit at 2.2.3, when runnable
  guides become a requirement. Date/Author: 2026-10-15, planning agent after
  panel review.
- Decision: `dead-code` findings that the corpus cannot resolve are handled by
  a scanned whitelist module, `tests/job_corpus/vulture_whitelist.py`, rather
  than by Vulture `ignore_names` entries or inline `# noqa: vulture` comments.
  Rationale: dotted `ignore_names` entries (`"Colour.RED"`) match nothing, and
  bare ones (`"RED"`) would exempt every same-named symbol repository-wide,
  which the `Constraints` section's stance against weakening gates rules out.
  The whitelist is ordinary source that `ty` type-checks, so a renamed or
  deleted model member breaks the build rather than silently rotting the
  exemption, and `tests/test_job_corpus_dead_code.py` asserts the whitelist and
  Vulture's own findings are equal sets so an entry is deleted the moment its
  consumer lands. Date/Author: 2026-10-15, implementation agent at EP-M0.

## Outcomes & retrospective

Not started. Complete at each milestone and at completion, reconciling any
discovery with the documents in `Conformance basis`.

## Context and orientation

The repository is a Python 3.14 project managed by `uv`. The package `pokie/`
holds only a scaffold `hello()` function. The language exists only as documents:

- `docs/terms-of-reference.md` defines goals G1–G5 (§6.1), success criteria
  (§7 Table 3), assumptions (§8.2 Table 4), and open questions Q1–Q8 (§9 Table
  5). §9 states "Owners are unassigned unless stated. Roadmap task 1.1.1
  assigns decision owners".
- `docs/pokie-design.md` is the proposed technical design: §3 syntax and
  lexing, §4 records, fields, lifecycle, and control transfer, §5 captures and
  cases, §6 adapters, §9 failures, §10 verification, §11 deferred scope.
- `docs/design-contracts.md` is canonical where it disagrees with the design.
  §1 holds the only worked example (the user-record program printing `1 2`), §3
  the adapter catalogue (`digits`, `hexstr`, `int`, `float`), and §4 the
  command-line interface (CLI) contract with exit statuses in Table 2.
- `docs/context.md` defines vocabulary (record, field, capture, rule, case,
  guard, adapter, binding) and the evidence statuses `Established`,
  `Agreed basis`, `Assumption`, `Proposed contract`, `Open question`, and
  `Deferred`.
- ADRs 0001–0003 (`docs/adrs/adr-000n-*.md`) are all `Proposed`.
- `docs/roadmap.md` lists tasks as `- [ ] N.N.N.` checkboxes.

Terms used in this plan:

- A *job* is one text-processing task a user wants done, such as "count
  accepted and rejected user records".
- A *case* is one concrete run of a job: named inputs, command-line operands,
  and the expected outcome.
- An *expected outcome* is the exact standard output bytes, the exit status,
  and a failure category.
- The *reference implementation* is a Python script that computes what the
  proposed pokie program should do, by following the design's contracts.
- An *alternative* is another way to do the job today: an awk program, a
  shell pipeline, prior art such as PAWK, or the *status quo* (keeping the
  user's existing approach, which terms-of-reference §5 calls valid).
- A *declared divergence* is a case on which a job states that one
  alternative legitimately produces a different outcome, with a reason.
- An *observation* is a recorded contract tension exposed by a job.
- The *decision register* is the table assigning owners to Q1–Q8.
- *Ports and adapters* (hexagonal architecture): the domain defines the
  interfaces (ports) it needs, and adapter modules implement them with real
  I/O. Here the domain is corpus policy; the single port runs programs.

Test conventions in `tests/`: flat `test_*.py` modules with a module docstring,
a docstring and `-> None` on every test, assertion messages held in a `why`
variable. Ruff requires `import typing as typ`,
`import collections.abc as cabc`, `import dataclasses`, and `import enum`
rather than `from` imports. Ruff's relaxed test rules apply only to
`**/test_*.py`; the harness package gets the full rule set, so magic numbers
become named constants. Tests run as `pytest -v -n auto` with a 30-second
per-test timeout.

## Conformance basis

Upstream revisions are those at commit `ccbf884` ("Apply Episodic lint
standards (#12)"):

- Terms of reference: `docs/terms-of-reference.md`, draft v0.1, revised
  2026-10-09. Traced items: TOR-JTBD (§5), TOR-G1–TOR-G5 (§6.1), TOR-SC-G1 and
  TOR-SC-G2G3 (§7 Table 3 rows "User-facing, G1" and "User-facing, G2/G3"),
  TOR-ALT (§3 Table 1 alternatives), TOR-A4 (§8.2 "Capture cases reduce parsing
  glue"), TOR-Q1–TOR-Q8 (§9 Table 5).
- Technical design: `docs/pokie-design.md`, proposed v0.1, updated
  2026-10-10. Traced items: DES-3.2 (lexical boundaries), DES-4.1 (input and
  fields), DES-4.2 (lifecycle), DES-4.3 (control transfer), DES-5 (captures and
  cases), DES-9 (failure model), DES-10 (verification evidence).
- Contracts: `docs/design-contracts.md` DC-1 (user-record example), DC-3
  (adapter catalogue), DC-4 (CLI outcomes, Table 2).
- ADRs: ADR-0002 (execution scope and lifecycle, Proposed), ADR-0003 (pattern
  adapter resolution, Proposed). ADR-0001 is context only.
- Roadmap: RM-1.1.1 success criterion "filtering, capture validation, and
  aggregation jobs have inputs, expected outcomes, alternatives, and assigned
  decision owners for Q1–Q8", and the phase 1 falsification clause.
- Standards: `AGENTS.md`, `.rules/python-*.md`,
  `docs/documentation-style-guide.md`, and `docs/scripting-standards.md` for
  subprocess hygiene (the harness is not a standalone script, so the PEP 723
  and Cyclopts rules do not apply).

Trace chains:

```plaintext
RM-1.1.1 categories -> TOR-G1, TOR-SC-G1 -> EP-M3 -> INV-COV-1 -> test_corpus_is_non_vacuous
RM-1.1.1 inputs and outcomes -> TOR-SC-G1, TOR-SC-G2G3 -> EP-M3 -> INV-ORACLE-1
  -> test_reference_reproduces_expected[*]
RM-1.1.1 alternatives -> TOR-ALT, TOR-JTBD -> EP-M3 -> INV-ORACLE-2
  -> test_alternative_agrees_or_declares_divergence[*]
RM-1.1.1 owners -> TOR-Q1..TOR-Q8 -> EP-M4 -> INV-REG-1, INV-REG-2
  -> test_repository_register_is_complete_and_consistent
RM-1.1.1 phase 1 falsification -> EP-M1, EP-M5 -> INV-VERDICT-1 -> docs/job-corpus.md "Phase 1 findings"
DC-1 -> validate-user-records/design-example -> INV-ORACLE-1
DES-4.1 -> unterminated, empty-field, out-of-range, multiple-files cases -> INV-COV-1
DES-4.2, DES-4.3, ADR-0002 -> filter-first-timeouts, filter-skip-comments, invalid-utf8 cases
DES-5, DC-1 binding transaction -> validate-last-good-uid -> OBS-08
DC-3 -> declared divergences on python-int-spellings and float-spellings -> OBS-05, OBS-09 -> TOR-Q6
DC-4 Table 2 -> Failure enum -> INV-FAIL-1
```

## Verification plan

The change introduces validation policy over data and an oracle relationship
between data and executable implementations. The obligations below make "the
corpus is correct" falsifiable.

Axioms (trusted, not verified here):

- AXIOM-1: CPython 3.14's `re.search`, `int(s, 10)`, `float(s)`,
  `str.split`, and `bytes.decode("utf-8")` behave as documented. The design
  defines its adapters by these functions (DC-3).
- AXIOM-2: `tomllib` conforms to TOML 1.0, preserving escape sequences in
  single-line basic strings exactly.
- AXIOM-3: the `awk` on `PATH` implements the POSIX features the alternatives
  use (`match`, `substr`, `split`, regular-expression matching, `next`, `exit`
  running `END`). Local evidence: GNU Awk 5.3.0 and mawk 1.3.4. POSIX lets
  implementations differ on hexadecimal, infinity, and NaN numeric strings, so
  alternatives must not depend on numeric-string coercion.
- AXIOM-4: `subprocess.run` reports the child's exit status and captures its
  output bytes faithfully.

Obligations:

- Obligation INV-ORACLE-1: for every case, the reference implementation run
  on the case's operands produces exactly the expected standard output bytes
  and exit status; its standard error is empty when the expected failure is
  `none`, and otherwise starts with `<failure> error:`.
  - Method: parameterized end-to-end tests over the real corpus.
  - Rationale: the corpus is a finite, enumerated specification of named
    examples.
  - Domain: all eighteen cases.
  - Artefact:
    `tests/test_job_corpus_alternatives.py::test_reference_reproduces_expected`.
  - Evidence: `make test`. Red: a stub `reference.py` that prints nothing
    fails with "expected b'1 2\n', observed b''".
  - Non-vacuity: parameters are loaded at import time from a sorted glob with
    stable identifiers; `empty_parameter_set_mark = "fail_at_collect"` turns
    an empty corpus into a collection error; `test_corpus_is_non_vacuous`
    asserts exactly eighteen cases, five filtering, four capture-validation,
    and two aggregation jobs. Negative controls: the behavioural scenario
    expecting `1 3`, and the failure-prefix check, which rejects a crash
    (`NameError`) on a case expecting an `input` failure.
- Obligation INV-ORACLE-2: for every executable non-reference alternative,
  the outcome (stdout and exit status, under the alternative's `comparison`,
  `exact` or `sorted-lines`) equals the expected outcome on every case not
  listed in its `divergences`, and differs on every case that is listed.
  - Method: parameterized end-to-end tests.
  - Rationale: the second clause catches stale declarations, which would
    otherwise hide a mistaken expectation.
  - Domain: every `(job, case, alternative)` triple with an awk or shell
    script.
  - Artefact:
    `tests/test_job_corpus_alternatives.py::test_alternative_agrees_or_declares_divergence`.
  - Evidence: `make test` locally (GNU Awk) and in CI (mawk). A missing
    `awk` skips only when `CI` is unset.
  - Non-vacuity: declared divergences exist on four cases
    (`filter-error-lines/invalid-utf8`, `aggregate-status-counts/invalid-utf8`,
    `validate-user-records/python-int-spellings`,
    `aggregate-endpoint-latency/float-spellings`); unit tests of
    `comparison.evaluate_agreement` cover all four agreement classes; a
    behavioural scenario shows a stale declaration is reported.
- Obligation INV-COV-1: the corpus has at least two jobs in each category
  and every tag in the `CaseTag` vocabulary appears on at least one case.
  - Method: Hypothesis property of `policy.find_coverage_gaps` plus the
    concrete repository test.
  - Domain: generated tuples of minimal valid jobs with arbitrary categories
    and tag subsets, including the empty tuple.
  - Artefacts:
    `tests/test_job_corpus_properties.py::test_coverage_gaps_match_model`
    and `tests/test_job_corpus_policy.py::test_corpus_is_non_vacuous`.
  - Evidence: the property asserts that missing categories are exactly those
    with zero jobs, under-populated categories exactly those with one, and
    missing tags exactly the vocabulary minus the tags present.
  - Non-vacuity: pinned examples for the empty corpus, a complete corpus, and
    a corpus with exactly one job in one category. Red: a stub returning `()`
    fails the empty-corpus example with an assertion difference.
- Obligation INV-REG-1: the register has exactly one row for each of Q1–Q8
  and no other identifiers; each owner is non-blank and not a placeholder
  (`TBD`, `unassigned`, `-`); every evidence task, "decide before" task, and
  gate is either a task number in `docs/roadmap.md` or the token `gap`
  (evidence tasks only); and "decide before" does not come after the earliest
  gate in roadmap order.
  - Method: Hypothesis property of `policy.find_register_gaps` plus the
    concrete repository test.
  - Domain: generated multisets of rows drawn from Q1–Q9 with valid, blank,
    or placeholder owners and task identifiers drawn from a generated
    roadmap.
  - Artefacts:
    `tests/test_job_corpus_properties.py::test_register_gaps_match_model`
    and `tests/test_job_corpus_register.py::test_repository_register_is_complete_and_consistent`.
  - Non-vacuity: pinned examples for the valid register, an empty register, a
    duplicated Q5, an unknown Q9, and a deadline after a gate. Negative
    controls: behavioural scenarios removing Q5 and naming task `9.9.9`.
- Obligation INV-REG-2: for every question, the register's corpus evidence
  equals the set of jobs whose `decisions` include it (the token `all` means
  every job; `none` means the empty set); each observation's questions are a
  subset of its job's `decisions`.
  - Method: parameterized unit tests of `policy.find_evidence_mismatches`.
  - Non-vacuity: cases for a job missing from the register, a register
    naming an unknown job, an exact match, and `all`.
- Obligation INV-FAIL-1: every expected outcome's failure category agrees
  with its exit status as DC-4 Table 2 requires.
  - Method: exhaustive parameterized test over the nine `Failure` members and
    statuses 0, 1, and 2, plus the repository audit.
  - Non-vacuity: the table includes every mismatching pair and asserts each
    is reported.
- Obligation INV-VERDICT-1: the audit verdict is `revise-contracts` if and
  only if any job has an observation of kind `contradiction`; every observation
  identifier appears in `docs/job-corpus.md`.
  - Method: Hypothesis property over generated observation lists plus the
    concrete repository test, and a behavioural scenario.
  - Non-vacuity: pinned examples with zero observations, only ambiguities,
    and one contradiction.
- Obligation LEM-LOAD-1: the TOML loader maps a job file to domain values
  without altering input bytes, and rejects malformed files with the file path
  relative to the corpus root and the TOML key.
  - Method: parameterized loader tests using `tmp_path`.
  - Domain: `text` inputs with and without a final `\n`, `hex` inputs with
    invalid UTF-8, empty `text`, a multi-line string containing `\r\n`
    (rejected), missing required keys, wrong types, unknown enum values,
    unknown keys, and a schema version other than 1.
  - Artefact: `tests/test_job_corpus_toml.py`.
  - Non-vacuity: assertions compare bytes, so a loader that appends or
    strips a final newline fails the unterminated example.
- Obligation INV-ORDER-1: for `filter-error-lines`, the reference output is
  exactly the input records matching `\bERROR\b`, in input order, each followed
  by a newline.
  - Method: Hypothesis property executing the real subprocess through
    standard input (`operands = ["-"]`), compared against an in-test model.
  - Rationale: G1 requires ordered records; a model check covers order and
    completeness, so an alternative that prints nothing cannot pass.
  - Domain: lists of 0–20 records of printable text excluding every Python
    line separator (`\n`, `\r`, `\x0b`, `\x0c`, `\x1c`–`\x1e`, `\x85`,
    ` `, ` `) and surrogates, with roughly half containing
    `ERROR`; output is split only on `b"\n"`. Settings: `max_examples=25`,
    `deadline=None`.
  - Artefact:
    `tests/test_job_corpus_alternatives.py::test_filter_reference_matches_ordered_model`.
  - Non-vacuity: a permanent unit test feeds the model checker a sorted
    output for a pinned out-of-order input and asserts it is rejected.
- Obligation INV-REPORT-1: the audit report renders every finding kind in a
  stable, ordered, corpus-relative format.
  - Method: two `syrupy` snapshots (every finding kind; a clean report),
    each paired with assertions on finding count and kinds.
  - Rationale: the report is the multivariant output a developer reads when
    a gate fails.
  - Artefact: `tests/test_job_corpus_report.py` and
    `tests/__snapshots__/test_job_corpus_report.ambr`.
  - Non-vacuity: paths are corpus-relative inside the domain, so nothing
    needs redaction; environment-specific data such as the awk version is
    kept out of the report and appears only in assertion messages.

- Obligation INV-DEADCODE-1: the Vulture whitelist exempts only names Vulture
  still reports, so it can never become a blanket exemption.
  - Method: `tests/test_job_corpus_dead_code.py` re-runs Vulture with the
    whitelist excluded by path, resolves each finding to a dotted
    `Class.member` name through `ast`, and asserts set equality with the
    whitelist's declarations. Both directions were falsification-tested: a
    stale entry and a missing entry each fail with the offending name.
  - Rationale: the whitelist exists because `StrEnum` members resolved from
    TOML text are invisible to Vulture however much consuming code exists, and
    an unguarded exemption list decays into "ignore all dead code".
  - Artefact: `tests/test_job_corpus_dead_code.py` and
    `tests/job_corpus/vulture_whitelist.py`.
  - Non-vacuity: the guard fails if Vulture cannot run, so an environment
    without `vulture` reports an error rather than passing.

No obligation needs symbolic execution or a proof: the domain logic is set
arithmetic, ordering, and byte comparison, which enumerated examples and
properties cover at proportionate cost. The residual gap is that no test can
show the corpus represents real users; the register assigns that gap to Q1.

## Corpus specification

This is the content EP-M3 creates. Every job records
`evidence_status = "Assumption"`. Expected outputs are exact byte strings in
Python escape notation. Every outcome below was reproduced on 2026-10-15 by
scratch prototypes under CPython 3.14, GNU Awk 5.3.0, and mawk 1.3.4.
`earliest_task` names the roadmap task that first executes a case through pokie.

Required tags (the whole `CaseTag` vocabulary): `empty-input`,
`unterminated-final-line`, `empty-field`, `out-of-range-field`,
`malformed-record`, `multiple-files`, `stdin`, `early-exit`, `next-record`,
`multiple-rules`, `input-failure`, `optional-capture`, `guard-rejection`,
`adapter-rejection`, `binding-isolation`, `preserved-text`, `unicode`.

Common Log Format (CLF) records follow the Apache documentation, for example
`127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif
HTTP/1.0" 200 2326`.
Under default whitespace splitting, `$7` is the path and `$9` the status.

### Filtering jobs

`filter-error-lines` (G1, G5; Q1, Q5; provenance: Pement, "print only lines
which match regular expression"). Program:

```plaintext
when /\bERROR\b/:
    print($0)
```

- Case `mixed-levels` (tags `unterminated-final-line`; earliest 2.1.3):
  records `2026-10-01T10:00:00 INFO started`,
  `2026-10-01T10:00:01 ERROR disk full`, `2026-10-01T10:00:02 WARN retrying`,
  and `2026-10-01T10:00:03 ERROR disk still full` without a final newline.
  Expected the two `ERROR` records, each newline-terminated; status 0.
- Case `empty-input` (tags `empty-input`; earliest 2.1.3): one empty input;
  expected empty output, status 0.
- Case `invalid-utf8` (tags `input-failure`; earliest 2.2.2): `hex` input
  encoding `ok ERROR one\n`, `\xff\xfe ERROR\n`, `later ERROR\n`. Expected
  `ok ERROR one\n`, status 1, failure `input`.
- Alternatives: awk `/(^|[^A-Za-z0-9_])ERROR([^A-Za-z0-9_]|$)/` and shell
  `grep -E` with the same expression, both declaring a divergence on
  `invalid-utf8` (neither validates encodings); status quo `grep -w ERROR`.
- Observations: OBS-01 (ambiguity, DES-4.1): "normalizing standard text line
  endings" does not say whether a lone `\r` or `U+2028` ends a record; corpus
  inputs avoid both until 1.1.2 decides. OBS-02 (ambiguity, DES-4.1 and DES-9):
  the design does not fix decoding granularity, so whether `ok ERROR one` is
  printed before the failure depends on per-record decoding; the expected
  outcome assumes per-record decoding.

`filter-server-errors` (G1; Q1, Q4, Q6; provenance: Pement `awk '$NF > 4'`
pattern and Apache CLF). Program:

```plaintext
when NF >= 9 and ($9).isascii() and ($9).isdigit() and int($9) >= 500:
    print($7)
```

- Case `access-log` (tags `malformed-record`, `unterminated-final-line`;
  earliest 2.1.3): six records: statuses `200`, `503` (path `/upload`), `500`
  (`/health`), a record `truncated record`, a record with status `abc`, and a
  final unterminated record with status `502` (`/report`). Expected
  `/upload\n/health\n/report\n`, status 0.
- Alternatives: awk `NF >= 9 && $9 ~ /^[0-9]+$/ && $9 + 0 >= 500 { print $7 }`;
  status quo, a Python loop with `split()` and `int()`.
- Observations: OBS-03 (ambiguity, DES-3.2): `$9.isascii()` is ambiguous
  because `9.` lexes as a float, so parentheses are needed. OBS-04 (ergonomic
  smell, DC-3): adapters work only in pattern position, so an expression
  predicate rebuilds `digits` by hand (`isascii() and isdigit()`;
  `"²".isdigit()` is true). Questions Q4, Q6.

`filter-missing-email` (G1; Q1, Q3; provenance: synthetic). Program:

```plaintext
start:
    FS = ","

when $3 == "":
    print($1)
```

- Case `team-roster` (tags `empty-field`, `out-of-range-field`; earliest
  2.1.3): records `1,Ada,ada@example.com`, `2,Lin,`, `3,"Smith, J",`, `4,,`, and
  `5`. Expected `2\n4\n5\n`, status 0. Record 3 has an empty email but its
  quoted comma shifts the fields, so it is not printed.
- Alternatives: awk `-F,`; status quo, Python's `csv` module, which would
  print 3.
- Observations: OBS-07 (ergonomic smell, DES-4.1): a literal separator
  silently misreads quoted CSV fields; users needing CSV must own structured
  input, which is Q3.

`filter-first-timeouts` (G1; Q1, Q5; provenance: Pement head emulation
`awk 'NR>1{exit};1'`). Program:

```plaintext
start:
    shown = 0

when /timeout/:
    print($0)
    shown += 1
    if shown == 2:
        exit

end:
    print(f"read {NR}")
```

- Case `stops-after-two` (tags `early-exit`; earliest 2.2.1): records `a`,
  `timeout 1`, `b`, `timeout 2`, `timeout 3`. Expected
  `timeout 1\ntimeout 2\nread 4\n`, status 0: `exit` still runs `end:` and `NR`
  counts delivered records only (ADR-0002).
- Alternatives: awk; status quo, a Python loop with `break` and a counter.

`filter-skip-comments` (G1; Q1, Q5; provenance: synthetic). Program:

```plaintext
when /^#/:
    next

when /ERROR/:
    print("error:", $0)

when NF > 2:
    print("long:", NR)
```

- Case `comments-and-rules` (tags `stdin`, `next-record`, `multiple-rules`;
  operands `["-"]`; earliest 2.2.1): records `# ERROR in comment a b c`,
  `ERROR disk full now`, `ok`, `x y z`. Expected
  `error: ERROR disk full now\nlong: 2\nlong: 4\n`, status 0: `next` skips
  later rules, and two rules fire on record 2.
- Alternatives: awk (same three rules); status quo, a Python loop with
  `continue`.

### Capture-validation jobs

`validate-user-records` (G2, G3; Q1, Q5, Q6; provenance:
`docs/design-contracts.md` §1, copied verbatim).

- Case `design-example` (tags `malformed-record`, `guard-rejection`,
  `adapter-rejection`; earliest 4.1.2): records `user=ada uid=42`,
  `user=lin uid=no`, `user=sam uid=-1`. Expected `1 2\n`, status 0.
- Case `python-int-spellings` (tags `unicode`; earliest 4.1.2): records
  `user=ravi uid=٤٢`, `user=kim uid=1_000`, `user=lee uid=+7`. Expected
  `3 0\n`. The awk alternative prints `1 2` and declares the divergence: its
  explicit regular expression accepts only ASCII signed decimals.
- Alternatives: awk using `match` and `substr`; prior art, PAWK
  (`pawk -B 'users = {}' ...` with the capture tuple `m`, text only); status
  quo, a Python loop with `re.search`, `try`/`except ValueError`, and a
  `Counter`.
- Observations: OBS-05 (ergonomic smell, DC-3): `int` accepts non-ASCII
  digits, digit separators, signs, and surrounding whitespace, which is broader
  than many users expect from "uid is an integer". Question Q6.

`validate-request-ids` (G2, G3; Q1, Q4, Q6; provenance: synthetic). Program:

```plaintext
start:
    malformed = 0

when /req=(\S+) ms=(\S+)/:
    case hexstr(rid), digits(ms):
        print(rid, ms)
    case _:
        malformed += 1

end:
    print(f"malformed {malformed}")
```

- Case `mixed-ids` (tags `malformed-record`, `preserved-text`; earliest
  4.1.2): records `req=00ff ms=12`, `req=zz01 ms=5`, `req=ABC ms=0x1`,
  `req=1a2b ms=007`, `no request here`. Expected
  `00ff 12\n1a2b 007\nmalformed 2\n`, status 0: preserving adapters keep
  leading zeros, and the last record does not match the regex, so it is not
  counted.
- Alternatives: awk; prior art, PAWK (text only); status quo.
- Notes: a stricter identifier rule (for example, even length) would need a
  custom adapter, which is Q4 evidence.

`validate-optional-unit` (G2, G3; Q1, Q5, Q6; provenance: synthetic). Program:

```plaintext
when /size=(?P<n>\d+)(?: unit=(?P<unit>\w+))?/:
    case {"n": int(n), "unit": None}:
        print(n, "bytes")
    case {"n": int(n), "unit": "KiB"}:
        print(n * 1024, "bytes")
    case {"n": n, "unit": unit}:
        print("unknown unit", unit)
```

- Case `units` (tags `optional-capture`; earliest 4.1.2): records `size=10`,
  `size=2 unit=KiB`, `size=3 unit=parsec`, `size=4 unit=`. Expected
  `10 bytes\n2048 bytes\nunknown unit parsec\n4 bytes\n`, status 0.
- Case `empty-input` (tags `empty-input`; earliest 4.1.2): expected empty
  output, status 0.
- Alternatives: awk; prior art, PAWK (text only); status quo.
- Observations: OBS-06 (ergonomic smell, DES-5): because `\w+` cannot match
  an empty string, `size=4 unit=` leaves the optional group unmatched and is
  silently treated as bytes; the pattern cannot tell a missing unit from an
  empty one.

`validate-last-good-uid` (G2, G3; Q1, Q5; provenance: synthetic, derived from
DC-1's binding rule). Program:

```plaintext
start:
    uid = None
    accepted = 0

when /uid=(\S+)/:
    case (int(uid),) if uid >= 0:
        accepted += 1

end:
    print(uid, accepted)
```

- Case `rejections-keep-last-good` (tags `binding-isolation`,
  `guard-rejection`, `adapter-rejection`; earliest 3.2.1): records `uid=42`,
  `uid=-1`, `uid=x`. Expected `42 1\n`, status 0: the false guard on `-1` must
  not publish its candidate binding.
- Alternatives: awk (natural, because awk has no pattern bindings); status
  quo.
- Observations: OBS-08 (host divergence, DES-5 and ADR-0002): Python's own
  `match` statement leaves `uid` as `-1` here, so the reference implementation,
  and later the lowering in task 2.1.2, must implement the binding transaction
  explicitly rather than relying on native `match`.

### Aggregation jobs

`aggregate-status-counts` (G1, G4; Q1, Q7; provenance: Apache CLF and Pement's
counting idioms). Program:

```plaintext
from collections import Counter

start:
    counts = Counter()

when NF >= 9:
    counts[$9] += 1

end:
    for status, total in sorted(counts.items()):
        print(status, total)
```

- Case `access-log` (tags `malformed-record`; earliest 2.1.3): five CLF
  records with statuses `200`, `503`, `200`, `404`, `200` and one record
  `truncated record`. Expected `200 3\n404 1\n503 1\n`, status 0.
- Case `empty-input` (tags `empty-input`; earliest 2.1.3): empty output,
  status 0.
- Case `invalid-utf8` (tags `input-failure`; earliest 2.2.2): one valid CLF
  record then a record containing `\xff`. Expected empty output, status 1,
  failure `input`: `end:` does not run after an input failure (ADR-0002), so no
  partial aggregate is printed.
- Alternatives: awk with `comparison = "sorted-lines"` (POSIX leaves
  `for (key in array)` order unspecified); shell
  `awk 'NF >= 9 { print $9 }' "$@" | sort | uniq -c | awk '{ print $2, $1 }'`
  run with `LC_ALL=C`. Both declare a divergence on `invalid-utf8`.
- Notes: this is the named non-accumulating-per-record workload for roadmap
  task 5.2.1.

`aggregate-endpoint-latency` (G1, G3, G4; Q1, Q3, Q6, Q7; provenance:
synthetic). Program:

```plaintext
import math
from collections import defaultdict
from statistics import fmean

start:
    samples = defaultdict(list)
    rejected = 0

when /^(\S+) (\S+)$/:
    case endpoint, float(ms) if ms >= 0 and math.isfinite(ms):
        samples[endpoint].append(ms)
    case _:
        rejected += 1

end:
    for endpoint in sorted(samples):
        print(f"{endpoint} {fmean(samples[endpoint]):.2f}")
    print(f"rejected {rejected} of {NR}")
```

- Case `two-files` (tags `multiple-files`, `unterminated-final-line`;
  earliest 4.1.2): `a.log` holds `/a 10`, `/b 3.5`, `/a 20` without a final
  newline; `b.log` holds `/b nan`, `/a 30`, `/b 4.5`, `/c -1` without a final
  newline. Expected `/a 20.00\n/b 4.00\nrejected 2 of 7\n`, status 0. Both
  files are unterminated, so a reader that concatenates files would join
  `/a 20` and `/b nan` and fail this case.
- Case `float-spellings` (earliest 4.1.2): `c.log` holds `/d 1e3` and
  `/d inf`. Expected `/d 1000.00\nrejected 1 of 2\n`. The awk alternative prints
  `rejected 2 of 2` and declares the divergence: its explicit decimal regular
  expression rejects exponent notation, whereas `float` follows Python's
  `float()`.
- Alternatives: awk with `sorted-lines`; status quo.
- Observations: OBS-09 (ergonomic smell, DC-3): `float` accepts `nan` and
  `inf`, so the program needs a `math.isfinite` guard; DC-3 already states that
  `float` is not a finite-number validator. Question Q6.

### Phase 1 verdict input

No planned case contradicts a proposed contract. OBS-01, OBS-02, and OBS-03 are
ambiguities for task 1.1.2 to resolve; OBS-04 to OBS-07 and OBS-09 are
ergonomic smells for Q4 and Q6; OBS-08 is a lowering obligation. The audit
verdict is therefore expected to be `proceed`. If an implementer finds a
contradiction while writing reference scripts, the verdict must flip and the
plan must be set to `BLOCKED`.

## Plan of work

### Stage A: toolchain proof on realistic code (EP-M0)

Add `pytest-bdd`, `syrupy`, and `hypothesis` to the `dev` group with
`uv add --dev`. In `pyproject.toml` add to `[tool.pytest.ini_options]`:
`bdd_features_base_dir = "tests/features"`, `pythonpath = ["tests"]`, and
`empty_parameter_set_mark = "fail_at_collect"`; add `"docs/"` to
`[tool.mutmut] also_copy`; add
`ignore_decorators = ["@given", "@when", "@then"]` to `[tool.vulture]` (not
`@pytest.fixture`, which would hide dead fixtures); add
`[tool.ty.environment] extra-paths = ["tests"]` only if `ty` cannot resolve
`job_corpus` without it.

Create `tests/conftest.py` with the Hypothesis profiles. Create the complete
`tests/job_corpus/model.py` (every type in `Interfaces and dependencies`), the
first job `tests/job_corpus/jobs/validate-user-records/` with its
`reference.py` and `alternative.awk`, a minimal runner and one test that runs
the reference on `design-example`, and one scenario in
`tests/features/job_corpus.feature` with its step module. Include one
`except (ValueError, TypeError):` handler to prove the Ruff 3.14 formatter and
Pylint on PyPy 3.12 agree on its syntax.

Run every gate, then the CI coverage command
(`uv run python -m slipcover --branch -m pytest -n auto`). Record the
interpreter used by `coverage-main.yml`. Fix any gate here, before more code
exists.

### Stage B: domain policy (EP-M1)

Red: write `tests/test_job_corpus_policy.py`,
`tests/test_job_corpus_comparison.py`, and
`tests/test_job_corpus_properties.py` against stubs with the final signatures
that return `()` or a fixed wrong value, so tests fail on assertion differences
rather than import errors. Mark red tests
`@pytest.mark.xfail(strict=True, reason="EP-M1 red")` if they must be committed
before green; remove the markers in the green commit.

Green: implement `tests/job_corpus/findings.py` (finding and verdict types),
`policy.py` (`find_coverage_gaps`, `find_identity_errors`,
`find_failure_mismatches`, `find_register_gaps`, `find_evidence_mismatches`,
`find_undocumented_observations`, `derive_verdict`), `comparison.py`
(`compare_outcome`, `evaluate_agreement`), and `audit.py` (`audit_corpus`, a
pure function over loaded values). Add `tests/test_job_corpus_boundaries.py`,
which parses each domain module's abstract syntax tree and fails if it imports
a forbidden module or anything from `job_corpus.adapters`.

### Stage C: adapters, runner, and report (EP-M2)

Implement `tests/job_corpus/ports.py` (`ProgramRunner`), `adapters/toml_jobs.py`
(`load_jobs`), `adapters/markdown_docs.py` (`load_register`,
`load_roadmap_task_ids`), `adapters/process_runner.py` (`ProcessRunner`), and
`report.py` (`render_report`). Compose them in `tests/conftest.py` fixtures
(`corpus_root`, `repository_jobs`, `process_runner`, `awk_executable`). Red
first in `tests/test_job_corpus_toml.py`, `tests/test_job_corpus_runner.py`,
`tests/test_job_corpus_register.py` (against `tmp_path` documents), and
`tests/test_job_corpus_report.py`. Add the unhappy behavioural scenarios.

The runner materializes inputs in a `tempfile.TemporaryDirectory`, replaces
each operand name with its path (or passes `-` and feeds the single input on
standard input), and runs:

- reference: `[sys.executable, "-I", script, *args, *operands]` with
  environment `{"PATH": <inherited PATH>, "LC_ALL": "C.UTF-8"}`;
- awk: `[awk, *args, "-f", script, *operands]` with
  `{"PATH": <inherited PATH>, "LC_ALL": "C"}`;
- shell: `["sh", script, *operands]` with the awk environment.

It uses `capture_output=True` and an injectable timeout (default 10 seconds);
`subprocess.TimeoutExpired` becomes an `ObservedOutcome` with `timed_out=True`
rather than an exception. A missing script becomes an `EvidenceFormatError` for
that case only, never a collection error. A unit test asserts each
environment's exact keys.

### Stage D: corpus content (EP-M3)

For each job in `Corpus specification`, in category order: write `job.toml` and
`program.pokie`, then a stub `reference.py` that prints nothing, and run the
focused test, which must fail with an expected-versus-observed message whose
observed output is `b''` (red). Write the real reference (green), then the awk
and shell alternatives, observing agreement or the declared divergence. Commit
after each category. Run the alternative tests once under mawk, using uv's
Debian image (Debian installs mawk as a required package) and a container-only
environment so the host `.venv` is untouched:

```bash
podman run --rm -v "$PWD":/w:Z -w /w -e UV_PROJECT_ENVIRONMENT=/tmp/venv \
  -e JOB_CORPUS_AWK=mawk ghcr.io/astral-sh/uv:python3.14-bookworm-slim \
  uv run pytest -q -n 0 tests/test_job_corpus_alternatives.py -k alternative_agrees
```

Record the transcript in `Artefacts and notes`. If the image cannot be pulled,
run each `alternative.awk` by hand in `docker.io/library/ubuntu:24.04` against
the case inputs, as the planning prototypes did. Add the happy-path Scenario
Outline.

### Stage E: decision register (EP-M4)

Write `test_repository_register_is_complete_and_consistent` first; it fails
with "register markers not found". Write `docs/decision-register.md`, run
`make fmt`, then run the test (green). Add the register scenarios.

### Stage F: documentation and completion (EP-M5)

Write the documentation in `Documentation changes`, including the "Phase 1
findings" section, run every gate, and mark roadmap 1.1.1 done.

## Decision register specification

`docs/decision-register.md` opens with its purpose, the status vocabulary from
`docs/context.md` §1, and the meaning of each column. The authoritative table
sits between `<!-- decision-register:start -->` and
`<!-- decision-register:end -->`, each surrounded by blank lines, with the
caption outside the markers. Columns: `ID`, `Decision owner`, `Evidence tasks`,
`Decide before`, `Gates`, `Corpus evidence`, `Status`. Proposed rows (every
owner is `@leynos (project owner)`; every status is `Open question`):

```plaintext
Q1 | 1.1.1, gap | 5.2.2 | 5.2.2                          | all
Q2 | 5.1.1      | 5.1.2 | 5.1.2, 5.1.3                   | none
Q3 | 1.1.2, 6.1.1 | 2.1.3 | 2.1.3                        | filter-missing-email, aggregate-endpoint-latency
Q4 | 4.2.1      | 4.2.2 | 4.2.2, 4.2.3                   | filter-server-errors, validate-request-ids
Q5 | 1.1.2      | 2.1.2 | 2.1.2, 2.2.1, 2.2.2, 3.2.1, 3.2.2 |
     filter-error-lines, filter-first-timeouts, filter-skip-comments,
     validate-user-records, validate-optional-unit, validate-last-good-uid
Q6 | 1.1.1, 4.1.1 | 4.1.2 | 4.1.2, 6.1.2                 |
     filter-server-errors, validate-user-records, validate-request-ids,
     validate-optional-unit, aggregate-endpoint-latency
Q7 | 5.2.1      | 5.2.1 | 5.2.1, 5.2.2                   | aggregate-status-counts, aggregate-endpoint-latency
Q8 | gap        | 5.2.2 | 5.2.2                          | none
```

Below the table, one subsection per question gives the interim default that
applies until the decision is made, the options on the table (from
terms-of-reference §9 "Suggested path" and design §11), the corpus cases and
observations that bear on it, and what would close it:

- Q1: interim, the corpus is a candidate, not the "agreed corpus" its
  resolution criterion requires; `gap`, no roadmap task observes users.
- Q2: interim, CPython 3.14 on Linux, matching the scaffold (design §3.2).
- Q3: interim, read-only fields and one reader (design §4.1); 1.1.2 ratifies
  this for v1, and 6.1.1 decides any expansion; OBS-07.
- Q4: interim, built-in catalogue only; OBS-04.
- Q5: interim, ADR-0002 as proposed; OBS-01, OBS-02, OBS-03, OBS-06, OBS-08.
- Q6: interim, `digits`, `hexstr`, `int`, `float` as DC-3; OBS-04, OBS-05,
  OBS-06, OBS-09.
- Q7: interim, no thresholds and no speed claims; thresholds must be agreed
  before 5.2.1 measures, so they cannot be fitted to results.
- Q8: interim, the project owner acts as sponsor and release approver pending
  elicitation; `gap`, no roadmap task elicits this. To be confirmed by
  `@leynos`, not by the implementer.

## Behavioural specification

`tests/features/job_corpus.feature`:

```gherkin
Feature: Representative job corpus and decision register
  Pokie's first release must demonstrate filtering, capture validation, and
  aggregation jobs whose outcomes are specified before any interpreter exists.

  Scenario Outline: A representative job's reference reproduces its outcomes
    Given the repository job "<job>"
    When the job's reference implementation runs against every case
    Then every observed outcome matches its expected outcome

    Examples:
      | job                     |
      | filter-error-lines      |
      | validate-user-records   |
      | aggregate-status-counts |

  Scenario: The repository corpus audit recommends proceeding
    Given the repository job corpus
    And the decision register in docs/decision-register.md
    When the corpus is audited
    Then the audit reports no findings
    And the verdict is "proceed"

  Scenario: A contradiction observation blocks ratification
    Given a temporary copy of the job "validate-user-records"
    And the job records an observation of kind "contradiction"
    When the corpus is audited
    Then the verdict is "revise-contracts"

  Scenario: A job whose expected output is wrong is rejected
    Given a temporary copy of the job "validate-user-records"
    And its "design-example" case expects standard output "1 3" and a newline
    When the job's reference implementation runs against every case
    Then the case "design-example" reports expected "1 3" and observed "1 2"

  Scenario: A stale divergence declaration is reported
    Given a temporary copy of the job "validate-user-records"
    And its awk alternative declares a divergence on "design-example"
    When the job's awk alternative runs against every case
    Then the case "design-example" reports a stale divergence

  Scenario: An alternative that exceeds the time limit is reported
    Given a temporary copy of the job "filter-error-lines"
    And its reference implementation never terminates
    When the job's reference implementation runs with a 0.5 second limit
    Then the case "mixed-levels" reports a timeout

  Scenario: A register missing a question is rejected
    Given the repository job corpus
    And a decision register without the row for "Q5"
    When the corpus is audited
    Then the audit reports that "Q5" has no owner

  Scenario: A register gate naming an unknown roadmap task is rejected
    Given the repository job corpus
    And a decision register whose "Q4" gates include "9.9.9"
    When the corpus is audited
    Then the audit reports that "9.9.9" is not a roadmap task

  Scenario: A malformed job file is rejected with its location
    Given a temporary job file that lacks the key "expected"
    When the corpus is loaded
    Then loading fails naming the job file and the key "expected"
```

Step definitions live in `tests/test_job_corpus_scenarios.py`, which calls
`pytest_bdd.scenarios("job_corpus.feature")` and uses `parsers.parse` for
quoted values. The full case sweep stays in the parameterized tests; the
outline uses one job per category to keep runtime and failure noise low.

## Milestones and plateaus

- EP-M0: development dependencies and configuration in place; the model,
  one complete job, one runner path, and one scenario pass every gate and the
  CI coverage command.
  - Requirements: de-risks every later milestone.
  - Acceptance: `make check-fmt`, `make typecheck`, `make lint`, and
    `make test` succeed in sequence.
  - Conformance check:
    - No product code touched.
    - Only the three approved development dependencies added.
    - Trace links unchanged.
  - Recovery: revert the commit; `uv sync` restores the previous lock.
  - Remaining gaps: policy, adapters, remaining jobs, register, documents.
  - Compatibility decision: none.
- EP-M1: pure policy, comparison, and audit with passing unit, boundary, and
  property tests.
  - Requirements: INV-COV-1, INV-REG-1, INV-REG-2, INV-FAIL-1,
    INV-VERDICT-1 at policy level.
  - Acceptance: focused tests then all four gates pass.
  - Conformance check:
    - The boundary test proves domain purity.
    - No public interface or dependency change.
    - Trace links current.
  - Recovery: revert the milestone commit.
  - Remaining gaps: loaders, runner, report, content.
  - Compatibility decision: none.
- EP-M2: loaders, runner, report, and unhappy scenarios pass against
  temporary corpora.
  - Requirements: LEM-LOAD-1, INV-REPORT-1, and the runner half of
    INV-ORACLE-1 and INV-ORACLE-2.
  - Acceptance: all four gates and the CI coverage command pass.
  - Conformance check:
    - Adapters depend only on the domain and the port; no adapter imports
      another.
    - Subprocess use follows `Constraints`, including environment allowlists.
  - Recovery: revert the milestone commit.
  - Remaining gaps: real corpus content and register.
  - Compatibility decision: none.
- EP-M3: eleven jobs and eighteen cases; references reproduce every outcome;
  awk and shell agree or declare divergences under GNU Awk and mawk; the
  coverage audit is clean.
  - Requirements: RM-1.1.1 categories, inputs, expected outcomes, and
    alternatives; INV-ORACLE-1, INV-ORACLE-2, INV-COV-1, INV-ORDER-1.
  - Acceptance: `make test` shows eighteen passing
    `test_reference_reproduces_expected` parameters.
  - Conformance check:
    - Every outcome is consistent with DES-4.1, DES-4.2, DES-4.3, DES-5,
      DES-9, DC-1, DC-3, and DC-4, or a `contradiction` observation exists
      and the plan is `BLOCKED`.
    - Proposed programs are labelled not executable.
  - Recovery: one commit per category; revert the failing one.
  - Remaining gaps: register and documentation.
  - Compatibility decision: none.
- EP-M4: `docs/decision-register.md` passes the register tests and
  scenarios.
  - Requirements: RM-1.1.1 owners; INV-REG-1; INV-REG-2.
  - Acceptance: all gates, including `make markdownlint` and `make nixie`.
  - Conformance check:
    - Owners name only established roles; interim defaults match the design.
    - Gates and deadlines exist in `docs/roadmap.md`.
  - Recovery: revert the commit.
  - Remaining gaps: documentation.
  - Compatibility decision: none.
- EP-M5: documentation, ADR 0004, Phase 1 findings, and roadmap updated; plan
  `COMPLETE`.
  - Requirements: AGENTS.md documentation duties; INV-VERDICT-1 at document
    level.
  - Acceptance: every gate in `Validation and acceptance` passes; the
    verdict line in `docs/job-corpus.md` matches the audit.
  - Conformance check:
    - Terms of reference §9 and design §10 and §11 point to the register and
      corpus.
    - README makes no new capability claim.
    - Roadmap 1.1.1 checked.
  - Recovery: documentation commits revert independently.
  - Remaining gaps: Q1–Q8 stay open by design; task 1.1.2 works through the
    observations.
  - Compatibility decision: none.

## Documentation changes

- `docs/adrs/adr-0004-define-the-job-corpus-schema-and-reference-oracle.md`
  (new, title "Define the job corpus schema and reference oracle", status
  `Proposed`): context (no interpreter; RM-1.1.1), decision drivers, options
  considered (executable Markdown corpus; TOML corpus with a reference oracle
  and declared divergences; YAML corpus; Gherkin-only examples), chosen option,
  schema versioning (`schema = 1`; unknown keys rejected; any incompatible
  change bumps the version), consequences (reference scripts are maintained
  code; awk portability discipline; reference scripts are not user-effort
  evidence), and outstanding decisions (OBS-01 and OBS-02 for 1.1.2).
- `docs/job-corpus.md` (new): purpose and evidence status; how to read a job
  directory; a list of jobs linking to their directories (no copied data);
  "Phase 1 findings", listing OBS-01 to OBS-09 with their classification,
  affected contracts, questions, and recommendation, ending in a verdict line
  ("Verdict: proceed to 1.1.2 with OBS-01, OBS-02, and OBS-03 as its agenda");
  and how the corpus feeds tasks 1.1.2, 2.1.3, 2.2.2, 2.2.3, 3.2.2, 4.2.3,
  5.1.2, 5.2.1, and 5.2.2.
- `docs/decision-register.md` (new): as specified above.
- `docs/context.md` §2: add job, case, reference implementation, alternative,
  declared divergence, observation, and decision owner.
- `docs/design-contracts.md`: a short section naming the corpus schema as the
  evidence contract for later tasks and linking ADR 0004.
- `docs/pokie-design.md` §10: one paragraph naming the corpus as the input to
  differential checks, linking ADR 0004; §11: link the register.
- `docs/terms-of-reference.md` §9: replace "Owners are unassigned unless
  stated. Roadmap task 1.1.1 assigns decision owners" with a pointer to
  `docs/decision-register.md`; §7 Table 3: link the corpus from "Filtering and
  aggregation corpus".
- `docs/developers-guide.md`: section "Job corpus and decision register"
  covering layout, the red-first procedure for adding a job (including a
  user-sourced job with `provenance`), reference conventions (per-record
  decoding, failure prefixes, explicit binding transactions, no native `match`
  with guards, deterministic ordering), awk and shell conventions (POSIX only,
  explicit regular-expression validation, `LC_ALL=C`), declaring divergences
  and observations, maintaining the register and its parser constraints, module
  boundaries and their reuse policy, snapshot updates with `-n 0`, the `awk`
  requirement and `JOB_CORPUS_AWK`, and the Linux-only scope.
- `docs/users-guide.md`: short section "Representative jobs" explaining that
  the corpus shows what pokie is intended to do, that its programs are proposed
  and not executable, and where to read expected outcomes. The section links to
  the corpus instead of embedding fenced programs, because the documentation
  style guide requires every fenced example in a user-facing document to be
  executable and tested, and no pokie program can run yet.
- `docs/contents.md`: add the job corpus and register documents, and ADR 0004
  under "Proposed decision records".
- `docs/repository-layout.md`: add `tests/job_corpus/`, `tests/features/`,
  and `tests/__snapshots__/`.
- `README.md`: add `docs/job-corpus.md` to "Learn more" and point the
  Contributing paragraph at it; no capability claim changes.
- `typos.local.toml`: add only exact tokens the spelling gate flags, citing
  this plan; never exclude `tests/job_corpus/**`.
- `docs/roadmap.md`: change `- [ ] 1.1.1.` to `- [x] 1.1.1.` only after
  every gate passes.

## Concrete steps

Run all commands from the repository root, sequentially, never in parallel,
logging with `tee`:

```bash
BRANCH=$(git branch --show-current)
make check-fmt 2>&1 | tee /tmp/check-fmt-pokie-$BRANCH.out
make fmt 2>&1 | tee /tmp/fmt-pokie-$BRANCH.out
make typecheck 2>&1 | tee /tmp/typecheck-pokie-$BRANCH.out
make lint 2>&1 | tee /tmp/lint-pokie-$BRANCH.out
make test 2>&1 | tee /tmp/test-pokie-$BRANCH.out
make markdownlint 2>&1 | tee /tmp/markdownlint-pokie-$BRANCH.out
make spelling 2>&1 | tee /tmp/spelling-pokie-$BRANCH.out
make nixie 2>&1 | tee /tmp/nixie-pokie-$BRANCH.out
make audit 2>&1 | tee /tmp/audit-pokie-$BRANCH.out
make validate 2>&1 | tee /tmp/validate-pokie-$BRANCH.out
uv run --with 'slipcover' python -m slipcover --branch -m pytest -n auto \
  2>&1 | tee /tmp/coverage-pokie-$BRANCH.out
```

`make fmt` is listed because the ExecPlan itself is a Markdown target: editing
it can leave a table that `mdtablefix` re-pads, which `make check-fmt` reports
and only `make fmt` fixes. `make spelling` and `make validate` are separate
targets (`make markdownlint` does not include them), and `make audit` is the
`pip-audit` gate named in `AGENTS.md`. The coverage command must be run through
`uv run --with 'slipcover'`: `uv tool run` installs an isolated environment in
which `pytest` is not importable, so that form fails before collecting tests
rather than reporting coverage.

EP-M0 dependency step:

```bash
uv add --dev "pytest-bdd>=9.0.0" "syrupy>=6.1.1" "hypothesis>=6.169.4"
```

Focused runs during EP-M1 to EP-M3:

```bash
uv run pytest tests/test_job_corpus_policy.py -v
uv run pytest tests/test_job_corpus_alternatives.py -v -k validate-user-records
```

Expected red transcript for a stub reference (abridged):

```plaintext
AssertionError: validate-user-records/design-example: expected b'1 2\n', observed b''
```

Expected green transcript at the end of EP-M3 (abridged):

```plaintext
test_reference_reproduces_expected[validate-user-records/design-example] PASSED
test_alternative_agrees_or_declares_divergence[validate-user-records/python-int-spellings/awk] PASSED
```

Commit after each milestone, and after each job category in EP-M3, with an
imperative subject under 50 characters.

## Validation and acceptance

Acceptance is behavioural:

1. `make test` passes with eighteen passing reference parameters; awk and
   shell parameters pass, or skip with "awk not on PATH" only outside CI.
2. Changing `validate-user-records/design-example` to expect `1 3` fails
   with a message containing `expected b'1 3\n'` and `observed b'1 2\n'`;
   reverting restores green.
3. Removing the Q5 row from the register fails
   `test_repository_register_is_complete_and_consistent` with a report line
   naming `Q5`; reverting restores green.
4. Adding an observation of kind `contradiction` to any job makes the audit
   verdict `revise-contracts` and fails the repository audit test; reverting
   restores green.
5. `docs/job-corpus.md` and `docs/decision-register.md` pass
   `make markdownlint` and `make nixie`.

Red-Green-Refactor evidence for each milestone (red command and failure, green
command and pass, refactor rerun) is recorded in `Artefacts and notes`.

Quality criteria:

- Tests: `make test` passes; the CI coverage command passes.
- Verification: INV-ORACLE-1, INV-ORACLE-2, INV-COV-1, INV-REG-1,
  INV-REG-2, INV-FAIL-1, INV-VERDICT-1, LEM-LOAD-1, INV-ORDER-1, and
  INV-REPORT-1 discharged as described.
- Lint and type checking: `make check-fmt`, `make typecheck`, and
  `make lint` pass after each milestone.
- Documentation: `make markdownlint` (including spelling) and `make nixie`
  pass.

## Idempotence and recovery

Every step is repeatable. `uv add` is idempotent. Tests write inputs only to
temporary directories. Update snapshots without xdist, because concurrent
workers can corrupt the shared snapshot file:
`uv run pytest -n 0 tests/test_job_corpus_report.py --snapshot-update`. Review
every snapshot change in the diff, and delete obsolete snapshots, which syrupy
otherwise reports as unused. If a milestone fails midway, revert to the last
milestone commit with `git revert`.

## Artefacts and notes

Planning prototypes (2026-10-15; CPython 3.14, GNU Awk 5.3.0, and mawk 1.3.4
20240123 in `ubuntu:24.04`; mawk and GNU Awk agreed on every case):

```plaintext
filter-server-errors      /upload /health /report
filter-missing-email      2 4 5
filter-first-timeouts     timeout 1 / timeout 2 / read 4
filter-skip-comments      error: ERROR disk full now / long: 2 / long: 4
validate-user-records     reference 1 2 (int spellings: 3 0); awk 1 2 (int spellings: 1 2)
validate-request-ids      00ff 12 / 1a2b 007 / malformed 2
validate-optional-unit    10 bytes / 2048 bytes / unknown unit parsec / 4 bytes
validate-last-good-uid    awk 42 1; native Python match leaks uid = -1
aggregate-status-counts   200 3 / 404 1 / 503 1 (awk and shell pipeline)
aggregate-endpoint-latency /a 20.00 / /b 4.00 / rejected 2 of 7; float spellings: reference 1 of 2, awk 2 of 2
filter-error-lines invalid ok ERROR one, then UnicodeDecodeError, status 1
```

## Interfaces and dependencies

Development dependencies (group `dev`): `pytest-bdd>=9.0.0`, `syrupy>=6.1.1`,
and `hypothesis>=6.169.4`. Standard library: `tomllib`, `subprocess`,
`tempfile`, `dataclasses`, `enum`, `typing`, `ast` (boundary test only).

Layout (all under `tests/`, imported as `job_corpus` via
`pythonpath = ["tests"]`):

```plaintext
tests/job_corpus/__init__.py          package docstring: scope and reuse policy
tests/job_corpus/model.py             corpus domain types
tests/job_corpus/findings.py          Finding, FindingKind, Agreement, Verdict, CaseResult, AuditReport
tests/job_corpus/policy.py            pure validation policy
tests/job_corpus/comparison.py        compare_outcome, evaluate_agreement
tests/job_corpus/audit.py             audit_corpus, verify_case
tests/job_corpus/report.py            render_report
tests/job_corpus/ports.py             ProgramRunner
tests/job_corpus/vulture_whitelist.py names Vulture cannot see through TOML text
tests/job_corpus/adapters/toml_jobs.py       load_jobs, EvidenceFormatError
tests/job_corpus/adapters/markdown_docs.py   load_register, load_roadmap_task_ids
tests/job_corpus/adapters/process_runner.py  ProcessRunner
tests/job_corpus/jobs/<job-id>/       job.toml, program.pokie, reference.py, alternative.awk, alternative.sh
tests/conftest.py                     Hypothesis profiles; corpus_root, repository_jobs, process_runner, awk_executable
tests/features/job_corpus.feature
```

Domain types (frozen, slotted dataclasses and `enum.StrEnum` members, as
`.rules/python-00.md` prefers):

```python
type Alternative = ScriptImplementation | DescribedAlternative


class Failure(enum.StrEnum):
    NONE = "none"
    STATIC = "static"
    INITIALIZATION = "initialization"
    INPUT = "input"
    GUARD = "guard"
    ADAPTER = "adapter"
    ACTION = "action"
    END = "end"
    BROKEN_PIPE = "broken-pipe"


@dataclasses.dataclass(frozen=True, slots=True)
class InputFile:
    name: str
    content: bytes


@dataclasses.dataclass(frozen=True, slots=True)
class ExpectedOutcome:
    stdout: bytes
    exit_status: int
    failure: Failure


@dataclasses.dataclass(frozen=True, slots=True)
class ScriptImplementation:
    kind: ScriptKind  # reference, awk, shell; pokie is added by task 2.1.3
    path: PurePosixPath  # relative to the corpus root
    args: tuple[str, ...]
    comparison: Comparison
    divergences: tuple[Divergence, ...]


class ProgramRunner(typ.Protocol):
    def run(self, implementation: ScriptImplementation, case: JobCase) -> ObservedOutcome: ...


def verify_case(
    job: CorpusJob, implementation: ScriptImplementation, case: JobCase, runner: ProgramRunner
) -> CaseResult: ...


def audit_corpus(
    jobs: cabc.Sequence[CorpusJob],
    register: cabc.Sequence[RegisterEntry],
    task_ids: cabc.Sequence[str],
    findings_text: str,
) -> AuditReport: ...
```

The remaining types follow the same pattern: `JobCategory`, `QuestionId`,
`CaseTag`, `ScriptKind`, `DescribedKind` (`status-quo`, `prior-art`),
`Comparison` (`exact`, `sorted-lines`), `ObservationKind`, `EvidenceStatus`;
`ObservedOutcome(stdout, stderr, exit_status, timed_out)`,
`JobCase(case_id, tags, operands, inputs, expected, earliest_task)`,
`Divergence(case_id, reason)`, `DescribedAlternative(kind, tool, description)`,
`ProposedProgram(path, args)`,
`Observation(observation_id, kind, contracts, questions, summary)`,
`CorpusJob(job_id, title, category,
goals, decisions, contracts, evidence_status, provenance, program,
alternatives, cases, observations)`,
and
`RegisterEntry(question, owner,
evidence_tasks, decide_before, gates, corpus_evidence)`.
`task_ids` is an ordered sequence so deadline ordering can be checked. Fields
whose only consumer is a later milestone, and the `StrEnum` members that TOML
text resolves at runtime, are declared in
`tests/job_corpus/vulture_whitelist.py` and checked against Vulture by
`tests/test_job_corpus_dead_code.py`; see `Surprises & discoveries`.

`job.toml` schema (version 1):

```toml
schema = 1
id = "validate-user-records"
title = "Count accepted and rejected user records"
category = "capture-validation"
goals = ["G2", "G3"]
decisions = ["Q1", "Q5", "Q6"]
contracts = ["DC-1", "DC-3", "DES-5"]
evidence_status = "Assumption"
provenance = ["docs/design-contracts.md §1"]
program = { path = "program.pokie", args = [] }

[[alternatives]]
kind = "reference"
path = "reference.py"

[[alternatives]]
kind = "awk"
path = "alternative.awk"
comparison = "exact"
divergences = [
  { case = "python-int-spellings", reason = "The awk validator accepts only ASCII signed decimals." },
]

[[alternatives]]
kind = "prior-art"
tool = "PAWK"
description = "pawk -B with a regex filter and the capture tuple m; conversion errors need try/except."

[[alternatives]]
kind = "status-quo"
description = "A Python loop combining re.search, try/except ValueError, and a Counter."

[[cases]]
id = "design-example"
tags = ["malformed-record", "guard-rejection", "adapter-rejection"]
operands = ["users.log"]
inputs = [{ name = "users.log", text = "user=ada uid=42\nuser=lin uid=no\nuser=sam uid=-1\n" }]
expected = { stdout = "1 2\n", exit_status = 0, failure = "none" }
earliest_task = "4.1.2"

[[observations]]
id = "OBS-05"
kind = "ergonomic-smell"
contracts = ["DC-3"]
questions = ["Q6"]
summary = "int accepts non-ASCII digits, digit separators, and signs."
```

Signposted skills for the implementer: `execplans` (keep this plan current),
`hexagonal-architecture` (keep the single port and pure core), `python-router`,
then `python-data-shapes` (frozen dataclasses and tagged unions),
`python-types-and-apis` (protocols), `python-testing` (fixtures,
parametrization, syrupy), `hypothesis` (properties), `python-errors-and-logging`
(`EvidenceFormatError`), `leta` (navigation), `en-gb-oxendict-style`
(documentation), and `commit-message`.

Signposted documents: `docs/terms-of-reference.md` §§3–9,
`docs/pokie-design.md` §§1–6, 9–11, `docs/design-contracts.md` §§1, 3–4,
`docs/context.md`, ADRs 0001–0003, `docs/developers-guide.md`,
`docs/documentation-style-guide.md` (ADR naming convention and template),
`docs/scripting-standards.md` (subprocess hygiene), and
`docs/complexity-antipatterns-and-refactoring-strategies.md` (guard clauses,
dispatch tables, extract method, and the warning against speculative layering;
the repository's cyclomatic-complexity limit is 8).

## Revision note

- 2026-10-15: initial draft.
- 2026-10-15: revised after a five-reviewer expert panel. Changes: separated
  the reference oracle from user-facing alternatives and dropped line counts;
  reduced the architecture to a pure core plus one `ProgramRunner` port;
  aligned failure categories with design-contracts §4 Table 2; added typed
  observations, an audit verdict, and the "Phase 1 findings" section as the
  go/no-go output to 1.1.2; added `validate-last-good-uid` (binding isolation)
  and `filter-skip-comments` (`next`, several rules, standard input), an
  `invalid-utf8` aggregation case, digit-separator and empty-unit cases, CLF
  inputs, and public provenance; fixed lexing, divergence reasons, and vacuous
  tags; moved inputs inline to avoid `*.log` ignores; added shell and prior-art
  alternatives; corrected register gates and added deadlines, gaps, and interim
  defaults; added environment allowlists, mawk verification, CI-aware awk
  skipping, Hypothesis profiles, coverage-ratchet checks, Vulture
  configuration, and a model-checked order property. Effect: eleven jobs and
  eighteen cases; the milestones keep their order, and EP-M0 now proves the
  toolchain on realistic code.
- 2026-10-15: re-verified the load-bearing external sources with Firecrawl
  once credits were restored (POSIX awk, runner image contents, pytest-bdd
  9.0.0, syrupy 6.1.1). No conclusion changed; evidence citations in `Risks`,
  `Surprises & discoveries`, and AXIOM-3 were strengthened.
- 2026-10-15: adopted the repository's new decision-record naming
  convention (`docs/adrs/adr-nnnn-title-slug.md`,
  `docs/rfcs/rfc-nnnn-title-slug.md`) and the refreshed documentation style
  guide. ADR citations and trace identifiers now use four digits (ADR-0002,
  ADR-0003), and the planned record is
  `docs/adrs/adr-0004-define-the-job-corpus-schema-and-reference-oracle.md`.
  The users' guide change now avoids fenced programs, following the refreshed
  guide's tested-example rule. No milestone, obligation, or acceptance
  criterion changed.
