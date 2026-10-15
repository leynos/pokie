"""End-to-end tests that run the corpus against its expected outcomes.

Every parameter comes from the committed corpus rather than from this module,
so a job's outcome is specified once, in `job.toml`, and this module only
reports what actually happened.
"""

import dataclasses
import os
import pathlib

import pytest
from job_corpus import model
from job_corpus.adapters import process_runner, toml_jobs

CORPUS_ROOT = pathlib.Path(__file__).resolve().parent / "job_corpus"

JOBS = toml_jobs.load_jobs(CORPUS_ROOT)

_SCRIPTS = [
    (job, case, implementation)
    for job in JOBS
    for case in job.cases
    for implementation in job.alternatives
    if isinstance(implementation, model.ScriptImplementation)
]

REFERENCE_RUNS = [
    pytest.param(job, case, implementation, id=f"{job.job_id}/{case.case_id}")
    for job, case, implementation in _SCRIPTS
    if implementation.kind is model.ScriptKind.REFERENCE
]

ALTERNATIVE_RUNS = [
    pytest.param(
        job,
        case,
        implementation,
        id=f"{job.job_id}/{case.case_id}/{implementation.kind}",
    )
    for job, case, implementation in _SCRIPTS
    if implementation.kind is not model.ScriptKind.REFERENCE
]

EXPECTED_CASE_COUNT = 2
"""Every case the corpus must hold. Raised as jobs land, ending at the plan's 18."""

EXPECTED_JOB_COUNT = 1
"""Every job the corpus must hold. Raised as jobs land, ending at the plan's 11."""

EXPECTED_CATEGORIES = {model.JobCategory.CAPTURE_VALIDATION}
"""Every category the corpus must cover; all three once EP-M3 lands its jobs."""

REQUIRED_TAGS = {
    model.CaseTag.MALFORMED_RECORD,
    model.CaseTag.GUARD_REJECTION,
    model.CaseTag.ADAPTER_REJECTION,
    model.CaseTag.UNICODE,
}


def describe(outcome: model.ObservedOutcome) -> str:
    """Return a bounded description of a run, for an assertion message.

    Parameters
    ----------
    outcome : model.ObservedOutcome
        The run to describe.

    Returns
    -------
    str
        The timeout flag, or the status and captured bytes.
    """
    if outcome.timed_out:
        return "timed out"
    return (
        f"status {outcome.exit_status}, "
        f"stdout {outcome.stdout!r}, stderr {outcome.stderr!r}"
    )


def test_corpus_is_non_vacuous() -> None:
    """The corpus must hold exactly the planned inventory.

    An equality, not a lower bound: a case added to ``job.toml`` without being
    accounted for here would otherwise pass unnoticed, and so would a case the
    loader silently dropped. Every other test in this module is parameterized
    over the corpus, so if the corpus empties, they all become passes rather
    than failures, and this test is what notices.
    """
    categories = {job.category for job in JOBS}
    tags = {tag for _, case, _ in _SCRIPTS for tag in case.tags}
    why = (
        f"the corpus must hold {EXPECTED_JOB_COUNT} job(s) and "
        f"{EXPECTED_CASE_COUNT} case(s); found {len(JOBS)} job(s) and "
        f"{len(REFERENCE_RUNS)} case(s)"
    )
    assert len(JOBS) == EXPECTED_JOB_COUNT, why
    assert len(REFERENCE_RUNS) == EXPECTED_CASE_COUNT, why
    assert categories == EXPECTED_CATEGORIES, why
    assert tags >= REQUIRED_TAGS, (
        f"every planned tag needs a case; missing {REQUIRED_TAGS - tags}"
    )


@pytest.mark.parametrize(("job", "case", "implementation"), REFERENCE_RUNS)
def test_reference_reproduces_expected(
    job: model.CorpusJob,
    case: model.JobCase,
    implementation: model.ScriptImplementation,
    process_runner_instance: process_runner.ProcessRunner,
) -> None:
    """The reference oracle must produce exactly the outcome the corpus specifies.

    The standard error is checked too, so the oracle cannot pass by crashing on
    a case that expects an ordinary result: an expected failure must announce
    itself with the failure category's prefix.

    The oracle runs with no awk available. It models proposed pokie semantics
    in pure Python, so a run that needed awk would be a defect in the corpus
    rather than a missing dependency, and this makes that defect an
    ``EvidenceFormatError`` instead of a silently different result.
    """
    runner = dataclasses.replace(process_runner_instance, awk_executable=None)
    outcome = runner.run(implementation, case)
    why = (
        f"{job.job_id}/{case.case_id}: expected {case.expected.stdout!r} and "
        f"status {case.expected.exit_status}; observed {describe(outcome)}"
    )
    assert outcome.stdout == case.expected.stdout, why
    assert outcome.exit_status == case.expected.exit_status, why
    if case.expected.failure is model.Failure.NONE:
        assert outcome.stderr == b"", why
    else:
        assert outcome.stderr.startswith(f"{case.expected.failure} error:".encode()), (
            why
        )


@pytest.mark.parametrize(("job", "case", "implementation"), ALTERNATIVE_RUNS)
def test_alternative_agrees_or_declares_divergence(
    job: model.CorpusJob,
    case: model.JobCase,
    implementation: model.ScriptImplementation,
    process_runner_instance: process_runner.ProcessRunner,
) -> None:
    """An alternative must agree unless it declares a divergence on that case.

    The second half matters as much as the first: a declaration whose case now
    agrees is stale, and a stale declaration would otherwise hide a mistaken
    expectation.

    The awk this skip reasons about is read off the very runner that would
    start it, so the precondition and the run cannot disagree about which
    interpreter is under test.
    """
    if (
        implementation.kind is model.ScriptKind.AWK
        and process_runner_instance.awk_executable is None
    ):
        if os.environ.get("CI"):
            pytest.fail(f"{job.job_id}: awk is required in continuous integration")
        pytest.skip("awk not on PATH")
    outcome = process_runner_instance.run(implementation, case)
    declared = {divergence.case_id for divergence in implementation.divergences}
    if case.case_id in declared:
        why = (
            f"{job.job_id}/{case.case_id}: {implementation.path} declares a "
            f"divergence that no longer holds: {describe(outcome)}"
        )
        assert outcome.stdout != case.expected.stdout, why
        return
    why = (
        f"{job.job_id}/{case.case_id}: {implementation.path} produced "
        f"{describe(outcome)}, expected {case.expected.stdout!r} with status "
        f"{case.expected.exit_status}"
    )
    assert outcome.stdout == case.expected.stdout, why
    assert outcome.exit_status == case.expected.exit_status, why
