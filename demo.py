#!/usr/bin/env python3
"""
Demo: roda o compressor sobre peticao_inicial.txt e exibe resultados.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from synonyms import Compressor

SAMPLE = Path(__file__).parent / "samples" / "peticao_inicial.txt"
SEPARATOR = "─" * 70


def header(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def main() -> None:
    text = SAMPLE.read_text()

    for safe_only, label in [(True, "SAFE ONLY  (substitutos inequívocos)"),
                              (False, "FULL       (inclui substitutos contextuais)")]:
        c = Compressor(domain="legal-pt", model="gpt-4o", safe_only=safe_only)
        result = c.compress(text)
        s = c.stats(text)

        header(label)

        print(f"\n  Tokens originais  : {s['original_tokens']:>6}")
        print(f"  Tokens comprimidos: {s['compressed_tokens']:>6}")
        print(f"  Economizados      : {s['tokens_saved']:>6}  ({s['savings_pct']}%)")
        print(f"  Substituições     : {s['substitutions']:>6}")

        # custo estimado (gpt-4o input: $2.50 / 1M tokens)
        cost_before = s["original_tokens"] / 1_000_000 * 2.50
        cost_after  = s["compressed_tokens"] / 1_000_000 * 2.50
        saved_usd   = cost_before - cost_after

        print(f"\n  Custo estimado (GPT-4o @ $2.50/1M tokens):")
        print(f"    Antes : ${cost_before:.6f}")
        print(f"    Depois: ${cost_after:.6f}")
        print(f"    Saving: ${saved_usd:.6f} por documento")

        docs_per_day = 10_000
        annual = saved_usd * docs_per_day * 365
        print(f"\n  Projeção ({docs_per_day:,} docs/dia):")
        print(f"    Economia anual: ${annual:,.2f}")

        header("SUBSTITUIÇÕES DETECTADAS")
        counts: dict[str, int] = {}
        for sub in result.substitutions:
            key = f"{sub.original.lower()} → {sub.replacement.lower()}"
            counts[key] = counts.get(key, 0) + 1

        for pair, n in sorted(counts.items(), key=lambda x: -x[1]):
            original_word, replacement_word = pair.split(" → ")
            savings = next(
                s.tokens_saved for s in result.substitutions
                if s.original.lower() == original_word
            )
            print(f"    {pair:<40} ×{n:>2}  (-{savings} tok cada  = -{savings * n} total)")

        print()

    header("TRECHO DO TEXTO COMPRIMIDO (safe-only, primeiras 800 chars)")
    c_safe = Compressor(domain="legal-pt", model="gpt-4o", safe_only=True)
    compressed = c_safe.compress(text).text
    print()
    print(compressed[:800])
    print("  [...]")
    print()


if __name__ == "__main__":
    main()
