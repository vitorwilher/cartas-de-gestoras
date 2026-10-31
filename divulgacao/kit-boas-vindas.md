# E-mail de boas-vindas — sequência 2888305 (Kit)

**Status em 31/10/2026: o boas-vindas é o 10516834**, "Sua edição completa das cartas
das gestoras", na posição 0 — entrega o link da **edição de amostra de 13/10** (a
mesma da página de obrigado, mídia 80537), apresenta o resumo semanal e cita a
assinatura. Criado pela API (POST, corpo conferido na releitura), publicado e movido
para a frente; o 10409446 (abaixo, só "resumo") ficou despublicado na posição 1, e o
10288509 de setembro na posição 2.

⚠️ O 10288509 aparece com **corpo vazio** (3 chars) em 31/10. O PUT de posição
preservou o corpo do 10409446, e o 10288509 já vinha com `has_unpublished_changes`,
então provavelmente estava assim antes — mas o tamanho não foi medido antes da
mudança. O texto original não está no repositório.

**Contatos internos na tag do projeto** (descontar nas métricas de leads):
`analisemacro.cloud+cartas-terca@gmail.com` (id 4366074132, **ativo** — o Vitor acompanha
as edições de terça por ele) e `+teste-cartas-3110` (id 4366050581, **cancelado**).
⚠️ O Kit **não reativa pela API** quem se descadastrou: o upsert da v4 e o
`tags/<id>/subscribe` da v3 respondem 200 (a v3 até devolve `active`) e o estado segue
`cancelled` em todas as releituras. Quem saiu só volta pelo painel ou por iniciativa
própria; por isso o acompanhamento ganhou um alias novo, inscrito pela landing.

**Ordem da sequência, sempre:** publicado na posição 0, rascunhos depois. Ver abaixo.

**Quem ficou parado em "Step 0" destrava sozinho** quando o e-mail publicado passa
para a posição 0 — mas não na hora. Os 4 leads de 14/10 a 20/10 receberam o
boas-vindas novo em 31/10 sem intervenção (conferido no painel, contato carlos.cmneto).
Ao conferir logo depois da troca, o contato de teste ainda parecia parado, e eu tirei
ele da sequência no painel e recoloquei pela API — **passo desnecessário**: era atraso.
Se precisar mesmo: o painel remove (a API dá 404 no DELETE) e a API recoloca
(`POST /v4/sequences/2888305/subscribers/<id>`); recolocar quem ainda está na
sequência é no-op (200 com a data antiga).

⚠️ O contador "Emails sent" do assinante **atrasa**: o contato de acompanhamento mostrava 0 com "Step 1 of 1" enquanto o e-mail já estava na caixa. O passo da sequência é o sinal confiável; o contador, não.

---

## Histórico: o e-mail de 08/10 (10409446)

**Status: NO AR desde 08/10/2026, pela API.** E-mail novo **10409446** publicado;
o antigo, **10288509** (com o link do PDF no GCS), ficou **despublicado** — guardado
no Kit, não apagado.

⚠️ **Editar não funciona, criar sim (testado em 08/10):**
`PUT /v4/sequences/2888305/emails/<id>` responde 200, grava o assunto e o
`published`, mas **descarta o corpo em silêncio** (até `"content": 123` volta 200).
`POST /v4/sequences/2888305/emails` com `content` GRAVA o corpo. O caminho foi:
criar o novo despublicado → conferir o corpo na releitura → publicar o novo →
despublicar o antigo (nessa ordem, para a sequência nunca ficar sem boas-vindas).

🔴 **Rascunho na frente do publicado TRAVA a sequência inteira, sem erro (achado em
31/10/2026).** O 10288509 despublicado ficou na posição 0 e o novo na 1. Todo lead de
08/10 a 31/10 (4 reais + 1 teste) parou em **"Step 0 of 1"** com 0 e-mails enviados —
o "Immediately" do publicado nunca chegou a valer. O painel não acusa nada; só se vê
abrindo o assinante. Corrigido pela API v4 em duas etapas (a posição precisa estar
livre: `422 position 0 is already taken`): `PUT .../emails/10288509 {"position": 2}`
e depois `PUT .../emails/10409446 {"position": 0}`. O PUT de posição **preserva** o
corpo (conferido na releitura). **Regra:** o e-mail publicado é sempre o da posição 0;
rascunho guardado vai para o fim.

A sequência está com `hold: false`: quem já tinha recebido o e-mail antigo saiu dela
e **não** recebe o novo. Só os cadastros a partir de 08/10.

🔴 **Por que trocar:** o e-mail atual entrega o link do PDF da edição em
`storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf`. Desde 07/10 a
síntese completa é paga (R$ 97/mês, produto 73335), e esse PDF vai sair do GCS
público — o link passaria a dar erro para todo lead novo.

O lead que se cadastra pela landing agora pediu **o resumo gratuito** (é o que o
formulário oferece). O e-mail entrega isso e convida para a assinatura, sem
pressão: ele acabou de chegar.

Onde: Kit → Sequences → 2888305 → primeiro e-mail.

---

**Assunto:** Você vai receber o resumo das cartas das gestoras

> Olá, {{ subscriber.first_name }}.
>
> Obrigado pelo cadastro. A partir de agora, toda semana em que alguma das gestoras
> que acompanho publicar carta nova, você recebe aqui o resumo da edição: as teses
> da semana e onde as casas divergem, em poucos parágrafos.
>
> São 15 gestoras brasileiras (Dynamo, IP, Alaska, Kapitalo, Adam, Legacy, Bahia,
> Occam, JGP, Kinea, NEO, Dahlia, Genoa, Sparta e Opportunity) e três de fora:
> Oaktree, GMO e Bridgewater. Na semana em que nenhuma publica, não há edição.
>
> A edição completa é para assinantes: a tese de cada casa destrinchada pelo
> mecanismo que a sustenta, as convergências e divergências com o patrimônio de
> cada lado, e um exercício em Python que testa uma das teses com dado público.
> Custa R$ 97 por mês, e todas as edições anteriores ficam na sua área do aluno.
>
> [Conhecer a assinatura](https://aluno.analisemacro.com.br/carrinho/?add-to-cart=73335)
>
> Vítor Wilher — Análise Macro

---

⚠️ Conferir depois de colar: mandar o e-mail de teste do próprio painel para um
endereço seu e clicar no botão — o carrinho deve mostrar R$ 97,00 / mês.
