# synonyms-pt

Redução de tokens em texto jurídico português via substituição de sinônimos.

Funciona como pré-processamento antes de qualquer chamada a LLM. Sem modelo auxiliar, sem inferência, sem perda semântica.

```bash
pip install synonyms-pt
```

```bash
echo "A controvérsia foi resolvida pelo magistrado." | synonyms compress --domain legal-pt
# → "A disputa foi resolvida pelo juiz."
# → -4 tokens (controvérsia: 4tok → disputa: 1tok, magistrado: 2tok → juiz: 1tok)
```

---

## Por que isso importa

Tokenizadores BPE (GPT-4o, Claude, etc.) são treinados majoritariamente em inglês. Palavras portuguesas — especialmente jargão jurídico derivado do latim — ficam fragmentadas em múltiplos tokens mesmo quando têm sinônimos mais curtos e semanticamente equivalentes.

**O detalhe que importa na medição:**

```python
import tiktoken
enc = tiktoken.get_encoding("o200k_base")

len(enc.encode("fiscalização"))    # → 3 tokens  ← errado pra medir custo real
len(enc.encode(" fiscalização"))   # → 1 token   ← como aparece em texto
len(enc.encode(" controle"))       # → 1 token   ← mesmo custo, nenhum saving aqui
```

O espaço antes da palavra faz parte do token no BPE. Medir em isolamento dá savings falsos. Esta lib mede corretamente.

---

## O que funciona de verdade

Benchmarks em corpus real (352 acórdãos TST + 173 editais PNCP):

| Corpus | Modo | Savings médio | P90 |
|--------|------|--------------|-----|
| TST (acórdãos trabalhistas) | safe-only | 0.33% | 0.55% |
| TST | full | 0.69% | 1.01% |
| PNCP (editais contratos) | safe-only | 0.04% | 0.07% |
| PNCP | full | 1.03% | 1.66% |

Esses números são modestos. Para documentos com vocabulário técnico denso (`consubstanciado`, `arrematante`, `controvérsia`) os savings são maiores — mas não exageramos a média.

**Preservação semântica:** 40 pares de Q&A sobre documentos originais vs. comprimidos via Claude. Nenhuma divergência factual.

---

## Instalação

```bash
pip install synonyms-pt
```

Dependências: `tiktoken`, `click`. Sem modelos, sem downloads.

---

## Uso

### CLI

```bash
# comprime stdin
echo "texto jurídico..." | synonyms compress --domain legal-pt

# mostra o que mudaria sem aplicar
synonyms analyze --domain legal-pt documento.txt

# tokens antes/depois
synonyms stats --domain legal-pt --model gpt-4o documento.txt

# lista o dicionário
synonyms dict list --domain legal-pt
```

### Python

```python
from synonyms import Compressor

c = Compressor(domain="legal-pt", model="gpt-4o", safe_only=True)
result = c.compress("A controvérsia foi resolvida pelo magistrado.")

print(result.text)          # "A disputa foi resolvida pelo juiz."
print(result.tokens_saved)  # 4
print(result.substitution_count)  # 2

# relatório completo
stats = c.stats("texto...")
print(stats["savings_pct"])  # 3.2
```

### safe_only vs full

- **`safe_only=True`** (padrão): 36 pares onde o sinônimo é semanticamente equivalente na grande maioria dos contextos. Recomendado para produção.
- **`safe_only=False`**: 58 pares, inclui substituições contextualmente válidas mas com nuances jurídicas. Cada entrada tem uma nota explicando quando não usar.

---

## O dicionário

58 pares curados manualmente em `data/legal_pt.json`. Cada entrada tem:

```json
{
  "controvérsia": {
    "replacement": "disputa",
    "gender_change": null,
    "safe": true,
    "notes": "controvérsia (4tok) → disputa (1tok). +3 tokens."
  }
}
```

Os pares `safe: false` estão no dicionário mas documentados — `inadimplência → mora`, `licitante → empresa`, etc. Você decide se usa.

---

## Expandir para outros domínios

```bash
# descobre palavras caras no seu corpus
python discover.py --corpus-dir seu/corpus/ --min-tokens 2 --min-freq 5

# OUTPUT:
# consubstanciado    ×223  5 tok
# arrematante        ×342  4 tok
# controvérsia       ×719  4 tok  ✓ (já no dict)
```

Depois valida os candidatos e adiciona ao dicionário. O processo está documentado em [`discover.py`](discover.py).

---

## Reproduzir os benchmarks

```bash
# baixa corpus TST (acórdãos públicos do TST)
python scraper.py fetch 350

# baixa corpus PNCP (editais de contratos públicos)
python scraper_pncp.py fetch 200

# roda benchmark com gráficos
python benchmark_full.py
```

Todos os dados são públicos. Os scrapers são incluídos.

---

## Limitações

- Funciona melhor em texto jurídico PT-BR. Outros domínios precisam de curadoria.
- Savings modestos em texto formulaico (acórdãos de tribunais superiores). Maior impacto em documentos com vocabulário técnico variado.
- Concordância gramatical de gênero é tratada para os pares mapeados, mas construções complexas podem precisar de revisão.
- O dicionário foi curado por humano, não gerado por LLM. É pequeno (58 pares) e cresce devagar.

---

## Licença

MIT
