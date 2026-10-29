"""Pure decision-register policy, exported through job_corpus.policy.

This feature module validates the corpus register only. It shares no document
parsing or product governance abstraction with runtime code.
"""

import collections
import collections.abc as cabc

from job_corpus import findings, model


def _row_task_errors(
    row: model.RegisterEntry, tasks: cabc.Sequence[str]
) -> tuple[str, ...]:
    """Check task references and ordering; ``gap`` is evidence-only.

    Returns
    -------
    tuple[str, ...]
        The invalid values or repeated identifiers.
    """
    unknown = {*row.evidence_tasks, row.decide_before, *row.gates} - set(tasks)
    if "gap" in row.evidence_tasks:
        unknown.discard("gap")
    errors = [f"unknown task {task}" for task in sorted(unknown)]
    if row.decide_before == "gap" or "gap" in row.gates:
        errors.append("gap is allowed only in evidence tasks")
    positions = {task: index for index, task in enumerate(tasks)}
    known_gates = [positions[gate] for gate in row.gates if gate in positions]
    earliest_gate = min(known_gates, default=len(tasks))
    if row.decide_before in positions and positions[row.decide_before] > earliest_gate:
        errors.append("decision deadline follows a gate")
    return tuple(errors)


def _row_errors(row: model.RegisterEntry, tasks: cabc.Sequence[str]) -> tuple[str, ...]:
    """Find unusable row values; for example, ``TBD`` is not an owner.

    Returns
    -------
    tuple[str, ...]
        The invalid values or repeated identifiers.
    """
    errors = list(_row_task_errors(row, tasks))
    if row.owner.strip().casefold() in {"", "tbd", "unassigned", "-"}:
        errors.append("owner is blank or a placeholder")
    if not row.evidence_tasks:
        errors.append("evidence tasks are empty")
    if not row.gates:
        errors.append("gates are empty")
    return tuple(errors)


def find_register_gaps(
    register: cabc.Sequence[model.RegisterEntry], task_ids: cabc.Sequence[str]
) -> tuple[findings.Finding, ...]:
    """Validate question coverage, owners, task references, and deadlines.

    For example, an empty register reports missing questions Q1 through Q8.

    Parameters
    ----------
    register : cabc.Sequence[model.RegisterEntry]
        Loaded decision-register rows.
    task_ids : cabc.Sequence[str]
        Roadmap task identifiers in delivery order.

    Returns
    -------
    tuple[findings.Finding, ...]
        The findings for the supplied evidence.
    """
    questions = {row.question for row in register}
    errors = [
        findings.Finding(findings.FindingKind.REGISTER, question, "missing question")
        for question in model.QuestionId
        if question not in questions
    ]
    counts = collections.Counter(row.question for row in register)
    errors.extend(
        findings.Finding(findings.FindingKind.REGISTER, question, "duplicate question")
        for question, count in sorted(counts.items())
        if count > 1
    )
    for row in register:
        if row.question not in model.QuestionId:
            errors.append(
                findings.Finding(
                    findings.FindingKind.REGISTER, row.question, "unknown question"
                )
            )
        errors.extend(
            findings.Finding(findings.FindingKind.REGISTER, row.question, error)
            for error in _row_errors(row, task_ids)
        )
    return tuple(errors)


def find_evidence_mismatches(
    jobs: cabc.Sequence[model.CorpusJob], register: cabc.Sequence[model.RegisterEntry]
) -> tuple[findings.Finding, ...]:
    """Check register/job agreement and observation question containment.

    For example, ``all`` expands to all loaded job IDs before comparison.

    Parameters
    ----------
    jobs : cabc.Sequence[model.CorpusJob]
        Loaded corpus jobs to validate.
    register : cabc.Sequence[model.RegisterEntry]
        Loaded decision-register rows.

    Returns
    -------
    tuple[findings.Finding, ...]
        The findings for the supplied evidence.
    """
    errors = []
    for row in register:
        expected = {job.job_id for job in jobs if row.question in job.decisions}
        actual = _expanded_evidence(row.corpus_evidence, jobs)
        if actual != expected:
            errors.append(
                findings.Finding(
                    findings.FindingKind.EVIDENCE,
                    row.question,
                    f"expected {sorted(expected)!r}; found {sorted(actual)!r}",
                )
            )
    errors.extend(
        findings.Finding(
            findings.FindingKind.EVIDENCE,
            item.observation_id,
            "observation questions are not job decisions",
        )
        for job in jobs
        for item in job.observations
        if not set(item.questions) <= set(job.decisions)
    )
    return tuple(errors)


def _expanded_evidence(
    evidence: tuple[str, ...], jobs: cabc.Sequence[model.CorpusJob]
) -> set[str]:
    """Expand a sole reserved token; mixed tokens remain invalid identifiers.

    Returns
    -------
    set[str]
        The detected names or expanded evidence identifiers.
    """
    if evidence == ("all",):
        return {job.job_id for job in jobs}
    if evidence == ("none",):
        return set()
    return set(evidence)
