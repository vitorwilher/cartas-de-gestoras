# Carrossel de Instagram — Cartas de Gestoras

**Status: PNGs da edição de 23/09 gerados, NÃO publicados.**

- **Arquivos:** `divulgacao/carrossel/slide-01.png` … `slide-10.png` (1080×1350)
- **Gerador:** `python divulgacao/carrossel.py` (reexecuta o exercício da edição)
- **Publicar:** `python divulgacao/publicar_instagram.py` (dry-run por padrão)
- **Palavra-chave da DM:** `GESTORAS` — ver `manychat-gestoras.md`

🔴 **Antes de publicar, colar no painel do ManyChat a DM revista em 23/09.** A que
está no ar ainda diz "12 maiores gestoras" e cita o carrossel do Copom de 09/09 —
quem comentar GESTORAS neste post receberia um texto sobre outro assunto.

## Por que este ângulo (edição de 23/09)

**"O seguro do investidor brasileiro mudou de sinal."** O exercício da edição mede
se o Treasury longo americano, convertido a reais, ainda protege a bolsa brasileira.
A resposta tem um contraste que se lê em dois segundos: −0,52 em março de 2020
(protegia) contra +0,17 hoje (anda junto). E ele nasce das cartas: a Genoa vê o Fed
podendo subir juros, e Marks vê o juro longo americano alto por fundamento.

Um ângulo só. Ficaram de fora a crítica de Marks às recompras do Tesouro, o
private equity da GMO e a regulação de IA da Bridgewater.

## Os 10 slides

| # | Tipo | Conteúdo |
|---|---|---|
| 1 | capa + gráfico | "O seguro mais clássico do investidor brasileiro mudou de sinal" — duas barras: mar/2020 (−0,52) e hoje (+0,17) |
| 2 | lista ✓ | No que as cartas concordam: Genoa (Fed pode subir) e Marks (juro longo por fundamento) |
| 3 | lista | Onde isso pesa: a lógica do seguro e por que ela falha com juro americano subindo |
| 4 | definição | Correlação negativa / perto de zero / positiva — **antes** dos gráficos de série |
| 5 | lista | Por que custa dinheiro |
| 6 | capa + gráfico | A série da correlação desde 2012, com zero, mediana e o ponto de hoje |
| 7 | capa + gráfico | O risco que a carteira 50/50 ainda apaga: 23% hoje, 30% na mediana |
| 8 | lista | O que o dado diz — inclui a ressalva "janela de 6 meses: retrato, não previsão" |
| 9 | lista numerada | O caminho que eu fiz |
| 10 | CTA | GESTORAS + "você ainda usa Treasury como seguro?" |

## Legenda do post

> Em março de 2020, quem tinha Treasury longo americano sem hedge de câmbio estava
> protegido: a bolsa brasileira caía, e o Treasury em reais subia. A correlação
> entre os dois chegou a −0,52.
>
> Hoje ela está em +0,17 — acima de 89% dos dias desde 2012. Desde 2024, ficou
> positiva em 87% dos dias. O seguro passou a andar junto com o risco que deveria
> cobrir.
>
> Duas cartas desta semana ajudam a entender por quê. A Genoa vê risco de o Fed
> subir juros ainda em 2026. Howard Marks, da Oaktree, escreve que o juro longo
> americano está alto por fundamento: inflação, déficit e demanda por capital. Num
> mundo assim, o Treasury pode cair junto com a bolsa.
>
> A ressalva: uma carteira 50/50 ainda apaga 23% do risco — o dólar ajuda. Mas a
> mediana histórica é 30%. E a janela é de seis meses: é retrato, não previsão.
>
> Você não precisa acreditar em mim nem nas gestoras. Os slides 6 e 7 saíram de um
> código em Python com dado público, que roda em segundos.
>
> É o que faço toda semana em que sai carta nova: leio as cartas de 15 gestoras
> brasileiras e, agora, de Oaktree, GMO e Bridgewater, destrincho as teses e escrevo
> um exercício que testa uma delas.
>
> Comenta GESTORAS que eu mando a edição desta semana — a síntese e o código — no
> direct.
>
> E me conta: você ainda usa Treasury como seguro?

## Publicado

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

## Sobre os gráficos (edição de 23/09)

Os três gráficos são **dados reais**, do mesmo código do exercício que está no PDF:
Ibovespa, ETF TLT e dólar do Yahoo Finance, retornos diários desde 2012, correlação
móvel de 126 dias úteis. A capa mostra só dois pontos da mesma série (o mínimo, em
17/03/2020, e hoje) — nada ali é ilustrativo.

⚠️ É uma correlação de **janela móvel**: os números mudam a cada pregão. Se o post
sair dias depois de 23/09, rode `carrossel.py` de novo e confira a legenda contra
os slides.
