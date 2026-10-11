"""Behavioural checks for composite action validation."""

import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] - integration tests drive the installed Actionlint.
import typing as typ

if typ.TYPE_CHECKING:
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
    assert workflow["on"]["workflow_dispatch"]["inputs"]["output"] == {
        "description": "Output directory",
        "default": "dist",
        "type": "string",
    }, "Action inputs must remain available to actionlint's expression checks"
    assert workflow["jobs"]["action"]["steps"] == [
        {"shell": "bash", "run": 'echo "${{ inputs.output }}"'}
    ], "The adapter must preserve the executable steps without escaping expressions"


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
    assert workflow["jobs"]["action"]["steps"] == [], (
        "CLI output must be valid workflow YAML"
    )


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
    assert (result.returncode == 0) == is_valid, (
        f"Actionlint must validate composite expressions: {result.stdout}"
    )
