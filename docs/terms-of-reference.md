# pokie – terms of reference

Status: draft v0.1 with acknowledged open questions. Audience: project owner,
implementers, and reviewers. Last substantive revision: 2026-10-09.

Companions: `docs/context.md`, `docs/pokie-design.md`, and `docs/roadmap.md`.
The agreed documentation basis authorizes exploration of a sequential tool for
Python-fluent shell users. It does not establish market demand or certify the
proposed language contracts.

## 1. Background and motivation

Pokie began with a deliberately invented concept: awk with Python syntax and
library support. The supplied conversation developed regex capture dispatch,
predicates, and conversion patterns as ways to express text processing without
separating recognition from validation into unrelated glue code.[^1]

The motivation is exploratory. No external event, customer request, funding
commitment, or measured usability deficiency establishes urgency. The first
useful result is evidence that the combined notation improves representative
text-processing jobs enough to justify maintaining another language.

The repository presently provides a generated Python greeting package and
development tooling. Product capabilities described here are targets.

## 2. Domain

The domain is command-line record processing: selecting text, extracting
values, rejecting malformed values, aggregating results, and emitting output
for another command or a human reader. Established alternatives include awk
programs and ordinary Python scripts. PAWK and pyawk already explore the
overlap between Python and awk-like processing.[^2][^3]

The [context document](context.md), `docs/context.md`, defines record, field,
capture, rule, case, guard, adapter, and binding. These distinctions matter:
matching part of a line must not redefine the whole input record, and rejecting
a conversion must not conceal a broken user extension.

Pipeline users expect predictable output, meaningful failure statuses, and
scripts that work on a stream without loading the entire input by default.
Those expectations form the agreed working basis, rather than findings from
user research. No regulatory or contractual obligations have been supplied.

## 3. Market context

| Alternative             | Existing role                                                       | Question pokie must answer                                       |
| ----------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------- |
| awk                     | Record-oriented filtering and aggregation                           | Does Python-shaped notation justify another tool for these jobs? |
| Python scripts          | General-purpose parsing with installed libraries                    | Does the notation remove enough loop and exception glue to help? |
| PAWK                    | Python line processing with begin/end and pattern-action facilities | Does structural capture dispatch add useful clarity?             |
| pyawk                   | A Python-based variant of common awk facilities                     | Does the adapter protocol justify a distinct language surface?   |
| Existing shell pipeline | Familiar commands already installed                                 | Is adopting pokie worth an extra runtime and syntax?             |

Table 1: Named alternatives and the differentiation questions they raise.

PAWK and pyawk are primary-source prior art, not adoption benchmarks. Pokie's
candidate gap is ergonomic: recognition, structural dispatch, and semantic
validation in one readable record-processing program. Competitive uniqueness,
commercial opportunity, and user preference remain unverified.

## 4. Users and stakeholders

| Group                                                     | Context and concerns                                                                                                     | Alternative or boundary                                | Evidence status                                  |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | ------------------------------------------------ |
| Primary: Python-fluent command-line users                 | Process logs and text extracts; value readable scripts and library reuse; dislike hidden state and installation friction | awk or Python script                                   | Agreed basis; demand unverified                  |
| Secondary: script reviewers and maintainers               | Need to understand rejected data, state changes, and failures without the author present                                 | Review ordinary scripts                                | Assumption                                       |
| Stakeholder: project owner                                | Determines scope and whether evidence warrants further work                                                              | Stop after discovery if value is insufficient          | Role established; release authority details open |
| Non-user: operator executing untrusted submitted programs | Requires isolation and resource containment                                                                              | Use a separately designed sandbox or execution service | Outside initial scope                            |
| Non-user: team requiring distributed streaming            | Requires recovery, partitioning, and delivery guarantees                                                                 | Use a streaming platform                               | Outside initial scope                            |

Table 2: Initial user and stakeholder mapping.

No named sponsor, paying segment, or enterprise procurement requirement has
been established. Reviewers are a distinct audience because compact syntax only
helps if another person can interpret it accurately.

## 5. Job to be done

When a Python-fluent command-line user needs to extract and summarize values
from text, they want recognition, validation, and aggregation in one readable
script, so they can produce a useful answer without maintaining a separate
parsing framework.

The functional outcome is a result with explicit treatment of malformed
records. The assumed emotional outcome is confidence that compact notation has
not hidden surprising behaviour. The assumed social outcome is a script a
teammate can review and reuse. Those latter outcomes need user evidence.

Current workarounds combine regex calls, unpacking, conversion exceptions, and
accumulator updates in Python, or place increasingly complex predicates inside
awk rules. Keeping the existing script is also a valid alternative.

## 6. Scope

### 6.1. Goals

- **G1 – Readable streaming:** express filtering and aggregation over
  ordered records with explicit initialization and final output.
- **G2 – Capture dispatch:** separate regex recognition from structural
  decisions, including multiple cases and guards.
- **G3 – Semantic validation:** distinguish preserving predicates from
  conversions, with ordinary rejection participating in case selection.
- **G4 – Library reuse:** use installed Python libraries without rewriting
  their functionality into pokie-specific equivalents.
- **G5 – Observable failures:** identify syntax, input, and user-code errors
  accurately enough to correct the program or data.

These goals derive from the chat and the agreed drafting basis. Success
criteria below make them falsifiable without prescribing architecture.

### 6.2. Non-goals

- Automatic parallelization and distributed execution are outside the
  initial release; ordering and shared state take priority.
- Reimplementing Python or promising every interpreter is outside scope;
  runtime compatibility must be stated and demonstrated.
- Dependency installation through `pokie nibble` is deferred; use ordinary
  Python environment management.
- Implicit conversion of every capture and an unrestricted catalogue of
  validators are outside scope; conversions must be visible in patterns.
- Untrusted-code isolation and guaranteed resource limits are outside
  scope; scripts execute with the operator's authority.
- Full awk compatibility, arbitrary record separators, capture histories,
  and a general parser-combinator framework are outside the initial scope.

## 7. Success criteria

| Dimension          | Proposed evidence                                               | Pass or decision criterion                                                                                                          |
| ------------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| User-facing, G1    | Filtering and aggregation corpus                                | Specified outputs, ordering, and empty-input outcomes match for every corpus program                                                |
| User-facing, G2/G3 | Valid, malformed, and optional-capture examples                 | Exactly the intended case runs; invalid conversions fall through; unexpected extension failures remain visible                      |
| User-facing, G4    | Imports from standard library and selected third-party packages | Programs run in the documented environment and preserve expected values and exceptions                                              |
| User-facing, G5    | Syntax and runtime diagnostic corpus                            | Diagnostics locate original pokie source and identify the failing input where applicable                                            |
| Operational        | Large stream with no accumulating user state                    | Reader/compiler overhead does not retain previous records; throughput and peak memory are reported against Python and awk baselines |
| Strategic          | Observation of representative users solving the same jobs       | Owner decides whether benefit warrants another language; recruitment and adoption thresholds remain open                            |

Table 3: Proposed success evidence tied to product goals.

No throughput, onboarding, revenue, or adoption threshold is invented here. The
evidence corpus and comparative usability exercise must be agreed before the
project claims success. Benchmarks describe their input and environment; they
do not promise a universal speed advantage.

## 8. Constraints and assumptions

### 8.1. Hard constraints

Python syntax and library reuse belong to the established product concept. The
repository carries an ISC licence. Repository documentation conventions require
British English with Oxford spelling, linked companion documents, and validated
Markdown and diagrams.

No budget ceiling, deadline, supported operating-system set, or externally
mandated runtime version has been supplied. The scaffold currently requires
Python 3.14 or newer; treating that as a release promise requires a decision.

### 8.2. Assumptions

| Assumption                                   | Consequence if false                                  | Evidence needed                                |
| -------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------- |
| Sequential execution serves the first users  | Reconsider target jobs before introducing concurrency | Representative workload observations           |
| Users can manage a Python environment        | Library reuse fails during onboarding                 | Clean-environment installation trials          |
| Programs are trusted                         | Current execution boundary is unsuitable              | Revisit scope and isolation requirements       |
| Capture cases reduce parsing glue            | Extra syntax provides insufficient value              | Comparative script review and task observation |
| A small adapter catalogue suffices initially | Early users need extensions before adoption           | Corpus of actual validation needs              |

Table 4: Load-bearing assumptions and their failure consequences.

### 8.3. Dependencies

The Python ecosystem and the user's installed packages are external
dependencies of library reuse. Platform-specific packages constrain the
compatibility claim. Representative inputs and user feedback are critical
dependencies of product validation; neither is replaced by passing tests.

Compiler and execution technology choices belong in `docs/pokie-design.md`.

## 9. Open questions

Owners are unassigned unless stated. Roadmap task 1.1.1 assigns decision owners
and establishes which evidence blocks each implementation slice.

| ID  | Question and downstream gate                                                         | Resolution criterion                                              | Suggested path                                                          |
| --- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Q1  | Which primary-user jobs justify adoption? Gates success claims                       | Agreed corpus and observed comparison against existing scripts    | User research; project owner coordinates                                |
| Q2  | Which runtimes, platforms, and distribution channels ship? Gates packaging           | Explicit compatibility matrix and clean-environment evidence      | Packaging decision and ADR                                              |
| Q3  | Are fields mutable, and can libraries own structured input? Gates language expansion | Chosen ownership and mutation contracts with interaction examples | Initial design proposes read-only fields and one reader; revisit by ADR |
| Q4  | How are custom adapters registered before compilation? Gates extension delivery      | Working registration spike with class-pattern disambiguation      | Adapter ADR and implementation spike                                    |
| Q5  | Do proposed guard bindings and lifecycle failures meet expectations? Gates lowering  | Ratified contract and representative counterexamples              | Scope/lifecycle ADR and semantic corpus                                 |
| Q6  | Which semantic validators belong in the catalogue? Gates later adapters              | Explicit accepted types, rejection rules, and evidence of need    | User corpus; no automatic promotion of joke examples                    |
| Q7  | What performance and usability thresholds justify release? Gates release claims      | Named workloads, baseline results, and owner-approved thresholds  | Measurements and task observation                                       |
| Q8  | Who sponsors the work and approves releases? Gates strategic success                 | Explicit authority and success criteria                           | Further elicitation                                                     |

Table 5: Open questions, gates, and resolution evidence.

## 10. Handoff and references

The draft is ready for a proposed design and GIST roadmap. Q2, Q4, and Q5 must
be settled before the dependent release or extension capabilities ship.
Vocabulary additions are recorded in `docs/context.md`.

Architecture candidates have separate proposed records:
`docs/adr-001-cpython-ast-lowering.md`,
`docs/adr-002-execution-scope-and-lifecycle.md`, and
`docs/adr-003-pattern-adapter-resolution.md`. Distribution remains an ADR
candidate until Q2 has evidence. These records explain mechanisms without
turning the terms of reference into an architecture specification.

[^1]: Supplied conversation, model `gpt-5-6-thinking`, 2026-08-05
    14:05:47 +01:00. Original conversation:
    <https://chatgpt.com/c/6a733511-6788-83eb-b782-dec8af1dca74>.
    Source is the user-provided transcript; the URL was not independently
    retrieved. Documentation basis approved in this session, 2026-10-09.
[^2]: [PAWK primary repository](https://github.com/alecthomas/pawk),
    accessed 2026-10-09.
[^3]: [pyawk primary repository](https://github.com/RussellLuo/pyawk),
    accessed 2026-10-09.
