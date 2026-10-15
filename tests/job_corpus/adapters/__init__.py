"""Adapters: everything in the harness that touches the outside world.

Each adapter depends only on `job_corpus.model` and `job_corpus.ports`; no
adapter imports another, so the domain stays testable without a file system,
a subprocess, or a Markdown document.
"""
