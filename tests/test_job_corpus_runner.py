"""Unit tests for the runner's operand, input-name, and stdin rules.

The end-to-end corpus tests in `tests/test_job_corpus_alternatives.py` drive the
runner through committed jobs, but every committed case happens to obey the
rules pinned here, so none of them can show what the runner does when a case
does not. That matters because the failure mode is silent: a case whose input
never reaches the program produces the same plausible-looking count that a
program prints for input it could not read.

`validate-user-records`'s oracle is the program under test. It counts the
``user=<name> uid=<int>`` records it reads, from its operands or from standard
input alike, so a one-record input makes the routes distinguishable: ``1 0``
when the record arrived, ``0 0`` when it did not.
"""

import dataclasses
import pathlib

import conftest
import pytest
from job_corpus import model, ports
from job_corpus.adapters import process_runner

ONE_RECORD = (model.InputFile(name="users.log", content=b"user=ada uid=42\n"),)
"""A single input the oracle reports as ``1 0`` when it receives it."""

TWO_RECORDS = (
    model.InputFile(name="first.log", content=b"user=ada uid=42\n"),
    model.InputFile(name="second.log", content=b"user=lin uid=7\n"),
)
"""Two inputs, so a case reading standard input cannot say which one it means."""

EMPTY_OUTCOME = model.ExpectedOutcome(
    stdout=b"", exit_status=0, failure=model.Failure.NONE
)
"""A placeholder the runner never consults: it reports what the program did."""


def reference_of(jobs: tuple[model.CorpusJob, ...]) -> model.ScriptImplementation:
    """Return the oracle these tests execute.

    Parameters
    ----------
    jobs : tuple[model.CorpusJob, ...]
        Every job the repository holds.

    Returns
    -------
    model.ScriptImplementation
        The ``validate-user-records`` reference. A corpus without it fails the
        assertion that names the job, rather than exercising nothing.
    """
    matches = [
        alternative
        for job in jobs
        for alternative in job.alternatives
        if job.job_id == "validate-user-records"
        and isinstance(alternative, model.ScriptImplementation)
        and alternative.kind is model.ScriptKind.REFERENCE
    ]
    assert matches, "the corpus declares no validate-user-records oracle"
    return matches[0]


def make_case(
    operands: tuple[str, ...], inputs: tuple[model.InputFile, ...]
) -> model.JobCase:
    """Return a case that differs from the committed ones only in its operands.

    The tags are deliberately empty: ``CaseTag`` names edge cases the committed
    corpus must cover, and labelling a synthetic case with one would overstate
    what it demonstrates and retire that tag's Vulture entry early.

    Parameters
    ----------
    operands : tuple[str, ...]
        The operands the program is started with.
    inputs : tuple[model.InputFile, ...]
        The inputs the runner may materialize.

    Returns
    -------
    model.JobCase
        A case whose identifier names this module, so a failure is traceable
        to the test that made it.
    """
    return model.JobCase(
        case_id="runner-operands",
        tags=(),
        operands=operands,
        inputs=inputs,
        expected=EMPTY_OUTCOME,
        earliest_task="4.1.2",
    )


@pytest.mark.parametrize(
    "operands",
    [
        pytest.param(("users.log",), id="named-operand"),
        pytest.param(("-",), id="stdin-operand"),
        pytest.param((), id="no-operands"),
    ],
)
def test_a_lone_input_reaches_the_program(
    process_runner_instance: process_runner.ProcessRunner,
    repository_jobs: tuple[model.CorpusJob, ...],
    operands: tuple[str, ...],
) -> None:
    """A single input must reach the program by every documented route.

    A named operand becomes the file's path, ``-`` becomes standard input, and
    no operands at all means standard input too: the oracle reads ``sys.stdin``
    when it is given nothing, and so does awk. A case that names no operand
    must therefore not be handed silent empty input, which is the shape that
    reads as a program finding nothing interesting rather than finding nothing.
    """
    case = make_case(operands, ONE_RECORD)
    outcome = process_runner_instance.run(reference_of(repository_jobs), case)
    why = f"operands {operands!r} lost the input: observed {outcome.stdout!r}"
    assert outcome.stdout == b"1 0\n", why
    assert outcome.exit_status == 0, why


def test_a_stdin_case_with_several_inputs_is_refused(
    process_runner_instance: process_runner.ProcessRunner,
    repository_jobs: tuple[model.CorpusJob, ...],
) -> None:
    """Standard input with several inputs is a corpus defect, not a guess.

    The runner cannot know which input the program would read. Picking the
    first silently would report the count for an input the case never selected,
    which is a wrong answer a reader of ``job.toml`` could not have predicted.
    """
    case = make_case(("-",), TWO_RECORDS)
    with pytest.raises(ports.EvidenceFormatError):
        process_runner_instance.run(reference_of(repository_jobs), case)


def test_an_operand_naming_no_input_is_refused(
    process_runner_instance: process_runner.ProcessRunner,
    repository_jobs: tuple[model.CorpusJob, ...],
) -> None:
    """An operand naming an input the case does not list must be reported.

    The sibling of the test above: neither a silent guess nor a silent empty
    file, so a typo in ``job.toml`` cannot pass as a program that read
    something uninteresting.
    """
    case = make_case(("absent.log",), ONE_RECORD)
    with pytest.raises(ports.EvidenceFormatError):
        process_runner_instance.run(reference_of(repository_jobs), case)


def test_every_named_operand_reaches_the_program(
    process_runner_instance: process_runner.ProcessRunner,
    repository_jobs: tuple[model.CorpusJob, ...],
) -> None:
    """Each named operand must be materialized, not just the first.

    A case over several files exists to show the program reading all of them,
    so a runner that wrote only the first would report a count for one file
    while the case claimed to have supplied two.
    """
    operands = tuple(input_file.name for input_file in TWO_RECORDS)
    case = make_case(operands, TWO_RECORDS)
    outcome = process_runner_instance.run(reference_of(repository_jobs), case)
    why = f"operands {operands!r} lost an input: observed {outcome.stdout!r}"
    assert outcome.stdout == b"2 0\n", why


def test_an_input_name_that_is_not_a_bare_file_name_is_refused(
    process_runner_instance: process_runner.ProcessRunner,
    repository_jobs: tuple[model.CorpusJob, ...],
) -> None:
    """An input name must be a bare file name, never a path.

    Two reasons, both about a wrong answer rather than tidiness. The operand
    is used as the path inside the run directory, and ``pathlib`` discards the
    left operand when the right is absolute, so an absolute name would have
    the run write outside its temporary directory — the constraint the plan
    states. And a name with a separator is not reachable as an operand, since
    the program is handed the joined path while the case says it named
    ``a/users.log``, so the two would disagree about which file the case
    selected.
    """
    escaping = "../users.log"
    inputs = (model.InputFile(name=escaping, content=b"user=ada uid=42\n"),)
    case = make_case((escaping,), inputs)
    with pytest.raises(ports.EvidenceFormatError):
        process_runner_instance.run(reference_of(repository_jobs), case)


def test_two_inputs_sharing_a_name_are_refused(
    process_runner_instance: process_runner.ProcessRunner,
    repository_jobs: tuple[model.CorpusJob, ...],
) -> None:
    """Duplicate input names are a corpus defect, not a silent last-one-wins.

    The name is the key that maps an operand to bytes, so a duplicate makes
    the mapping ambiguous and the dict comprehension keeps the last. The run
    would then feed the program bytes the case never selected for that
    operand, and the reported outcome would describe an input no reader of
    ``job.toml`` could have predicted from the operands listed.
    """
    duplicated = (
        model.InputFile(name="users.log", content=b"user=ada uid=42\n"),
        model.InputFile(name="users.log", content=b"user=lin uid=7\n"),
    )
    case = make_case(("users.log",), duplicated)
    with pytest.raises(ports.EvidenceFormatError):
        process_runner_instance.run(reference_of(repository_jobs), case)


def test_mixed_stdin_and_file_operands_are_refused(
    process_runner_instance: process_runner.ProcessRunner,
    reference_implementation: tuple[model.CorpusJob, model.ScriptImplementation],
) -> None:
    """The case format cannot unambiguously select bytes for mixed stdin/files."""
    _, implementation = reference_implementation
    case = make_case(("-", "users.log"), ONE_RECORD)
    with pytest.raises(ports.EvidenceFormatError) as raised:
        process_runner_instance.run(implementation, case)
    assert raised.value.key == "operands", "mixed routes must name the operand key"


def test_a_missing_script_is_a_case_format_error(
    tmp_path: pathlib.Path,
    reference_implementation: tuple[model.CorpusJob, model.ScriptImplementation],
) -> None:
    """A missing implementation does not masquerade as an ordinary program crash."""
    job, implementation = reference_implementation
    runner = process_runner.ProcessRunner(corpus_root=tmp_path)
    with pytest.raises(ports.EvidenceFormatError) as raised:
        runner.run(implementation, job.cases[0])
    assert raised.value.path == implementation.path, (
        "the missing script path must survive"
    )
    assert raised.value.key == "path", "the format error must identify the path key"


@pytest.mark.parametrize(
    ("kind", "key"), [(model.ScriptKind.POKIE, "kind"), (model.ScriptKind.AWK, "awk")]
)
def test_unavailable_implementation_kinds_are_explicit(
    process_runner_instance: process_runner.ProcessRunner,
    reference_implementation: tuple[model.CorpusJob, model.ScriptImplementation],
    kind: model.ScriptKind,
    key: str,
) -> None:
    """An absent executable or unsupported language yields evidence errors."""
    job, reference = reference_implementation
    runner = dataclasses.replace(process_runner_instance, awk_executable=None)
    implementation = dataclasses.replace(reference, kind=kind)
    with pytest.raises(ports.EvidenceFormatError) as raised:
        runner.run(implementation, job.cases[0])
    why = f"{kind} must identify its unsupported capability through {key!r}"
    assert raised.value.key == key, why


@pytest.mark.parametrize(
    ("kind", "script", "expected"),
    [
        pytest.param(
            model.ScriptKind.REFERENCE,
            "import os\nprint(','.join(sorted(os.environ)))\n",
            model.ObservedOutcome(b"LC_ALL,PATH\n", b"", 0),
            id="isolated-environment",
        ),
        pytest.param(
            model.ScriptKind.SHELL,
            'printf \'%s:%s\\n\' "$LC_ALL" "$1"\n',
            model.ObservedOutcome(b"C:fixture-argument\n", b"", 0),
            id="shell-arguments",
        ),
        pytest.param(
            model.ScriptKind.REFERENCE,
            "import time\ntime.sleep(2)\n",
            model.ObservedOutcome(b"", b"", 0, timed_out=True),
            id="bounded-timeout",
        ),
    ],
)
def test_command_boundaries_and_timeouts_are_observable(
    tmp_path: pathlib.Path,
    kind: model.ScriptKind,
    script: str,
    expected: model.ObservedOutcome,
) -> None:
    """Real child processes preserve environment/argument boundaries and timeouts."""
    path = tmp_path / "implementation"
    path.write_text(script)
    runner = process_runner.ProcessRunner(
        corpus_root=tmp_path, timeout=0.01 if expected.timed_out else 10.0
    )
    implementation = model.ScriptImplementation(
        kind=kind, path=pathlib.PurePosixPath(path.name), args=("fixture-argument",)
    )
    outcome = runner.run(implementation, make_case((), ONE_RECORD))
    why = f"the {kind} run must preserve its timeout classification"
    assert outcome.timed_out is expected.timed_out, why
    why = f"the {kind} run must preserve stdout bytes"
    assert outcome.stdout == expected.stdout, why
    why = f"the {kind} run must preserve stderr bytes"
    assert outcome.stderr == expected.stderr, why
    if not expected.timed_out:
        assert outcome.exit_status == expected.exit_status, (
            "completed runs retain status"
        )


def test_the_awk_report_survives_an_unrunnable_awk(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The header must still report a pinned awk that cannot be executed."""
    monkeypatch.setenv("JOB_CORPUS_AWK", "/nonexistent/awk")
    header = conftest.pytest_report_header(request.config)
    assert "(version unknown) [JOB_CORPUS_AWK]" in header, header


def test_the_header_line_reports_exactly_what_the_probe_found() -> None:
    """A returned banner is reported; a missing executable and banner are said."""
    found = conftest.report_header_line("/usr/bin/mawk", "mawk 1.3.4", named=False)
    assert found == "job corpus awk: /usr/bin/mawk (mawk 1.3.4)", found
    assert conftest.report_header_line(None, "", named=False) == (
        "job corpus awk: no awk (version unknown)"
    ), "a missing awk must be named, not shown as a version"
