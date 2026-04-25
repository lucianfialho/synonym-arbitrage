"""
Gender agreement correction for Portuguese.

When a word changes gender (e.g., comarca f → foro m), determiners that
immediately precede it in the text must also change.
"""

from __future__ import annotations

import re

# Feminine → masculine mapping (and inverse for m→f)
_F_TO_M: dict[str, str] = {
    # definite articles
    "a": "o",
    "as": "os",
    # indefinite articles
    "uma": "um",
    "umas": "uns",
    # preposition + definite article
    "da": "do",
    "das": "dos",
    "na": "no",
    "nas": "nos",
    "pela": "pelo",
    "pelas": "pelos",
    "à": "ao",
    "às": "aos",
    # preposition + definite article (em + a = na, but "em a" is non-standard)
    # demonstratives
    "esta": "este",
    "estas": "estes",
    "essa": "esse",
    "essas": "esses",
    "aquela": "aquele",
    "aquelas": "aqueles",
    "nesta": "neste",
    "nestas": "nestes",
    "nessa": "nesse",
    "nessas": "nesses",
    "naquela": "naquele",
    "naquelas": "naqueles",
    "desta": "deste",
    "destas": "destes",
    "dessa": "desse",
    "dessas": "desses",
    "daquela": "daquele",
    "daquelas": "daqueles",
    "àquela": "àquele",
    "àquelas": "àqueles",
    # indefinite + preposition
    "numa": "num",
    "numas": "nuns",
    "duma": "dum",
    "dumas": "duns",
}

_M_TO_F: dict[str, str] = {v: k for k, v in _F_TO_M.items()}

# Pattern to find a determiner token immediately before the word position
# Matches optional whitespace + the last word-like token before position
_PRECEDING_TOKEN = re.compile(r"(\S+)(\s+)$")


def _get_table(gender_change: str) -> dict[str, str] | None:
    if gender_change == "f→m":
        return _F_TO_M
    if gender_change == "m→f":
        return _M_TO_F
    return None


def correct_preceding_determiner(
    chars: list[str],
    match_start_in_chars: int,
    gender_change: str,
) -> None:
    """
    Mutates `chars` in-place: if the token immediately before match_start
    is a gendered determiner, replace it with its gender-corrected form.
    """
    table = _get_table(gender_change)
    if not table:
        return

    prefix = "".join(chars[:match_start_in_chars])
    m = _PRECEDING_TOKEN.search(prefix)
    if not m:
        return

    token = m.group(1)
    token_lower = token.lower()
    replacement = table.get(token_lower)
    if not replacement:
        return

    # Preserve case of original token
    if token.isupper():
        replacement = replacement.upper()
    elif token.istitle():
        replacement = replacement.capitalize()

    token_start = m.start(1)
    token_end = m.end(1)
    chars[token_start:token_end] = list(replacement)
