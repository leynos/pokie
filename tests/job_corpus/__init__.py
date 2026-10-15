"""Representative job corpus harness.

The package holds the phase 1 evidence for roadmap task 1.1.1: the jobs pokie's
first release must demonstrate, their expected outcomes, the independent
implementations compared against those outcomes, and the policy that turns the
resulting observations into a go/no-go verdict for task 1.1.2.

Scope and reuse policy: the harness is test-only code. It is never packaged,
never imported by `pokie/`, and never imported by scripts outside `tests/`. Its
pure core (`model`, `findings`, `policy`, `comparison`, `audit`, and `report`)
performs no input or output, so it can be validated by unit and property tests;
everything that reads a file, runs a process, or writes to a stream lives in
`job_corpus.adapters`. Add new corpus data under `job_corpus/jobs/` and new
validation rules to `job_corpus.policy`; do not widen the adapters' surface
without recording why in `docs/developers-guide.md`.
"""
