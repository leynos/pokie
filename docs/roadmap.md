# pokie roadmap

This roadmap delivers the goals in `docs/terms-of-reference.md` through the
proposed architecture in [the design](pokie-design.md), `docs/pokie-design.md`.
Goals, Ideas, Steps, and Tasks (GIST) alignment maps each phase to a
falsifiable idea, each step to one delivery workstream, and each checkbox to a
review-sized execution unit. It promises no dates.

G1–G5 cover readable streaming, capture dispatch, semantic validation, library
reuse, and observable failures. Proposed decisions live in
`docs/adr-001-cpython-ast-lowering.md`,
`docs/adr-002-execution-scope-and-lifecycle.md`, and
`docs/adr-003-pattern-adapter-resolution.md`. All tasks remain unchecked:
documentation is not an implementation milestone.

## 1. Establish falsifiable contracts

Idea: settling ownership, execution, and pattern contracts before building the
first script will reveal semantic contradictions while changes remain cheap.
Reject the foundation if representative examples cannot be specified without
incompatible rules.

This phase supplies decisions and evidence inputs, not a parser layer with no
user outcome. It supports every product goal.

### 1.1. Determine what the first release must demonstrate

This step asks whether the proposed scope covers actual text-processing jobs.
Its evidence determines the corpus and which open decisions block later slices.
See terms-of-reference.md §§4–9 and pokie-design.md §§1–2.

- [ ] 1.1.1. Establish the representative job corpus and decision register.
  - See terms-of-reference.md §§5–9 and pokie-design.md §1.
  - Success: filtering, capture validation, and aggregation jobs have inputs,
    expected outcomes, alternatives, and assigned decision owners for Q1–Q8.
- [ ] 1.1.2. Ratify the compiler and execution proposals against the corpus.
  - Requires 1.1.1.
  - See pokie-design.md §§2–5 and ADRs 001–002.
  - Success: scope, input ownership, control transfer, binding visibility,
    and finalization are decided; counterexamples update the contracts.

### 1.2. Establish inspectable language boundaries

This step asks whether pokie syntax can coexist with Python fragments without
corrupting source locations. Its result determines the parser approach and
verification oracle. See pokie-design.md §§3, 7, and 10.

- [ ] 1.2.1. Create the lexical and source-coordinate fixture corpus.
  - Requires 1.1.2.
  - See pokie-design.md §§3, 7, and 10; design-contracts.md §2.
  - Success: regex/division, escaped delimiters, comments, Unicode,
    multiline strings, and f-string expressions have unambiguous spans.
- [ ] 1.2.2. Establish the IR contract and bounded reference evaluator.
  - Requires 1.2.1.
  - See pokie-design.md §§7, 10 and design-contracts.md §2.
  - Success: small ordered-rule/lifecycle programs produce inspectable
    traces; generated cases shrink while preserving contract validity.

## 2. Deliver useful ordered text scripts

Idea: filtering and aggregation with Python libraries will be useful before
advanced patterns if a complete inline/file workflow preserves record order and
reports original-source failures. Falsify it if the corpus still requires
ordinary Python loop scaffolding to achieve its basic outcomes.

This is the first end-to-end language slice, addressing G1, G4, and G5.

### 2.1. Run initialization, predicates, and aggregates

This step asks whether one persistent scope can express the baseline jobs. It
informs capture dispatch without introducing another execution path. See
pokie-design.md §§3–4, 7.

- [ ] 2.1.1. Implement the scanner/parser for preambles, lifecycle blocks,
  expression rules, and direct actions with source spans.
  - Requires phase 1.
  - See pokie-design.md §§3, 7 and design-contracts.md §2.
  - Success: lexical fixtures pass and rejected constructs locate the
    original token before any user code executes.
- [ ] 2.1.2. Lower the baseline IR to compiled Python in a persistent scope.
  - Requires 2.1.1.
  - See pokie-design.md §§4.2, 7, and 10; ADR 001.
  - Success: imports, definitions, state, and ordered rule traces agree
    with the evaluator for bounded generated programs.
- [ ] 2.1.3. Add the single-owner reader, fields, counters, and separator
  configuration to execute the baseline corpus.
  - Requires 2.1.2.
  - See pokie-design.md §4.1 and design-contracts.md §4.
  - Success: empty input, final unterminated lines, empty fields, and
    sequential files preserve the specified outputs and counts.

### 2.2. Make pipeline control and failures observable

This step asks whether ordinary shell workflows survive nested control and
input errors. The result determines whether the core execution contract can
carry later pattern features. See pokie-design.md §§4.3, 8–10.

- [ ] 2.2.1. Implement record-level `next` and `exit` with normal finalization.
  - Requires 2.1.3.
  - See pokie-design.md §§4.2–4.3, 10 and ADR 002.
  - Success: nested loops and `finally` produce the specified trace;
    ordinary `break`/`continue` still target user loops.
- [ ] 2.2.2. Implement inline/file CLI invocation and diagnostic translation.
  - Requires 2.2.1.
  - See pokie-design.md §§7–9 and design-contracts.md §4.
  - Success: usage/compile errors return 2, runtime errors return 1,
    output stays on standard output, and spans identify pokie source.
- [ ] 2.2.3. Deliver the baseline CLI interaction suite and runnable guide.
  - Requires 2.2.2.
  - See pokie-design.md §10 and terms-of-reference.md §7.
  - Success: inline/file source, stdin/files, separators, encodings, empty
    input, broken pipes, and failure-after-output exercise the installed
    CLI surface; README status reflects only delivered capabilities.

## 3. Dispatch on regex captures

Idea: structural cases will reduce semantic regex complexity when positional
and named captures have predictable meanings. Falsify it if the corpus requires
regex tricks merely to select an optional or malformed value.

This slice addresses G2 and extends the same record driver.

### 3.1. Recognize text and select one structural case

This step asks whether capture views remain distinct from fields and the whole
record. It informs adapter integration. See pokie-design.md §5.

- [ ] 3.1.1. Add regex predicates, eager regex validation, and `MATCH` access.
  - Requires 2.2.3.
  - See pokie-design.md §§3.2, 5, and 7.
  - Success: capture-free, optional, repeated, named, and zero-length
    matches agree with Python `re`; `$0` remains the record.
- [ ] 3.1.2. Add literals, bindings, wildcards, sequences, and starred patterns.
  - Requires 3.1.1.
  - See pokie-design.md §§5, 10 and design-contracts.md §2.
  - Success: first accepted case runs once; rejected partial matches
    preserve existing names in generated pattern cases.
- [ ] 3.1.3. Add mapping, alternative, `as`, and ordinary class patterns.
  - Requires 3.1.2.
  - See pokie-design.md §5 and design-contracts.md §2.
  - Success: named-view matching, consistent alternative bindings, and
    the supported Python structural subset pass differential examples.

### 3.2. Prove guarded dispatch preserves state

This step asks whether guards can inspect candidates without publishing failed
bindings. It determines whether adapters can reject safely in phase 4. See
pokie-design.md §§5, 10.

- [ ] 3.2.1. Add isolated guard evaluation and binding commit.
  - Requires 3.1.3.
  - See pokie-design.md §§5, 7, and 10; ADR 002.
  - Success: false guards discard candidate names, accepted names persist,
    exceptions propagate, and assignment expressions are diagnosed.
- [ ] 3.2.2. Deliver capture/guard interaction scenarios and published examples.
  - Requires 3.2.1.
  - See pokie-design.md §10 and terms-of-reference.md §7.
  - Success: optional named captures, mapping remainders, Unicode spans,
    f-strings, fallback cases, and subsequent rules have specified output.

## 4. Validate semantic values through adapters

Idea: explicit preserving and converting patterns will reduce conversion
exception glue without concealing user-code defects. Falsify it if extension
registration requires executing unvalidated program code or rejection rules
cannot distinguish bad data from broken adapters.

This slice addresses G3 and tests the proposed extension boundary.

### 4.1. Make built-in adapter outcomes explicit

This step asks whether the result protocol composes with transactional
patterns. Its outcome fixes the catalogue and class-pattern resolution. See
pokie-design.md §6 and ADR 003.

- [ ] 4.1.1. Ratify and implement frozen registry resolution and tagged results.
  - Requires 3.2.2.
  - See pokie-design.md §6, design-contracts.md §3, and ADR 003.
  - Success: registered patterns use stable identities, expression calls
    stay ordinary, and `Match(None/False/0)` remain successes.
- [ ] 4.1.2. Deliver `digits`, `hexstr`, `int`, and `float` adapters.
  - Requires 4.1.1.
  - See pokie-design.md §§6, 10 and design-contracts.md §3.
  - Success: generated subjects verify preservation/conversion, optional
    `None`, signed/Unicode numeric text, float special values, and rejection
    exception boundaries against the declared catalogue.

### 4.2. Demonstrate extensions without weakening compilation

This step asks how users can register adapters before validation without
running a program preamble. It determines whether Q4 can close and which public
interface belongs in the developer guide. See pokie-design.md §6.

- [ ] 4.2.1. Select and record the custom registration mechanism.
  - Requires 4.1.2.
  - See pokie-design.md §6, design-contracts.md §3, and ADR 003.
  - Success: a narrow registration spike exercises discovery, duplicate
    names, qualified names, and phase ordering; ADR 003 records the result.
- [ ] 4.2.2. Deliver the selected public registration interface and examples.
  - Requires 4.2.1.
  - See pokie-design.md §§6–7 and design-contracts.md §3.
  - Success: a custom narrower integer adapter works from the documented
    API; unexpected exceptions fail visibly; guides describe reuse scope.
- [ ] 4.2.3. Deliver adapter/guard/fallback CLI interaction coverage.
  - Requires 4.2.2.
  - See pokie-design.md §10 and design-contracts.md §1.
  - Success: the representative user-record program prints `1 2`;
    side-effect limits, nested inner patterns, and broken extensions have
    separate observable outcomes across inline and file invocation.

## 5. Demonstrate installable library-compatible workflows

Idea: the notation is worth adopting if it works from installed artefacts with
existing libraries and shows a benefit against the user's alternatives. Falsify
it if environment friction or comparative task results erase the value of
compact dispatch.

This phase tests G4/G5 and the success criteria rather than announcing a
release merely because a compiler exists.

### 5.1. Select a reproducible distribution boundary

This step asks which runtime/environment matrix the project can support. Its
evidence closes Q2 and determines public installation instructions. See
pokie-design.md §8 and terms-of-reference.md §§7–9.

- [ ] 5.1.1. Record compatibility and distribution choices in an ADR.
  - Requires 4.2.3.
  - See pokie-design.md §8 and terms-of-reference.md Q2.
  - Success: supported CPython versions, platforms, environment model,
    metadata, and install channels are explicit.
- [ ] 5.1.2. Deliver wheel/sdist packaging and the console entry point.
  - Requires 5.1.1.
  - See pokie-design.md §8 and design-contracts.md §4.
  - Success: clean installation outside the checkout runs corpus programs
    without missing helpers, resources, or source-tree imports.
- [ ] 5.1.3. Deliver the installed-library and CLI combination matrix.
  - Requires 5.1.2.
  - See pokie-design.md §§8, 10.
  - Success: standard, selected pure-Python, and native-extension imports
    work on the declared matrix; mandatory higher-order cases supplement
    pairwise CLI coverage.

### 5.2. Decide whether the language earns continued investment

This step asks whether the success criteria have evidence. Results determine
release claims and which deferred work, if any, deserves promotion. See
terms-of-reference.md §7 and pokie-design.md §10.

- [ ] 5.2.1. Publish reproducible workload and memory measurements.
  - Requires 5.1.3.
  - See pokie-design.md §10 and terms-of-reference.md Q7.
  - Success: equivalent Python/awk baselines, record lengths, match rates,
    and accumulating/non-accumulating modes are reported; unexplained
    record-count-dependent reader retention blocks release.
- [ ] 5.2.2. Record comparative task evidence and update public readiness.
  - Requires 5.2.1 and 1.1.1.
  - See terms-of-reference.md §§7, 9 and pokie-design.md §§1, 11.
  - Success: the owner records release/continue/stop reasoning, remaining
    assumptions, and supported capabilities; published examples execute
    from their Markdown and guides preserve operational instructions.

## 6. Evaluate deferred extensions

Idea: after the core promise has evidence, extensions can be judged by user
value and semantic cost. Falsify it if an extension cannot preserve the core
contracts or lacks a demonstrated job. Completion can mean rejecting an
extension; these tasks do not promise its implementation.

### 6.1. Evaluate richer parsing and pattern composition

This step asks which parsing features justify additional language rules. Its
outcome is a promotion or rejection decision. See pokie-design.md §11.

- [ ] 6.1.1. Decide whether range rules, structured input, or mutable fields
  warrant a scoped RFC.
  - Requires phase 5.
  - See pokie-design.md §11 and terms-of-reference.md Q3.
  - Success: a decision includes single-reader ownership, same-record range
    transitions, and field/record consistency where relevant.
- [ ] 6.1.2. Decide whether more validators, transforms, or composition ship.
  - Requires phase 5.
  - See pokie-design.md §11 and terms-of-reference.md Q6.
  - Success: accepted proposals define representations, rejection,
    reachability, binding compatibility, and evaluation order.

### 6.2. Require evidence for execution and packaging expansion

This step asks whether performance or environment limitations justify a larger
execution/distribution surface. It informs a separate design rather than
silently changing v1. See pokie-design.md §§2, 9–11.

- [ ] 6.2.1. Decide whether Rust acceleration or parallel execution is
      justified.
  - Requires 5.2.1 and 5.2.2.
  - See pokie-design.md §§2, 10–11 and ADR 001.
  - Success: profiles identify a worthwhile target; any proposal includes
    semantic equivalence, ordering/effects, and distribution costs.
- [ ] 6.2.2. Decide whether dependency management or isolated execution belongs
  in a separate product scope.
  - Requires 5.2.2.
  - See pokie-design.md §§8–9, 11 and terms-of-reference.md §6.2.
  - Success: unmet needs and new trust/environment boundaries are explicit;
    absent evidence, existing Python tools remain the recommendation.
