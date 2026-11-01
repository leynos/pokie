"""Adapters: everything in the harness that touches the outside world.

The TOML loader is one adapter split across modules: `toml_jobs` walks the
schema and calls the private `toml_values` and `toml_source` helpers. Every
adapter depends only on `job_corpus.model` and `job_corpus.ports`, so the
domain stays testable without a file system, a subprocess, or a Markdown
document.
"""
