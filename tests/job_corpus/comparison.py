"""Compare observable outcomes without consulting files or running programs."""

from job_corpus import findings, model


def compare_outcome(
    expected: model.ExpectedOutcome,
    observed: model.ObservedOutcome,
    comparison: model.Comparison = model.Comparison.EXACT,
) -> bool:
    r"""Return whether stdout and status agree; a timeout never agrees.

    For example, sorted-line comparison accepts ``b'b\na\n'`` for
    ``b'a\nb\n'`` while retaining duplicate lines and final-newline bytes.

    Parameters
    ----------
    expected : model.ExpectedOutcome
        The specified stdout, exit status, and failure category.
    observed : model.ObservedOutcome
        The captured output, exit status, and timeout flag.
    comparison : model.Comparison
        The permitted stdout ordering relaxation.

    Returns
    -------
    bool
        Whether the observable outcome agrees.
    """
    if observed.timed_out or observed.exit_status != expected.exit_status:
        return False
    if comparison is model.Comparison.SORTED_LINES:
        return observed.stdout.endswith(b"\n") == expected.stdout.endswith(
            b"\n"
        ) and sorted(observed.stdout.split(b"\n")) == sorted(
            expected.stdout.split(b"\n")
        )
    return observed.stdout == expected.stdout


def evaluate_agreement(
    implementation: model.ScriptImplementation,
    case: model.JobCase,
    observed: model.ObservedOutcome,
) -> findings.Agreement:
    """Classify agreement and declarations; an obsolete declaration is stale.

    For example, an agreeing case with a declared divergence returns
    ``Agreement.STALE_DIVERGENCE`` rather than silently hiding that claim.

    Parameters
    ----------
    implementation : model.ScriptImplementation
        The executable implementation and its divergence declarations.
    case : model.JobCase
        The input case and specified outcome.
    observed : model.ObservedOutcome
        The captured output, exit status, and timeout flag.

    Returns
    -------
    findings.Agreement
        The agreement classification, including stale claims.
    """
    if observed.timed_out:
        return findings.Agreement.UNEXPECTED_DIFFERENCE
    agrees = compare_outcome(case.expected, observed, implementation.comparison)
    declared = any(item.case_id == case.case_id for item in implementation.divergences)
    if declared:
        return (
            findings.Agreement.STALE_DIVERGENCE
            if agrees
            else findings.Agreement.DECLARED_DIVERGENCE
        )
    return (
        findings.Agreement.AGREED
        if agrees
        else findings.Agreement.UNEXPECTED_DIFFERENCE
    )
