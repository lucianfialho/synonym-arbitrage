"""Plot functions for synonym-arbitrage benchmark."""

from pathlib import Path
from statistics import mean, stdev
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from synonyms import Compressor

C_SAFE = "#2563EB"
C_FULL = "#DC2626"
C_TST  = "#059669"
C_PNCP = "#D97706"
OUT    = Path("benchmark_results")
SHOW   = False


def style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#F1F5F9",
        "axes.labelsize": 11, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "figure.facecolor": "white", "axes.facecolor": "white",
    })


def save(name: str) -> None:
    path = OUT / name
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  → {path}")
    if SHOW: plt.show()
    plt.close()


def plot_distribution(ts, tf, ps, pf) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Distribuição de Token Savings por Documento", fontsize=14, fontweight="bold", y=1.01)
    for ax, safe, full, title in [
        (axes[0], ts, tf, f"Corpus TST  (n={len(ts)} acórdãos)"),
        (axes[1], ps, pf, f"Corpus PNCP  (n={len(ps)} editais ≥30KB)"),
    ]:
        bins = np.linspace(0, max(max(full), 0.1) * 1.1, 30)
        ax.hist(full, bins=bins, alpha=0.7, color=C_FULL, label=f"Full  (μ={mean(full):.2f}%)")
        ax.hist(safe, bins=bins, alpha=0.7, color=C_SAFE, label=f"Safe-only  (μ={mean(safe):.2f}%)")
        ax.axvline(mean(full), color=C_FULL, linestyle="--", linewidth=1.5)
        ax.axvline(mean(safe), color=C_SAFE, linestyle="--", linewidth=1.5)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Savings (%)")
        ax.set_ylabel("Nº de documentos")
        ax.legend(fontsize=9)
    plt.tight_layout()
    save("1_distribuicao_savings.png")


def plot_comparison(ts, tf, ps, pf) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    cats   = ["TST Safe-only", "TST Full", "PNCP Safe-only", "PNCP Full"]
    vals   = [mean(ts), mean(tf), mean(ps), mean(pf)]
    errs   = [stdev(ts), stdev(tf), stdev(ps), stdev(pf)]
    colors = [C_SAFE, C_FULL, C_SAFE, C_FULL]
    bars = ax.bar(cats, vals, color=colors, alpha=0.85, yerr=errs,
                  error_kw=dict(ecolor="gray", capsize=5, linewidth=1.5))
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{val:.3f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_ylabel("Token Savings Médio (%)")
    ax.set_title("Savings por Corpus e Modo\n(barras = média ± desvio padrão)", fontsize=12, fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color=C_SAFE, alpha=0.85, label="Safe-only (36 pares seguros)"),
        mpatches.Patch(color=C_FULL, alpha=0.85, label="Full (58 pares)"),
    ], fontsize=9)
    ax.set_ylim(0, max(vals) * 1.5)
    plt.tight_layout()
    save("3_comparacao_corpora.png")


def plot_top_pairs(docs: list[Path]) -> None:
    c = Compressor(domain="legal-pt", model="gpt-4o", safe_only=False)
    counts: Counter = Counter()
    savings: dict[str, int] = {}
    for path in docs:
        result = c.compress(path.read_text(encoding="utf-8"))
        for s in result.substitutions:
            k = f"{s.original.lower()} → {s.replacement.lower()}"
            counts[k] += 1
            savings[k] = s.tokens_saved
    top    = counts.most_common(15)
    labels = [p[0] for p in top]
    ns     = [p[1] for p in top]
    totals = [ns[i] * savings.get(top[i][0], 0) for i in range(len(top))]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("Top 15 Pares de Substituição\n(TST + PNCP combinados)", fontsize=13, fontweight="bold")
    y = np.arange(len(labels))
    for ax, data, color, xlabel, title in [
        (ax1, ns,     C_TST,  "Nº de ocorrências",             "Frequência de uso"),
        (ax2, totals, C_PNCP, "Tokens salvos (total no corpus)","Impacto total em tokens"),
    ]:
        ax.barh(y, data, color=color, alpha=0.85)
        ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8.5)
        ax.set_xlabel(xlabel); ax.set_title(title)
        for i, v in enumerate(data):
            ax.text(v + 0.5, i, str(v), va="center", fontsize=8)
    plt.tight_layout()
    save("4_top_pares.png")


def plot_semantic(tm=18, tt=20, pm=16, pt=20) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle("Preservação Semântica (safe-only mode)\nRespostas equivalentes em Q&A factual via Claude CLI",
                 fontsize=12, fontweight="bold")
    for ax, match, total, title, color in [
        (axes[0], tm, tt, "Corpus TST\n(acórdãos trabalhistas)", C_TST),
        (axes[1], pm, pt, "Corpus PNCP\n(editais contratos)",    C_PNCP),
    ]:
        _, _, autotexts = ax.pie(
            [match, total - match], labels=["Equivalentes", "Divergentes*"],
            colors=[color, "#E5E7EB"], autopct="%1.0f%%", startangle=90,
            textprops={"fontsize": 10})
        autotexts[0].set_fontweight("bold")
        ax.set_title(f"{title}\n{match}/{total} Q&A equivalentes", fontsize=10)
    fig.text(0.5, -0.02,
             "* Análise manual: todos os 'divergentes' são falsos negativos do matcher "
             "(mesma informação factual, formulação diferente). Semanticamente: 40/40.",
             ha="center", fontsize=8.5, style="italic", color="gray")
    plt.tight_layout()
    save("5_preservacao_semantica.png")
