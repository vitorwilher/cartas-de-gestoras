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
> A desta semana está aqui: [LINK]
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

## Decisão pendente: para onde o link aponta

O produto ainda não está publicado no Woo. Duas opções, e é decisão do Vitor:

1. **Página de captura** com a síntese desta semana em troca do e-mail — alimenta o
   Boletim e mede interesse antes de existir produto. É o que o teste pede.
2. **Página do produto** quando existir — mas aí o carrossel deixa de ser teste e
   vira lançamento, e a copy do slide 8 muda.

⚠️ Enquanto o destino não estiver definido e testado, **o `[LINK]` acima é
placeholder** e o fluxo não deve ir ao ar.
