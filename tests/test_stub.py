"""Tests for the generated package stub."""

from __future__ import annotations

import pokie


def test_hello_returns_stub_greeting() -> None:
    """The generated package exposes a working greeting."""
    assert pokie.hello() == "hello from Python"
