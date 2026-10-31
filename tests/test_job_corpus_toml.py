"""Loader tests for the `job.toml` schema.

Obligation LEM-LOAD-1 in the ExecPlan owns this module. The tests here pin the
loader's strictness where a value of the wrong type could otherwise pass as the
right one. ``schema`` is compared against an integer constant, and Python makes
``True == 1`` and ``1.0 == 1``, so a version written as a boolean or a float
would otherwise load as version 1 — a malformed corpus file accepted in
silence, which is the failure the loader exists to prevent.

The suite grows with EP-M2, which adds the rest of LEM-LOAD-1's domain: input
encodings, missing and unknown keys, and unknown enum members.
"""

import pathlib

import pytest
from job_corpus import ports
from job_corpus.adapters import toml_jobs, toml_source

RELATIVE = pathlib.PurePosixPath("jobs/sample-job/job.toml")
"""Where the sample document sits relative to the corpus root.

The loader reads the job's identifier out of this path as well as out of the
document, so a temporary copy has to keep the same directory name.
"""

DOCUMENT = """\
schema = 1
id = "sample-job"
title = "Reject sample records"
category = "filtering"
goals = ["G1"]
decisions = ["Q1"]
contracts = ["DC-1"]
evidence_status = "Assumption"
provenance = ["docs/design-contracts.md §1"]
program = { path = "program.pokie", args = [] }

[[alternatives]]
kind = "reference"
path = "reference.py"

[[cases]]
id = "sample-case"
tags = []
operands = ["records.log"]
inputs = [{ name = "records.log", text = "ERROR a\\n" }]
expected = { stdout = "ERROR a\\n", exit_status = 0, failure = "none" }
earliest_task = "4.1.2"
"""
"""A minimal job file, holding one of everything the schema requires."""


def document_for(schema: str) -> str:
    """Return the sample document with its version spelled as ``schema``.

    Parameters
    ----------
    schema : str
        The TOML spelling of the version, such as ``"true"`` or ``"1.0"``.

    Returns
    -------
    str
        The document, unchanged apart from its first line.
    """
    return DOCUMENT.replace("schema = 1\n", f"schema = {schema}\n", 1)


def test_the_sample_document_loads() -> None:
    """The sample must be valid, so a rejection is attributable to its version.

    Without this control, the parameterized test below would pass for any
    document that happened to be malformed for an unrelated reason.
    """
    job = toml_jobs.load_job(DOCUMENT, RELATIVE)
    assert job.job_id == "sample-job", f"the sample loaded as {job.job_id!r}"


@pytest.mark.parametrize(
    "schema",
    [
        pytest.param("true", id="boolean"),
        pytest.param("false", id="boolean-false"),
        pytest.param("1.0", id="float"),
        pytest.param("0.5", id="fraction"),
        pytest.param('"1"', id="string"),
        pytest.param("2", id="later-version"),
        pytest.param("0", id="earlier-version"),
    ],
)
def test_a_version_the_loader_cannot_read_is_refused(schema: str) -> None:
    """A version must be the integer this loader accepts, and nothing else.

    ``True == 1`` and ``1.0 == 1`` in Python, so the two boolean spellings and
    the float ``1.0`` compare equal to `SCHEMA_VERSION` and would load as
    version 1. They are not version 1: they are a document whose version the
    loader cannot read, and accepting one would let a malformed job file
    through the strictness this loader promises. The remaining spellings are
    rejected already, and are pinned here so a later change cannot lose them.
    """
    text = document_for(schema)
    with pytest.raises(ports.EvidenceFormatError) as raised:
        toml_jobs.load_job(text, RELATIVE)
    why = f"schema = {schema} loaded instead of being refused"
    assert raised.value.path == RELATIVE, why
    assert raised.value.key == "schema", why


@pytest.mark.parametrize(
    ("old", "new", "key"),
    [
        ("schema = 1\n", "", "schema"),
        ('title = "Reject sample records"\n', "", "title"),
        ("schema = 1", "extra = 1\nschema = 1", ""),
        ('title = "Reject sample records"', "title = 7", "title"),
        ('goals = ["G1"]', 'goals = "G1"', "goals"),
        ('goals = ["G1"]', "goals = [1]", "goals"),
        ('decisions = ["Q1"]', 'decisions = "Q1"', "decisions"),
        ('category = "filtering"', 'category = "unknown"', "category"),
        ('program = { path = "program.pokie", args = [] }', "program = 1", "program"),
        ('kind = "reference"', 'kind = "unknown"', "alternatives.kind"),
        ('id = "sample-job"', 'id = "different-job"', "id"),
        (
            'inputs = [{ name = "records.log", text = "ERROR a\\n" }]',
            "inputs = 1",
            "cases.inputs",
        ),
        (
            'inputs = [{ name = "records.log", text = "ERROR a\\n" }]',
            "inputs = [1]",
            "cases.inputs",
        ),
        ('text = "ERROR a\\n"', 'text = "a\\r\\n"', "cases.inputs.text"),
        ('text = "ERROR a\\n"', 'hex = "not hex"', "cases.inputs.hex"),
        (', text = "ERROR a\\n"', "", "cases.inputs"),
        ('text = "ERROR a\\n"', 'text = "a", hex = "61"', "cases.inputs"),
        ("exit_status = 0, ", "", "cases.expected.exit_status"),
        ("exit_status = 0", "exit_status = true", "cases.expected.exit_status"),
        ("schema = 1", "schema = [", ""),
    ],
)
def test_malformed_documents_report_the_exact_key(old: str, new: str, key: str) -> None:
    """Each malformed public document identifies its own file and schema key."""
    assert old in DOCUMENT, "the mutation must change the known-valid document"
    with pytest.raises(ports.EvidenceFormatError) as raised:
        toml_jobs.load_job(DOCUMENT.replace(old, new, 1), RELATIVE)
    why = f"the malformed field must identify {key!r} in {RELATIVE}"
    assert raised.value.path == RELATIVE, why
    assert raised.value.key == key, why


@pytest.mark.parametrize(
    ("encoding", "expected"),
    [
        ('text = ""', b""),
        ('text = "unterminated"', b"unterminated"),
        ('hex = "fffe0d0a"', b"\xff\xfe\r\n"),
    ],
)
def test_input_encodings_preserve_exact_bytes(encoding: str, expected: bytes) -> None:
    """Empty, unterminated, and non-UTF-8 data retain their exact byte boundaries."""
    job = toml_jobs.load_job(
        DOCUMENT.replace('text = "ERROR a\\n"', encoding), RELATIVE
    )
    why = f"{encoding} must decode to {expected!r} without newline normalization"
    assert job.cases[0].inputs[0].content == expected, why


def test_a_job_document_that_cannot_be_read_is_reported(tmp_path: pathlib.Path) -> None:
    """A directory in place of job.toml produces a deterministic read error."""
    (tmp_path / RELATIVE).mkdir(parents=True)
    with pytest.raises(
        ports.EvidenceFormatError, match="cannot read job file"
    ) as raised:
        toml_jobs.load_jobs(tmp_path)
    why = "the unreadable document must retain its corpus-relative path"
    assert raised.value.path == RELATIVE, why


def test_an_empty_corpus_is_loaded_for_policy_to_report(tmp_path: pathlib.Path) -> None:
    """The loader preserves an empty inventory for the non-vacuity policy."""
    assert not toml_jobs.load_jobs(tmp_path), "empty directories must yield no jobs"


_INLINE_INPUT = 'inputs = [{ name = "records.log", text = "ERROR a\\n" }]'
"""The sample's inline input table, which the multiline tests replace."""

_CRLF_TEXT = 'inputs = [{ name = "records.log", text = """a\r\nb""" }]'
"""A multiline ``text`` whose raw CRLF `tomllib` would normalize away."""

_REFUSED = [
    pytest.param(_CRLF_TEXT, id="basic-crlf"),
    pytest.param("inputs = [{ name = 'r', text = '''a\rb''' }]", id="literal-cr"),
    pytest.param('inputs = [{ "text" = """a\r\nb""" }]', id="quoted-key"),
    pytest.param('a = 1\ninputs = [{ text = """c\r\nd""" }]', id="after-plain-key"),
    pytest.param('x = """a\\"""b"""\ntext = """c\r\nd"""', id="after-escape"),
    pytest.param('x = """a""""\ntext = """c\r\nd"""', id="after-trailing-quote"),
    pytest.param('x = "a#b\\"c"\ntext = """d\r\ne"""', id="after-hash"),
]
"""Sources the scan must refuse: a ``text`` string holding a physical CR.

The literals before the later cases also prove an earlier one does not
misalign the scan.
"""

_ACCEPTED = [
    pytest.param('inputs = [{ text = """a\nb\n""" }]', id="multiline-lf"),
    pytest.param('# text = """\ninputs = [{ text = "a" }]', id="in-a-comment"),
    pytest.param('inputs = ["""a\r\nb"""]', id="not-a-value"),
    pytest.param('x = """a\r\nb"""', id="another-key"),
    pytest.param('= """a\r\nb"""', id="no-key"),
    pytest.param('text = """a', id="unterminated"),
]
"""Sources the scan must leave alone, because they hide no ``text`` CR."""


@pytest.mark.parametrize("source", _REFUSED)
def test_a_multiline_text_holding_a_carriage_return_is_refused(source: str) -> None:
    """The scan must refuse a multiline ``text`` before `tomllib` can hide the CR."""
    with pytest.raises(ports.EvidenceFormatError) as raised:
        toml_source.reject_multiline_text_carriage_returns(source, RELATIVE)
    assert raised.value.path == RELATIVE, source
    assert raised.value.key == "cases.inputs.text", source


@pytest.mark.parametrize("source", _ACCEPTED)
def test_the_scan_refuses_nothing_but_a_text_carriage_return(source: str) -> None:
    """A comment, another key, or an unterminated literal is left to `tomllib`."""
    toml_source.reject_multiline_text_carriage_returns(source, RELATIVE)


@pytest.mark.parametrize(
    ("document", "expected"),
    [
        pytest.param(DOCUMENT.replace("\n", "\r\n"), b"ERROR a\n", id="single-line"),
        pytest.param(DOCUMENT.replace(_INLINE_INPUT, _CRLF_TEXT), None, id="multiline"),
    ],
)
def test_reading_a_file_preserves_the_carriage_returns_it_holds(
    tmp_path: pathlib.Path, document: str, expected: bytes | None
) -> None:
    """``newline=""`` must expose the CR that the source scan has to reject.

    The single-line text loads and keeps its bytes under CRLF line endings; the
    multiline one is refused, so reading erased nothing either way.
    """
    document_path = tmp_path / RELATIVE
    document_path.parent.mkdir(parents=True)
    document_path.write_bytes(document.encode("utf-8"))
    if expected is None:
        with pytest.raises(ports.EvidenceFormatError) as raised:
            toml_jobs.load_jobs(tmp_path)
        assert raised.value.key == "cases.inputs.text", "the CR must survive"
        return
    (job,) = toml_jobs.load_jobs(tmp_path)
    assert job.cases[0].inputs[0].content == expected, "CRLF must not reach the text"
