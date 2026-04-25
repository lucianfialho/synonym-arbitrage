from __future__ import annotations

import re
from dataclasses import dataclass, field

from .synonym_db import Entry
from .gender import correct_preceding_determiner
from .ner import is_proper_noun_context


@dataclass
class Substitution:
    original: str
    replacement: str
    tokens_saved: int
    position: int


@dataclass
class Result:
    text: str
    original_text: str
    substitutions: list[Substitution] = field(default_factory=list)

    @property
    def tokens_saved(self) -> int:
        return sum(s.tokens_saved for s in self.substitutions)

    @property
    def substitution_count(self) -> int:
        return len(self.substitutions)


def _build_pattern(words: list[str]) -> re.Pattern:
    sorted_words = sorted(words, key=len, reverse=True)
    escaped = [re.escape(w) for w in sorted_words]
    return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)


def process(text: str, entries: dict[str, Entry], model: str = "gpt-4o") -> Result:
    if not entries:
        return Result(text=text, original_text=text)

    pattern = _build_pattern(list(entries.keys()))
    substitutions: list[Substitution] = []
    offset = 0
    result_chars = list(text)

    for match in pattern.finditer(text):
        word_lower = match.group().lower()
        entry = entries.get(word_lower)
        if not entry:
            continue

        savings = entry.savings_for(model)
        if savings <= 0:
            continue

        if is_proper_noun_context(text, match.start(), match.end()):
            continue

        original = match.group()
        replacement = _match_case(original, entry.replacement)

        start = match.start() + offset
        end = match.end() + offset

        if entry.gender_change:
            correct_preceding_determiner(result_chars, start, entry.gender_change)

        result_chars[start:end] = list(replacement)
        offset += len(replacement) - len(original)

        substitutions.append(Substitution(
            original=original,
            replacement=replacement,
            tokens_saved=savings,
            position=match.start(),
        ))

    return Result(
        text="".join(result_chars),
        original_text=text,
        substitutions=substitutions,
    )


def _match_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original.istitle():
        return replacement.capitalize()
    return replacement
