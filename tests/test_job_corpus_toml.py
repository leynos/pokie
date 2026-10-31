"""Loader tests for the `job.toml` schema.

Obligation LEM-LOAD-1 in the ExecPlan owns this module. The tests pin the
loader's strictness where a wrong-typed value could pass as the right one:
Python makes ``True == 1`` and ``1.0 == 1``, so a boolean or float ``schema``
would otherwise load as version 1 — a malformed file accepted in silence.

The sample document lives in `tests/data/sample_job.toml`, so each mutation
below differs from one known-valid file rather than from an inlined literal.
"""

import pathlib

import pytest
from job_corpus import model, ports
from job_corpus.adapters import toml_jobs, toml_source

RELATIVE = pathlib.PurePosixPath("jobs/sample-job/job.toml")
"""Where the sample document sits relative to the corpus root.

The loader also reads the job identifier from this directory name.
"""

JOB_DIR = RELATIVE.parent
"""The sample's directory, which the paths it writes resolve against."""

DOCUMENT = (pathlib.Path(__file__).parent / "data" / "sample_job.toml").read_text(
    encoding="utf-8"
)
"""The sample job, holding one of everything the schema defines."""


def document_for(schema: str) -> str:
    """Return the sample document with its version spelled as ``schema``.

    The TOML spelling, such as ``"true"`` or ``"1.0"``, replaces only the first
    line, so each refusal test differs from the valid document solely in it.

    Returns
    -------
    str
        The document, unchanged apart from its first line.
    """
    return DOCUMENT.replace("schema = 1\n", f"schema = {schema}\n", 1)


def test_the_sample_document_decodes_every_field() -> None:
    """Every decoded value must be the document's own, not a loader default.

    The expected values are written out here rather than read back from the
    loader, and the sample uses non-default arguments, comparison, and
    divergence, so substituting any default fails. This test is also the
    control the mutation table below relies on: the sample is known-valid, so
    a rejection is attributable to the mutation.
    """
    job = toml_jobs.load_job(DOCUMENT, RELATIVE)
    assert (job.job_id, job.title, job.category) == (
        "sample-job",
        "Reject sample records",
        model.JobCategory.FILTERING,
    ), "the identity fields must be the document's own"
    assert (job.goals, job.decisions, job.contracts) == (
        ("G1",),
        (model.QuestionId.Q1, model.QuestionId.Q6),
        ("DC-1",),
    ), "the goal, decision, and contract lists must survive decoding"
    assert (job.evidence_status, job.provenance) == (
        model.EvidenceStatus.ASSUMPTION,
        ("docs/design-contracts.md §1",),
    ), "the evidence status and provenance must survive decoding"
    assert job.program == model.ProposedProgram(
        JOB_DIR / "program.pokie", ("-F", "|")
    ), "the program must keep its own path and arguments"
    reference, awk, prior_art, status_quo = job.alternatives
    assert isinstance(prior_art, model.DescribedAlternative), (
        "the third alternative must be described rather than a script"
    )
    assert isinstance(status_quo, model.DescribedAlternative), (
        "the fourth alternative must be described rather than a script"
    )
    assert reference == model.ScriptImplementation(
        model.ScriptKind.REFERENCE, JOB_DIR / "reference.py", ("--strict",)
    ), "the reference alternative must keep its path and arguments"
    assert awk == model.ScriptImplementation(
        model.ScriptKind.AWK,
        JOB_DIR / "alternative.awk",
        comparison=model.Comparison.SORTED_LINES,
        divergences=(
            model.Divergence("sample-case", "POSIX leaves array order unspecified."),
        ),
    ), "the awk alternative must keep its comparison and divergence"
    assert (prior_art.kind, prior_art.tool, prior_art.description) == (
        model.DescribedKind.PRIOR_ART,
        "PAWK",
        "pawk -B with a regex filter.",
    ), "the prior-art alternative must keep its tool and description"
    assert (status_quo.kind, status_quo.tool, status_quo.description) == (
        model.DescribedKind.STATUS_QUO,
        "",
        "A Python loop combining re.search and a Counter.",
    ), "the status-quo alternative must keep its description"
    (case,) = job.cases
    assert (case.case_id, case.tags, case.operands, case.earliest_task) == (
        "sample-case",
        (model.CaseTag.MALFORMED_RECORD,),
        ("records.log",),
        "4.1.2",
    ), "the case must keep its tags, operands, and earliest task"
    assert case.inputs == (model.InputFile("records.log", b"ERROR a\n"),), (
        "the case's input must keep its exact bytes"
    )
    assert case.expected == model.ExpectedOutcome(
        b"ERROR a\n", 0, model.Failure.NONE
    ), "the expected outcome must be the document's own"
    ambiguity, smell = job.observations
    assert ambiguity == model.Observation(
        "OBS-01",
        model.ObservationKind.AMBIGUITY,
        ("DC-2",),
        (model.QuestionId.Q3,),
        "The contract does not say whether empty input is a failure.",
    ), "the ambiguity observation must keep every field the document states"
    assert (smell.kind, smell.contracts, smell.questions) == (
        model.ObservationKind.ERGONOMIC_SMELL,
        ("DC-3",),
        (model.QuestionId.Q6,),
    ), "the second observation must keep its own kind, contracts, and questions"


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
        ('decisions = ["Q1", "Q6"]', 'decisions = "Q1"', "decisions"),
        ('category = "filtering"', 'category = "unknown"', "category"),
        (
            'program = { path = "program.pokie", args = ["-F", "|"] }',
            "program = 1",
            "program",
        ),
        ('kind = "reference"', 'kind = "unknown"', "alternatives.kind"),
        ('kind = "prior-art"', 'kind = "unknown"', "alternatives.kind"),
        ('tool = "PAWK"', "tool = 7", "alternatives.tool"),
        (
            'description = "pawk -B with a regex filter."',
            "",
            "alternatives.description",
        ),
        ('tool = "PAWK"', 'colour = "red"\ntool = "PAWK"', "alternatives"),
        ('id = "OBS-01"', "id = 7", "observations.id"),
        ('kind = "ambiguity"', 'kind = "unknown"', "observations.kind"),
        ('contracts = ["DC-2"]', "contracts = [1]", "observations.contracts"),
        ('questions = ["Q3"]', 'questions = ["Q9"]', "observations.questions"),
        ('questions = ["Q3"]', "questions = 1", "observations.questions"),
        (
            'summary = "The contract does not say whether empty input is a failure."',
            "",
            "observations.summary",
        ),
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


@pytest.mark.parametrize("payload", [None, b"\xff"])
def test_a_job_document_that_cannot_be_read_is_reported(
    tmp_path: pathlib.Path, payload: bytes | None
) -> None:
    """A directory or undecodable bytes in place of job.toml is a read error."""
    document = tmp_path / RELATIVE
    document.parent.mkdir(parents=True)
    if payload is None:
        document.mkdir()
    else:
        document.write_bytes(payload)
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
    pytest.param('"\\u0074ext" = """a\r\nb"""\n', id="escaped-key"),
    pytest.param('a = 1\ninputs = [{ text = """c\r\nd""" }]', id="after-plain-key"),
    pytest.param('x = """a\\"""b"""\ntext = """c\r\nd"""', id="after-escape"),
    pytest.param('x = """a""""\ntext = """c\r\nd"""', id="after-trailing-quote"),
    pytest.param('x = "a#b\\"c"\ntext = """d\r\ne"""', id="after-hash"),
    pytest.param('x = """a\\\\"""\ntext = """c\r\nd"""', id="after-backslash"),
    pytest.param('x = """a\\""""\ntext = """c\r\nd"""', id="after-escaped-quote"),
]
"""Spellings the loader must refuse: a ``text`` string holding a physical CR.

An earlier literal or key, escape included, must not misalign the scan.
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
    """The loader must refuse a multiline ``text`` before `tomllib` can hide the CR."""
    with pytest.raises(ports.EvidenceFormatError) as raised:
        toml_jobs.load_job(source, RELATIVE)
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
