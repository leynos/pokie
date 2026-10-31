"""Shared fixtures and Hypothesis profiles for the test suite.

The corpus harness runs child processes, and Hypothesis deadlines measure
wall-clock time around the property body, so coverage instrumentation can trip
one on a run that is merely slow. The default profile therefore has no
deadline; `ci` also derandomizes, making a failure reproducible from its seed.
"""

import os
import pathlib
import shutil
import typing as typ

import hypothesis
import pytest
from job_corpus import model
from job_corpus.adapters import process_runner, toml_jobs

if typ.TYPE_CHECKING:
    import collections.abc as cabc

hypothesis.settings.register_profile("default", deadline=None)
hypothesis.settings.register_profile(
    "ci", parent=hypothesis.settings.get_profile("default"), derandomize=True
)
hypothesis.settings.load_profile("ci" if os.environ.get("CI") else "default")

CORPUS_ROOT = pathlib.Path(__file__).resolve().parent / "job_corpus"
"""The corpus directory: job data, the reference oracle, and the alternatives."""


class AwkFacts(typ.NamedTuple):
    """The host awk the corpus runs, resolved once at configuration time."""

    executable: str | None
    """The resolved path, or ``None`` when no awk is installed."""

    banner: str
    """The first version line the probe printed, or ``""`` for no answer."""

    named: bool
    """Whether ``JOB_CORPUS_AWK`` named the executable, rather than ``PATH``."""


AWK_FACTS_KEY: pytest.StashKey[AwkFacts] = pytest.StashKey()
"""Where the session stores the facts, so rendering reads rather than probes."""


def collect_awk_facts(
    *,
    environ: cabc.Mapping[str, str] = os.environ,
    which: cabc.Callable[[str], str | None] = shutil.which,
    probe: cabc.Callable[[str], str] = process_runner.awk_version,
) -> AwkFacts:
    """Resolve the host awk and probe its version, before any rendering.

    Discovery, the environment, and the probe are injectable, so a test can
    drive every outcome without depending on this host's installed awks.

    Returns
    -------
    AwkFacts
        The executable, its version banner, and whether it was named.
    """
    named = environ.get("JOB_CORPUS_AWK", "")
    executable = named or which("awk")
    return AwkFacts(executable, probe(executable) if executable else "", bool(named))


def pytest_configure(config: pytest.Config) -> None:
    """Resolve the host awk once, at the session boundary before rendering."""
    config.stash[AWK_FACTS_KEY] = collect_awk_facts()


def report_header_line(facts: AwkFacts) -> str:
    """Format the corpus awk header line from facts already collected.

    Both absences are named outright, so the header never renders an empty
    version as though it were a version somebody probed.

    Returns
    -------
    str
        The one-line report naming what the probe found.
    """
    found = facts.executable or "no awk"
    banner = facts.banner or "version unknown"
    override = " [JOB_CORPUS_AWK]" if facts.named else ""
    return f"job corpus awk: {found} ({banner}){override}"


def pytest_report_header(config: pytest.Config) -> str:
    """Report the awk resolved at configuration, without probing again.

    Returns
    -------
    str
        The header line built from the facts `pytest_configure` stored.
    """
    return report_header_line(config.stash[AWK_FACTS_KEY])


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
def process_runner_instance(
    corpus_root: pathlib.Path, pytestconfig: pytest.Config
) -> process_runner.ProcessRunner:
    """Return a runner rooted at the repository corpus, using the session awk.

    Returns
    -------
    process_runner.ProcessRunner
        The runner the corpus tests execute implementations through.
    """
    facts = pytestconfig.stash[AWK_FACTS_KEY]
    return process_runner.ProcessRunner(
        corpus_root=corpus_root, awk_executable=facts.executable
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
