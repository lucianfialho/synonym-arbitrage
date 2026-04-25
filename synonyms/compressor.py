from __future__ import annotations

from . import synonym_db, tokenizer as tok
from .processor import Result, process


class Compressor:
    def __init__(self, domain: str = "legal-pt", model: str = "gpt-4o", safe_only: bool = False):
        self.domain = domain
        self.model = model
        self.entries = synonym_db.load(domain, model, safe_only=safe_only)

    def compress(self, text: str) -> Result:
        return process(text, self.entries, self.model)

    def analyze(self, text: str) -> Result:
        return self.compress(text)

    def stats(self, text: str) -> dict:
        result = self.compress(text)
        original_tokens = tok.count(text, self.model)
        compressed_tokens = tok.count(result.text, self.model)
        return {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "tokens_saved": original_tokens - compressed_tokens,
            "savings_pct": round((original_tokens - compressed_tokens) / original_tokens * 100, 2) if original_tokens else 0,
            "substitutions": result.substitution_count,
        }
