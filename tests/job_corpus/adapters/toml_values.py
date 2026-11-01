r"""Scalar coercion for ``job.toml`` documents.

Internal to ``job_corpus.adapters``: `toml_jobs` walks a schema, one helper per
value. Coercion never defaults, so a failure names the corpus-relative file
and dotted key via `_fail`.

Input bytes arrive as a single-line ``text`` string or as ``hex``. A multiline
``text`` is valid unless it holds a physical carriage return, which
`toml_source` rejects before parsing: `tomllib` normalizes ``\r\n`` inside such
a value, so only that case needs ``hex``.
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
    A guard is written ``return _fail(...)``, whose return is unreachable.
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
        The same file, with the key extended by ``name`` (bare if it was empty).
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

    Every unknown key is reported at once, in sorted order, one report per
    document.

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

    The check is on the type: Python makes ``True == 1``, so a boolean would
    pass a value test.

    Parameters
    ----------
    value : object
        The decoded TOML value.
    where : Where
        The value's location.

    Returns
    -------
    int
        The value, which must be an integer and not a boolean.
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
        The array's strings, in the order the document gives them.
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
        The array's elements, each of which a ``_load_*`` function reads.
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
        The member whose value is that string.
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
        One member per array element, in the order the document gives them.
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
        The key's decoded value.
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
        The input's exact content.
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

    A job names its scripts relative to its own directory, so the runner need
    not know the job; ``reference.py`` in ``jobs/example/job.toml`` resolves to
    ``jobs/example/reference.py``. An absolute path or a ``..`` component is
    refused, since either would run a script from outside the job.

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
    path = pathlib.PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        message = f"expected a path in the job directory, not {name}"
        _fail(_dotted(where, "path"), message)
    return where[0].parent / path
