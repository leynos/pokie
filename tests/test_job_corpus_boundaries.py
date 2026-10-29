"""Architecture checks for the corpus's pure domain modules."""

import ast
import typing as typ

import pytest

if typ.TYPE_CHECKING:
    import pathlib

DOMAIN_MODULES = ("model", "findings", "policy", "comparison", "audit", "report")
FORBIDDEN = {"tomllib", "subprocess", "os", "io", "shutil", "tempfile"}


def forbidden_imports(source: str) -> set[str]:
    """Return forbidden module imports; for example, ``import os`` yields os.

    Returns
    -------
    set[str]
        The detected names or expanded evidence identifiers.
    """
    modules = set()
    for node in ast.walk(ast.parse(source)):
        match node:
            case ast.Import(names=names):
                modules.update(alias.name for alias in names)
            case ast.ImportFrom(module="pathlib", names=names):
                modules.update(
                    f"pathlib.{alias.name}"
                    for alias in names
                    if alias.name != "PurePosixPath"
                )
            case ast.ImportFrom(module="job_corpus", names=names):
                modules.update(f"job_corpus.{alias.name}" for alias in names)
            case ast.ImportFrom(module=module):
                modules.add(module or "")
    return {
        name
        for name in modules
        if name.split(".")[0] in FORBIDDEN
        or name.startswith(("job_corpus.adapters", "pathlib."))
    }


def test_domain_modules_keep_io_outside_policy(corpus_root: pathlib.Path) -> None:
    """Loaded values are the sole input to every currently implemented domain module."""
    for name in DOMAIN_MODULES:
        path = corpus_root / f"{name}.py"
        if not path.exists():
            continue  # The report module lands in EP-M2.
        source = path.read_text()
        assert not forbidden_imports(source), name
        tree = ast.parse(source)
        attributes = {
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
        }
        path_attributes = {
            attribute for attribute in attributes if attribute.startswith("pathlib.")
        }
        assert path_attributes <= {"pathlib.PurePosixPath"}, name


@pytest.mark.parametrize(
    "source",
    [
        "import os",
        "from subprocess import run",
        "from job_corpus import adapters",
        "from job_corpus.adapters import toml_jobs",
        "from pathlib import Path",
        "from pathlib import PosixPath",
    ],
)
def test_boundary_detector_rejects_forbidden_dependencies(source: str) -> None:
    """The boundary check itself has permanent failing-import controls."""
    assert forbidden_imports(source), (
        "the architecture detector must reject the forbidden import"
    )
