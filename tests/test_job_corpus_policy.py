"""Finite policy controls independent of the committed corpus inventory."""

import dataclasses
import typing as typ

import pytest
from job_corpus import findings, model, policy


def test_empty_corpus_reports_every_coverage_obligation() -> None:
    """An empty collection cannot pass the roadmap's coverage criterion."""
    gaps = policy.find_coverage_gaps(())
    why = "an empty corpus must report every missing category and tag"
    assert {gap.subject for gap in gaps} == {
        *(f"category/{category}" for category in model.JobCategory),
        *(f"tag/{tag}" for tag in model.CaseTag),
    }, why
    why = "every empty-corpus finding must have the coverage kind"
    assert all(gap.kind is findings.FindingKind.COVERAGE for gap in gaps), why


def test_identity_checks_repeated_jobs_and_case_names(
    repository_jobs: tuple[model.CorpusJob, ...],
) -> None:
    """Repeated IDs must be diagnosed before they collapse into lookup maps."""
    job = repository_jobs[0]
    observation = model.Observation(
        "OBS-99", model.ObservationKind.AMBIGUITY, (), (), "Synthetic duplicate control"
    )
    repeated = dataclasses.replace(
        job, cases=(job.cases[0], job.cases[0]), observations=(observation,)
    )
    messages = [
        error.message for error in policy.find_identity_errors((repeated, repeated))
    ]
    why = "repeated job, case, and observation identities must all be reported"
    assert set(messages) >= {
        "duplicate job",
        f"duplicate case {job.cases[0].case_id}",
        "duplicate observation",
    }, why


@pytest.mark.parametrize("failure", list(model.Failure))
@pytest.mark.parametrize("status", [0, 1, 2])
def test_failure_categories_follow_cli_status_table(
    repository_jobs: tuple[model.CorpusJob, ...], failure: model.Failure, status: int
) -> None:
    """Every failure/status pairing is checked against DC-4's independent table."""
    job = repository_jobs[0]
    expected = model.ExpectedOutcome(b"", status, failure)
    case = dataclasses.replace(job.cases[0], expected=expected)
    job = dataclasses.replace(job, cases=(case,))
    required = expected_failure_status(failure)
    why = "the failure category must agree with the DC-4 exit status"
    assert bool(policy.find_failure_mismatches((job,))) is (status != required), why


def expected_failure_status(failure: model.Failure) -> int:
    """Apply DC-4's independent table; for example, static failures use status 2.

    Returns
    -------
    int
        The status required by the specified failure category.
    """
    match failure:
        case model.Failure.NONE:
            return 0
        case model.Failure.STATIC:
            return 2
        case _:
            return 1


def register_row(question: model.QuestionId) -> model.RegisterEntry:
    """Build a valid policy row; for example Q1 decides before its sole gate.

    Returns
    -------
    model.RegisterEntry
        A valid decision row.
    """
    return model.RegisterEntry(
        question, "@leynos", ("1.1.1",), "1.1.2", ("1.1.2",), ("none",)
    )


@pytest.mark.parametrize("evidence_tasks", [("1.1.1",), ("gap",)])
def test_register_requires_exact_question_inventory(
    evidence_tasks: tuple[str, ...],
) -> None:
    """Q5 cannot disappear or occur twice, and unknown Q9 is rejected."""
    rows = tuple(
        dataclasses.replace(register_row(question), evidence_tasks=evidence_tasks)
        for question in model.QuestionId
    )
    tasks = ("1.1.1", "1.1.2")
    why = "the complete unique question inventory must be accepted"
    assert not policy.find_register_gaps(rows, tasks), why
    why = "missing Q5 must be reported"
    assert any(
        error.subject == "Q5"
        for error in policy.find_register_gaps(rows[:4] + rows[5:], tasks)
    ), why
    why = "duplicate Q5 must be reported"
    assert any(
        error.message == "duplicate question"
        for error in policy.find_register_gaps((*rows, rows[4]), tasks)
    ), why
    unknown = dataclasses.replace(rows[0], question=typ.cast("model.QuestionId", "Q9"))
    why = "unknown Q9 must be reported"
    assert any(
        error.message == "unknown question"
        for error in policy.find_register_gaps((unknown,), tasks)
    ), why


@pytest.mark.parametrize("owner", ["", " ", "TBD", "unassigned", "-"])
def test_register_rejects_placeholder_owners(owner: str) -> None:
    """An accountable owner must be more than a placeholder spelling."""
    row = dataclasses.replace(register_row(model.QuestionId.Q1), owner=owner)
    why = "placeholder text cannot identify an accountable owner"
    assert any(
        "owner" in error.message
        for error in policy.find_register_gaps((row,), ("1.1.1", "1.1.2"))
    ), why


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"evidence_tasks": ("9.9.9",)}, "unknown task 9.9.9"),
        ({"decide_before": "1.1.3"}, "decision deadline follows a gate"),
        ({"gates": ("gap",)}, "gap is allowed only in evidence tasks"),
        ({"decide_before": "gap"}, "gap is allowed only in evidence tasks"),
        ({"evidence_tasks": ()}, "evidence tasks are empty"),
        ({"gates": ()}, "gates are empty"),
    ],
)
def test_register_deadlines_and_references_are_actionable(
    changes: dict[str, object], message: str
) -> None:
    """A row must name real evidence and decide before its earliest gate."""
    row = dataclasses.replace(register_row(model.QuestionId.Q1), **changes)
    errors = policy.find_register_gaps((row,), ("1.1.1", "1.1.2", "1.1.3"))
    why = "register deadlines and references must be actionable roadmap entries"
    assert message in {error.message for error in errors}, why


@pytest.mark.parametrize("use_all_token", [True, False])
def test_register_evidence_matches_jobs(
    repository_jobs: tuple[model.CorpusJob, ...], *, use_all_token: bool
) -> None:
    """Explicit evidence names Q1 jobs; all is valid only when every job bears on Q1."""
    bearing = tuple(
        job.job_id for job in repository_jobs if model.QuestionId.Q1 in job.decisions
    )
    evidence = ("all",) if use_all_token else bearing
    row = dataclasses.replace(
        register_row(model.QuestionId.Q1), corpus_evidence=evidence
    )
    mismatches = policy.find_evidence_mismatches(repository_jobs, (row,))
    should_mismatch = use_all_token and set(bearing) != {
        job.job_id for job in repository_jobs
    }
    assert bool(mismatches) is should_mismatch, "all must expand to every loaded job"
    unknown = max(job.job_id for job in repository_jobs) + "-missing"
    wrong_cases = [(unknown,), ("all", unknown)]
    if bearing:
        wrong_cases.append(("none",))
    for wrong in wrong_cases:
        row = dataclasses.replace(row, corpus_evidence=wrong)
        why = "unknown evidence must not satisfy the question's exact job set"
        assert policy.find_evidence_mismatches(repository_jobs, (row,)), why


def test_observations_are_documented_and_belong_to_job_questions(
    repository_jobs: tuple[model.CorpusJob, ...],
) -> None:
    """Whole IDs and question containment prevent misleading trace links."""
    job = repository_jobs[0]
    observation = model.Observation(
        "OBS-99",
        model.ObservationKind.AMBIGUITY,
        (),
        (model.QuestionId.Q8,),
        "Synthetic trace control",
    )
    job = dataclasses.replace(
        job, decisions=(model.QuestionId.Q1,), observations=(observation,)
    )
    why = "an observation outside its job decisions must be reported"
    assert policy.find_evidence_mismatches((job,), ()), why
    why = "the exact observation identifier must count as documented"
    assert not policy.find_undocumented_observations((job,), "OBS-99"), why
    why = "a longer identifier must not document the shorter observation"
    assert policy.find_undocumented_observations((job,), "OBS-990"), why


def test_reference_divergences_produce_one_finding_per_implementation(
    reference_implementation: tuple[model.CorpusJob, model.ScriptImplementation],
) -> None:
    """An invalid reference declaration should not repeat the same diagnostic."""
    job, reference = reference_implementation
    first = job.cases[0]
    cases = (first, dataclasses.replace(first, case_id=first.case_id + "-second"))
    job = dataclasses.replace(job, cases=cases)
    reference = dataclasses.replace(
        reference,
        divergences=tuple(
            model.Divergence(case.case_id, "unsupported") for case in job.cases
        ),
    )
    job = dataclasses.replace(job, alternatives=(reference,))
    errors = policy.find_identity_errors((job,))
    why = "reference declarations must produce exactly one actionable diagnostic"
    assert [error.message for error in errors] == [
        "reference cannot declare divergences"
    ], why


def test_duplicate_divergences_identify_the_script_and_case(
    reference_implementation: tuple[model.CorpusJob, model.ScriptImplementation],
) -> None:
    """Repeated valid declarations remain actionable instead of collapsing."""
    job, reference = reference_implementation
    case_id = job.cases[0].case_id
    declaration = model.Divergence(case_id, "deliberate alternative semantics")
    alternative = dataclasses.replace(
        reference,
        kind=model.ScriptKind.AWK,
        divergences=(declaration, declaration),
    )
    job = dataclasses.replace(job, alternatives=(reference, alternative))
    expected = findings.Finding(
        findings.FindingKind.IDENTITY,
        str(alternative.path),
        f"duplicate divergence {case_id}",
    )
    why = "a repeated valid declaration must produce exactly its duplicate finding"
    assert policy.find_identity_errors((job,)) == (expected,), why


def test_divergence_defects_are_independently_actionable(
    reference_implementation: tuple[model.CorpusJob, model.ScriptImplementation],
) -> None:
    """Each malformed script and each defect need a distinct actionable finding."""
    job, reference = reference_implementation
    unknown = max(case.case_id for case in job.cases) + "-missing"
    first = dataclasses.replace(
        reference,
        kind=model.ScriptKind.AWK,
        path=reference.path.with_name("first.awk"),
        divergences=(model.Divergence(unknown, " "),),
    )
    second = dataclasses.replace(first, path=reference.path.with_name("second.awk"))
    job = dataclasses.replace(job, alternatives=(reference, first, second))
    errors = policy.find_identity_errors((job,))
    expected_messages = {
        f"divergence names unknown case {unknown}",
        f"divergence {unknown} has no reason",
    }
    why = "each script and divergence defect must identify its own correction"
    assert {(error.subject, error.message) for error in errors} == {
        (str(script.path), message)
        for script in (first, second)
        for message in expected_messages
    }, why


@pytest.mark.parametrize("evidence", [("none",), ()])
def test_empty_question_evidence_is_explicitly_representable(
    repository_jobs: tuple[model.CorpusJob, ...], evidence: tuple[str, ...]
) -> None:
    """A question with no bearing jobs accepts the empty set and its none token."""
    jobs = tuple(
        dataclasses.replace(job, decisions=(), observations=())
        for job in repository_jobs
    )
    row = dataclasses.replace(
        register_row(model.QuestionId.Q1), corpus_evidence=evidence
    )
    why = "none and an empty inventory must represent exactly zero bearing jobs"
    assert not policy.find_evidence_mismatches(jobs, (row,)), why


@pytest.mark.parametrize("reference_count", [0, 2])
def test_job_requires_exactly_one_reference(
    reference_implementation: tuple[model.CorpusJob, model.ScriptImplementation],
    reference_count: int,
) -> None:
    """An absent or ambiguous oracle cannot supply a job's evidence."""
    job, reference = reference_implementation
    job = dataclasses.replace(job, alternatives=(reference,) * reference_count)
    errors = policy.find_identity_errors((job,))
    why = "zero and multiple reference implementations must each be rejected"
    assert [error.message for error in errors] == [
        "expected exactly one reference implementation"
    ], why


@pytest.mark.parametrize("evidence_tasks", [("1.1.1",), ("gap",)])
@pytest.mark.parametrize("placement", ["deadline", "gate"])
def test_misplaced_gap_has_one_stable_diagnostic(
    evidence_tasks: tuple[str, ...], placement: str
) -> None:
    """Misplacing the reserved token has one cause regardless of evidence cells."""
    row = dataclasses.replace(
        register_row(model.QuestionId.Q1),
        evidence_tasks=evidence_tasks,
        decide_before="gap" if placement == "deadline" else "1.1.2",
        gates=("gap",) if placement == "gate" else ("1.1.2",),
    )
    errors = policy.find_register_gaps((row,), ("1.1.1", "1.1.2"))
    why = (
        "a misplaced gap must have one placement finding, never an unknown-task finding"
    )
    assert [error.message for error in errors if error.subject == row.question] == [
        "gap is allowed only in evidence tasks"
    ], why
