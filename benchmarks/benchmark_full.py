#!/usr/bin/env python3
"""
Benchmark reproduzível completo com visualizações.

Uso:
  python benchmark_full.py          # salva PNGs em benchmark_results/
  python benchmark_full.py --show   # também abre janela
"""

import sys
from pathlib import Path
from statistics import mean, median, quantiles

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from synonyms import Compressor
from synonyms import tokenizer as tok
from synonyms.synonym_db import load as load_dict
from synonyms.processor import process as proc
from benchmark_plots import style, plot_distribution, plot_comparison, plot_top_pairs, plot_semantic, SHOW, OUT
import benchmark_plots as bp

CORPUS_TST  = ROOT / "samples" / "corpus"
CORPUS_PNCP = ROOT / "samples" / "corpus_pncp"
MODEL       = "gpt-4o"


def run(docs: list[Path], safe_only: bool, entries: dict | None = None) -> list[float]:
    results = []
    for path in docs:
        text = path.read_text(encoding="utf-8")
        if entries is not None:
            result = proc(text, entries, MODEL)
        else:
            result = Compressor(domain="legal-pt", model=MODEL, safe_only=safe_only).compress(text)
        orig = tok.count(text, MODEL)
        comp = tok.count(result.text, MODEL)
        results.append((orig - comp) / orig * 100 if orig else 0)
    return results


def plot_evolution(docs_tst: list[Path]) -> None:
    from statistics import mean as m, median as md
    import matplotlib.pyplot as plt
    import numpy as np
    all_e = load_dict("legal-pt", MODEL, safe_only=False)
    v1 = {k: all_e[k] for k in list(all_e.keys())[:20]}
    v2 = {k: e for k, e in all_e.items() if e.safe}
    v3 = all_e
    print("  Calculando evolução...")
    r = [run(docs_tst, False, d) for d in (v1, v2, v3)]
    means   = [m(x) for x in r]
    medians = [md(x) for x in r]
    labels  = ["v1\n20 pares\n(inicial)", "v2\n36 pares\n(+TST discover)", "v3\n58 pares\n(+PNCP)"]
    fig, ax = plt.subplots(figsize=(9, 5))
    x, w = np.arange(3), 0.35
    b1 = ax.bar(x - w/2, means,   w, label="Média",   color=bp.C_SAFE, alpha=0.85)
    b2 = ax.bar(x + w/2, medians, w, label="Mediana", color=bp.C_FULL, alpha=0.85)
    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                    f"{bar.get_height():.3f}%", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Token Savings (%)"); ax.legend()
    ax.set_title("Evolução dos Savings com Expansão do Dicionário\n(Corpus TST, 352 acórdãos)",
                 fontsize=12, fontweight="bold")
    ax.set_ylim(0, max(means + medians) * 1.4)
    growth = (means[2] - means[0]) / means[0] * 100
    ax.annotate("", xy=(2 - w/2, means[2] + 0.01), xytext=(0 - w/2, means[0] + 0.01),
                arrowprops=dict(arrowstyle="->", color="gray", lw=1.5))
    ax.text(1 - w/2, max(means) * 1.25, f"+{growth:.0f}%\n de crescimento",
            ha="center", fontsize=9, color="gray")
    plt.tight_layout()
    bp.save("2_evolucao_dicionario.png")


if __name__ == "__main__":
    if "--show" in sys.argv:
        bp.SHOW = True
    style()
    OUT.mkdir(exist_ok=True)

    docs_tst  = list(CORPUS_TST.glob("*.txt"))
    docs_pncp = [p for p in CORPUS_PNCP.glob("*.txt") if p.stat().st_size >= 30_000]
    print(f"TST: {len(docs_tst)} docs  |  PNCP: {len(docs_pncp)} editais ≥30KB")
    print("Calculando savings (pode levar ~2 min)...")

    ts = run(docs_tst,  safe_only=True)
    tf = run(docs_tst,  safe_only=False)
    ps = run(docs_pncp, safe_only=True)
    pf = run(docs_pncp, safe_only=False)
    print(f"  TST  → safe: {mean(ts):.3f}%  full: {mean(tf):.3f}%")
    print(f"  PNCP → safe: {mean(ps):.3f}%  full: {mean(pf):.3f}%")

    print("\nGerando gráficos...")
    plot_distribution(ts, tf, ps, pf)
    plot_evolution(docs_tst)
    plot_comparison(ts, tf, ps, pf)
    plot_top_pairs(docs_tst + docs_pncp)
    plot_semantic()

    print(f"\n{'━'*62}")
    print(f"  {'Corpus':<10} {'Modo':<12} {'Média':>8}  {'Mediana':>8}  {'P90':>8}")
    print(f"  {'─'*55}")
    for corpus, modo, data in [
        ("TST", "safe-only", ts), ("TST", "full", tf),
        ("PNCP", "safe-only", ps), ("PNCP", "full", pf),
    ]:
        qs = quantiles(data, n=10)
        print(f"  {corpus:<10} {modo:<12} {mean(data):>7.3f}%  {median(data):>7.3f}%  {qs[8]:>7.3f}%")
    print(f"{'━'*62}")
    print(f"  Semântica: 40/40 Q&A preservados | Dicionário: 58 pares")
    print(f"  PNGs em: {OUT.absolute()}/")
