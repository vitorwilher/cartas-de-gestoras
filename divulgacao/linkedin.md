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

> Quatro gestoras publicaram carta em agosto e concordam em quase tudo: núcleos de
> serviços pressionados, expectativas com viés de alta, atividade desacelerando,
> eleição empatada.
>
> Aí chega o Copom e elas se separam.
>
> Bahia, Occam e Legacy leem que o ciclo de cortes segue. A Kinea projeta pausa —
> "para preservar margem de manobra até que haja maior clareza sobre o orçamento".
>
> A divergência não está no diagnóstico de inflação. Está na função de reação
> atribuída ao Banco Central: para Legacy e Occam, ele reage aos dados de
> atividade que sinalizou acompanhar; para a Kinea, à incerteza fiscal
> pós-eleitoral.
>
> E isso tem consequência de carteira. Bahia e Occam carregam o mesmo trade —
> steepener doméstico, aplicado na ponta curta e tomado na longa. A pausa que a
> Kinea projeta é exatamente o cenário em que a perna curta desse trade perde.
>
> A pergunta que importa, então, é quanto dessa aposta já está no preço.
>
> Dá para medir. A curva prefixada do Tesouro Direto é pública: interpolando os
> vértices de 2 e 7 anos, a inclinação hoje está em +48 pontos-base — percentil 45
> da distribuição desde 2010. Nem esticada, nem comprimida. O degrau está na média
> histórica, o que significa que a aposta não está barata na entrada.
>
> É um dado que reforça o histórico recente: no Bahia Mutá, as estratégias de
> juros renderam -3,7% em 12 meses; no Occam Retorno Absoluto, o Juros Local
> acumula -1,99% no ano.
>
> Toda semana eu leio as cartas das 12 maiores gestoras do Brasil, destrincho as
> teses e escrevo um exercício em Python que testa uma delas com dado público. O
> código deste roda em seis segundos.
>
> A edição desta semana está aqui: [LINK]
>
> #mercadofinanceiro #rendafixa #python #análisededados

## Ressalvas

- Os números de retorno (-3,7% e -1,99%) saíram das cartas. A inclinação de
  +48 bps foi medida pelo código do exercício, com dado do Tesouro Direto de
  08/09/2026.
- ⚠️ **O `[LINK]` precisa ser substituído** pela URL fixa do PDF
  (`https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf`) ou
  pela landing do ConvertKit, se a captura de e-mail valer também aqui — decisão
  do Vitor.
- A publicação é manual: não há automação de LinkedIn na casa, e o CLAUDE.md do
  ROI registra que o canal **não recebe verba de tráfego** hoje.
