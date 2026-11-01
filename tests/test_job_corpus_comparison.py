"""Observable comparison contracts, including stale divergence declarations."""

import dataclasses

import hypothesis as hyp
import pytest
from hypothesis import strategies as st
from job_corpus import comparison, findings, model

# Shorthands that keep every row of the table below on one line.
from job_corpus.model import Comparison as _Mode
from job_corpus.model import ObservedOutcome as _Observed


@pytest.mark.parametrize(
    ("observed", "mode", "agrees"),
    [
        (_Observed(b"a\nb\n", b"diagnostic", 0), _Mode.EXACT, True),
        (_Observed(b"b\na\n", b"", 0), _Mode.EXACT, False),
        (_Observed(b"b\na\n", b"", 0), _Mode.SORTED_LINES, True),
        (_Observed(b"a\nb", b"", 0), _Mode.SORTED_LINES, False),
        (_Observed(b"a\na\nb\n", b"", 0), _Mode.SORTED_LINES, False),
        (_Observed(b"a\nb\n", b"", 1), _Mode.EXACT, False),
        (_Observed(b"a\nb\n", b"", 0, timed_out=True), _Mode.EXACT, False),
    ],
)
def test_outcome_comparison_preserves_observable_contract(
    observed: model.ObservedOutcome, mode: model.Comparison, *, agrees: bool
) -> None:
    """Only the selected line-order relaxation may alter the comparison."""
    expected = model.ExpectedOutcome(b"a\nb\n", 0, model.Failure.NONE)
    why = "comparison must preserve every observable constraint except selected order"
    assert comparison.compare_outcome(expected, observed, mode) is agrees, why


@pytest.mark.parametrize(
    ("declared", "result", "agreement"),
    [
        (False, "matches", findings.Agreement.AGREED),
        (True, "matches", findings.Agreement.STALE_DIVERGENCE),
        (False, "differs", findings.Agreement.UNEXPECTED_DIFFERENCE),
        (True, "differs", findings.Agreement.DECLARED_DIVERGENCE),
        (True, "timeout", findings.Agreement.UNEXPECTED_DIFFERENCE),
        (False, "timeout", findings.Agreement.UNEXPECTED_DIFFERENCE),
    ],
)
def test_agreement_checks_both_halves_of_divergence_claim(
    reference_implementation: tuple[model.CorpusJob, model.ScriptImplementation],
    agreement: findings.Agreement,
    result: str,
    *,
    declared: bool,
) -> None:
    """A declaration needs an observed difference; timeout supplies no evidence."""
    job, implementation = reference_implementation
    case = job.cases[0]
    declarations = (
        (model.Divergence(case.case_id, "different language"),) if declared else ()
    )
    implementation = dataclasses.replace(implementation, divergences=declarations)
    outcome = model.ObservedOutcome(
        case.expected.stdout,
        b"",
        case.expected.exit_status + (1 if result == "differs" else 0),
        timed_out=result == "timeout",
    )
    why = "declarations must match the observed agreement truth table"
    assert comparison.evaluate_agreement(implementation, case, outcome) is agreement, (
        why
    )


def test_sorted_comparison_splits_only_newline_bytes() -> None:
    """A carriage return inside a record cannot become a record separator."""
    expected = model.ExpectedOutcome(b"a\rb\n", 0, model.Failure.NONE)
    observed = model.ObservedOutcome(b"a\nb\n", b"", 0)
    why = "carriage returns must remain bytes inside records"
    assert not comparison.compare_outcome(
        expected, observed, model.Comparison.SORTED_LINES
    ), why


_RECORD = st.binary(max_size=6).map(lambda raw: raw.replace(b"\n", b"\r"))
"""One record: any bytes, but never a separator, so a CR stays inside it."""


def _stdout(lines: list[bytes], *, final: bool) -> bytes:
    """Render records as a program writes them: joined, then terminated.

    Returns
    -------
    bytes
        The records joined by newlines, with a final one only when requested.
    """
    body = b"\n".join(lines)
    return body + b"\n" if final and lines else body


@hyp.given(
    lines=st.one_of(st.just([]), st.just([b"a", b"a"]), st.lists(_RECORD, max_size=6)),
    data=st.data(),
)
def test_sorted_comparison_accepts_every_reordering(
    lines: list[bytes], data: st.DataObject
) -> None:
    """Any permutation of the same records and terminator must agree."""
    reordered = list(data.draw(st.permutations(lines)))
    expected = model.ExpectedOutcome(_stdout(lines, final=True), 0, model.Failure.NONE)
    observed = model.ObservedOutcome(_stdout(reordered, final=True), b"", 0)
    why = f"reordering {lines!r} as {reordered!r} must still agree"
    sorted_lines = model.Comparison.SORTED_LINES
    assert comparison.compare_outcome(expected, observed, sorted_lines), why


@hyp.given(lines=st.lists(_RECORD, min_size=1, max_size=5), data=st.data())
def test_sorted_comparison_rejects_every_observable_change(
    lines: list[bytes], data: st.DataObject
) -> None:
    """Changed bytes, counts, terminator, status, or timeout must not agree."""
    expected = model.ExpectedOutcome(_stdout(lines, final=True), 0, model.Failure.NONE)
    changed = list(lines)
    changed[data.draw(st.integers(min_value=0, max_value=len(lines) - 1))] += b"x"
    observed = {
        "record-bytes": (_stdout(changed, final=True), 0, False),
        "record-count": (_stdout([*lines, b"extra"], final=True), 0, False),
        "final-newline": (_stdout(lines, final=False), 0, False),
        "exit-status": (_stdout(lines, final=True), 1, False),
        "timeout": (_stdout(lines, final=True), 0, True),
    }
    for difference, (stdout, status, timed_out) in observed.items():
        why = f"a changed {difference} must not agree for {lines!r}"
        outcome = model.ObservedOutcome(stdout, b"", status, timed_out=timed_out)
        assert not comparison.compare_outcome(
            expected, outcome, model.Comparison.SORTED_LINES
        ), why
