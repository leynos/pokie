"""Tests for the externally visible GitHub workflow contracts."""

import re
import typing as typ
from pathlib import Path

import pytest
import yaml

REPOSITORY = Path(__file__).parents[1]
COVERAGE_WORKFLOWS = ("ci.yml", "coverage-main.yml")
BASELINE_FILE = ".coverage-baseline-v3.python"
RETIRED_BASELINE_FILES = (
    ".coverage-baseline.python",
    ".coverage-baseline-v2.python",
)
ACTIONLINT_INSTALL = re.compile(r"actionlint@(v\d+\.\d+\.\d+)")


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


def job_steps(workflow_name: str) -> list[list[dict[str, typ.Any]]]:
    """Return every job's step list for one workflow.

    Parameters
    ----------
    workflow_name : str
        Workflow file name below ``.github/workflows``.

    Returns
    -------
    list[list[dict[str, Any]]]
        One step list per job, in declaration order.
    """
    path = REPOSITORY / ".github/workflows" / workflow_name
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [job.get("steps", []) for job in workflow["jobs"].values()]


def is_ratchet_step(step: dict[str, typ.Any]) -> bool:
    """Report whether a step delegates to the shared action with the ratchet on.

    Parameters
    ----------
    step : dict[str, Any]
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


def only_ratchet_step(workflow_name: str) -> dict[str, typ.Any]:
    """Return the single coverage-ratchet step declared by one workflow.

    Parameters
    ----------
    workflow_name : str
        Workflow file name below ``.github/workflows``.

    Returns
    -------
    dict[str, Any]
        The step that delegates to the shared coverage action with the ratchet
        on.
    """
    steps = [
        step
        for job in job_steps(workflow_name)
        for step in job
        if is_ratchet_step(step)
    ]
    why = f"{workflow_name} must run the coverage ratchet exactly once"
    assert len(steps) == 1, why
    return steps[0]


@pytest.mark.parametrize("workflow_name", COVERAGE_WORKFLOWS)
def test_each_coverage_workflow_runs_one_ratchet(workflow_name: str) -> None:
    """A second ratchet step would hide which baseline the workflow enforces."""
    only_ratchet_step(workflow_name)


@pytest.mark.parametrize("workflow_name", COVERAGE_WORKFLOWS)
def test_coverage_workflows_share_the_committed_baseline(workflow_name: str) -> None:
    """Both ratchet runs must start from the same committed measurement."""
    step = only_ratchet_step(workflow_name)
    configured = step["with"].get("baseline-python-file")
    why = f"{workflow_name} must ratchet against {BASELINE_FILE}"
    assert configured == BASELINE_FILE, why


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
    bodies = [
        earlier.get("run", "")
        for steps in job_steps(workflow_name)
        for index, step in enumerate(steps)
        if is_ratchet_step(step)
        for earlier in steps[:index]
    ]
    return "\n".join(bodies)


def actionlint_pin(workflow_name: str) -> str:
    """Return the Actionlint release one workflow installs before measuring.

    Parameters
    ----------
    workflow_name : str
        Workflow file name below ``.github/workflows``.

    Returns
    -------
    str
        The pinned release tag, such as ``v1.7.12``.
    """
    match = ACTIONLINT_INSTALL.search(pre_ratchet_run_text(workflow_name))
    why = f"{workflow_name} must install Actionlint before measuring coverage"
    assert match is not None, why
    return match.group(1)


@pytest.mark.parametrize("workflow_name", COVERAGE_WORKFLOWS)
def test_coverage_workflows_provision_the_probed_test_tools(
    workflow_name: str,
) -> None:
    """A skipped test drops its own covered lines from the ratchet figure."""
    setup = pre_ratchet_run_text(workflow_name)
    # `make lint` depends on `duplication`, which installs the detector.
    detector_setup = ("make install-nose", "make lint")
    why = f"{workflow_name} must install the duplication detector the suite probes"
    assert any(command in setup for command in detector_setup), why


def test_coverage_workflows_pin_the_same_actionlint() -> None:
    """One pin keeps both ratchet runs on the same linter release."""
    pins = {name: actionlint_pin(name) for name in COVERAGE_WORKFLOWS}
    why = f"Both coverage workflows must install one Actionlint release: {pins}"
    assert len(set(pins.values())) == 1, why


@pytest.mark.parametrize("workflow_name", COVERAGE_WORKFLOWS)
def test_coverage_workflows_do_not_name_a_retired_baseline(
    workflow_name: str,
) -> None:
    """Naming a retired path could restore its cached figure."""
    path = REPOSITORY / ".github/workflows" / workflow_name
    text = path.read_text(encoding="utf-8")
    why = f"{workflow_name} must not name any of {RETIRED_BASELINE_FILES}"
    assert not any(retired in text for retired in RETIRED_BASELINE_FILES), why


def test_committed_python_baseline_is_one_percentage_line() -> None:
    """The shared action parses one percentage, so the file must hold only that."""
    text = (REPOSITORY / BASELINE_FILE).read_text(encoding="utf-8")
    why = f"{BASELINE_FILE} must hold exactly one percentage line"
    assert re.fullmatch(r"\d{1,3}(?:\.\d+)?\n", text), why
    why = f"{BASELINE_FILE} must be a percentage between 0 and 100"
    assert 0.0 <= float(text) <= 100.0, why
