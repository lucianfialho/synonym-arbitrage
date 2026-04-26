#!/usr/bin/env python3
"""Quick benchmark on synthetic sample documents (5 files)."""

import sys
from pathlib import Path
from statistics import mean, stdev
from collections import Counter

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from synonyms import Compressor
from synonyms import tokenizer as tok

SAMPLES = ROOT / "samples"
MODELS  = ["gpt-4o"]
DOCS = {
    "Petição Inicial":   SAMPLES / "peticao_inicial.txt",
    "Acórdão":           SAMPLES / "acordao.txt",
    "Contrato":          SAMPLES / "contrato.txt",
    "Despacho Judicial": SAMPLES / "despacho_judicial.txt",
    "Parecer Jurídico":  SAMPLES / "parecer.txt",
}
S = "─" * 96
S2 = "━" * 96


def run_doc(text: str, model: str, safe_only: bool) -> dict:
    c      = Compressor(domain="legal-pt", model=model, safe_only=safe_only)
    result = c.compress(text)
    orig   = tok.count(text, model)
    comp   = tok.count(result.text, model)
    saved  = orig - comp
    pairs  = Counter(f"{s.original.lower()}→{s.replacement.lower()}" for s in result.substitutions)
    return {"orig": orig, "comp": comp, "saved": saved,
            "tau": comp/orig if orig else 1.0,
            "pct": round(saved/orig*100, 2) if orig else 0,
            "n": result.substitution_count,
            "per1k": round(result.substitution_count/orig*1000, 1) if orig else 0,
            "pairs": len(pairs), "top": pairs.most_common(5)}


def row(name: str, r: dict) -> str:
    return (f"  {name:<22}{r['orig']:>8}{r['comp']:>9}{r['saved']:>8}"
            f"{r['tau']:>9.4f}{r['pct']:>9.2f}%{r['n']:>7}{r['per1k']:>9}{r['pairs']:>8}")


def avg_row(rows: list[dict]) -> str:
    return (f"  {'AVERAGE':<22}{mean(r['orig'] for r in rows):>8.0f}"
            f"{mean(r['comp'] for r in rows):>9.0f}{mean(r['saved'] for r in rows):>8.1f}"
            f"{mean(r['tau'] for r in rows):>9.4f}{mean(r['pct'] for r in rows):>9.2f}%"
            f"{mean(r['n'] for r in rows):>7.1f}{mean(r['per1k'] for r in rows):>9.1f}"
            f"{mean(r['pairs'] for r in rows):>8.1f}")


def header() -> str:
    return (f"  {'Document':<22}{'Tok-Orig':>8}{'Tok-Comp':>9}{'Saved':>8}"
            f"{'τ':>9}{'Savings%':>10}{'#Subs':>7}{'Subs/1k':>9}{'Pairs':>8}")


def run(model: str) -> None:
    print(f"\n{S2}\n  MODEL: {model}  |  domain: legal-pt\n{S2}")
    for label, safe_only in [("SAFE-ONLY", True), ("FULL", False)]:
        print(f"\n  Mode: {label}\n{S}\n{header()}\n{S}")
        rows = [run_doc(p.read_text(), model, safe_only) for p in DOCS.values()]
        for name, r in zip(DOCS, rows):
            print(row(name, r))
        print(S)
        print(avg_row(rows))
        print(S)
        if len(rows) > 1:
            sd = stdev(r["pct"] for r in rows)
            print(f"\n  std: ±{sd:.2f}pp | min: {min(r['pct'] for r in rows):.2f}% | max: {max(r['pct'] for r in rows):.2f}%")

    print(f"\n{S}\n  TOP PAIRS (full mode)\n{S}")
    pairs: Counter = Counter()
    for path in DOCS.values():
        c = Compressor(domain="legal-pt", model=model, safe_only=False)
        for s in c.compress(path.read_text()).substitutions:
            pairs[f"{s.original.lower()} → {s.replacement.lower()} (-{s.tokens_saved}tok)"] += 1
    total = sum(pairs.values())
    for pair, n in pairs.most_common(12):
        print(f"  {pair:<48} {n:>6}  {n/total*100:>5.1f}%  {'█'*int(n/total*50)}")

    print(f"\n{S}\n  ROI (GPT-4o @ $2.50/1M tokens)\n{S}")
    orig_avg = mean(tok.count(p.read_text(), model) for p in DOCS.values())
    for label, safe_only in [("safe-only", True), ("full", False)]:
        c    = Compressor(domain="legal-pt", model=model, safe_only=safe_only)
        comp = mean(tok.count(c.compress(p.read_text()).text, model) for p in DOCS.values())
        usd  = (orig_avg - comp) / 1_000_000 * 2.50
        print(f"\n  [{label}]")
        for vol, n in [("1k/day", 1_000), ("10k/day", 10_000), ("100k/day", 100_000)]:
            print(f"    {vol:<12}  ${usd*n*365:>10,.2f}/year")
    print(f"\n{S2}\n")


if __name__ == "__main__":
    for m in MODELS:
        run(m)
