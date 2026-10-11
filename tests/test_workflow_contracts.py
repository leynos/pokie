"""Tests for the externally visible GitHub workflow contracts."""

import json
import os
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] - Node integration tests execute the repository helper.
from pathlib import Path

import yaml


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


def test_codescene_workflow_helper_emits_repository_variable_payload() -> None:
    """The workflow helper sends the configured repository variable payload."""
    repository = Path(__file__).parents[1].resolve()
    helper_path = (repository / ".github/scripts/update_codescene_sha.js").resolve()
    node = shutil.which("node")
    why = "The CodeScene helper integration test requires Node.js on PATH"
    assert node is not None, why
    node_path = str(Path(node).resolve())

    known_sha = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    environment = os.environ.copy()
    environment["SHA"] = known_sha
    javascript = """
const helperPath = process.argv[2];
const github = {
  rest: {
    actions: {
      updateRepoVariable: async (payload) => {
        process.stdout.write(JSON.stringify(payload));
      },
    },
  },
};
const context = { repo: { owner: 'example-owner', repo: 'different-repository' } };
require(helperPath)({ github, context }).catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
"""
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - resolved Node and repository helper, no shell.
        [node_path, "-", str(helper_path)],
        capture_output=True,
        check=False,
        cwd=repository,
        env=environment,
        input=javascript,
        text=True,
        timeout=30,
    )

    why = f"The CodeScene helper must complete successfully: {result.stderr}"
    assert result.returncode == 0, why
    expected_payload = {
        "owner": "example-owner",
        "repo": "different-repository",
        "name": "CODESCENE_CLI_SHA256",
        "value": known_sha,
    }
    why = "The helper must emit the complete owner, repository, name, and SHA payload"
    assert json.loads(result.stdout) == expected_payload, why
