"""Compose pure corpus policy and explicit case verification.

The audit accepts loaded values; orchestration code owns file reads and child
processes through the existing ProgramRunner port.
"""

import typing as typ

from job_corpus import comparison, findings, model, policy

if typ.TYPE_CHECKING:
    import collections.abc as cabc

    from job_corpus.ports import ProgramRunner


def audit_corpus(
    jobs: cabc.Sequence[model.CorpusJob],
    register: cabc.Sequence[model.RegisterEntry],
    task_ids: cabc.Sequence[str],
    findings_text: str,
) -> findings.AuditReport:
    """Audit loaded evidence in stable kind/subject/message order.

    For example, an empty corpus returns coverage and missing-question
    findings even though its contradiction verdict is ``proceed``.

    Returns
    -------
    findings.AuditReport
        Ordered findings and the separate contract verdict.
    """
    errors = (
        *policy.find_coverage_gaps(jobs),
        *policy.find_identity_errors(jobs),
        *policy.find_failure_mismatches(jobs),
        *policy.find_register_gaps(register, task_ids),
        *policy.find_evidence_mismatches(jobs, register),
        *policy.find_undocumented_observations(jobs, findings_text),
    )
    ordered = tuple(
        sorted(errors, key=lambda error: (error.kind, error.subject, error.message))
    )
    return findings.AuditReport(ordered, policy.derive_verdict(jobs))


def verify_case(
    job: model.CorpusJob,
    implementation: model.ScriptImplementation,
    case: model.JobCase,
    runner: ProgramRunner,
) -> findings.CaseResult:
    """Run one case and preserve both its observation and comparison findings.

    For example, a reference crash on an expected input error is rejected
    unless stderr starts with ``input error:`` and stdout/status agree.

    Returns
    -------
    findings.CaseResult
        The observation, classification, and diagnostic findings.
    """
    observed = runner.run(implementation, case)
    agreement = comparison.evaluate_agreement(implementation, case, observed)
    errors = []
    if agreement in {
        findings.Agreement.UNEXPECTED_DIFFERENCE,
        findings.Agreement.STALE_DIVERGENCE,
    }:
        errors.append(
            findings.Finding(
                findings.FindingKind.OUTCOME,
                f"{job.job_id}/{case.case_id}",
                f"{implementation.path}: {agreement}; "
                f"expected {case.expected.stdout!r} "
                f"and status {case.expected.exit_status}; observed {observed.stdout!r} "
                f"and status {observed.exit_status}; timed out {observed.timed_out}",
            )
        )
    if implementation.kind is model.ScriptKind.REFERENCE:
        errors.extend(_reference_diagnostics(job, case, observed))
    return findings.CaseResult(
        job.job_id, case.case_id, agreement, observed, tuple(errors)
    )


def _reference_diagnostics(
    job: model.CorpusJob, case: model.JobCase, observed: model.ObservedOutcome
) -> tuple[findings.Finding, ...]:
    """Check reference stderr; for example, a success must emit no diagnostic.

    Returns
    -------
    tuple[findings.Finding, ...]
        The findings for the supplied evidence.
    """
    if case.expected.failure is model.Failure.NONE:
        valid = observed.stderr == b""
    else:
        valid = observed.stderr.startswith(f"{case.expected.failure} error:".encode())
    if valid:
        return ()
    return (
        findings.Finding(
            findings.FindingKind.OUTCOME,
            f"{job.job_id}/{case.case_id}",
            f"invalid reference diagnostic {observed.stderr!r}",
        ),
    )
