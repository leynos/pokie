"""Shared helpers for the GitHub workflow contracts and their harness."""

import os
import re
import stat
import subprocess  # ruff: ignore[suspicious-subprocess-import] - the harness runs the checked-in install step with stub commands.
import typing as typ
from pathlib import Path

import yaml

REPOSITORY = Path(__file__).parents[1]
COVERAGE_WORKFLOWS = ("ci.yml", "coverage-main.yml")
BASELINE_FILE = ".coverage-baseline-v3.python"
RETIRED_BASELINE_FILES = (
    ".coverage-baseline.python",
    ".coverage-baseline-v2.python",
)
ACTIONLINT_INSTALL = re.compile(r"actionlint@(v\d+\.\d+\.\d+)")
# `go install` writes into GOBIN when it is set, so the workflows resolve the
# directory instead of assuming GOPATH/bin. The assignment and the PATH update
# must share one `run` body: a separate step starts a new shell, where `gobin`
# is unset and nothing reaches `GITHUB_PATH`.
GO_BIN_EXPOSURE = re.compile(
    r'gobin="\$\(go env GOBIN\)"'
    r".*?"
    r'echo "\$\{gobin:-\$\(go env GOPATH\)/bin\}" >> "\$GITHUB_PATH"',
    re.DOTALL,
)
# `make lint` depends on `duplication`, which installs the detector.
DETECTOR_SETUP = (r"make\s+install-nose(?![\w-])", r"make\s+lint(?![\w-])")
# `with` is a keyword, so the record uses the functional TypedDict form. Only
# the fields these contracts read are declared.
WorkflowStep = typ.TypedDict(
    "WorkflowStep",
    {"uses": str, "run": str, "with": dict[str, str]},
    total=False,
)

# The harness runs each install step with stub commands. GitHub runs a `run`
# body with `bash -e`; `-u` and `pipefail` are stricter, so an unset variable or
# a broken pipe in the snippet fails here too.
SHELL = ("bash", "-euo", "pipefail", "-c")
EXECUTABLE = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH | stat.S_IRUSR | stat.S_IWUSR

# The step only needs `go env` and `go install`. The install writes the binary
# where the real command would, so a test can resolve it afterwards.
GO_STUB = """#!/bin/sh
case "$1" in
  env)
    case "$2" in
      GOBIN) printf '%s\\n' "$STUB_GOBIN" ;;
      GOPATH) printf '%s\\n' "$STUB_GOPATH" ;;
      *) echo "unexpected go env $2" >&2; exit 2 ;;
    esac
    ;;
  install)
    case "$2" in
      *actionlint*) : ;;
      *) echo "unexpected go package $2" >&2; exit 2 ;;
    esac
    printf '#!/bin/sh\\nexit 0\\n' > "$STUB_GOBIN/actionlint"
    chmod +x "$STUB_GOBIN/actionlint"
    ;;
  *)
    echo "unexpected go command $1" >&2
    exit 2
    ;;
esac
"""

# Every other command is recorded and succeeds without touching the host.
RECORDING_STUB = """#!/bin/sh
printf '%s %s\\n' "$(basename "$0")" "$*" >> "$STUB_CALLS"
exit 0
"""
RECORDED_COMMANDS = ("uv", "npm", "sudo", "apt-get", "make")


class InstallStepMissingError(RuntimeError):
    """A workflow declares no step that installs Actionlint."""


def job_steps(workflow_name: str) -> list[list[WorkflowStep]]:
    """Return every job's step list for one workflow.

    Parameters
    ----------
    workflow_name : str
        Workflow file name below ``.github/workflows``.

    Returns
    -------
    list[list[WorkflowStep]]
        One step list per job, in declaration order.
    """
    path = REPOSITORY / ".github/workflows" / workflow_name
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        typ.cast("list[WorkflowStep]", job.get("steps", []))
        for job in workflow["jobs"].values()
    ]


def is_ratchet_step(step: WorkflowStep) -> bool:
    """Report whether a step delegates to the shared action with the ratchet on.

    Parameters
    ----------
    step : WorkflowStep
        One parsed workflow step.

    Returns
    -------
    bool
        ``True`` when the step is a coverage-ratchet invocation.
    """
    return (
        "generate-coverage@" in step.get("uses", "")
        and step.get("with", {}).get("with-ratchet") == "true"
    )


def pre_ratchet_steps(workflow_name: str) -> list[WorkflowStep]:
    """Return the steps that precede the coverage-ratchet step.

    Parameters
    ----------
    workflow_name : str
        Workflow file name below ``.github/workflows``.

    Returns
    -------
    list[WorkflowStep]
        Every step declared before the ratchet step in its job, in declaration
        order.
    """
    return [
        earlier
        for steps in job_steps(workflow_name)
        for index, step in enumerate(steps)
        if is_ratchet_step(step)
        for earlier in steps[:index]
    ]


def pre_ratchet_run_text(workflow_name: str) -> str:
    """Return the run commands declared before the coverage-ratchet step.

    Parameters
    ----------
    workflow_name : str
        Workflow file name below ``.github/workflows``.

    Returns
    -------
    str
        The ``run`` bodies of every step that precedes the ratchet step in its
        job, in declaration order.
    """
    return "\n".join(step.get("run", "") for step in pre_ratchet_steps(workflow_name))


def write_executable(path: Path, contents: str) -> None:
    """Write an executable shell script.

    Parameters
    ----------
    path : Path
        Destination path.
    contents : str
        Script source.
    """
    path.write_text(contents, encoding="utf-8")
    path.chmod(EXECUTABLE)


def install_step(workflow_name: str) -> tuple[dict[str, str], str]:
    """Return the declared environment and the Actionlint install step body.

    Parameters
    ----------
    workflow_name : str
        Workflow file name below ``.github/workflows``.

    Returns
    -------
    tuple[dict[str, str], str]
        The environment variables the workflow and its jobs declare, and the
        ``run`` body of the first step that installs Actionlint.

    Raises
    ------
    InstallStepMissingError
        When no step in the workflow installs Actionlint.
    """
    path = REPOSITORY / ".github/workflows" / workflow_name
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    declared: dict[str, str] = {
        key: value
        for job in document["jobs"].values()
        for key, value in job.get("env", {}).items()
    }
    declared |= document.get("env", {})
    for steps in job_steps(workflow_name):
        for step in steps:
            body = step.get("run", "")
            if ACTIONLINT_INSTALL.search(body):
                return declared, body
    raise InstallStepMissingError(workflow_name)


def run_install_step(
    workflow_name: str, runtime: dict[str, typ.Any]
) -> subprocess.CompletedProcess[str]:
    """Execute one workflow's install step against the stub commands.

    Parameters
    ----------
    workflow_name : str
        Workflow file name below ``.github/workflows``.
    runtime : dict[str, typ.Any]
        The ``stub_runtime`` fixture.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The completed step, with its output captured.
    """
    job_env, body = install_step(workflow_name)
    return subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - fixed argument list, no shell.
        [*SHELL, body],
        env=runtime["env"] | job_env,
        capture_output=True,
        text=True,
        check=False,
    )


def stub_environment(tmp_path: Path) -> dict[str, typ.Any]:
    """Create stub commands and the paths the install step writes.

    Parameters
    ----------
    tmp_path : Path
        Pytest's per-test temporary directory.

    Returns
    -------
    dict[str, typ.Any]
        ``env`` for the step, plus the ``go_bin``, ``calls`` and
        ``github_path`` paths the assertions read.
    """
    bin_dir = tmp_path / "bin"
    go_bin = tmp_path / "gobin"
    go_path = tmp_path / "gopath" / "bin"
    calls = tmp_path / "calls.log"
    github_path = tmp_path / "github_path"
    bin_dir.mkdir()
    go_bin.mkdir()
    go_path.mkdir(parents=True)
    write_executable(bin_dir / "go", GO_STUB)
    for name in RECORDED_COMMANDS:
        write_executable(bin_dir / name, RECORDING_STUB)
    environment = {
        "PATH": os.pathsep.join((str(bin_dir), "/usr/bin", "/bin")),
        "GITHUB_PATH": str(github_path),
        "STUB_GOBIN": str(go_bin),
        "STUB_GOPATH": str(go_path.parent),
        "STUB_CALLS": str(calls),
    }
    return {
        "env": environment,
        "go_bin": go_bin,
        "calls": calls,
        "github_path": github_path,
    }
