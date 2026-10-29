"""Architecture checks for the corpus's pure domain modules."""

import ast
import typing as typ

import pytest

if typ.TYPE_CHECKING:
    import collections.abc as cabc
    import pathlib

DOMAIN_MODULES = (
    "model",
    "findings",
    "policy",
    "comparison",
    "audit",
    "register_policy",
    "report",
)
FORBIDDEN = {"tomllib", "subprocess", "os", "io", "shutil", "tempfile"}


def forbidden_imports(tree: ast.AST) -> set[str]:
    """Return forbidden imports from a tree; ``import os`` yields ``os``.

    Parameters
    ----------
    tree : ast.AST
        The parsed source tree to inspect.

    Returns
    -------
    set[str]
        Forbidden module or imported member names.
    """
    modules = set()
    for node in ast.walk(tree):
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

    Parameters
    ----------
    node : ast.ImportFrom
        The import statement whose module and member names are resolved.

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


def pathlib_member_accesses(tree: ast.AST) -> cabc.Iterator[str]:
    """Yield imported pathlib members, normalizing module aliases.

    For example, ``pl.Path`` yields ``pathlib.Path`` after its alias import.
    A pure path's ``parent`` remains an instance property, not a module member.

    Parameters
    ----------
    tree : ast.AST
        The already parsed tree shared with the import check.

    Yields
    ------
    str
        Each direct pathlib member under the canonical module name.
    """
    aliases = set()
    members = []
    for node in ast.walk(tree):
        match node:
            case ast.Import(names=names):
                aliases.update(
                    alias.asname or "pathlib"
                    for alias in names
                    if alias.name == "pathlib"
                )
            case ast.Attribute(value=ast.Name(id=qualifier), attr=member):
                members.append((qualifier, member))
    for qualifier, member in members:
        if qualifier in aliases:
            yield f"pathlib.{member}"


def check_domain_modules(corpus_root: pathlib.Path) -> None:
    """Check concrete domain sources; for example, adapters are forbidden imports.

    Parameters
    ----------
    corpus_root : pathlib.Path
        The directory containing the implemented domain modules.
    """
    for name in DOMAIN_MODULES:
        path = corpus_root / f"{name}.py"
        if name == "report" and not path.exists():
            continue  # The report module lands in EP-M2.
        assert path.exists(), f"domain module {name} must exist under corpus_root"
        tree = ast.parse(path.read_text())
        forbidden = forbidden_imports(tree)
        assert not forbidden, f"{name} imports forbidden modules: {sorted(forbidden)}"
        disallowed = set(pathlib_member_accesses(tree)) - {"pathlib.PurePosixPath"}
        assert not disallowed, f"{name} uses pathlib attributes: {sorted(disallowed)}"


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
    ("source", "is_allowed"),
    [
        ("import os", False),
        ("from subprocess import run", False),
        ("from job_corpus import adapters", False),
        ("from job_corpus.adapters import toml_jobs", False),
        ("from pathlib import Path", False),
        ("from pathlib import PosixPath", False),
        ("from . import adapters", False),
        ("from .adapters import toml_jobs", False),
        ("from . import model", True),
        ("from .model import Failure", True),
        ("from pathlib import PurePosixPath", True),
    ],
)
def test_boundary_detector_classifies_imports(source: str, *, is_allowed: bool) -> None:
    """Pure domain imports pass while concrete and relative adapter imports fail."""
    why = f"the architecture detector must classify {source!r} as allowed={is_allowed}"
    assert bool(forbidden_imports(ast.parse(source))) is not is_allowed, why


@pytest.mark.parametrize(
    ("access", "is_allowed"),
    [
        ("Path.cwd()", False),
        ("PurePosixPath('example')", True),
        ("PurePosixPath('example').parent", True),
    ],
)
def test_pathlib_alias_preserves_only_pure_path_access(
    tmp_path: pathlib.Path, access: str, *, is_allowed: bool
) -> None:
    """Aliases retain pure path construction and cannot hide filesystem access."""
    for name in DOMAIN_MODULES:
        if name == "report":
            continue
        source = (
            f"import pathlib as pl\nvalue = pl.{access}\n" if name == "policy" else ""
        )
        (tmp_path / f"{name}.py").write_text(source)
    if is_allowed:
        check_domain_modules(tmp_path)
    else:
        with pytest.raises(AssertionError, match="uses pathlib attributes"):
            check_domain_modules(tmp_path)
