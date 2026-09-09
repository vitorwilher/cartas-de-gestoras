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
