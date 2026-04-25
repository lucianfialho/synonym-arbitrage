"""
Lightweight proper-noun guard for legal PT text.

No external NLP deps. Catches the patterns that appear in legal documents:
  - "Comarca de São Paulo"   → "Comarca" is part of a jurisdiction name
  - "COMARCA DE SÃO PAULO"  → same, all-caps header style
  - "Dr. João da Silva"      → not relevant but safe to skip

Rules (applied in order; first match = skip substitution):
  1. Word followed by "de/da/do/dos/das + Capitalized" → proper noun compound
  2. Word is immediately preceded by a proper title abbreviation (Dr., Dra., Sr., etc.)
  3. Word follows a comma + uppercase block (e.g., "..., COMARCA DE SP, ...")
"""

from __future__ import annotations

import re

# preposition + proper noun (initial uppercase or all-caps)
# prep handles da/DA/de/DE/do/DO/das/DAS/dos/DOS
# next word MUST start uppercase (no IGNORECASE on the whole pattern)
_PREP_PROPER = re.compile(
    r"^\s+[Dd][AaEeOo][Ss]?\s+[A-ZÁÉÍÓÚÂÊÔÃÕÀÈÌÒÙÇ]",
)

# title abbreviations that signal a proper name follows
_TITLES = re.compile(r"\b(Dr|Dra|Sr|Sra|Prof|Des|Min)\.\s*$", re.IGNORECASE)


def is_proper_noun_context(text: str, start: int, end: int) -> bool:
    """
    Returns True if the match at [start:end] in `text` is part of a proper noun
    and should NOT be substituted.
    """
    after = text[end:]
    before = text[:start]

    # Rule 1: followed by preposition + proper noun
    # e.g. "comarca de São Paulo" or "COMARCA DE SÃO PAULO"
    if _PREP_PROPER.match(after):
        return True

    # Rule 2: preceded by a title abbreviation
    if _TITLES.search(before):
        return True

    return False
