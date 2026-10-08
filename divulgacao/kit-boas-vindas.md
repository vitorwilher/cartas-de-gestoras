# E-mail de boas-vindas — sequência 2888305 (Kit)

**Status: NO AR desde 08/10/2026, pela API.** E-mail novo **10409446** publicado;
o antigo, **10288509** (com o link do PDF no GCS), ficou **despublicado** — guardado
no Kit, não apagado.

⚠️ **Editar não funciona, criar sim (testado em 08/10):**
`PUT /v4/sequences/2888305/emails/<id>` responde 200, grava o assunto e o
`published`, mas **descarta o corpo em silêncio** (até `"content": 123` volta 200).
`POST /v4/sequences/2888305/emails` com `content` GRAVA o corpo. O caminho foi:
criar o novo despublicado → conferir o corpo na releitura → publicar o novo →
despublicar o antigo (nessa ordem, para a sequência nunca ficar sem boas-vindas).

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
