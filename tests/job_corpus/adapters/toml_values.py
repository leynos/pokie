r"""Scalar coercion for ``job.toml`` documents.

This module is internal to the ``job_corpus.adapters`` package, and its
underscore-prefixed names say as much: `job_corpus.adapters.toml_jobs` walks a
document's schema and calls one helper per value, so the walk reads as the
schema it implements while these helpers stay shared between its shapes.
Nothing outside the package has a reason to import from here.

Coercion never defaults. A value of the wrong shape is a defect in the
evidence, not a value to guess at, so a failure names the corpus-relative file
and the dotted TOML key it came from. Each helper accordingly takes a ``where``
pair holding those two things, and every diagnostic the module raises comes
from `_fail`: a guard calls it, and so does the ``_load_*`` walk that consumes
these values.

Input bytes arrive as a single-line TOML basic string (``text``) or as
hexadecimal (``hex``), never as a multi-line string: `tomllib` normalizes
``\r\n`` inside those, so a carriage return needs ``hex``.
"""

import enum
import pathlib
import typing as typ

from job_corpus.ports import EvidenceFormatError

type Where = tuple[pathlib.PurePosixPath, str]


def _fail(where: Where, message: str) -> typ.NoReturn:
    """Report a malformed job file; never returns.

    Parameters
    ----------
    where : Where
        The corpus-relative file and the dotted key the problem is in.
    message : str
        The diagnostic, which this prefixes with the file and the key.

    Raises
    ------
    EvidenceFormatError
        Always, carrying ``where`` so the defect names the file and the key.

    Notes
    -----
    A guard that must end a function returning a value is written as
    ``return _fail(...)``: the call never returns, so the returned expression
    is unreachable.
    """
    path, key = where
    raise EvidenceFormatError(message, path=path, key=key)


def _dotted(where: Where, name: str) -> Where:
    """Return the location of a nested key, for a diagnostic.

    Parameters
    ----------
    where : Where
        The location of the table the key is in.
    name : str
        The key within that table.

    Returns
    -------
    Where
        The same file, with the dotted key extended by ``name``. An empty key
        becomes ``name`` rather than ``.name``.
    """
    path, prefix = where
    return path, f"{prefix}.{name}" if prefix else name


def _table(value: object, where: Where) -> dict[str, object]:
    """Return a TOML table, or report the value as malformed.

    Parameters
    ----------
    value : object
        The decoded TOML value.
    where : Where
        The value's location.

    Returns
    -------
    dict[str, object]
        The value as a table, whose keys `tomllib` has made strings already.
        A value that is not a table, or that holds a key which is not a
        string, is reported through `_fail` rather than returned.
    """
    if not isinstance(value, dict):
        _fail(where, "expected a table")
    if not all(isinstance(key, str) for key in value):
        _fail(where, "expected a table with string keys")
    return typ.cast("dict[str, object]", value)


def _no_unknown_keys(
    value: dict[str, object], allowed: frozenset[str], where: Where
) -> None:
    """Report keys the schema does not define at this position.

    Every unknown key is reported at once, in sorted order, so that one
    document always yields one report rather than one report per run.

    Parameters
    ----------
    value : dict[str, object]
        The table to check.
    allowed : frozenset[str]
        Every key the schema defines here.
    where : Where
        The table's location.
    """
    unknown = sorted(set(value) - allowed)
    if unknown:
        _fail(where, f"unknown key(s): {', '.join(unknown)}")


def _text(value: object, where: Where) -> str:
    """Return a string, or report the value as malformed.

    Parameters
    ----------
    value : object
        The decoded TOML value.
    where : Where
        The value's location.

    Returns
    -------
    str
        The value as a string; anything else is reported through `_fail`.
    """
    if not isinstance(value, str):
        _fail(where, "expected a string")
    return value


def _integer(value: object, where: Where) -> int:
    """Return an integer, rejecting booleans, or report the value as malformed.

    Every integer the schema reads goes through here, so a field cannot be
    stricter or laxer than its neighbours. The check is on the type rather than
    on the value because Python makes ``True == 1`` and ``1.0 == 1``: a boolean
    or a float would otherwise compare equal to the integer a caller expects
    and be accepted as one.

    Parameters
    ----------
    value : object
        The decoded TOML value.
    where : Where
        The value's location.

    Returns
    -------
    int
        The value as an integer. A value that is not one, or that is a boolean
        which Python would otherwise let pass as 0 or 1, is reported through
        `_fail`.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        _fail(where, "expected an integer")
    return value


def _strings(value: object, where: Where) -> tuple[str, ...]:
    """Return an array of strings in document order, or report it as malformed.

    Parameters
    ----------
    value : object
        The decoded TOML value.
    where : Where
        The value's location.

    Returns
    -------
    tuple[str, ...]
        The array's strings, in the order the document gives them. A value
        that is not an array of strings is reported through `_fail`.
    """
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        _fail(where, "expected an array of strings")
    return tuple(typ.cast("list[str]", value))


def _tables(value: object, where: Where) -> list[object]:
    """Return an array, or report the value as malformed.

    Parameters
    ----------
    value : object
        The decoded TOML value.
    where : Where
        The value's location.

    Returns
    -------
    list[object]
        The array's elements, each of which a ``_load_*`` function reads. A
        value that is not an array is reported through `_fail`.
    """
    if not isinstance(value, list):
        _fail(where, "expected an array of tables")
    return typ.cast("list[object]", value)


def _member[MemberT: enum.StrEnum](
    enum_type: type[MemberT], value: object, where: Where
) -> MemberT:
    """Return the enum member a string names, or report an unknown value.

    Parameters
    ----------
    enum_type : type[MemberT]
        The enum the member belongs to.
    value : object
        The decoded TOML value.
    where : Where
        The value's location.

    Returns
    -------
    MemberT
        The member whose value is that string. A value that is not a string,
        or that names no member of ``enum_type``, is reported through `_fail`,
        naming every member the enum does define.
    """
    text = _text(value, where)
    try:
        return enum_type(text)
    except ValueError:
        known = ", ".join(repr(member.value) for member in enum_type)
        _fail(where, f"expected one of {known}; got {text!r}")


def _members[MemberT: enum.StrEnum](
    enum_type: type[MemberT], value: object, where: Where
) -> tuple[MemberT, ...]:
    """Return the enum members an array of strings names, in array order.

    Parameters
    ----------
    enum_type : type[MemberT]
        The enum the members belong to.
    value : object
        The decoded TOML value.
    where : Where
        The value's location.

    Returns
    -------
    tuple[MemberT, ...]
        One member per array element, in the order the document gives them. A
        value that is not an array of strings, or that has an element naming
        no member of ``enum_type``, is reported through `_fail`.
    """
    if not isinstance(value, list):
        _fail(where, "expected an array of strings")
    return tuple(_member(enum_type, item, where) for item in value)


def _required(table: dict[str, object], name: str, where: Where) -> object:
    """Return a required key's value, or report it as missing.

    Parameters
    ----------
    table : dict[str, object]
        The table that must hold the key.
    name : str
        The key's name, without the prefix of its table.
    where : Where
        The table's location.

    Returns
    -------
    object
        The key's decoded value. A table without the key is reported through
        `_fail`, naming the key within its table.
    """
    if name not in table:
        _fail(_dotted(where, name), "expected the key to be present")
    return table[name]


def _all_required(
    table: dict[str, object], names: tuple[str, ...], where: Where
) -> None:
    """Report the first of a set of required keys that is absent.

    Parameters
    ----------
    table : dict[str, object]
        The table that must hold every key.
    names : tuple[str, ...]
        The keys the schema makes mandatory here.
    where : Where
        The table's location.
    """
    for name in names:
        _required(table, name, where)


def _contents(table: dict[str, object], where: Where) -> bytes:
    """Decode an input's bytes from exactly one of ``text`` or ``hex``.

    Parameters
    ----------
    table : dict[str, object]
        The input's table, which holds the encoding.
    where : Where
        The table's location.

    Returns
    -------
    bytes
        The input's exact content. A table holding neither encoding or both,
        a ``hex`` value that is not hexadecimal, or a ``text`` value holding a
        carriage return that a TOML basic string would have normalized away
        are all reported through `_fail`.
    """
    present = [name for name in ("text", "hex") if name in table]
    if len(present) != 1:
        _fail(where, "expected exactly one of 'text' or 'hex'")
    if present[0] == "hex":
        try:
            return bytes.fromhex(_text(table["hex"], _dotted(where, "hex")))
        except ValueError:
            _fail(_dotted(where, "hex"), "expected hexadecimal bytes")
    text = _text(table["text"], _dotted(where, "text"))
    if "\r" in text:
        _fail(_dotted(where, "text"), "carriage returns need the 'hex' encoding")
    return text.encode("utf-8")


def _corpus_path(name: str, where: Where) -> pathlib.PurePosixPath:
    """Resolve a path written relative to its own job directory.

    A job names its scripts the way a reader of that directory would, so the
    job stays readable and moves without rewriting its paths. Domain values
    carry the corpus-relative path instead, so the runner and the report never
    need to know which job a script belongs to. For example, ``reference.py``
    in ``jobs/example/job.toml`` resolves to ``jobs/example/reference.py``.

    Parameters
    ----------
    name : str
        The path as the job wrote it.
    where : Where
        The location of the key that named it, whose file locates the job.

    Returns
    -------
    pathlib.PurePosixPath
        The path relative to the corpus root.
    """
    return where[0].parent / pathlib.PurePosixPath(name)
