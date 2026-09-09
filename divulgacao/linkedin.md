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

> Toda semana, doze gestoras brasileiras publicam suas cartas. Você lê duas ou
> três — as que já acompanha, ou as que alguém comentou no grupo.
>
> O problema não é o tempo de leitura. É que o valor de ler doze cartas está
> justamente em compará-las: uma carta isolada dá a visão de uma casa, doze dão o
> mapa do que o mercado brasileiro está apostando — e de onde ele discorda de si
> mesmo.
>
> Foi para isso que montei a Síntese das Cartas das Gestoras.
>
> Toda semana você recebe:
>
> → A tese de cada casa e, mais importante, o mecanismo que a sustenta — a cadeia
> causal que faz a aposta se pagar, e a condição em que ela quebra.
>
> → As convergências e divergências: onde o consenso se forma e onde racha. Na
> última edição, três mesas olhando dados diferentes — inadimplência, recuperações
> judiciais, reestruturações de crédito — descreveram o mesmo ciclo virando.
>
> → Um exercício em Python que testa uma das teses com dado público. Se duas
> gestoras estão tomadas em inclinação de curva, o código mede quanto dessa aposta
> já está no preço. Roda em seis segundos, com dados do Tesouro Direto e do Banco
> Central. Você replica, adapta, discorda.
>
> Não é para você concordar com as gestoras. É para conseguir checar.
>
> Dynamo, IP, Alaska, Kapitalo, Adam, Legacy, Bahia, Occam, JGP, Kinea, NEO e
> Dahlia. É de graça, e chega no seu e-mail:
>
> https://analisemacro.kit.com/sintese-semanal-das-cartas-das-gestoras
>
> #mercadofinanceiro #rendafixa #python #análisededados

## Ressalvas

- **O foco é o produto, não a edição** (decisão do Vitor em 09/09). O objetivo do
  post é a captura no ConvertKit — uma copy sobre a manchete de uma edição
  envelhece no dia seguinte e não se sustenta se a composição de gestoras mudar
  (a Kinea caiu do PDF de 09/09 por rate limit na coleta).
- **Landing:** `https://analisemacro.kit.com/sintese-semanal-das-cartas-das-gestoras`
  (form `9899518`, criado em 09/09). Verificado: HTTP 200. Existe também o
  `9794131` — `/sintese-das-cartas-das-gestoras`, de 12/08 — que serve a MESMA
  página; usar o novo e arquivar o antigo, para não dividir a métrica.
- ⚠️ A landing precisa entregar a **URL fixa do PDF**
  (`storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf`) na sequência
  de boas-vindas. Como o pipeline sobrescreve esse arquivo toda terça, quem se
  inscrever em qualquer semana recebe sempre a edição corrente — sem trocar nada
  no painel.
- O exemplo do ciclo de crédito é real, da edição de 09/09. Os +48 bps do gráfico
  foram medidos pelo código do exercício, com dado do Tesouro Direto de 08/09/2026.
- A publicação é manual: não há automação de LinkedIn na casa, e o canal não
  recebe verba de tráfego hoje.
