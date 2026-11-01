"""Tests for the externally visible GitHub workflow contracts."""

import re
import typing as typ
from pathlib import Path

import pytest
import yaml

REPOSITORY = Path(__file__).parents[1]
COVERAGE_WORKFLOWS = ("ci.yml", "coverage-main.yml")
BASELINE_FILE = ".coverage-baseline-v2.python"
RETIRED_BASELINE_FILE = ".coverage-baseline.python"


def test_act_runtime_excludes_vulnerable_releases() -> None:
    """Act must include the fixes for the command and cache injection advisories."""
    path = Path(__file__).parents[1] / ".github/workflows/act-validation.yml"
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    pin = workflow["jobs"]["act-validation"]["env"]["ACT_VERSION"]
    version = tuple(map(int, pin.removeprefix("v").split(".")))
    why = "Act must include the CVE-2026-34041 and CVE-2026-34042 fixes"
    assert version >= (0, 2, 86), why


def test_pure_wheel_action_preserves_upload_and_output_contracts() -> None:
    """The wheel action defaults to upload and maps its configured output path."""
    repository = Path(__file__).parents[1]
    action_path = repository / ".github/actions/pure-python-wheel/action.yml"
    action = yaml.safe_load(action_path.read_text(encoding="utf-8"))

    upload_input = action["inputs"]["upload-artefact"]
    why = "The reusable wheel action must upload artefacts unless disabled"
    assert upload_input["default"] == "true", why

    steps = action["runs"]["steps"]
    upload_step = next(
        step for step in steps if step.get("name") == "Upload wheel artefact"
    )
    why = "The upload step must honour the upload-artefact input"
    assert upload_step["if"] == "inputs.upload-artefact == 'true'", why

    build_step = next(step for step in steps if step.get("name") == "Build wheel")
    why = "The output directory input must reach the build through OUT_DIR"
    assert build_step["env"]["OUT_DIR"] == "${{ inputs.out-dir }}", why


def test_act_smoke_disables_upload_and_handles_output_paths_with_spaces() -> None:
    """The Act smoke job disables uploads and uses a spaced output path."""
    repository = Path(__file__).parents[1]
    workflow_path = repository / ".github/workflows/act-smoke.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["pure-wheel"]["steps"]

    build_step = next(step for step in steps if step.get("name") == "Build pure wheel")
    why = "The smoke job must disable artefact upload and exercise a spaced path"
    assert build_step["with"]["upload-artefact"] == "false", why
    why = "The smoke job must exercise an output directory containing a space"
    assert " " in build_step["with"]["out-dir"], why


def ratchet_steps(workflow_name: str) -> list[dict[str, typ.Any]]:
    """Return the coverage-ratchet steps declared by one workflow.

    Parameters
    ----------
    workflow_name : str
        Workflow file name below ``.github/workflows``.

    Returns
    -------
    list[dict[str, Any]]
        Steps that delegate to the shared coverage action with the ratchet on.
    """
    path = REPOSITORY / ".github/workflows" / workflow_name
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        step
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "generate-coverage@" in step.get("uses", "")
        and step.get("with", {}).get("with-ratchet") == "true"
    ]


@pytest.mark.parametrize("workflow_name", COVERAGE_WORKFLOWS)
def test_each_coverage_workflow_runs_one_ratchet(workflow_name: str) -> None:
    """A second ratchet step would hide which baseline the workflow enforces."""
    why = f"{workflow_name} must run the coverage ratchet exactly once"
    assert len(ratchet_steps(workflow_name)) == 1, why


@pytest.mark.parametrize("workflow_name", COVERAGE_WORKFLOWS)
def test_coverage_workflows_share_the_committed_baseline(workflow_name: str) -> None:
    """Both ratchet runs must start from the same committed measurement."""
    step = ratchet_steps(workflow_name)[0]
    configured = step["with"].get("baseline-python-file")
    why = f"{workflow_name} must ratchet against {BASELINE_FILE}"
    assert configured == BASELINE_FILE, why


@pytest.mark.parametrize("workflow_name", COVERAGE_WORKFLOWS)
def test_coverage_workflows_do_not_name_the_retired_baseline(
    workflow_name: str,
) -> None:
    """Naming the retired path would restore its scaffold-era cached figure."""
    path = REPOSITORY / ".github/workflows" / workflow_name
    why = f"{workflow_name} must not name {RETIRED_BASELINE_FILE}"
    assert RETIRED_BASELINE_FILE not in path.read_text(encoding="utf-8"), why


def test_committed_python_baseline_is_one_percentage_line() -> None:
    """The shared action parses one percentage, so the file must hold only that."""
    text = (REPOSITORY / BASELINE_FILE).read_text(encoding="utf-8")
    why = f"{BASELINE_FILE} must hold exactly one percentage line"
    assert re.fullmatch(r"\d{1,3}(?:\.\d+)?\n", text), why
    why = f"{BASELINE_FILE} must be a percentage between 0 and 100"
    assert 0.0 <= float(text) <= 100.0, why
