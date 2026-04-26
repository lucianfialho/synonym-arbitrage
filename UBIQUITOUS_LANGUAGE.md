# Ubiquitous Language — Legal PT

Glossário canônico para domínio jurídico brasileiro.
Gerado a partir de `data/legal_pt.json` — termos canônicos escolhidos por menor custo em tokens BPE (o200k_base, GPT-4o).

**Como usar:** inclua este glossário como system prompt (ou `--append-system-prompt`) ao processar documentos jurídicos com LLMs. O modelo usará os termos canônicos nas respostas, reduzindo tokens no output.

---

## Partes do processo

| Termo canônico | Definição | Aliases a evitar |
|---|---|---|
| **autor** | Parte que propõe a ação (polo ativo) | requerente, reclamante, demandante, peticionário |
| **ré** | Polo passivo feminino | requerida, reclamada, demandada |
| **réu** | Polo passivo masculino | requerido, reclamado, demandado, imputado |
| **parte** | Qualquer litigante do processo | litigante |
| **credor** | Quem tem direito a receber | exequente |
| **devedor** | Quem deve cumprir obrigação | executado |
| **advogado** | Representante legal constituído | procurador (quando for advogado) |
| **apelante** | Quem recorre da decisão | recorrente |
| **apelada** | Polo passivo do recurso | recorrida |
| **comprador** | Quem arremata em leilão | arrematante |

## Tribunal e jurisdição

| Termo canônico | Definição | Aliases a evitar |
|---|---|---|
| **juiz** | Magistrado que conduz o processo | magistrado |
| **juíza** | Forma feminina | magistrada |
| **decisão** | Pronunciamento judicial | pronunciamento, decisum, despacho (cuidado: tecnicamente distintos) |
| **aprovação** | Ato de homologar ou habilitar resultado | homologação, habilitação |
| **aviso** | Comunicação formal entre partes | notificação |
| **extinção** | Encerramento do contrato ou processo | rescisão (cuidado: rescisão implica descumprimento) |

## Conceitos processuais

| Termo canônico | Definição | Aliases a evitar |
|---|---|---|
| **disputa** | Controvérsia jurídica entre partes | controvérsia |
| **mora** | Estado de inadimplemento obrigacional | inadimplência, inadimplemento |
| **cumprimento** | Estado de adimplência | adimplência |
| **prazo** | Período para praticar ato processual | dilação, interstício |
| **violação** | Descumprimento de norma ou obrigação | desrespeito |
| **rever** | Examinar novamente a matéria | rediscutir |
| **restando** | Permanecendo pendente | remanescendo |
| **provou** | Demonstrou o ônus probatório | desincumbiu |
| **análise** | Exame da matéria | cognição (cuidado: cognição tem sentido técnico) |
| **contestação** | Impugnação formal ao pedido | impugnação |
| **dispensa** | Hipótese de contratação direta | inexigibilidade (cuidado: são hipóteses distintas) |

## Licitações e contratos públicos

| Termo canônico | Definição | Aliases a evitar |
|---|---|---|
| **comprador** | Quem arremata em leilão público | arrematante |
| **compra** | Ato de arrematar | arrematação |
| **empresa** | Pessoa jurídica participante de licitação | licitante (cuidado: licitante é mais preciso) |
| **grupo** | Conjunto de empresas associadas | consórcio (cuidado: consórcio tem forma jurídica específica) |
| **reprovação** | Inabilitação em licitação | inabilitação |

## Construções latinas e formais

| Termo canônico | Definição | Aliases a evitar |
|---|---|---|
| **baseado** | Fundamentado em | consubstanciado |
| **externo** | Relativo a requisito formal | extrínseco |
| **interno** | Relativo a requisito de mérito | intrínseco |
| **moral** | Dano não patrimonial (CLT art. 223-A) | extrapatrimonial |
| **vê** | Constata, identifica | vislumbra |
| **diz** | Estabelece, determina (referindo-se a norma) | preceitua |
| **excesso** | Falta de proporcionalidade | desproporcionalidade |
| **objetivo** | Propósito, finalidade | desiderato |

---

## Relações entre termos

- Um **autor** propõe ação contra um **réu** perante um **juiz**
- O **juiz** emite **decisões** que podem ser impugnadas via recurso pelo **apelante**
- Em licitações, o **comprador** é quem vence a **compra** (não necessariamente uma **empresa** — pode ser pessoa física)
- **Mora** é o estado; **violação** é o ato — não são sinônimos perfeitos

---

## Termos a NÃO substituir

Estes têm significado jurídico preciso sem equivalente mais curto:

- `comarca` — em contexto de nome próprio ("Comarca de São Paulo") nunca substituir
- `licitante` — mais preciso que `empresa` em textos de licitação formal
- `magistrado` — quando o cargo é o ponto, não a pessoa
- `habilitação` — fase específica do processo licitatório
- `inadimplemento` — diferente de `mora` (mora = atraso, inadimplemento = não-cumprimento)

---

## Exemplo de uso como system prompt

```
Ao responder sobre documentos jurídicos brasileiros, use os seguintes termos canônicos:
- autor (não: requerente, reclamante)
- réu/ré (não: requerido/a, reclamado/a)
- juiz (não: magistrado)
- disputa (não: controvérsia)
- mora (não: inadimplência)
- baseado (não: consubstanciado)
Preserve termos técnicos sem equivalente mais curto (comarca em nomes próprios, habilitação em licitações).
```
