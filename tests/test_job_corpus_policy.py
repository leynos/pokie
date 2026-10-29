"""Finite policy controls independent of the committed corpus inventory."""

import dataclasses
import typing as typ

import pytest
from job_corpus import findings, model, policy


def test_empty_corpus_reports_every_coverage_obligation() -> None:
    """An empty collection cannot pass the roadmap's coverage criterion."""
    gaps = policy.find_coverage_gaps(())
    assert {gap.subject for gap in gaps} == {
        *(f"category/{category}" for category in model.JobCategory),
        *(f"tag/{tag}" for tag in model.CaseTag),
    }, "an empty corpus must expose every missing coverage obligation"
    assert all(gap.kind is findings.FindingKind.COVERAGE for gap in gaps), (
        "an empty corpus must expose every missing coverage obligation"
    )


def test_identity_checks_repeated_jobs_and_case_names(
    repository_jobs: tuple[model.CorpusJob, ...],
) -> None:
    """Repeated IDs must be diagnosed before they collapse into lookup maps."""
    job = repository_jobs[0]
    repeated = dataclasses.replace(job, cases=(job.cases[0], job.cases[0]))
    messages = [
        error.message for error in policy.find_identity_errors((repeated, repeated))
    ]
    assert set(messages) >= {
        "duplicate job",
        "duplicate case design-example",
        "duplicate observation",
    }, "repeated job, case, and observation identities must all be reported"


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
    assert bool(policy.find_failure_mismatches((job,))) is (status != required), (
        "the failure category must agree with the DC-4 exit status"
    )


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


def test_register_requires_exact_question_inventory() -> None:
    """Q5 cannot disappear or occur twice, and unknown Q9 is rejected."""
    rows = tuple(register_row(question) for question in model.QuestionId)
    tasks = ("1.1.1", "1.1.2")
    assert not policy.find_register_gaps(rows, tasks), (
        "the register must contain exactly one row per known question"
    )
    assert any(
        error.subject == "Q5"
        for error in policy.find_register_gaps(rows[:4] + rows[5:], tasks)
    ), "the register must contain exactly one row per known question"
    assert any(
        error.message == "duplicate question"
        for error in policy.find_register_gaps((*rows, rows[4]), tasks)
    ), "the register must contain exactly one row per known question"
    unknown = dataclasses.replace(rows[0], question=typ.cast("model.QuestionId", "Q9"))
    assert any(
        error.message == "unknown question"
        for error in policy.find_register_gaps((unknown,), tasks)
    ), "the register must contain exactly one row per known question"


@pytest.mark.parametrize("owner", ["", " ", "TBD", "unassigned", "-"])
def test_register_rejects_placeholder_owners(owner: str) -> None:
    """An accountable owner must be more than a placeholder spelling."""
    row = dataclasses.replace(register_row(model.QuestionId.Q1), owner=owner)
    assert any(
        "owner" in error.message
        for error in policy.find_register_gaps((row,), ("1.1.1", "1.1.2"))
    ), "placeholder text cannot identify an accountable owner"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"evidence_tasks": ("9.9.9",)}, "unknown task 9.9.9"),
        ({"decide_before": "1.1.3"}, "decision deadline follows a gate"),
        ({"gates": ("gap",)}, "gap is allowed only in evidence tasks"),
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
    assert message in {error.message for error in errors}, (
        "register deadlines and references must be actionable roadmap entries"
    )


@pytest.mark.parametrize("evidence", [("all",), ("validate-user-records",)])
def test_register_evidence_matches_jobs(
    repository_jobs: tuple[model.CorpusJob, ...], evidence: tuple[str, ...]
) -> None:
    """The all token and explicit job inventory mean the same exact set."""
    row = dataclasses.replace(
        register_row(model.QuestionId.Q1), corpus_evidence=evidence
    )
    assert not policy.find_evidence_mismatches(repository_jobs, (row,)), (
        "register evidence must equal the jobs bearing on the question"
    )
    for wrong in (("none",), ("unknown-job",), ("all", "unknown-job")):
        row = dataclasses.replace(row, corpus_evidence=wrong)
        assert policy.find_evidence_mismatches(repository_jobs, (row,)), (
            "register evidence must equal the jobs bearing on the question"
        )


def test_observations_are_documented_and_belong_to_job_questions(
    repository_jobs: tuple[model.CorpusJob, ...],
) -> None:
    """Whole IDs and question containment prevent misleading trace links."""
    job = repository_jobs[0]
    observation = dataclasses.replace(
        job.observations[0], questions=(model.QuestionId.Q8,)
    )
    job = dataclasses.replace(job, observations=(observation,))
    assert policy.find_evidence_mismatches((job,), ()), (
        "observation identifiers and questions must preserve exact trace links"
    )
    assert not policy.find_undocumented_observations((job,), "OBS-05"), (
        "observation identifiers and questions must preserve exact trace links"
    )
    assert policy.find_undocumented_observations((job,), "OBS-050"), (
        "observation identifiers and questions must preserve exact trace links"
    )


def test_reference_divergences_produce_one_finding_per_implementation(
    repository_jobs: tuple[model.CorpusJob, ...],
) -> None:
    """An invalid reference declaration should not repeat the same diagnostic."""
    job = repository_jobs[0]
    reference = job.alternatives[0]
    assert isinstance(reference, model.ScriptImplementation), (
        "fixture needs a reference"
    )
    reference = dataclasses.replace(
        reference,
        divergences=tuple(
            model.Divergence(case.case_id, "unsupported") for case in job.cases
        ),
    )
    job = dataclasses.replace(job, alternatives=(reference,))
    errors = policy.find_identity_errors((job,))
    assert [error.message for error in errors] == [
        "reference cannot declare divergences"
    ], "reference declarations must produce exactly one actionable diagnostic"
