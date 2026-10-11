"""Behavioural checks for composite action validation."""

import os
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] - integration tests drive the installed Actionlint.
from pathlib import Path

import pytest
import yaml

from scripts.action_workflow import action_workflow, app


def test_action_adapter_preserves_shell_steps_and_inputs(tmp_path: Path) -> None:
    """Shell and expression diagnostics must survive the workflow adapter."""
    path = tmp_path / "action.yml"
    path.write_text(
        "name: Example\n"
        "inputs:\n"
        "  output:\n"
        "    description: Output directory\n"
        "    default: dist\n"
        "runs:\n"
        "  using: composite\n"
        "  steps:\n"
        "    - shell: bash\n"
        '      run: echo "${{ inputs.output }}"\n',
        encoding="utf-8",
    )
    workflow = yaml.safe_load(action_workflow(path))
    expected_inputs = {
        "description": "Output directory",
        "default": "dist",
        "type": "string",
    }
    inputs = workflow["on"]["workflow_dispatch"]["inputs"]
    assert inputs["output"] == expected_inputs, "Actionlint must see the action inputs"
    expected_steps = [{"shell": "bash", "run": 'echo "${{ inputs.output }}"'}]
    steps = workflow["jobs"]["action"]["steps"]
    assert steps == expected_steps, "Actionlint must see unchanged executable steps"


def test_action_adapter_cli_emits_parseable_workflow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The actual CLI must emit only the workflow YAML on standard output."""
    path = tmp_path / "action.yml"
    path.write_text(
        "name: Example\nruns:\n  using: composite\n  steps: []\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exit_info:
        app([str(path)])
    assert exit_info.value.code == 0, "Rendering valid YAML must exit successfully"
    workflow = yaml.safe_load(capsys.readouterr().out)
    why = "CLI output must be valid workflow YAML"
    assert workflow["jobs"]["action"]["steps"] == [], why


@pytest.mark.timeout(180)
def test_action_adapter_runs_outside_project_environment(tmp_path: Path) -> None:
    """The adapter's uv metadata must supply dependencies outside the project."""
    adapter = tmp_path / "action_workflow.py"
    shutil.copyfile(Path(__file__).parents[1] / "scripts/action_workflow.py", adapter)
    action = tmp_path / "action.yml"
    action.write_text(
        "name: Example\nruns:\n  using: composite\n  steps: []\n", encoding="utf-8"
    )
    environment = os.environ.copy()
    environment.pop("VIRTUAL_ENV", None)
    uv = shutil.which("uv")
    assert uv is not None, "Standalone script validation requires uv on PATH"
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - resolved uv command and generated fixture, no shell.
        [
            uv,
            "run",
            "--no-project",
            "--python",
            "3.14",
            "--script",
            str(adapter),
            str(action),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env=environment,
        timeout=120,
    )
    why = f"Standalone uv script must succeed: {result.stderr}"
    assert result.returncode == 0, why
    workflow = yaml.safe_load(result.stdout)
    why = "Standalone action adapter must preserve an empty composite step list"
    assert workflow["jobs"]["action"]["steps"] == [], why


@pytest.mark.parametrize("is_valid", [True, False], ids=["valid", "invalid-input"])
def test_actionlint_checks_adapted_action_expressions(
    tmp_path: Path, *, is_valid: bool
) -> None:
    """The real linter must reject action expressions referencing missing inputs."""
    path = tmp_path / "action.yml"
    input_name = "output" if is_valid else "missing"
    path.write_text(
        "name: Example\n"
        "inputs:\n"
        "  output:\n"
        "    description: Output directory\n"
        "runs:\n"
        "  using: composite\n"
        "  steps:\n"
        "    - shell: bash\n"
        f'      run: echo "${{{{ inputs.{input_name} }}}}"\n',
        encoding="utf-8",
    )
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(action_workflow(path), encoding="utf-8")
    actionlint = shutil.which("actionlint")
    if actionlint is None:
        pytest.skip("The Actionlint integration check requires actionlint on PATH")
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - resolved detector and generated fixture, no shell.
        [actionlint, str(workflow)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    why = f"Actionlint must validate composite expressions: {result.stdout}"
    assert (result.returncode == 0) == is_valid, why
