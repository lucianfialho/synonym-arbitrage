#!/usr/bin/env python3
"""Scraper: TST acórdãos → corpus. API pública do TST."""

import sys
import time
import random
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from tst_queries import QUERIES

CORPUS_DIR = Path(__file__).parent / "samples" / "corpus"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://jurisprudencia-backend2.tst.jus.br/rest/pesquisa-textual/{offset}/{limit}"

PAGE_SIZE   = 15   # docs por request
PAGES_QUERY = 5    # páginas por query → 75 docs/query no máximo
MIN_CHARS   = 800
RATE_LIMIT  = 0.35


def clean_html(raw: str) -> str:
    # CDATA wrapper makes BeautifulSoup treat inner HTML as text, not tags.
    # Strip markers first so the inner HTML gets properly parsed.
    raw = re.sub(r"<!\[CDATA\[", "", raw)
    raw = re.sub(r"\]\]>", "", raw)
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_page(query: str, offset: int) -> tuple[list[dict], int]:
    url = API_URL.format(offset=offset, limit=PAGE_SIZE)
    body = {"ou": query, "tipos": [{"codigo": "ACORDAO"}]}
    try:
        resp = httpx.post(
            url, json=body,
            headers={"Content-Type": "application/json"},
            timeout=20.0,
            params={"a": random.randint(1000, 9999)},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("registros", []), data.get("totalRegistros", 0)
    except Exception as e:
        print(f"    [erro offset={offset}] {e}", file=sys.stderr)
        return [], 0


def extract(reg: dict) -> str | None:
    raw = (
        reg.get("inteiroTeorHtml") or
        reg.get("txtConteudoDecisao") or
        reg.get("txtConteudoDecisaoHighlight") or ""
    )
    if not raw:
        return None
    text = clean_html(raw)
    return text if len(text) >= MIN_CHARS else None


def scrape(target: int = 1000, verbose: bool = True) -> int:
    existing = {p.stem for p in CORPUS_DIR.glob("*.txt")}
    saved = 0

    for query in QUERIES:
        if saved >= target:
            break

        if verbose:
            print(f"\n  [{saved:>4}/{target}] query: '{query}'")

        for page in range(PAGES_QUERY):
            if saved >= target:
                break

            offset = page * PAGE_SIZE + 1
            records, total = fetch_page(query, offset)
            time.sleep(RATE_LIMIT)

            if not records:
                break

            for item in records:
                reg    = item.get("registro", {})
                doc_id = reg.get("id") or ""
                if not doc_id or doc_id in existing:
                    continue
                text = extract(reg)
                if not text:
                    continue
                numero = reg.get("numFormatado", doc_id)
                orgao  = reg.get("orgaoJudicante", {}).get("descricao", "TST")
                pub    = reg.get("dtaPublicacao", "")[:10]
                tipo   = reg.get("tipo", {}).get("codigoTipoJurisprudencia", "ACORDAO")
                header = (f"TRIBUNAL SUPERIOR DO TRABALHO\nÓRGÃO: {orgao}\n"
                          f"PROCESSO: {numero}\nPUBLICAÇÃO: {pub}\nTIPO: {tipo}\n"
                          f"{'─'*60}\n\n")
                (CORPUS_DIR / f"{doc_id}.txt").write_text(header + text, encoding="utf-8")
                existing.add(doc_id)
                saved += 1
                if verbose:
                    print(f"    [{saved:>4}] {numero[:45]:<45} {len(text):>7} chars")
                if saved >= target:
                    break
            if len(records) < PAGE_SIZE:
                break

    return saved


def stats() -> None:
    docs = list(CORPUS_DIR.glob("*.txt"))
    if not docs:
        print("Corpus vazio.")
        return
    from statistics import mean, median
    sizes = [len(p.read_text()) for p in docs]
    print(f"\nCorpus TST: {len(docs)} docs | "
          f"avg {mean(sizes):.0f} chars | median {median(sizes):.0f} | "
          f"min {min(sizes)} | max {max(sizes)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    n   = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

    if cmd == "fetch":
        already = len(list(CORPUS_DIR.glob("*.txt")))
        print(f"Corpus atual: {already} docs. Buscando até {n} total...")
        total = scrape(target=n)
        print(f"\nTotal salvo: {total} novos  |  corpus total: {len(list(CORPUS_DIR.glob('*.txt')))}")
        stats()
    elif cmd == "stats":
        stats()
    elif cmd == "clear":
        for f in CORPUS_DIR.glob("*.txt"):
            f.unlink()
        print("Corpus limpo.")
    else:
        print("Uso: python scraper.py [fetch [N] | stats | clear]")
