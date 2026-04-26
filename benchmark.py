#!/usr/bin/env python3
"""
Benchmark: synonym-reduction vs. baseline (no compression).

Metrics reported (same framing as LLMLingua/TCRA-LLM papers):
  - tokens_orig    : token count before compression
  - tokens_comp    : token count after compression
  - tokens_saved   : absolute savings
  - compression_ratio τ : compressed / original  (lower = better)
  - savings_pct    : (1 - τ) * 100
  - n_subs         : number of substitutions applied
  - subs_per_1k    : substitutions per 1,000 tokens (density)
  - unique_pairs   : distinct word → replacement pairs used
"""

import sys
from pathlib import Path
from statistics import mean, stdev
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

from synonyms import Compressor
from synonyms import tokenizer as tok

SAMPLES_DIR = Path(__file__).parent / "samples"
MODELS = ["gpt-4o"]  # extend with "gpt-4", "claude" as needed

DOCS = {
    "Petição Inicial":    SAMPLES_DIR / "peticao_inicial.txt",
    "Acórdão":            SAMPLES_DIR / "acordao.txt",
    "Contrato":           SAMPLES_DIR / "contrato.txt",
    "Despacho Judicial":  SAMPLES_DIR / "despacho_judicial.txt",
    "Parecer Jurídico":   SAMPLES_DIR / "parecer.txt",
}

SEP  = "─" * 100
SEP2 = "━" * 100


def run_doc(text: str, model: str, safe_only: bool) -> dict:
    c = Compressor(domain="legal-pt", model=model, safe_only=safe_only)
    result = c.compress(text)
    orig   = tok.count(text, model)
    comp   = tok.count(result.text, model)
    saved  = orig - comp
    pairs  = Counter(
        f"{s.original.lower()}→{s.replacement.lower()}"
        for s in result.substitutions
    )
    return {
        "tokens_orig":      orig,
        "tokens_comp":      comp,
        "tokens_saved":     saved,
        "tau":              comp / orig if orig else 1.0,
        "savings_pct":      round(saved / orig * 100, 2) if orig else 0,
        "n_subs":           result.substitution_count,
        "subs_per_1k":      round(result.substitution_count / orig * 1000, 1) if orig else 0,
        "unique_pairs":     len(pairs),
        "top_pairs":        pairs.most_common(5),
    }


def fmt_row(name: str, r: dict) -> str:
    return (
        f"  {name:<22}"
        f"{r['tokens_orig']:>8}"
        f"{r['tokens_comp']:>9}"
        f"{r['tokens_saved']:>8}"
        f"{r['tau']:>9.4f}"
        f"{r['savings_pct']:>9.2f}%"
        f"{r['n_subs']:>7}"
        f"{r['subs_per_1k']:>9}"
        f"{r['unique_pairs']:>8}"
    )


def fmt_avg(rows: list[dict]) -> str:
    return (
        f"  {'AVERAGE':<22}"
        f"{mean(r['tokens_orig']  for r in rows):>8.0f}"
        f"{mean(r['tokens_comp']  for r in rows):>9.0f}"
        f"{mean(r['tokens_saved'] for r in rows):>8.1f}"
        f"{mean(r['tau']          for r in rows):>9.4f}"
        f"{mean(r['savings_pct']  for r in rows):>9.2f}%"
        f"{mean(r['n_subs']       for r in rows):>7.1f}"
        f"{mean(r['subs_per_1k']  for r in rows):>9.1f}"
        f"{mean(r['unique_pairs'] for r in rows):>8.1f}"
    )


def col_header() -> str:
    return (
        f"  {'Document':<22}"
        f"{'Tok-Orig':>8}"
        f"{'Tok-Comp':>9}"
        f"{'Saved':>8}"
        f"{'τ (ratio)':>9}"
        f"{'Savings%':>10}"
        f"{'#Subs':>7}"
        f"{'Subs/1k':>9}"
        f"{'Pairs':>8}"
    )


def run_benchmark(model: str) -> None:
    print(f"\n{SEP2}")
    print(f"  MODEL: {model}   |   domain: legal-pt   |   date: 2026-04-25")
    print(SEP2)

    for label, safe_only in [("SAFE-ONLY", True), ("FULL", False)]:
        print(f"\n  Mode: {label}")
        print(SEP)
        print(col_header())
        print(SEP)

        rows = []
        for name, path in DOCS.items():
            text = path.read_text()
            r = run_doc(text, model, safe_only)
            rows.append(r)
            print(fmt_row(name, r))

        print(SEP)
        print(fmt_avg(rows))
        print(SEP)

        # std dev of savings_pct across docs
        if len(rows) > 1:
            sd = stdev(r["savings_pct"] for r in rows)
            print(f"\n  Savings std dev: ±{sd:.2f}pp  "
                  f"| min: {min(r['savings_pct'] for r in rows):.2f}%  "
                  f"| max: {max(r['savings_pct'] for r in rows):.2f}%")

    # Top substitution pairs across all docs (full mode)
    print(f"\n{SEP}")
    print("  TOP SUBSTITUTION PAIRS  (across all docs, full mode)")
    print(SEP)
    global_pairs: Counter = Counter()
    for path in DOCS.values():
        text = path.read_text()
        c = Compressor(domain="legal-pt", model=model, safe_only=False)
        result = c.compress(text)
        for s in result.substitutions:
            global_pairs[f"{s.original.lower()} → {s.replacement.lower()} (-{s.tokens_saved}tok)"] += 1

    print(f"\n  {'Pair':<50} {'Occurrences':>12}  {'% of all subs':>14}")
    total = sum(global_pairs.values())
    for pair, n in global_pairs.most_common(15):
        pct = n / total * 100
        bar = "█" * int(pct / 2)
        print(f"  {pair:<50} {n:>12}  {pct:>13.1f}%  {bar}")

    # ROI projection
    print(f"\n{SEP}")
    print("  ROI PROJECTION  (GPT-4o @ $2.50/1M input tokens)")
    print(SEP)
    avg_orig  = mean(tok.count(p.read_text(), model) for p in DOCS.values())
    c_safe    = Compressor(domain="legal-pt", model=model, safe_only=True)
    c_full    = Compressor(domain="legal-pt", model=model, safe_only=False)
    avg_safe  = mean(tok.count(c_safe.compress(p.read_text()).text, model) for p in DOCS.values())
    avg_full  = mean(tok.count(c_full.compress(p.read_text()).text, model) for p in DOCS.values())

    price_per_tok = 2.50 / 1_000_000
    for label, avg_comp in [("safe-only", avg_safe), ("full", avg_full)]:
        saved_per_doc = (avg_orig - avg_comp) * price_per_tok
        print(f"\n  [{label}]")
        for vol_label, n_docs in [("1k docs/day", 1_000), ("10k docs/day", 10_000), ("100k docs/day", 100_000)]:
            annual = saved_per_doc * n_docs * 365
            print(f"    {vol_label:<16}  ${annual:>10,.2f} / year")

    print(f"\n{SEP2}\n")


if __name__ == "__main__":
    for model in MODELS:
        run_benchmark(model)
