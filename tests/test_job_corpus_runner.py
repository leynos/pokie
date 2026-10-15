"""Unit tests for the runner's operand and standard-input rules.

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

import typing as typ

import pytest
from job_corpus import model, ports

if typ.TYPE_CHECKING:
    # pytest matches a fixture by parameter name, not by annotation, so the
    # runner type is needed only by the type checker.
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

    The tags are deliberately empty: ``CaseTag`` names the edge cases the
    committed corpus must cover, and these synthetic cases are not part of it.
    Labelling them with a corpus tag would overstate what they demonstrate and
    would retire that tag's entry in the Vulture whitelist before EP-M3 adds
    the real case for it.

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
    assert outcome.stdout == b"2 0\n", (
        f"operands {operands!r} lost an input: observed {outcome.stdout!r}"
    )
