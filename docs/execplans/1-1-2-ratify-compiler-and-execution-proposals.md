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

Task 1.1.1 builds the evidence base: an executable job corpus and a register of
open decisions. This task, 1.1.2, uses that evidence to settle five contract
areas that every later slice depends on:

1. Scope: what the program namespace is, which statements each section
   allows, and which names are reserved.
2. Input ownership: who reads input, how bytes become records and fields,
   and what happens when user code or a child process competes for the input
   stream.
3. Control transfer: how `next` and `exit` cross user loops, `try`, `with`,
   and `finally`, and what happens when a construct swallows them.
4. Binding visibility: when capture-pattern bindings become visible, what
   guards and the helpers they call see, and where record-scoped names may be
   read.
5. Finalization: when the `end:` block runs, what each failure does to it,
   and which process status and diagnostic result.

A *contract* is a precise statement of observable behaviour in
`docs/pokie-design.md`, `docs/design-contracts.md`, or an architectural
decision record (ADR). To *ratify* a contract, the project owner accepts it,
the ADR that records it moves from `Proposed` to `Accepted`, and later roadmap
tasks build on it without reopening it. A *counterexample* is a concrete
program, input, or host-Python behaviour that breaks or disambiguates a
proposed contract. The roadmap's success criterion is "scope, input ownership,
control transfer, binding visibility, and finalization are decided;
counterexamples update the contracts".

After this change, a reader can do four things that are not possible today.

First, they can open `tests/contract_ratification/register.toml` and find every
decision. Each entry has a stable identifier such as `CONTROL-3`, its area, its
rule, whether the evidence upheld or amended the original proposal, the
counterexamples behind it, its executable evidence, and the downstream roadmap
tasks that must implement it. Each area carries the project owner's verdict,
with a date and a link to where it was given.

Second, they can run `make test` and see the register checked. Every decision
cites evidence that exists. Every counterexample has a disposition. Every
*witness* (evidence that the chosen rule is feasible on CPython 3.14) passes.
Every *control* (the same check run against the rejected alternative) fails in
the predicted way, which proves the evidence can discriminate. The ratification
verdict is `ratified` only when the owner has accepted every area.

Third, they can read ADR 0002 as `Accepted`, and a new ADR 0005, also
`Accepted`, that gives the record reader sole ownership of program input.
`docs/pokie-design.md` and `docs/design-contracts.md` state the ratified rules,
cite the decision identifiers, and include a decision index that a test keeps
identical to the register.

Fourth, they can run three new corpus jobs that would have exposed the
ambiguities resolved here. For example, `aggregate-port-changes` prints `a 80`,
`a 443`, then `2 1` under the ratified guard rule. It would print only `0 1` if
helpers called from a guard could see uncommitted candidate bindings.

Success is observable:

- `make test` passes, including
  `tests/test_contract_control.py::test_signal_unwinding_matches_model` and
  `tests/test_contract_ratification_scenarios.py::test_every_contract_area_is_ratified`.
- Setting any area's `owner_verdict` back to `pending` makes
  `test_repository_register_is_ratified` fail, naming that area.
- Replacing the chosen control-signal adapter with one whose signals derive
  from `Exception` makes the unwinding property fail, with a shrunk shape
  containing `except Exception:`. The plan keeps exactly that mutant as a
  permanent control test.
- Deleting a row from the decision index in `docs/design-contracts.md` makes
  `test_contract_index_matches_register` fail.

No product behaviour ships. `pokie/` is untouched, and no document may claim
that pokie can run a program.

## Constraints

- Two tracks. Track A (EP-M1 and EP-M2) builds the register core and the
  host evidence. It may start as soon as this plan is approved, because it
  depends only on harness code already merged to `main`. Track B (EP-M3, EP-M4,
  and EP-M5) needs the corpus, so it may start only once task 1.1.1 is
  complete. Completion means that the 1.1.1 roadmap checkbox is ticked,
  `docs/job-corpus.md` and `docs/decision-register.md` exist, the corpus holds
  its eleven planned jobs, and the 1.1.1 repository audit reports `proceed`. At
  drafting time (2026-11-14), only EP-M0 and EP-M1 of the 1.1.1 plan have
  merged.
- No product behaviour is introduced. `pokie/` must not change. Documents
  describe ratified rules as contracts for future implementation, never as
  delivered capability.
- Decisions belong to the project owner. The only established role is the
  project owner, `@leynos` (terms of reference §4 Table 2), who owns Q3 and Q5
  in the decision register. The implementer prepares recommendations and
  evidence, but records `owner_verdict = "accepted"` only after the owner
  accepts explicitly in a pull-request review or comment. The comment URL is
  recorded in `decided_in`.
- Contracts must not drift silently. A counterexample that no amendment can
  resolve gets effect `falsifies`, which flips the ratification verdict to
  `revise-contracts`. The plan is then set to `BLOCKED` and escalated. This is
  the falsification outcome that phase 1 exists to detect.
- No runtime or development dependency is added. `pytest-bdd` 9, `syrupy` 6,
  and `hypothesis` 6 are already in the `dev` group of `pyproject.toml`.
- All new code is test-only and lives under `tests/`. The wheel packages only
  `pokie` (`[tool.hatch.build.targets.wheel] packages = ["pokie"]`).
- Hexagonal boundaries apply inside `tests/contract_ratification/`:
  - The domain modules (`model.py`, `policy.py`, `render.py`,
    `control_model.py`, and `records_model.py`) perform no input/output
    (I/O). They do not call `exec`, `compile`, or `subprocess`. They import
    nothing from `tomllib`, `os`, `io`, `sys`, `shutil`, `tempfile`, or any
    `adapters` package, whether `contract_ratification.adapters` or
    `job_corpus.adapters`.
  - Importing another package's domain values (for example
    `job_corpus.model.Observation`) is allowed.
  - `ports.py` declares `typing.Protocol` interfaces that both models and
    adapters satisfy.
  - Only adapters execute host Python, read files, or run processes.
  - An abstract syntax tree (AST) test enforces these rules, extending
    `tests/test_job_corpus_boundaries.py`.
- Host sketches are verification oracles, not compiler prototypes. They
  build Python source from small structured shape values and never parse pokie
  source text. They model one action, or one driver lifecycle, at a time.
  Roadmap task 1.2.2 owns the intermediate representation (IR) and the
  reference evaluator, and is recorded in `discharged_by` as the task that must
  agree with, then replace, these models.
- Every code file stays under 400 lines, and every function stays within the
  Ruff and Pylint limits in `pyproject.toml`: `max-complexity = 8`,
  `max-args = 4`, `max-locals = 10` (Ruff) and 20 (Pylint), and
  `max-bool-expr = 2`. Pylint's `max-args = 4` counts fixtures and parametrized
  arguments together.
- Subprocess probes run through `ProcessRunner`
  (`tests/job_corpus/adapters/process_runner.py`). They use argument lists,
  never `shell=True`, and an explicit environment allowlist. Python children
  run as `sys.executable -I`. No probe uses the network or writes outside its
  temporary directory. Only behaviour that needs process isolation
  (`sys.modules["__main__"]`, file-descriptor 0, process exit status, or
  signals) is a subprocess probe. Everything else is an in-process test in a
  fresh module namespace.
- Data tables live in data files: the register in
  `tests/contract_ratification/register.toml`, and fixture registers,
  seeded-defect tables, and the lifecycle outcome table in `tests/data/`.
- Prose and identifiers use en-GB-oxendict spelling ("-ize", "-yse",
  "-our"), except external API names. Markdown wraps at 80 columns, and code
  blocks wrap at 120 columns.
- ADR edits follow `docs/documentation-style-guide.md` "Architectural decision
  records": the template title form, the required sections in order, `Accepted`
  with a date and a decision summary, and no renumbering. The new ADR is
  numbered 0005, because 1.1.1 reserves 0004 for its corpus-schema ADR.

## Tolerances (exception triggers)

ExecPlan files are excluded from every size limit below, including when this
plan is edited in the same change. Counts compare against the merge base with
`main` at the start of execution, recorded in `Progress` as `BASE`.

- Code: no more than 3,200 net Python lines (additions minus deletions) and
  32 Python files under `tests/`, excluding `tests/job_corpus/jobs/`.
- Corpus content: no more than 950 net lines and 15 files under
  `tests/job_corpus/jobs/`. That is about 290 lines per job, taken from the
  existing two-case job (287 lines in four files) plus the extra cases.
- Configuration and data: no more than 700 net lines across
  `tests/contract_ratification/register.toml`, `tests/data/*`,
  `tests/features/*.feature`, snapshot files under `__snapshots__/`, and
  `pyproject.toml`. Changes to `pyproject.toml` are limited to dead-code,
  duplication, and lint-scope settings, at most 40 lines. Any change to
  `[project]`, the dependency groups, or `uv.lock` breaches this limit.
- Documentation: no more than 1,400 net lines under `docs/` (excluding
  `docs/execplans/`) and `README.md`.
- Enforce each category independently. Spare capacity in one category never
  offsets another.
- Interface: if anything under `pokie/` must change, stop and escalate.
- Dependencies: if any new dependency is needed, stop and escalate.
- Track B precondition: if task 1.1.1 is incomplete when EP-M2 ends, set the
  plan to `BLOCKED (awaiting 1.1.1)`. Record in `Progress` whether the owner
  has granted 1.1.1 the budget increase it needs to finish.
- Falsification: if a counterexample has effect `falsifies`, or a witness
  fails on CPython 3.14, set the plan to `BLOCKED` and escalate.
- Vacuity: if a control passes (that is, the rejected alternative behaves
  like the chosen rule), the evidence for that decision is vacuous. Stop,
  record it, and escalate. Never delete or weaken the control.
- Owner redirection: if the owner rejects a recommendation, change only what
  the owner directs. Then re-run that area's EP-M2 evidence and the affected
  corpus jobs. If more than eight decisions change, re-plan the EP-M5
  documentation budget before continuing.
- Overlap: if a model or sketch needs to parse pokie text, evaluate more
  than one action's unwinding (beyond the lifecycle table), or grow past 250
  lines, it is turning into roadmap task 1.2.2. Stop and escalate.
- Runtime: if the new tests add more than 30 seconds to `make test` on this
  machine, lower `max_examples` for the in-process properties through the
  profiles in `tests/conftest.py`. If that is not enough, stop and escalate.
- Tooling: if a lint gate rejects the new code and the only fix would exclude
  `tests/` or `tests/contract_ratification/` from that gate, stop and escalate.
- Coverage: if the coverage ratchet (`.coverage-baseline-v2.python`) falls,
  restructure the code or add boundary tests. Never lower or bypass the ratchet.
- Iterations: if a gate still fails after three fix attempts, stop and
  escalate.

## Risks

- Risk: task 1.1.1 may not finish without an owner decision, because its
  plan measured 4,797 of its 4,800 net Python lines with EP-M2 to EP-M5 still
  open. Severity: high. Likelihood: high. Mitigation: the two-track split lets
  Track A proceed. EP-M0 records whether the owner has raised 1.1.1's budget.
  Track B waits for 1.1.1 and is rebased onto it.
- Risk: Track B edits files that 1.1.1 also edits: the counts pinned in
  `tests/test_job_corpus_alternatives.py`, the Q3 and Q5 rows of
  `docs/decision-register.md`, and the "Phase 1 findings" in
  `docs/job-corpus.md`. Severity: medium. Likelihood: certain. Mitigation:
  Track B starts only after 1.1.1 merges, and makes those edits in EP-M3,
  together with the jobs that require them.
- Risk: the 1.1.1 strict TOML helpers are private (`_table`, `_strings`,
  `_member`, and others in `tests/job_corpus/adapters/toml_values.py`), and
  1.1.1 is still changing them. Severity: medium. Likelihood: high. Mitigation:
  promote them to public names in a separate small pull request on `main`,
  updating every caller at once with no aliases. Track A's loader depends on
  that pull request. If the owner prefers not to touch 1.1.1's files before it
  merges, the register loader moves to Track B and Track A tests the domain
  against in-memory registers only.
- Risk: a model restates the rule it verifies, so the evidence is vacuous.
  Severity: high. Likelihood: medium. Mitigation: each model is compared
  differentially with real CPython execution of rendered Python source.
  Controls run the same property against a rejected-alternative adapter through
  the same port, and must produce a named shrunk counterexample.
- Risk: the sketches drift into a second compiler or evaluator. Severity:
  medium. Likelihood: medium. Mitigation: the overlap tolerance, the one-action
  scope, and the `discharged_by = ["1.2.2"]` replacement obligation.
- Risk: the owner disagrees with several recommendations. Severity: medium.
  Likelihood: medium. Mitigation: EP-M4 asks for one verdict per area, with
  listed exceptions, and gives options and trade-offs for every contested
  decision. EP-M5 starts only after the verdicts are recorded.
- Risk: `mdtablefix` (run by `make fmt`) re-pads tables, rewrites `...` to
  `…` in table cells, and skips tables whose code spans contain an unescaped
  `|`. Severity: low. Likelihood: high. Mitigation: the decision index carries
  only identifiers, areas, dispositions, verdicts, and dates. The renderer
  escapes `|`. The comparison splits cells on unescaped pipes, trims them, and
  ignores the separator row.
- Risk: PEP 765 `SyntaxWarning`s from generated shapes flood the test
  output. Severity: low. Likelihood: medium. Mitigation: the shape strategy
  never places `break` or `continue` directly in a `finally` block. A dedicated
  test covers those cases and asserts the warning.
- Risk: Vulture and Skylos flag pytest-bdd steps, Hypothesis helpers, and
  enum members reached only from TOML. Severity: low. Likelihood: high.
  Mitigation: extend the single scanned whitelist
  `tests/job_corpus/vulture_whitelist.py` and its two-way guard in
  `tests/test_job_corpus_dead_code.py`. A second whitelist would mask entries,
  because Vulture matches by name.
- Risk: subprocess-only and failure-only lines change coverage. Severity:
  medium. Likelihood: medium. Mitigation: subprocess probe scripts are not
  imported, so SlipCover does not count them (as with today's `reference.py`).
  Assertion messages are precomputed, as 1.1.1 does, so no line runs only on
  failure.
- Risk: awk alternatives behave differently under mawk (on CI) and GNU Awk
  (locally). Severity: low. Likelihood: low. Mitigation: use POSIX features and
  explicit character classes only.

## Progress

- [x] (2026-11-14) Branch renamed to
  `1-1-2-ratify-compiler-and-execution-proposals`, tracking the same name on
  `origin`.
- [x] (2026-11-14) Leta workspace registered. Leta's Python language server
  (basedpyright) failed to start, so symbol navigation fell back to file reads.
- [x] (2026-11-14) Wyvern reconnaissance (three read-only agents): the 1.1.1
  plan's state and budget history; the harness architecture and tooling; and
  contract tensions across the design, contracts, context, terms of reference,
  and ADRs 0001–0002.
- [x] (2026-11-14) Prior-art and host-semantics research with Firecrawl: the
  POSIX awk `exit`, `next`, `getline`, and `END` rules; the Python 3.14 `match`,
  `try`, and `exec`/`compile` contracts; PEP 765; and PAWK.
- [x] (2026-11-14) Scratch CPython 3.14.7 probes confirmed the load-bearing
  host behaviours (see `Artefacts and notes`).
- [x] (2026-11-14) Draft ExecPlan written and committed.
- [x] (2026-11-14) Expert-panel review by four independent reviewers
  (language semantics, verification, architecture and process, and user
  advocacy). They raised 11 blocking, 35 major, and 30 minor findings, all
  dispositioned in this revision (see `Decision log`).
- [x] (2026-11-14) Draft pull request opened for review:
  <https://github.com/leynos/pokie/pull/39>.
- [ ] Plan approved by the project owner.
- [ ] EP-M0: entry checks and baseline.
- [ ] EP-M1 (Track A): register domain, loader, verdict, and scenarios.
- [ ] EP-M2 (Track A): host evidence, one commit per contract area.
- [ ] EP-M3 (Track B): counterexample corpus jobs and corpus documents.
- [ ] EP-M4 (Track B): owner ratification gate.
- [ ] EP-M5 (Track B): contract documents, ADRs, and roadmap completion.

## Surprises & discoveries

- Observation: task 1.1.1 is only partly delivered, and its line budget is
  exhausted. Evidence: its plan's `Progress` marks EP-M2 partial and EP-M3 to
  EP-M5 undelivered, and reports 4,797 of 4,800 net lines.
  `tests/test_job_corpus_alternatives.py` pins `EXPECTED_JOB_COUNT = 1`.
  Impact: the two-track structure.
- Observation: Python's native `match` leaks candidate bindings when a guard
  is false (`guard-false leak: ada 7`). Impact: confirms 1.1.1 OBS-08 and
  BIND-1.
- Observation: a static rule cannot prevent signal suppression. Aliases
  (`BE = BaseException`), shadowing (`Exception = BaseException`), computed
  handler types (`except type(x)`), `except* BaseException`, and signals raised
  from `except` or `else` clauses all swallowed a `BaseException` signal in
  reviewer experiments. A pending-signal flag checked at the end of the action
  caught every case. Impact: CONTROL-3 adds a runtime check.
- Observation: a guard on `sys.stdin` does not stop a child process from
  reading program input. `subprocess.run(["wc", "-l"])` in one action consumed
  198,141 of 200,000 piped lines, and nothing failed. Impact: INPUT-5 moves
  ownership to file descriptor 0.
- Observation: after a user's `sys.stdin.readline()`, a binary driver reading
  `sys.stdin.buffer` saw zero records, not two, because the text layer had
  buffered everything. Impact: the corrected `PRB-INPUT-STDIN-RACE` expectation.
- Observation: in CPython 3.14 on Linux, the default `multiprocessing` start
  method is `forkserver`. With a pokie `__main__` module, a `Pool` either
  re-ran the `.pokie` file as Python (`SyntaxError`) or hung (no `__file__`).
  Only `fork` worked. Restoring `__main__` before `atexit` handlers ran broke
  later pickling. Impact: SCOPE-1 leaves the module installed and documents the
  start-method limitation.
- Observation: separately executed compilation units overwrite the module's
  `__annotate__` in Python 3.14. Two units kept only the second unit's
  annotations. Impact: the stronger CX-02 witness for SCOPE-2.
- Observation: `next` inside `with sqlite3_connection:` rolled the
  transaction back, because `__exit__` sees the signal as an exception. Impact:
  CONTROL-2 documents this, and CX-25 records it.
- Observation: splitting bytes on `\n` and decoding each record separately
  fails for UTF-16 and keeps a UTF-8 byte-order mark (BOM) as record content.
  Impact: INPUT-3 uses one incremental decoder per operand.
- Observation: Python 3.14 evaluates annotations and `type` aliases lazily,
  so they read a record-scoped global from a later record, as generator
  expression bodies do. Lambda defaults are eager. Impact: BIND-5.
- Observation: when standard output cannot be flushed at exit, CPython exits
  with status 120. A `print` wrapped in `except Exception` keeps running after
  a broken pipe. Restoring the default `SIGPIPE` disposition gives status 141
  with no noise, as gawk does. Impact: FINAL-2 and FINAL-6.
- Observation: GNU Awk 5.3.0 stops with `fatal: cannot open file` on a
  missing later operand, after printing earlier records. It does not run `END`,
  and exits with status 2. The draft's "warns and continues" was wrong. Impact:
  CX-07 now upholds INPUT-4.
- Observation: `"a\x1cb".split()` and `"a\xa0b".split()` both give two items,
  while gawk's default field splitting gives `NF=1`. `"".split(",")` gives one
  item, while awk gives `NF=0`. Impact: INPUT-10.
- Observation: `ProcessRunner` refuses an operand that names no input
  (`_materialize` raises `EvidenceFormatError`), by design after 1.1.1's runner
  hardening. Impact: there is no missing-operand corpus case. CX-07 cites the
  decision and the gawk research.
- Observation: a pytest-bdd scenario bound explicitly with `@scenario` can
  carry a stacked `xfail` marker. Without `raises=AssertionError`, a missing
  step definition is reported as XFAIL. Impact: every pre-milestone marker sets
  `raises=AssertionError`.
- Observation: `hypothesis.find` defaults to 2,000 examples and suppresses
  health checks, and `hypothesis.event` counts cannot be asserted. Impact:
  controls rerun the witness property itself against the mutant adapter, and
  class coverage uses explicit `@example` cases.
- Observation: ADR 0002 deviates from the current ADR template. It has
  `Consequences` and `Alternatives considered` instead of
  `Known risks and limitations` and `Options considered`, and its title lacks
  the template prefix. Impact: EP-M5 restructures it while accepting it.

## Decision log

- Decision: deliver ratification as an executable register with evidence.
  Rationale: the phase 1 idea is falsifiable only if a changed contract or a
  broken host assumption fails a test. Date: 2026-11-14.
- Decision: split delivery into Track A (EP-M1 and EP-M2) and Track B (EP-M3
  to EP-M5). Rationale: 1.1.1 may stall on its budget, but the register and
  host evidence do not depend on its unfinished milestones. Ratification
  "against the corpus" still waits for the corpus. Date: 2026-11-14, following
  the architecture review.
- Decision: write each control as the witness property itself, run with the
  same strategy and settings against a rejected-alternative adapter of the same
  port. It runs inside `pytest.raises(AssertionError)` with `database=None` and
  `report_multiple_bugs=False`, and asserts the shrunk example. Rationale:
  `hypothesis.find` uses a different budget and suppresses health checks, so
  its success says nothing about the witness's power. Date: 2026-11-14,
  following the verification review.
- Decision: put an explicit `@hypothesis.example` on each property for every
  required input class, and do not assert event statistics. Rationale:
  statistics cannot be asserted, while examples are deterministic and
  reviewable. Date: 2026-11-14.
- Decision: cut the register's generated-register property and the
  lifecycle model, using data tables instead. The lifecycle outcome table
  (`tests/data/lifecycle_outcomes.json`), derived row by row from
  `docs/design-contracts.md` Table 2, is the model. Rationale: the domains are
  finite and small, and the cut frees budget for the controls. Date: 2026-11-14.
- Decision: keep a small renderer for the decision index, used both for the
  owner dossier and for `docs/design-contracts.md` §6, and snapshot it only for
  a fixture register that exercises escaping and ordering. Rationale: a
  snapshot of the live register would churn at EP-M4 and would duplicate the
  document-sync test. AGENTS.md requires snapshots to capture meaningful,
  stable contracts. Date: 2026-11-14.
- Decision: the verdict has four values with this precedence:
  `revise-contracts` (a falsifying counterexample or a failing witness), then
  `revise-evidence` (a vacuous control or an unresolved reference), then
  `pending-owner`, then `ratified`. Rationale: evidence defects are the
  implementer's to fix, not the owner's. Date: 2026-11-14.
- Decision: record owner verdicts per contract area, with explicit
  per-decision exceptions. Each area verdict has `decided_on` and `decided_in`
  (a review or comment URL). A later task may set a decision to `superseded`,
  citing its superseding ADR, without breaking the ratification test.
  Rationale: thirty-odd separate verdicts would be ceremony, and an approval
  given only in conversation leaves no durable record. Date: 2026-11-14.
- Decision: the EP-M4 gate is a planned wait, recorded as
  `IN PROGRESS (awaiting owner verdicts, EP-M4)`. `BLOCKED` is reserved for
  deviations and tolerance breaches. Date: 2026-11-14.
- Decision: input ownership gets its own ADR 0005. Rationale: Q3 has its own
  lifecycle through task 6.1.1, and ADR 0002 is titled for scope and lifecycle.
  Date: 2026-11-14.
- Decision: ADR 0001 stays `Proposed` by default, gaining the ratified
  lowering constraints. It moves to `Accepted` only if the owner asks.
  Rationale: its own status asks for packaging evidence (Q2, task 5.1.1); the
  style guide allows `Outstanding decisions` only on `Proposed` ADRs; and the
  1.1.2 success criterion does not need ADR 0001 accepted. Date: 2026-11-14.
- Decision: static-validation rules are ratified as contracts, and later
  tasks enforce them. The register's `discharged_by` lists those tasks, and
  each must add a failing static-validation test per rule. Rationale: no parser
  exists. Phase 1 "supplies decisions and evidence inputs, not a parser layer".
  Date: 2026-11-14.
- Decision: add one sentence to `docs/users-guide.md` pointing to the
  ratified decision index as future behaviour, and make no other change.
  Rationale: no behaviour ships, but the guide's reference to "proposed"
  behaviour would otherwise go stale. Date: 2026-11-14, following the
  user-advocacy review.
- Decision: reviewer recommendations that conflict are put to the owner as
  options, not resolved silently. Rationale: they are owner decisions with
  legitimate trade-offs. There are three: CONTROL-1's strictness, INPUT-4's
  existence pre-check, and SCOPE-7's `sys.path[0]`. Date: 2026-11-14.

## Outcomes & retrospective

Not started. On completion, record:

- which decisions were ratified, amended, deferred, or redirected by the
  owner;
- which counterexamples changed contracts;
- whether any control exposed a vacuous model;
- the final size of each budget category.

## Context and orientation

The repository is a Python 3.14 project managed by `uv`. `pokie/` contains only
a generated greeting package. The language exists as documents:

- `docs/terms-of-reference.md` defines goals G1–G5 and open questions Q1–Q8.
  Q3 asks whether fields are mutable and whether libraries can own structured
  input. Q5 asks whether the guard-binding and lifecycle-failure proposals meet
  expectations.
- `docs/context.md` defines the vocabulary and the evidence statuses
  (`Established`, `Agreed basis`, `Assumption`, `Proposed contract`,
  `Open question`, and `Deferred`).
- `docs/pokie-design.md` is the technical design. §2 records the AST-lowering
  choice. §3 covers program structure and lexical boundaries. §4 covers input,
  fields, state, lifecycle, and control transfer. §5 covers capture and
  structural-pattern semantics. §7 covers compilation boundaries. §9 is the
  failure and trust model. §10 is the verification strategy, and §11 the
  deferred scope.
- `docs/design-contracts.md` holds canonical structured contracts: the
  representative program (§1), the IR envelope (§2), the adapter protocol (§3),
  the command-line interface (CLI) and status table (§4, Table 2), and the
  pipeline diagram (§5).
- `docs/adrs/adr-0001-lower-pokie-through-python-asts.md` and
  `docs/adrs/adr-0002-preserve-one-program-scope-and-ordered-lifecycle.md` are
  both `Proposed`.
  `docs/adrs/adr-0003-resolve-adapters-through-an-explicit-registry.md` is out
  of scope, because roadmap task 4.1.1 owns it.
- `docs/execplans/1-1-1-establish-the-representative-job-corpus-and-decision-register.md`
  is the predecessor plan. Its "Corpus specification" lists eleven jobs, with
  observations OBS-01 to OBS-09. Its "Phase 1 verdict input" names OBS-01,
  OBS-02, and OBS-03 as this task's agenda. Its register routes OBS-06 and
  OBS-08 to Q5, and OBS-07 to Q3.

The executable harness is under `tests/job_corpus/`:

- `model.py` holds frozen values. `Failure` has `none`, `static`,
  `initialization`, `input`, `guard`, `adapter`, `action`, `end`, and
  `broken-pipe`. `ObservationKind` has `contradiction`, `ambiguity`,
  `ergonomic-smell`, and `host-divergence`. The module also defines `CorpusJob`,
  `JobCase` (`case_id`, `tags`, `operands`, `inputs`, `expected`, and
  `earliest_task`), `ScriptImplementation`, `Observation`, and `RegisterEntry`.
- `policy.py` and `register_policy.py` hold pure checks.
  - `derive_verdict` returns `revise-contracts` exactly when some
    observation has kind `contradiction`.
  - `find_undocumented_observations` requires every observation id to
    appear in `docs/job-corpus.md`.
  - `find_evidence_mismatches` requires each register row's corpus evidence
    to equal the jobs whose `decisions` name that question.
- `ports.py` defines `ProgramRunner.run(implementation, case)` and
  `EvidenceFormatError(message, path=..., key=...)`.
- `adapters/process_runner.py` defines `ProcessRunner`.
  - Its `_materialize` feeds standard input when a case has no operands or
    `("-",)`, and then requires exactly one input.
  - It refuses operands with no matching input.
  - It runs references as `sys.executable -I`, with only `PATH` and `LC_ALL`
    in the environment and a 10-second timeout.
  - Because `-I` implies `-P`, a probe script cannot import a sibling
    module.
- `adapters/toml_jobs.py` loads `job.toml` (schema 1; unknown keys are
  rejected at every level) using the private helpers in
  `adapters/toml_values.py`.
- `jobs/validate-user-records/` is the only job so far. It holds
  `job.toml`, `program.pokie` (proposed, not executable), `reference.py` (a
  Python model of the proposed semantics), and `alternative.awk`.
- Tests:
  - `tests/test_job_corpus_*.py`;
  - the feature file `tests/features/job_corpus.feature`, with steps in
    `tests/test_job_corpus_scenarios.py`;
  - the properties in `tests/test_job_corpus_properties.py`;
  - the domain-purity test `tests/test_job_corpus_boundaries.py`.
- `tests/conftest.py` registers Hypothesis profiles: no deadline by default,
  and `derandomize` under `CI`.

Tooling comes from `Makefile` and `pyproject.toml`.

- `make all` runs
  `build check-fmt lint typecheck test markdownlint nixie audit validate test-workflow-contracts`.
- `make lint` runs Interrogate at 100% docstring coverage (nested functions
  included), Ruff, Pylint on PyPy 3.12, the DF12 lints, ambrleaks, Skylos with
  Vulture (`dead-code`), `nose` duplication, and actionlint with yamllint.
- `make test` runs `pytest -v -n auto` with `pythonpath = ["tests"]`, a
  30-second per-test timeout, and
  `empty_parameter_set_mark = "fail_at_collect"`.
- The coverage ratchet baseline in `.coverage-baseline-v2.python` is 98.04.

The agents named in this plan are local helpers. `scrutineer` runs the
repository's gates sequentially and reports the results. Wyvern is a read-only
reconnaissance agent. Firecrawl is the web-research tool. Leta is a
language-server code navigator. None of them is required: every step can be run
by hand with the commands given.

Budget calibration. The 1.1.1 plan started with 45 files and 4,800 net Python
lines outside job directories. The owner raised the file limit to 92, but the
line cap held. The work reached the cap several times and was compacted each
time, once from 4,859 lines down to 4,792. One loader there came to about 850
lines (`toml_jobs` 378, `toml_values` 335, `toml_source` 137). `model.py` is
346 lines, and test modules run from 279 to 381 lines.

This plan reuses that loader stack, which is why it estimates fewer lines:

| Part                                                                          | Estimate (lines) |
| ----------------------------------------------------------------------------- | ---------------- |
| Register domain: `model.py`, `policy.py`, `render.py`, `ports.py`             | 550              |
| Models: `control_model.py`, `records_model.py`                                | 220              |
| Host and rejected-alternative adapters (control, binding, records, lifecycle) | 600              |
| Register loader, probe runner adapter, and document trace adapter             | 350              |
| Probe scripts, sharing code through arguments                                 | 150              |
| Tests, scenario steps, and whitelist entries                                  | 900              |

*Table 1: Bottom-up code estimate for this plan.*

The total is about 2,770 lines, so the code limit of 3,200 includes about 15%
contingency.

Three corpus jobs come to about 290 lines each. The documentation estimate
covers:

- ADR 0002, restructured and accepted, about 160 lines;
- ADR 0005, new, about 180 lines;
- design amendments, about 450 lines;
- contract amendments and the decision index, about 150 lines;
- context, terms of reference, register, findings, developers' guide,
  users' guide, layout, and contents, about 250 lines.

That totals about 1,190 lines, so the documentation limit is 1,400.

## Conformance basis

Upstream artefacts, at `main` commit `7311a47`:

- Terms of reference, draft v0.1 (2026-10-09): G1–G5, Q3, Q5, and the §6.2
  non-goals. Identifiers: `TOR-G1`–`TOR-G5`, `TOR-Q3`, and `TOR-Q5`.
- Technical design, proposed v0.1 (2026-10-10): §§2–5, 7, 9, 10, and 11.
  Identifiers: `DES-2`, `DES-3.1`, `DES-3.2`, `DES-4.1`, `DES-4.2`, `DES-4.3`,
  `DES-5`, `DES-7`, `DES-9`, `DES-10`, and `DES-11`.
- Design contracts, proposed v0.1 (2026-10-10): `DC-1`, `DC-2`, and `DC-4`.
- `ADR-0001` (Proposed, 2026-10-09) and `ADR-0002` (Proposed, 2026-10-09).
- The 1.1.1 ExecPlan (Status APPROVED) and, once present,
  `docs/job-corpus.md` and `docs/decision-register.md`. Identifiers: OBS-01,
  OBS-02, OBS-03, OBS-06, OBS-07, and OBS-08, and register rows Q3 and Q5.
- Roadmap task `RM-1.1.2`. Downstream tasks that consume decisions:
  `RM-1.2.1`, `RM-1.2.2`, `RM-2.1.1`, `RM-2.1.2`, `RM-2.1.3`, `RM-2.2.1`,
  `RM-2.2.2`, `RM-2.2.3`, `RM-3.1.1`, `RM-3.1.2`, `RM-3.2.1`, `RM-4.1.1`,
  `RM-5.1.1`, and `RM-6.1.1`.
- Governing standards: `AGENTS.md`, `docs/documentation-style-guide.md`,
  `docs/developers-guide.md`, `docs/scripting-standards.md`, and
  `docs/complexity-antipatterns-and-refactoring-strategies.md`.

Trace chains (upstream, then decision area, then milestone, then acceptance
evidence):

- `TOR-Q5, DES-4.2, ADR-0002 → SCOPE-* → EP-M2, EP-M5 →
  test_registered_main_module_pickles, test_contract_index_matches_register`
- `TOR-Q3, DES-4.1 → INPUT-* → EP-M2, EP-M3, EP-M5 →
  test_record_splitting_matches_model, aggregate-csv-by-header cases`
- `TOR-G5, DES-4.3, ADR-0002 → CONTROL-* → EP-M2, EP-M3 →
  test_signal_unwinding_matches_model, filter-complete-rows cases`
- `TOR-G2, DES-5, DC-1, OBS-08 → BIND-* → EP-M2, EP-M3 →
  test_binding_transaction_preserves_prior_state, aggregate-port-changes cases`
- `TOR-G5, DES-4.2, DC-4 → FINAL-* → EP-M2 →
  test_lifecycle_outcomes_match_table`
- `OBS-03, DES-3.2 → LEX-1 → RM-1.2.1` (deferred; no 1.1.2 evidence)
- `RM-1.1.2 success → all areas → EP-M4, EP-M5 →` the
  `test_repository_register_is_ratified` test and the scenario "Every contract
  area is ratified"

## Ratification agenda

This is the proposal that EP-M4 puts to the owner. Each decision has a stable
identifier, a recommended rule, a recommended disposition, the counterexamples
behind it, and the tasks that will implement it (`impl:`). The dispositions are:

- `ratified`: the proposal stands as written;
- `amended`: the proposal changes or gains a rule;
- `deferred`: the question goes to a named later task.

"Static error" means a compile-time diagnostic with status 2, before any user
code runs. Where reviewers disagreed, the alternatives are listed as owner
options.

### Scope

- SCOPE-1 (amended; CX-01, CX-26). The program namespace is a module object
  with `__name__ == "__main__"`, `__spec__ = None`, `__loader__ = None`, and
  `__builtins__` set to the `builtins` module. In a command-line run it is
  installed as `sys.modules["__main__"]` and stays installed until the process
  exits, because the program owns the process and `atexit` handlers may still
  pickle program classes. Preamble, `start:`, rules, guards, and `end:` all use
  its dictionary as globals.
  - Known limitation: `multiprocessing` and `ProcessPoolExecutor` with the
    `spawn` or `forkserver` start methods cannot import a pokie `__main__`.
    Programs must use `get_context("fork")`, or define picklable callables in
    an importable module.
  - Owner option: whether `__file__` is set to a file program's path. The
    recommendation is no `__file__`, so that spawn workers fail fast instead
    of re-running pokie source as Python.
  - The original proposal ("one dedicated module-like globals dictionary")
    broke `pickle`.
  - impl: 2.1.2.
- SCOPE-2 (amended; CX-02). A program is one compilation unit.
  `from __future__` imports may appear only at the start of the preamble, and
  apply to every section. Elsewhere they are a static error. The
  compiler-generated record loop and its `next`/`exit` handlers are part of
  that unit. The host driver only runs and wraps the unit. impl: 2.1.2.
- SCOPE-3 (ratified, clarified). The preamble is any Python suite, including
  expression statements and loops. It runs once, after the whole program passes
  static validation and before `start:`. A top-level statement after the first
  lifecycle block or rule is a static error. impl: 2.1.1.
- SCOPE-4 (amended; CX-03). At section level (outside `def`, `lambda`, and
  `class` bodies), statements that are invalid at module level (`return`,
  `yield`, `await`, `async for`, `async with`, and `nonlocal`) are static
  errors, reported at the pokie span. `global` is permitted, and refers to the
  program namespace. impl: 2.1.1.
- SCOPE-5 (amended; CX-04). These names are reserved: the `__pokie_` prefix,
  `NR`, `NF`, `FNR`, `FILENAME`, `FIELDS`, `MATCH`, `next`, `exit`, and `quit`.
  `FS` is also reserved, except as an assignment target in the preamble or
  `start:`.
  - A reserved name may not be the target of an assignment, augmented
    assignment, `del`, `for`, a `with` or `except` alias, `import M as
    NAME`, `from M import NAME`, `global`, `def`, `class`, `type`, or a
    capture pattern.
  - `FNR`, `FILENAME`, and `FIELDS` are reserved now, even if the owner
    defers exposing them, because reserving them after release would break
    programs.
  - Residuals: access through `globals()`, and `from m import *`.
    Reservation is hygiene, not isolation (design §7).
  - impl: 2.1.1.
- SCOPE-6 (ratified). Definitions inside rule actions are allowed and run
  again for each record. A class redefined for each record fails `pickle`'s
  identity check for instances made in earlier records. This is a documented
  consequence. impl: none.
- SCOPE-7 (amended; new). `sys.argv` is `[PROGRAM, *operands]`, where
  `PROGRAM` is the program file path, or `-c` for an inline program, as in
  Python.
  - Owner option for `sys.path[0]`: the recommendation is the program file's
    directory, or the current directory for inline programs, as in Python.
    The alternative is to leave `sys.path` unchanged, so a program cannot
    import its sibling helpers.
  - Passing parameters such as awk's `-v NAME=VALUE` goes to 2.2.2. Until
    then, `os.environ` is the documented recipe.
  - impl: 2.2.2.

### Input ownership

- INPUT-1 (ratified; Q3 for v1; OBS-07). One driver-owned reader consumes
  the input operands. Fields, `$0`, `NF`, `NR`, `FNR`, `FILENAME`, and `FIELDS`
  are read-only. Mutable fields, quoted CSV, and library-owned structured input
  (including `getline`-style look-ahead) are deferred to 6.1.1. Writing to
  several output files stays a Python recipe (`contextlib.ExitStack`). impl:
  2.1.3.
- INPUT-2 (amended; CX-05, OBS-01). After decoding, records are split on
  U+000A only. A `\r` immediately before U+000A, or at the end of an
  unterminated final record, is removed. A lone `\r`, `\v`, `\f`, `\x1c` to
  `\x1e`, U+0085, U+2028, or U+2029 is record content. A final unterminated
  line is a record, and an empty operand has none. Records never span operands.
  impl: 2.1.3.
- INPUT-3 (amended; CX-06, CX-29, OBS-02). Each operand is decoded with a
  stateful incremental decoder in strict mode.
  - When a decode error occurs, every complete record before the error
    offset is delivered first, with its effects and output kept.
  - The failure names the operand, the line number within the operand, and
    the global `NR + 1`. The diagnostic suggests `--encoding`.
  - `utf-8` keeps a BOM as content, and `utf-8-sig` strips one per operand.
  - A lenient error mode goes to 2.2.2.
  - This matches the 1.1.1 `filter-error-lines/invalid-utf8` expectation
    (`ok ERROR one` is printed).
  - impl: 2.1.3 and 2.2.2.
- INPUT-4 (ratified, clarified; CX-07). Operands are opened lazily, in order,
  when the previous operand is exhausted. A missing or unreadable operand is an
  input failure when it is reached, after earlier output, with no `end:`. This
  matches GNU Awk except for the status (1, not 2).
  - Owner option: the user-advocacy reviewer recommends also checking, with
    `stat` and without opening, that every operand exists before the
    preamble runs. A missing operand would then be a usage error (status 2),
    so a typo in the fiftieth operand is not found only after forty-nine
    files. The residual is a race between that check and the later open.
  - impl: 2.2.2.
- INPUT-5 (amended; CX-08, CX-23). This reverses design §4.1's explicit "No
  special `stdin` object is injected" and its note that direct reads are
  "outside this contract".
  - Scope: the rule applies when standard input is an input source (no
    operands, or `-`) and the program reads input (INPUT-6).
  - File descriptor: the reader takes a private duplicate of file
    descriptor 0, and points descriptor 0 at the null device for the rest of
    the run, `end:` included. Child processes, `open(0)`, and C extensions
    therefore see end-of-file instead of silently consuming records.
  - `sys.stdin` guard: `sys.stdin` is replaced by a guard whose read methods
    (`read`, `readline`, `readlines`, iteration, and `buffer` reads) raise an
    input-ownership failure.
    - `isatty()` returns `False`, and `encoding` is kept.
    - `fileno()` raises `io.UnsupportedOperation`, so `input()` cannot
      bypass the guard.
    - `close()` does nothing.
  - Residuals: `sys.__stdin__`, `breakpoint()`, and `pdb` see the guard or
    end-of-file. Descriptor-level ownership is POSIX-only; other platforms
    are decided under Q2.
  - When standard input is not an input source, both `sys.stdin` and
    descriptor 0 are untouched, so a program may read configuration from
    them.
  - Options considered: a `sys.stdin` guard alone (misses child processes);
    descriptor redirection with the guard (recommended); and leaving the
    behaviour unspecified (silent data loss).
  - impl: 2.1.3 and 2.2.2.
- INPUT-6 (amended; CX-09). A program with no rules and no `end:` block
  reads no input. Operands given to such a program are a usage error (status 2:
  "program reads no input"). awk silently ignores them. impl: 2.2.2.
- INPUT-7 (amended; CX-10, CX-31). `FS` may be assigned in the preamble or
  `start:`, and is frozen before the first operand opens.
  - `-F` is a usage argument. It processes the escapes `\t` and `\\`. An
    empty separator, or a separator longer than one character that contains
    a regex metacharacter, is a usage error (status 2) with a hint that
    separators are literal.
  - An invalid `FS` at the end of initialization is an initialization
    failure (status 1).
  - The default `FS = " "` splits on Python's `str.split()` whitespace, which
    includes `\x1c`–`\x1f`, `\v`, U+0085, and U+00A0. Unlike awk, which
    splits on space, tab, and newline, so this is documented.
  - With a literal `FS`, an empty record has `NF == 0`, as in awk, not the
    one empty field that `"".split(",")` gives.
  - impl: 2.1.3 and 2.2.2.
- INPUT-8 (ratified, clarified; CX-11). `NR` is readable everywhere: 0 in the
  preamble and `start:`, and the total of delivered records in `end:`. `$0`,
  `$n`, `NF`, `FNR`, `FILENAME`, `FIELDS`, and `MATCH` are record-scoped, and
  are valid only in rule predicates, guards, and actions. Elsewhere they are a
  static error. Unlike awk, `end:` has no last record; programs keep it in a
  variable. impl: 2.1.1 and 2.1.3.
- INPUT-9 (ratified, clarified). Pokie `exit` stops reading, and closes every
  driver-owned operand before `end:` runs. impl: 2.2.1.
- INPUT-10 (amended; new; CX-28, CX-31). Field access beyond a literal `$n`:
  - `FIELDS` is a read-only tuple of the current record's fields, so
    `FIELDS[-1]` is awk's `$NF` and `FIELDS[i - 1]` is `$i`.
  - `FNR` (the record number within the current operand) and `FILENAME`
    (the operand name, or `-`) are exposed read-only.
  - Owner option: defer exposing all three to 2.1.3, keeping them reserved
    under SCOPE-5. The corpus job `aggregate-csv-by-header` then documents
    the `NR == 1` header hazard across two files as an open
    ergonomic-smell.
  - `$(expr)` syntax is not adopted.
  - impl: 1.2.1 and 2.1.3.

### Control transfer

- CONTROL-1 (amended; CX-12). `next` and `exit` are pokie statements, never
  calls. They are valid only as a whole simple statement in a rule action.
  - Recommended (stricter) rule: any call whose callee is the bare name
    `exit` or `quit` is a static error, whatever the name is bound to. With
    SCOPE-5, binding `next`, `exit`, or `quit` is also a static error. The
    diagnostic suggests pokie `exit` or `sys.exit(status)`. This keeps
    reviewers from having to tell `exit` (which runs `end:`) from `exit(1)`
    (which does not) by parentheses alone.
  - Owner option (looser): only a call to an unbound `exit` or `quit` (the
    `site` builtin) is an error, so `from sys import exit; exit(1)` stays
    legal.
  - `next(iterator)` keeps its Python meaning.
  - impl: 1.2.1 (keyword placement fixtures) and 2.1.1.
- CONTROL-2 (ratified; INV-CTL-1; CX-25). The lowering raises
  compiler-owned signals that derive from `BaseException` and not from
  `Exception`. Only the compiler-generated handlers in the same compilation
  unit catch them. Every enclosing `finally` runs exactly once, innermost
  first, and every enclosing context manager's `__exit__` runs.
  - Known risk: `__exit__` receives the private signal type, so transaction
    managers (for example a `sqlite3` connection used with `with`) roll back
    on `next` or `exit`. Commit explicitly before `next`.
  - impl: 2.2.1.
- CONTROL-3 (amended; CX-13, CX-14, CX-27). Suppression is detected at
  runtime and linted statically.
  - Runtime: the lowering records a pending signal before raising it, and
    clears the record when a generated handler receives it. If an action
    finishes, normally or by another exception, while a signal is still
    pending, that is an action failure (status 1). The diagnostic names the
    suppressing construct where it can.
  - Static lint: within a rule action, any `try` statement whose body,
    handlers, or `else` clause lexically contain `next` or `exit` is a static
    error if:
    - it has a bare `except:`;
    - it has a handler or `except*` clause naming the builtin
      `BaseException`, alone or in a tuple, unless that handler's last
      statement is a bare `raise`; or
    - its `finally` contains a `break` or `continue` that would leave the
      `finally` block (PEP 765).
  - The lint is conservative and not complete, because aliasing, shadowing,
    computed handler types, and suppressing context managers defeat it. The
    runtime check covers those.
  - impl: 2.1.1 (lint) and 2.2.1 (runtime check).
- CONTROL-4 (ratified, clarified; CX-15). `next` and `exit` are static errors
  in the preamble, `start:`, `end:`, and nested `def`, `lambda`, or `class`
  bodies.
  - Unlike awk, `exit` in `start:` is rejected. The diagnostic suggests
    `sys.exit(status)`, or omitting rules and `end:` (INPUT-6).
  - The documented recipe for awk's `exit n` is to set a variable, use
    `exit`, then call `sys.exit(variable)` in `end:`.
  - `exit STATUS` becomes a deferred candidate in design §11.
  - impl: 2.1.1.
- CONTROL-5 (ratified; CX-16). `break` and `continue` in an action are valid
  only inside a user-written loop, and are otherwise static errors, because the
  generated record loop would make them legal Python. impl: 2.1.1.
- CONTROL-6 (amended). An `Exception` raised while a signal unwinds (for
  example from a `finally`) replaces the signal and is an action failure.
  Diagnostics hide the private signal from the displayed exception context.
  `SystemExit` and `KeyboardInterrupt` keep host semantics (FINAL-4). impl:
  2.2.1 and 2.2.2.

### Binding visibility

- BIND-1 (ratified; CX-17, OBS-08). Candidate bindings stay private until
  the pattern and guard both succeed. The first accepted case commits all its
  names to the program namespace at once, and rejected attempts leave it
  unchanged. The lowering must not let Python's native `match` bind program
  names directly. impl: 2.1.2, 3.1.2, and 3.2.1.
- BIND-2 (ratified, clarified; CX-18). A guard evaluates with the candidates
  as local parameters and the program namespace as globals. A function the
  guard calls sees committed program state, not the candidates. impl: 3.2.1.
- BIND-3 (ratified, clarified). An assignment expression (`:=`) anywhere in a
  guard, including nested comprehensions and lambdas, is a static error. The
  diagnostic suggests an adapter, or computing the value in the action. impl:
  3.2.1.
- BIND-4 (amended). Guards may read the current record's record-scoped
  names (INPUT-8), including `MATCH` in regex rules. impl: 3.2.1.
- BIND-5 (amended; CX-19, CX-30). Inside generator expressions and lambdas,
  record-scoped names denote the record that was current when the expression
  was created. The lowering captures it, through an eagerly evaluated generated
  scope or default value.
  - `def` and `class` bodies, annotations (function, variable, and return),
    `type` aliases, and type-parameter scopes are lazily evaluated nested
    scopes. Record-scoped names in them are static errors.
  - Eagerly evaluated positions (a generator's outermost iterable, default
    values, decorators, and class bases) may read record-scoped names.
  - List, set, and dictionary comprehensions are allowed.
  - Owner option: the simpler rule, a static error in generator expressions
    and lambdas as well. It costs the common idiom
    `when any(k in $0 for k in KEYWORDS):`.
  - impl: 2.1.2.
- BIND-6 (ratified, clarified). `MATCH` exists only within a regex rule (its
  guards and its action), and is a static error in expression rules. The
  runtime unbinds it when the rule finishes. impl: 3.1.1.
- BIND-7 (ratified; CX-20). Accepted bindings persist until rebound, as Python
  loop variables do. A name bound only by an earlier record's case keeps its
  value. A static warning, when a case body reads a capture name that only a
  sibling case binds, goes to 3.2.1. impl: 3.2.1.

### Finalization

- FINAL-1 (ratified, clarified). Initialization means running the preamble,
  running `start:`, and validating `FS`. `end:` runs exactly once after
  end-of-file (EOF) or pokie `exit`, if and only if initialization succeeded,
  including on empty input. impl: 2.2.1.
- FINAL-2 (amended; CX-24). Any initialization, input, predicate, guard,
  adapter, action, suppression (CONTROL-3), or unwinding failure skips `end:`,
  and gives status 1. Output already written is kept.
  - The driver flushes standard output before writing the diagnostic to
    standard error.
  - The diagnostic names:
    - the pokie span and section;
    - for record-phase failures, the operand and its line number, and `NR`;
    - and states that `end:` was not run.
  - After `end:`, the driver flushes standard output. A flush failure is an
    output failure (status 1), except for a broken pipe (FINAL-6).
  - impl: 2.2.2.
- FINAL-3 (ratified). A failure in `end:` gives status 1 and is not retried.
  impl: 2.2.1.
- FINAL-4 (ratified, clarified; CX-21). `SystemExit` and `KeyboardInterrupt`
  keep host semantics in every section.
  - `sys.exit(n)` from a rule ends the run with status `n`, without `end:`.
  - `sys.exit(n)` as the last statement of `end:` is the supported way to
    report a status after printing a summary.
  - An uncaught `KeyboardInterrupt` terminates the process by `SIGINT`
    (shell status 130). The driver never turns it into status 1.
  - Suppressing the traceback goes to 2.2.2.
  - impl: 2.2.2.
- FINAL-5 (ratified, clarified; CX-22). No hook spans the lifecycle. A
  resource opened in `start:` is closed by `end:` on success. After a failure,
  it is left to interpreter finalization, or to the program's own
  `contextlib.ExitStack` or `atexit` use. A lifecycle-spanning `finally:` block
  becomes a deferred candidate in design §11. impl: none.
- FINAL-6 (amended; CX-24). Broken pipes on standard output use the default
  `SIGPIPE` disposition (POSIX). The process ends as awk's does, without
  writing anything to standard error, and `end:` does not run if it had not
  finished. This amends `docs/design-contracts.md` Table 2. The exact shell
  status (141 by signal, against the table's 1) is decided by 2.2.2 with the
  CLI; other platforms are decided under Q2. impl: 2.2.2 and 2.2.3.

### Routed corpus observations

- LEX-1 (deferred to 1.2.1; OBS-03). For `$9.isascii()`, the recommended
  scanner rule reads `$` followed by the longest run of ASCII digits, and a
  following `.` begins attribute access.
- OBS-06 (`unit=` with an empty capture) is routed to Q6 (task 4.1.x). It
  concerns adapter catalogue strictness, not the five areas.
- OBS-07 (literal separator and quoted CSV) is dispositioned by INPUT-1:
  quoted CSV is deferred to 6.1.1.
- Interleaving with child-process output: Python does not flush before a
  child writes, while gawk's `system()` does. This keeps Python semantics, and
  documents `print(..., flush=True)` in 2.2.3.

## Counterexample catalogue

Each counterexample has an identifier, the decision it informs, its effect
(`upholds`, `clarifies`, `amends`, or `falsifies`), and its evidence. Evidence
references use five kinds:

- `probe:` names a subprocess probe declared in the register;
- `test:` names an in-process test by its pytest node id;
- `case:` names a corpus case;
- `obs:` names a corpus observation;
- `cite:` names a document anchor or footnote. Only `upholds` and
  `clarifies` counterexamples may rely on `cite:` alone.

- CX-01 (SCOPE-1, amends): a program-defined `@dataclass` cannot be pickled
  from a plain-dictionary namespace. Evidence: `probe:PRB-SCOPE-MODULE`
  (witness) and `probe:PRB-SCOPE-DICT` (control).
- CX-02 (SCOPE-2, amends): separately executed units overwrite
  `__annotate__`, so the preamble's annotations are lost. Evidence:
  `test:tests/test_contract_scope.py::test_one_unit_keeps_all_annotations`
  (witness) and `::test_two_units_lose_preamble_annotations` (control).
- CX-03 (SCOPE-4, amends): an action containing `return` is a Python
  `SyntaxError` at module level, but would silently leave a generated driver
  function. Evidence: `test:...::test_module_level_rejects_function_statements`.
- CX-04 (SCOPE-5, amends): a preamble `NR = 5` executes, so reservation must
  be static. Evidence: `test:...::test_driver_names_are_writable_globals`.
- CX-05 (INPUT-2, amends): `a\rb\n` gives two records under universal
  newlines but one under awk. Evidence: `test:` the INV-IN-1 controls.
- CX-06 (INPUT-3, amends): a text-mode loop decodes in chunks, so an invalid
  byte on line 2 fails before line 1 is processed. Evidence: LEM-IN-2 tests;
  `case:filter-error-lines/invalid-utf8`.
- CX-07 (INPUT-4, upholds): GNU Awk 5.3.0 prints earlier records, then fails
  fatally on a missing later operand, without `END`, with status 2. Evidence:
  `cite:` research note (gawk run, 2026-11-14).
- CX-08 (INPUT-5, amends): a `sys.stdin.readline()` in `start:` steals the
  whole buffer from a binary reader (zero records remain). Evidence:
  `probe:PRB-INPUT-STDIN-GUARD` (witness) and `probe:PRB-INPUT-STDIN-RACE`
  (control).
- CX-09 (INPUT-6, amends): `pokie 'print("hi")'` would wait for a terminal
  end-of-file. Evidence: `cite:` POSIX awk BEGIN-only rule.
- CX-10 (INPUT-7, clarifies): `-F ''` is a usage error in `DC-4` but an
  initialization failure in `DES-4.1`. Evidence: `cite:` both sections.
- CX-11 (INPUT-8, upholds): awk keeps `$0` and `NF` in `END`; pokie does
  not. Evidence: `cite:` POSIX awk.
- CX-12 (CONTROL-1, amends): an action that calls `exit()` raises
  `SystemExit`, so `end:` silently does not run. Evidence:
  `probe:PRB-CTL-BUILTIN-EXIT`.
- CX-13 (CONTROL-3, amends): a bare `except:`, `except BaseException`,
  `except (ValueError, BaseException)`, `except* BaseException`, and
  `contextlib.suppress(BaseException)` each swallow the signal.
  `except Exception`, `except* Exception`, and a non-suppressing `with` do not.
  Evidence: `test:...::test_swallowing_constructs`, parameterized from
  `tests/data/swallow_constructs.json`.
- CX-14 (CONTROL-3, amends): `finally: break` swallows the signal, with one
  `SyntaxWarning`, including when the signal is raised from an `except` or
  `else` clause. A `break` inside a loop within `finally` does not. Evidence:
  the same test.
- CX-15 (CONTROL-4, upholds): awk allows `exit` in BEGIN; pokie rejects it.
  Evidence: `cite:` POSIX awk.
- CX-16 (CONTROL-5, upholds): a bare `break` in an action, lowered inside the
  generated record loop, stops all input. Evidence:
  `test:...::test_bare_break_leaves_generated_record_loop`.
- CX-17 (BIND-1, upholds): native `match` with a false guard leaves its
  candidates bound. Evidence: the INV-BIND-1 control; `obs:OBS-08`;
  `case:validate-last-good-uid/rejections-keep-last-good`.
- CX-18 (BIND-2, clarifies): a helper called from a guard reads the
  committed value. Evidence: `test:...::test_guard_helper_sees_committed_state`;
  `case:aggregate-port-changes/consecutive-ports`.
- CX-19 (BIND-5, amends): a stored generator expression reading a record
  global yields a later record. Evidence: `test:` the BIND-5 control.
- CX-20 (BIND-7, upholds): `port` keeps its value across a rejected record.
  Evidence: `case:aggregate-port-changes/consecutive-ports`.
- CX-21 (FINAL-4, clarifies): `sys.exit(0)` in a rule gives status 0 with no
  `end:` output. Evidence: `probe:PRB-FINAL-EXIT-STATUS`.
- CX-22 (FINAL-5, clarifies): a `with open(...)` in `start:` closes before the
  first record. Evidence: `cite:` design §3.1.
- CX-23 (INPUT-5, amends): a child process inherits descriptor 0 and
  consumes records. Evidence: `probe:PRB-INPUT-CHILD-INHERIT` (control) and
  `probe:PRB-INPUT-CHILD-NULL` (witness).
- CX-24 (FINAL-2, FINAL-6, amends): with `print` inside `except Exception`,
  piping to `head -1` keeps the program running, then exits with status 120.
  Restoring `SIGPIPE` ends it at once. Evidence:
  `probe:PRB-FINAL-SIGPIPE-DEFAULT` (witness) and
  `probe:PRB-FINAL-SIGPIPE-IGNORED` (control).
- CX-25 (CONTROL-2, clarifies): `next` inside `with sqlite3_connection:` rolls
  back the transaction. Evidence: `test:...::test_context_manager_sees_signal`.
- CX-26 (SCOPE-1, clarifies): a `forkserver` pool cannot import a pokie
  `__main__`, while `fork` can. Evidence: `probe:PRB-SCOPE-MP-FORK` (witness)
  and `cite:` the reviewer experiment for `forkserver`. A hanging probe would
  breach the runtime tolerance, so it is not executed.
- CX-27 (CONTROL-3, amends): aliases, shadowing, and computed handler types
  defeat any static rule. Evidence: `test:...::test_pending_signal_check`,
  parameterized from the same JSON table. With the runtime check, every
  construct gives a suppression failure. Without it, every construct swallows
  the signal (control).
- CX-28 (INPUT-10, amends): with two CSV operands, each with a header,
  `NR == 1` counts the second header as data (`team 1`). Evidence:
  `case:aggregate-csv-by-header/two-files`.
- CX-29 (INPUT-3, amends): decoding each record separately fails for UTF-16,
  and keeps a UTF-8 BOM as content. Evidence: the LEM-IN-2 tests.
- CX-30 (BIND-5, amends): annotations and `type` aliases created during
  record `a` read record `b`. Evidence:
  `test:...::test_lazy_scopes_read_later_record`.
- CX-31 (INPUT-7, INPUT-10, clarifies): `"a\x1cb".split()` and
  `"a\xa0b".split()` give two fields where gawk gives one, and `"".split(",")`
  gives one field where awk gives none. Evidence:
  `test:...::test_field_split_edges`.

## Verification plan

The verification target is the ratification itself. The domain code checks that
the register is complete and coherent. The host evidence checks two things:
that each ratified rule is feasible on CPython 3.14, and that each rejected
alternative really fails. Python's own semantics are axioms. This plan does not
verify CPython, and does not verify the future compiler.

### Axioms

- AXIOM-1: CPython 3.14.x behaves as the Python 3.14 language and library
  references document for `try`/`finally`, `match`, `with`, `exec`, `compile`,
  `pickle`, `io`, `codecs`, `signal`, and `multiprocessing`. Every in-process
  test and subprocess probe exercises it.
- AXIOM-2: `BaseException` subclasses that are not `Exception` subclasses
  pass through `except Exception:` handlers. INV-CTL-1 exercises this.
- AXIOM-3: CPython 3.14 emits `SyntaxWarning` for `break`, `continue`, or
  `return` that exits a `finally` block (PEP 765, Final). The CX-14 test
  exercises this.
- AXIOM-4: the POSIX awk specification (Open Group Base Specifications,
  Issue 8) defines `exit` in BEGIN, leaves `next` in BEGIN/END undefined, and
  keeps `$0`, `NF`, and `NR` available in END. This is cited prior art, not
  executed.
- AXIOM-5: `ProcessRunner` behaves as `docs/developers-guide.md` "Corpus
  harness" documents. Its own tests exercise that boundary.
- AXIOM-6: descriptor-level stdin ownership and the `SIGPIPE` disposition
  rely on POSIX (Linux on CI). Probes that need them are skipped with a stated
  reason on non-POSIX platforms, and the skip is recorded as a Q2 input.

### Ports

`tests/contract_ratification/ports.py` declares the interfaces that pure models
and host adapters both implement. A control is a further adapter of the same
port that embodies a rejected alternative, so vacuity is checked structurally.
Each port lists its chosen adapter first, then its rejected-alternative
adapters:

- `UnwindSemantics.trace(shape, records) -> Trace`:
  - `control_model.UnwindModel`;
  - `host_control.BaseExceptionSignals` (chosen);
  - `host_control.ExceptionSignals` (rejected);
  - `host_control.ContinueLowering` (rejected).
- `BindingSemantics.namespace_after(prior, subject, cases) -> Namespace`:
  - `host_binding.CommitAfterGuard` (chosen);
  - `host_binding.NativeMatch` (rejected);
  - `host_binding.TentativeCommit` (rejected).
- `RecordSource.records(data, encoding) -> Records`:
  - `records_model.RecordModel`;
  - `host_reader.IncrementalReader` (chosen);
  - `host_reader.UniversalNewlines` (rejected);
  - `host_reader.SplitLines` (rejected);
  - `host_reader.PerRecordDecode` (rejected).
- `LifecycleDriver.outcome(script) -> LifecycleOutcome`:
  - `host_lifecycle.OrderedDriver` (chosen);
  - `host_lifecycle.EndInFinally` (rejected).
- `ProbeRunner.run(probe) -> ObservedOutcome`:
  - `adapters.probe_runner.CorpusProbeRunner`. It converts a `Probe` into a
    `ScriptImplementation` and a `JobCase` with no operands and exactly one
    input (the probe's standard input, possibly empty), then calls
    `ProcessRunner`.

### Invariants and lemmas

- INV-REG-1 (register completeness).
  - Rule:
    - each of the five areas has at least one decision;
    - decision ids are unique and match `AREA-n`;
    - every `amended` decision cites at least one counterexample;
    - every counterexample is cited by a decision and has an effect;
    - a `cite:`-only counterexample has effect `upholds` or `clarifies`;
    - every witness probe has a control probe with a different expected
      outcome;
    - every evidence reference resolves (a `probe:` id in the register, a
      `case:` or `obs:` id in the loaded corpus, a `test:` node id found by
      an AST scan of `tests/test_contract_*.py`, or a `cite:` target found in
      the cited document);
    - every `discharged_by` entry is a task id in `docs/roadmap.md`.
  - Method: a seeded-defect table, `tests/data/register_defects.json`. Each
    row is one mutation of the fixture register
    `tests/data/ratified_register.toml`, which audits as `ratified` against
    a stub evidence index, together with the single expected finding.
  - Artefacts: `policy.py` and `tests/test_contract_ratification_policy.py`.
  - Discharge: the clean row has no findings, and each defect row yields
    exactly one finding, naming its subject.
  - Non-vacuity: the table has one row per defect kind; every finding kind
    in `policy.py` appears in at least one row (asserted); and the seeded
    defects are independent, so "exactly one" is meaningful.
  - Limit: a `test:` reference proves only that the test exists. The test
    suite itself proves that it passes.
- INV-REG-2 (verdict precedence): the verdict is the first of
  `revise-contracts`, `revise-evidence`, `pending-owner`, and `ratified` whose
  condition holds (see `Decision log`). Method: a parameterized truth table
  over the four conditions, 16 rows. Non-vacuity: for each condition, a row
  exists where that condition alone changes the verdict.
- INV-DOC-1 (document trace): every decision id appears in at least one of
  its `documents`. The index between `<!-- ratified-contracts:start -->` and
  `<!-- ratified-contracts:end -->` in `docs/design-contracts.md` equals
  `render_decision_index(register)` after cell normalization. Method: an
  example test, plus a syrupy snapshot of `render_decision_index` applied to a
  fixture register that contains a `|`, backticks, a long cell, and both
  `CONTROL-2` and `CONTROL-10` (numeric ordering). Non-vacuity: the red step
  deletes one index row from a copy of the document, and changes one
  disposition, and observes both failures.
- INV-CTL-1 (signal unwinding within one action: CONTROL-2, CONTROL-5, and
  CONTROL-6).
  - Rule: for every action shape, `BaseExceptionSignals.trace` equals
    `UnwindModel.trace`. A shape is a tree value with at most four levels of
    `for`, `while`, `try`/`finally`, `try`/`except Exception`,
    non-suppressing `with`, and `if NR == k`. It contains one `next`,
    `exit`, user `break`, or user `continue` at a generated position, and is
    followed in the program by a second traced rule.
  - Model: `next` runs every enclosing `finally` and `__exit__` exactly
    once, innermost first, skips the second rule for that record, and
    continues with the next record. `exit` does the same, then delivers no
    further records. User `break` and `continue` affect only the innermost
    user loop.
  - Renderer rules:
    - `while` loops increment their counter first;
    - no jump is placed directly in a `finally` block;
    - jump positions inside `except` handlers are generated only when the
      shape raises.
  - Driver boundary: the adapter catches the signal classes and records any
    escape as an `("escaped", type_name)` trace entry, so differences shrink.
  - Method: Hypothesis, with records drawn from 0 to 3, differential.
  - Artefacts: `control_model.py`, `adapters/host_control.py`, and
    `tests/test_contract_control.py::test_signal_unwinding_matches_model`.
  - Non-vacuity:
    - explicit `@example`s cover each statement kind at depth 1 and depth 3,
      and `exit` on the first and last record;
    - control `test_exception_signals_are_caught_by_user_handler` reruns the
      property against `ExceptionSignals` inside
      `pytest.raises(AssertionError)`, and asserts that the shrunk shape
      contains `try_except_exception`;
    - control `test_continue_lowering_fails_in_nested_loops` does the same
      against `ContinueLowering`, and asserts a shrunk shape with a nested
      loop.
- INV-BIND-1 (binding transaction: BIND-1, BIND-2, and BIND-7).
  - Rule: for any prior namespace and any ordered list of cases, the
    namespace after `CommitAfterGuard` runs equals the prior namespace
    updated with only the first accepted case's bindings, or the prior
    namespace unchanged if none is accepted. Each case is a sequence pattern
    of a given length with capture names and a real guard expression over
    candidates and globals. The subject is a tuple whose length decides
    which patterns match.
  - Sketch: the adapter renders real Python source and executes it. The
    chosen sketch binds candidates as parameters of a generated guard
    function. Guard expressions reference candidates, including a candidate
    that shadows a prior global, and may call a helper that reads globals.
  - Method: Hypothesis, differential. The expected namespace is computed
    independently from the case list by direct evaluation.
  - Artefacts: `adapters/host_binding.py` and
    `tests/test_contract_binding.py::test_binding_transaction_preserves_prior_state`.
  - Non-vacuity:
    - `@example`s cover overlapping names, a false guard, a failed pattern,
      and a guard helper that reads a shadowed global;
    - control `test_native_match_leaks_candidates` reruns the property
      against `NativeMatch`, and asserts a shrunk case list with a false
      guard;
    - control `test_tentative_commit_changes_guard_helpers` does the same
      against `TentativeCommit`, and asserts a shrunk case with a helper
      call.
- INV-IN-1 (record splitting: INPUT-2).
  - Rule: for any text over the alphabet {`a`, `é`, `\n`, `\r`, `\v`, `\f`,
    `\x1c`, `\x1d`, `\x1e`, U+0085, U+2028, U+2029}, encoded in UTF-8,
    `IncrementalReader.records` equals `RecordModel.records`. The model
    removes every `\r` directly before `\n` and a trailing `\r` at EOF,
    splits on `\n`, and drops the empty piece after a final `\n`.
  - Method: Hypothesis.
  - Artefacts: `records_model.py`, `adapters/host_reader.py`, and
    `tests/test_contract_input.py::test_record_splitting_matches_model`.
  - Non-vacuity: `@example`s for each separator; controls rerun the property
    against `UniversalNewlines` and `SplitLines`, and assert shrunk inputs
    containing `\r` and U+2028 respectively.
- LEM-IN-2 (incremental decoding: INPUT-3). A parameterized table covers:
  - `ok\n\xff\nlater\n` in UTF-8, which delivers `ok`, then fails with line
    2 and `NR + 1 = 2`;
  - UTF-16 with a BOM, two records, which decodes correctly;
  - `utf-8` keeping a BOM, against `utf-8-sig` stripping it.

  Control: `PerRecordDecode` fails on the UTF-16 row and keeps the BOM under
  `utf-8-sig`. `UniversalNewlines` (text-mode iteration) fails before delivering
  `ok`.
- INV-FIN-1 (lifecycle outcomes: FINAL-1 to FINAL-4, CONTROL-3, CONTROL-6,
  INPUT-7, and INPUT-9).
  - Rule: for every row of `tests/data/lifecycle_outcomes.json`,
    `OrderedDriver.outcome(row.script)` equals the row's expected outcome:
    whether `end:` ran, the records delivered, the status, and the failure
    category.
  - Rows: one per distinct outcome class, about 26. They cover:
    - preamble failure, `start:` failure, and invalid `FS`;
    - EOF with zero records and with two records;
    - `exit` on the first and last record;
    - predicate, guard, adapter, action, and input failure on records 1
      and 2;
    - suppression detected by the pending-signal check;
    - an `Exception` while unwinding;
    - `SystemExit(3)` in `start:`, in a rule, and as the last statement of
      `end:`;
    - an `end:` failure.
  - Each row cites the `docs/design-contracts.md` Table 2 line it derives
    from.
  - Method: exhaustive parameterization. The domain is finite, so this is
    not Hypothesis.
  - Artefacts: `adapters/host_lifecycle.py` and
    `tests/test_contract_lifecycle.py::test_lifecycle_outcomes_match_table`.
  - Non-vacuity: control
    `test_end_in_finally_driver_publishes_partial_results` asserts that
    `EndInFinally` disagrees on every record-phase failure row. Its `try`
    wraps the record loop only, so initialization rows agree, and the test
    asserts that too.
  - `KeyboardInterrupt` and the `SIGPIPE` rows are subprocess probes,
    because in-process they would kill the xdist worker.
- Host evidence for static rules (SCOPE-4, SCOPE-5, CONTROL-1, the CONTROL-3
  lint, CONTROL-4, CONTROL-5, BIND-3, BIND-5, and INPUT-8): these are not
  invariants that 1.1.2 can discharge, because no validator exists. The tests
  show only that each hazard is real on CPython, which justifies the rule.
  Discharge moves to the `discharged_by` tasks.

### Subprocess probes

Subprocess probes live in `tests/contract_ratification/probes/`. They are
standard-library scripts that take a mode argument, so related witnesses and
controls share one script and stay clear of the duplication gate. Each is
declared in the register with its arguments, standard input, expected output,
and status, and is run through `CorpusProbeRunner`:

- `main_module.py`:
  - `PRB-SCOPE-MODULE` (witness): mode `registered` prints `pickled`;
  - `PRB-SCOPE-DICT` (control): mode `dict` prints `PicklingError`;
  - `PRB-SCOPE-MP-FORK`: mode `fork-pool` prints `pool [9]`.
- `stdin_owner.py`, with three records on standard input:
  - `PRB-INPUT-STDIN-GUARD` (witness): `guarded` prints `ownership-error`;
  - `PRB-INPUT-STDIN-RACE` (control): `unguarded` prints
    `driver records: 0`;
  - `PRB-INPUT-CHILD-NULL` (witness): `child-null` prints
    `driver records: 3`;
  - `PRB-INPUT-CHILD-INHERIT` (control): `child-inherit` prints a count
    below 3. The control asserts "fewer than three" through an
    `expected_stdout_prefix` match.
- `exit_status.py`:
  - `PRB-CTL-BUILTIN-EXIT`: `builtin-exit` exits 0 with no `end:` output;
  - `PRB-FINAL-EXIT-STATUS`: `rule-sysexit` exits 0 with no `end:` output,
    and `end-sysexit` exits 3 after the summary;
  - `PRB-FINAL-INTERRUPT`: `interrupt` terminates by `SIGINT`, with status
    -2 as reported by `subprocess`.
- `sigpipe.py`, writing 200,000 lines to a pipe closed after one line:
  - `PRB-FINAL-SIGPIPE-DEFAULT` (witness): `default` gives status -13 and
    empty standard error;
  - `PRB-FINAL-SIGPIPE-IGNORED` (control): `python-default`, with `print`
    wrapped in `except Exception`, gives status 120 and an
    `Exception ignored` message.

`ProcessRunner` can carry a mode argument through the `ScriptImplementation`
arguments. If it cannot (for example, if it does not support a reader closing
its pipe early), the adapter gains a minimal `run_isolated` helper within the
code budget, and the change is recorded in `Decision log`.

### Residual gaps

Sampling does not prove all Python behaviour. The shape grammar excludes
`async` constructs (static errors under SCOPE-4), `match` statements inside
actions, and generators (CONTROL-4 forbids signals in nested definitions).
Context-manager suppression is caught by CONTROL-3's runtime check, but no test
proves that the future compiler implements it; 2.2.1 owns that. `sys.__stdin__`
and debugger reads remain residuals of INPUT-5. The `forkserver` hang is cited,
not executed. No formal prover is used: the obligations are contract
feasibility, not program correctness, and the finite lifecycle domain is
enumerated exhaustively.

## Plan of work

### Stage A: entry checks and baseline (EP-M0)

Record the merge base as `BASE`. Confirm that the TOML-helper promotion pull
request (see `Risks`) has merged, or that the owner chose the in-memory
alternative. Run the full gate set once through `scrutineer`, or by hand with
the commands in `Concrete steps`, to record a green baseline. Re-survey
`tests/job_corpus/` for helpers that landed after drafting (1.1.1's EP-M2 adds
`adapters/markdown_docs.py` and `report.py`), and reuse them where they fit.
Update `Interfaces and dependencies` before writing code. Record 1.1.1's status
and whether its budget has been raised.

### Stage B: register domain (EP-M1, Track A)

Red:

- Write `tests/test_contract_ratification_policy.py`,
  `tests/test_contract_ratification_render.py`, and
  `tests/test_contract_ratification_scenarios.py`, with the feature file
  `tests/features/contract_ratification.feature`.
- Write the fixture register `tests/data/ratified_register.toml` and the
  seeded-defect table.
- Run them, observe the import and missing-step failures, and do not commit
  the red state.

Green:

- Add `tests/contract_ratification/__init__.py`, `model.py`, `ports.py`,
  `policy.py`, `render.py`, `adapters/toml_register.py`, and
  `adapters/document_trace.py`.
- Seed the repository `register.toml` with every agenda decision, every
  counterexample, and every probe. Leave the area verdicts `pending`.
- Mark the three tests that can only pass later with
  `xfail(strict=True, raises=AssertionError, reason=...)`:
  - `test_repository_register_is_ratified` (EP-M4 removes the marker);
  - the scenario "Every contract area is ratified" (EP-M4);
  - `test_contract_index_matches_register` (EP-M5).
- Every other test passes against the fixture register.

Refactor: extend the boundary AST test, the Vulture whitelist, and its guard.

### Stage C: host evidence (EP-M2, Track A)

Work one contract area per commit, in this order: control transfer, binding
visibility, input ownership, finalization, then scope. For each property:

1. Write the property and its controls against the port.
2. Run them before any adapter exists, and observe the collection failure.
3. Add the chosen adapter and the model. The witness passes.
4. Add each rejected-alternative adapter. Its control passes, because the
   rerun property fails with the predicted shrunk example.
5. Declare the area's probes in `register.toml`, and add the scripts.

At the end of the stage, every `probe:`, `test:`, and `cite:` reference
resolves. The only remaining findings are `case:` and `obs:` references to jobs
that do not exist yet, and the pending verdicts, so the verdict is
`revise-evidence`. If 1.1.1 is still incomplete, set the plan to
`BLOCKED (awaiting 1.1.1)` here.

### Stage D: counterexample corpus jobs (EP-M3, Track B)

Rebase onto `main` after 1.1.1 has merged. Add the three jobs under
`Corpus additions`, with observation ids OBS-10 to OBS-12. Update the job and
case counts pinned in `tests/test_job_corpus_alternatives.py`. In the same
milestone:

- update the corpus evidence of the Q3 and Q5 rows in
  `docs/decision-register.md`, so `find_evidence_mismatches` holds;
- add OBS-10 to OBS-12 to `docs/job-corpus.md`, so
  `find_undocumented_observations` holds;
- add the `filter-complete-rows/numeric-rows` row to the Examples table of
  `tests/features/job_corpus.feature`.

The corpus audit stays `proceed`. The ratification verdict becomes
`pending-owner`.

### Stage E: owner ratification gate (EP-M4, Track B)

Render the decision index and the evidence summary into the pull request. For
each area, ask for one verdict, giving the recommendation, the owner options,
the counterexamples, and the evidence. Set this plan to
`IN PROGRESS (awaiting owner verdicts, EP-M4)`. Record each area verdict with
`decided_on` and `decided_in`, and list any per-decision exceptions. If the
owner picks an option or alternative, update the rule, adapters, probe
expectations, and corpus cases first, then re-run the area's evidence. Stage E
ends when `test_repository_register_is_ratified` passes and its marker is
removed.

### Stage F: contract documents (EP-M5, Track B)

Apply `Documentation changes`, then remove the marker from
`test_contract_index_matches_register`. Tick roadmap 1.1.2, set this plan to
`COMPLETE`, and fill in `Outcomes & retrospective`.

## Corpus additions

All three jobs follow the 1.1.1 schema: `job.toml`, `program.pokie` (marked
proposed, not executable), a `reference.py` that models the ratified rule
explicitly, and an `alternative.awk` that uses only POSIX features.
`aggregate-port-changes` is labelled with provenance "contract probe" (rather
than counted as representative evidence for Q1), because its naming
deliberately exposes the guard-visibility rule.

`filter-complete-rows` (filtering; G1, G5; Q5; CONTROL-2, CONTROL-5; OBS-10).
The program:

```plaintext
start:
    FS = ","
    seen = 0
    skipped = 0

when NR > 1:
    values = []
    for text in ($2, $3, $4):
        try:
            values.append(float(text))
        except ValueError:
            skipped += 1
            next
        finally:
            seen += 1
    print($1, sum(values))

end:
    print(seen, skipped)
```

- Case `numeric-rows` (tags `next-record`, `malformed-record`): input
  `id,a,b,c\nr1,1,2,3\nr2,4,x,6\nr3,7,8,9\n`. Expected
  `r1 6.0\nr3 24.0\n8 1\n`, status 0. The `finally` counts the value that
  triggered `next`, and `print` does not run for `r2`.
- Case `empty-input` (tags `empty-input`): expected `0 0\n`, status 0.
- OBS-10 (ambiguity, resolved by CONTROL-2): whether `next` inside `except`
  within a user loop runs `finally`, and whether it leaves only the user loop.
- Alternatives: awk with an explicit numeric regex and a field loop, which
  declares a divergence on float spellings that awk does not accept; status
  quo, a Python loop with `for`/`else`.

`aggregate-port-changes` (aggregation; G2, G3; Q5; BIND-1, BIND-2, BIND-7;
OBS-11). The program:

```plaintext
def changed(candidate):
    return candidate != port

start:
    port = None
    changes = 0
    malformed = 0

when /^svc=(\w+) port=(\S+)$/:
    case name, int(port) if changed(port):
        changes += 1
        print(name, port)
    case name, int(_):
        pass
    case _:
        malformed += 1

end:
    print(changes, malformed)
```

- Case `consecutive-ports` (tags `binding-isolation`, `guard-rejection`,
  `adapter-rejection`): input
  `svc=a port=80\nsvc=a port=80\nsvc=a port=x\nsvc=a port=443\n`. Expected
  `a 80\na 443\n2 1\n`, status 0. Inside the guard, `port` is the candidate,
  while `changed` reads the committed `port`. Under a tentative-commit reading,
  every guard compares a value with itself, so the output would be `0 1\n`.
- OBS-11 (ambiguity, resolved by BIND-2): what helpers called from a guard
  see.
- Alternatives: awk with an explicit `prev` variable; status quo, a Python
  loop with `try`/`except ValueError`.

`aggregate-csv-by-header` (aggregation; G1, G4; Q3, Q5; INPUT-1, INPUT-5,
INPUT-7, INPUT-10; OBS-12). The program assumes the recommended INPUT-10:

```plaintext
from collections import Counter

start:
    FS = ","
    teams = Counter()

when FNR == 1:
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
- Case `two-files`: operands `["a.csv", "b.csv"]`, where `a.csv` is
  `name,team\nada,core\n` and `b.csv` is `name,team\nlin,ops\nsam,core\n`.
  Expected `core 2\nops 1\n`, status 0. With `NR == 1`, the output would include
  `team 1` (CX-28).
- Case `header-only`: input `name,team\n`. Expected empty output, status 0.
- Case `empty-input`: expected empty output, status 0.
- OBS-12 (ergonomic-smell, resolved by INPUT-5 and INPUT-10): reading the
  header with `sys.stdin.readline()` in `start:` competes with the reader, and
  `NR == 1` fails across files. If the owner defers INPUT-10, OBS-12 stays
  open, the program uses `NR == 1`, and the `two-files` case expects
  `core 2\nops 1\nteam 1\n`.
- Alternatives:
  - awk with `-F,` and `FNR == 1 { next }`, using
    `comparison = "sorted-lines"`;
  - shell, with `comparison = "sorted-lines"`:

    ```sh
    awk 'FNR > 1' "$@" | cut -s -d, -f2 | LC_ALL=C sort | uniq -c | awk '{ print $2, $1 }'
    ```

  - status quo, `csv.DictReader` with a `Counter`.

## Behavioural specification

Feature file `tests/features/contract_ratification.feature`, with steps in
`tests/test_contract_ratification_scenarios.py`. Each defect scenario starts
from the fixture register (`tests/data/ratified_register.toml`), which audits as
`ratified` against a stub evidence index, and applies exactly one defect:

```gherkin
Feature: Ratify pokie's compiler and execution contracts
  The project owner ratifies scope, input ownership, control transfer,
  binding visibility, and finalization against executable evidence.

  Scenario: Every contract area is ratified
    Given the repository ratification register
    When the register is audited against the repository evidence
    Then the verdict is "ratified"
    And every contract area has an accepted owner verdict

  Scenario: A pending owner verdict blocks ratification
    Given a register that audits as ratified
    And the "control-transfer" area verdict is "pending"
    When the register is audited
    Then the verdict is "pending-owner"
    And exactly one finding names "control-transfer"

  Scenario: An amendment without a counterexample is rejected
    Given a register that audits as ratified
    And decision "SCOPE-1" cites no counterexamples
    When the register is audited
    Then the verdict is "revise-evidence"
    And exactly one finding names "SCOPE-1"

  Scenario: A falsifying counterexample demands contract revision
    Given a register that audits as ratified
    And counterexample "CX-17" has effect "falsifies"
    When the register is audited
    Then the verdict is "revise-contracts"

  Scenario: A control that agrees with its witness is vacuous
    Given a register that audits as ratified
    And probe "PRB-SCOPE-DICT" expects the same output as "PRB-SCOPE-MODULE"
    When the register is audited
    Then the verdict is "revise-evidence"
    And exactly one finding names "PRB-SCOPE-DICT"
```

The first scenario is bound explicitly with `@scenario(...)` before
`scenarios(...)`. Until EP-M4 it carries
`@pytest.mark.xfail(strict=True, raises=AssertionError,
reason="awaiting owner verdicts (EP-M4)")`,
so a missing step definition still fails. The other four pass from EP-M1
onwards.

## Milestones and plateaus

- EP-M0 (entry checks).
  - End state: `BASE` recorded, baseline green, TOML-helper route decided,
    and 1.1.1 status recorded.
  - Acceptance: the gate report and the `Progress` entries.
  - Conformance check: no product or harness file has changed.
  - Recovery: none needed.
  - Remaining gaps: everything else.
- EP-M1 (Track A; INV-REG-1, INV-REG-2, and the INV-DOC-1 renderer).
  - End state: the register package, loader, verdict, renderer snapshot, and
    scenarios 2–5 pass against the fixture register. The repository
    register is seeded, and its three pending tests are strict-xfail with
    `raises=AssertionError`.
  - Acceptance: `make check-fmt`, `make typecheck`, `make lint`, and
    `make test` pass.
  - Conformance check: the boundary test covers the new domain modules, and
    no adapter imports leak into them.
  - Recovery: revert the milestone commits; nothing depends on them yet.
  - Remaining gaps: evidence, jobs, verdicts, and documents.
- EP-M2 (Track A; INV-CTL-1, INV-BIND-1, INV-IN-1, LEM-IN-2, INV-FIN-1, and
  all probes).
  - End state: every `probe:`, `test:`, and `cite:` reference resolves;
    every witness passes; every control fails as predicted; and the
    repository verdict is `revise-evidence`, caused only by missing `case:`
    and `obs:` references.
  - Acceptance: the four gates and the named tests pass.
  - Conformance check: no sketch parses pokie text or exceeds 250 lines, and
    every witness agrees with the agenda's recommended rule.
  - Recovery: one commit per area, so an area can be reverted alone.
  - Remaining gaps: jobs, verdicts, and documents.
- EP-M3 (Track B; CX-17, CX-18, CX-20, and CX-28 corpus evidence).
  - End state: three jobs pass under their references and alternatives; the
    register and job-corpus documents agree with the corpus; the corpus
    audit is `proceed`; and the ratification verdict is `pending-owner`.
  - Acceptance: the four gates, plus `make markdownlint` and `make nixie`,
    pass.
  - Conformance check: no observation of kind `contradiction` was needed.
  - Recovery: delete a job directory and restore the pinned counts and
    document rows.
  - Remaining gaps: verdicts and the contract documents.
- EP-M4 (Track B; owner decision gate).
  - End state: every area has an accepted verdict with `decided_on` and
    `decided_in`; owner redirections are reflected in the evidence; and the
    verdict is `ratified`.
  - Acceptance: the first scenario and `test_repository_register_is_ratified`
    pass without markers, and the four gates pass.
  - Conformance check: no verdict was recorded without a linked owner
    acceptance.
  - Recovery: verdicts are data, and can be reverted per area.
  - Remaining gaps: the contract documents.
- EP-M5 (Track B; INV-DOC-1 and the `RM-1.1.2` success criterion).
  - End state: the documents below are updated, the index test passes
    without its marker, the roadmap is ticked, and the plan is `COMPLETE`.
  - Acceptance: `make all` passes (through `scrutineer`, or by hand).
  - Conformance check: every `amended` decision is stated in the design or
    contracts; ADR statuses match the verdicts; and the precondition,
    falsification, and owner constraints held throughout.
  - Recovery: one commit per document group.
  - Remaining gaps: none for 1.1.2. Downstream obligations are the
    register's `discharged_by` entries.

## Documentation changes

EP-M3 makes these changes:

- `docs/decision-register.md`: corpus evidence for Q3 and Q5, on single-line
  rows.
- `docs/job-corpus.md`: OBS-10 to OBS-12, and the three jobs.

EP-M5 makes these changes:

- `docs/adrs/adr-0002-preserve-one-program-scope-and-ordered-lifecycle.md`:
  - Retitle it "Architectural decision record (ADR) 0002: Preserve one
    program scope and ordered lifecycle", and restructure it to the
    template.
  - Set Status to "Accepted (YYYY-MM-DD): one `__main__` module compiled as
    one unit; `BaseException` control signals with runtime suppression
    detection; commit-after-guard bindings; `end:` only after EOF or
    `exit`".
  - Add `Decision drivers`, `Options considered` (keeping the existing
    alternatives, plus the tentative-commit and `Exception`-signal
    alternatives), a decision outcome that lists the SCOPE, CONTROL, BIND,
    and FINAL ids, `Known risks and limitations` (context managers seeing
    signals, `multiprocessing` start methods, `globals()` access, stale
    bindings, and the residuals), and `Architectural rationale`.
  - Since it is still `Proposed`, edit the body directly. No amendment
    banner is needed.
- New `docs/adrs/adr-0005-give-the-record-reader-sole-ownership-of-input.md`,
  status `Accepted (YYYY-MM-DD)`, covering:
  - INPUT-1 to INPUT-10;
  - the options considered for standard input (a shared stream, a guard
    only, descriptor redirection with a guard, and an injected reader
    object);
  - the field-access options (`FIELDS`, `$(expr)`, and deferral);
  - the non-goals (`getline` look-ahead and multiple output files);
  - Q3 v1 scope, and the 6.1.1 deferral.
- `docs/adrs/adr-0001-lower-pokie-through-python-asts.md`: add the
  lowering constraints from SCOPE-1, SCOPE-2, BIND-1, BIND-5, CONTROL-2, and
  CONTROL-3 to its proposed direction, and keep it `Proposed` unless the owner
  asks to accept it.
- `docs/pokie-design.md`:
  - Update the status line to ratified v0.2 with the date, and the §1
    paragraph on ratification.
  - Amend §3.1 (SCOPE-2 to SCOPE-4, and INPUT-6), §3.2 (CONTROL-1), §4.1
    (INPUT-1 to INPUT-5, INPUT-7, INPUT-8, and INPUT-10), §4.2 (SCOPE-1,
    SCOPE-7, FINAL-1 to FINAL-5, and the flush order), §4.3 (CONTROL-2 to
    CONTROL-6), §5 (BIND-1 to BIND-7), §7 (SCOPE-5), and §9 (the CONTROL-3
    runtime check, INPUT-5, and FINAL-6).
  - In §10, point the Table 2 rows at the register's evidence.
  - In §11, add the lifecycle-spanning cleanup block and `exit STATUS`
    candidates.
  - Cite decision ids inline.
- `docs/design-contracts.md`:
  - Update the status line.
  - Add §6 "Ratified semantic decisions", with the rendered index between
    markers and a caption.
  - Amend §4 Table 2 (the `-F` usage row, operands to a program that reads
    no input, `SystemExit` and `KeyboardInterrupt`, the suppression row, and
    the broken-pipe row).
  - Amend §2's `Control` placement, with a pointer to CONTROL-4.
- `docs/context.md`:
  - Add the evidence status `Ratified contract`.
  - Add the terms control signal, initialization, record-scoped name,
    program namespace, counterexample, witness, and control (evidence).
  - Fix the lifecycle-block definition to include pokie `exit`.
- `docs/terms-of-reference.md` §9 Table 5: Q5 "Ratified contract (1.1.2, ADR
  0002)", and Q3 "Ratified contract for v1 (1.1.2, ADR 0005); expansion is an
  open question for 6.1.1".
- `docs/decision-register.md`: Q5 status `Ratified contract`, and Q3
  `Ratified contract (v1)`. EP-M0 confirms that the 1.1.1 register parser
  accepts these strings; if not, use its vocabulary and record the mapping.
- `docs/job-corpus.md` "Phase 1 findings": the dispositions of OBS-01,
  OBS-02, OBS-06, OBS-07, OBS-08, and OBS-03 (LEX-1).
- `docs/developers-guide.md`: a "Contract ratification register" section
  covering:
  - the package layout and ports;
  - the register schema;
  - how to add a decision, counterexample, probe, or rejected-alternative
    adapter;
  - the witness and control rule;
  - the verdict values and their precedence;
  - that verdicts are recorded only with a linked owner acceptance;
  - `superseded`;
  - the `discharged_by` obligation.
- `docs/users-guide.md`: one sentence pointing to `docs/design-contracts.md`
  §6 as ratified future behaviour.
- `docs/repository-layout.md`: add `tests/contract_ratification/`.
- `docs/contents.md`: a heading for accepted decision records; ADR 0005; and
  this ExecPlan.
- `docs/roadmap.md`: tick 1.1.2.

## Concrete steps

Run every command from the repository root. Format first, so that every later
gate checks one fixed tree. Keep full logs with `tee`:

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

`make lint` runs its sub-gates in one recipe, so an early failure leaves later
sub-gates unverified. Re-run it to completion after each fix.

For focused red-green cycles:

```bash
uv run pytest -v -n 0 tests/test_contract_*.py
```

Expected after EP-M1 (abridged):

```plaintext
tests/test_contract_ratification_scenarios.py::test_a_pending_owner_verdict_blocks_ratification PASSED
tests/test_contract_ratification_scenarios.py::test_every_contract_area_is_ratified XFAIL (awaiting owner verdicts (EP-M4))
tests/test_contract_ratification_policy.py::test_repository_register_is_ratified XFAIL (awaiting owner verdicts (EP-M4))
```

Expected after EP-M2 (abridged):

```plaintext
tests/test_contract_control.py::test_signal_unwinding_matches_model PASSED
tests/test_contract_control.py::test_exception_signals_are_caught_by_user_handler PASSED
tests/test_contract_binding.py::test_native_match_leaks_candidates PASSED
tests/test_contract_lifecycle.py::test_lifecycle_outcomes_match_table[action-failure-record-2] PASSED
```

Expected after EP-M4:

```plaintext
tests/test_contract_ratification_scenarios.py::test_every_contract_area_is_ratified PASSED
tests/test_contract_ratification_policy.py::test_repository_register_is_ratified PASSED
```

Update the renderer snapshot serially, because syrupy can corrupt snapshots
under xdist, and an unused snapshot fails the session:

```bash
uv run pytest -n 0 tests/test_contract_ratification_render.py --snapshot-update
```

Measure the budgets:

```bash
git diff --numstat BASE -- 'tests/**/*.py' ':!tests/job_corpus/jobs/**' \
  | awk '{a+=$1; d+=$2; n++} END {print n " files, " a-d " net lines"}'
git diff --numstat BASE -- 'tests/job_corpus/jobs/**' \
  | awk '{a+=$1; d+=$2; n++} END {print n " files, " a-d " net lines"}'
git diff --numstat BASE -- tests/contract_ratification/register.toml 'tests/data/**' \
  'tests/features/**' '**/__snapshots__/**' pyproject.toml \
  | awk '{a+=$1; d+=$2} END {print a-d " net lines"}'
git diff --numstat BASE -- docs ':!docs/execplans/**' README.md \
  | awk '{a+=$1; d+=$2} END {print a-d " net lines"}'
```

Commit after each green step, with every gate passing. Use imperative subjects
such as "Add ratification register domain (1.1.2)".

## Validation and acceptance

The task is complete when all of these hold:

- `make all` passes.
- `test_repository_register_is_ratified` passes, and every area has an
  accepted owner verdict with `decided_on` and `decided_in`.
- Each control test passes because its rejected-alternative adapter fails
  the witness property, with the predicted shrunk example. Swapping a chosen
  adapter for its rejected alternative makes the witness fail.
- `test_contract_index_matches_register` passes, and editing either side
  breaks it.
- ADR 0002 and ADR 0005 are `Accepted`. ADR 0001 matches the owner's
  verdict.
- Roadmap 1.1.2 is ticked.

## Idempotence and recovery

Every step can be re-run. The register and corpus are data, loaded fresh on
each run. Probes write only inside `ProcessRunner`'s temporary directory.
In-process sketches execute in fresh module objects and never touch
`sys.modules["__main__"]`, file descriptor 0, or signal dispositions; only
subprocess probes do. If a milestone fails halfway, revert to the last green
commit with `git revert` (never a destructive reset on a shared branch), and
re-run the milestone's red step. Snapshot updates are deterministic and serial.

## Artefacts and notes

Scratch probe transcript (CPython 3.14.7, 2026-11-14; not committed):

```plaintext
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
P8 SyntaxError: nonlocal x - nonlocal declaration not allowed at module level
P8 ok: global x
P9 helper in guard sees committed n -> guard False
P10 context: _Next
P12 lone CR split: ['a\n', 'b\n'] newline='': ['a\r', 'b\r\n', 'c']
bare break in action stops record loop: ['a']
```

Expert-panel experiments (2026-11-14; recorded by the reviewers, not committed):

```plaintext
alias BE = BaseException ............ swallowed
Exception = BaseException ........... swallowed
except type(x) ...................... swallowed
except* BaseException ............... swallowed
except* Exception ................... propagated
signal from except + finally: break . swallowed warn=1
pending-flag runtime check .......... RuntimeError: control signal suppressed in record a
forkserver Pool, __file__=prog.pokie  SyntaxError, ConnectionResetError
forkserver/spawn Pool, no __file__ .. hung (killed by timeout)
fork Pool ........................... pool [9]
two exec units __annotate__ ......... {'y': <class 'str'>}
next inside `with sqlite3 conn` ..... row count 0 (rolled back)
child `wc -l` inheriting fd 0 ....... child 198141 lines, parent 1860
stdin.readline() then buffer reader . driver records: 0
print in except Exception | head -1 . status 120, "Exception ignored ... BrokenPipeError"
SIG_DFL SIGPIPE | head -1 ........... status 141, empty stderr
gawk 5.3.0 missing 2nd operand ...... earlier records, "fatal: cannot open file", no END, status 2
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
  a failed match."
- Python 3.14 reference, `try`: "If the finally clause executes a return,
  break or continue statement, the saved exception is discarded."
- PEP 765 (Final, 3.14): CPython emits `SyntaxWarning` for
  `return`/`break`/`continue` that exits a `finally` block.
- Python 3.14 `exec`: separate globals and locals execute "as if it were
  embedded in a class definition". `return` and `yield` may not be used outside
  function definitions.
- PAWK: `-B` and `-E` statements, with per-line exceptions ignored unless
  `--strict` is given. That contrasts with FINAL-2's abort-without-`end:` rule.

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
    LEXICAL = "lexical"  # routed items only; never counted as a ratified area


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
    SUPERSEDED = "superseded"


class RatificationVerdict(enum.StrEnum):
    REVISE_CONTRACTS = "revise-contracts"
    REVISE_EVIDENCE = "revise-evidence"
    PENDING_OWNER = "pending-owner"
    RATIFIED = "ratified"


@dataclasses.dataclass(frozen=True, slots=True)
class Decision:
    id: str  # "CONTROL-3"
    area: ContractArea
    rule: str
    disposition: Disposition
    proposal: str  # where the original proposal lived, e.g. "DES-4.3"
    documents: tuple[str, ...]
    counterexamples: tuple[str, ...]
    evidence: tuple[str, ...]  # "probe:ID", "test:NODE", "case:JOB/CASE", "obs:OBS-nn", "cite:PATH#ANCHOR"
    discharged_by: tuple[str, ...]  # roadmap task ids


@dataclasses.dataclass(frozen=True, slots=True)
class AreaVerdict:
    area: ContractArea
    owner_verdict: OwnerVerdict
    decided_on: str  # "" or YYYY-MM-DD
    decided_in: str  # "" or a review or comment URL
    exceptions: tuple[str, ...]  # decision ids the owner redirected


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
    expected_stdout_prefix: bool  # match a prefix only (for counts that vary)
    expected_status: int
    pairs_with: str  # the witness a control opposes, otherwise ""


def audit_register(register: Register, evidence: EvidenceIndex) -> RatificationReport: ...
def render_decision_index(register: Register) -> str: ...
```

- `Register` groups the area verdicts, decisions, counterexamples, and
  probes.
- `EvidenceIndex` holds the resolvable ids that adapters supply: probe
  outcomes, corpus case ids, observation ids, test node ids, citation targets,
  and roadmap task ids.
- `RatificationReport` holds the verdict and sorted findings. It reuses
  `job_corpus.findings.Finding` if that type's kinds can be extended without
  disturbing the 1.1.1 policies; otherwise it defines a sibling type. Decide at
  EP-M1 and record the choice in `Decision log`.

Register file shape (TOML, schema 1, unknown keys rejected):

```toml
schema = 1

[[verdicts]]
area = "binding-visibility"
owner_verdict = "pending"
decided_on = ""
decided_in = ""
exceptions = []

[[decisions]]
id = "BIND-2"
area = "binding-visibility"
rule = "A guard sees candidates as locals; functions it calls see committed program state."
disposition = "ratified"
proposal = "DES-5"
documents = ["docs/adrs/adr-0002-preserve-one-program-scope-and-ordered-lifecycle.md", "docs/pokie-design.md"]
counterexamples = ["CX-18"]
evidence = ["test:tests/test_contract_binding.py::test_guard_helper_sees_committed_state", "case:aggregate-port-changes/consecutive-ports"]
discharged_by = ["3.2.1"]

[[counterexamples]]
id = "CX-18"
area = "binding-visibility"
summary = "A helper called from a guard reads the committed value, not the candidate."
effect = "clarifies"
evidence = ["test:tests/test_contract_binding.py::test_guard_helper_sees_committed_state"]

[[probes]]
id = "PRB-SCOPE-DICT"
role = "control"
script = "probes/main_module.py"
args = ["dict"]
stdin = ""
expected = { stdout = "PicklingError\n", stdout_prefix = false, exit_status = 0 }
pairs_with = "PRB-SCOPE-MODULE"
```

Reused from the 1.1.1 harness:

- `ProcessRunner`, `ScriptImplementation`, `JobCase`, `InputFile`, and
  `EvidenceFormatError`;
- the strict TOML helpers, promoted to public names (see `Risks`);
- `model.Observation` and the corpus loader, for resolving `case:` and
  `obs:` references;
- if 1.1.1's EP-M2 delivers it, `adapters/markdown_docs.py`, which then
  replaces the planned `adapters/document_trace.py`.

## Skills and documentation signposts

Load these skills during implementation:

- `execplans`, to keep this plan current;
- `hexagonal-architecture`, for the ports, the models, and the chosen and
  rejected adapters;
- `python-router`, then:
  - `python-testing`, for fixtures, parametrization, syrupy, and pytest-bdd
    marks;
  - `hypothesis`, for shape strategies, `@example`, and controls rerun
    against mutant adapters;
  - `python-verification`, if a control's adequacy is in doubt;
- `python-data-shapes` and `python-types-and-apis`, for frozen values,
  `StrEnum`, and `Protocol` ports;
- `python-errors-and-logging`, for loader errors (reuse
  `EvidenceFormatError`);
- `python-concurrency`, for the `multiprocessing` probe;
- `skylos` and `ruff-016`, for dead-code and lint findings;
- `leta`, for navigation (install basedpyright, or fall back to reads);
- `en-gb-oxendict-style`, for prose;
- `commit-message` and `pr-creation`, for commits and the pull request.

Read these first:

- `AGENTS.md`;
- `docs/developers-guide.md`, "Corpus harness";
- `docs/documentation-style-guide.md`, "Architectural decision records";
- `docs/complexity-antipatterns-and-refactoring-strategies.md` §4.A (single
  responsibility, early abstraction, and guard clauses) and §5.C (pattern
  matching and dispatch tables, for the shape renderers);
- `docs/scripting-standards.md`, for probe-script conventions;
- the 1.1.1 ExecPlan's `Surprises & discoveries`, for tooling traps:
  - the Ruff/Pylint `except (A, B)` conflict, which needs `# fmt: skip`;
  - Interrogate covering private and nested helpers;
  - Vulture and pytest-bdd;
  - coverage filtering;
  - fix steps placed before check steps.

## Revision note

2026-11-14 (revision 1): initial draft. It recorded the 1.1.1 precondition gap,
a 34-decision agenda, CX-01 to CX-22, the witness and control design, three
corpus jobs, and the owner decision gate.

2026-11-14 (revision 2): revised after the four-reviewer expert panel. The
changes:

- Split delivery into Track A and Track B, and added the TOML-helper
  promotion route.
- Rewrote CONTROL-3 with a runtime pending-signal check, because the static
  rule was shown to be incomplete.
- Moved INPUT-5 to file-descriptor ownership after the child-process
  counterexample, and fixed the `PRB-INPUT-STDIN-RACE` expectation.
- Changed SCOPE-1 to leave `__main__` installed and document the
  `multiprocessing` start-method limitation.
- Moved INPUT-3 to incremental decoding per operand.
- Added SCOPE-7 (`sys.argv`, `sys.path`) and INPUT-10 (`FIELDS`, `FNR`, and
  `FILENAME`).
- Made the FINAL-6 broken-pipe mechanism explicit, and specified diagnostic
  contents.
- Widened BIND-5 to lazily evaluated scopes, and adopted record capture for
  generator expressions and lambdas, with the simpler rule as an owner option.
- Corrected CX-07 against gawk 5.3.0, and added CX-23 to CX-31.
- Introduced ports and rejected-alternative adapters, controls that rerun
  the witness property, explicit `@example`s in place of statistics, a
  lifecycle outcome table in place of the lifecycle model, and in-process tests
  instead of most subprocess probes.
- Made the scenarios non-vacuous through a fixture register, and added
  `raises=AssertionError` to every strict `xfail`.
- Added the `revise-evidence` verdict, per-area owner verdicts with
  `decided_in`, and `superseded`.
- Kept ADR 0001 `Proposed` by default, and fixed ADR 0005's number.
- Replaced `filter-first-bad-token` with `filter-complete-rows`, added
  `case _` handling and a "contract probe" label to `aggregate-port-changes`,
  and dropped the `missing-second-file` case, which the runner refuses.
- Moved the corpus document edits into EP-M3.
- Recalibrated the budgets.

This affects the remaining work: owner approval of the plan is next. Track A
may then begin. Track B waits for 1.1.1.
