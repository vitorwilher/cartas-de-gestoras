# Fluxo ManyChat — palavra-chave `GESTORAS`

**Status: fluxo criado no painel (Vitor, 09/09). Texto da DM revisto em 07/10 — falta colar.**

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

🔴 **Texto novo de 07/10/2026 — colar no painel** (a API do ManyChat não edita
fluxo). A síntese completa virou assinatura de R$ 97/mês; a DM antiga dizia "É
gratuito" e prometia a edição completa por e-mail, o que deixou de ser verdade.

> Oi! Vi que você comentou GESTORAS.
>
> Aqui está o link:
>
> https://analisemacro.com.br/conteudo/cartas-das-gestoras/?utm_source=manychat&utm_medium=dm&utm_campaign=cartas-de-gestoras
>
> A edição completa, com a tese de cada casa, onde elas divergem e o código do
> exercício, é para assinantes. Na mesma página, se preferir, você se cadastra
> para receber de graça o resumo de cada edição por e-mail.
>
> Acompanho 15 gestoras brasileiras e Oaktree, GMO e Bridgewater. Sai edição
> sempre que alguma publica carta nova.

<details><summary>DM anterior (23/09 a 07/10), só para histórico</summary>

> Oi! Vi que você comentou GESTORAS no carrossel. A edição desta semana — a
> síntese das cartas e o código do exercício — chega no seu e-mail assim que você
> se cadastrar aqui: [link]. É gratuito. [...]

</details>

⚠️ **Desde 23/09 a DM leva à LANDING, não ao PDF** (decisão do Vitor): o objetivo é
o cadastro, que põe o lead na tag e no envio de cada edição. O PDF chega pelo
e-mail de boas-vindas da sequência 2888305, na hora. A UTM `manychat` é a que o
`funil_seguidores.py` do ROI usa para separar DM de link da bio.

⚠️ **Texto revisto em 23/09/2026, precisa ser colado no painel** (a API do ManyChat
não edita fluxo). Mudou: "12 maiores" virou "15 gestoras brasileiras" (a lista
original cobria 4 das 50 maiores independentes), entraram as três de fora, "toda
semana" passou a depender de haver carta nova, e saiu o parágrafo que citava o
carrossel do Copom de 09/09 — a palavra-chave GESTORAS serve a 30 carrosséis do
calendário, e a DM fixa não pode falar de um só.

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

**Essa URL nunca muda.** O pipeline sobrescreve o arquivo a cada edição, depois de
gerá-la — o passo "Publicar o PDF no GCS" no workflow. Assim o fluxo do
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
