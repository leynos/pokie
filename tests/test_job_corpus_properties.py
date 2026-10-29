"""Independent finite-set models for corpus policy invariants."""

import collections
import dataclasses
import typing as typ

import hypothesis as hyp
from hypothesis import strategies as st
from job_corpus import findings, model, policy


@hyp.given(
    categories=st.lists(st.sampled_from(tuple(model.JobCategory)), max_size=10),
    tags=st.sets(st.sampled_from(tuple(model.CaseTag))),
)
@hyp.example(categories=[], tags=set())
@hyp.example(
    categories=[category for category in model.JobCategory for _ in range(2)],
    tags=set(model.CaseTag),
)
@hyp.example(categories=[model.JobCategory.FILTERING], tags=set())
def test_coverage_gaps_match_model(
    repository_jobs: tuple[model.CorpusJob, ...],
    categories: list[model.JobCategory],
    tags: set[model.CaseTag],
) -> None:
    """Missing categories, singletons, and tags match an independent set model."""
    template = repository_jobs[0]
    case = dataclasses.replace(template.cases[0], tags=tuple(tags))
    jobs = tuple(
        dataclasses.replace(template, category=category, cases=(case,))
        for category in categories
    )
    counts = collections.Counter(categories)
    expected = {
        f"category/{category}" for category in model.JobCategory if counts[category] < 2
    }
    present_tags = tags if categories else set()
    expected.update(f"tag/{tag}" for tag in model.CaseTag if tag not in present_tags)
    gaps = policy.find_coverage_gaps(jobs)
    assert {gap.subject for gap in gaps} == expected, (
        "coverage subjects must equal the model's missing category and tag set"
    )
    for category in model.JobCategory:
        category_findings = [
            gap for gap in gaps if gap.subject == f"category/{category}"
        ]
        if counts[category] < 2:
            assert f"found {counts[category]}" in category_findings[0].message, (
                f"the category finding must report its actual count {counts[category]}"
            )


@hyp.given(kinds=st.lists(st.sampled_from(tuple(model.ObservationKind)), max_size=12))
@hyp.example(kinds=[])
@hyp.example(kinds=[model.ObservationKind.AMBIGUITY])
@hyp.example(kinds=[model.ObservationKind.CONTRADICTION])
def test_verdict_tracks_contradictions_only(
    repository_jobs: tuple[model.CorpusJob, ...], kinds: list[model.ObservationKind]
) -> None:
    """Only a contradiction changes the phase-one falsification verdict."""
    job = repository_jobs[0]
    observations = tuple(
        model.Observation(f"OBS-{index}", kind, (), (), "Generated verdict control")
        for index, kind in enumerate(kinds)
    )
    job = dataclasses.replace(job, observations=observations)
    expected = (
        findings.Verdict.REVISE_CONTRACTS
        if model.ObservationKind.CONTRADICTION in kinds
        else findings.Verdict.PROCEED
    )
    assert policy.derive_verdict((job,)) is expected, (
        "only contradictions may change the contract verdict"
    )


@hyp.given(
    questions=st.lists(
        st.sampled_from([*map(str, model.QuestionId), "Q9"]), max_size=12
    ),
    owner=st.sampled_from(["@leynos", "", "TBD", "unassigned", "-"]),
    deadline=st.integers(min_value=0, max_value=3),
    gate=st.integers(min_value=0, max_value=3),
)
@hyp.example(questions=[], owner="@leynos", deadline=0, gate=0)
@hyp.example(
    questions=list(map(str, model.QuestionId)), owner="@leynos", deadline=0, gate=0
)
def test_register_gaps_match_model(
    questions: list[str], owner: str, deadline: int, gate: int
) -> None:
    """Question multisets, placeholder owners, and roadmap order match a model."""
    tasks = ("1.1.1", "1.1.2", "1.1.3")
    candidates = (*tasks, "9.9.9")
    rows = tuple(
        model.RegisterEntry(
            typ.cast("model.QuestionId", question),
            owner,
            ("1.1.1",),
            candidates[deadline],
            (candidates[gate],),
            ("none",),
        )
        for question in questions
    )
    errors = policy.find_register_gaps(rows, tasks)
    counts = collections.Counter(questions)
    expected_subjects = {
        str(question) for question in model.QuestionId if counts[str(question)] != 1
    }
    expected_subjects.update(question for question in questions if question == "Q9")
    row_invalid = owner != "@leynos" or deadline == 3 or gate == 3
    if deadline < 3 and gate < 3:
        row_invalid = row_invalid or deadline > gate
    if row_invalid:
        expected_subjects.update(questions)
    assert {error.subject for error in errors} == expected_subjects, (
        "register findings must match the independent multiset/order model"
    )
