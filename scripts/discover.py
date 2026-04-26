#!/usr/bin/env python3
"""
dict discover: varre corpus, encontra palavras ≥N tokens em contexto,
e mostra candidatos para o dicionário com frequência real.

Uso:
  python discover.py                          # top 50 palavras caras no corpus
  python discover.py --min-tokens 2 --top 100
  python discover.py --text "arquivo.txt"     # texto avulso
"""

import re
import sys
import argparse
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from synonyms.tokenizer import get_encoding

CORPUS_DIR = Path(__file__).parent.parent / "samples" / "corpus"

# Palavras a ignorar: funcionais, artigos, preposições, muito curtas
STOPWORDS = {
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "por", "para", "com", "sem", "sob", "sobre", "até", "após",
    "ante", "perante", "entre", "contra", "desde", "durante",
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "que", "se", "não", "mais", "mas", "ou", "e", "nem",
    "ao", "aos", "à", "às", "pelo", "pela", "pelos", "pelas",
    "num", "numa", "nuns", "numas", "dum", "duma",
    "este", "esta", "estes", "estas", "esse", "essa", "esses", "essas",
    "aquele", "aquela", "aqueles", "aquelas",
    "seu", "sua", "seus", "suas", "meu", "minha",
    "qual", "quais", "quando", "onde", "como", "porque", "pois",
    "ser", "ter", "estar", "fazer", "poder", "dever",
    "foi", "são", "era", "será", "seja", "sido", "sendo",
    "tem", "têm", "tinha", "teria", "tiver",
    "pode", "deve", "há", "houve",
    "id", "nr", "nº", "art", "arts",
}

# Padrão: só palavras (sem números, siglas curtas, pontuação)
WORD_RE = re.compile(r'\b([a-záéíóúâêôãõàèìòùçü]{5,})\b', re.IGNORECASE)


def tokenize_corpus(paths: list[Path], model: str) -> Counter:
    enc = get_encoding(model)
    freq: Counter = Counter()

    for path in paths:
        text = path.read_text(encoding="utf-8")
        # pula o header (primeiras linhas até ──)
        body_start = text.find("─" * 10)
        if body_start > 0:
            text = text[body_start:]

        for match in WORD_RE.finditer(text):
            word = match.group(1).lower()
            if word in STOPWORDS or len(word) < 5:
                continue
            freq[word] += 1

    return freq


def count_in_context(word: str, enc) -> int:
    return len(enc.encode(" " + word))


def main() -> None:
    p = argparse.ArgumentParser(description="Descobre palavras caras em corpus")
    p.add_argument("--min-tokens", type=int, default=2,
                   help="Mínimo de tokens em contexto para incluir (default: 2)")
    p.add_argument("--top", type=int, default=60,
                   help="Quantas palavras mostrar (default: 60)")
    p.add_argument("--min-freq", type=int, default=3,
                   help="Frequência mínima no corpus (default: 3)")
    p.add_argument("--model", default="gpt-4o")
    p.add_argument("--text", help="Arquivo de texto avulso em vez do corpus")
    args = p.parse_args()

    enc = get_encoding(args.model)

    if args.text:
        paths = [Path(args.text)]
    else:
        paths = list(CORPUS_DIR.glob("*.txt"))
        if not paths:
            print("Corpus vazio. Rode: python scraper.py fetch")
            sys.exit(1)

    print(f"\nAnalisando {len(paths)} documento(s) com {args.model}...")
    freq = tokenize_corpus(paths, args.model)

    # Filtra por frequência mínima e custo em tokens
    candidates = []
    for word, count in freq.most_common():
        if count < args.min_freq:
            continue
        tok_count = count_in_context(word, enc)
        if tok_count >= args.min_tokens:
            candidates.append((word, count, tok_count))

    # Ordena por tokens desc, depois frequência desc
    candidates.sort(key=lambda x: (-x[2], -x[1]))

    print(f"\n{'─'*70}")
    print(f"  {'palavra':<25} {'freq':>6}  {'tok em contexto':>15}  {'em dict?':>9}")
    print(f"{'─'*70}")

    import json
    existing = json.loads((Path(__file__).parent.parent / "data" / "legal_pt.json").read_text())

    shown = 0
    for word, count, tok in candidates[:args.top]:
        in_dict = "✓" if word in existing else ""
        print(f"  {word:<25} {count:>6}×   {tok:>3} tok              {in_dict:>9}")
        shown += 1

    print(f"{'─'*70}")
    print(f"  Total únicas ≥{args.min_tokens} tok: {len(candidates)}  |  mostrando top {shown}")
    print(f"\n  Próximo passo: escolher palavras sem ✓ e buscar sinônimos")
    print(f"  Exemplo: python discover.py | grep -v '✓' | head -20\n")


if __name__ == "__main__":
    main()
