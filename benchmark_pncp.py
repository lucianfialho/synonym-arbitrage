#!/usr/bin/env python3
"""Benchmark no corpus PNCP (editais de contratos públicos)."""

import sys
from pathlib import Path
from statistics import mean, median, stdev

sys.path.insert(0, str(Path(__file__).parent))

from synonyms import Compressor
from synonyms import tokenizer as tok

CORPUS_DIR = Path(__file__).parent / "samples" / "corpus_pncp"
MODEL = "gpt-4o"
MIN_SIZE = 30_000  # só editais maiores
SEP = "─" * 88
SEP2 = "━" * 88


def run(text: str, safe_only: bool) -> dict:
    c = Compressor(domain="legal-pt", model=MODEL, safe_only=safe_only)
    result = c.compress(text)
    orig = tok.count(text, MODEL)
    comp = tok.count(result.text, MODEL)
    return {
        "orig": orig,
        "saved": orig - comp,
        "savings_pct": round((orig - comp) / orig * 100, 3) if orig else 0,
        "n_subs": result.substitution_count,
    }


def main() -> None:
    docs = [p for p in CORPUS_DIR.glob("*.txt") if p.stat().st_size >= MIN_SIZE]
    if not docs:
        print("Corpus PNCP vazio ou sem editais grandes.")
        sys.exit(1)

    print(f"\n{SEP2}")
    print(f"  BENCHMARK — Corpus PNCP (editais contratos públicos)")
    print(f"  {len(docs)} editais ≥{MIN_SIZE//1000}KB  |  model: {MODEL}  |  domain: legal-pt")
    print(SEP2)

    for label, safe_only in [("SAFE-ONLY", True), ("FULL", False)]:
        rows = [run(p.read_text(encoding="utf-8"), safe_only) for p in docs]
        savings = [r["savings_pct"] for r in rows]
        saved   = [r["saved"] for r in rows]
        subs    = [r["n_subs"] for r in rows]

        print(f"\n  Mode: {label}")
        print(SEP)
        print(f"  {'Metric':<28} {'Mean':>8} {'Median':>8} {'Std':>7} {'P10':>7} {'P90':>7}")
        print(f"  {'─'*60}")

        from statistics import quantiles
        for name, data in [("Savings %", savings), ("Tokens saved/doc", saved), ("Subs/doc", subs)]:
            m, md = mean(data), median(data)
            sd = stdev(data) if len(data) > 1 else 0
            qs = quantiles(data, n=10)
            print(f"  {name:<28} {m:>8.3f} {md:>8.3f} {sd:>7.3f} {qs[0]:>7.3f} {qs[8]:>7.3f}")

        # ROI
        saving_usd = mean(saved) / 1_000_000 * 2.50
        print(f"\n  ROI (GPT-4o @ $2.50/1M tokens):")
        for vol, n in [("1k/dia", 1_000), ("10k/dia", 10_000), ("100k/dia", 100_000)]:
            print(f"    {vol:<12} ${saving_usd * n * 365:>9,.2f}/ano")

        # top docs
        top = sorted(zip(savings, docs), reverse=True)[:3]
        print(f"\n  Top 3 editais:")
        for pct, path in top:
            obj = path.read_text(encoding="utf-8").split('\n')[4].replace('OBJETO: ','')[:55]
            print(f"    {pct:>5.2f}%  {obj}")

    print(f"\n{SEP2}\n")


if __name__ == "__main__":
    main()
