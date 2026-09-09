# Fluxo ManyChat — palavra-chave `GESTORAS`

**Status: RASCUNHO. O fluxo NÃO existe ainda.**

🔴 **Bloqueio conhecido, verificado no `../ROI_Diagnostico/CLAUDE.md`:** a API do
ManyChat **não cria fluxo** (`createFlow` → 404) nem permite conferir qual
palavra-chave um fluxo escuta (`getFlow` → 404). O fluxo é trabalho de painel.

⚠️ **Publicar o carrossel ANTES de o fluxo existir perde lead em silêncio** — quem
comenta `GESTORAS` não recebe nada e não há como saber depois. O único teste que
prova ponta a ponta é comentar a palavra-chave de uma conta que nunca interagiu.

## O que criar no painel

| Campo | Valor |
|---|---|
| Gatilho | `feed_comment_trigger` no post do carrossel |
| Palavra-chave | `GESTORAS` |
| Resposta pública | uma linha, variada (o ManyChat responde no comentário) |
| Ação | DM com o link |

## Resposta pública no comentário

> Mandei no seu direct 👀

## A DM

> Oi! Vi que você comentou GESTORAS no carrossel.
>
> Toda semana eu leio as cartas das 12 maiores gestoras do Brasil — Dynamo, IP,
> Alaska, Kapitalo, Adam, Legacy, Bahia, Occam, JGP, Kinea, NEO e Dahlia — e faço
> duas coisas com elas:
>
> 1. Destrincho a tese de cada uma: o mecanismo que a sustenta e a condição em que
> ela quebra.
> 2. Escrevo um exercício em Python que testa uma dessas teses com dado público —
> o código roda em segundos e você replica.
>
> A desta semana está aqui: https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf
>
> Nela tem o racha do Copom que mostrei no carrossel, com a passagem exata de cada
> carta, e o exercício que mede quanto do steepener a curva já pagou — o mesmo
> gráfico dos slides 6 e 7, com o código inteiro.

## O link e a UTM

⚠️ **`utm_source=manychat` é o valor exato** que o `funil_seguidores.py` do ROI
procura para separar quem veio da DM de quem veio do link da bio. Marcar como
`instagram` contaria clique de bio como conversão de DM.

```
?utm_source=manychat&utm_medium=dm&utm_campaign=cartas-de-gestoras
```

🔑 Todo link que o ManyChat entrega numa DM carrega `mcp_token=` na URL — é assim
que o `monitors/manychat_entrega.py` mede a entrega.

## O link: URL fixa, conteúdo que muda sozinho

```
https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf
```

**Essa URL nunca muda.** O pipeline sobrescreve o arquivo toda terça, depois de
gerar a edição — o passo "Publicar o PDF no GCS" no workflow. Assim o fluxo do
ManyChat é criado UMA vez e continua entregando o material da semana corrente,
sem ninguém trocar link em painel.

Cada edição também fica guardada num endereço datado
(`.../cartas/2026-09-09.pdf`), para quem recebeu o link numa semana conseguir
reabrir aquela edição depois.

Verificado em 2026-09-09: as duas URLs respondem **HTTP 200 / application/pdf**.

⚠️ Se a publicação falhar numa semana, o passo é `continue-on-error` — a edição
não é perdida (o PDF já foi gerado e enviado por WhatsApp), mas **o link público
fica com a versão anterior**. Conferir a data na capa do PDF ao checar.

### A captura de e-mail

A DM leva para a landing do ConvertKit, que entrega essa URL depois do
formulário. A landing aponta para o link fixo, então ela também é criada uma vez
só — a API do Kit não cria formulário (404 em v3 e v4), é trabalho de painel.
