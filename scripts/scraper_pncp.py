#!/usr/bin/env python3
"""Scraper: PNCP editais de contratos públicos → corpus. API pública, sem auth."""

import sys
import time
import re
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from pncp_fetch import fetch_contracts, fetch_edital, extract_pdf, parse_compra_ref, is_good, PAGE_SIZE

CORPUS_DIR = Path(__file__).parent.parent / "samples" / "corpus_pncp"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)
RATE_LIMIT = 0.5


def scrape(target: int = 200, days_back: int = 120, verbose: bool = True) -> int:
    existing = {p.stem for p in CORPUS_DIR.glob("*.txt")}
    saved    = 0
    today    = date.today()

    for day_offset in range(days_back):
        if saved >= target:
            break
        d        = today - timedelta(days=day_offset + 1)
        date_str = d.strftime("%Y%m%d")
        if verbose:
            print(f"\n  [{saved:>3}/{target}] data: {d.isoformat()}")

        page = 1
        while saved < target:
            items, total = fetch_contracts(date_str, page)
            time.sleep(RATE_LIMIT)
            if not items:
                break

            for item in items:
                if saved >= target:
                    break
                if not is_good(item):
                    continue

                ctrl   = item.get("numeroControlePNCP", "")
                doc_id = re.sub(r"[^a-z0-9]", "_", ctrl.lower())[:40]
                ref    = parse_compra_ref(item)
                if not ref or doc_id in existing:
                    continue

                pdf = fetch_edital(*ref)
                time.sleep(RATE_LIMIT)
                if not pdf:
                    continue

                text = extract_pdf(pdf)
                if not text:
                    continue

                orgao  = item.get("orgaoEntidade", {}).get("razaoSocial", "")
                cat    = item.get("categoriaProcesso", {})
                cat_nm = cat.get("nome", "") if isinstance(cat, dict) else ""
                objeto = item.get("objetoContrato", "")[:200]
                valor  = item.get("valorGlobal") or item.get("valorInicial") or 0
                uf     = item.get("unidadeOrgao", {}).get("ufSigla", "")

                header = (f"PORTAL NACIONAL DE CONTRATAÇÕES PÚBLICAS — PNCP\n"
                          f"ÓRGÃO: {orgao}\nUF: {uf}\nCATEGORIA: {cat_nm}\n"
                          f"OBJETO: {objeto}\nVALOR: R$ {valor:,.2f}\n"
                          f"CONTRATO: {ctrl}\n{'─'*60}\n\n")

                (CORPUS_DIR / f"{doc_id}.txt").write_text(header + text, encoding="utf-8")
                existing.add(doc_id)
                saved += 1
                if verbose:
                    print(f"    [{saved:>3}] {objeto[:50]:<50} {len(text):>7} chars")

            if page * PAGE_SIZE >= min(total, 200):
                break
            page += 1

    return saved


def stats() -> None:
    docs = list(CORPUS_DIR.glob("*.txt"))
    if not docs:
        print("Corpus PNCP vazio.")
        return
    from statistics import mean, median
    sizes = [len(p.read_text()) for p in docs]
    print(f"\nCorpus PNCP: {len(docs)} editais | "
          f"avg {mean(sizes):.0f} | median {median(sizes):.0f} | "
          f"min {min(sizes)} | max {max(sizes)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    n   = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    if cmd == "fetch":
        print(f"Buscando {n} editais do PNCP...")
        total = scrape(target=n)
        print(f"\nTotal: {total} editais  →  {CORPUS_DIR}")
        stats()
    elif cmd == "stats":
        stats()
    elif cmd == "clear":
        for f in CORPUS_DIR.glob("*.txt"):
            f.unlink()
        print("Corpus PNCP limpo.")
    else:
        print("Uso: python scraper_pncp.py [fetch [N] | stats | clear]")
