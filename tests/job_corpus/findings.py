"""Pure audit results shared by policy, comparison, and report rendering.

These values describe corpus evidence; they are not product diagnostics and
must not become a general application validation framework.
"""

import dataclasses
import enum
import typing as typ

if typ.TYPE_CHECKING:
    from job_corpus import model


class FindingKind(enum.StrEnum):
    """The independently actionable defects in corpus evidence."""

    COVERAGE = "coverage"
    IDENTITY = "identity"
    FAILURE = "failure"
    REGISTER = "register"
    EVIDENCE = "evidence"
    OBSERVATION = "observation"
    OUTCOME = "outcome"


class Agreement(enum.StrEnum):
    """Whether an implementation supports its declared oracle relationship."""

    AGREED = "agreed"
    DECLARED_DIVERGENCE = "declared-divergence"
    UNEXPECTED_DIFFERENCE = "unexpected-difference"
    STALE_DIVERGENCE = "stale-divergence"


class Verdict(enum.StrEnum):
    """Whether the proposed contracts survive the corpus specification."""

    PROCEED = "proceed"
    REVISE_CONTRACTS = "revise-contracts"


@dataclasses.dataclass(frozen=True, slots=True)
class Finding:
    """One defect, identified by a stable corpus-relative subject."""

    kind: FindingKind
    subject: str
    message: str


@dataclasses.dataclass(frozen=True, slots=True)
class CaseResult:
    """An implementation's observed outcome and comparison classification."""

    job_id: str
    case_id: str
    agreement: Agreement
    observed: model.ObservedOutcome
    findings: tuple[Finding, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class AuditReport:
    """Deterministically ordered findings and the separate contract verdict."""

    findings: tuple[Finding, ...]
    verdict: Verdict
