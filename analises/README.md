# Mapa da indústria de gestão de recursos do Brasil

Apuração sobre dados públicos da CVM, cruzando o cadastro de fundos com o
cadastro de administradores de carteira. Reproduz com `python3 mapa_industria.py`.

**Data-base:** 11/09/2026 (PL informado pelos fundos majoritariamente em 2025).

---

## O que é apurado e o que não é

Este documento tem duas partes, e a separação é deliberada.

A **Parte 1** sai dos dados: quantas gestoras existem, que fundos administram,
como o patrimônio se divide. Cada número é reproduzível pelo script.

A **Parte 2** é hipótese de negócio. As perguntas sobre "interesses das pessoas
que trabalham nas gestoras" e "que produtos elas vendem" **não têm resposta em
base cadastral** — nenhum dado da CVM diz o que um analista quer aprender. O que
faço ali é derivar hipóteses do que os dados mostram, marcadas como tal. Tratar
a Parte 2 como fato seria inventar.

---

# Parte 1 · O apurado

## O universo

| | |
|---|---|
| Gestoras PJ autorizadas pela CVM (ativas) | **1.547** |
| Dessas, com ao menos um fundo sob gestão | **1.260** |
| Autorizadas **sem nenhum fundo** | 287 |
| Fundos em funcionamento | **33.445** |
| Classes em funcionamento | 33.676 |
| PL somado (fundos com PL informado) | **~R$ 13,3 tri** |

⚠️ 25,9% dos fundos não informam PL. As somas cobrem os ~24,8 mil que informam.

## A divisão macro

Por classificação ANBIMA, em % do patrimônio:

| Bloco | Classes | % do PL |
|---|---|---|
| **Renda Fixa** | 6.012 | **34,2%** |
| **Multimercado** | 10.856 | **31,2%** |
| **Previdência** | 4.407 | **17,1%** |
| Não classificado | 8.367 | 13,4% |
| **Ações** | 3.769 | **3,5%** |
| Outros (FII/FIDC/FIP) | 201 | 0,5% |
| Cambial | 64 | 0,1% |

**A leitura que importa:** renda fixa e multimercado somam **65% do patrimônio**.
Ações são **3,5%** — apesar de 3.769 classes dedicadas a elas. É uma indústria
de juro e de macro, não de *stock picking*. Previdência sozinha (17%) vale cinco
vezes o mercado de ações.

## A concentração

| Recorte | % do PL |
|---|---|
| Top 5 gestoras | **51,6%** |
| Top 10 | 61,7% |
| Top 20 | 69,6% |
| Top 50 | 80,7% |
| Top 100 | 88,0% |

As cinco maiores são **BB (17,6%), Itaú (13,2%), Bradesco (10,6%), Caixa (5,9%)
e Santander (4,3%)** — todas braço de banco. Metade da indústria é bancária.

Mas a cauda é o número relevante para a AM: as **1.240 gestoras fora do top 20**
somam **R$ 4,03 tri (30,4% do PL)**. Não são irrelevantes — são desassistidas.

## O porte típico

| Faixa de PL | Gestoras |
|---|---|
| 100 bi+ | 14 |
| 10 a 100 bi | 108 |
| 1 a 10 bi | 339 |
| 100 mi a 1 bi | 404 |
| Abaixo de 100 mi | 279 |
| Sem PL informado | 116 |

**Mediana: 6 fundos e R$ 428 milhões de PL.** A gestora típica do Brasil é
pequena. Metade administra 6 fundos ou menos; 25% administram 2 ou menos.

## Onde estão

**SP concentra 869 gestoras (R$ 8,5 tri)** e **RJ 178 (R$ 3,4 tri)**. Juntos,
83% das casas e 89% do patrimônio. O terceiro colocado (DF) tem 12 gestoras.

## Público-alvo dos fundos

| Público | Classes | PL |
|---|---|---|
| Profissional | 16.013 | R$ 12,1 tri |
| Público Geral | 5.344 | R$ 5,3 tri |
| Qualificado | 3.561 | R$ 1,1 tri |

## As 12 gestoras do produto, dentro desse mapa

| Grupo | PJs | Fundos | PL (R$ bi) | % da indústria |
|---|---|---|---|---|
| Kinea | 2 | 361 | 177,32 | 1,34% |
| Kapitalo | 3 | 110 | 42,43 | 0,32% |
| Legacy | 1 | 108 | 25,15 | 0,19% |
| Dynamo | 2 | 15 | 20,04 | 0,15% |
| Occam | 2 | 73 | 14,04 | 0,11% |
| JGP | 3 | 83 | 13,84 | 0,10% |
| Alaska | 1 | 27 | 8,78 | 0,07% |
| Bahia Asset | 2 | 38 | 6,39 | 0,05% |
| NEO | 3 | 63 | 5,87 | 0,04% |
| Dahlia | 1 | 67 | 4,59 | 0,03% |
| IP Capital | 1 | 28 | 4,24 | 0,03% |
| Adam | 1 | 36 | 3,68 | 0,03% |
| **Juntas** | **22** | **1.011** | **326,4** | **2,46%** |

**Achado que muda o enquadramento do produto:** as 12 casas mais lidas do país
administram **2,46% do patrimônio**. O produto cobre a elite editorial da
indústria, não a elite patrimonial. São duas indústrias diferentes — e o alcance
comercial da AM não está limitado ao peso financeiro dessas casas.

A Kinea sozinha (R$ 177 bi, braço do Itaú) vale mais que as outras onze somadas.
A Dynamo, referência editorial máxima, administra R$ 20 bi em 15 fundos.

---

# Parte 2 · Hipóteses de negócio

> Nada abaixo é dado. São inferências a partir da Parte 1, marcadas para que não
> sejam confundidas com apuração. Cada uma traz como testá-la.

## Que produtos essas casas vendem

Derivável dos dados com segurança razoável: vendem **fundos**, majoritariamente
de renda fixa e multimercado, para **investidor profissional** (R$ 12,1 tri dos
R$ 13,3 tri). O produto da indústria é gestão de patrimônio de terceiros sob
mandato — não conteúdo, não ferramenta.

Isso importa para a AM porque define o que a gestora **compra**: ela não compra
formação por hobby. Compra o que reduz custo de análise, acelera time novo, ou
vira insumo do material que ela mesma manda ao cotista.

## Quem trabalha lá — e o que essa pessoa quer

**Hipótese, não dado.** O que sustenta: 65% do PL em renda fixa e multimercado
implica times que trabalham com juro, câmbio, inflação e macro — exatamente o
terreno técnico da Análise Macro. Ações, onde a AM tem menos a dizer, é 3,5%.

A gestora mediana (6 fundos, R$ 428 mi) não tem time de dados. Não tem quem
construa pipeline de IPCA, monitor de Copom ou backtest de curva. Nas grandes,
isso é departamento; nas 1.240 da cauda, é o próprio gestor no Excel.

**Como testar:** ler as vagas abertas dessas casas (LinkedIn, Gupy) e ver que
stack pedem. É a pesquisa de campo que ficou fora deste escopo.

## Como a AM vira fornecedora dessa indústria

Quatro hipóteses, da mais próxima do que já existe à mais distante:

**1. Formação corporativa para a cauda.** 1.240 gestoras fora do top 20, medianas
de 6 fundos, sem time de dados. A AM já tem o catálogo (Python, séries temporais,
macro aplicada). O que falta é a porta B2B: turma fechada, in-company, por casa.
É a hipótese mais barata de testar — uma proposta a dez casas responde.

**2. O produto atual como porta de entrada.** As Cartas já colocam a AM na frente
de quem lê as 12. Um assinante dentro de uma gestora é um caso de uso corporativo
esperando acontecer.

**Isto deixou de ser hipótese — foi verificado em 11/09/2026.** Dos 38 leads da
landing, **6 (16%) usam e-mail corporativo do próprio setor**:

| Domínio | O que é |
|---|---|
| `xpi.com.br` | XP Investimentos |
| `safra.com.br` | Banco Safra |
| `suno.com.br` | Suno Research |
| `kpwealth.com.br` | wealth management |
| `farosmfo.com.br` | multi-family office |
| `fundacaoatlantico.com.br` | fundo de pensão |

Com 38 leads e sem divulgação paga, **um em cada seis já é do setor**, chegando
por conta própria. É a evidência mais forte deste documento a favor da via B2B —
e a mais barata de acompanhar: basta reler os domínios a cada 100 leads novos.

⚠️ Amostra de 38. O padrão é sugestivo, não estatisticamente robusto.

**3. Dado e ferramenta.** O MCP do projeto já serve conteúdo por assinatura. A
mesma arquitetura serve série tratada, núcleo de inflação, monitor de Copom. A
gestora mediana compraria acesso pronto em vez de construir. É a hipótese de
maior margem e maior esforço.

**4. Conteúdo white-label.** As casas precisam escrever para cotistas todo mês —
é literalmente o insumo deste projeto. A AM sabe produzir análise macro em
escala. Vender a produção da carta (ou do anexo técnico) é mercado adjacente ao
que ela já faz.

## O que eu não sei e recomendo apurar antes de decidir

- **Que perfil técnico essas casas contratam.** Só vagas reais respondem.
- **Se já existe fornecedor ocupando esse espaço.** Não pesquisei concorrência.
- **Quanto uma gestora paga por formação.** Nenhum dado aqui toca preço.
- **Se a cauda tem orçamento.** R$ 428 mi de PL mediano com taxa de ~1% dá
  ~R$ 4,3 mi de receita anual. Cabe treinamento, mas não é orçamento infinito.

---

## Arquivos

| Arquivo | O que é |
|---|---|
| `mapa_industria.py` | O script. Todo número acima sai dele |
| `gestoras_consolidado.csv` | 1.260 gestoras, com fundos, PL, UF, porte |
| `divisao_macro.csv` | Distribuição por bloco ANBIMA |
| `resumo.json` | Todos os agregados, inclusive os não citados aqui |

### Fontes

- `registro_fundo_classe.zip` — CVM Dados Abertos (cadastro vigente, pós-RCVM 175)
- `cad_adm_cart.zip` — CVM, administradores de carteira

⚠️ **Não usar `cad_fi.csv`** para retrato do presente: apesar do nome, é o cadastro
do regime antigo — 46.575 de 46.806 registros estão CANCELADA e só 22 em
funcionamento. Um script apontado para ele responde "13 fundos no Brasil" sem
erro nenhum. Aconteceu na primeira versão desta análise.

### As três limpezas sem as quais o resultado é absurdo

1. **PL impossível.** SOLE, MARE e SERENA (Genesis Capital) declaram R$ 16,68
   **trilhões cada**, valor idêntico e mesma data — R$ 50 tri somados, mais que o
   PIB. Sem cortar, a Genesis aparece como 78% da indústria, à frente do BB.
2. **Multi-gestor.** 614 fundos têm mais de um gestor e apareciam em duplicidade,
   inflando o total em R$ 0,56 tri.
3. **Placeholder de nome.** `DENOM_COMERC` vem como `--` ou `-----` quando não há
   nome fantasia. Sem tratar, 136 gestoras viram "--" — incluindo **Santander
   (R$ 573 bi)** e **Kinea (R$ 169 bi)**, que somem de qualquer ranking por nome.

Com as três: R$ 13,3 tri. Sem elas: R$ 63,9 tri.

⚠️ Os nomes de fantasia **não batem** com a razão social na CVM: a IP é
"INVESTIDOR PROFISSIONAL", a Adam é "ADAMCAPITAL" (sem espaço), a Bahia é "BAHIA
AM". Buscar por "IP Capital" ou "Adam Capital" devolve vazio **em silêncio**.
