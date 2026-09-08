# Carrossel de Instagram — lançamento das Cartas de Gestoras

**Status: RASCUNHO. Não publicado.**

Regras do canal (do CLAUDE.md do ROI_Diagnostico e da skill de copy):
- **Abre com cena/narrativa, não com rótulo** — está medido: série que abre com
  rótulo engaja metade.
- CTA de **salvamento + pergunta**. CTA de venda derruba alcance.
- Publicação via `connectors/instagram.py::publish_carousel` (Graph API).

---

**Slide 1 — a cena**

> Doze gestoras publicam carta todo mês.
>
> Você lê duas.

**Slide 2 — a tensão**

> O problema não é o tempo.
>
> É que o valor de ler doze cartas está em compará-las — e ninguém compara doze
> PDFs abertos ao mesmo tempo.

**Slide 3 — o que se perde**

> Uma carta isolada mostra a visão de uma casa.
>
> Doze mostram onde o mercado brasileiro concorda — e onde ele racha.

**Slide 4 — exemplo real**

> Edição de 8 de setembro:
>
> Adam, Legacy e Occam convergiam que capex em IA e emissão de dívida disputam a
> mesma poupança. Três casas diferentes, o mesmo mecanismo.
>
> Isso só aparece lendo as três juntas.

**Slide 5 — o mecanismo, não o resumo**

> Resumo diz o que a gestora falou.
>
> O que importa é o mecanismo: por que a aposta se paga, e o que precisaria ser
> verdade para ela falhar.

**Slide 6 — a verificação**

> E se desse para checar?
>
> Se a gestora está tomada em inclinação de juros, dá para montar a curva DI em
> Python e olhar com os próprios olhos.

**Slide 7 — fecho + CTA de salvamento**

> Salva esse post para quando for ler a próxima carta.
>
> E me conta: qual gestora você acompanha de verdade?

---

## Notas

- Sem preço nos slides: o público do Instagram está em nível 1-2 de consciência.
  Preço no primeiro toque é o erro documentado que gerou 174 mensagens e zero
  respostas na campanha de Claude Code T2.
- O exemplo do slide 4 é real, extraído de `digests/resumo/resumo-2026-09-08.qmd`.
- ⚠️ Se virar anúncio: nome de campanha/adset **sem pipe (`|`)** — a macro
  `{{campaign.name}}` entra na URL e o firewall devolve 403 de tela branca. Já
  custou R\$ 385,72 em nove dias.
