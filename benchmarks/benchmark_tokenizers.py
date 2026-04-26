#!/usr/bin/env python3
"""
Compara savings entre o200k_base (GPT-4o) e cl100k_base (GPT-4/Claude)
no corpus real de acórdãos TST.
"""

import sys
from pathlib import Path
from statistics import mean, median, stdev

sys.path.insert(0, str(Path(__file__).parent.parent))

from synonyms import Compressor
from synonyms import tokenizer as tok

CORPUS_DIR = Path(__file__).parent.parent / "samples" / "corpus"
SEP  = "─" * 88
SEP2 = "━" * 88

MODELS = [
    ("gpt-4o",       "o200k_base", "GPT-4o / GPT-5.x"),
    ("gpt-4",        "cl100k_base", "GPT-4 / Claude (aprox.)"),
]


def run(text: str, model: str, safe_only: bool) -> dict:
    c = Compressor(domain="legal-pt", model=model, safe_only=safe_only)
    result = c.compress(text)
    orig = tok.count(text, model)
    comp = tok.count(result.text, model)
    return {
        "orig":        orig,
        "saved":       orig - comp,
        "savings_pct": round((orig - comp) / orig * 100, 3) if orig else 0,
        "n_subs":      result.substitution_count,
    }


def run_model(docs: list[Path], model: str, safe_only: bool) -> list[dict]:
    return [run(p.read_text(encoding="utf-8"), model, safe_only) for p in docs]


def show(rows: list[dict], label: str) -> None:
    savings = [r["savings_pct"] for r in rows]
    saved   = [r["saved"] for r in rows]
    subs    = [r["n_subs"] for r in rows]

    print(f"\n  {label}")
    print(f"  {'Metric':<28} {'Mean':>8} {'Median':>8} {'Std':>7} {'P10':>7} {'P90':>7}")
    print(f"  {'─'*65}")

    for name, data in [
        ("Savings %",         savings),
        ("Tokens saved/doc",  saved),
        ("Substituições/doc", subs),
    ]:
        m, md, sd = mean(data), median(data), stdev(data) if len(data) > 1 else 0
        from statistics import quantiles
        qs = quantiles(data, n=10)
        p10, p90 = qs[0], qs[8]
        print(f"  {name:<28} {m:>8.3f} {md:>8.3f} {sd:>7.3f} {p10:>7.3f} {p90:>7.3f}")

    # ROI
    price = {"gpt-4o": 2.50, "gpt-4": 10.00}
    for model_id, price_per_m in price.items():
        if model_id in label.lower() or ("gpt-4" in label and "4o" not in label and model_id == "gpt-4"):
            saving_usd = mean(saved) / 1_000_000 * price_per_m
            print(f"\n  ROI ({model_id} @ ${price_per_m}/1M tokens):")
            for vol, n in [("1k/dia", 1_000), ("10k/dia", 10_000), ("100k/dia", 100_000)]:
                print(f"    {vol:<12} ${saving_usd * n * 365:>9,.2f}/ano")


def main() -> None:
    docs = sorted(CORPUS_DIR.glob("*.txt"))
    if not docs:
        print("Corpus vazio. Rode: python scraper.py fetch 1000")
        sys.exit(1)

    print(f"\n{SEP2}")
    print(f"  COMPARAÇÃO DE TOKENIZADORES — Corpus Real TST")
    print(f"  {len(docs)} acórdãos  |  domain: legal-pt")
    print(SEP2)

    for safe_only, mode_label in [(True, "SAFE-ONLY"), (False, "FULL")]:
        print(f"\n{'─'*88}")
        print(f"  MODO: {mode_label}")
        print(f"{'─'*88}")

        results = {}
        for model_id, enc_name, display in MODELS:
            rows = run_model(docs, model_id, safe_only)
            results[display] = rows
            show(rows, f"{display} [{enc_name}]")

        # Tabela comparativa direta
        print(f"\n  {'Comparativo':^40}")
        print(f"  {'Métrica':<28} {'GPT-4o':>12} {'GPT-4/Claude':>14} {'Δ':>8}")
        print(f"  {'─'*64}")
        r4o  = results["GPT-4o / GPT-5.x"]
        r4   = results["GPT-4 / Claude (aprox.)"]
        for name, key in [("Savings % médio", "savings_pct"), ("Tokens salvos/doc", "saved")]:
            v4o = mean(r["savings_pct" if "%" in name else "saved"] for r in r4o)
            v4  = mean(r["savings_pct" if "%" in name else "saved"] for r in r4)
            delta = v4 - v4o
            print(f"  {name:<28} {v4o:>12.3f} {v4:>14.3f} {delta:>+8.3f}")

    # Por-palavra: qual tokenizador beneficia mais cada par
    print(f"\n{SEP}")
    print("  SAVINGS POR PAR (in-context, com espaço)")
    print(SEP)
    import tiktoken as tik
    encs = {
        "o200k": tik.get_encoding("o200k_base"),
        "cl100k": tik.get_encoding("cl100k_base"),
    }
    import json
    data = json.loads((Path(__file__).parent.parent / "data" / "legal_pt.json").read_text())

    print(f"  {'palavra':<22} {'substituto':<16} {'o200k (GPT-4o)':>16} {'cl100k (GPT-4)':>16} {'melhor':>8}")
    print(f"  {'─'*82}")
    for word, entry in sorted(data.items()):
        rep = entry["replacement"]
        s = {}
        for name, enc in encs.items():
            o = len(enc.encode(" " + word))
            r = len(enc.encode(" " + rep))
            s[name] = o - r
        winner = "ambos=0" if s["o200k"] == 0 == s["cl100k"] else \
                 "cl100k" if s["cl100k"] > s["o200k"] else \
                 "o200k"  if s["o200k"]  > s["cl100k"] else "igual"
        if s["o200k"] == 0 and s["cl100k"] == 0:
            continue  # skip zero-zero
        print(f"  {word:<22} {rep:<16} "
              f"{s['o200k']:>+5} tok            "
              f"{s['cl100k']:>+5} tok            "
              f"{winner:>8}")

    print(f"\n{SEP2}\n")


if __name__ == "__main__":
    main()
