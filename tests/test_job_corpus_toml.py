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
from job_corpus.adapters import toml_jobs

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
