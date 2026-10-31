"""Refuse carriage returns that a multiline TOML string would hide.

`tomllib` normalizes physical CRLF to LF inside multiline strings, so a
carriage return authored there never reaches the decoded value that
`job_corpus.adapters.toml_values` checks. This scan reads the raw text, before
parsing, and holds a ``text`` input to the same ``hex`` requirement.
"""

import typing as typ

from job_corpus.ports import EvidenceFormatError

if typ.TYPE_CHECKING:
    import collections.abc as cabc
    import pathlib

_BARE_KEY = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
_SPACE = " \t\r\n"
_CONTENT_QUOTES = 2
"""How many quotes before a closing delimiter may belong to the content."""
_MESSAGE = "carriage returns need the 'hex' encoding"


def reject_multiline_text_carriage_returns(
    document_text: str, relative: pathlib.PurePosixPath
) -> None:
    r'''Refuse a ``text`` input whose multiline string holds a carriage return.

    Scanning the raw source is the point: parsing is what normalizes the
    carriage return away. ``text`` occurs only under ``cases.inputs``, so the
    diagnostic names that key.

    Raises
    ------
    EvidenceFormatError
        If a multiline string assigned to ``text`` contains a carriage return.

    Examples
    --------
    ``'inputs = [{ text = """a\r\nb""" }]'`` raises, naming
    ``cases.inputs.text``; ``'inputs = [{ text = "a\\r\\nb" }]'`` is a
    single-line string and never reaches this scan.
    '''
    for start, end in _multiline_spans(document_text):
        if "\r" in document_text[start:end] and _names_text(document_text, start):
            raise EvidenceFormatError(_MESSAGE, path=relative, key="cases.inputs.text")


def _multiline_spans(document_text: str) -> cabc.Iterator[tuple[int, int]]:
    """Yield each multiline string's bounds, skipping comments and plain strings.

    Yields
    ------
    tuple[int, int]
        The start and end offsets of one multiline string's raw source.
    """
    index = 0
    while index < len(document_text):
        character = document_text[index]
        if character == "#":
            newline = document_text.find("\n", index)
            index = len(document_text) if newline < 0 else newline + 1
            continue
        if character not in "\"'":
            index += 1
            continue
        end = _literal_end(document_text, index)
        if document_text.startswith(character * 3, index):
            yield index, end
        index = end


def _literal_end(document_text: str, start: int) -> int:
    """Return the index just past the literal opening at ``start``.

    Basic strings honour backslash escapes and literals have none. An
    unterminated literal ends at the document's end, leaving the report to
    `tomllib`.

    Returns
    -------
    int
        The offset just past the literal, or where scanning stopped.
    """
    quote = document_text[start]
    multiline = document_text.startswith(quote * 3, start)
    delimiter = quote * 3 if multiline else quote
    index = start + len(delimiter)
    while index < len(document_text):
        character = document_text[index]
        if character == "\\" and quote == '"':
            index += 2
        elif character == "\n" and not multiline:
            return index
        elif document_text.startswith(delimiter, index):
            return _closing_end(document_text, index) if multiline else index + 1
        index += 1
    return index


def _closing_end(document_text: str, start: int) -> int:
    """Return the index just past a closing delimiter and its content quotes.

    TOML lets one or two quotes before the delimiter belong to the content, so
    a run of four or five quotes closes the string after all of them.

    Returns
    -------
    int
        The offset just past the closing run.
    """
    quote = document_text[start]
    end = start + 3
    for _ in range(_CONTENT_QUOTES):
        if document_text.startswith(quote, end):
            end += 1
    return end


def _names_text(document_text: str, start: int) -> bool:
    """Return whether the literal at ``start`` is assigned to the key ``text``.

    A TOML key may be bare or quoted, and both spellings name the same key, so
    the quoted spelling must be refused too.

    Returns
    -------
    bool
        Whether the key before ``=`` names ``text``.
    """
    before = document_text[:start].rstrip(_SPACE)
    if not before.endswith("="):
        return False
    key = before[:-1].rstrip(_SPACE)
    if key.endswith(('"', "'")):
        key = key[key.rfind(key[-1], 0, len(key) - 1) + 1 : -1]
    else:
        key = key[len(key.rstrip(_BARE_KEY)) :]
    return key == "text"
