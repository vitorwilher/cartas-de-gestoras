# Plano de teste — Fase 1 (ouvir)

**Status: AGUARDANDO APROVAÇÃO. Nada foi executado.**

O objetivo desta fase é um só: **ver o JSON de uma conversa chegar no nosso
endpoint**. Não responder, não gravar, não alterar nada.

---

## Por que é seguro

| | |
|---|---|
| O webhook da Meta | **não é tocado** — continua do Kommo |
| O número +55 21 97116-7250 | **não é tocado** |
| A rotina da Raiane | **não muda** |
| O que fazemos | **adicionar** um segundo webhook do Kommo, que só escuta |

O Kommo já dispara para dois destinos hoje (`woocom.kommo.com` e o Cloud Run
`amblack-webhook`). Adicionar um terceiro é o padrão da casa, não uma novidade.

**Reversível em uma chamada:** `DELETE /api/v4/webhooks` com a URL. Se algo
estranhar, sai em segundos e tudo volta ao que era.

---

## O que vou fazer, na ordem

### 1. Salvar o estado atual
`GET /api/v4/webhooks` e guardar a resposta num arquivo. É o retrato para
comparar depois e para restaurar, se preciso.

### 2. Subir o endpoint
Um Cloudflare Worker (`wa-escuta.analisemacro.workers.dev`) que faz três coisas:

- responde `200 OK` a qualquer POST (o Kommo exige, senão desativa o webhook)
- guarda o JSON recebido num KV, com a hora
- expõe `GET /ultimos` para eu ler o que chegou

Sem credencial nenhuma. Ele não fala com a Meta, não fala com o Kommo, não envia
mensagem. **Só escuta.**

### 3. Cadastrar o webhook
Uma única chamada:
```
POST /api/v4/webhooks
{"destination": "https://wa-escuta.analisemacro.workers.dev/kommo",
 "settings": ["add_talk"]}
```

### 4. Você manda um "oi"
De um número seu que **não** seja cliente, para o WhatsApp da Análise Macro.

### 5. Eu leio o que chegou
`GET /ultimos` no Worker. Uma chamada, ao Worker — **não ao Kommo**.

### 6. Conferir que nada quebrou
Você confirma no Kommo que a mensagem apareceu normalmente no board, como
sempre. Esse é o teste que importa.

### 7. Remover o webhook
`DELETE /api/v4/webhooks`. Fim da fase 1.

---

## Orçamento de chamadas ao Kommo

⚠️ **O IP foi bloqueado em 08/09 por excesso de requisições.**

Este plano usa **exatamente 3 chamadas** ao Kommo, espaçadas:

| # | Chamada | Quando |
|---|---|---|
| 1 | `GET /webhooks` (estado atual) | início |
| 2 | `POST /webhooks` (cadastrar) | após o Worker estar no ar |
| 3 | `DELETE /webhooks` (remover) | ao fim do teste |

Nenhuma sondagem, nenhum laço. A leitura do resultado é feita no Worker.

---

## O que decide o sucesso

**Critério:** o JSON de `add_talk` aparece no Worker **e** a mensagem chega
normalmente no Kommo.

Se o JSON não vier, aprendemos que `add_talk` não dispara para mensagem de
WhatsApp (só para conversa criada por outro caminho) — e aí o plano muda, sem
nenhum prejuízo.

---

## O que NÃO acontece nesta fase

- Nenhuma mensagem é enviada a ninguém
- Nenhum lead é criado ou alterado
- Nenhuma configuração da Meta é tocada
- Nenhum dado de cliente sai do Kommo

---

## Para aprovar

Preciso de duas coisas suas:

1. **O ok para executar** os passos 1 a 3 e 7
2. **Um número de teste** — o seu, ou outro que não seja de cliente

O passo 4 (mandar o "oi") é seu. Os demais são meus.
