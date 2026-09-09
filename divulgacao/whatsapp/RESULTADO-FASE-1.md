# Fase 1 — resultado: FUNCIONOU

Executada em 2026-09-09. O Alan mandou uma mensagem real para o WhatsApp da
Análise Macro e o evento chegou ao nosso endpoint.

## O que ficou provado

**O Kommo avisa o nosso código quando chega mensagem de WhatsApp** — sem tocar no
webhook da Meta, no número ou na rotina de atendimento.

Evento recebido às 21:44:56, em `application/x-www-form-urlencoded`:

| Campo | Exemplo | Para que serve |
|---|---|---|
| `talk[add][0][origin]` | **`waba`** | confirma que veio do WhatsApp |
| `talk[add][0][contact_id]` | 28771643 | quem escreveu |
| `talk[add][0][entity_id]` | 23711835 | o lead criado no Kommo |
| `talk[add][0][chat_id]` | uuid | a conversa |
| `talk[add][0][talk_id]` | 106564 | a talk |
| `talk[add][0][is_read]` | 0 | ninguém leu ainda |
| `account[subdomain]` | analisemacro | a conta |

**O contato é consultável:** `GET /api/v4/contacts/{contact_id}` devolveu nome e
telefone (`+55 13 99114-5811`). É o que liga a conversa ao lead que veio da
landing — a chave da automação.

Payload completo (anonimizado): `evento-add-talk-exemplo.json`.

## Confirmado com DOIS remetentes

Não foi acaso: dois eventos independentes, com 3 minutos de diferença, cada um
com seu próprio contato, lead e talk.

| # | Hora | contact_id | entity_id | talk_id | Quem |
|---|---|---|---|---|---|
| 1 | 21:44:56 | 28771643 | 23711835 | 106564 | Alan |
| 2 | 21:47:57 | 28771685 | 23711881 | 106565 | Luiz |

Os dois com `origin=waba` e `is_read=0`. Em ambos, `GET /contacts/{id}` devolveu
nome e telefone corretos.

**O que isso prova:** o `talk_id` é sequencial e cada conversa gera um evento
próprio — dá para tratar cada lead individualmente, que é o que a automação
precisa.

## Achados que custariam tempo depois

⚠️ **O Kommo EXIGE barra no final da URL do webhook.** Sem ela, recusa com
`"Invalid URL"` — mensagem que não diz nada sobre o problema real. Perdi uma
tentativa nisso.

⚠️ **`add_talk` NÃO dispara ao criar lead pela API.** Testei: criar lead devolve
200 e nenhum evento chega. Ele é mesmo sobre conversa de chat, e conversa de chat
só nasce de mensagem real. Não dá para simular.

⚠️ **`DELETE /api/v4/leads` devolve 405.** Não dá para apagar lead pela API — só
renomear e apagar no painel.

## Estado atual

| | |
|---|---|
| Webhook `add_talk` | id `47472088`, **ativo** |
| Worker | `wa-escuta.analisemacro.workers.dev` — só escuta |
| Webhooks originais | intactos (baseline em `baseline_webhooks_kommo.json`) |
| Chamadas ao Kommo | 6 no total, espaçadas |

## Pendência para o painel

🔴 **Apagar o lead "ZZ APAGAR — teste de webhook Claude 09/09"** (id 23711759).
Criei para testar se o evento disparava por criação de lead (não dispara) e a API
não permite remover.

## Próximo passo — fase 2

Guardar o evento com o telefone resolvido, para cruzar com o lead da landing.
Ainda sem enviar nada a ninguém.


---

# Fase 2 — resultado: FUNCIONOU

Executada em 2026-09-09, logo após a fase 1.

## O que o Worker faz agora

Ao receber o evento, ele **resolve quem escreveu e de onde veio**:

1. `GET /contacts/{contact_id}` no Kommo → nome e telefone (com cache de 24h,
   para não repetir consulta do mesmo contato)
2. Procura esse telefone na tag Mercado Financeiro do ConvertKit
3. Guarda tudo no KV — **sem enviar nada a ninguém**

## Testado nos dois cenários

| Cenário | Resultado |
|---|---|
| Telefone **fora** da base do Kit | `veio_da_landing: false`, com `estado: nao_encontrado` |
| Mesmo telefone **dentro** da base | `veio_da_landing: true`, achado na página 11 |

O segundo teste foi feito criando um assinante com o telefone do Alan, e ele foi
removido em seguida.

## Dois achados que custariam horas

⚠️ **O Kit IGNORA `per_page` acima de 50.** Pedir 100 devolve 50, e `total_pages`
é calculado sobre 50. Meu código parava "quando vinha menos que o pedido" — o que
encerrava a busca na primeira página, **sempre**. O lead estava na página 11 de 11
e nunca era encontrado. Agora a paginação usa `total_pages`.

⚠️ **A API do Kit não busca por campo custom.** Não há como perguntar "quem tem
este telefone?" — só listar e varrer. Por isso a busca é na TAG do projeto (532
pessoas) e não na base inteira (5.118).

## A melhoria que vale fazer depois

Varrer 11 páginas a cada mensagem funciona, mas é frágil: cresce com a lista e
depende da API do Kit estar no ar.

**O certo é o formulário gravar o telefone no nosso KV no momento do cadastro.**
Aí a consulta é instantânea, exata e não depende de ninguém. Exige um ajuste na
ponte PHP — vale quando a fase 3 começar.

## Estado

| | |
|---|---|
| Worker | `wa-escuta.analisemacro.workers.dev` — ouve, resolve e registra |
| Segredos | KOMMO_TOKEN, KOMMO_SUBDOMAIN, CONVERTKIT_SECRET (no Worker) |
| Envio de mensagem | **nenhum** — continua só observando |
