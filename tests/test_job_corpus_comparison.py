"""Observable comparison contracts, including stale divergence declarations."""

import dataclasses

import pytest
from job_corpus import comparison, findings, model


@pytest.mark.parametrize(
    ("observed", "mode", "agrees"),
    [
        (
            model.ObservedOutcome(b"a\nb\n", b"diagnostic", 0),
            model.Comparison.EXACT,
            True,
        ),
        (model.ObservedOutcome(b"b\na\n", b"", 0), model.Comparison.EXACT, False),
        (model.ObservedOutcome(b"b\na\n", b"", 0), model.Comparison.SORTED_LINES, True),
        (model.ObservedOutcome(b"a\nb", b"", 0), model.Comparison.SORTED_LINES, False),
        (
            model.ObservedOutcome(b"a\na\nb\n", b"", 0),
            model.Comparison.SORTED_LINES,
            False,
        ),
        (model.ObservedOutcome(b"a\nb\n", b"", 1), model.Comparison.EXACT, False),
        (
            model.ObservedOutcome(b"a\nb\n", b"", 0, timed_out=True),
            model.Comparison.EXACT,
            False,
        ),
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
