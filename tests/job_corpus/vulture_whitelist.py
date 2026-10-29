"""Names that are live but invisible to static analysis.

Vulture runs over `tests/` so that unused helpers are caught, but a corpus
harness is full of names that no Python expression ever mentions. Vulture's
scanner cannot see through either pattern this package relies on:

- The `StrEnum` vocabularies are a *wire format*. A member is reached when a
  `job.toml` string names it, through `toml_values._member`, which calls
  `enum_type(text)`. Constructing a member from text is a runtime lookup, so
  `Failure.GUARD` stays unreported until some expression spells it literally.
- Some descriptive fields are read only by the report and documentation
  checks that later milestones add.

This module is Vulture's documented answer to that: it is scanned as ordinary
source, and each attribute access below marks one declared name as read. Every
entry is real attribute access, so `ty` fails the build if a name is renamed or
deleted, and the whitelist cannot silently drift out of step with the model.

Entries should be *removed* as consuming code lands, never added speculatively:
`tests/test_job_corpus_dead_code.py` fails when an entry here is no longer
reported by Vulture, which is what keeps this list from rotting into a blanket
exemption.
"""

from job_corpus import model

# Failure categories other than `NONE`, which the oracle tests name directly.
_ = (
    model.Failure.INITIALIZATION,
    model.Failure.GUARD,
    model.Failure.ADAPTER,
    model.Failure.ACTION,
    model.Failure.END,
    model.Failure.BROKEN_PIPE,
)

# Categories and case tags exercised by jobs EP-M3 adds; only the
# capture-validation tags are named in Python today.
_ = (
    model.JobCategory.FILTERING,
    model.JobCategory.AGGREGATION,
    model.CaseTag.PRESERVED_TEXT,
    model.CaseTag.OPTIONAL_CAPTURE,
    model.CaseTag.BINDING_ISOLATION,
    model.CaseTag.EMPTY_INPUT,
    model.CaseTag.EMPTY_FIELD,
    model.CaseTag.OUT_OF_RANGE_FIELD,
    model.CaseTag.UNTERMINATED_FINAL_LINE,
    model.CaseTag.INPUT_FAILURE,
    model.CaseTag.EARLY_EXIT,
    model.CaseTag.STDIN,
    model.CaseTag.NEXT_RECORD,
    model.CaseTag.MULTIPLE_RULES,
    model.CaseTag.MULTIPLE_FILES,
)

# The open questions the register rows are keyed by, and the observation
# vocabulary that decides the phase 1 verdict.
_ = (
    model.QuestionId.Q2,
    model.QuestionId.Q3,
    model.QuestionId.Q4,
    model.QuestionId.Q5,
    model.QuestionId.Q6,
    model.QuestionId.Q7,
    model.ObservationKind.ERGONOMIC_SMELL,
    model.ObservationKind.HOST_DIVERGENCE,
    model.EvidenceStatus.ESTABLISHED,
    model.EvidenceStatus.AGREED_BASIS,
    model.EvidenceStatus.ASSUMPTION,
    model.EvidenceStatus.PROPOSED_CONTRACT,
    model.EvidenceStatus.OPEN_QUESTION,
    model.EvidenceStatus.DEFERRED,
)

# Reserved for roadmap task 2.1.3, which supplies the pokie interpreter.
_ = (
    model.ScriptKind.POKIE,
    model.DescribedKind.STATUS_QUO,
    model.DescribedKind.PRIOR_ART,
)

# Read by the policy and report modules of EP-M1 and EP-M2.
_ = (
    model.DescribedAlternative.description,
    model.JobCase.earliest_task,
    model.Observation.contracts,
    model.Observation.summary,
    model.CorpusJob.title,
    model.CorpusJob.goals,
    model.CorpusJob.contracts,
    model.CorpusJob.evidence_status,
    model.CorpusJob.provenance,
    model.CorpusJob.program,
)
