"""Shared fixtures and Hypothesis profiles for the test suite.

The corpus harness runs child processes, and Hypothesis deadlines measure
wall-clock time around the property body, so coverage instrumentation can trip
one on a run that is merely slow. The default profile therefore has no
deadline; `ci` also derandomizes, making a failure reproducible from its seed.
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


def _awk_executable() -> str | None:
    """Resolve the awk the corpus harness should execute, or ``None``.

    ``JOB_CORPUS_AWK`` wins, so CI pins mawk rather than trusting ``PATH``.

    Returns
    -------
    str | None
        The named executable, or the first awk on ``PATH``, or ``None``.
    """
    return os.environ.get("JOB_CORPUS_AWK") or shutil.which("awk")


def report_header_line(executable: str | None, banner: str, *, named: bool) -> str:
    """Format the corpus awk header line from already-probed facts.

    ``banner`` is what `process_runner.awk_version` reported, and ``named``
    says whether ``JOB_CORPUS_AWK`` supplied the executable. Both absences are
    named outright, so the header never invents a version.

    Returns
    -------
    str
        The one-line report naming the probe's outcome.
    """
    override = " [JOB_CORPUS_AWK]" if named else ""
    found = executable or "no awk"
    return f"job corpus awk: {found} ({banner or 'version unknown'}){override}"


def pytest_report_header(config: pytest.Config) -> str:
    """Report which awk the corpus harness will execute, and its version.

    Returns
    -------
    str
        The header line built from the resolved executable and its probe.
    """
    executable = _awk_executable()
    banner = process_runner.awk_version(executable) if executable else ""
    named = bool(os.environ.get("JOB_CORPUS_AWK"))
    return report_header_line(executable, banner, named=named)


@pytest.fixture(scope="session")
def corpus_root() -> pathlib.Path:
    """Return the corpus root directory, which holds ``jobs/<job-id>/``.

    Returns
    -------
    pathlib.Path
        The directory the corpus loader reads jobs from.
    """
    return CORPUS_ROOT


@pytest.fixture(scope="session")
def repository_jobs(corpus_root: pathlib.Path) -> tuple[model.CorpusJob, ...]:
    """Load every job committed to the repository corpus, ordered by directory.

    Returns
    -------
    tuple[model.CorpusJob, ...]
        The loaded jobs.
    """
    return toml_jobs.load_jobs(corpus_root)


@pytest.fixture(scope="session")
def process_runner_instance(corpus_root: pathlib.Path) -> process_runner.ProcessRunner:
    """Return a runner rooted at the repository corpus, probing the host awk once.

    Returns
    -------
    process_runner.ProcessRunner
        The runner the corpus tests execute implementations through.
    """
    return process_runner.ProcessRunner(
        corpus_root=corpus_root, awk_executable=_awk_executable()
    )


@pytest.fixture(scope="session")
def reference_implementation(
    repository_jobs: tuple[model.CorpusJob, ...],
) -> tuple[model.CorpusJob, model.ScriptImplementation]:
    """Select a reference and its job without relying on alternative order.

    Tests can unpack ``job, reference = reference_implementation`` and retain
    the containing case metadata with the narrowed executable type. An absent
    reference fails the fixture rather than yielding nothing to compare.

    Returns
    -------
    tuple[model.CorpusJob, model.ScriptImplementation]
        The first job/reference pair.
    """
    for job in repository_jobs:
        for implementation in job.alternatives:
            match implementation:
                case model.ScriptImplementation(kind=model.ScriptKind.REFERENCE):
                    return job, implementation
    pytest.fail("the corpus must contain a reference implementation")
