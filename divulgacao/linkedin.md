# LinkedIn — arte e copy

**Status: arte gerada, NÃO publicada.**

- **Arte:** `divulgacao/linkedin/linkedin-01.png` (1200×627, proporção do feed)
- **Gerador:** `python divulgacao/linkedin.py`
- Os números vêm do mesmo `dados_do_exercicio()` do carrossel — o que aparece
  aqui, no Instagram e no PDF é sempre a mesma medida.

## Por que não é o carrossel do Instagram

Outro público e outro comportamento. No LinkedIn não há "arraste para ver" nem
comentário com palavra-chave: o post é lido inteiro na timeline, e o texto carrega
mais peso que a imagem. Por isso é **uma peça horizontal** — gráfico de um lado,
argumento do outro — e a copy é mais longa e mais técnica.

⚠️ **Sem CTA de comentário.** O fluxo `GESTORAS` do ManyChat é do Instagram; aqui o
link vai direto no texto.

## Copy do post

> Três gestoras publicaram carta em agosto olhando dados diferentes — e as três
> descreveram o mesmo ciclo de crédito virando.
>
> A Bahia registra inadimplência em alta. A Legacy vê "aumento da frequência de
> casos de empresas em dificuldades financeiras" e trata isso como risco de ciclo:
> demissões, crédito, consumo. A Occam, na carta de crédito, conta o salto nas
> reestruturações e responde com duration curta e subordinação.
>
> Três mesas, três recortes, o mesmo sinal. É o tipo de coisa que só aparece
> lendo as cartas lado a lado.
>
> No resto, elas divergem — e é aí que fica interessante.
>
> No Brasil, Bahia e Occam carregam o mesmo trade: steepener na curva nominal
> (aplicado no juro curto, tomado no longo), com a mesma lógica — o Copom corta e
> ancora a ponta curta, enquanto a longa importa prêmio global e carrega risco
> fiscal e eleitoral.
>
> A pergunta que importa é quanto dessa aposta já está no preço.
>
> Dá para medir, com dado público. A curva prefixada do Tesouro Direto é aberta:
> interpolando os vértices de 2 e 7 anos, a inclinação hoje está em +48
> pontos-base — percentil 45 da distribuição desde 2010. Nem esticada, nem
> comprimida. O degrau está na média histórica, o que significa que a aposta não
> está barata na entrada.
>
> Um dado que conversa com o histórico recente: no Bahia Mutá, as estratégias de
> juros renderam -3,7% em 12 meses.
>
> É isso que eu faço toda semana: leio as cartas das 12 maiores gestoras do
> Brasil, destrincho o mecanismo por trás de cada tese e escrevo um exercício em
> Python que testa uma delas. O código deste roda em seis segundos, com dados do
> Tesouro Direto e do Banco Central.
>
> A edição desta semana — síntese e código — está aqui:
> https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf
>
> #mercadofinanceiro #rendafixa #python #análisededados

## Ressalvas

- **A copy fala de três gestoras, não quatro.** Esta edição cobre Bahia, Occam,
  Legacy e Dynamo — a **Kinea caiu com HTTP 403** na coleta (rate limit por eu ter
  rodado o pipeline várias vezes no mesmo dia). A versão anterior desta copy
  citava a Kinea e a divergência do Copom: quem abrisse o PDF não acharia nem uma
  coisa nem outra. Conferir sempre a copy contra o documento da edição.
- A Dynamo entra no PDF mas fica fora da copy: a Carta 128 é de abril e não trata
  de conjuntura.
- Os números saíram das fontes: -3,7% é da carta da Bahia; +48 bps e o percentil
  45 foram medidos pelo código do exercício, com dado do Tesouro Direto de
  08/09/2026.
- O link é a **URL fixa** — o pipeline sobrescreve o PDF toda terça, então o post
  continua entregando a edição corrente mesmo semanas depois.
- A publicação é manual: não há automação de LinkedIn na casa, e o canal não
  recebe verba de tráfego hoje.
