# Carrossel de Instagram — Cartas de Gestoras

**Status: edição de 29/09 PRONTA, NÃO publicada** — aguarda revisão do Vitor.

- **Arquivos:** `divulgacao/carrossel/slide-01.png` … `slide-10.png` (1080×1350)
- **Gerador:** `python divulgacao/carrossel.py` (reexecuta o exercício da edição)
- **Publicar:** `python divulgacao/publicar_instagram.py` (dry-run por padrão)
- **Palavra-chave da DM:** `GESTORAS` — ver `manychat-gestoras.md` (a DM é genérica
  desde 23/09 e serve a esta edição sem mudança)
- **Números conferidos:** 01/10/2026, Yahoo Finance (S&P 500 até 30/09; Ibovespa e
  dólar até 01/10)

## Por que este ângulo (edição de 29/09)

**"A GMO vê 20 pontos de vento contra o S&P 500. Quanto disso chega ao Brasil?"**
A edição só teve GMO e Bridgewater, e o exercício mede o beta do Ibovespa em dólar
ao S&P 500 separado por regime. O contraste se lê em dois segundos: aplicado a um
S&P −20%, o beta de mercado calmo (0,96) dá −19%; o beta medido nas correções
(1,34), −27%.

Um ângulo só. Ficaram de fora o preço do carbono da Bridgewater e a mecânica de
inelasticidade da demanda por ações (o multiplicador de 4x da GMO).

⚠️ O slide 2 do padrão é "no que as cartas concordam". Sem carta brasileira e com a
Bridgewater em outro tema, ele virou **"O que a GMO argumenta"** — a mesma posição
na sequência (a tese, com ✓), sem inventar consenso.

## Os 10 slides

| # | Tipo | Conteúdo |
|---|---|---|
| 1 | capa + gráfico | "A GMO vê 20 pontos de vento contra o S&P 500. Quanto disso chega ao Brasil?" — duas barras: −19% (beta calmo) e −27% (beta de correção) |
| 2 | lista ✓ | O que a GMO argumenta: oferta de ações como gatilho, ~20 pontos em 12-18 meses |
| 3 | lista | Onde isso pesa: venda do que é líquido; bolsa e real como fonte de caixa |
| 4 | definição | Beta / Correção / Beta por regime — **antes** dos gráficos de série |
| 5 | lista | Por que custa dinheiro |
| 6 | capa + gráfico | Dispersão semanal desde 2004, por regime, com a reta de cada um (1,34 × 0,96) |
| 7 | capa + gráfico | Distância do S&P 500 até a máxima, linha dos −10% e o ponto de hoje (−0,9%) |
| 8 | lista | O que o dado diz — inclui "hoje o regime é calmo" e "âncora, não previsão" |
| 9 | lista numerada | O caminho que eu fiz |
| 10 | CTA | GESTORAS + "na sua conta de risco, o beta do Brasil é um número só?" |

## Legenda do post

> Na semana de 10 de outubro de 2008, o S&P 500 caiu 18%. O Ibovespa, medido em
> dólar, caiu 28% — e o dólar subiu 11% contra o real no mesmo intervalo.
>
> Em março de 2020, de novo: o S&P 500 caiu 15% numa semana, e o Ibovespa em
> dólar, 24%.
>
> A GMO publicou sua carta trimestral argumentando que o gatilho da bolha de IA
> será a oferta de ações — SpaceX, OpenAI, Anthropic e as emissões das gigantes
> de nuvem — e estima um vento contrário de cerca de 20 pontos sobre o S&P 500 em
> 12 a 18 meses.
>
> A pergunta para quem está no Brasil: quanto disso chega aqui?
>
> Medi com dado público, semanal, desde 2004. Nas semanas calmas, o beta do
> Ibovespa em dólar ao S&P 500 é 0,96. Nas semanas em que o S&P 500 está em
> correção (mais de 10% abaixo da máxima de um ano), sobe para 1,34. Aplicado a
> uma queda de 20%, é a diferença entre −19% e −27%.
>
> O real faz parte disso: em correção, o dólar sobe 0,39% a cada 1% de queda do
> S&P 500; no mercado calmo, 0,21%.
>
> As ressalvas. Hoje o S&P 500 está a 0,9% da máxima: o regime é calmo, a correção
> não começou. E a causa importa: na semana do anúncio das tarifas americanas, em
> abril de 2025, o S&P 500 caiu 9% e o Ibovespa em dólar, menos de 2%. O beta por
> regime é âncora histórica, não previsão.
>
> Você não precisa acreditar em mim nem na GMO. Os slides 6 e 7 saíram de um código
> em Python com dado público, que roda em segundos.
>
> É o que faço toda semana em que sai carta nova: leio as cartas de 15 gestoras
> brasileiras e de Oaktree, GMO e Bridgewater, destrincho as teses e escrevo um
> exercício que testa uma delas.
>
> Comenta GESTORAS que eu mando a edição desta semana — a síntese e o código — no
> direct.
>
> E me conta: na sua conta de risco, o beta do Brasil é um número só?

## Publicado

- **23/09/2026:** https://www.instagram.com/p/DdpUMufEWmF/ — 10 slides e legenda conferidos pela Graph API
- **15/09/2026:** https://www.instagram.com/p/DdUg1OiG8My/
- Palavra-chave `GESTORAS` na legenda (mesma do fluxo do ManyChat).

⚠️ A Graph API devolveu `400 "Only photo or video can be accepted as media type."`
em 3 dos 10 slides, em posições diferentes a cada rodada — imagens idênticas entre
si (1080x1350 PNG RGB). É falha TRANSITÓRIA da Meta ao baixar a imagem, não defeito
do arquivo: a mesma URL passa segundos depois. `InstagramConnector._post` ganhou
retry por causa disso; sem ele, um hiccup em qualquer filho aborta o carrossel
inteiro deixando containers órfãos.

## Checklist antes de publicar

- [ ] 🔴 **Criar o fluxo `GESTORAS` no painel do ManyChat** — a API não cria. Sem
      ele, quem comenta não recebe nada e o lead se perde em silêncio
- [ ] Definir para onde o link da DM aponta (página de captura ou produto)
- [ ] Testar ponta a ponta comentando `GESTORAS` de uma conta que nunca interagiu
- [ ] Conferir os PNGs no celular — é de onde vem a maior parte do tráfego
- [ ] Se virar anúncio: nome de campanha/adset **sem pipe (`|`)** — a macro
      `{{campaign.name}}` entra na URL e o firewall devolve 403 de tela branca.
      Já custou R\$ 385,72 em nove dias

## Sobre os gráficos (edição de 29/09)

Os três gráficos são **dados reais**, do mesmo código do exercício que está no PDF
(`dados_do_exercicio()` reexecuta o bloco Python da edição): S&P 500, Ibovespa e
dólar do Yahoo Finance (`^GSPC`, `^BVSP`, `BRL=X`), retornos semanais (sexta),
regime pelo drawdown do S&P 500 na semana anterior. A capa aplica os dois betas
a um choque de −20% — é a conta da caixa de texto do próprio exercício.

Os números da legenda que não estão nos slides (semanas de 10/10/2008, 20/03/2020
e 04/04/2025) saíram da mesma série semanal do exercício (`ret`), conferidos em
01/10/2026.

⚠️ **O BRL=X do Yahoo tem um buraco de out/2004 a mar/2006.** O alinhamento do
exercício descarta essas semanas, então "desde 2004" tem uma lacuna de ~17 meses
(1.103 semanas na amostra). Não muda a conclusão, mas é checável.

⚠️ **O beta móvel de 26 semanas não entra na peça.** O resample semanal rotula a
semana corrente, ainda aberta, com a sexta futura, e o beta "de hoje" pula de 0,30
(última semana fechada, 25/09) para 0,09 com a semana pela metade. `regimes()` usa
só semanas fechadas; a peça mostra o drawdown, que é estável.

⚠️ O drawdown de hoje (−0,9%) e o regime mudam a cada pregão. Se o post sair dias
depois, rode `carrossel.py` de novo e confira slide 7, slide 8 e a legenda. Os
betas por regime (0,96 e 1,34) são da amostra inteira e quase não se movem.
