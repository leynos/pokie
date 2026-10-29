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
            case ast.ImportFrom():
                modules.update(imported_modules(node))
    return {
        name
        for name in modules
        if name.split(".")[0] in FORBIDDEN
        or name.startswith(("job_corpus.adapters", "pathlib."))
    }


def imported_modules(node: ast.ImportFrom) -> set[str]:
    """Resolve imports relative to the domain, such as ``from . import adapters``.

    Returns
    -------
    set[str]
        Module and selected imported names used by the boundary filter.
    """
    prefix = "job_corpus." if node.level else ""
    module = prefix + (node.module or "")
    names = {module}
    if node.module in {None, "job_corpus", "pathlib"}:
        stem = module.rstrip(".")
        names.update(f"{stem}.{alias.name}" for alias in node.names)
    names.discard("pathlib.PurePosixPath")
    return names


def check_domain_modules(corpus_root: pathlib.Path) -> None:
    """Check concrete domain sources; for example, adapters are forbidden imports."""
    for name in DOMAIN_MODULES:
        path = corpus_root / f"{name}.py"
        if name == "report" and not path.exists():
            continue  # The report module lands in EP-M2.
        assert path.exists(), f"domain module {name} must exist under corpus_root"
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
    "is_missing", [False, True], ids=["repository", "misplaced-root"]
)
def test_domain_modules_keep_io_outside_policy(
    corpus_root: pathlib.Path, tmp_path: pathlib.Path, *, is_missing: bool
) -> None:
    """Validate concrete domain modules and reject an empty misplaced corpus root."""
    if is_missing:
        with pytest.raises(AssertionError, match="domain module"):
            check_domain_modules(tmp_path)
    else:
        check_domain_modules(corpus_root)


@pytest.mark.parametrize(
    "source",
    [
        "import os",
        "from subprocess import run",
        "from job_corpus import adapters",
        "from job_corpus.adapters import toml_jobs",
        "from pathlib import Path",
        "from pathlib import PosixPath",
        "from . import adapters",
        "from .adapters import toml_jobs",
    ],
)
def test_boundary_detector_rejects_forbidden_dependencies(source: str) -> None:
    """The boundary check itself has permanent failing-import controls."""
    assert forbidden_imports(source), (
        "the architecture detector must reject the forbidden import"
    )


@pytest.mark.parametrize(
    "source",
    [
        "from . import model",
        "from .model import Failure",
        "from pathlib import PurePosixPath",
    ],
)
def test_boundary_detector_accepts_pure_imports(source: str) -> None:
    """Relative domain imports remain valid when they do not reach adapters."""
    assert not forbidden_imports(source), "pure domain imports must remain permitted"
