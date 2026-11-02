"""Behavioural checks for the install step each coverage job runs.

The contract tests read the workflow text. These tests execute the real ``run``
body against stub commands, so a snippet that resolves the wrong directory, or
that never reaches ``GITHUB_PATH``, fails here rather than on a runner where
Actionlint would silently be missing.
"""

import os
import re
import shutil
import typing as typ

import pytest
from workflow_support import (
    COVERAGE_WORKFLOWS,
    run_install_step,
    stub_environment,
)

if typ.TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("workflow_name", COVERAGE_WORKFLOWS)
def test_install_step_exposes_the_resolved_go_bin(
    workflow_name: str,
    tmp_path: Path,
) -> None:
    """Actionlint must be resolvable from the PATH the step publishes."""
    stub_runtime = stub_environment(tmp_path)
    completed = run_install_step(workflow_name, stub_runtime)
    why = f"{workflow_name} install step failed: {completed.stderr}"
    assert completed.returncode == 0, why

    exposed = stub_runtime["github_path"].read_text(encoding="utf-8").split()
    why = f"{workflow_name} must publish exactly the resolved Go binary directory"
    assert exposed == [str(stub_runtime["go_bin"])], why

    search_path = os.pathsep.join([*exposed, stub_runtime["env"]["PATH"]])
    why = f"{workflow_name} must make Actionlint resolvable from the published PATH"
    assert shutil.which("actionlint", path=search_path) is not None, why


def test_coverage_main_installs_the_pinned_detector(tmp_path: Path) -> None:
    """The main job must provision the detector its suite probes for."""
    stub_runtime = stub_environment(tmp_path)
    completed = run_install_step("coverage-main.yml", stub_runtime)
    why = f"coverage-main.yml install step failed: {completed.stderr}"
    assert completed.returncode == 0, why

    calls = stub_runtime["calls"].read_text(encoding="utf-8")
    why = "coverage-main.yml must run `make install-nose` before measuring"
    assert re.search(r"^make install-nose$", calls, re.MULTILINE), why
