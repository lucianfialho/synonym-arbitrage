#!/usr/bin/env python3
"""
Benchmark sobre corpus real de acórdãos do TST.
"""

import sys
from pathlib import Path
from statistics import mean, median, stdev

sys.path.insert(0, str(Path(__file__).parent.parent))

from synonyms import Compressor
from synonyms import tokenizer as tok

CORPUS_DIR = Path(__file__).parent.parent / "samples" / "corpus"
MODEL = "gpt-4o"
SEP  = "─" * 90
SEP2 = "━" * 90


def run(text: str, safe_only: bool) -> dict:
    c = Compressor(domain="legal-pt", model=MODEL, safe_only=safe_only)
    result = c.compress(text)
    orig = tok.count(text, MODEL)
    comp = tok.count(result.text, MODEL)
    return {
        "orig":        orig,
        "comp":        comp,
        "saved":       orig - comp,
        "tau":         comp / orig if orig else 1.0,
        "savings_pct": round((orig - comp) / orig * 100, 3) if orig else 0,
        "n_subs":      result.substitution_count,
        "subs_per_1k": round(result.substitution_count / orig * 1000, 2) if orig else 0,
    }


def percentile(data: list[float], p: float) -> float:
    s = sorted(data)
    i = (len(s) - 1) * p / 100
    lo, hi = int(i), min(int(i) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def main() -> None:
    docs = sorted(CORPUS_DIR.glob("*.txt"))
    if not docs:
        print("Corpus vazio. Rode: python scraper.py fetch 100")
        sys.exit(1)

    print(f"\n{SEP2}")
    print(f"  BENCHMARK — Corpus Real TST")
    print(f"  {len(docs)} acórdãos  |  model: {MODEL}  |  domain: legal-pt")
    print(SEP2)

    for label, safe_only in [("SAFE-ONLY", True), ("FULL", False)]:
        rows = []
        for path in docs:
            text = path.read_text(encoding="utf-8")
            rows.append(run(text, safe_only))

        savings = [r["savings_pct"] for r in rows]
        tokens_saved = [r["saved"] for r in rows]
        orig_tokens = [r["orig"] for r in rows]
        subs = [r["n_subs"] for r in rows]

        print(f"\n  Mode: {label}")
        print(SEP)
        print(f"  {'Metric':<30} {'Mean':>10} {'Median':>10} {'Std':>8} {'P10':>8} {'P90':>8}")
        print(SEP)

        metrics = [
            ("Tokens original",    orig_tokens),
            ("Tokens saved",       tokens_saved),
            ("Savings %",          savings),
            ("Substituições/doc",  subs),
            ("Subs/1k tokens",     [r["subs_per_1k"] for r in rows]),
            ("Compression τ",      [r["tau"] for r in rows]),
        ]

        for name, data in metrics:
            m  = mean(data)
            md = median(data)
            sd = stdev(data) if len(data) > 1 else 0
            p10 = percentile(data, 10)
            p90 = percentile(data, 90)
            print(f"  {name:<30} {m:>10.3f} {md:>10.3f} {sd:>8.3f} {p10:>8.3f} {p90:>8.3f}")

        print(SEP)

        # Docs com maior saving
        top = sorted(zip(savings, docs), reverse=True)[:5]
        print(f"\n  Top 5 documentos (savings%):")
        for pct, path in top:
            n = tok.count(path.read_text(encoding="utf-8"), MODEL)
            print(f"    {pct:>6.2f}%  {n:>6} tok  {path.stem[:50]}")

        # ROI
        total_orig = sum(orig_tokens)
        total_saved = sum(tokens_saved)
        price = 2.50 / 1_000_000
        saving_per_doc = mean(tokens_saved) * price

        print(f"\n  ROI (GPT-4o @ $2.50/1M tokens):")
        print(f"    Saving médio/doc : ${saving_per_doc:.6f}")
        for vol, n_day in [("1k/dia", 1_000), ("10k/dia", 10_000), ("100k/dia", 100_000)]:
            print(f"    {vol:<12} ${saving_per_doc * n_day * 365:>10,.2f}/ano")

    # Distribuição de savings
    print(f"\n{SEP}")
    print("  DISTRIBUIÇÃO DE SAVINGS% (full mode, {len(docs)} docs)")
    print(SEP)
    full_savings = [run(p.read_text(encoding="utf-8"), False)["savings_pct"] for p in docs]
    buckets = [(0, 0.5), (0.5, 1), (1, 2), (2, 3), (3, 5), (5, 100)]
    for lo, hi in buckets:
        count = sum(1 for s in full_savings if lo <= s < hi)
        bar = "█" * count
        pct = count / len(full_savings) * 100
        print(f"  [{lo:>4.1f}% – {hi:>4.1f}%)  {count:>4} docs  {pct:>5.1f}%  {bar}")

    print(f"\n{SEP2}\n")


if __name__ == "__main__":
    main()
