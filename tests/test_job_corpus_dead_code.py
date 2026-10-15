"""Guard that keeps the Vulture whitelist from rotting into a blanket exemption.

`tests/job_corpus/vulture_whitelist.py` names declarations that are live even
though no Python expression spells them. An entry that has outlived its
justification would quietly exempt a name from dead-code detection, so this
module fails when the whitelist and Vulture disagree in either direction: every
entry must still be a name Vulture reports as unused, and every name Vulture
reports must be declared.

That makes the whitelist self-clearing. When EP-M1's policy and EP-M2's report
start reading a field, Vulture stops reporting it and this test fails until the
entry is deleted.
"""

import ast
import pathlib
import re
import subprocess  # ruff: ignore[suspicious-subprocess-import] - the guard must exercise the same detector the gate runs.
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

SCAN_TARGET = REPO_ROOT / "tests"

WHITELIST = SCAN_TARGET / "job_corpus" / "vulture_whitelist.py"

_FINDING = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+): unused \w+ '(?P<name>[^']+)'")

_VULTURE_FOUND_UNUSED_CODE = 3
"""Vulture's documented exit status when it has findings to report."""


def defining_class_by_line(tree: ast.Module) -> dict[int, str]:
    """Map each class-body declaration to the class that declares it.

    Parameters
    ----------
    tree : ast.Module
        A parsed module.

    Returns
    -------
    dict[int, str]
        The line number of every statement declared directly in a class body,
        mapped to its class name. A module-level declaration is absent, so the
        caller reports it unqualified.
    """
    classes: dict[int, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for statement in node.body:
            lineno = getattr(statement, "lineno", None)
            if lineno is not None:
                classes[lineno] = node.name
    return classes


def qualify(classes: dict[int, str], lineno: int, name: str) -> str:
    """Return a Vulture finding as a dotted name.

    Parameters
    ----------
    classes : dict[int, str]
        A module's class-body declarations, as `defining_class_by_line`
        returns them.
    lineno : int
        The line Vulture reported.
    name : str
        The bare name Vulture reported.

    Returns
    -------
    str
        ``Class.member`` for a class-body declaration, else the bare name. This
        is the form the whitelist uses once its module alias is dropped, so an
        enum member and a same-named module-level constant stay distinct.

    Examples
    --------
    >>> qualify({7: "Colour"}, 7, "RED")
    'Colour.RED'
    >>> qualify({}, 3, "helper")
    'helper'
    """
    declaring = classes.get(lineno)
    return f"{declaring}.{name}" if declaring else name


def declared_names() -> set[str]:
    """Return every name the whitelist declares, unqualified.

    Returns
    -------
    set[str]
        The entries of every tuple assignment in the whitelist, with the module
        alias removed. For example ``model.Failure.STATIC`` becomes
        ``Failure.STATIC`` and ``ports.ProgramRunner`` becomes
        ``ProgramRunner``.
    """
    tree = ast.parse(WHITELIST.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Tuple):
            continue
        for element in node.value.elts:
            parts = attribute_chain(element)
            names.add(".".join(parts[1:]) if len(parts) > 1 else parts[0])
    return names


def attribute_chain(node: ast.expr) -> list[str]:
    """Return the dotted components of an attribute expression.

    Parameters
    ----------
    node : ast.expr
        One element of a whitelist tuple, such as ``model.Failure.STATIC``.

    Returns
    -------
    list[str]
        The components in order, such as ``["model", "Failure", "STATIC"]``.
        An expression that is not an attribute chain yields its own source
        shape rather than raising, so the caller's assertion reports it.
    """
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return list(reversed(parts))


def reported_names() -> set[str]:
    """Return every name Vulture reports once the whitelist is excluded.

    Returns
    -------
    set[str]
        Qualified names, as `qualify` produces them.
    """
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - resolved interpreter, literal arguments, no shell.
        [
            sys.executable,
            "-m",
            "vulture",
            str(SCAN_TARGET),
            f"--exclude={WHITELIST.name}",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if result.returncode not in {0, _VULTURE_FOUND_UNUSED_CODE}:
        pytest.fail(f"vulture could not run: {result.stderr.strip()}")
    tree_by_path: dict[str, dict[int, str]] = {}
    names: set[str] = set()
    for line in result.stdout.splitlines():
        match = _FINDING.match(line)
        if match is None:
            continue
        path = match.group("path")
        if path not in tree_by_path:
            source = pathlib.Path(path)
            tree_by_path[path] = defining_class_by_line(
                ast.parse(source.read_text(encoding="utf-8"))
            )
        names.add(
            qualify(
                tree_by_path[path],
                int(match.group("line")),
                match.group("name"),
            )
        )
    return names


def test_whitelist_matches_vulture() -> None:
    """The whitelist must declare exactly what Vulture still reports.

    A declared name Vulture no longer reports is a stale entry: the consuming
    code has landed, so the exemption must go. A reported name the whitelist
    does not declare means a genuinely dead declaration reached the corpus
    harness, which the `dead-code` gate would reject but whose cause this test
    names directly.
    """
    declared = declared_names()
    reported = reported_names()
    stale = sorted(declared - reported)
    undeclared = sorted(reported - declared)
    why = (
        f"stale whitelist entries (delete them, their consumers exist): "
        f"{stale}; undeclared unused names: {undeclared}"
    )
    assert declared == reported, why
