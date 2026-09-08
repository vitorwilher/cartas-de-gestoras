# E-mail de lançamento — tag Mercado Financeiro (ConvertKit)

**Status: RASCUNHO. Não disparado.** Por decisão do Vitor (2026-09-08), nada sai
sem comando explícito.

- **Segmento:** tag `Mercado Financeiro`, ID **22406993** — 530 assinantes
  (conferido na API do ConvertKit em 2026-09-08). Não usar a tag 22775548
  ("Mercado Financeiro e Investimentos"): está zerada e é órfã.
- **Nível de consciência:** 2-3. Esta lista conhece a AM e conhece o mercado, mas
  não sabe que este produto existe. Abre com a dor, não com o preço.
- **Ângulo:** o trabalho concreto — ninguém lê 12 cartas por mês.

## Ficha de fatos (tudo conferido na fonte em 2026-09-08)

| Fato | Valor | Fonte |
|---|---|---|
| Gestoras cobertas | 12 | `gestoras/gestoras.yml` |
| Mensais / irregulares | 10 / 2 | idem, campo `periodicidade` |
| Preço | R\$ 97/mês | definido pelo Vitor |
| Plugin de recorrência | WooCommerce Subscriptions ativo | `system_status` da API do Woo |
| Slug do produto | `cartas-de-gestoras` (livre) | API do Woo |
| Edições já geradas | 3 | `digests/resumo/` |
| Maior cobertura numa edição | 11 gestoras | `mcp/catalogo.json` |
| Acervo de exercícios (matéria-prima) | 88 em Python, Mercado Financeiro | `exercicios/acervo.json` |

⚠️ **Campos ainda VAZIOS — não podem virar texto:**
- Não há data de fim de campanha. **Sem urgência real, o e-mail fecha sem ela**
  (regra 5 da skill: não inventar).
- Não há depoimento deste produto — ele não tem cliente ainda.
- Não há garantia definida. Se for adotar os 7 dias padrão da casa, precisa
  confirmar que vale para assinatura recorrente.

---

## Assunto

> Doze cartas de gestora por mês. Ninguém lê todas.

Alternativo (mais direto, nível 3):

> O que a Bahia e a Adam discordam sobre juros longos

## Corpo

> Toda virada de mês, doze gestoras publicam suas cartas. Dynamo, IP, Alaska,
> Kapitalo, Adam, Legacy, Bahia, Occam, JGP, Kinea, NEO e Dahlia.
>
> Você provavelmente lê duas ou três. As que já conhece, ou as que alguém comentou
> no grupo. As outras nove ficam na aba aberta até a semana virar.
>
> O problema não é o tempo de leitura. É que **o valor de ler doze cartas está
> justamente em compará-las** — em ver onde o consenso se forma e onde racha. Uma
> carta isolada te dá a visão de uma casa. Doze te dão o mapa do que o mercado
> brasileiro está apostando, e onde ele está dividido.
>
> Foi para isso que montei as **Cartas de Gestoras**.
>
> **Como funciona**
>
> Toda terça, um pipeline lê as cartas novas das doze gestoras e entrega uma
> síntese. Não um resumo — uma análise que expõe, de cada gestora, o **mecanismo**
> por trás da aposta: a cadeia causal que faz a tese se pagar, e a condição em que
> ela quebra.
>
> Depois vem a seção que só existe porque as doze estão juntas: **convergências e
> divergências**. Na edição de 8 de setembro, por exemplo, Adam, Legacy e Occam
> convergiam que capex em IA e emissão de dívida disputam a mesma poupança — e é
> aí que a leitura conjunta paga.
>
> **E um exercício em Python**
>
> Aqui está a diferença que importa. Toda edição traz um exercício em código, com
> dados públicos brasileiros, que verifica o mecanismo da semana. Se a Bahia está
> tomada em inclinação de juros nominal, o exercício monta a curva DI e mostra
> como se lê aquela inclinação.
>
> Não é para você concordar com a gestora. É para você **conseguir checar**.
>
> **Onde chega**
>
> O PDF no seu WhatsApp assim que sai. E, se você trabalha com Claude Code ou
> Codex, um servidor MCP para consultar o histórico direto do seu terminal —
> perguntar como a tese da Kinea evoluiu nos últimos meses, sem sair do editor.
>
> **R\$ 97 por mês.** Assinatura, cancela quando quiser.
>
> Uma ressalva honesta: as cartas não são todas mensais. Dynamo e IP publicam
> ensaios irregulares — e são os de maior densidade. A cadência semanal existe
> para não perder nenhum. **Quando nenhuma gestora publica nada, não há edição
> naquela semana** — você não recebe e-mail vazio.
>
> [Assinar as Cartas de Gestoras →]
>
> — Vitor Wilher

---

## Notas de auditoria

- ✅ Sem escassez inventada; sem contador; sem "últimas vagas".
- ✅ Todo número conferido na fonte (tabela acima).
- ✅ Ressalva técnica presente e em posição de destaque: a cadência é irregular e
  pode não haver edição na semana.
- ✅ Nenhuma promessa de retorno financeiro — o produto ensina método, não sinal.
- ✅ Um ângulo só; sem emoji; sem superlativo.
- ⚠️ **Falta a âncora de preço.** A skill manda usar "De X por Y" no fecho. Sem
  preço de tabela definido, entra só o valor cheio — o que é honesto, mas mais
  fraco. Decisão do Vitor: existe preço de lançamento?
- ⚠️ **Falta o link do checkout.** Só existe depois que o produto for publicado no
  Woo. Testar o carrinho ao vivo antes de disparar, lendo o preço na página.
