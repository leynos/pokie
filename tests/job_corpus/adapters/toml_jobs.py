"""Load ``job.toml`` documents into corpus domain values.

A job file is evidence, so the loader is strict: an unknown key, a missing
table, or an unrecognized enum member fails with the job file and the TOML key
rather than defaulting, because a corpus that silently ignored half a case
would still pass its own tests.

This module is the schema walk: it reads a document's tables in the order the
schema nests them and delegates each scalar to
`job_corpus.adapters.toml_values`, which owns the ``text``/``hex`` encodings,
the ``where`` pair every diagnostic carries, and `_fail`.

Every ``_load_*`` function takes the decoded ``value`` and ``where`` and
reports a malformed value through `_fail` rather than defaulting; each
``Raises`` section names only the failures the function raises itself.
"""

import pathlib
import tomllib
import typing as typ

from job_corpus import model
from job_corpus.adapters.toml_values import (
    _all_required,
    _contents,
    _corpus_path,
    _dotted,
    _fail,
    _integer,
    _member,
    _members,
    _no_unknown_keys,
    _required,
    _strings,
    _table,
    _tables,
    _text,
)
from job_corpus.ports import EvidenceFormatError

if typ.TYPE_CHECKING:
    from job_corpus.adapters.toml_values import Where

SCHEMA_VERSION = 1
"""The only ``job.toml`` schema version this loader accepts."""

_REQUIRED_JOB_KEYS = (
    "id",
    "title",
    "category",
    "goals",
    "decisions",
    "contracts",
    "evidence_status",
    "provenance",
    "program",
    "alternatives",
    "cases",
)
_JOB_KEYS = frozenset({"schema", "observations", *_REQUIRED_JOB_KEYS})
_PROGRAM_KEYS = frozenset({"path", "args"})
_SCRIPT_KEYS = frozenset({"kind", "path", "args", "comparison", "divergences"})
_DESCRIBED_KEYS = frozenset({"kind", "tool", "description"})
_DIVERGENCE_KEYS = frozenset({"case", "reason"})
_CASE_KEYS = frozenset({
    "id",
    "tags",
    "operands",
    "inputs",
    "expected",
    "earliest_task",
})
_INPUT_KEYS = frozenset({"name", "text", "hex"})
_EXPECTED_KEYS = frozenset({"stdout", "exit_status", "failure"})
_OBSERVATION_KEYS = frozenset({"id", "kind", "contracts", "questions", "summary"})
_REQUIRED_CASE_KEYS = ("id", "operands", "inputs", "expected", "earliest_task")
_REQUIRED_SCRIPT_KEYS = ("kind", "path")
_REQUIRED_DESCRIBED_KEYS = ("kind", "description")
_REQUIRED_INPUT_KEYS = ("name",)
_REQUIRED_EXPECTED_KEYS = ("stdout", "exit_status", "failure")
_REQUIRED_OBSERVATION_KEYS = ("id", "kind", "summary")


def _load_input(value: object, where: Where) -> model.InputFile:
    """Load one named input file.

    Returns
    -------
    model.InputFile
        The input's operand name and exact bytes.
    """
    table = _table(value, where)
    _no_unknown_keys(table, _INPUT_KEYS, where)
    _all_required(table, _REQUIRED_INPUT_KEYS, where)
    return model.InputFile(
        name=_text(table["name"], _dotted(where, "name")),
        content=_contents(table, where),
    )


def _load_expected(value: object, where: Where) -> model.ExpectedOutcome:
    """Load a case's expected outcome.

    Returns
    -------
    model.ExpectedOutcome
        The specified standard output, exit status, and failure category.
    """
    table = _table(value, where)
    _no_unknown_keys(table, _EXPECTED_KEYS, where)
    _all_required(table, _REQUIRED_EXPECTED_KEYS, where)
    return model.ExpectedOutcome(
        stdout=_text(table["stdout"], _dotted(where, "stdout")).encode("utf-8"),
        exit_status=_integer(table["exit_status"], _dotted(where, "exit_status")),
        failure=_member(model.Failure, table["failure"], _dotted(where, "failure")),
    )


def _load_case(value: object, where: Where) -> model.JobCase:
    """Load one case, with its inputs, operands, and expected outcome.

    Returns
    -------
    model.JobCase
        The case's identifier, tags, operands, inputs, expected outcome, and
        the earliest roadmap task that could satisfy it.
    """
    table = _table(value, where)
    _no_unknown_keys(table, _CASE_KEYS, where)
    _all_required(table, _REQUIRED_CASE_KEYS, where)
    return model.JobCase(
        case_id=_text(table["id"], _dotted(where, "id")),
        tags=_members(model.CaseTag, table.get("tags", []), _dotted(where, "tags")),
        operands=_strings(table["operands"], _dotted(where, "operands")),
        inputs=tuple(
            _load_input(item, _dotted(where, "inputs"))
            for item in _tables(table["inputs"], _dotted(where, "inputs"))
        ),
        expected=_load_expected(table["expected"], _dotted(where, "expected")),
        earliest_task=_text(table["earliest_task"], _dotted(where, "earliest_task")),
    )


def _load_program(value: object, where: Where) -> model.ProposedProgram:
    """Load the proposed, non-executable pokie program.

    Returns
    -------
    model.ProposedProgram
        The program's corpus-relative path, resolved against ``where``'s
        file, and its fixed arguments.
    """
    table = _table(value, where)
    _no_unknown_keys(table, _PROGRAM_KEYS, where)
    _all_required(table, ("path",), where)
    return model.ProposedProgram(
        path=_corpus_path(_text(table["path"], _dotted(where, "path")), where),
        args=_strings(table.get("args", []), _dotted(where, "args")),
    )


def _load_divergence(value: object, where: Where) -> model.Divergence:
    """Load one declared divergence between an alternative and the oracle.

    Returns
    -------
    model.Divergence
        The case the alternative is expected to differ on, and why.
    """
    table = _table(value, where)
    _no_unknown_keys(table, _DIVERGENCE_KEYS, where)
    _all_required(table, ("case", "reason"), where)
    return model.Divergence(
        case_id=_text(table["case"], _dotted(where, "case")),
        reason=_text(table["reason"], _dotted(where, "reason")),
    )


def _load_script(
    table: dict[str, object], kind: model.ScriptKind, where: Where
) -> model.ScriptImplementation:
    """Load an executable alternative from its already-read ``table``.

    ``kind`` is the kind its ``kind`` key named; absent optional keys default
    to no arguments, exact comparison, and no divergences.

    Returns
    -------
    model.ScriptImplementation
        The script, with its arguments, comparison mode, and divergences.
    """
    _no_unknown_keys(table, _SCRIPT_KEYS, where)
    _all_required(table, _REQUIRED_SCRIPT_KEYS, where)
    return model.ScriptImplementation(
        kind=kind,
        path=_corpus_path(_text(table["path"], _dotted(where, "path")), where),
        args=_strings(table.get("args", []), _dotted(where, "args")),
        comparison=_member(
            model.Comparison,
            table.get("comparison", model.Comparison.EXACT.value),
            _dotted(where, "comparison"),
        ),
        divergences=tuple(
            _load_divergence(item, _dotted(where, "divergences"))
            for item in _tables(
                table.get("divergences", []), _dotted(where, "divergences")
            )
        ),
    )


def _load_described(
    table: dict[str, object], kind: model.DescribedKind, where: Where
) -> model.DescribedAlternative:
    """Load an alternative the corpus names but does not execute.

    ``kind`` is the kind its ``kind`` key named; an absent ``tool`` becomes
    the empty string that an unnamed status quo is written as.

    Returns
    -------
    model.DescribedAlternative
        The named alternative and its prose description.
    """
    _no_unknown_keys(table, _DESCRIBED_KEYS, where)
    _all_required(table, _REQUIRED_DESCRIBED_KEYS, where)
    return model.DescribedAlternative(
        kind=kind,
        tool=_text(table.get("tool", ""), _dotted(where, "tool")),
        description=_text(table["description"], _dotted(where, "description")),
    )


def _load_alternative(value: object, where: Where) -> model.Alternative:
    """Load one alternative, choosing its shape from its ``kind``.

    Returns
    -------
    model.Alternative
        A script for an executable language, else the described alternative;
        an unrecognized ``kind`` is reported through `_fail`.
    """
    table = _table(value, where)
    raw = _text(_required(table, "kind", where), _dotted(where, "kind"))
    by_name = {member.value: member for member in model.ScriptKind}
    described = {member.value: member for member in model.DescribedKind}
    if raw in by_name:
        return _load_script(table, by_name[raw], where)
    if raw in described:
        return _load_described(table, described[raw], where)
    known = ", ".join(repr(name) for name in (*by_name, *described))
    return _fail(_dotted(where, "kind"), f"expected one of {known}; got {raw!r}")


def _load_observation(value: object, where: Where) -> model.Observation:
    """Load one recorded contract tension.

    Returns
    -------
    model.Observation
        The tension, with absent ``contracts`` and ``questions`` empty.
    """
    table = _table(value, where)
    _no_unknown_keys(table, _OBSERVATION_KEYS, where)
    _all_required(table, _REQUIRED_OBSERVATION_KEYS, where)
    return model.Observation(
        observation_id=_text(table["id"], _dotted(where, "id")),
        kind=_member(model.ObservationKind, table["kind"], _dotted(where, "kind")),
        contracts=_strings(table.get("contracts", []), _dotted(where, "contracts")),
        questions=_members(
            model.QuestionId, table.get("questions", []), _dotted(where, "questions")
        ),
        summary=_text(table["summary"], _dotted(where, "summary")),
    )


def _load_identity(
    table: dict[str, object], relative: pathlib.PurePosixPath, where: Where
) -> str:
    """Check the schema and that ``id`` names the containing directory.

    Returns
    -------
    str
        The job identifier, reused by the caller's model construction.
    """
    schema_where = _dotted(where, "schema")
    schema = _integer(_required(table, "schema", where), schema_where)
    if schema != SCHEMA_VERSION:
        _fail(schema_where, f"expected {SCHEMA_VERSION}, got {schema!r}")
    _all_required(table, _REQUIRED_JOB_KEYS, where)
    directory = relative.parent.name
    document_id = _text(table["id"], (relative, "id"))
    if document_id != directory:
        _fail(
            (relative, "id"),
            f"expected {directory!r} to match the directory name; got {document_id!r}",
        )
    return document_id


def load_job(document_text: str, relative: pathlib.PurePosixPath) -> model.CorpusJob:
    """Load one job document, keyed by its corpus-relative path.

    ``relative`` locates the job's directory and keeps diagnostics corpus-relative.

    Parameters
    ----------
    document_text : str
        The ``job.toml`` file's text.
    relative : pathlib.PurePosixPath
        The file's path relative to the corpus root.

    Returns
    -------
    model.CorpusJob
        The job, with its alternatives, cases, and observations.

    Raises
    ------
    EvidenceFormatError
        If the text is not valid TOML.
    """
    try:
        document = tomllib.loads(document_text)
    except tomllib.TOMLDecodeError as error:
        message = f"invalid TOML: {error}"
        raise EvidenceFormatError(message, path=relative, key="") from error
    where: Where = (relative, "")
    table = _table(document, where)
    _no_unknown_keys(table, _JOB_KEYS, where)
    document_id = _load_identity(table, relative, where)
    return model.CorpusJob(
        job_id=document_id,
        title=_text(table["title"], (relative, "title")),
        category=_member(model.JobCategory, table["category"], (relative, "category")),
        goals=_strings(table["goals"], (relative, "goals")),
        decisions=_members(
            model.QuestionId, table["decisions"], (relative, "decisions")
        ),
        contracts=_strings(table["contracts"], (relative, "contracts")),
        evidence_status=_member(
            model.EvidenceStatus,
            table["evidence_status"],
            (relative, "evidence_status"),
        ),
        provenance=_strings(table["provenance"], (relative, "provenance")),
        program=_load_program(table["program"], (relative, "program")),
        alternatives=tuple(
            _load_alternative(item, (relative, "alternatives"))
            for item in _tables(table["alternatives"], (relative, "alternatives"))
        ),
        cases=tuple(
            _load_case(item, (relative, "cases"))
            for item in _tables(table["cases"], (relative, "cases"))
        ),
        observations=tuple(
            _load_observation(item, (relative, "observations"))
            for item in _tables(
                table.get("observations", []), (relative, "observations")
            )
        ),
    )


def load_jobs(corpus_root: pathlib.Path) -> tuple[model.CorpusJob, ...]:
    """Load every job in the corpus, ordered by directory name.

    The order is fixed so that test parameter identifiers, and therefore
    failure reports, stay stable between runs.

    Parameters
    ----------
    corpus_root : pathlib.Path
        The directory containing ``jobs/<job-id>/job.toml``.

    Returns
    -------
    tuple[model.CorpusJob, ...]
        Every loaded job. A corpus with no job files yields no jobs, which the
        coverage policy reports as a gap rather than as a loader error.

    Raises
    ------
    EvidenceFormatError
        If a job file cannot be read.
    """
    loaded: list[model.CorpusJob] = []
    for document_path in sorted((corpus_root / "jobs").glob("*/job.toml")):
        relative = pathlib.PurePosixPath(
            document_path.relative_to(corpus_root).as_posix()
        )
        try:
            text = document_path.read_text(encoding="utf-8")
        except OSError as error:
            message = f"cannot read job file: {error}"
            raise EvidenceFormatError(message, path=relative, key="") from error
        loaded.append(load_job(text, relative))
    return tuple(loaded)
