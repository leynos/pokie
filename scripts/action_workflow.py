#!/usr/bin/env -S uv run --script
# Match the repository's Python 3.14 lint and CI runtime.
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "cyclopts==4.25.2",
#     "pyyaml==6.0.3",
# ]
# ///
"""Expose composite action steps to actionlint's workflow checks.

The adapter preserves action inputs and steps; action-validator owns metadata
validation. It is used only by ``make lint-actions`` and is not a runtime API.
"""

from pathlib import Path  # ruff: ignore[typing-only-standard-library-import] - Cyclopts resolves the runtime CLI annotation.

import cyclopts
import yaml

app = cyclopts.App()


def action_workflow(path: Path) -> str:
    """Render a workflow retaining the composite action's steps and inputs.

    For example, ``action_workflow(Path(".github/actions/build/action.yml"))``
    returns YAML that actionlint can check as a manually dispatched workflow.

    Returns
    -------
    str
        Workflow YAML preserving the inputs and executable action steps.
    """
    action = yaml.safe_load(path.read_text(encoding="utf-8"))
    inputs = {
        name: {**definition, "type": "string"}
        for name, definition in action.get("inputs", {}).items()
    }
    workflow = {
        "name": action["name"],
        "on": {"workflow_dispatch": {"inputs": inputs}},
        "jobs": {
            "action": {"runs-on": "ubuntu-latest", "steps": action["runs"]["steps"]}
        },
    }
    return yaml.safe_dump(workflow, sort_keys=False)


@app.default
def main(path: Path) -> None:
    """Print an action's workflow representation for the lint pipeline.

    For example, ``uv run --script scripts/action_workflow.py action.yml`` emits
    YAML that can be piped to ``actionlint -`` without executing action steps.
    """
    print(action_workflow(path), end="")


if __name__ == "__main__":
    app()
