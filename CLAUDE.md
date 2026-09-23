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

**Ampliada para 15 em 2026-09-11**, pela apuração de `analises/`: a lista do post
cobria só **4 das 50 maiores gestoras independentes** do país (13% do PL desse
grupo). Entraram **Genoa**, **Sparta** e **Opportunity** — mensais, ativas, com
carta de tese pública, somando R$ 109 bi. A Sparta traz **crédito privado**, eixo
que só a Occam cobria em parte e que vale 34% do patrimônio da indústria.

Ficaram de fora por **ausência real de carta pública**, não por barreira técnica:
SPX e Verde (distribuem por e-mail/BTG/Empiricus), Absolute e Pátria (só lâminas
e artigos de marketing). A **Atmos** publica ensaios densos, no nível de
Dynamo/IP, mas **parou na carta 33 (1H25)** — a 34 dá 404; revisitar antes de
incluir.

**Piloto internacional aberto em 2026-09-23**, a partir de outro post do Peruffo
(11 gestoras do mundo): entraram **Oaktree** (memos do Howard Marks), **GMO**
(Quarterly Letter) e **Bridgewater** (artigos de Research & Insights) — as mais
densas em tese macro e que não exigem browser. Campo `regiao: internacional` no
catálogo. Na síntese elas têm **seção própria, depois das brasileiras**, com um
item extra ("Leitura para o Brasil", sempre sinalizado como interpretação) e o
fechamento "## O olhar de fora"; **não recebem peso patrimonial** (a tabela é da
CVM). Fora do piloto: **Fundsmith e Pershing Square dão 403 com o desafio da
Cloudflare** (exigiriam Playwright), Berkshire deu timeout local (URL previsível,
anual — testar da CI), e Pabrai, Marcellus, Oakmark, AQR e DoubleLine não foram
mapeadas. ⚠️ A landing e a copy ainda falam em "15 gestoras brasileiras".

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
| **Mensal** (13) | Alaska, Bahia, Occam, JGP, Kinea, NEO, Dahlia, Adam, Legacy, Kapitalo, **Genoa**, **Sparta**, **Opportunity** |
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

Nove estratégias, escolhidas por site (campo `estrategia` no catálogo):

| Estratégia | Gestoras | Quando usar |
|---|---|---|
| `wp_rest` | Bahia, JGP, Kinea, IP | API REST do WordPress (`/wp-json/wp/v2/`) — JSON estruturado, contorna JS e HTML pesado |
| `rss` | Dynamo, NEO, Dahlia | O feed contém as cartas como itens |
| `html` | Occam, Adam, Kapitalo, **Genoa** | `href` diretos no HTML servido |
| `ajax` | Legacy | Endpoint `admin-ajax.php`, sem nonce nem auth |
| `url_previsivel` | Alaska | URL derivável da data (tratar 404 do mês corrente) |
| `url_serial` | **Sparta** | URL por contador AAAAMM, **quando a listagem HTML está desatualizada** |
| `url_fixa` | **Opportunity** | Um único PDF em URL sobrescrita; o identificador vem do CONTEÚDO |
| `html_posts` | **Oaktree**, **Bridgewater** | Cartões de listagem com data em inglês; item sem data é DESCARTADO |
| `pdf_da_pagina` | **GMO** | A listagem aponta a edição corrente, cuja página traz o PDF |

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
- **Sparta**: a **tabela da página está congelada** — em 11/09/2026 o último
  `href` listado era `CartaMensal_202512`, mas os PDFs de 2026 existem (202606,
  202607, 202608 = HTTP 200 `application/pdf`). Um coletor de `href` perderia 8
  meses **sem erro nenhum**, só devolvendo menos itens. É a única exceção em que
  templar a URL é MAIS confiável que a página — daí a estratégia `url_serial`.
- **Opportunity**: não há listagem nem histórico, só **um PDF numa URL fixa,
  sobrescrita** a cada mês. A URL não identifica a carta: usá-la como
  identificador faria o pipeline nunca detectar novidade. `descobrir_url_fixa`
  tira o identificador do **conteúdo** (a data na capa), com `Last-Modified` de
  desempate.
- **Genoa**: o rótulo do link é só `"PDF"` e a data ("Carta Mensal /
  Agosto/2026") vive no **avô** do `<a>`, não no pai. Sem subir um nível na
  árvore, as 78 cartas caíam todas no fallback de hoje — **falha silenciosa**,
  sem exceção. `descobrir_html` agora sobe um nível só quando o contexto
  imediato não tem nome de mês, para não alterar Occam/Adam/Kapitalo (conferido:
  contagens idênticas antes e depois).
- **Item sem data trava a série** (achado em 23/09/2026): na Genoa, um *white
  paper* sem mês no rótulo caiu no fallback de hoje, virou o "mais recente" e
  entrou na edição de 15/09 **no lugar da carta de agosto**. Como a data de hoje
  sempre vence, o delta pararia nele para sempre, sem erro. Mesmo mecanismo,
  latente, na Adam: `_AGOSTO_2026` no nome do arquivo anula o `\b` da regex.
  Filtro por "carta mensal" (Genoa) e por "carta" no arquivo (Adam, que também
  listava 6 Relatórios Gerenciais). **Uma data igual a hoje no coletor é sintoma.**

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

### Dimensionar o consenso (`analises/peso_das_teses.py`)

A seção "Convergências e divergências" dizia *quantas* casas defendem cada tese.
Contar trata Dynamo (R$ 20 bi) e Dahlia (R$ 4,6 bi) como iguais. Agora o prompt
recebe o **peso patrimonial** de cada casa e pode escrever "quatro casas, somando
R$ 58 bi sob mandato compatível, veem o ciclo virando; duas, com R$ 12 bi,
discordam" — mostra se o consenso é da maioria ou de quem carrega o risco. É um
cruzamento que nenhuma carta individual faz, e nasce de `analises/`.

⚠️ **NUNCA usar o PL total da gestora para dimensionar uma tese.** O PL da CVM
soma todos os fundos da casa, e a composição varia brutalmente (medido 11/09/2026):

| Casa | PL total | em juro/macro |
|---|---|---|
| Kinea | R$ 177,3 bi | R$ 9,3 bi (**5%**) — o resto é crédito e previdência |
| Dynamo | R$ 20,0 bi | R$ 0,0 bi (**0%**) — 96% é ações |
| Alaska | R$ 8,8 bi | R$ 0,0 bi (**0%**) |
| Kapitalo | R$ 42,4 bi | R$ 29,5 bi (70%) |

Uma conta sobre juro somando PL total faria a Kinea dominar com R$ 177 bi que
estão em crédito imobiliário. A solução: a CVM classifica por FUNDO
(`Classificacao_Anbima`), então cada eixo de tese recebe só o PL dos fundos com
mandato compatível.

⚠️ **Mandato não é posição.** A classe diz o que o fundo PODE fazer, não o que
fez — um macro pode estar zerado em juro. Por isso o prompt exige escrever "sob
mandato compatível", nunca "apostando". A regra está no `SYSTEM_PROMPT`.

`contexto_patrimonial()` em `cartas.py` lê `analises/peso_das_teses_prompt.txt`.
**Falha ali nunca derruba a síntese** — avisa no stderr e a edição sai sem os
números, como era antes. Mesmo princípio da falha isolada por gestora.

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

**Regra geral, definida pelo Vitor em 2026-09-08: preparar, nunca disparar.**
Woo e Instagram recebem rascunho e revisão humana; nenhum script deste repositório
publica produto ou posta.

**Exceção, aberta pelo Vitor em 2026-09-09: o e-mail semanal.** Para o pipeline
rodar sozinho, `broadcast_semanal.py --enviar` AGENDA o broadcast (`send_at` ~30
min à frente, status `scheduled`) em vez de criar rascunho. A janela é deliberada:
`scheduled` é cancelável no painel, envio imediato é irreversível. Três guardas
antes de agendar: a tag precisa ter gente, o `subscriber_filter` precisa constar na
RELEITURA, e o status precisa ter virado `scheduled` — senão o script falha e manda
enviar à mão.

⚠️ **Isso exige a API v4** (`api.kit.com/v4`, header `X-Kit-Api-Key`; Bearer dá 401).
A **v3 aceita `subscriber_filter`, responde 200 e descarta o campo em silêncio** —
volta `null`. Um broadcast criado pela v3 sai para a lista INTEIRA (5.118), não para
a tag do projeto. Na CI o secret é `CONVERT_KIT_V4`.

⚠️ **A leitura de tags do Kit atrasa por indexação.** Logo após marcar alguém,
`/v4/tags/<id>/subscribers` pode voltar vazio enquanto o painel já mostra a tag. Não
concluir que a marcação falhou a partir de uma leitura só. Os scripts têm bloqueios
explícitos para isso — `preparar_disparo.py` se recusa a criar o broadcast enquanto
a copy tiver placeholder de checkout.

⚠️ **O atraso vale na direção inversa também, e é pior.** Depois de REMOVER uma tag
(`DELETE /v4/tags/<tag>/subscribers/<sub>`, responde 204), a lista
`GET /v4/tags/<id>/subscribers` **segue mostrando quem já saiu** — em 11/09/2026
ainda listava as 28 pessoas removidas depois de 110s, com o total da tag intacto.
A leitura que diz a verdade é `GET /v4/subscribers/<id>/tags`, por assinante, que
já refletia a remoção em segundos. Se as duas discordarem, a do assinante vence.
Nunca repetir a escrita com base na lista da tag.

### Tag no Kit é gatilho, não rótulo (incidente de 11/09/2026)

A ponte da landing aplicava três tags. A terceira, `13265211` ("Leads - Exercícios"),
estava documentada — no comentário do código e no README — como segmentação "pelo
formato". **Era falso:** a tag tem funil próprio e inscrevia o lead no **Boletim AM**,
que nem a landing nem a página de obrigado mencionam. As duas páginas prometem só a
síntese semanal das cartas.

Por que importa além do incômodo: quem chega pela landing é lead frio de Instagram
e LinkedIn. E-mail de produto que a pessoa não conhece, na primeira semana, é o
caminho curto para marcar spam — e spam de lead novo castiga a reputação do domínio
inteiro, **inclusive a entrega desta própria síntese**. O risco não fica contido na
landing.

Corrigido: tag removida do snippet no ar e dos **28** leads que a ganharam por essa
via entre 09/09 e 11/09. Os **8** que já tinham a tag de origem anterior (a mais
antiga de dez/2025) foram **preservados** — consentiram noutra isca, e removê-la
apagaria consentimento legítimo. Ao limpar marcação indevida, sempre separar quem
veio pela porta errada de quem já estava lá.

**Regra que fica:** antes de acrescentar qualquer tag a uma ponte de captura,
conferir em *Automations → Visual automations* o que está pendurado nela, e conferir
se a copy promete aquilo. Para oferecer outro produto, o caminho é **checkbox
opcional na landing, desmarcado** — nunca tag embutida no código.

⚠️ **Pendência:** a API do Kit **não expõe as automações visuais** (`/v3/automations/rules`
dá 404), então não dá para auditar isso por código. Falta conferir no painel o que
está pendurado em **"Mercado Financeiro" (22406993)**, que a ponte continua aplicando.

**Validado de ponta a ponta em 11/09/2026**, com submit real do formulário: o lead
recebeu só `Leads - Cartas Semanais` + `Mercado Financeiro`, com `phone` e `whatsapp`
gravados com DDI, e a sequência disparou o e-mail da síntese — nenhum e-mail do
Boletim. A ponte segue funcionando depois da edição.

⚠️ **Ao verificar um teste desses, buscar o assinante POR E-MAIL**
(`/v4/subscribers?email_address=...`). A listagem `?sort_order=desc` está defasada
pela indexação e **omitiu um cadastro feito 9 minutos antes** — o que me levou a
afirmar, errado, que o teste não havia chegado ao Kit. Ausência em listagem do Kit
nunca é prova de que algo não aconteceu.

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

### A ponte da landing é editável por API (Code Snippets)

A ponte PHP que a landing usa não vive só no repositório: quem executa é o plugin
**Code Snippets** do WordPress, e ele **tem REST API**. A ponte é o snippet **id 11**
("Cartas de Gestoras -> ConvertKit (captura)", ativo, escopo `global`), em
`/wp-json/code-snippets/v1/snippets/11`. Credenciais: `WP_FRONT_*` no `.env` do
`../ROI_Diagnostico` (usuário `claude-bot`). Editado por essa via em 11/09/2026.

⚠️ **O snippet no ar contém o API Secret REAL do Kit**, que o arquivo versionado
(`divulgacao/wordpress/captura_cartas_para_convertkit.php`) guarda como placeholder.
Ao editar: baixar o código do ar e alterar só o trecho necessário. **Nunca** subir o
arquivo do repositório por cima — o secret se perde e a captura para.

Três armadilhas, todas verificadas (as três produzem falso resultado, não erro):

1. **Sem `User-Agent` de navegador, tudo responde 403** — inclusive `wp/v2/users/me`.
   É o WAF do gocache, não permissão. O corpo vem vazio e parece erro de credencial.
2. **O POST exige o `id` no corpo JSON**, não só na URL. Sem ele o plugin responde
   **200 devolvendo o código ANTIGO** e não grava nada. Conferir se o `code` da
   resposta reflete o que foi enviado.
3. **A releitura sem cache-buster serve cópia velha do CDN.** Logo após gravar, o
   GET devolvia o conteúdo anterior com o `modified` antigo. Usar `?nocache=<ts>` +
   `Cache-Control: no-cache`, e comparar `modified` e o tamanho do `code` — nunca só
   o texto. (`per_page=200` devolve 400; listar sem `per_page`.)

Mesmo espírito da seção do WordPress no `../Newsletters`: **status 200 nunca é prova
de efeito**. Aqui o 200 mentiu duas vezes seguidas, por motivos diferentes.

### A URL fixa do PDF (`divulgacao/publicar_pdf.py`)

O PDF de cada edição é publicado no GCS em **uma URL que nunca muda**:

```
https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf
```

O fluxo do ManyChat e a landing do ConvertKit apontam para ela e são criados
**uma vez só**; o pipeline sobrescreve o arquivo toda terça, no passo "Publicar o
PDF no GCS" do workflow. Sem isso, cada edição exigiria trocar o link à mão em
dois painéis — e a API do ManyChat nem permite editar fluxo.

Cada edição também vai para um endereço datado (`cartas/AAAA-MM-DD.pdf`), para
quem recebeu o link numa semana conseguir reabrir aquela edição depois.

Reaproveita o bucket e as credenciais do `../ROI_Diagnostico` (`SOCIAL_GCS_BUCKET`,
`GCS_CREDENTIALS_PATH`), no molde do `social/assets_gcs.py` de lá.

⚠️ **A URL fixa sobe com `Cache-Control: public, max-age=60`** (desde 23/09). Com
o padrão do GCS (1 h), um nó de borda ainda servia a edição anterior logo depois da
troca — e o e-mail sai 30 min depois apontando para ela. A datada fica no padrão.

⚠️ O passo é `continue-on-error`: falha na publicação **não derruba a edição** (o
PDF já foi gerado e enviado por WhatsApp), mas deixa o link público com a versão
anterior. Ao conferir, olhar a data na capa do PDF.

⚠️ Na CI faltam dois secrets: `SOCIAL_GCS_BUCKET` e `GCS_CREDENTIALS_JSON` (o JSON
da service account, inteiro). Sem eles o passo se pula com aviso no stderr.

### O calendário de iscas

A trilha **C · Mercado Financeiro** foi acrescentada ao
`../ROI_Diagnostico/social/iscas/2026_calendario-iscas.xlsx`: 30 quartas, de
16/09/2026 a 07/04/2027, palavra-chave única `GESTORAS`. Quartas porque
segundas/quintas são da trilha A e terças da B — e porque o pipeline roda terça
07:00, deixando a edição pronta no dia seguinte.

⚠️ **A planilha também vive no Drive** (`1tPuifu125UPND3GgVN8XPR2z4mJHg726`, pasta
"Iscas — Notebooks Estatística (trilha B)"), e a versão de lá costuma estar à
frente da local — é onde o Vitor marca os fluxos como `SIM`. O conector do Drive
**não escreve conteúdo** (só título e pasta), então o caminho é: baixar a versão do
Drive, editar, e o Vitor sobe por "Gerenciar versões" para preservar o ID.

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
- [x] **URL fixa do PDF** — `divulgacao/publicar_pdf.py` publica no GCS e o
  workflow chama a cada execução. Verificado: HTTP 200, application/pdf
- [x] **Todos os secrets da CI configurados (09/09)** — conferido cruzando
  `gh secret list` contra os `secrets.*` do workflow: nada falta. `ANTHROPIC_MODEL`
  aparece como ausente e está correto assim — é opcional, e sem ele o código usa
  o default `claude-fable-5-1`.
  ⚠️ As duas credenciais do Kit são necessárias JUNTAS: sem o
  `CONVERTKIT_API_SECRET` o script não consegue contar a tag e aborta como se ela
  estivesse vazia — por isso o guard do workflow checa as duas
- [x] **Fluxo `GESTORAS` no ManyChat criado** (Vitor, 09/09) e carrossel publicado:
  https://www.instagram.com/p/DdFcVNRla6q/ — `divulgacao/publicar_instagram.py`

  🔴 **ESTE CARROSSEL VIROU O PADRÃO DE CONTEÚDO DE INSTAGRAM DA CASA INTEIRA**
  (decisão do Vitor, 11/09/2026). `divulgacao/carrossel.py` deixou de ser só o
  gerador desta edição: é a **peça de referência** que orienta toda a produção do
  @analisemacro, iscas incluídas. A regra completa está no CLAUDE.md do
  **ROI_Diagnostico**, seção "O PADRÃO DE CONTEÚDO DO INSTAGRAM"; o estudo que a
  sustenta é https://claude.ai/code/artifact/aa906dae-3b55-446d-94c8-093a2e6b591d
  (59 posts, 30 dias).

  ⚠️ **Ao mexer em `carrossel.py`, você está mexendo no padrão da casa.** O que
  foi canonizado: bullets (nunca parágrafo) · `_limpar()` + `_titulo()` como
  doutrina de gráfico (título E medida são obrigatórios — sem eles o gráfico não
  se explica no feed) · a ordem dos 10 slides, com o slide "o caminho que eu fiz"
  · CTA com palavra-chave **e** pergunta, sem preço · `ocupar_o_slide()` para que
  bullets curtos não deixem metade do slide vazia.
- [x] **Landing publicada** em `/projetos/cartas-das-gestoras/` — captura nome,
  e-mail e WhatsApp, aplica **2 tags** no Kit (projeto + Mercado Financeiro) e
  inicia a sequência. Eram 3 até 11/09; ver "Tag no Kit é gatilho, não rótulo"
- [ ] **Auditar as automações de "Mercado Financeiro" (22406993)** no painel do
  Kit — é a tag que a ponte ainda aplica, e a API não expõe automação visual
- [x] **Envio automático do e-mail semanal** — `broadcast_semanal.py --enviar`
  agenda para +30 min, com guardas de frescor e duplicata (ver testes)
- [ ] Publicar o produto no Woo e **testar o carrinho ao vivo**, lendo o preço na
  página (HTTP 200 não prova nada), antes de qualquer disparo
- [ ] Definir `ASSINANTES_HMAC_SECRET` e ligar o webhook do Woo ao KV
- [ ] Avaliar as trilhas secundárias hoje fora do escopo: cartas por fundo da
  Kinea (168 PDFs em `/atualizacoes/`), demais fundos da Kapitalo (Kappa-Zeta,
  NW3, Tarkus, Temáticas), calls e cartas de crédito da Legacy, e o Informe
  Mensal da IP (que é o produto mensal dela, distinto do Relatório de Gestão)

## O estado em 09/09/2026 — o pipeline entrega sozinho

Fecha o ciclo aberto no MVP: as três dimensões (produto, assinatura, divulgação)
saíram do papel e o pipeline **entrega sem intervenção humana**.

| Peça | Onde |
|---|---|
| Landing de captura | `analisemacro.com.br/projetos/cartas-das-gestoras/` |
| Página de obrigado | `.../cartas-das-gestoras-obrigado/` |
| Carrossel publicado | `instagram.com/p/DdFcVNRla6q/` |
| PDF (URL fixa) | `storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf` |
| Paper técnico | `paper/paper.pdf` — 7 páginas, números gerados por código |
| Desenho da arquitetura | `docs/arquitetura-whatsapp-hub.svg` |
| Copy do LinkedIn | `divulgacao/linkedin/copy-captura-2026-09-09.md` (o Vitor posta) |

### O que roda toda terça, e em que ordem

1. `cartas.py --pdf --send` — coleta, sintetiza, gera o exercício, renderiza e
   manda por WhatsApp
2. `publicar_pdf.py` — sobrescreve a URL fixa no GCS
3. `broadcast_semanal.py --enviar --espera 30` — **agenda** o e-mail para a tag
   do projeto
4. **Resumo da execução** — escreve o resultado de cada canal no Summary do run

**Edição extra** (fora do cron): `gh workflow run cartas.yml -f nota="..."`. A
`nota` vira uma caixa "Nota desta edição" dentro de "Nesta edição" no PDF e um
parágrafo no e-mail. O cron roda sem nota. Usada em 23/09 para anunciar as
internacionais e corrigir a Genoa de 15/09.

⚠️ O passo 4 existe porque um `continue-on-error` que falha deixa o run **verde**:
sem ele, "e-mail não enviado" era visualmente idêntico a "enviado".

### As três guardas do envio automático

O pior desfecho de comunicação automática não é ficar mudo — é mandar a mensagem
errada para a pessoa certa, e isso não se desfaz. Ver `tests/test_broadcast.py`.

1. **Frescor** — recusa edição com mais de 2 dias. `cartas.py` sai com código 0
   quando ninguém publicou, e os `.qmd` são versionados: sem a guarda, uma terça
   quieta **reenviaria a edição anterior aos mesmos leads**
2. **Duplicata** — não cria broadcast se já existe um pendente com o mesmo
   assunto. Rodar duas vezes agendava dois e-mails idênticos
3. **Segmento confirmado na releitura** — status HTTP não é prova de efeito

Terminar com código 0 em "nada a enviar" é deliberado: silêncio é resultado
normal do pipeline, não falha.

### O que ainda depende de decisão

- **Fase 4 do WhatsApp** (follow-up de D+1 dentro da janela de 24h) — não iniciada
- **Publicar o produto no Woo** e testar o carrinho ao vivo antes de vender
- A tag tem poucos leads reais: os primeiros envios alcançam pouca gente. É
  esperado — é a landing que precisa acumular

---

## Como atualizar este documento

Artefato **vivo**: atualize **por evento, não por antecipação**. Trocou uma
biblioteca, encontrou uma armadilha nova, mudou um endpoint ou resolveu um
obstáculo operacional → atualize a seção correspondente. Não registre decisões
hipotéticas nem conteúdo gerado.
