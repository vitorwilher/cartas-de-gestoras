# Landing de captura — fluxo de dois passos

**Status: as duas páginas estão PUBLICADAS, com layout Elementor.**

⚠️ **A página de captura foi recriada (78368 → 78376).** Eu havia gravado uma sonda
"TESTE DE ESCRITA" na 78368 ao verificar se o `_elementor_data` aceitava escrita,
e o WordPress passou a servir aquela versão mesmo depois de eu regravar o layout
— o conteúdo ficou preso nas revisões do post. Trocar o slug, republicar e limpar
o meta não resolveram. A saída foi criar a página do zero, sem histórico, e apagar
a antiga em definitivo (para liberar o slug).

**Lição:** nunca gravar dado de teste num post real. Testar em post descartável.

| Página | id | Slug |
|---|---|---|
| Captura | `78391` | `/conteudo/cartas-das-gestoras/` — **no ar** |
| Obrigado | `78388` | `/conteudo/cartas-das-gestoras-obrigado/` — **no ar** |

Editar: `analisemacro.com.br/wp-admin/post.php?post=<id>&action=edit`

## O fluxo (desenho do Vitor, 09/09)

```
Landing 1: nome + e-mail + telefone
        ↓  (ponte PHP)
   ConvertKit: sequência 2888305 + tag Mercado Financeiro
        ↓
Página de obrigado:
   • botão que baixa o PDF na hora
   • botão "Mandar Oi no WhatsApp"  ← o LEAD inicia a conversa
        ↓
   janela de 24h aberta → conversa livre com o lead
```

### Por que o "Oi" é o lead quem manda

**A Meta não permite enviar mensagem para quem nunca conversou com o número.**
Fora da janela de 24h só se envia template aprovado *para aquele uso* — e usar o
template UTILITY de entrega do PDF para captação é reclassificação de uso: a Meta
**descarta em silêncio** (a API responde `accepted`) e ainda derruba a qualidade
do número de produção, o mesmo que entrega o resto.

Pedindo o "Oi" ao lead, é ele quem abre a janela. Sem template de captação, sem
risco para o número, e com 24h de conversa livre. É a solução certa.

## A ponte PHP

`captura_cartas_para_convertkit.php` — Code Snippets → Add New.

⚠️ **Escopo `global`, não `front-end`.** O submit do Elementor vai por
`admin-ajax.php`, que "front-end" não cobre: a ponte fica ativa, sem erro de
sintaxe, e não executa. Foi o que mais custou tempo no conserto de 15/08 — se o
dado parar de chegar, confira o ESCOPO antes do código.

Substituir `<<<API_SECRET_DO_CONVERTKIT>>>` pelo API Secret do Kit.

**Por que a ponte existe:** a ação "ConvertKit" do Elementor Pro escreve apenas
`email` e `first_name` — não escreve campo, tag nem sequência a partir do
formulário. Verificado no payload real e documentado no ROI (3 plugins testados
em 02-03/09/2026, todos iguais).

**O que ela faz**, em duas chamadas:
1. `/v3/sequences/2888305/subscribe` — inscreve na **mesma sequência** que a
   landing nativa do Kit dispara, gravando `first_name`, `phone` e `whatsapp`.
   Assim as duas portas de entrada entregam a mesma régua de e-mail.
2. `/v3/tags/22406993/subscribe` — a tag Mercado Financeiro, que segmenta broadcast.

**Testado de verdade em 09/09/2026:** a chamada à sequência devolveu HTTP 200,
estado `active`, com `phone` e `whatsapp` gravados. O assinante de teste foi removido.

## Convive com o que já está no ar?

Sim. Três snippets estão ativos em produção (conferidos na API do Code Snippets
em 09/09/2026), todos do **Boletim AM**:

| id | Escopo | O que faz |
|---|---|---|
| 5 | `front-end` | copia a UTM da URL para os campos do Elementor |
| 8 | `global` | grava a UTM no assinante do Kit (prioridade 20) |
| 10 | `global` | aplica as tags de categoria (prioridade 30) |

**Nenhum deles serve para nós:** o id 8 abre com
`if ( 'boletimam' !== $form_id && 'boletimam' !== $form_name ) return;` — só
processa o form do Boletim e ignora qualquer outro. Por isso a ponte nova existe.

**Por que não quebra:**

- A ponte nova tem o filtro espelhado (`cartasgestoras`), então as duas nunca
  processam o mesmo submit.
- Múltiplos handlers no mesmo hook é o padrão do WordPress — os ids 8 e 10 já
  dividem `elementor_pro/forms/new_record` sem conflito.
- Falha aberta por design: erro cai em `error_log` e retorna, sem interromper o
  cadastro nem propagar exceção.

⚠️ **Prioridade 40, não 30.** O snippet 10 já ocupa a 30, e prioridade igual deixa
a ordem indefinida. São formulários diferentes (seria inofensivo), mas ordem
definida é mais fácil de depurar.

⚠️ **Erro de sintaxe PHP pode derrubar o site.** O Code Snippets desativa o
snippet em vez de gerar fatal, mas o risco real é errar ao colar. Ativar em
horário de baixo tráfego e **testar um cadastro no Boletim AM logo depois**, para
confirmar que as pontes antigas seguem funcionando.

## Montar o formulário (Elementor)

Na página 78368, três campos:

| Campo | Tipo | ID | Obrigatório |
|---|---|---|---|
| Nome | Texto | `nome` | sim |
| E-mail | E-mail | `email` | sim |
| WhatsApp | Telefone | `telefone` | sim |

⚠️ **Configurações Adicionais → ID do formulário: `cartasgestoras`.** É por esse
id que a ponte reconhece o form; com outro valor ela ignora o submit em silêncio.

⚠️ **Ações após o envio → Redirecionar** para a página de obrigado
(`/conteudo/cartas-das-gestoras-obrigado/`).

## ⚠️ O que ainda NÃO tem: design

O conteúdo das duas páginas está escrito, na anatomia da landing do Livro
Linguagem Econômica (id `73683`) — hero, o que você recebe, para quem é, quem
escreve. Mas são **blocos Gutenberg, sem layout**.

O `_elementor_data` **aceita escrita** pela REST API (testei), mas a leitura volta
vazia — não dá para copiar o layout do livro por lá. O caminho rápido é
**duplicar a página 73683 no Elementor** e trocar o texto pelo que está aqui,
herdando o layout inteiro.

## Números e ids conferidos (09/09/2026)

| O quê | Valor |
|---|---|
| Sequência (a mesma do form do Alan) | `2888305` |
| Tag Mercado Financeiro | `22406993` (a `22775548` é órfã) |
| Campos no Kit | `phone` (676333), `whatsapp` (1142293) |
| WhatsApp da casa | `wa.me/5521971167250` (o mesmo da página do livro) |
| PDF (URL fixa) | `storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf` |

## Falta

- [ ] Montar o layout no Elementor (duplicar a 73683)
- [ ] Montar o formulário com id `cartasgestoras` e o redirect
- [ ] Instalar a ponte com escopo `global` e o API Secret
- [ ] Testar o fluxo ponta a ponta com um e-mail real
- [ ] **Publicar as duas páginas** (autorizado pelo Vitor em 09/09)
- [ ] Conferir se a sequência 2888305 entrega a URL fixa do PDF no e-mail
