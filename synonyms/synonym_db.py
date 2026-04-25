from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import tokenizer as tok

DATA_DIR = Path(__file__).parent.parent / "data"

DOMAINS = {
    "legal-pt": DATA_DIR / "legal_pt.json",
}


@dataclass
class Entry:
    word: str
    replacement: str
    safe: bool
    gender_change: str | None
    notes: str
    savings: dict[str, int] = field(default_factory=dict)

    def savings_for(self, model: str) -> int:
        if model not in self.savings:
            self.savings[model] = tok.token_savings(self.word, self.replacement, model)
        return self.savings[model]


def load(domain: str, model: str = "gpt-4o", safe_only: bool = False) -> dict[str, Entry]:
    path = DOMAINS.get(domain)
    if not path or not path.exists():
        raise ValueError(f"Unknown domain '{domain}'. Available: {list(DOMAINS)}")

    raw = json.loads(path.read_text())
    entries: dict[str, Entry] = {}

    for word, data in raw.items():
        entry = Entry(
            word=word,
            replacement=data["replacement"],
            safe=data.get("safe", False),
            gender_change=data.get("gender_change"),
            notes=data.get("notes", ""),
        )
        if safe_only and not entry.safe:
            continue
        if entry.savings_for(model) <= 0:
            continue
        entries[word] = entry

    return entries
