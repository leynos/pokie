"""Regression checks for dead helpers hidden by Skylos's test-path heuristic."""

import subprocess  # ruff: ignore[suspicious-subprocess-import] - these tests drive the real installed detector.
import sys
import typing as typ

import pytest

if typ.TYPE_CHECKING:  # pragma: no cover - static fixture annotations only.
    from pathlib import Path


@pytest.mark.parametrize("case", ["orphan", "live-helper", "unused-test-local"])
def test_test_helpers_are_checked(tmp_path: Path, case: str) -> None:
    """An unused test helper must block; a helper called by a test must pass."""
    path = tmp_path / "test_example.py"
    call = "1" if case == "orphan" else "helper()"
    local = '    orphan_local = "unused"\n' if case == "unused-test-local" else ""
    path.write_text(
        "def helper():\n    return 1\n\ndef test_example():\n"
        f"{local}    assert {call} == 1\n",
        encoding="utf-8",
    )
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - resolved detector and generated fixture, no shell.
        [
            sys.executable,
            "-m",
            "vulture",
            str(path),
            "--ignore-names=test_*,pytestmark",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    expected = 0 if case == "live-helper" else 3
    why = f"Dead test helpers must fail without exempting bodies: {result.stdout}"
    assert result.returncode == expected, why
