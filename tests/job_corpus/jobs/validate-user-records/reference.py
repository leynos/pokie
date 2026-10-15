#!/usr/bin/env python3
"""Reference oracle for the validate-user-records job.

This script deliberately models the *proposed* pokie semantics of
`docs/design-contracts.md` §1 rather than idiomatic shell-script style. In
particular it shows the property that a native Python `match` statement gets
wrong for pokie, which is why the lowering in roadmap task 2.1.2 must
implement it explicitly: bindings are transactional, so a case whose guard
rejects publishes nothing and a rejected candidate binding never overwrites a
committed one.

Roadmap task 5.2.2 compares pokie against users' own scripts; this file is not
part of that comparison, so its shape and length are not evidence about
pokie's ergonomics. Read it as a specification that happens to be executable.

Usage: ``reference.py [FILE ...]``; no operands reads standard input. Input is
decoded per record with strict UTF-8, so an invalid byte fails after the
records before it have already been printed.
"""

import collections
import collections.abc as cabc
import pathlib
import re
import sys

_USER_RECORD = re.compile(r"user=(\w+) uid=(\S+)")


def accepted_uid(text: str) -> int | None:
    """Return the integer a pokie ``int`` adapter would produce, or ``None``.

    The proposed `int` adapter accepts exactly what ``int(subject, 10)``
    accepts, so this function defers to CPython rather than reimplementing
    Python's numeric grammar. ``None`` means the adapter found no match.

    Parameters
    ----------
    text : str
        The captured subject.

    Returns
    -------
    int | None
        The converted integer, or ``None`` when the adapter rejects.

    Examples
    --------
    >>> accepted_uid("42")
    42
    >>> accepted_uid("-1")
    -1
    >>> accepted_uid("no") is None
    True
    """
    try:
        return int(text, 10)
    # The parentheses are load-bearing and `ruff format` removes them under
    # `target-version = "py314"`, which rewrites this as the PEP 758 form
    # `except ValueError, TypeError:`. Pylint, which the Makefile pins to PyPy
    # 3.12, cannot parse that form and fails the lint gate with E0001. Both
    # tools run over this file, so the parentheses are pinned here rather than
    # in either tool's configuration.
    except (ValueError, TypeError):  # fmt: skip
        return None


def iterate_records(stream: cabc.Iterable[bytes]) -> cabc.Iterator[str]:
    """Yield decoded records from a binary stream, one record at a time.

    Decoding happens per record so that record order stays observable: an
    invalid byte fails after the records before it have been delivered.

    Parameters
    ----------
    stream : collections.abc.Iterable[bytes]
        A binary, line-buffered stream such as ``sys.stdin.buffer``.

    Yields
    ------
    str
        One record with its line terminator removed.
    """
    for raw in stream:
        yield raw.decode("utf-8").rstrip("\r\n")


def collect_counts(
    records: cabc.Iterable[str],
) -> tuple[dict[int, str], collections.Counter[str]]:
    """Apply the program's rules to every record, in order.

    Parameters
    ----------
    records : collections.abc.Iterable[str]
        The decoded records, in input order.

    Returns
    -------
    tuple[dict[int, str], collections.Counter[str]]
        The accepted identifiers mapped to names, and the rejected spellings
        with their counts.

    Examples
    --------
    >>> users, rejected = collect_counts(["user=ada uid=42", "user=lin uid=no"])
    >>> print(len(users), sum(rejected.values()))
    1 1
    """
    users: dict[int, str] = {}
    rejected: collections.Counter[str] = collections.Counter()
    for record in records:
        match = _USER_RECORD.search(record)
        if match is None:
            continue
        name, raw_uid = match.groups()
        uid = accepted_uid(raw_uid)
        # The case guard is `uid >= 0`; a rejected conversion falls through to
        # the next case, and only an accepted case commits its bindings.
        if uid is not None and uid >= 0:
            users[uid] = name
        else:
            rejected[raw_uid] += 1
    return users, rejected


def read_operands(
    operands: cabc.Sequence[str],
) -> tuple[dict[int, str], collections.Counter[str]]:
    """Run the program over the operands, defaulting to standard input.

    Files are read sequentially into one aggregate, as the one-reader contract
    in `docs/pokie-design.md` §4.1 requires.

    Parameters
    ----------
    operands : collections.abc.Sequence[str]
        File names to read; empty, or ``["-"]``, means standard input.

    Returns
    -------
    tuple[dict[int, str], collections.Counter[str]]
        The combined accepted identifiers and rejected spellings.

    Examples
    --------
    >>> users, rejected = read_operands(["-"])
    >>> print(len(users), sum(rejected.values()))  # doctest: +SKIP
    0 0
    """
    if not operands or list(operands) == ["-"]:
        return collect_counts(iterate_records(sys.stdin.buffer))
    users: dict[int, str] = {}
    rejected: collections.Counter[str] = collections.Counter()
    for operand in operands:
        with pathlib.Path(operand).open("rb") as handle:
            partial_users, partial_rejected = collect_counts(iterate_records(handle))
        users.update(partial_users)
        rejected.update(partial_rejected)
    return users, rejected


def main(operands: list[str]) -> None:
    """Print the accepted-user count and the rejected-record total.

    Parameters
    ----------
    operands : list[str]
        File names to read; empty, or ``["-"]``, means standard input.
    """
    users, rejected = read_operands(operands)
    print(len(users), sum(rejected.values()))


if __name__ == "__main__":
    main(sys.argv[1:])
