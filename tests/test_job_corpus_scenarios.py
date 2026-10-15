"""Behavioural scenarios for the job corpus.

These scenarios state in prose what the parameterized tests state in data, and
they are the only tests that fail with a sentence rather than a parameter
identifier. Each step delegates to the same loaded corpus and the same runner,
so a scenario cannot agree with a promise the unit tests contradict.
"""

import dataclasses

import pytest
from job_corpus import model
from job_corpus.adapters import process_runner  # ruff: ignore[typing-only-third-party-import] - pytest-bdd resolves a step's annotations when it finds the step function.
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("job_corpus.feature")


@dataclasses.dataclass(slots=True)
class ScenarioState:
    """The state the steps of one scenario share.

    pytest-bdd has no implicit context object, so each scenario gets one of
    these through a fixture rather than through a module-level global that
    would leak between scenarios.
    """

    job: model.CorpusJob | None = None
    outcomes: tuple[tuple[model.JobCase, model.ObservedOutcome], ...] = ()


@pytest.fixture
def corpus_scenario() -> ScenarioState:
    """Return the empty state for one scenario.

    Returns
    -------
    ScenarioState
        Fresh state, so a step that runs before its ``Given`` fails on an
        assertion rather than on another scenario's leftovers.
    """
    return ScenarioState()


def select_job(jobs: tuple[model.CorpusJob, ...], job_id: str) -> model.CorpusJob:
    """Return the loaded job with the given identifier.

    Parameters
    ----------
    jobs : tuple[model.CorpusJob, ...]
        Every job the repository holds.
    job_id : str
        The identifier a scenario named.

    Returns
    -------
    model.CorpusJob
        The matching job. A tuple with no such identifier fails the assertion
        that names the jobs the corpus does hold, rather than picking one.
    """
    by_id = {job.job_id: job for job in jobs}
    assert job_id in by_id, (
        f"the corpus holds no job {job_id!r}; it holds {sorted(by_id)!r}"
    )
    return by_id[job_id]


def reference_of(job: model.CorpusJob) -> model.ScriptImplementation:
    """Return the oracle implementation of a job.

    Parameters
    ----------
    job : model.CorpusJob
        The job whose oracle is wanted.

    Returns
    -------
    model.ScriptImplementation
        The job's reference implementation. A job that declares no reference
        fails the assertion that names it, which would otherwise leave the
        scenario with nothing to run.
    """
    found = [
        alternative
        for alternative in job.alternatives
        if isinstance(alternative, model.ScriptImplementation)
        and alternative.kind is model.ScriptKind.REFERENCE
    ]
    assert found, f"{job.job_id} declares no reference implementation"
    return found[0]


@given(parsers.parse('the repository job "{job_id}"'))
def repository_job(
    corpus_scenario: ScenarioState,
    repository_jobs: tuple[model.CorpusJob, ...],
    job_id: str,
) -> None:
    """Select one job from the committed corpus."""
    corpus_scenario.job = select_job(repository_jobs, job_id)


@when("the job's reference implementation runs against every case")
def run_reference(
    corpus_scenario: ScenarioState,
    process_runner_instance: process_runner.ProcessRunner,
) -> None:
    """Run the job's oracle over every case and record what it produced."""
    job = corpus_scenario.job
    assert job is not None, "the scenario must select a job first"
    reference = reference_of(job)
    corpus_scenario.outcomes = tuple(
        (case, process_runner_instance.run(reference, case)) for case in job.cases
    )


@then("every observed outcome matches its expected outcome")
def every_outcome_matches(corpus_scenario: ScenarioState) -> None:
    """Compare every recorded run with the outcome the corpus specifies."""
    assert corpus_scenario.outcomes, "the scenario must run the reference first"
    mismatched = [
        f"{case.case_id}: expected {case.expected.stdout!r}, "
        f"observed {outcome.stdout!r}"
        for case, outcome in corpus_scenario.outcomes
        if outcome.stdout != case.expected.stdout
        or outcome.exit_status != case.expected.exit_status
    ]
    assert not mismatched, "; ".join(mismatched)
