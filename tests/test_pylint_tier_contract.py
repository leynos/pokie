"""Contract tests for the Pylint lint tier.

The tier runs a pinned Pylint as a uv tool on managed PyPy 3.12. Two
properties of that tier are easy to lose without any test noticing: the
interpreter pin, which decides the grammar Pylint parses with, and the
`syntax-error` message, which decides whether a module that grammar cannot
parse fails the lint or is skipped without a word. Both regressed silently
before: a bare `pypy` moved to a newer PyPy with no commit here, and a
disabled `syntax-error` let unparsable modules go unlinted.
"""

import re
import shlex
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] - the end-to-end test drives Make.
import tomllib
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE_PATH = _REPO_ROOT / "Makefile"
CONFIG_PATH = _REPO_ROOT / "pyproject.toml"

pytestmark = pytest.mark.skipif(
    not (MAKEFILE_PATH.exists() and CONFIG_PATH.exists()),
    reason="Makefile or lint configuration not present in this working copy",
)

_PROBE_TARGET: str = "jm5-pylint-probe"


def _makefile_variable(name: str) -> str:
    """Return the value assigned to a Makefile variable.

    Parameters
    ----------
    name : str
        The variable name, assigned with ``=`` or ``?=``.

    Returns
    -------
    str
        The assigned value with surrounding whitespace removed.
    """
    # Join backslash continuations so a multi-line assignment reads whole.
    text = MAKEFILE_PATH.read_text(encoding="utf-8").replace("\\\n", " ")
    match = re.search(rf"^{re.escape(name)}\s*\??=\s*(.+)$", text, flags=re.MULTILINE)
    assert match is not None, f"{name} is not defined in the Makefile"
    return match.group(1).strip()


def test_pylint_tier_pins_the_interpreter() -> None:
    """The tier must name the interpreter whose grammar it parses with."""
    why = "PYLINT_PYTHON must stay pypy@3.12: bare pypy follows uv's next release"
    assert _makefile_variable("PYLINT_PYTHON") == "pypy@3.12", why


def test_pylint_tier_runs_the_pinned_release_on_managed_python() -> None:
    """The tier must run the pinned Pylint on a uv-managed interpreter."""
    why = "PYLINT_VERSION must pin the reviewed Pylint release exactly"
    assert _makefile_variable("PYLINT_VERSION") == "4.0.9", why
    command = _makefile_variable("PYLINT")
    for fragment in (
        "tool run --managed-python --python $(PYLINT_PYTHON)",
        "--from 'pylint==$(PYLINT_VERSION)' pylint",
    ):
        assert fragment in command, f"PYLINT must contain {fragment!r}: {command}"


def test_pylint_reports_unparsable_modules() -> None:
    """The Pylint policy must not disable `syntax-error`."""
    config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    disabled = config["tool"]["pylint"]["messages control"]["disable"]
    why = (
        "pyproject.toml must not disable syntax-error: a module the interpreter "
        f"cannot parse would then be skipped silently; disable={disabled!r}"
    )
    assert "syntax-error" not in disabled, why


def _make_quoted(path: Path) -> str:
    """Quote a path for a shell word inside a Make recipe.

    Parameters
    ----------
    path : Path
        The path to quote.

    Returns
    -------
    str
        The shell-quoted path with each ``$`` doubled, so Make passes it to
        the shell as one literal word.
    """
    return shlex.quote(str(path)).replace("$", "$$")


def _run_make_probe(
    recipe: str, *, directory: Path = _REPO_ROOT, timeout: int = 600
) -> subprocess.CompletedProcess[str]:
    """Run one repository Make recipe for a tooling contract.

    For example, ``_run_make_probe("$(PYLINT) clean.py")`` checks a module
    through the configured tier. Reuse this test-only driver for Make probes.

    Parameters
    ----------
    recipe : str
        A fixed recipe with any generated paths shell-quoted.
    directory : Path
        The repository containing the Makefile.
    timeout : int
        Maximum seconds for the probe.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The finished Make process, with output captured.
    """
    make = shutil.which("make")
    assert make is not None, "make must be on PATH"
    return subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - fixed argument list, no shell.
        [
            make,
            "--no-print-directory",
            "-s",
            "-C",
            str(directory),
            "--eval",
            f"{_PROBE_TARGET}: ; {recipe}",
            _PROBE_TARGET,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


@pytest.mark.skipif(
    shutil.which("uv") is None or shutil.which("make") is None,
    reason="the end-to-end check needs make and uv",
)
@pytest.mark.timeout(620)
def test_configured_pylint_fails_on_an_unparsable_module(tmp_path: Path) -> None:
    """The configured tier must fail on a parse error and pass a clean module.

    This drives the real `$(PYLINT)` command, so it catches a disabled
    `syntax-error` wherever it is configured, not only in the file the
    contract above reads.
    """
    broken = tmp_path / "broken_module.py"
    broken.write_text("def broken(\n    return 1\n", encoding="utf-8")
    clean = tmp_path / "clean_module.py"
    clean.write_text('"""A clean module."""\n\nVALUE = 1\n', encoding="utf-8")

    failed = _run_make_probe(f"$(PYLINT) {_make_quoted(broken)}")
    passed = _run_make_probe(f"$(PYLINT) {_make_quoted(clean)}")

    failed_output = f"{failed.stdout}{failed.stderr}"
    passed_output = f"{passed.stdout}{passed.stderr}"
    assert failed.returncode != 0, f"a parse error must fail the tier: {failed_output}"
    assert "syntax-error" in failed.stdout, f"expected the parse error: {failed_output}"
    assert passed.returncode == 0, f"a clean module must pass: {passed_output}"


@pytest.mark.parametrize("tool", ["ruff", "ty"])
def test_tool_versions_match_make_dependencies_and_ci(tool: str) -> None:
    """Local commands and CI must use the same reviewed tool versions."""
    version = _makefile_variable(f"{tool.upper()}_VERSION")
    config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    dependencies = config["dependency-groups"]["dev"]
    assert f"{tool}=={version}" in dependencies, "The dev pin must match Make"
    workflow = yaml.safe_load(
        (_REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    )
    ci_version = workflow["jobs"]["lint-test"]["env"][f"{tool.upper()}_VERSION"]
    assert ci_version == version, "CI must install the version that Make executes"


def test_python_discovery_includes_new_scripts_and_action_code(tmp_path: Path) -> None:
    """A new Python source in any supported area must enter the lint targets."""
    git = shutil.which("git")
    assert git is not None, "Git must be installed"
    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - resolved Git and generated directory, no shell.
        [git, "init", "--quiet", str(tmp_path)],
        check=True,
        capture_output=True,
        timeout=30,
    )
    paths = {
        "pokie/new.py",
        "tests/new.py",
        "scripts/new.py",
        ".github/actions/example/new.py",
        ".github/workflows/new.py",
    }
    for relative in paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    (tmp_path / "Makefile").write_text(
        MAKEFILE_PATH.read_text(encoding="utf-8"), encoding="utf-8"
    )
    result = _run_make_probe(
        "@printf '%s\\n' $(PYTHON_TARGETS)", directory=tmp_path, timeout=30
    )
    assert result.returncode == 0, f"Source discovery must succeed: {result.stderr}"
    why = "Every production, test, script, workflow and action source must be linted"
    assert set(result.stdout.splitlines()) == paths, why


@pytest.mark.timeout(180)
def test_duplication_gate_sees_every_source_area(tmp_path: Path) -> None:
    """Copies across production, tests, scripts and hidden actions must block."""
    binary = _REPO_ROOT / ".tools/nose/nose"
    if not binary.exists():
        pytest.skip("Run make install-nose before the detector integration test")
    roots = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "tool"
    ]["nose"]["roots"]
    shutil.copyfile(_REPO_ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    source = (
        "def summarize(values):\n"
        "    total = 0\n"
        "    positives = 0\n"
        "    negatives = 0\n"
        "    for value in values:\n"
        "        total += value * value\n"
        "        if value > 0:\n"
        "            positives += 1\n"
        "        else:\n"
        "            negatives += 1\n"
        "    return total, positives, negatives\n"
    )
    for root in roots:
        directory = tmp_path / root
        directory.mkdir(parents=True)
        (directory / "sample.py").write_text(source, encoding="utf-8")
    result = _run_make_probe(
        "$(DUPLICATION_GATE) check "
        f"--repository {_make_quoted(tmp_path)} --binary {_make_quoted(binary)}",
        timeout=150,
    )
    assert result.returncode == 2, "Make must fail when the detector blocks"
    assert "duplicate code:" in result.stdout, "A valid family must be reported"
    for root in roots:
        why = f"Every area must be reported: {result.stdout} {result.stderr}"
        assert f"{root}/sample.py" in result.stdout, why
