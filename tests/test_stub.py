"""Tests for the generated package stub."""

import pytest

import pokie
from scripts.wheel_smoke import main as check_wheel


def test_hello_returns_stub_greeting() -> None:
    """The generated package exposes a working greeting."""
    assert pokie.hello() == "hello from Python", (
        "The public greeting must use the scaffold fallback"
    )


def test_wheel_smoke_checks_the_public_package(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The smoke script verifies the installed package before reporting success."""
    check_wheel()
    assert capsys.readouterr().out == "hello from Python\n", (
        "The wheel smoke test must report the verified public greeting"
    )


def test_wheel_smoke_rejects_an_unexpected_greeting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A broken package must fail the act smoke check."""
    monkeypatch.setattr(pokie, "hello", lambda: "unexpected")
    with pytest.raises(RuntimeError, match="Unexpected wheel greeting"):
        check_wheel()
