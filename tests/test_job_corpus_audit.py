"""Composition and reference-diagnostic checks for the pure audit API."""

import dataclasses

import pytest
from job_corpus import audit, findings, model


@dataclasses.dataclass(frozen=True, slots=True)
class FixedRunner:
    """A port implementation returning one controlled outcome."""

    outcome: model.ObservedOutcome

    def run(
        self, implementation: model.ScriptImplementation, case: model.JobCase
    ) -> model.ObservedOutcome:
        """Return the controlled observation; no subprocess is involved.

        Returns
        -------
        model.ObservedOutcome
            The controlled outcome.
        """
        del implementation, case
        return self.outcome


def test_audit_orders_findings_without_conflating_them_with_verdict() -> None:
    """Missing evidence is actionable even without a contract contradiction."""
    report = audit.audit_corpus((), (), (), "")
    assert report.verdict is findings.Verdict.PROCEED, (
        "an empty corpus has no contradiction and must retain the proceed verdict"
    )
    assert {error.kind for error in report.findings} == {
        findings.FindingKind.COVERAGE,
        findings.FindingKind.REGISTER,
    }, "an empty corpus must report only coverage and register defects"
    keys = [(error.kind, error.subject, error.message) for error in report.findings]
    assert keys == sorted(keys), "findings must be sorted by kind, subject, and message"


@pytest.mark.parametrize(
    ("failure", "stderr", "valid"),
    [
        (model.Failure.NONE, b"", True),
        (model.Failure.NONE, b"noise", False),
        (model.Failure.INPUT, b"input error: invalid UTF-8", True),
        (model.Failure.INPUT, b"NameError: crash", False),
    ],
)
def test_reference_cannot_pass_by_crashing_with_matching_status(
    reference_implementation: tuple[model.CorpusJob, model.ScriptImplementation],
    failure: model.Failure,
    stderr: bytes,
    *,
    valid: bool,
) -> None:
    """Reference diagnostics must name the specified failure category."""
    job, implementation = reference_implementation
    expected = model.ExpectedOutcome(
        b"", 0 if failure is model.Failure.NONE else 1, failure
    )
    case = dataclasses.replace(job.cases[0], expected=expected)
    observed = model.ObservedOutcome(b"", stderr, expected.exit_status)
    result = audit.verify_case(job, implementation, case, FixedRunner(observed))
    assert bool(result.findings) is not valid, (
        "diagnostic findings must agree with the specified stderr validity"
    )
    assert result.job_id == job.job_id, (
        "the result must retain the containing job identifier"
    )
    assert result.case_id == case.case_id, (
        "the result must retain the input case identifier"
    )
    assert result.observed == observed, (
        "the result must retain the exact observed outcome"
    )
    assert result.agreement is findings.Agreement.AGREED, (
        "stdout and status agreement is separate from reference stderr validity"
    )


def test_bad_outcome_names_expected_and_observed_bytes(
    reference_implementation: tuple[model.CorpusJob, model.ScriptImplementation],
) -> None:
    """A failing oracle provides enough evidence to diagnose the mismatch."""
    job, implementation = reference_implementation
    case = job.cases[0]
    observed = model.ObservedOutcome(
        case.expected.stdout + b"unexpected", b"", case.expected.exit_status
    )
    result = audit.verify_case(job, implementation, case, FixedRunner(observed))
    assert result.findings[0].kind is findings.FindingKind.OUTCOME, (
        "a mismatch must identify the outcome and expected/observed bytes"
    )
    assert f"expected {case.expected.stdout!r}" in result.findings[0].message, (
        "the diagnostic must preserve the specified output bytes"
    )
    assert f"observed {observed.stdout!r}" in result.findings[0].message, (
        "the diagnostic must preserve the observed output bytes"
    )
