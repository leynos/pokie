"""Pure validation policy for loaded representative corpus evidence.

Helpers here apply only to the corpus schema; callers supply loaded values
and roadmap order, so no policy depends on the current working directory.
"""

import collections
import collections.abc as cabc
import re

from job_corpus import findings, model

MINIMUM_CATEGORY_JOBS = 2
"""At least two examples per category prevent token coverage."""


def _duplicates(values: cabc.Iterable[str]) -> tuple[str, ...]:
    """Return repeated identifiers in stable order, such as ``('Q5',)``.

    Returns
    -------
    tuple[str, ...]
        The invalid values or repeated identifiers.
    """
    return tuple(
        sorted(key for key, count in collections.Counter(values).items() if count > 1)
    )


def find_coverage_gaps(
    jobs: cabc.Sequence[model.CorpusJob],
) -> tuple[findings.Finding, ...]:
    """Find missing categories and tags; an empty corpus has both.

    For example, ``find_coverage_gaps(())`` reports every category and tag.

    Returns
    -------
    tuple[findings.Finding, ...]
        The findings for the supplied evidence.
    """
    counts = collections.Counter(job.category for job in jobs)
    tags = {tag for job in jobs for case in job.cases for tag in case.tags}
    categories = (
        findings.Finding(
            findings.FindingKind.COVERAGE,
            f"category/{category}",
            f"expected at least two jobs; found {counts[category]}",
        )
        for category in model.JobCategory
        if counts[category] < MINIMUM_CATEGORY_JOBS
    )
    missing_tags = (
        findings.Finding(
            findings.FindingKind.COVERAGE, f"tag/{tag}", "no case exercises this tag"
        )
        for tag in model.CaseTag
        if tag not in tags
    )
    return (*categories, *missing_tags)


def _job_identity_errors(job: model.CorpusJob) -> tuple[findings.Finding, ...]:
    """Check local identifiers; a repeated case names its containing job.

    Returns
    -------
    tuple[findings.Finding, ...]
        The findings for the supplied evidence.
    """
    cases = {case.case_id for case in job.cases}
    errors = [
        findings.Finding(
            findings.FindingKind.IDENTITY, job.job_id, f"duplicate case {case_id}"
        )
        for case_id in _duplicates(case.case_id for case in job.cases)
    ]
    scripts = tuple(
        item
        for item in job.alternatives
        if isinstance(item, model.ScriptImplementation)
    )
    if sum(item.kind is model.ScriptKind.REFERENCE for item in scripts) != 1:
        errors.append(
            findings.Finding(
                findings.FindingKind.IDENTITY,
                job.job_id,
                "expected exactly one reference implementation",
            )
        )
    for script in scripts:
        errors.extend(_divergence_errors(job, script, cases))
    return tuple(errors)


def _divergence_errors(
    job: model.CorpusJob, script: model.ScriptImplementation, cases: set[str]
) -> tuple[findings.Finding, ...]:
    """Refuse unknown, repeated, or unexplained claims, such as case ``typo``.

    Returns
    -------
    tuple[findings.Finding, ...]
        The findings for the supplied evidence.
    """
    errors = [
        findings.Finding(
            findings.FindingKind.IDENTITY,
            str(script.path),
            f"duplicate divergence {case_id}",
        )
        for case_id in _duplicates(item.case_id for item in script.divergences)
    ]
    for item in script.divergences:
        if item.case_id not in cases or not item.reason.strip():
            errors.append(
                findings.Finding(
                    findings.FindingKind.IDENTITY,
                    job.job_id,
                    f"invalid divergence {item.case_id}",
                )
            )
        if script.kind is model.ScriptKind.REFERENCE:
            errors.append(
                findings.Finding(
                    findings.FindingKind.IDENTITY,
                    job.job_id,
                    "reference cannot declare divergences",
                )
            )
    return tuple(errors)


def find_identity_errors(
    jobs: cabc.Sequence[model.CorpusJob],
) -> tuple[findings.Finding, ...]:
    """Find duplicate jobs, cases, observations, and invalid declarations.

    For example, supplying the same job twice reports its duplicate ID.

    Returns
    -------
    tuple[findings.Finding, ...]
        The findings for the supplied evidence.
    """
    errors = [
        findings.Finding(findings.FindingKind.IDENTITY, job_id, "duplicate job")
        for job_id in _duplicates(job.job_id for job in jobs)
    ]
    errors.extend(
        findings.Finding(
            findings.FindingKind.IDENTITY, identifier, "duplicate observation"
        )
        for identifier in _duplicates(
            item.observation_id for job in jobs for item in job.observations
        )
    )
    errors.extend(error for job in jobs for error in _job_identity_errors(job))
    return tuple(errors)


def find_failure_mismatches(
    jobs: cabc.Sequence[model.CorpusJob],
) -> tuple[findings.Finding, ...]:
    """Check DC-4's failure/status table, including static failures at status 2.

    For example, ``Failure.NONE`` paired with status 1 produces a finding.

    Returns
    -------
    tuple[findings.Finding, ...]
        The findings for the supplied evidence.
    """
    statuses = {model.Failure.NONE: 0, model.Failure.STATIC: 2}
    return tuple(
        findings.Finding(
            findings.FindingKind.FAILURE,
            f"{job.job_id}/{case.case_id}",
            f"{case.expected.failure} requires status "
            f"{statuses.get(case.expected.failure, 1)}",
        )
        for job in jobs
        for case in job.cases
        if case.expected.exit_status != statuses.get(case.expected.failure, 1)
    )


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
    errors.extend(
        findings.Finding(findings.FindingKind.REGISTER, question, "duplicate question")
        for question in _duplicates(row.question for row in register)
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


def find_undocumented_observations(
    jobs: cabc.Sequence[model.CorpusJob], findings_text: str
) -> tuple[findings.Finding, ...]:
    """Require every observation ID as a whole token in the findings text.

    For example, ``OBS-010`` does not document observation ``OBS-01``.

    Returns
    -------
    tuple[findings.Finding, ...]
        The findings for the supplied evidence.
    """
    identifiers = set(re.findall(r"\bOBS-[0-9]+\b", findings_text))
    return tuple(
        findings.Finding(
            findings.FindingKind.OBSERVATION,
            item.observation_id,
            "observation is undocumented",
        )
        for job in jobs
        for item in job.observations
        if item.observation_id not in identifiers
    )


def derive_verdict(jobs: cabc.Sequence[model.CorpusJob]) -> findings.Verdict:
    """Return revise-contracts exactly when a contradiction exists.

    For example, an empty corpus has no contradictions and returns proceed.

    Returns
    -------
    findings.Verdict
        The contract verdict derived from observations.
    """
    if any(
        item.kind is model.ObservationKind.CONTRADICTION
        for job in jobs
        for item in job.observations
    ):
        return findings.Verdict.REVISE_CONTRACTS
    return findings.Verdict.PROCEED
