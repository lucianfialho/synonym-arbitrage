#!/usr/bin/env python3
"""Semantic preservation test: same Q&A on original vs. compressed text via claude CLI."""

import sys
import re
import json
import subprocess
import random
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from synonyms import Compressor

CORPUS_TST  = ROOT / "samples" / "corpus"
CORPUS_PNCP = ROOT / "samples" / "corpus_pncp"

QUESTIONS_TST = [
    "Qual foi o resultado do julgamento (provido, não provido, não conhecido)?",
    "Quem é o reclamante/requerente neste processo?",
    "Qual o número do processo?",
    "Qual o órgão julgador?",
    "O recurso foi aceito ou rejeitado?",
]

QUESTIONS_PNCP = [
    "Qual é o objeto do contrato em uma frase?",
    "Qual é o valor total do contrato?",
    "Qual é o órgão contratante?",
    "Qual é o prazo de vigência do contrato?",
    "Quais são as principais obrigações do contratado?",
]

SEP = "─" * 80


def ask_claude(prompt: str, context: str) -> str:
    ctx = context[:4000]
    question = f"Contexto:\n\n{ctx}\n\nPergunta: {prompt}\n\nResponda em 1-2 frases, direto ao ponto."
    result = subprocess.run(
        ["claude", "-p", question, "--output-format", "json"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        return f"[erro: {result.stderr[:200]}]"
    try:
        data = json.loads(result.stdout)
        return data.get("result", "").strip()
    except Exception:
        return result.stdout.strip()[:500]


def normalize(text: str) -> str:
    t = re.sub(r"\*+", "", text)
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).lower().strip()


def answers_match(a: str, b: str) -> tuple[bool, str]:
    a_n, b_n = normalize(a), normalize(b)
    words_a = set(w for w in a_n.split() if len(w) > 3)
    words_b = set(w for w in b_n.split() if len(w) > 3)

    if not words_a or not words_b:
        return True, "resposta vazia"

    overlap = words_a & words_b
    score = len(overlap) / max(len(words_a), len(words_b))

    if score >= 0.4:
        return True, f"overlap {score:.0%}"
    else:
        return False, f"overlap {score:.0%} — divergência"


def test_corpus(corpus_dir: Path, questions: list[str], n_docs: int = 5, safe_only: bool = True) -> dict:
    docs = sorted(corpus_dir.glob("*.txt"), key=lambda p: p.stat().st_size, reverse=True)[:n_docs * 2]
    docs = random.sample(docs, min(n_docs, len(docs)))

    c = Compressor(domain="legal-pt", model="gpt-4o", safe_only=safe_only)
    results = []

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        compressed = c.compress(text)
        savings = compressed.tokens_saved

        doc_results = {"doc": doc.name[:40], "savings": savings, "qa": []}
        for q in random.sample(questions, min(2, len(questions))):
            print(f"\n  Doc: {doc.name[:40]}  (savings: {savings} tok)")
            print(f"  Q: {q}")

            ans_orig = ask_claude(q, text)
            ans_comp = ask_claude(q, compressed.text)

            match, reason = answers_match(ans_orig, ans_comp)

            print(f"  Original  : {ans_orig[:100]}")
            print(f"  Comprimido: {ans_comp[:100]}")
            print(f"  {'✓' if match else '✗'}  {reason}")

            doc_results["qa"].append({
                "question": q,
                "original": ans_orig,
                "compressed": ans_comp,
                "match": match,
                "reason": reason,
            })
        results.append(doc_results)

    total_qa = sum(len(r["qa"]) for r in results)
    matches   = sum(1 for r in results for qa in r["qa"] if qa["match"])

    return {"docs_tested": len(results), "qa_total": total_qa, "matches": matches,
            "match_rate": matches / total_qa if total_qa else 0,
            "avg_savings": sum(r["savings"] for r in results) / len(results) if results else 0}


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    n_docs = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print(f"\n{'━'*80}")
    print(f"  TESTE DE PRESERVAÇÃO SEMÂNTICA")
    print(f"  {n_docs} docs por corpus  |  safe-only mode  |  claude CLI")
    print(f"{'━'*80}")

    if mode in ("tst", "both") and CORPUS_TST.exists():
        print(f"\n{SEP}")
        print("  CORPUS TST (acórdãos trabalhistas)")
        print(SEP)
        stats = test_corpus(CORPUS_TST, QUESTIONS_TST, n_docs=n_docs, safe_only=True)
        print(f"\n  Resultado TST: {stats['matches']}/{stats['qa_total']} respostas equivalentes ({stats['match_rate']:.0%})")
        print(f"  Savings médio: {stats['avg_savings']:.0f} tokens/doc")

    if mode in ("pncp", "both") and CORPUS_PNCP.exists():
        print(f"\n{SEP}")
        print("  CORPUS PNCP (editais contratos públicos)")
        print(SEP)
        stats = test_corpus(CORPUS_PNCP, QUESTIONS_PNCP, n_docs=n_docs, safe_only=True)
        print(f"\n  Resultado PNCP: {stats['matches']}/{stats['qa_total']} respostas equivalentes ({stats['match_rate']:.0%})")
        print(f"  Savings médio: {stats['avg_savings']:.0f} tokens/doc")

    print(f"\n{'━'*80}\n")


if __name__ == "__main__":
    main()
