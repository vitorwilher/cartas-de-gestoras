# Landing de captura no WordPress

**Status: página criada como RASCUNHO. Não publicada.**

- **Página:** id `78368`, slug `cartas-de-gestoras`
- **Editar:** https://analisemacro.com.br/wp-admin/post.php?post=78368&action=edit
- **Ponte PHP:** `captura_cartas_para_convertkit.php` (deste diretório)

## Por que precisa da ponte

**A ação "ConvertKit" do Elementor Pro escreve APENAS `email` e `first_name`.**
Ela lê as tags do Kit para montar o seletor, mas não escreve campo nem tag a
partir do formulário. Está verificado no payload real e documentado no
`../ROI_Diagnostico/CLAUDE.md` — o Cristiano e o Alan testaram 3 plugins em
02-03/09/2026, todos iguais.

Sem a ponte, **o telefone não chega ao Kit**.

## ⚠️ O que esta página É e o que NÃO é

**É o CONTEÚDO da landing, não o design.** O texto segue a anatomia da página do
Livro Linguagem Econômica (id `73683`), que é o padrão da casa: hero com promessa
específica → o que você recebe → para quem é → o argumento → quem escreve (com
credenciais e citação) → formulário.

**NÃO tem layout.** A página do livro é montada no **Elementor**, e o Elementor
guarda o layout em `_elementor_data` — um post meta que a REST API **expõe a
chave mas não o valor**, e que não dá para escrever de fora com segurança. O que
criei via API são blocos Gutenberg: o texto certo, na ordem certa, sem desenho.

O caminho a partir daqui é abrir no Elementor e montar as seções sobre esse
texto — ou, mais rápido, **duplicar a página do livro** (73683) e trocar o
conteúdo, herdando o layout inteiro pronto.

## Passo a passo

### 1. Montar o formulário no Elementor

Editar a página, trocar o parágrafo marcado `[SUBSTITUIR POR FORMULÁRIO
ELEMENTOR]` por um widget **Form** com três campos:

| Campo | Tipo | ID | Obrigatório |
|---|---|---|---|
| Nome | Texto | `nome` | sim |
| E-mail | E-mail | `email` | sim |
| Telefone | Telefone | `telefone` | **sim** (decisão do Vitor) |

⚠️ Em **Configurações Adicionais → ID do formulário**, definir exatamente
`cartasgestoras`. É por esse id que a ponte reconhece o form; com outro valor ela
ignora o submit e o telefone se perde em silêncio.

### 2. Instalar a ponte

Code Snippets → Add New → colar `captura_cartas_para_convertkit.php`.

⚠️ **Escopo `global`, não `front-end`.** O submit do Elementor vai por
`admin-ajax.php`, que não é coberto por "front-end". A ponte fica ativa, sem erro
de sintaxe, e simplesmente não executa. Foi o que mais custou tempo no conserto de
15/08 — se o dado parar de chegar, confira o ESCOPO antes do código.

Substituir `<<<API_SECRET_DO_CONVERTKIT>>>` pelo API Secret do Kit.

### 3. Testar antes de publicar

Preencher o formulário com um e-mail real de teste e conferir na API do Kit se o
assinante recebeu a tag e os campos `phone` e `whatsapp`.

## O que a ponte faz

Uma única chamada a `/v3/tags/22406993/subscribe`, que **cria o assinante se ele
não existir e aplica a tag ao mesmo tempo**:

- `first_name` ← campo nome
- `fields.phone` e `fields.whatsapp` ← telefone, normalizado para dígitos com DDI
  55 quando vem só com DDD (formato que o disparo de WhatsApp espera)
- tag **Mercado Financeiro** (`22406993`)

**Testado de verdade em 09/09/2026** com a chamada exata que o PHP faz: HTTP 200,
`phone` e `whatsapp` gravados, tag aplicada. O assinante de teste foi removido.

⚠️ **O Kit descarta em silêncio valor de campo que não existe.** Os campos usados
foram conferidos na API: `phone` (676333) e `whatsapp` (1142293). Ao acrescentar
campo novo, criar antes no painel do Kit.

⚠️ A tag `22406993` é a que **tem gente** (532 assinantes). Existe outra chamada
"Mercado Financeiro e Investimentos" (`22775548`) que está **zerada e é órfã** —
não usar.

## Duas decisões que faltam

1. **A sequência de boas-vindas** precisa entregar a URL fixa do PDF
   (`https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf`).
   Como o pipeline sobrescreve o arquivo toda terça, quem se inscrever em qualquer
   semana recebe a edição corrente — sem trocar nada no painel.
2. **Esta página x a landing do Kit.** Já existe
   `analisemacro.kit.com/sintese-semanal-das-cartas-das-gestoras` (form 9899518),
   no ar. Manter as duas divide a métrica: decidir qual é a oficial.

   ⚠️ **As duas capturam telefone.** O form NATIVO do Kit já traz
   `email_address`, `fields[first_name]` e `fields[phone]` — verificado no JS do
   formulário (`/ec3285530c/index.js`) em 09/09/2026. A limitação de só passar
   email e first_name é da integração **Elementor→ConvertKit**, que não se aplica
   a um form do próprio Kit.

   A diferença real entre as duas é outra:

   | | Kit (9899518) | WordPress (78368) |
   |---|---|---|
   | Telefone | sim, nativo | sim, via ponte |
   | Trabalho para manter | nenhum | snippet + form Elementor |
   | Controle de design | limitado ao Kit | total |
   | UTM no assinante | não | sim (ponte id 8 já existente) |
   | Pixel/CAPI da Meta | não | sim, o do site |

   Se o objetivo é só captar, **a do Kit já resolve e não precisa de manutenção**.
   A do WordPress se justifica por design próprio, UTM e rastreamento de anúncio.
