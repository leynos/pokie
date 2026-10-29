"""Pure validation policy for loaded representative corpus evidence.

Helpers here apply only to the corpus schema; callers supply loaded values
and roadmap order, so no policy depends on the current working directory.
"""

import collections
import collections.abc as cabc
import re

from job_corpus import findings, model
from job_corpus.register_policy import (
    find_evidence_mismatches as find_evidence_mismatches,
)
from job_corpus.register_policy import (
    find_register_gaps as find_register_gaps,
)

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

    Parameters
    ----------
    jobs : cabc.Sequence[model.CorpusJob]
        Loaded corpus jobs to validate.

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


def _script_implementations(
    job: model.CorpusJob,
) -> cabc.Iterator[model.ScriptImplementation]:
    """Select executable alternatives; for example, skip a described status quo.

    Yields
    ------
    model.ScriptImplementation
        Each executable implementation in declaration order.
    """
    for item in job.alternatives:
        match item:
            case model.ScriptImplementation():
                yield item


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
    scripts = tuple(_script_implementations(job))
    if sum(item.kind is model.ScriptKind.REFERENCE for item in scripts) != 1:
        errors.append(
            findings.Finding(
                findings.FindingKind.IDENTITY,
                job.job_id,
                "expected exactly one reference implementation",
            )
        )
    for script in scripts:
        errors.extend(_divergence_errors(script, cases))
    return tuple(errors)


def _divergence_errors(
    script: model.ScriptImplementation, cases: set[str]
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
    errors.extend(
        findings.Finding(
            findings.FindingKind.IDENTITY,
            str(script.path),
            f"divergence names unknown case {item.case_id}",
        )
        for item in script.divergences
        if item.case_id not in cases
    )
    errors.extend(
        findings.Finding(
            findings.FindingKind.IDENTITY,
            str(script.path),
            f"divergence {item.case_id} has no reason",
        )
        for item in script.divergences
        if not item.reason.strip()
    )
    if script.kind is model.ScriptKind.REFERENCE and script.divergences:
        errors.append(
            findings.Finding(
                findings.FindingKind.IDENTITY,
                str(script.path),
                "reference cannot declare divergences",
            )
        )
    return tuple(errors)


def find_identity_errors(
    jobs: cabc.Sequence[model.CorpusJob],
) -> tuple[findings.Finding, ...]:
    """Find duplicate jobs, cases, observations, and invalid declarations.

    For example, supplying the same job twice reports its duplicate ID.

    Parameters
    ----------
    jobs : cabc.Sequence[model.CorpusJob]
        Loaded corpus jobs to validate.

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

    Parameters
    ----------
    jobs : cabc.Sequence[model.CorpusJob]
        Loaded corpus jobs to validate.

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


def find_undocumented_observations(
    jobs: cabc.Sequence[model.CorpusJob], findings_text: str
) -> tuple[findings.Finding, ...]:
    """Require every observation ID as a whole token in the findings text.

    For example, ``OBS-010`` does not document observation ``OBS-01``.

    Parameters
    ----------
    jobs : cabc.Sequence[model.CorpusJob]
        Loaded corpus jobs to validate.
    findings_text : str
        Findings document text that must mention observation identifiers.

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

    Parameters
    ----------
    jobs : cabc.Sequence[model.CorpusJob]
        Loaded corpus jobs to validate.

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
