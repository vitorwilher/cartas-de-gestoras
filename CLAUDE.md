# Projeto: Síntese das cartas das gestoras

## Contexto

Pipeline automatizado que lê as **cartas aos investidores das principais gestoras
brasileiras**, sintetiza com LLM e entrega o resumo via WhatsApp.

É o segundo pipeline de síntese informacional do portfólio, irmão do
`../Newsletters` (digest semanal de newsletters). Reaproveita deliberadamente a
arquitetura, as convenções e a **infraestrutura de entrega já validada** daquele
projeto — inclusive o número de produção do WhatsApp e o System User token sem
expiração. Ver `../Newsletters/CLAUDE.md` para o histórico das armadilhas da
Meta API (billing 141006, frequency cap de MARKETING, `accepted` ≠ entregue).

Segue **CRISP-DM** adaptado: "modelagem" = prompt engineering + escolha de
modelo; "avaliação" = validação qualitativa da síntese; "deployment" =
agendamento em nuvem (GitHub Actions) com entrega por WhatsApp.

**Origem da lista de gestoras**: post do Instagram de Ricardo Peruffo, CFA
(`docs_post-instagram-peruffo.jpeg`), que compilou as 12 principais gestoras do
Brasil: Dynamo, IP, Alaska, Kapitalo, Adam, Legacy, Bahia, Occam, JGP, Kinea,
Neo e Dahlia.

## Objetivo de negócio

Entregar, numa cadência fixa, uma **síntese das cartas novas** publicadas pelas
gestoras desde a última execução, com:

1. Uma seção por gestora que publicou carta nova (não por tema — aqui a **fonte
   é a unidade de análise**, ao contrário do digest de newsletters)
2. A **tese de investimento** de cada gestora: posicionamento, o que mudou desde
   a carta anterior, e os riscos que ela mesma aponta
3. Uma seção final de **convergências e divergências** entre as gestoras — o
   valor real de ler 12 cartas juntas é ver onde o consenso se forma e onde
   racha
4. Rastreabilidade: link para o PDF original de cada carta citada

## A dimensão temporal é heterogênea (decisão central do projeto)

**As cartas NÃO são todas mensais.** Mapeamento verificado em 2026-08-11
(todas as URLs retornaram HTTP 200 em requisição real):

| Periodicidade | Gestoras |
|---|---|
| **Mensal** (10) | Alaska, Bahia, Occam, JGP, Kinea, NEO, Dahlia, Adam, Legacy, Kapitalo |
| **Irregular** (2) | **Dynamo** (~2-4/ano), **IP Capital Partners** (~1/ano) |

As duas irregulares são justamente as de maior densidade editorial: publicam
**ensaios temáticos**, não relatórios periódicos de performance. A Dynamo, ao
contrário da tradição que a descreve como trimestral, publicou as cartas 125-128
com intervalos de 2, 6 e 2,5 meses.

Duas gestoras publicam **séries paralelas** no mesmo mês, e ambas devem ser
capturadas: Occam (Carta Mensal + Carta Mensal Crédito) e Legacy (macro +
crédito). A Kapitalo publica uma carta por fundo em 5 sub-páginas, com
periodicidades distintas (K10/Kappa-Zeta/NW3 mensais, Tarkus semestral,
Temáticas irregulares).

O mapeamento completo, com as armadilhas de cada site, vive em
`gestoras/gestoras.yml` — **leia as `notas` antes de mexer na coleta**.

Consequência arquitetural: o pipeline **não pode assumir uma cadência única**.
Ele roda num cron fixo, detecta o que é **novo desde a última execução** e
sintetiza **apenas o delta**. Se nenhuma gestora publicou nada na janela, o
pipeline termina sem enviar nada — silêncio é uma saída válida.

O estado (última carta vista por gestora e série) é versionado no campo
`ultima_carta` de `gestoras/gestoras.yml`: vazio antes da primeira execução e um
mapa `{serie: identificador}` depois dela. O workflow commita esse campo de volta,
no mesmo espírito do `usado_em` das séries do `../Newsletters`. Sem esse commit,
o marcador morreria com o runner e toda execução reprocessaria o histórico inteiro.

## Arquitetura

```
Cron GitHub Actions (cadência fixa)  ou  workflow_dispatch
    │
    ▼
Para cada gestora em gestoras/gestoras.yml:
    ├─▶ coleta a página de listagem de cartas (httpx + BeautifulSoup)
    ├─▶ descobre as cartas publicadas e suas datas
    ├─▶ compara com `ultima_carta` (estado versionado)  ──▶ nada novo? pula
    └─▶ baixa o PDF novo → extrai texto (pdfplumber)
            │
            ▼
    corpus (só as cartas novas)
            │
            ▼
    Claude Opus (síntese; streaming + adaptive thinking)
            │
            ▼
    .qmd → Quarto + XeLaTeX → .pdf
            ├─▶ git commit (digests/ + gestoras/gestoras.yml)
            └─▶ Meta WhatsApp Cloud API v20.0 (template UTILITY, header document)
```

## Convenções

- **Linguagem**: Python 3.12+
- **Coleta HTTP**: `httpx` com timeout de 60s (mesma escolha do Newsletters)
- **Parsing HTML**: `BeautifulSoup4` com `html.parser`
- **Extração de PDF**: `pdfplumber`
- **LLM**: SDK oficial `anthropic`, modelo Claude Opus
- **Streaming**: `client.messages.stream(...)` — não `messages.create` (evita
  timeout em respostas longas)
- **Adaptive thinking**: `thinking={"type": "adaptive"}`, `output_config={"effort": "high"}`
- **Credenciais**: SEMPRE via `.env` local / `secrets` no GitHub Actions
- **Comentários e docstrings**: em português
- **Encoding**: UTF-8

## Estratégias de coleta (verificadas)

**Nenhuma das 12 exige login, cadastro ou browser headless.** Isso foi
verificado site a site — é o achado que torna o projeto viável com `httpx` +
`BeautifulSoup`, sem Playwright/Selenium.

Cinco estratégias, escolhidas por site (campo `estrategia` no catálogo):

| Estratégia | Gestoras | Quando usar |
|---|---|---|
| `wp_rest` | Bahia, JGP, Kinea, IP | API REST do WordPress (`/wp-json/wp/v2/`) — JSON estruturado, contorna JS e HTML pesado |
| `rss` | Dynamo, NEO, Dahlia | O feed contém as cartas como itens |
| `html` | Occam, Adam, Kapitalo | `href` diretos no HTML servido |
| `ajax` | Legacy | Endpoint `admin-ajax.php`, sem nonce nem auth |
| `url_previsivel` | Alaska | URL derivável da data (tratar 404 do mês corrente) |

**Regra de ouro da coleta: NUNCA construir a URL do PDF por template** — exceto
na Alaska e, com ressalvas, na Adam. Os nomes de arquivo têm sufixos ad-hoc
(`-1`, `_`, `v2`, `vf`), capitalização variável, acentos e até hashes SHA-1
opacos. Sempre extrair o `href`.

**Regra de ouro da data: a data vem do TEXTO da página, nunca do nome do
arquivo.** Há divergências reais e documentadas: na Kapitalo, o item rotulado
"Julho 2026" aponta para `Carta-do-Gestor_Agosto_2026.pdf`; na Legacy,
`202501_Carta-Mensal.pdf` aparece rotulado como Janeiro/2026.

### Armadilhas que custariam horas (todas verificadas)

- **Bahia**: o link do PDF é montado por **JavaScript inline** — não existe
  `href` no HTML servido. Um scraper de `href` volta vazio. Daí a REST API.
- **IP**: os `href` saem **sem aspas** (`href=https://...pdf target=_blank`).
  Regex com `href="..."` falha **silenciosamente**. Usar parser HTML de verdade.
- **JGP**: o domínio **sem `www`** tem cadeia de certificado incompleta e quebra
  o handshake TLS. Usar sempre `https://www.jgp.com.br`.
- **Dynamo**: paginação é **path-based** (`/2436-2/page/2/`); `?page=2` é
  ignorado e devolve a página 1.
- **Dahlia**: paginação é **client-side** — `/nossas-cartas/page/2` devolve
  conteúdo idêntico à página 1. Usar o feed para o histórico. Slugs têm acentos
  não escapados (`/post/cila-e-caríbdis`), exigindo URL-encoding.
- **NEO**: os PDFs por fundo ficam no **SharePoint** e respondem 200 com
  `content-type: text/html` (shell do visualizador, não o PDF).
- **Adam**: a pasta de upload é o **mês seguinte** ao de referência. E o site só
  expõe cartas de **2026 em diante** — o histórico anterior foi removido.
- **Kinea/NEO**: a carta macro é **HTML inline, sem PDF** — o extrator de PDF
  não se aplica; o texto vem do próprio corpo do post.

## Restrições críticas

### Coleta
- **Respeitar as fontes**: as cartas são material público das gestoras, mas a
  coleta deve ser educada — um request por carta nova, com `User-Agent`
  identificável e pausa entre chamadas. Nunca varrer o histórico inteiro a cada
  execução (é para isso que existe o estado `ultima_carta`)
- **PDFs brutos não são versionados** (ver `.gitignore`): são binários pesados e
  o direito de redistribuição é da gestora. Versionamos o texto extraído, os
  metadados e o link para o original
- **Falha por gestora é isolada**: se o site de uma gestora mudar de layout, sair
  do ar ou bloquear, essa gestora é pulada **com log no stderr** e o pipeline
  segue com as demais. Uma gestora quebrada nunca derruba a síntese das outras

### Segurança
- **NUNCA** commitar `.env` (deve estar no `.gitignore`)
- **NUNCA** imprimir token ou API key em logs

### WhatsApp Cloud API
- Reaproveita integralmente a infra do `../Newsletters`: versão `v20.0`, número
  de produção da Análise Macro, System User token sem expiração
- Template **precisa ser categoria UTILITY**, não MARKETING. O cap de marketing
  da Meta é **global por usuário** (conta envios de todas as empresas) e o
  excedente é **descartado em silêncio** — com a API ainda respondendo
  `accepted`. Foi a causa real de duas não-entregas no Newsletters em 2026
- **`accepted` ≠ entregue**: é apenas "enfileirado". Confirmação real exigiria
  webhook (não temos). Logar o `wamid` — é o que o suporte da Meta pede
- Parâmetros de template **não aceitam newline** (erro 132018): unir listas com
  ` · `, nunca com `\n`
- Template próprio: `sintese_cartas_gestoras`, categoria UTILITY, idioma `pt_BR`,
  header `document` e corpo com `{{1}}` data, `{{2}}` gestoras cobertas e `{{3}}`
  resumo executivo específico da edição (uma linha, até 450 caracteres). Não
  reutilizar o template de newsletters: além do texto incorreto, o teste de
  2026-08-11 ocorreu dentro da janela de atendimento aberta por uma mensagem do
  destinatário e, portanto, não validou entrega automática fora das 24 horas

## Estrutura do repositório

```
Cartas_de_Gestoras/
├── .env                     # credenciais locais (gitignored)
├── .env.example             # template público
├── .github/workflows/       # cron + dispatch manual
├── .gitignore
├── AM.png                   # logo Análise Macro (titlepage do PDF)
├── CLAUDE.md
├── cartas/                  # PDFs baixados (gitignored) + texto extraído
├── digests/resumo/          # sínteses: resumo-YYYY-MM-DD.qmd / .pdf
├── gestoras/gestoras.yml    # catálogo + estado (URL, periodicidade, ultima_carta)
├── exercicios/              # acervo indexado + seleção/geração do exercício semanal
│   ├── acervo.json          # índice dos 88 exercícios de Mercado Financeiro
│   ├── selecao.py           # casa conceito da carta com exercício do acervo
│   └── geracao.py           # escolhe o conceito e escreve o exercício novo
├── mcp/                     # servidor MCP (Cloudflare Worker) — acesso por assinante
│   ├── src/index.ts
│   ├── gerar_catalogo.py    # digests/*.qmd -> catalogo.json que o Worker serve
│   └── wrangler.jsonc
├── assinatura/              # WooCommerce: produto e sincronismo com o KV do MCP
│   ├── woo.py               # cria o produto (draft) — NUNCA publica
│   └── sincronizar.py       # assinaturas ativas -> comandos wrangler kv put
├── divulgacao/              # copy e preparação de disparo — NUNCA envia
│   ├── email-lancamento.md
│   ├── carrossel-instagram.md
│   └── preparar_disparo.py
├── requirements.txt
└── cartas.py                # script principal
```

## Renderização do PDF

Desde 2026-09-08 o layout é o **design system de livros digitais da casa**
(`_extensions/analisemacro/am-livro`, copiado de `~/Dropbox/Claude Design/Design
System Ebook/`). Saiu o XeLaTeX, entrou o **Typst**.

- **Quarto 1.9+**, que já traz o **Typst embutido** — **TinyTeX não é mais
  necessário** (removido do workflow)
- Capa, tipografia, caixas e sumário vêm da extensão; o `.qmd` gerado só carrega
  conteúdo e os metadados da edição (`kicker`, `edition`, `category`)
- O subtítulo é montado no `escrever_qmd`: lista as gestoras quando são até 4,
  senão diz "N gestoras nesta edição"

⚠️ **O render acontece num diretório TEMPORÁRIO, com o `.qmd` copiado para junto
de `_extensions/` e `_brand.yml`.** O Quarto resolve extensão e brand a partir do
diretório **do arquivo** e **não sobe** para a raiz do projeto — nem com um
`_quarto.yml` declarado. Um `.qmd` em `digests/resumo/` falha com *"Unable to read
the extension 'am-livro'"*. Foi por isso que o `render.ps1` do template original
também renderizava fora da pasta.

⚠️ As **fontes da marca (7 MB) são versionadas** em `_extensions/.../fonts/`. A CI
não as tem de outra forma, e sem elas o Typst não compõe o texto.

## O produto (MVP, a partir de 2026-09-08)

Decisão do Vitor: o pipeline vira **produto de assinatura a R$ 97/mês**. A promessa
não é "resumo das cartas" — é **mostrar a quem é do mercado como destrinchar
tecnicamente as teses das gestoras**. Marketing de educação, com lucro.

Consequência para o conteúdo: a síntese sozinha não sustenta o preço. O que sustenta
é o par **síntese + exercício replicável**. Por isso o `SYSTEM_PROMPT` exige, em cada
seção, **o mecanismo** — a cadeia causal que faz a aposta se pagar — e não a descrição
do mês. Quando a carta é meramente descritiva (caso recorrente da Alaska), o prompt
manda dizer isso explicitamente em vez de inflar a seção com paráfrase.

### O exercício da semana (`exercicios/`)

Dois estágios de LLM: `escolher_conceito` lê a síntese e nomeia o mecanismo dominante
(restrito aos 12 conceitos que o acervo cobre); `gerar_exercicio` escreve o exercício.

**O acervo do Clube AM é matéria-prima, nunca entregável.** Os 88 exercícios de
Mercado Financeiro em Python (`Exercicios_AM/Mercado Financeiro/`) estão em **Dropbox
Smart Sync**: `ls` local mostra todos com **0 bytes**, e ler com `cat` devolve vazio
sem erro. O conteúdo real só sai via `mcp__claude_ai_Dropbox__fetch`. E o código é de
2022-2025 com defeitos verificados (`return` dentro de `for` fora de função, `!pip
install` em arquivo `.py`). Ele orienta **tema e abordagem didática**; o código
entregue ao assinante é gerado do zero, com dados atuais.

Falha na geração do exercício **nunca derruba a síntese** — mesmo princípio da falha
isolada por gestora.

### O MCP (`mcp/`)

Servidor MCP remoto em Cloudflare Workers, no molde do `nucleos-mcp` do
`../Nucleos_BCB/mcp` — mas com uma diferença central: aquele é *authless*, este é
**autenticado**. Todo caminho fora de `/health` exige `Authorization: Bearer <token>`,
conferido contra o KV `ASSINANTES` (que o webhook do WooCommerce mantém).

Cinco tools: `cartas_ultima_edicao`, `cartas_listar_edicoes`, `cartas_edicao`,
`cartas_exercicio` e `cartas_por_gestora`.

O Worker lê um `catalogo.json` publicado num release — o pipeline o regenera com
`mcp/gerar_catalogo.py`. Assim o servidor se atualiza **sem re-deploy**.

⚠️ **`@modelcontextprotocol/sdk` deve ficar pinado em `1.29.0` exato, sem `^`.** O
pacote `agents` fixa essa versão; com `^`, o npm instala 1.30.0 na raiz e sobra uma
cópia aninhada. O `tsc` falha com `TS2416 ... separate declarations of a private
property '_serverInfo'` — mensagem que aponta para herança de classe, não para o
problema real.

### Assinatura e divulgação (`assinatura/`, `divulgacao/`)

**Regra permanente, definida pelo Vitor em 2026-09-08: preparar, nunca disparar.**
Woo, ConvertKit e Instagram recebem rascunho e revisão humana; nenhum script deste
repositório publica produto, envia e-mail ou posta. Os scripts têm bloqueios
explícitos para isso — `preparar_disparo.py` se recusa a criar o broadcast enquanto
a copy tiver placeholder de checkout.

**Fatos verificados em 2026-09-08 (conferir de novo antes de usar):**

| Fato | Valor | Fonte |
|---|---|---|
| WooCommerce Subscriptions | **ativo** na loja | `system_status` da API |
| Loja | `aluno.analisemacro.com.br` | `WC_URL` |
| Slug `cartas-de-gestoras` | livre | API do Woo |
| Tag ConvertKit "Mercado Financeiro" | ID **22406993**, 530 assinantes | API do Kit |
| Tag 22775548 ("...e Investimentos") | **zerada, órfã — não usar** | API do Kit |

As credenciais vivem no `.env` do `../ROI_Diagnostico`, que já as usa. Os
conectores de lá (`connectors/woocommerce.py`, `connectors/convertkit.py`) são
**somente leitura** — alimentam o dashboard; a camada de escrita é a daqui.

O acesso ao MCP é derivado por HMAC do id da assinatura
(`ASSINANTES_HMAC_SECRET`): token reproduzível sem tabela de correspondência e
revogável trocando o segredo. `pending-cancel` mantém acesso — a pessoa cancelou,
mas o período pago ainda corre.

## Itens em aberto

- [x] **Mapeamento verificado das 12 gestoras (2026-08-11)** — em
  `gestoras/gestoras.yml`. 10 mensais + 2 irregulares; nenhuma exige login ou
  browser headless
- [x] Implementar `cartas.py` (coleta com as 5 estratégias + síntese + entrega)
- [x] Definir a cadência do cron: **semanal, terças às 07:00 BRT**. Com 10
  gestoras mensais concentradas nos primeiros ~13 dias do mês seguinte, essa
  frequência captura o delta com folga e ainda pega as irregulares (Dynamo/IP)
  sem atraso relevante
- [x] Template UTILITY `sintese_cartas_gestoras` aprovado na WABA de produção
  (id `1540816607134176`). O
  pipeline consulta o status antes do upload e recusa envio enquanto não estiver
  `APPROVED`
- [x] **Síntese aprofundada** — `SYSTEM_PROMPT` reescrito para exigir o mecanismo
  econômico, não a descrição do mês. Modelo atualizado para `claude-opus-5` (o
  default anterior, `claude-opus-4-7`, era de geração anterior), effort `xhigh`
- [x] **Exercício em Python** (`exercicios/`) — acervo do Clube AM indexado (88
  exercícios de Mercado Financeiro), casamento por conceito e geração em dois estágios
- [x] **MCP hospedado** (`mcp/`) — 5 tools, gate por assinante via KV, typecheck e
  build validados
- [ ] **Validar a qualidade do exercício gerado.** Não há `.env` nesta máquina, então
  a geração nunca rodou localmente — só o casamento determinístico foi testado. É o
  teste que decide se a promessa de R$ 97 se sustenta; fazer antes de vender
- [ ] Criar o KV namespace (`wrangler kv namespace create ASSINANTES`), preencher o
  `id` em `wrangler.jsonc` e publicar o Worker
- [ ] Publicar o `catalogo.json` no release `digests` que o Worker consome
- [x] **Layout migrado para o `am-livro` (Typst)** — capa, tipografia e caixas do
  design system da casa; TinyTeX removido do workflow. O `render.ps1` do template
  era só conveniência: o Quarto do macOS/Linux renderiza direto
- [x] **Assinatura preparada** (`assinatura/`) — produto R$ 97/mês pronto para criar
  como rascunho; Subscriptions confirmado ativo; sincronismo Woo -> KV do MCP escrito
- [x] **Divulgação escrita** (`divulgacao/`) — e-mail para a tag Mercado Financeiro
  (530 assinantes) e carrossel de Instagram, ambos em rascunho
- [ ] **Decisões de oferta que faltam para a copy fechar**: existe preço de tabela
  para a âncora "De X por Y"? Existe data de fim de campanha (sem ela a copy sai
  sem urgência — não se inventa)? A garantia de 7 dias da casa vale para recorrente?
- [ ] Publicar o produto no Woo e **testar o carrinho ao vivo**, lendo o preço na
  página (HTTP 200 não prova nada), antes de qualquer disparo
- [ ] Definir `ASSINANTES_HMAC_SECRET` e ligar o webhook do Woo ao KV
- [ ] Avaliar as trilhas secundárias hoje fora do escopo: cartas por fundo da
  Kinea (168 PDFs em `/atualizacoes/`), demais fundos da Kapitalo (Kappa-Zeta,
  NW3, Tarkus, Temáticas), calls e cartas de crédito da Legacy, e o Informe
  Mensal da IP (que é o produto mensal dela, distinto do Relatório de Gestão)

---

## Como atualizar este documento

Artefato **vivo**: atualize **por evento, não por antecipação**. Trocou uma
biblioteca, encontrou uma armadilha nova, mudou um endpoint ou resolveu um
obstáculo operacional → atualize a seção correspondente. Não registre decisões
hipotéticas nem conteúdo gerado.
