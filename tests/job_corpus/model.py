"""Corpus domain types.

Every value the harness reasons about is a frozen dataclass or a `StrEnum`
member, so policy functions can take values rather than files and stay pure.
The types mirror the `job.toml` schema documented in ADR 0004; the loader in
`job_corpus.adapters.toml_jobs` is the only place a document becomes these
values.
"""

import dataclasses
import enum
import typing as typ

if typ.TYPE_CHECKING:
    import pathlib

type Alternative = ScriptImplementation | DescribedAlternative


class Failure(enum.StrEnum):
    """Failure category of an observed or expected run.

    The members mirror `docs/design-contracts.md` §4 Table 2. `NONE` implies
    exit status 0, `STATIC` implies 2, and every other member implies 1.
    """

    NONE = "none"
    STATIC = "static"
    INITIALIZATION = "initialization"
    INPUT = "input"
    GUARD = "guard"
    ADAPTER = "adapter"
    ACTION = "action"
    END = "end"
    BROKEN_PIPE = "broken-pipe"


class JobCategory(enum.StrEnum):
    """The three job kinds roadmap task 1.1.1 must cover."""

    FILTERING = "filtering"
    CAPTURE_VALIDATION = "capture-validation"
    AGGREGATION = "aggregation"


class QuestionId(enum.StrEnum):
    """An open question from `docs/terms-of-reference.md` §9 Table 5."""

    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
    Q5 = "Q5"
    Q6 = "Q6"
    Q7 = "Q7"
    Q8 = "Q8"


class CaseTag(enum.StrEnum):
    """A property a case exercises, used to prove coverage is not vacuous."""

    MALFORMED_RECORD = "malformed-record"
    GUARD_REJECTION = "guard-rejection"
    ADAPTER_REJECTION = "adapter-rejection"
    PRESERVED_TEXT = "preserved-text"
    OPTIONAL_CAPTURE = "optional-capture"
    BINDING_ISOLATION = "binding-isolation"
    EMPTY_INPUT = "empty-input"
    EMPTY_FIELD = "empty-field"
    OUT_OF_RANGE_FIELD = "out-of-range-field"
    UNTERMINATED_FINAL_LINE = "unterminated-final-line"
    INPUT_FAILURE = "input-failure"
    EARLY_EXIT = "early-exit"
    STDIN = "stdin"
    NEXT_RECORD = "next-record"
    MULTIPLE_RULES = "multiple-rules"
    MULTIPLE_FILES = "multiple-files"
    UNICODE = "unicode"


class ScriptKind(enum.StrEnum):
    """The implementations a case can be run against.

    `REFERENCE` is the oracle: it deliberately models proposed pokie
    semantics. `POKIE` is reserved for roadmap task 2.1.3 and has no script
    yet, which is why no corpus job declares it.
    """

    REFERENCE = "reference"
    AWK = "awk"
    SHELL = "shell"
    POKIE = "pokie"


class DescribedKind(enum.StrEnum):
    """A named alternative that exists only as prose."""

    STATUS_QUO = "status-quo"
    PRIOR_ART = "prior-art"


class Comparison(enum.StrEnum):
    """How an alternative's standard output is compared with the expected.

    `SORTED_LINES` exists because POSIX leaves `for (key in array)` order
    unspecified, so an awk aggregation cannot promise a line order.
    """

    EXACT = "exact"
    SORTED_LINES = "sorted-lines"


class ObservationKind(enum.StrEnum):
    """Why an observation was recorded against the corpus.

    `CONTRADICTION` is the falsification output of phase 1: it flips the audit
    verdict to `revise-contracts` and blocks ratification.
    """

    CONTRADICTION = "contradiction"
    AMBIGUITY = "ambiguity"
    ERGONOMIC_SMELL = "ergonomic-smell"
    HOST_DIVERGENCE = "host-divergence"


class EvidenceStatus(enum.StrEnum):
    """The status vocabulary of `docs/context.md` §1."""

    ESTABLISHED = "Established"
    AGREED_BASIS = "Agreed basis"
    ASSUMPTION = "Assumption"
    PROPOSED_CONTRACT = "Proposed contract"
    OPEN_QUESTION = "Open question"
    DEFERRED = "Deferred"


@dataclasses.dataclass(frozen=True, slots=True)
class InputFile:
    """One input the runner materializes before starting an implementation.

    The content is written verbatim, with no newline normalization.
    """

    name: str
    """The operand name the program sees, such as ``app.log``."""

    content: bytes
    """The exact bytes written."""


@dataclasses.dataclass(frozen=True, slots=True)
class ExpectedOutcome:
    """The specified result of running a program over a case's inputs."""

    stdout: bytes
    """The exact expected standard output."""

    exit_status: int
    """The expected process exit status."""

    failure: Failure
    """The failure category the outcome demonstrates."""


@dataclasses.dataclass(frozen=True, slots=True)
class ObservedOutcome:
    """What an implementation actually did, as the runner reported it."""

    stdout: bytes
    """Captured standard output."""

    stderr: bytes
    """Captured standard error."""

    exit_status: int
    """The process exit status; meaningless when ``timed_out`` is true."""

    timed_out: bool = False
    """Whether the implementation exceeded the runner's time limit."""


@dataclasses.dataclass(frozen=True, slots=True)
class Divergence:
    """A case where an alternative is expected to disagree with the oracle.

    A declaration is a claim, not an excuse: the alternative tests fail when a
    declared divergence agrees, so a stale declaration cannot hide a wrong
    expectation.
    """

    case_id: str
    """The case the alternative is expected to differ on."""

    reason: str
    """Why the difference is inherent to the alternative's language."""


@dataclasses.dataclass(frozen=True, slots=True)
class ScriptImplementation:
    """An executable implementation of a job."""

    kind: ScriptKind
    """Which language the script is written in."""

    path: pathlib.PurePosixPath
    """The script's path, relative to the corpus root."""

    args: tuple[str, ...] = ()
    """Fixed arguments inserted before the script and its operands."""

    comparison: Comparison = Comparison.EXACT
    """How its output is compared with the expected outcome."""

    divergences: tuple[Divergence, ...] = ()
    """Cases where it is expected to disagree with the oracle."""


@dataclasses.dataclass(frozen=True, slots=True)
class DescribedAlternative:
    """An alternative the corpus names but does not execute.

    Users' existing workarounds, and prior art such as PAWK, are recorded as
    prose: reproducing them would need their own runtimes, and the comparison
    roadmap task 5.2.2 makes is a task observation, not a script diff.
    """

    kind: DescribedKind
    """Whether this is the status quo or prior art."""

    tool: str
    """The named tool, empty for an unnamed status quo."""

    description: str
    """How the same job would be done with that alternative."""


@dataclasses.dataclass(frozen=True, slots=True)
class JobCase:
    """One input and outcome pair a job's programs must reproduce."""

    case_id: str
    """The identifier used in test parameters and divergence declarations."""

    tags: tuple[CaseTag, ...]
    """The properties this case exercises."""

    operands: tuple[str, ...]
    """Operand names passed to the program; ``-`` means standard input."""

    inputs: tuple[InputFile, ...]
    """The files the runner materializes for the operands."""

    expected: ExpectedOutcome
    """The specified outcome."""

    earliest_task: str
    """The earliest roadmap task that could satisfy this case."""


@dataclasses.dataclass(frozen=True, slots=True)
class ProposedProgram:
    """A pokie program that is specified but not executable.

    No interpreter exists, so every program in the corpus is a proposal. The
    path is recorded so `docs/job-corpus.md` can link to the real file rather
    than copying it.
    """

    path: pathlib.PurePosixPath
    """The program's path, relative to the corpus root."""

    args: tuple[str, ...] = ()
    """Command-line options the program would need, such as ``-F,``."""


@dataclasses.dataclass(frozen=True, slots=True)
class Observation:
    """A tension between the corpus and a proposed contract."""

    observation_id: str
    """The stable ``OBS-nn`` identifier `docs/job-corpus.md` must mention."""

    kind: ObservationKind
    """What sort of tension this is."""

    contracts: tuple[str, ...]
    """The contract identifiers it bears on, such as ``DC-1``."""

    questions: tuple[QuestionId, ...]
    """The open questions it supplies evidence for."""

    summary: str
    """One sentence describing the tension."""


@dataclasses.dataclass(frozen=True, slots=True)
class CorpusJob:
    """One representative job, with everything needed to validate it."""

    job_id: str
    """The directory name under ``job_corpus/jobs/``."""

    title: str
    """One line describing the job."""

    category: JobCategory
    """Which of the three job kinds this demonstrates."""

    goals: tuple[str, ...]
    """The product goals from `docs/terms-of-reference.md` §6.1."""

    decisions: tuple[QuestionId, ...]
    """The open questions this job supplies evidence for."""

    contracts: tuple[str, ...]
    """The contract identifiers the job exercises."""

    evidence_status: EvidenceStatus
    """How well evidenced the job's provenance is."""

    provenance: tuple[str, ...]
    """Where the job came from: a document section or ``synthetic``."""

    program: ProposedProgram
    """The proposed pokie program, which no interpreter can run yet."""

    alternatives: tuple[Alternative, ...]
    """Implementations compared against the expected outcomes."""

    cases: tuple[JobCase, ...]
    """The input and outcome pairs."""

    observations: tuple[Observation, ...] = ()
    """Contract tensions recorded while specifying the job."""


@dataclasses.dataclass(frozen=True, slots=True)
class RegisterEntry:
    """One row of the decision register."""

    question: QuestionId
    """The open question the row governs."""

    owner: str
    """The role accountable for the decision."""

    evidence_tasks: tuple[str, ...]
    """Roadmap tasks that produce the evidence, or the token ``gap``."""

    decide_before: str
    """The roadmap task that cannot start until the decision is made."""

    gates: tuple[str, ...]
    """The roadmap tasks whose delivery the decision gates."""

    corpus_evidence: tuple[str, ...]
    """Job identifiers supplying evidence, or ``all`` or ``none``."""
