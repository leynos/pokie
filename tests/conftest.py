"""Shared fixtures and Hypothesis profiles for the test suite.

The corpus harness runs child processes, and Hypothesis deadlines measure
wall-clock time around the property body. Under the coverage instrumentation
continuous integration uses, a deadline can fire on a run that is merely slow,
so the default profile has no deadline. The `ci` profile additionally
derandomizes, which makes a continuous-integration failure reproducible from
its seed rather than a fresh draw.
"""

import os
import pathlib
import shutil

import hypothesis
import pytest
from job_corpus import model
from job_corpus.adapters import process_runner, toml_jobs

hypothesis.settings.register_profile("default", deadline=None)
hypothesis.settings.register_profile(
    "ci", parent=hypothesis.settings.get_profile("default"), derandomize=True
)
hypothesis.settings.load_profile("ci" if os.environ.get("CI") else "default")

CORPUS_ROOT = pathlib.Path(__file__).resolve().parent / "job_corpus"
"""The corpus directory: job data, the reference oracle, and the alternatives."""


@pytest.fixture(scope="session")
def corpus_root() -> pathlib.Path:
    """Return the corpus root directory.

    Returns
    -------
    pathlib.Path
        The directory containing ``jobs/<job-id>/``.
    """
    return CORPUS_ROOT


@pytest.fixture(scope="session")
def repository_jobs(corpus_root: pathlib.Path) -> tuple[model.CorpusJob, ...]:
    """Load every job committed to the repository corpus.

    Returns
    -------
    tuple[model.CorpusJob, ...]
        The loaded jobs, ordered by directory name.
    """
    return toml_jobs.load_jobs(corpus_root)


@pytest.fixture(scope="session")
def awk_executable() -> str | None:
    """Return the awk on this host, or ``None`` when none is installed.

    Continuous integration installs mawk, so a missing awk there is a real
    failure rather than a reason to skip; the corpus tests decide that.

    Returns
    -------
    str | None
        The executable named by ``JOB_CORPUS_AWK``, or the first awk on
        ``PATH``.
    """
    override = os.environ.get("JOB_CORPUS_AWK")
    if override:
        return override
    return shutil.which("awk")


@pytest.fixture(scope="session")
def process_runner_instance(
    corpus_root: pathlib.Path, awk_executable: str | None
) -> process_runner.ProcessRunner:
    """Return the runner that starts corpus implementations as child processes.

    Returns
    -------
    process_runner.ProcessRunner
        A runner rooted at the repository corpus.
    """
    return process_runner.ProcessRunner(
        corpus_root=corpus_root, awk_executable=awk_executable
    )


@pytest.fixture(scope="session")
def reference_implementation(
    repository_jobs: tuple[model.CorpusJob, ...],
) -> tuple[model.CorpusJob, model.ScriptImplementation]:
    """Select a reference and its job without relying on alternative order.

    Tests can unpack ``job, reference = reference_implementation`` and retain
    the containing case metadata with the narrowed executable type.

    Parameters
    ----------
    repository_jobs : tuple[model.CorpusJob, ...]
        Loaded jobs containing the corpus's reference implementations.

    Returns
    -------
    tuple[model.CorpusJob, model.ScriptImplementation]
        The first job/reference pair; an absent reference fails the fixture.
    """
    for job in repository_jobs:
        for implementation in job.alternatives:
            match implementation:
                case model.ScriptImplementation(kind=model.ScriptKind.REFERENCE):
                    return job, implementation
    pytest.fail("the corpus must contain a reference implementation")
