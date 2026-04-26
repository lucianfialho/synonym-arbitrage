---
name: legal-pt-ul
description: Maintain the ubiquitous language glossary for Brazilian legal domain. Use when user wants to add terms, flag ambiguities, or update canonical choices in UBIQUITOUS_LANGUAGE.md.
---

# Legal PT — Ubiquitous Language Maintainer

Maintain `UBIQUITOUS_LANGUAGE.md` for the Brazilian legal domain, keeping canonical terms aligned with the token-efficiency criterion in `data/legal_pt.json`.

## Process

1. Read `UBIQUITOUS_LANGUAGE.md` and `data/legal_pt.json`
2. Identify what changed or what the user wants to add
3. For each new term candidate:
   - Check token cost: `from synonyms.tokenizer import count; count(" " + word)`
   - Only canonicalize if a shorter-token synonym exists
   - Mark `safe: false` if legal semantics differ
4. Update `UBIQUITOUS_LANGUAGE.md` tables
5. If a new pair is valid, also add to `data/legal_pt.json`
6. Output a summary of changes

## Criteria for canonical term selection

- **Token cost wins** when semantics are equivalent (e.g., `disputa` = 1 tok vs `controvérsia` = 4 tok)
- **Precision wins** when semantics differ (keep `inadimplemento` and `mora` separate)
- **Domain expert wins** when a term has established legal meaning — add to "terms to NOT substitute" section

## Output format

Update `UBIQUITOUS_LANGUAGE.md` in place. Add new rows to appropriate table. If a new category emerges, create a new table.

Summarize inline:
- Terms added: N
- Terms flagged as ambiguous: N
- Terms moved to "do not substitute": N
