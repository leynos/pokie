# Establish the representative job corpus and decision register

This ExecPlan (execution plan) is a living document. The sections
`Constraints`, `Tolerances`, `Risks`, `Progress`, `Surprises & discoveries`,
`Decision log`, `Outcomes & retrospective`, `Conformance basis`, and
`Verification plan` must be kept up to date as work proceeds.

Status: DRAFT

Roadmap item: `docs/roadmap.md` task 1.1.1, "Establish the representative job
corpus and decision register".

## Purpose / big picture

Pokie is a proposed language for Python-fluent command-line users: awk-like
ordered record processing with Python statements, regex capture dispatch, and
explicit validating or converting patterns. No interpreter exists. Phase 1 of
the roadmap asks whether the proposed contracts survive contact with real
text-processing jobs before anyone builds a parser. Task 1.1.1 supplies the
evidence that the rest of phase 1 (and later, phases 2–5) is judged against.

After this change, a reader can open one document, `docs/job-corpus.md`, and
see nine representative jobs grouped as filtering, capture validation, and
aggregation. For each job they see the proposed pokie program, the exact input
records, the exact expected standard output and exit status, and the
alternatives a user has today: an ordinary Python script, an awk program, and
keeping the status quo. A second document, `docs/decision-register.md`, assigns
an accountable decision owner, an evidence task, and gated roadmap tasks to
each of the open questions Q1–Q8 in `docs/terms-of-reference.md` §9, and links
each question to the corpus jobs that bear on it.

The corpus is executable evidence, not prose. Running `make test` loads every
job from `tests/job_corpus/jobs/`, runs each job's Python alternative and awk
alternative as real subprocesses against the job's inputs, and checks that:
the Python alternative reproduces every expected outcome exactly; the awk
alternative either agrees or diverges only on cases where the job declares a
divergence with a reason; the corpus covers all three job categories and the
required edge cases; and the decision register assigns exactly one owner to
each of Q1–Q8 and is consistent with the jobs. The proposed pokie programs are
recorded but deliberately not executed, because no pokie implementation
exists; task 1.1.2 ratifies them against the design, and tasks 2.1.3 onwards
execute them.

Success is observable as follows. `make test` passes, and its output includes
one passing test per job case for the Python alternatives (for example,
`test_python_alternative_reproduces_expected[validate-user-records/design-example]`).
Deliberately editing `tests/job_corpus/jobs/validate-user-records/job.toml` so
that the expected output reads `1 3` makes that test fail with a message naming
expected `1 3` and observed `1 2`. Deleting the Q5 row from
`docs/decision-register.md` makes the register test fail naming `Q5`.

## Constraints

- No product behaviour is introduced. `pokie/` (the shipped package) must not
  be modified, and no document may describe pokie as able to run a corpus
  program. Proposed pokie programs are stored as data and labelled "proposed,
  not executable".
- The corpus must not silently change a design contract. If a job cannot be
  specified without contradicting `docs/design-contracts.md`,
  `docs/pokie-design.md`, or ADRs 001–003, record the contradiction as a
  counterexample in the job's `notes` and in `Decision log`, and escalate. This
  is the falsification signal the roadmap's phase 1 idea asks for; it must not
  be smoothed over.
- Decision owners must be real accountable roles that exist today. The only
  established role is the project owner (`@leynos`, terms-of-reference §4
  Table 2). Do not invent sponsors, teams, or people.
- No runtime dependencies are added. `pyproject.toml` `dependencies` stays
  empty. Only the development dependencies named in `Interfaces and
  dependencies` may be added.
- The corpus harness is test-support code that lives under `tests/` and is not
  packaged in the wheel (`[tool.hatch.build.targets.wheel] packages =
  ["pokie"]` already guarantees this).
- Every code file stays under 400 lines; functions respect the repository's
  Ruff limits (`max-complexity = 8`, `max-args = 4`, `max-locals = 10`,
  `max-bool-expr = 2`).
- Subprocesses are launched with argument lists, never `shell=True`; Python
  alternatives run with `sys.executable -I`; no alternative performs network
  access or writes outside its temporary directory.
- All prose and identifiers use en-GB-oxendict spelling (`-ize`, `-yse`,
  `-our`), except external API names.
- Hexagonal boundaries hold: domain modules (`model.py`, `policy.py`,
  `comparison.py`) import nothing from `adapters/`, perform no I/O, and do not
  import `tomllib`, `subprocess`, or `pathlib`.

## Tolerances (exception triggers)

- Scope: if the change needs more than 60 files (excluding corpus data under
  `tests/job_corpus/jobs/`) or more than 1,600 net lines of Python, stop and
  escalate.
- Interface: if anything under `pokie/` must change, stop and escalate.
- Dependencies: if any dependency other than `pytest-bdd`, `syrupy`, and
  `hypothesis` (development group only) is needed, stop and escalate.
- Contracts: if any job's expected outcome contradicts a proposed contract,
  stop, record the counterexample, set this plan to `BLOCKED`, and escalate.
- Ownership: if the project owner rejects the proposed owner assignment for any
  question during review, stop and update the register only as directed.
- Tooling: if the duplication, dead-code, or Pylint gates reject the per-job
  alternative scripts and the fix would require excluding `tests/` from a
  gate, stop and escalate rather than weakening the gate.
- Runtime: if the new tests add more than 60 seconds to `make test` on this
  machine, stop and reduce subprocess fan-out before continuing.
- Portability: if continuous integration's `awk` disagrees with local GNU Awk
  on any case that is not a declared divergence, stop and escalate; do not add
  implementation-specific special cases.
- Iterations: if a gate still fails after three fix attempts, stop and
  escalate.

## Risks

- Risk: the corpus is synthetic. Every job is invented by the implementer, so
  "representative" is an assumption, not user evidence (terms-of-reference §8.2
  Table 4). Severity: high. Likelihood: high. Mitigation: label every job's
  `evidence_status` as `assumption` (vocabulary from `docs/context.md` §1);
  state in `docs/job-corpus.md` and the register that Q1 remains open until
  observed comparison (roadmap 5.2.2); make adding a user-sourced job a
  documented, test-guarded procedure.
- Risk: awk implementations differ. Local `awk` is GNU Awk 5.3.0; GitHub's
  `ubuntu-latest` image may resolve `awk` to mawk. Severity: medium.
  Likelihood: medium. Mitigation: restrict awk alternatives to POSIX features
  (no `asort`, `PROCINFO`, three-argument `match`, or `gensub`); run awk with
  `LC_ALL=C`; use `sorted-lines` comparison wherever POSIX leaves `for (key in
  array)` order unspecified; include the awk version string in failure
  messages; inspect the CI log of the draft pull request.
- Risk: new development tools disagree with the strict lint stack (Ruff
  preview rules, Interrogate 100%, Pylint, Skylos, Vulture, nose duplication,
  `ty`). pytest-bdd step functions and the many small `alternative.py` scripts
  are the likely friction. Severity: medium. Likelihood: medium. Mitigation:
  milestone EP-M0 proves the toolchain on one trivial scenario before any
  corpus code exists; alternatives are written as idiomatic, documented
  scripts with distinct logic; any narrow per-file ignore cites this plan.
- Risk: pytest-bdd 9.0.0 or syrupy 6.1.1 may not yet support pytest 9.1.1.
  Severity: medium. Likelihood: low. Mitigation: EP-M0 runs one scenario and
  one snapshot before further work; if incompatible, pin the newest compatible
  release and record it in `Decision log`.
- Risk: the Markdown register drifts from the corpus. Severity: medium.
  Likelihood: medium. Mitigation: invariant INV-REG-2 makes the register's
  evidence column and the jobs' `decisions` lists mutually derivable, and
  `make test` fails on any mismatch.
- Risk: the design's phrase "normalizing standard text line endings"
  (`docs/pokie-design.md` §4.1) is ambiguous about lone carriage returns and
  Unicode line separators. Severity: low. Likelihood: high. Mitigation: do not
  choose; record it in `filter-error-lines` `notes` as a question for task
  1.1.2, and keep every corpus input free of carriage returns until 1.1.2
  decides.
- Risk: mutation testing copies the tree but not `docs/`. Severity: low.
  Likelihood: high. Mitigation: add `docs/` to `[tool.mutmut] also_copy`
  because the register tests read `docs/decision-register.md` and
  `docs/roadmap.md`.

## Progress

- [x] (2026-10-15) Branch renamed to
  `1-1-1-establish-the-representative-job-corpus-and-decision-register`
  tracking the same name on `origin`.
- [x] (2026-10-15) Reconnaissance of the terms of reference, design,
  contracts, context, ADRs, roadmap, tooling, and test conventions.
- [x] (2026-10-15) Prior-art and format research: PAWK, pyawk, the POSIX awk
  specification, and Markdown Architectural Decision Records (MADR) 4.0.0.
- [x] (2026-10-15) Scratch prototype of six alternatives confirming the
  expected outcomes recorded in `Corpus specification`.
- [x] (2026-10-15) Draft ExecPlan written.
- [ ] Expert-panel review and revision of this plan.
- [ ] Plan approved by the project owner.
- [ ] EP-M0: development dependencies and toolchain proof.
- [ ] EP-M1: domain model, policy, and comparison with unit and property tests.
- [ ] EP-M2: ports, adapters, application service, and report snapshots.
- [ ] EP-M3: corpus content and executable alternatives.
- [ ] EP-M4: decision register document and register tests.
- [ ] EP-M5: documentation, ADR 004, and roadmap completion.

## Surprises & discoveries

- Observation: Firecrawl research failed with "Insufficient credits".
  Evidence: two `firecrawl_scrape` calls on 2026-10-15. Impact: prior-art
  pages were retrieved with WebFetch instead; the cited sources are unchanged.
- Observation: Python's `int(s, 10)` accepts Arabic-Indic digits, so the
  design's `int` adapter accepts `uid=٤٢` while any awk alternative rejects
  it. Evidence: scratch prototype printed `1 0` (Python) and `0 1` (awk) for
  `user=ravi uid=٤٢`. Impact: this is the corpus's first declared divergence
  and direct evidence for Q6 (catalogue breadth).
- Observation: a Python script iterating a text-mode file decodes in chunks,
  so an invalid byte on line 2 raises before line 1 is printed. Evidence:
  CPython `io.TextIOWrapper` behaviour; the scratch prototype that decodes
  each binary line separately printed line 1 and then failed with status 1.
  Impact: Python alternatives must read bytes and decode per record to model
  the design's "output already emitted is preserved" contract
  (`docs/pokie-design.md` §9).
- Observation: `ty` 0.0.56 resolves `from job_corpus import ...` in
  `tests/test_*.py` when `tests/job_corpus/` is a package. Evidence: scratch
  experiment in `/tmp/tyexp.*` printed "All checks passed!". Impact: the
  harness can live under `tests/` without path configuration.

## Decision log

- Decision: represent each job as a directory under `tests/job_corpus/jobs/`
  containing `job.toml`, `program.pokie`, `alternative.py`, and usually
  `alternative.awk`. Rationale: TOML is parsed by the standard library's
  `tomllib` (no new dependency); separate program files keep pokie, Python,
  and awk text readable and let Ruff, `ty`, and Interrogate check the Python
  alternatives as real code. `docs/repository-layout.md` already reserves
  `tests/` for language fixtures. Date/Author: 2026-10-15, planning agent.
- Decision: the Python alternative is the executable oracle for expected
  outcomes; awk is a second, independent implementation whose disagreements
  must be declared. Rationale: no pokie implementation exists, so expected
  outcomes need an independent check that can fail. Two implementations in
  different languages make a wrong expectation hard to hide. Date/Author:
  2026-10-15, planning agent.
- Decision: the decision register is a Markdown table in
  `docs/decision-register.md`, parsed by a test adapter, rather than a TOML
  file. Rationale: the register is a governance document the project owner
  edits; keeping one authoritative copy in `docs/` avoids a second source of
  truth. The parser only reads a fenced region between HTML comment markers,
  which keeps the format narrow. Date/Author: 2026-10-15, planning agent.
- Decision: owners use a MADR-style split of accountable decision owner
  (`decision-makers`) and evidence task (the roadmap task responsible for
  producing evidence). Every question's decision owner is the project owner,
  `@leynos`, until Q8 names a sponsor or release approver. Rationale: the
  project owner is the only established role; roadmap tasks already describe
  who produces evidence. Requires confirmation at plan approval. Date/Author:
  2026-10-15, planning agent.
- Decision: the harness is a hexagonal mini-application under
  `tests/job_corpus/`, not product code under `pokie/`. Rationale: the corpus
  is project evidence consumed by tests, later CLI suites (2.2.3), and
  benchmarks (5.2.1); shipping it in the wheel would advertise unimplemented
  behaviour. Date/Author: 2026-10-15, planning agent.
- Decision: record the corpus and register formats in a new ADR 004 with
  status `Proposed`, referenced from `docs/pokie-design.md` §10. Rationale:
  later roadmap tasks (1.1.2, 2.1.3, 5.2.1, 5.2.2) depend on the format, so it
  is a substantive, hard-to-reverse choice. Date/Author: 2026-10-15, planning
  agent.

## Outcomes & retrospective

Not started. Complete at each milestone and at completion, reconciling any
discovery with the documents in `Conformance basis`.

## Context and orientation

The repository is a Python 3.14 project managed by `uv`. The package `pokie/`
contains only a scaffold `hello()` function. The language exists only as
documents:

- `docs/terms-of-reference.md` defines goals G1–G5 (§6.1), success criteria
  (§7 Table 3), assumptions (§8.2), and open questions Q1–Q8 (§9 Table 5). §9
  states "Owners are unassigned unless stated. Roadmap task 1.1.1 assigns
  decision owners".
- `docs/pokie-design.md` is the proposed technical design. §1 sets scope, §2
  records prior art (PAWK, pyawk) and the compiler choice, §3–§5 define
  syntax, records, lifecycle, captures, and cases, §9 the failure model, and
  §10 the verification strategy.
- `docs/design-contracts.md` is canonical where it disagrees with the design.
  §1 contains the only worked example (the user-record program printing
  `1 2`), §3 the adapter catalogue (`digits`, `hexstr`, `int`, `float`), and
  §4 the command-line interface (CLI) contract and exit statuses.
- `docs/context.md` defines vocabulary (record, field, capture, rule, case,
  guard, adapter, binding) and the evidence statuses `Established`, `Agreed
  basis`, `Assumption`, `Proposed contract`, `Open question`, and `Deferred`.
- ADRs 001–003 (`docs/adr-00N-*.md`) are all `Proposed`.
- `docs/roadmap.md` lists tasks as `- [ ] N.N.N.` checkboxes.

Terms used in this plan:

- A *job* is one text-processing task a user wants done, such as "count
  accepted and rejected user records".
- A *case* is one concrete run of a job: named input files and the expected
  outcome.
- An *expected outcome* is the exact standard output bytes, the process exit
  status, and a diagnostic category (`none` or the failure kind).
- An *alternative* is another way to do the job today: an ordinary Python
  script, an awk program, or keeping the existing approach (the *status quo*,
  which terms-of-reference §5 calls a valid alternative).
- A *declared divergence* is a case where a job states that its awk
  alternative legitimately produces a different outcome, with a reason.
- The *decision register* is the table assigning owners to Q1–Q8.
- *Ports and adapters* (hexagonal architecture): the domain defines
  interfaces (ports) for what it needs, and separate adapter modules implement
  them with real I/O. Here, the domain is corpus validation policy; the
  adapters read TOML, parse Markdown, and run subprocesses.

Test conventions observed in `tests/`: flat `test_*.py` modules with a module
docstring, a docstring and `-> None` on every test, assertion messages held in
a `why` variable, no shared `conftest.py` yet. Ruff requires `import typing as
typ`, `import collections.abc as cabc`, `import dataclasses`, and `import
enum` styles rather than `from` imports for those modules. Tests run under
`pytest -n auto` (xdist) with a 30-second per-test timeout.

## Conformance basis

Upstream revisions are those at commit `ccbf884` ("Apply Episodic lint
standards (#12)"):

- Terms of reference: `docs/terms-of-reference.md`, draft v0.1, revised
  2026-10-09. Traced items: TOR-JTBD (§5), TOR-G1–TOR-G5 (§6.1), TOR-SC-G1 and
  TOR-SC-G2G3 (§7 Table 3 rows "User-facing, G1" and "User-facing, G2/G3"),
  TOR-A1–TOR-A5 (§8.2 Table 4 rows in order), TOR-Q1–TOR-Q8 (§9 Table 5).
- Technical design: `docs/pokie-design.md`, proposed v0.1, updated
  2026-10-10. Traced items: DES-4.1 (input and fields), DES-4.2 (lifecycle),
  DES-4.3 (control transfer), DES-5 (captures and cases), DES-9 (failure
  model), DES-10 (verification evidence).
- Contracts: `docs/design-contracts.md` DC-1 (user-record example), DC-3
  (adapter catalogue), DC-4 (CLI outcomes, Table 2).
- ADRs: ADR-002 (execution scope and lifecycle, Proposed), ADR-003 (pattern
  adapter resolution, Proposed). ADR-001 is context only.
- Roadmap: RM-1.1.1 success criterion "filtering, capture validation, and
  aggregation jobs have inputs, expected outcomes, alternatives, and assigned
  decision owners for Q1–Q8".
- Standards: `AGENTS.md`, `.rules/python-*.md`,
  `docs/documentation-style-guide.md`, `docs/scripting-standards.md` (for
  subprocess hygiene; the harness is not a standalone script, so its PEP 723
  and Cyclopts rules do not apply).

Trace chains:

```plaintext
RM-1.1.1 (categories) -> TOR-G1, TOR-SC-G1 -> EP-M3 -> INV-COV-1 -> test_repository_corpus_covers_required_categories
RM-1.1.1 (inputs, expected outcomes) -> TOR-SC-G1, TOR-SC-G2G3 -> EP-M3 -> INV-ORACLE-1 -> test_python_alternative_reproduces_expected[*]
RM-1.1.1 (alternatives) -> TOR §3 Table 1, TOR-JTBD -> EP-M3 -> INV-ORACLE-2 -> test_awk_alternative_agrees_or_declares_divergence[*]
RM-1.1.1 (owners for Q1-Q8) -> TOR-Q1..TOR-Q8 -> EP-M4 -> INV-REG-1, INV-REG-2 -> test_repository_register_is_complete_and_consistent
DC-1 -> EP-M3 -> validate-user-records/design-example -> INV-ORACLE-1
DES-4.1 (unterminated final line, empty fields, out-of-range fields, multiple files) -> EP-M3 -> INV-COV-1 required tags
DES-4.2, DES-4.3, ADR-002 (exit runs end:) -> EP-M3 -> filter-first-timeouts/stops-after-two
DES-9, DC-4 (input failure preserves output, status 1) -> EP-M3 -> filter-error-lines/invalid-utf8
DC-3 (int and float inherit Python breadth) -> EP-M3 -> declared awk divergences -> TOR-Q6 evidence
TOR-A4 (capture cases reduce glue) -> EP-M3 status-quo and Python alternatives -> RM-5.2.2 comparison input
```

## Verification plan

The change introduces validation policy over data and an oracle relationship
between data and executable alternatives. The obligations below are the
invariants and lemmas that make "the corpus is correct" falsifiable.

Axioms (trusted, not verified here):

- AXIOM-1: CPython 3.14's `re.search`, `int(s, 10)`, `float(s)`, `str.split`,
  and `bytes.decode("utf-8")` behave as documented. The design's adapters are
  defined by these functions (DC-3), so the Python alternative inherits the
  intended semantics by construction.
- AXIOM-2: `tomllib` conforms to TOML 1.0, including exact preservation of escape
  sequences in basic strings.
- AXIOM-3: the `awk` on `PATH` implements the POSIX awk features used by the
  alternatives (`match`, `substr`, `split`, `sub`, numeric strings, `exit`
  running `END`). Local evidence: GNU Awk 5.3.0.
- AXIOM-4: `subprocess.run` reports the child's exit status and captures its
  standard output bytes faithfully.

Obligations:

- Obligation INV-ORACLE-1: for every job case, the Python alternative run on
  the case's inputs produces exactly the expected standard output bytes and
  exit status, and its standard error is empty if and only if the expected
  diagnostic is `none`.
  - Method: parameterized end-to-end tests over the real corpus.
  - Rationale: the corpus is a finite, enumerated specification; each case is
    a named example with distinct meaning.
  - Domain: every `(job, case)` pair in `tests/job_corpus/jobs/` (expected 15
    pairs after EP-M3).
  - Artefact: `tests/test_job_corpus_alternatives.py::test_python_alternative_reproduces_expected`.
  - Evidence: `make test`; red first by writing each `job.toml` before its
    `alternative.py` exists, which fails with "alternative script not found".
  - Non-vacuity: a collection-time assertion requires at least 15 parameters
    and at least one case per category, so an empty or partially loaded
    corpus fails instead of passing vacuously. Negative control: the
    behavioural scenario "A job whose expected output is wrong is rejected"
    builds a temporary corpus whose expected stdout is `1 3` and asserts a
    mismatch naming both values.
- Obligation INV-ORACLE-2: for every job case and every awk alternative, the
  awk outcome equals the expected outcome (under the alternative's declared
  comparison, `exact` or `sorted-lines`) on every case not listed in
  `diverges_on`, and differs on every case listed in `diverges_on`.
  - Method: parameterized end-to-end tests; skipped with an explicit reason
    when no `awk` is on `PATH`.
  - Rationale: the second clause catches stale divergence declarations, which
    would otherwise hide a fixed or mistaken expectation.
  - Domain: every `(job, case)` pair with an awk alternative.
  - Artefact: `tests/test_job_corpus_alternatives.py::test_awk_alternative_agrees_or_declares_divergence`.
  - Evidence: `make test`.
  - Non-vacuity: at least two declared divergences exist after EP-M3
    (`validate-user-records/unicode-digits`,
    `aggregate-endpoint-latency/float-spellings`), and a unit test of
    `comparison.evaluate_agreement` shows that a declared divergence whose
    outcome actually agrees is reported as `stale-divergence`.
- Obligation INV-COV-1: the corpus contains at least one job in each category
  (`filtering`, `capture-validation`, `aggregation`), at least two jobs per
  category, and at least one case carrying each required edge tag
  (`empty-input`, `unterminated-final-line`, `empty-field`,
  `out-of-range-field`, `malformed-record`, `multiple-files`, `early-exit`,
  `input-failure`, `optional-capture`, `unicode`).
  - Method: property test of the pure policy plus a concrete test of the real
    corpus.
  - Rationale: the policy function `policy.find_coverage_gaps` is a set
    computation over an open-ended input space; a property states it exactly.
  - Domain: Hypothesis-generated tuples of minimal valid jobs with arbitrary
    categories and tag subsets, including the empty tuple.
  - Artefacts: `tests/test_job_corpus_properties.py::test_coverage_gaps_are_exact_complement`
    and `tests/test_job_corpus_policy.py::test_repository_corpus_covers_required_categories`.
  - Evidence: the property asserts that reported missing categories equal
    `REQUIRED_CATEGORIES - present` and missing tags equal
    `REQUIRED_TAGS - present`.
  - Non-vacuity: `@example(())` (everything missing) and an example with every
    category and tag (nothing missing) are pinned, so both outcome classes run
    on every execution; `hypothesis.event` labels each generated corpus as
    complete or incomplete for inspection with `--hypothesis-show-statistics`.
    Seeded fault: changing the implementation to return `present` instead of
    the complement fails the property immediately.
- Obligation INV-REG-1: the register contains exactly one row for each of
  Q1–Q8, no other question identifiers, a non-blank owner that is not a
  placeholder (`TBD`, `unassigned`, `-`), and gate and evidence-task
  identifiers that exist as task numbers in `docs/roadmap.md`.
  - Method: property test of `policy.find_register_gaps` plus a concrete test
    of the real documents.
  - Domain: generated multisets of register rows drawn from Q1–Q9 with
    possibly blank or placeholder owners, and generated sets of known roadmap
    task identifiers.
  - Artefacts: `tests/test_job_corpus_properties.py::test_register_gaps_report_missing_duplicate_and_unknown`
    and `tests/test_job_corpus_register.py::test_repository_register_is_complete_and_consistent`.
  - Evidence: the property asserts missing = Q1–Q8 minus present, duplicates =
    identifiers occurring more than once, unknown = present minus Q1–Q8, and
    acceptance if and only if all three are empty and every owner is valid.
  - Non-vacuity: pinned examples for the exact valid register, an empty
    register, a duplicated Q5, and an unknown Q9. Negative control: the
    behavioural scenario deleting the Q5 row.
- Obligation INV-REG-2: for every question `Qn`, the set of jobs listed in
  the register's corpus evidence column equals the set of jobs whose
  `decisions` include `Qn`; every job's `decisions` refer only to Q1–Q8.
  - Method: parameterized unit tests of `policy.find_evidence_mismatches`
    plus the concrete repository test.
  - Rationale: bidirectional derivability prevents the register and the
    corpus drifting apart.
  - Non-vacuity: unit cases for a job missing from the register, a register
    entry naming a non-existent job, and an exact match.
- Obligation LEM-LOAD-1: the TOML adapter maps a job file to domain values
  without altering input bytes, and rejects malformed files with the file
  path and TOML key.
  - Method: parameterized adapter tests using `tmp_path`.
  - Domain: inline `text` inputs containing `\n` with and without a final
    terminator, `path` inputs containing invalid UTF-8, an empty `text`,
    missing required keys, wrong value types, unknown categories, and unknown
    tags.
  - Artefact: `tests/test_job_corpus_toml.py`.
  - Non-vacuity: the round-trip assertion compares bytes, so a loader that
    appended or stripped a trailing newline fails the unterminated-line
    example.
- Obligation INV-ORDER-1: for every filtering job marked
  `order_preserving = true`, the Python alternative's output records form a
  subsequence of its input records, in input order.
  - Method: Hypothesis property executing the real subprocess.
  - Rationale: G1 requires ordered records; this checks the oracle respects
    ordering on inputs beyond the handwritten cases.
  - Domain: lists of 0–20 records drawn from printable text without line
    terminators, mixing lines containing and lacking the word `ERROR`;
    `max_examples=25`, `deadline=None`.
  - Artefact: `tests/test_job_corpus_alternatives.py::test_filter_alternative_preserves_record_order`.
  - Non-vacuity: the strategy is built so roughly half of the records contain
    `ERROR`, `hypothesis.event` records whether output was empty, and a pinned
    `@example` with three matching records out of order relative to a sorted
    copy proves the check is order-sensitive. Seeded fault: a local variant of
    the alternative that sorts its output must fail the property; this is
    demonstrated once during EP-M3 and recorded in `Artefacts and notes`, not
    kept in the suite.
- Obligation INV-REPORT-1: audit reports render every finding kind with a
  stable, path-relative, ordered format.
  - Method: `syrupy` snapshots paired with semantic assertions.
  - Rationale: the report is a multivariant output (one renderer, many
    finding kinds) read by humans when a gate fails.
  - Artefact: `tests/test_job_corpus_report.py`, snapshots in
    `tests/__snapshots__/test_job_corpus_report.ambr`.
  - Non-vacuity: each snapshot test also asserts the finding count and kinds,
    and absolute temporary paths are replaced with corpus-relative paths
    before snapshotting.

No obligation requires symbolic execution or a proof: the domain logic is set
arithmetic and record comparison, which properties and enumerated examples
cover completely at proportionate cost. The residual gap is that the corpus
is synthetic; no test can show that it represents real users. That gap is
owned by Q1 in the register.

## Corpus specification

This is the content EP-M3 creates. Every job uses `evidence_status =
"assumption"`. Expected outputs below are exact byte strings written with
Python escape notation. Outcomes marked "verified"
were reproduced by the scratch prototype on 2026-10-15 with CPython 3.14 and
GNU Awk 5.3.0.

### Filtering jobs

`filter-error-lines` (goals G1, G5; decisions Q1, Q5; `order_preserving =
true`). Program:

```plaintext
when /\bERROR\b/:
    print($0)
```

Case `mixed-levels`, tags `unterminated-final-line`, input `app.log` (no final
newline after the last record):

```plaintext
2026-10-01T10:00:00 INFO started
2026-10-01T10:00:01 ERROR disk full
2026-10-01T10:00:02 WARN retrying
2026-10-01T10:00:03 ERROR disk still full
```

Expected stdout is the two `ERROR` records, each followed by a newline; exit
status 0; diagnostic `none`. Case `empty-input`, tags `empty-input`: one empty
file; expected stdout empty, status 0. Case `invalid-utf8`, tags
`input-failure`, input file `inputs/invalid-utf8.log` containing the bytes
`ok ERROR one\n`, `\xff\xfe ERROR\n`, `later ERROR\n`: expected stdout
`ok ERROR one\n`, status 1, diagnostic `input` (verified). The awk alternative
declares a divergence on `invalid-utf8` because awk does not validate
encodings. Notes record the open question about lone carriage returns for
task 1.1.2.

`filter-server-errors` (G1; Q1, Q3). Program:

```plaintext
when NF >= 3 and $3.isascii() and $3.isdigit() and int($3) >= 500:
    print($2)
```

Case `access-log`, tags `irregular-whitespace`, `malformed-record`,
`unterminated-final-line`:

```plaintext
GET /index 200 512
POST /upload 503 0
GET /health 500 12
  GET   /spaced   502   7
GET /short
GET /odd abc 1
```

Expected stdout `/upload\n/health\n/spaced\n`, status 0 (verified with awk).
The `isascii()` test keeps the job's meaning identical in Python and awk;
whether users expect it is recorded in `notes` as Q3 evidence.

`filter-missing-email` (G1; Q3). Program:

```plaintext
start:
    FS = ","

when $2 == "":
    print($1)
```

Case `team-roster`, tags `empty-field`, `out-of-range-field`:

```plaintext
1,ada@example.com,core
2,,core
3,lin@example.com,
4,,
5
```

Expected stdout `2\n4\n5\n` (record `5` has no second field, which reads as
`""` under DES-4.1), status 0 (verified with `awk -F,`).

`filter-first-timeouts` (G1; Q5). Program:

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

Case `stops-after-two`, tags `early-exit`: records `a`, `timeout 1`, `b`,
`timeout 2`, `timeout 3`. Expected stdout `timeout 1\ntimeout 2\nread 4\n`,
status 0 (verified with awk). This is direct evidence for ADR-002's rule that
`exit` still runs `end:` and that `NR` counts delivered records only.

### Capture-validation jobs

`validate-user-records` (G2, G3; Q5, Q6). Program copied verbatim from
`docs/design-contracts.md` §1. Case `design-example`, tags
`malformed-record`: records `user=ada uid=42`, `user=lin uid=no`,
`user=sam uid=-1`; expected stdout `1 2\n`, status 0 (verified with Python
and awk). Case `unicode-digits`, tags `unicode`: record `user=ravi uid=٤٢`;
expected stdout `1 0\n` (verified with Python). The awk alternative prints
`0 1` and declares a divergence: POSIX awk has no Unicode decimal conversion,
whereas the proposed `int` adapter follows `int(s, 10)` (DC-3). Notes record
that this behaviour bears on Q6 (should `int` accept non-ASCII digits?).

`validate-request-ids` (G2, G3; Q4, Q6). Program:

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

Case `mixed-ids`, tags `malformed-record`, `preserved-text`:

```plaintext
req=00ff ms=12
req=zz01 ms=5
req=ABC ms=0x1
req=1a2b ms=007
no request here
```

Expected stdout `00ff 12\n1a2b 007\nmalformed 2\n`, status 0 (verified with
awk). Leading zeros survive because `hexstr` and `digits` preserve their
subject. The last record does not match the regex, so the rule does nothing
and it is not counted. Notes record that a stricter identifier rule (for
example, even-length identifiers) would need a custom adapter, which is Q4
evidence.

`validate-optional-unit` (G2, G3; Q5, Q6). Program:

```plaintext
when /size=(?P<n>\d+)(?: unit=(?P<unit>\w+))?/:
    case {"n": int(n), "unit": None}:
        print(n, "bytes")
    case {"n": int(n), "unit": "KiB"}:
        print(n * 1024, "bytes")
    case {"n": n, "unit": unit}:
        print("unknown unit", unit)
```

Case `units`, tags `optional-capture`: records `size=10`, `size=2 unit=KiB`,
`size=3 unit=parsec`. Expected stdout
`10 bytes\n2048 bytes\nunknown unit parsec\n`, status 0. Case `empty-input`,
tags `empty-input`: expected empty stdout, status 0.

### Aggregation jobs

`aggregate-status-counts` (G1, G4; Q1, Q7). Program:

```plaintext
from collections import Counter

start:
    counts = Counter()

when NF >= 3:
    counts[$3] += 1

end:
    for status, total in sorted(counts.items()):
        print(status, total)
```

Case `access-log`: statuses `200`, `503`, `200`, `404`, `200` on five
well-formed records. Expected stdout `200 3\n404 1\n503 1\n`. Case
`empty-input`, tags `empty-input`: expected empty stdout, status 0. The awk
alternative uses `comparison = "sorted-lines"` because POSIX leaves `for (key
in array)` order unspecified; tag `unordered-aggregate`.

`aggregate-endpoint-latency` (G1, G3, G4; Q3, Q6, Q7). Program:

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

Case `two-files`, tags `multiple-files`, `unterminated-final-line`: input
`a.log` contains `/a 10`, `/b 3.5`, `/a 20` (terminated); `b.log` contains
`/b nan`, `/a 30`, `/b 4.5`, `/c -1` (last line unterminated). Expected stdout
`/a 20.00\n/b 4.00\nrejected 2 of 7\n`, status 0 (verified with Python and
awk). Case `float-spellings`: `c.log` contains `/d 1e3` and `/d inf`. Expected
stdout `/d 1000.00\nrejected 1 of 2\n` (verified with Python). The awk
alternative prints `rejected 2 of 2` and declares a divergence: its decimal
regular expression rejects exponent notation, whereas `float` follows
Python's `float()` (DC-3). The awk alternative uses `sorted-lines`
comparison.

### Status-quo alternative

Every job also carries a non-executable alternative with `kind =
"status-quo"` and a one-paragraph description of what a user does today (for
example, "a twenty-line Python script combining `re.search`, `try`/`except
ValueError`, and a `Counter`"). The Python alternative's line count is
recorded automatically in the generated job catalogue so roadmap task 5.2.2
can compare script sizes without re-deriving them.

## Plan of work

### Stage A: toolchain proof (EP-M0)

Add `pytest-bdd`, `syrupy`, and `hypothesis` to the `dev` dependency group in
`pyproject.toml` with `uv add --dev`, which also updates `uv.lock`. Add
`bdd_features_base_dir = "tests/features"` to `[tool.pytest.ini_options]` and
`"docs/"` to `[tool.mutmut] also_copy`. Create
`tests/features/job_corpus.feature` containing only the `Feature:` header and
one placeholder-free scenario, "The corpus harness is importable", with a
matching step module `tests/test_job_corpus_scenarios.py`, and a first syrupy
snapshot of a trivial report. Run every gate. This proves the new tools pass
Ruff, Interrogate, Pylint, Skylos, Vulture, the duplication check, and `ty`
before any real code exists. If a gate objects, fix it here.

### Stage B: domain first (EP-M1)

Write red tests, then the pure domain modules under `tests/job_corpus/`:

- `model.py`: enumerations `JobCategory`, `QuestionId` (Q1–Q8),
  `CaseTag`, `AlternativeKind` (`python`, `awk`, `status-quo`),
  `Comparison` (`exact`, `sorted-lines`), and `Diagnostic` (`none`, `input`,
  `runtime`); frozen, slotted dataclasses `InputFile`, `ExpectedOutcome`,
  `ObservedOutcome`, `JobCase`, `Alternative`, `CorpusJob`, and
  `RegisterEntry`.
- `policy.py`: `find_coverage_gaps`, `find_register_gaps`,
  `find_evidence_mismatches`, and `find_identity_errors` (duplicate job or
  case identifiers), each returning a tuple of `Finding` values and doing no
  I/O.
- `comparison.py`: `compare_outcome` (expected versus observed under a
  `Comparison`) and `evaluate_agreement` (classifies a case as `agrees`,
  `declared-divergence`, `undeclared-divergence`, or `stale-divergence`).

Red: create `tests/test_job_corpus_policy.py` and
`tests/test_job_corpus_properties.py` with the tests named in `Verification
plan`, importing names that do not exist yet; run them and observe
`ImportError`. Green: implement the three modules. Refactor: keep each
function within the complexity limits.

### Stage C: ports, adapters, and the application service (EP-M2)

- `ports.py`: `typing.Protocol` classes `JobSource` (`load_jobs() ->
  tuple[CorpusJob, ...]`), `RegisterSource` (`load_entries() ->
  tuple[RegisterEntry, ...]`), `RoadmapSource` (`task_ids() ->
  frozenset[str]`), and `AlternativeRunner` (`run(alternative, case) ->
  ObservedOutcome`).
- `adapters/toml_jobs.py`: `TomlJobSource(root: Path)` reading every
  `jobs/*/job.toml` with `tomllib`, resolving `program`, alternative `path`,
  and input `path` relative to the job directory, and raising
  `CorpusFormatError(path, key, reason)` on any schema violation.
- `adapters/markdown_docs.py`: `MarkdownRegisterSource(path: Path)` parsing
  the table between `<!-- decision-register:start -->` and
  `<!-- decision-register:end -->`, and `MarkdownRoadmapSource(path: Path)`
  collecting identifiers from lines matching `- [ ] N.N.N.` or `- [x]
  N.N.N.`.
- `adapters/process_runner.py`: `ProcessRunner(awk: str | None)` writing
  case inputs to a `tempfile.TemporaryDirectory`, then running
  `[sys.executable, "-I", script, *files]` or `[awk, "-f", script, *files]`
  with `env={"LC_ALL": "C", "PATH": os.environ["PATH"]}` for awk,
  `timeout=10`, and `capture_output=True`. When a case's `input_mode` is
  `stdin`, the single input is passed on standard input instead.
- `service.py`: `audit_corpus(jobs: JobSource, register: RegisterSource,
  roadmap: RoadmapSource) -> AuditReport` and `verify_alternative(job,
  alternative, runner) -> tuple[CaseResult, ...]`.
- `report.py`: `render_report(report: AuditReport) -> str`.

Red: `tests/test_job_corpus_toml.py`, `tests/test_job_corpus_register.py`
(adapter tests against `tmp_path` documents only), and
`tests/test_job_corpus_report.py` fail on missing imports. Green: implement.
Add the unhappy behavioural scenarios to the feature file and their steps.

### Stage D: corpus content (EP-M3)

For each job in `Corpus specification`, in category order: create
`job.toml` and `program.pokie` first and run the focused end-to-end test,
which fails because `alternative.py` is missing (red); then write
`alternative.py` (green) and `alternative.awk`, observing that awk agrees or
diverges exactly where declared. Commit after each category. Add the
happy-path behavioural scenarios. Demonstrate the order-preservation seeded
fault once and record its output in `Artefacts and notes`.

### Stage E: decision register (EP-M4)

Write `docs/decision-register.md` (contents in `Decision register
specification`). Red: `test_repository_register_is_complete_and_consistent`
is written before the document exists and fails with "register markers not
found". Green: write the document. Add the register scenarios to the feature
file.

### Stage F: documentation and completion (EP-M5)

Write ADR 004 and `docs/job-corpus.md`; update the design, terms of
reference, contents, repository layout, developers' guide, users' guide, and
README as described in `Documentation changes`; mark roadmap 1.1.1 done; run
every gate.

## Decision register specification

`docs/decision-register.md` opens with a purpose paragraph, the status
vocabulary from `docs/context.md` §1, and the meaning of each column. The
authoritative table sits between the two HTML comment markers and has the
columns `ID`, `Decision owner`, `Evidence task`, `Status`, `Gates`, and
`Corpus evidence`. Proposed rows:

```plaintext
Q1 | @leynos (project owner) | 5.2.2 | Open question | 5.2.2 | filter-error-lines, filter-server-errors, aggregate-status-counts
Q2 | @leynos (project owner) | 5.1.1 | Open question | 5.1.2, 5.1.3 | none
Q3 | @leynos (project owner) | 1.1.2 | Open question | 2.1.3, 6.1.1 | filter-server-errors, filter-missing-email, aggregate-endpoint-latency
Q4 | @leynos (project owner) | 4.2.1 | Open question | 4.2.2 | validate-request-ids
Q5 | @leynos (project owner) | 1.1.2 | Open question | 2.1.2, 2.2.1, 3.2.1 |
    filter-error-lines, filter-first-timeouts, validate-user-records, validate-optional-unit
Q6 | @leynos (project owner) | 4.1.2 | Open question | 4.1.2, 6.1.2 |
    validate-user-records, validate-request-ids, validate-optional-unit, aggregate-endpoint-latency
Q7 | @leynos (project owner) | 5.2.1 | Open question | 5.2.2 | aggregate-status-counts, aggregate-endpoint-latency
Q8 | @leynos (project owner) | 5.2.2 | Open question | 5.2.2 | none
```

Below the table, one short subsection per question states why the evidence
task was chosen, which corpus cases bear on it, and what would close it. Q1's
subsection states that the corpus is a candidate, not the "agreed corpus" its
resolution criterion requires, until the project owner agrees it. Q8's
subsection states that the project owner holds every decision until Q8 names
a sponsor or release approver.

## Behavioural specification

`tests/features/job_corpus.feature`:

```gherkin
Feature: Representative job corpus and decision register
  Pokie's first release must demonstrate filtering, capture validation, and
  aggregation jobs whose outcomes are specified before any interpreter exists.

  Scenario: Every Python alternative reproduces its expected outcomes
    Given the repository job corpus
    When each job's Python alternative runs against every case
    Then every observed outcome matches its expected outcome

  Scenario: Awk alternatives agree or declare their divergence
    Given the repository job corpus
    And an awk executable is available
    When each job's awk alternative runs against every case
    Then no case reports an undeclared or stale divergence

  Scenario: The corpus covers every job category and required edge case
    Given the repository job corpus
    When the corpus is audited
    Then the audit reports no coverage gaps

  Scenario: Every open question has one accountable owner
    Given the repository job corpus
    And the decision register in docs/decision-register.md
    When the corpus is audited
    Then questions Q1 to Q8 each have exactly one owner and known gates

  Scenario: A job whose expected output is wrong is rejected
    Given a temporary corpus copied from job "validate-user-records"
    And its "design-example" case expects standard output "1 3"
    When the job's Python alternative runs against every case
    Then the case "design-example" reports expected "1 3" and observed "1 2"

  Scenario: A register missing a question is rejected
    Given the repository job corpus
    And a decision register without the row for "Q5"
    When the corpus is audited
    Then the audit reports that "Q5" has no owner

  Scenario: A malformed job file is rejected with its location
    Given a temporary corpus whose job file lacks the key "expected"
    When the corpus is loaded
    Then loading fails naming the job file and the key "expected"
```

Step definitions live in `tests/test_job_corpus_scenarios.py`, which calls
`pytest_bdd.scenarios("job_corpus.feature")`.

## Milestones and plateaus

- EP-M0: the development group contains `pytest-bdd`, `syrupy`, and
  `hypothesis`; one trivial scenario and one snapshot pass; all gates pass.
  - Requirements: none directly; de-risks every later milestone.
  - Acceptance: `make check-fmt typecheck lint test` succeeds.
  - Conformance check:
    - No product code touched.
    - Only the three approved development dependencies added.
    - Trace links unchanged.
  - Recovery: revert the commit; `uv sync` restores the previous lock.
  - Remaining gaps: everything else.
  - Compatibility decision: none.
- EP-M1: pure domain model, policy, and comparison exist with passing unit
  and property tests.
  - Requirements: INV-COV-1, INV-REG-1, INV-REG-2 (policy level).
  - Acceptance: `pytest tests/test_job_corpus_policy.py
    tests/test_job_corpus_properties.py` passes; all gates pass.
  - Conformance check:
    - Domain modules import no adapter, `tomllib`, `subprocess`, or
      `pathlib` (verified by `rg`).
    - No public interface or dependency change.
    - Trace links current.
  - Recovery: revert the milestone commit.
  - Remaining gaps: no I/O, no corpus content.
  - Compatibility decision: none.
- EP-M2: adapters, service, and report exist; unhappy behavioural scenarios
  pass against temporary corpora.
  - Requirements: LEM-LOAD-1, INV-REPORT-1.
  - Acceptance: adapter, report, and scenario tests pass; all gates pass.
  - Conformance check:
    - Adapters depend on domain and ports only; no adapter imports another.
    - Subprocess use follows `Constraints`.
    - No trust boundary change beyond running repository-owned scripts.
  - Recovery: revert the milestone commit.
  - Remaining gaps: real corpus content.
  - Compatibility decision: none.
- EP-M3: nine jobs and fifteen cases exist; Python alternatives reproduce
  every expected outcome; awk alternatives agree or declare divergences;
  coverage audit is clean.
  - Requirements: RM-1.1.1 categories, inputs, expected outcomes, and
    alternatives; INV-ORACLE-1, INV-ORACLE-2, INV-COV-1, INV-ORDER-1.
  - Acceptance: `make test` shows one passing
    `test_python_alternative_reproduces_expected` parameter per case.
  - Conformance check:
    - Every expected outcome is consistent with DES-4.1, DES-4.2, DES-4.3,
      DES-5, DES-9, DC-1, DC-3, and DC-4; any inconsistency is escalated.
    - Proposed programs are labelled not executable.
    - No contract changed.
  - Recovery: each category is a separate commit; revert the failing one.
  - Remaining gaps: register and documentation.
  - Compatibility decision: none.
- EP-M4: `docs/decision-register.md` exists and passes
  `test_repository_register_is_complete_and_consistent` and the register
  scenarios.
  - Requirements: RM-1.1.1 owners for Q1–Q8; INV-REG-1; INV-REG-2.
  - Acceptance: all gates, including `make markdownlint`.
  - Conformance check:
    - Owners name only established roles.
    - Gates exist in `docs/roadmap.md`.
  - Recovery: revert the commit.
  - Remaining gaps: documentation.
  - Compatibility decision: none.
- EP-M5: documentation, ADR 004, and roadmap updated; plan `COMPLETE`.
  - Requirements: AGENTS.md documentation duties.
  - Acceptance: every gate in `Validation and acceptance` passes.
  - Conformance check:
    - Terms of reference §9 and design §10 point to the register and corpus.
    - README makes no new capability claim.
    - Roadmap 1.1.1 checked.
  - Recovery: documentation-only commits can be reverted independently.
  - Remaining gaps: Q1–Q8 remain open by design; 1.1.2 ratifies contracts.
  - Compatibility decision: none.

## Documentation changes

- `docs/adr-004-job-corpus-and-decision-register.md` (new, status
  `Proposed`): context (no interpreter, RM-1.1.1), decision drivers, options
  considered (Markdown-only corpus; TOML corpus with executable alternatives;
  YAML corpus needing PyYAML at test time; Gherkin-only examples), chosen
  option, consequences (alternatives become maintained code; awk portability
  discipline; register edited by the owner), and outstanding decisions (CR
  normalization handed to 1.1.2).
- `docs/job-corpus.md` (new): purpose, evidence status, schema reference for
  `job.toml`, a catalogue table (job, category, goals, decisions, cases,
  declared divergences, Python alternative lines), and how corpus evidence
  feeds roadmap tasks 1.1.2, 2.1.3, 2.2.3, 5.2.1, and 5.2.2.
- `docs/decision-register.md` (new): as specified above.
- `docs/pokie-design.md` §10: one paragraph naming the corpus as the input to
  differential checks and linking ADR 004; §11: link the register for owners.
- `docs/terms-of-reference.md` §9: replace "Owners are unassigned unless
  stated. Roadmap task 1.1.1 assigns decision owners" with a sentence pointing
  to `docs/decision-register.md`; §7 Table 3: link the corpus from the
  "Filtering and aggregation corpus" cell.
- `docs/developers-guide.md`: new section "Job corpus and decision register"
  covering layout, the red-first procedure for adding a job, alternative
  conventions (decode per record, `-I`, POSIX awk, `LC_ALL=C`, deterministic
  ordering), declaring divergences, maintaining the register, and the
  hexagonal module boundaries with their reuse policy.
- `docs/users-guide.md`: new short section "Representative jobs" explaining
  that the corpus shows what pokie is intended to do, that its programs are
  proposed and not executable, and where to read expected outcomes.
- `docs/contents.md`: add the three new documents.
- `docs/repository-layout.md`: add `tests/job_corpus/`, `tests/features/`,
  and `tests/__snapshots__/`.
- `README.md`: add `docs/job-corpus.md` to "Learn more" and point the
  Contributing paragraph at it; no capability claim changes.
- `docs/roadmap.md`: change `- [ ] 1.1.1.` to `- [x] 1.1.1.` only after
  every gate passes.

## Concrete steps

Run all commands from the repository root. Log every gate with `tee`:

```bash
BRANCH=$(git branch --show-current)
make check-fmt 2>&1 | tee /tmp/check-fmt-pokie-$BRANCH.out
make typecheck 2>&1 | tee /tmp/typecheck-pokie-$BRANCH.out
make lint 2>&1 | tee /tmp/lint-pokie-$BRANCH.out
make test 2>&1 | tee /tmp/test-pokie-$BRANCH.out
make markdownlint 2>&1 | tee /tmp/markdownlint-pokie-$BRANCH.out
make nixie 2>&1 | tee /tmp/nixie-pokie-$BRANCH.out
```

Run the gates sequentially, never in parallel. EP-M0:

```bash
uv add --dev "pytest-bdd>=9.0.0" "syrupy>=6.1.1" "hypothesis>=6.169.4"
```

Focused red/green runs during EP-M1 to EP-M3:

```bash
uv run pytest tests/test_job_corpus_policy.py -v
uv run pytest tests/test_job_corpus_alternatives.py -v -k validate-user-records
```

Expected red transcript at the start of EP-M1 (abridged):

```plaintext
E   ModuleNotFoundError: No module named 'job_corpus'
```

Expected green transcript at the end of EP-M3 (abridged):

```plaintext
test_python_alternative_reproduces_expected[validate-user-records/design-example] PASSED
test_awk_alternative_agrees_or_declares_divergence[validate-user-records/unicode-digits] PASSED
```

Commit after each milestone (and after each job category in EP-M3) with an
imperative subject under 50 characters.

## Validation and acceptance

Acceptance is behavioural:

1. `make test` passes with 15 passing Python-alternative parameters and the
   awk parameters passing (or skipped with "awk not on PATH" only where awk is
   absent).
2. Changing `validate-user-records/design-example` to expect `1 3` fails
   with a message containing `expected '1 3\n'` and `observed '1 2\n'`;
   reverting restores green.
3. Removing the Q5 row from the register fails
   `test_repository_register_is_complete_and_consistent` with a report line
   naming `Q5`; reverting restores green.
4. `docs/job-corpus.md` and `docs/decision-register.md` render on GitHub and
   pass `make markdownlint`.

Red-Green-Refactor evidence is recorded in `Artefacts and notes` for each
milestone: the red command and failure, the green command and pass, and the
refactor rerun.

Quality criteria:

- Tests: `make test` passes.
- Verification: INV-ORACLE-1, INV-ORACLE-2, INV-COV-1, INV-REG-1,
  INV-REG-2, LEM-LOAD-1, INV-ORDER-1, and INV-REPORT-1 discharged as
  described.
- Lint and type checking: `make check-fmt`, `make typecheck`, and `make lint`
  pass after each milestone.
- Documentation: `make markdownlint` (including spelling) and `make nixie`
  pass.

## Idempotence and recovery

Every step is repeatable. `uv add` is idempotent for an already-present
requirement. Tests create inputs in temporary directories and never write to
the repository. Snapshot updates are explicit (`pytest --snapshot-update`) and
must be reviewed in the diff. If a milestone fails midway, revert to the last
milestone commit with `git revert` rather than rewriting history.

## Artefacts and notes

Scratch prototype transcript (2026-10-15, CPython 3.14, GNU Awk 5.3.0):

```plaintext
--F2 awk        /upload /health /spaced
--F3 awk        2 4 5
--F4 awk        timeout 1 / timeout 2 / read 4
--V1 py         1 2   (unicode case: 1 0)
--V1 awk        1 2   (unicode case: 0 1)
--V2 awk        00ff 12 / 1a2b 007 / malformed 2
--A2 py, awk    /a 20.00 / /b 4.00 / rejected 2 of 7
--A2 spellings  py: /d 1000.00 / rejected 1 of 2; awk: rejected 2 of 2
--F1 invalid    ok ERROR one, then UnicodeDecodeError, status 1
```

## Interfaces and dependencies

Development dependencies (group `dev`): `pytest-bdd>=9.0.0` for behavioural
scenarios, `syrupy>=6.1.1` for report snapshots, and `hypothesis>=6.169.4` for
property tests. No runtime dependency. Standard library: `tomllib`,
`subprocess`, `tempfile`, `dataclasses`, `enum`, `typing`.

Package layout (all under `tests/`, imported as `job_corpus`):

```plaintext
tests/job_corpus/__init__.py          package docstring; scope and reuse policy
tests/job_corpus/model.py             domain types
tests/job_corpus/policy.py            pure validation policy
tests/job_corpus/comparison.py        outcome comparison and agreement
tests/job_corpus/ports.py             JobSource, RegisterSource, RoadmapSource, AlternativeRunner
tests/job_corpus/service.py           audit_corpus, verify_alternative
tests/job_corpus/report.py            render_report
tests/job_corpus/adapters/toml_jobs.py
tests/job_corpus/adapters/markdown_docs.py
tests/job_corpus/adapters/process_runner.py
tests/job_corpus/jobs/<job-id>/job.toml, program.pokie, alternative.py, alternative.awk, inputs/
tests/conftest.py                     corpus_root, repository_jobs, process_runner fixtures
tests/features/job_corpus.feature
```

Key signatures:

```python
@dataclasses.dataclass(frozen=True, slots=True)
class ExpectedOutcome:
    stdout: bytes
    exit_status: int
    diagnostic: Diagnostic


class AlternativeRunner(typ.Protocol):
    def run(self, alternative: Alternative, case: JobCase) -> ObservedOutcome: ...


def compare_outcome(
    expected: ExpectedOutcome, observed: ObservedOutcome, comparison: Comparison
) -> OutcomeComparison: ...


def find_coverage_gaps(jobs: cabc.Sequence[CorpusJob]) -> tuple[Finding, ...]: ...
```

`job.toml` schema (version 1):

```toml
schema = 1
id = "validate-user-records"
title = "Count accepted and rejected user records"
category = "capture-validation"
goals = ["G2", "G3"]
decisions = ["Q5", "Q6"]
contracts = ["design-contracts §1", "design-contracts §3", "pokie-design §5"]
evidence_status = "assumption"
program = "program.pokie"
notes = ["int follows int(s, 10), so non-ASCII decimal digits are accepted (Q6)."]

[[alternatives]]
kind = "python"
path = "alternative.py"

[[alternatives]]
kind = "awk"
path = "alternative.awk"
comparison = "exact"
diverges_on = ["unicode-digits"]
divergence_reason = "POSIX awk has no Unicode decimal conversion."

[[alternatives]]
kind = "status-quo"
description = "A Python script combining re.search, try/except ValueError, and a Counter."

[[cases]]
id = "design-example"
tags = ["malformed-record"]
input_mode = "files"
inputs = [{ name = "users.log", text = "user=ada uid=42\nuser=lin uid=no\nuser=sam uid=-1\n" }]
expected = { stdout = "1 2\n", exit_status = 0, diagnostic = "none" }
```

Signposted skills for the implementer: `execplans` (keep this plan current),
`hexagonal-architecture` (port and adapter boundaries), `python-router`, then
`python-data-shapes` (frozen dataclasses), `python-types-and-apis`
(protocols), `python-testing` (fixtures, parametrization, syrupy),
`hypothesis` (properties), `python-errors-and-logging`
(`CorpusFormatError`), `leta` (navigation), `en-gb-oxendict-style`
(documentation), and `commit-message`.

Signposted documents: `docs/terms-of-reference.md` §§4–9,
`docs/pokie-design.md` §§1–5, 9–11, `docs/design-contracts.md` §§1, 3–4,
`docs/context.md`, ADRs 001–003, `docs/developers-guide.md`,
`docs/documentation-style-guide.md` (ADR template),
`docs/scripting-standards.md` (subprocess hygiene), and
`docs/complexity-antipatterns-and-refactoring-strategies.md` (guard clauses,
dispatch tables, extract method; the repository's limit is cyclomatic
complexity 8).

## Revision note

2026-10-15: initial draft.
