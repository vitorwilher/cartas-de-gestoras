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
├── requirements.txt
└── cartas.py                # script principal
```

## Renderização do PDF

- **Quarto 1.9+** com engine **XeLaTeX** (via TinyTeX na CI)
- `lang: pt-BR` ativa babel-portuges e hifenização automaticamente
- Titlepage customizada com logo `AM.png`, título, autor com footnote bio e data
  em pt-BR — mesmo padrão do `../Newsletters`
- Os `.qmd` ficam **2 níveis abaixo** da raiz (`digests/resumo/`), então a capa
  referencia `../../AM.png`

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
