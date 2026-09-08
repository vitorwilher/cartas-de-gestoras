// =====================================================================
//  AM Livro — template Typst do design system de livros digitais da Análise Macro
//  v0.2 · registro CLARO (fundo branco/paper). Herda os tokens do DS de carrossel branco.
// =====================================================================

// ---------- Tokens padrão (espelham tokens.ts dos DS de carrossel) ----------
// O _brand.yml complementa/sobrescreve via `palette:` (dicionário brand-color).
#let am-tokens = (
  blue: rgb("#1CA0D8"), blue-soft: rgb("#7FC4E8"), blue-light: rgb("#BFE3F5"),
  cyan: rgb("#03CDFF"), cyan-bright: rgb("#43EBFC"),
  royal: rgb("#002C8F"), royal-deep: rgb("#0A1F6E"), blue-cta: rgb("#0061D6"), blue-electric: rgb("#2681FE"),
  navy: rgb("#0A1A3C"), navy2: rgb("#0D2149"), ink: rgb("#0A1526"),
  paper: rgb("#EDF1F6"), ink-title: rgb("#0B1220"), body-text: rgb("#3A4658"), body-muted: rgb("#6B7788"),
  hairline: rgb("#C6D0DC"), watermark: rgb("#DDE4EC"),
  white: rgb("#FFFFFF"), grey: rgb("#C9D3DE"), grey-muted: rgb("#7E8DA0"),
  amber: rgb("#FFC53D"), yellow: rgb("#FCC606"), green: rgb("#00DC59"), red: rgb("#E5484D"),
)

// Gradiente de título sobre claro (assinatura do DS branco: azul → navy)
#let am-grad = gradient.linear(dir: ttb, rgb("#178FC6"), rgb("#1470B6"), rgb("#0A1A3C"))
// Fundo perolado dos endcaps (DS branco): branco → paper → um tom mais frio na base
#let am-bg-light = gradient.radial(rgb("#FFFFFF"), rgb("#EDF1F6"), rgb("#E3E9F1"), center: (50%, 0%), radius: 115%)

#let am-font-title = "Space Grotesk"
#let am-font-body  = "Inter"
#let am-font-mono  = "JetBrains Mono"
#let am-font-capa  = "Space Grotesk"   // título de CAPA (decisão da rodada de capas)
#let am-logo = "logo-am-cor.png"

// Estado compartilhado (paleta) para os componentes chamados no corpo do livro
#let am-state = state("am-state", (:))
#let am-P() = am-tokens + am-state.get()

// Caixas da casa: cor de fundo, filete, cor do rótulo e ícone (SVG Noto Emoji, Apache 2.0)
#let am-kinds = (
  definicao:  (label: "Definição",      fill: rgb("#E4F2FA"), stroke: rgb("#1CA0D8"), label-color: rgb("#0F7FB0"), icon: "am-icone-definicao.svg"),
  atencao:    (label: "Atenção",        fill: rgb("#FDEBEB"), stroke: rgb("#E5484D"), label-color: rgb("#B3261E"), icon: "am-icone-atencao.svg"),
  dica:       (label: "Dica",           fill: rgb("#FDF1D8"), stroke: rgb("#E0A030"), label-color: rgb("#8A5A0B"), icon: "am-icone-dica.svg"),
  pratica:    (label: "Na prática",     fill: rgb("#E3F7EA"), stroke: rgb("#22A85F"), label-color: rgb("#14703F"), icon: "am-icone-pratica.svg"),
  exemplo:    (label: "Exemplo",        fill: rgb("#E0F6FB"), stroke: rgb("#0AA6C9"), label-color: rgb("#0B7A93"), icon: "am-icone-exemplo.svg"),
  objetivos:  (label: "Neste capítulo", fill: rgb("#E6EEFF"), stroke: rgb("#0061D6"), label-color: rgb("#0047A3"), icon: "am-icone-objetivos.svg"),
  resumo:     (label: "Em resumo",      fill: rgb("#E9EDF3"), stroke: rgb("#0A1A3C"), label-color: rgb("#0A1A3C"), icon: "am-icone-resumo.svg"),
  saiba-mais: (label: "Saiba mais",     fill: rgb("#E9F0FF"), stroke: rgb("#2681FE"), label-color: rgb("#1A5FCC"), icon: "am-icone-saiba-mais.svg"),
  exercicio:  (label: "Exercício",      fill: rgb("#EBEFFB"), stroke: rgb("#002C8F"), label-color: rgb("#002C8F"), icon: "am-icone-exercicio.svg"),
  solucao:    (label: "Solução",        fill: rgb("#F2FAF5"), stroke: rgb("#1B7F4D"), label-color: rgb("#14603A"), icon: "am-icone-solucao.svg"),
  checagem:   (label: "Teste seu entendimento", fill: rgb("#F1EEFB"), stroke: rgb("#7A5AF8"), label-color: rgb("#5335C8"), icon: "am-icone-checagem.svg"),
)

// ---------- Componentes ----------

// Caixa da casa (callout) — nunca separa o cabeçalho do corpo: se a caixa
// couber numa página, vai inteira (inquebrável, empurrada se preciso); se for
// maior que uma página, quebra, mas o cabeçalho fica grudado no corpo (sticky).
#let am-callout(kind: "definicao", title: none, body) = {
  let k = am-kinds.at(kind, default: am-kinds.definicao)
  let inner = [
    #set par(justify: false)
    #block(sticky: true, below: 4pt, grid(columns: (auto, 1fr), column-gutter: 7pt, align: horizon,
      image(k.icon, height: 17pt),
      [
        #text(font: am-font-body, size: 7pt, weight: 700, tracking: 1.4pt, fill: k.label-color)[#upper(k.label)]
        #if title != none [
          #linebreak()
          #text(font: am-font-title, weight: 700, size: 10.5pt, fill: am-tokens.ink-title)[#title]
        ]
      ]))
    #set text(size: 9.6pt)
    #body
  ]
  let caixa(brk) = block(width: 100%, inset: (left: 13pt, right: 12pt, top: 9pt, bottom: 10pt), radius: 6pt,
    fill: k.fill, stroke: (left: 3pt + k.stroke), breakable: brk, above: 1.25em, below: 1.25em, inner)
  layout(size => {
    if measure(width: size.width, caixa(true)).height < size.height * 0.95 { caixa(false) } else { caixa(true) }
  })
}

// Lead: 1º parágrafo do capítulo, maior e sem justificar
#let am-lead(body) = block(width: 100%, above: 0.6em, below: 1.4em)[
  #set par(justify: false, leading: 0.72em)
  #set text(size: 12pt, fill: am-tokens.ink-title.lighten(18%))
  #body
]

// Destaque: pull-quote centrada (equivale ao slide Destaque) — sempre inteira numa página
#let am-destaque(body) = block(width: 100%, above: 1.6em, below: 1.6em, inset: (x: 8%, y: 6pt), breakable: false)[
  #align(center)[
    #line(length: 28mm, stroke: 1.2pt + am-grad)
    #v(8pt)
    #set par(justify: false, leading: 0.55em)
    #set text(hyphenate: false)
    #show emph: e => text(fill: am-grad)[#e.body]
    #text(font: am-font-title, weight: 700, size: 17pt, fill: am-tokens.ink-title)[#body]
    #v(6pt)
    #line(length: 28mm, stroke: 1.2pt + am-grad)
  ]
]

// Substitui o container de código do Quarto (Skylighting) pelo da casa
#let Skylighting(fill: none, number: false, start: 1, sourcelines) = {
  let blocks = []
  let lnum = start - 1
  for ln in sourcelines {
    if number {
      lnum = lnum + 1
      blocks = blocks + box(width: if start + sourcelines.len() > 999 { 30pt } else { 24pt },
        text(fill: am-tokens.body-muted, [ #lnum ]))
    }
    blocks = blocks + ln + EndLine()
  }
  block(fill: rgb("#F3F7FB"), stroke: 0.5pt + am-tokens.hairline, width: 100%, inset: (x: 11pt, y: 9pt),
    radius: 5pt, breakable: true, above: 1.1em, below: 1.1em,
    text(size: 9.2pt, blocks))
}

// Saída de código (```{.saida} no .qmd): o que o bloco anterior imprime ou devolve.
// Branco, grudada ao bloco de código, rótulo SAÍDA — distinta do código sem competir com ele.
// Mesma regra de quebra do am-callout: cabe na página -> não quebra; rótulo nunca órfão.
#let am-saida(txt) = {
  let inner = [
    #block(sticky: true, below: 3pt,
      text(font: am-font-body, size: 6.5pt, weight: 700, tracking: 1.4pt, fill: am-tokens.body-muted)[SAÍDA])
    #show raw.where(block: true): set block(fill: none, inset: 0pt, radius: 0pt, width: 100%)
    #set text(size: 8.4pt, fill: am-tokens.body-text)
    #raw(block: true, txt)
  ]
  let caixa(brk) = block(width: 100%, above: -0.55em, below: 1.2em,
    inset: (left: 11pt, right: 9pt, top: 7pt, bottom: 8pt), radius: (bottom: 5pt),
    fill: white, stroke: (left: 0.5pt + am-tokens.hairline, right: 0.5pt + am-tokens.hairline, bottom: 0.5pt + am-tokens.hairline),
    breakable: brk, inner)
  layout(size => {
    if measure(width: size.width, caixa(true)).height < size.height * 0.95 { caixa(false) } else { caixa(true) }
  })
}

// Callouts padrão do Quarto (note/tip/warning/…) redesenhados no estilo da casa
// — mesma regra de quebra do am-callout (inteiro numa página; título nunca órfão)
#let callout(body: [], title: "Callout", background_color: rgb("#dddddd"), icon: none, icon_color: black, body_background_color: white) = {
  let inner = [
    #set par(justify: false)
    #block(sticky: true, below: 3pt,
      text(font: am-font-title, weight: 700, size: 10.5pt, fill: am-tokens.ink-title)[#title])
    #set text(size: 9.6pt)
    #body
  ]
  let caixa(brk) = block(width: 100%, inset: (left: 13pt, right: 12pt, top: 9pt, bottom: 10pt), radius: 6pt,
    fill: background_color, stroke: (left: 3pt + icon_color), breakable: brk, above: 1.25em, below: 1.25em, inner)
  layout(size => {
    if measure(width: size.width, caixa(true)).height < size.height * 0.95 { caixa(false) } else { caixa(true) }
  })
}

// Badge chamativa do kicker — legível de longe/em tela pequena
#let am-badge(txt, dark: false) = box(
  fill: if dark { rgb("#0061D6") } else { rgb("#0A1A3C") },
  radius: 4pt, inset: (x: 10pt, y: 5.5pt),
  text(font: am-font-body, size: 11pt, weight: 700, tracking: 2.2pt, fill: white)[#upper(txt)])

// Categoria com a última palavra em bold (regra do Footer do DS) — usada na capa
#let am-category-label(category, col) = {
  let words = category.split(" ")
  let last = words.last()
  let head = words.slice(0, words.len() - 1).join(" ")
  text(fill: col)[#head #text(weight: 700)[#last]]
}

// Título em texto puro, truncado (para cabeçalho/rodapé)
#let am-plain(content, max: 70) = {
  let s = content-to-string(content)
  let cl = s.clusters()
  if cl.len() > max { cl.slice(0, max - 2).join() + "…" } else { s }
}

// Faixa de CTA no meio do texto (`::: {.cta}` no .qmd) — usada na ABERTURA do livro.
// Diferente do CTA final, que ocupa uma página inteira: aqui é um bloco navy, largura da
// mancha, que não interrompe a leitura. Título, uma linha de apoio e o botão-cápsula.
#let am-cta-faixa(title: none, button: none, url: none, body) = {
  let P = am-tokens   // tokens fixos: o bloco roda fora de `context` (como am-destaque)
  block(width: 100%, above: 1.8em, below: 1.8em, breakable: false,
    inset: (x: 20pt, y: 18pt), radius: 8pt,
    fill: P.navy,
    stroke: (left: 3pt + P.blue))[
    #set par(justify: false, leading: 0.62em)
    #set text(hyphenate: false)
    #if title != none {
      show emph: e => text(fill: P.blue-light)[#e.body]
      text(font: am-font-title, weight: 700, size: 15pt, fill: P.white)[#title]
      v(7pt)
    }
    #set text(font: am-font-body, size: 10pt, fill: P.grey)
    #body
    #if button != none and url != none {
      v(12pt)
      link(url)[#box(fill: P.blue-cta, radius: 20pt, inset: (x: 18pt, y: 9pt),
        text(font: am-font-body, size: 10pt, weight: 700, fill: P.white)[#button])]
    }
  ]
}

// ---------- Livro ----------
#let am-livro(
  title: none, subtitle: none, authors: (), date: none, lang: "pt", region: "BR",
  category: "Análise de Dados", kicker: "LIVRO DIGITAL", edition: none, tagline: none,
  capa-imagem: none, capa-layout: "V1", sobre: none,
  cta: (:), palette: (:),
  toc: true, toc_title: "Sumário", toc_depth: 2, sectionnumbering: "1.1",
  doc,
) = {
  let P = am-tokens + palette
  am-state.update(palette)
  let site = "analisemacro.com.br"
  let cta = (
    title: [Este livro acabou. #linebreak() A _prática_, não.],
    subtitle: [Receba todos os dias, direto no seu e-mail, um insight #linebreak() sobre estatística, econometria e IA aplicadas.],
    button: "Quero receber →",
    url: "https://analisemacro.com.br/boletim-am",
  ) + cta

  set document(title: title, author: authors)
  set text(lang: lang, region: region, hyphenate: true)

  // ---- endcap: página inteira, fundo perolado + watermark da marca ----
  let endcap(watermark: true, body) = page(
    margin: 0pt, header: none, footer: none, numbering: none, fill: P.paper,
  )[
    #place(top + left, rect(width: 100%, height: 100%, fill: am-bg-light))
    #if watermark {
      place(bottom + left, dx: -12pt, dy: 30pt,
        box(text(font: am-font-title, weight: 700, size: 215pt, hyphenate: false, fill: P.watermark)[análise]))
    }
    #body
  ]

  // ================= CAPA =================
  // Três layouts do laboratório de capas, escolhidos por `livro.capa-layout`:
  //   "V1" (padrão) · Xerox  — foto sangrada + véu navy + scrim na base, badge e título embaixo.
  //   "V4"          · Janela — foto sangrada + véu navy denso + vinheta radial, tudo centrado
  //                            no eixo: logo, badge, título e subtítulo empilhados no meio.
  //   "V6"          · CGE    — foto sangrada + véu navy + gradiente escuro à esquerda,
  //                            kicker em rótulo espaçado e título no terço superior, filete no pé.
  // Nos três o título vai em Space Grotesk 700, com a palavra-chave no gradiente claro.
  // Sem `capa-imagem`, cai na capa clara perolada (sem foto).
  let grad-capa = gradient.linear(dir: ttb, rgb("#EAF6FE"), rgb("#BFE3F5"), rgb("#52B3E0"), rgb("#1C8FCB"))
  // O título vai num `block` próprio: assim o #v() que vem depois dele não é
  // absorvido pelo parágrafo do título (com `par(spacing: 0pt)` no bloco da capa).
  let capa-titulo(size) = block(width: 100%, above: 0pt, below: 0pt)[
    #set par(justify: false, leading: 0.58em)
    #set text(hyphenate: false)
    #show emph: e => text(fill: grad-capa)[#e.body]
    #text(font: am-font-capa, weight: 700, size: size, fill: white)[#title]
  ]
  // "Isto é um livro": as capas escuras se dissolviam no fundo branco de site, loja e e-reader —
  // em thumbnail não se lia o objeto. Duas peças resolvem, e valem para TODO layout com foto:
  //   · LOMBADA — faixa de 7 mm na borda esquerda, gradiente ciano→azul-CTA, que lê como o vinco
  //     de um livro fechado visto de frente (é o que dá a leitura de objeto em tamanho pequeno);
  //   · FILETE de contorno — recorta a capa contra fundos claros.
  let capa-objeto = {
    place(top + left, rect(width: 7mm, height: 297mm,
      fill: gradient.linear(dir: ttb, P.blue, rgb("#0061D6"))))
    place(top + left, rect(width: 210mm, height: 297mm,
      fill: none, stroke: 1.2pt + white.transparentize(62%), inset: 0pt))
  }
  if capa-imagem != none and capa-layout == "V4" {
    // V4 · Janela — foto sangrada sob véu navy denso + vinheta radial; tudo centrado no eixo.
    // O título é centralizado, então ele vai num bloco próprio com `align(center)`.
    page(margin: 0pt, header: none, footer: none, numbering: none, fill: P.ink)[
      #place(top + left, box(width: 210mm, height: 297mm, clip: true,
        image(capa-imagem, width: 100%, height: 100%, fit: "cover")))
      #place(top + left, rect(width: 210mm, height: 297mm, fill: P.navy.transparentize(35%)))
      #place(top + left, rect(width: 210mm, height: 297mm,
        fill: gradient.radial(P.ink.transparentize(60%), P.ink.transparentize(30%), P.ink.transparentize(10%),
          center: (50%, 45%), radius: 95%)))
      #place(center + horizon, dy: -10mm, block(width: 150mm)[
        #set par(spacing: 0pt)
        #align(center)[
          #image("logo-am-branco.png", width: 46mm)
          #v(16mm)
          #am-badge(kicker, dark: true)
          #v(16pt)
          #capa-titulo(32pt)
          #if subtitle != none {
            block(width: 100%, above: 26pt, below: 0pt,
              text(font: am-font-body, size: 11.5pt, fill: P.grey)[#subtitle])
          }
        ]
      ])
      #place(bottom + center, dy: -18mm,
        text(font: am-font-body, size: 8.5pt, fill: P.grey)[Análise Macro · #site])
      #capa-objeto
    ]
  } else if capa-imagem != none and capa-layout == "V6" {
    page(margin: 0pt, header: none, footer: none, numbering: none, fill: P.ink)[
      #place(top + left, box(width: 210mm, height: 297mm, clip: true,
        image(capa-imagem, width: 100%, height: 100%, fit: "cover")))
      #place(top + left, rect(width: 210mm, height: 297mm, fill: P.navy.transparentize(59%)))
      #place(top + left, rect(width: 210mm, height: 297mm,
        fill: gradient.linear(dir: ltr, P.ink.transparentize(6%), P.ink.transparentize(18%), P.ink.transparentize(100%))))
      #place(top + left, dx: 18mm, dy: 18mm, image("logo-am-branco.png", width: 45mm))
      #place(top + left, dx: 18mm, dy: 84mm, block(width: 128mm)[
        #set par(spacing: 0pt)
        #am-badge(kicker, dark: true)
        #v(16pt)
        #capa-titulo(34pt)
        #if subtitle != none {
          block(width: 100%, above: 20pt, below: 0pt,
            text(font: am-font-body, size: 11.5pt, fill: P.grey)[#subtitle])
        }
      ])
      #place(bottom + left, dx: 18mm, dy: -18mm, block(width: 174mm)[
        #line(length: 100%, stroke: 0.6pt + white.transparentize(70%))
        #v(7pt)
        #grid(columns: (1fr, 1fr),
          text(font: am-font-body, size: 8.5pt, fill: P.grey)[Análise Macro],
          align(right, text(font: am-font-body, size: 8.5pt, weight: 600, fill: white)[#site]))
      ])
      #capa-objeto
    ]
  } else if capa-imagem != none {
    page(margin: 0pt, header: none, footer: none, numbering: none, fill: P.ink)[
      #place(top + left, box(width: 210mm, height: 297mm, clip: true,
        image(capa-imagem, width: 100%, height: 100%, fit: "cover")))
      #place(top + left, rect(width: 210mm, height: 297mm, fill: P.navy.transparentize(47%)))
      #place(bottom + left, rect(width: 210mm, height: 165mm,
        fill: gradient.linear(dir: ttb, P.ink.transparentize(100%), P.ink.transparentize(28%), P.ink.transparentize(6%), P.ink.transparentize(4%))))
      #place(top + left, dx: 18mm, dy: 18mm, image("logo-am-branco.png", width: 45mm))
      #place(bottom + left, dx: 18mm, dy: -22mm, block(width: 160mm)[
        #set par(spacing: 0pt)
        #am-badge(kicker, dark: true)
        #v(16pt)
        #capa-titulo(40pt)
        #if subtitle != none {
          block(width: 100%, above: 22pt, below: 0pt,
            text(font: am-font-body, size: 13.5pt, fill: P.grey)[#subtitle])
        }
        #block(width: 100%, above: 16pt, below: 0pt,
          text(font: am-font-body, size: 9pt, fill: P.grey)[#site])
      ])
      #capa-objeto
    ]
  } else {
    endcap[
      #place(top + left, dx: 18mm, dy: 18mm, image(am-logo, width: 40mm))
      #place(horizon + left, dx: 18mm, dy: -14mm, block(width: 158mm)[
        #set par(spacing: 0pt)
        #am-badge(kicker)
        #v(16pt)
        #set par(justify: false, leading: 0.58em)
        #set text(hyphenate: false)
        #show emph: e => text(fill: am-grad)[#e.body]
        #block(width: 100%, above: 0pt, below: 0pt,
          text(font: am-font-capa, weight: 700, size: 40pt, fill: P.ink-title)[#title])
        #if subtitle != none {
          block(width: 100%, above: 22pt, below: 0pt,
            text(font: am-font-body, size: 14.5pt, fill: P.body-text)[#subtitle])
        }
        #block(width: 100%, above: 16pt, below: 0pt,
          text(font: am-font-body, size: 9pt, fill: P.body-muted)[#site])
      ])
    ]
  }

  // ================= CORPO: página, tipografia, chrome =================
  counter(page).update(1)
  set page(
    paper: "a4", margin: (top: 26mm, bottom: 22mm, x: 22mm), fill: P.white, numbering: "1",
    // cabeçalho: só o nome da seção (capítulo corrente); some na página de abertura do capítulo
    header: context {
      let pg = here().page()
      let opens-here = query(heading.where(level: 1)).filter(h => h.location().page() == pg)
      let prev = query(selector(heading.where(level: 1)).before(here()))
      if opens-here.len() == 0 and prev.len() > 0 {
        align(center, text(font: am-font-body, size: 6.5pt, tracking: 1.3pt, weight: 600, hyphenate: false,
          fill: P.body-muted)[#upper(am-plain(prev.last().body, max: 80))])
        v(-3pt)
        line(length: 100%, stroke: 0.5pt + P.hairline)
      }
    },
    // rodapé: logo + nome do livro à esquerda · número da página à direita
    footer: context {
      line(length: 100%, stroke: 0.5pt + P.hairline)
      v(-2pt)
      grid(columns: (auto, 1fr, auto), column-gutter: 7pt, align: horizon,
        image(am-logo, height: 4.8mm),
        text(font: am-font-body, size: 7.5pt, fill: P.body-muted)[#am-plain(title, max: 78)],
        text(font: am-font-body, size: 7.5pt, weight: 700, fill: P.navy)[#counter(page).display()])
    },
  )
  set text(font: am-font-body, size: 10.5pt, fill: P.body-text)
  set par(justify: true, leading: 0.74em, spacing: 1.15em)
  set heading(numbering: sectionnumbering)
  show strong: set text(fill: P.navy)
  show link: set text(fill: P.blue)
  set list(marker: ([#text(fill: P.blue)[•]], [#text(fill: P.blue)[–]]), indent: 0.6em, body-indent: 0.6em)
  set enum(numbering: n => text(fill: P.navy, weight: 600)[#n.], indent: 0.6em, body-indent: 0.6em)
  // calt: 0 — a JetBrains Mono usa alternativas contextuais que transformam "<|" e "|>" em setas
  // (◁ ▷), corrompendo tokens especiais de LLM e o operador |> do R. `ligatures: false` NÃO
  // resolve (só desliga `liga`); é preciso desligar `calt`. O código tem de sair literal.
  show raw: set text(font: am-font-mono, size: 0.92em, features: (calt: 0))
  show raw.where(block: false): set text(weight: 500)
  show quote: it => block(width: 100%, inset: (left: 12pt, y: 2pt), stroke: (left: 2.5pt + P.blue),
    text(style: "italic", fill: P.ink-title.lighten(15%))[#it.body])
  set figure(numbering: it => numbering("1.1", counter(heading).get().first(), it), placement: auto)
  set figure.caption(separator: [ — ])
  show figure.caption: set text(font: am-font-body, size: 8.5pt, fill: P.body-muted)
  show figure.caption: set align(center)
  show figure: set block(above: 1.5em, below: 1.7em)
  show table: set text(size: 9pt)
  set table(stroke: none, inset: (x: 8pt, y: 6pt),
    fill: (x, y) => if y == 0 { P.navy } else if calc.odd(y) { P.paper } else { none })
  show table.cell.where(y: 0): set text(fill: P.white, weight: 700)
  show footnote.entry: set text(size: 8.5pt)
  set math.equation(numbering: equation-numbering)

  // ---- Abertura de capítulo (H1) ----
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    block(width: 100%, inset: (top: 26mm, bottom: 10mm), breakable: false)[
      #if it.numbering != none [
        #text(font: am-font-body, size: 8.5pt, weight: 600, tracking: 3pt, fill: P.body-muted)[CAPÍTULO]
        #v(-2pt)
        #text(font: am-font-title, weight: 700, size: 66pt, fill: am-grad)[#counter(heading).display("1")]
        #v(2pt)
      ]
      #set par(justify: false, leading: 0.5em)
      #set text(hyphenate: false)
      #show emph: e => text(fill: am-grad)[#e.body]
      #text(font: am-font-title, weight: 700, size: 27pt, fill: P.ink-title)[#it.body]
      #v(8pt)
      #line(length: 28mm, stroke: 2pt + P.blue)
    ]
  }
  show heading.where(level: 2): it => block(above: 1.7em, below: 0.75em, breakable: false,
    text(font: am-font-title, weight: 700, size: 15pt, fill: P.navy)[#it])
  show heading.where(level: 3): it => block(above: 1.4em, below: 0.6em, breakable: false,
    text(font: am-font-title, weight: 500, size: 12pt, fill: P.blue)[#it])
  show heading.where(level: 4): it => block(above: 1.2em, below: 0.5em,
    text(font: am-font-body, weight: 600, size: 10.5pt, fill: P.ink-title)[#it.body])

  // ================= ROSTO + COLOFÃO =================
  page(header: none, footer: none)[
    #image(am-logo, width: 27mm)
    #v(28mm)
    #text(font: am-font-body, size: 9pt, weight: 600, tracking: 3pt, fill: P.body-muted)[#upper(kicker)]
    #v(6pt)
    #set par(justify: false, leading: 0.5em)
    #set text(hyphenate: false)
    #show emph: e => text(fill: am-grad)[#e.body]
    #text(font: am-font-title, weight: 700, size: 30pt, fill: P.ink-title)[#title]
    #v(10pt)
    #if subtitle != none { text(font: am-font-body, size: 13pt, fill: P.body-text)[#subtitle] }
    #v(16pt)
    #line(length: 28mm, stroke: 2pt + P.blue)
    #v(12pt)
    #if authors.len() > 0 { text(size: 11pt, weight: 600, fill: P.navy)[#authors.join(", ")]; linebreak() }
    #if edition != none { text(size: 9.5pt, fill: P.body-muted)[#edition] }
    #place(bottom + left, block(width: 100%)[
      #line(length: 100%, stroke: 0.5pt + P.hairline)
      #v(6pt)
      #set par(justify: false, leading: 0.6em)
      #set text(size: 8pt, fill: P.body-muted)
      © #datetime.today().year() Análise Macro · #site · \@analisemacro \
      Material de apoio ao ensino. Reprodução total ou parcial só com autorização da Análise Macro. \
      Encontrou um erro ou tem uma sugestão? Fale com a equipe pelo WhatsApp — #link("https://analisemacro.com.br/zap")[analisemacro.com.br/zap] — ou por email: comercial\@analisemacro.com.br. \
      #if date != none [Versão de #date.]
    ])
  ]

  // ================= SUMÁRIO =================
  if toc {
    page(header: none)[
      #text(font: am-font-title, weight: 700, size: 27pt, fill: P.ink-title)[#toc_title]
      #v(3pt)
      #line(length: 28mm, stroke: 2pt + P.blue)
      #v(10mm)
      #show outline.entry.where(level: 1): it => {
        v(9pt, weak: true)
        text(font: am-font-title, weight: 700, size: 11pt, fill: P.navy, it)
      }
      #show outline.entry.where(level: 2): set text(size: 9.5pt)
      #outline(title: none, depth: toc_depth, indent: 1.4em)
    ]
  }

  // ================= CONTEÚDO =================
  doc

  // ================= SOBRE A ANÁLISE MACRO =================
  let sobre-texto = if sobre != none { sobre } else {
    [A Análise Macro é uma plataforma brasileira de educação, consultoria e análise de dados focada em economia, finanças e ciência de dados. Ela surgiu para preencher a lacuna prática deixada pelas faculdades, unindo a teoria econômica ao uso de ferramentas como Python, R e inteligência artificial para o tratamento de séries temporais e conjuntura.]
  }
  page(header: none, footer: none)[
    #v(30mm)
    #image(am-logo, width: 34mm)
    #v(10mm)
    #text(font: am-font-title, weight: 700, size: 22pt, fill: P.ink-title)[Sobre a Análise Macro]
    #v(4pt)
    #line(length: 28mm, stroke: 2pt + P.blue)
    #v(8mm)
    #block(width: 128mm)[
      #set par(justify: false, leading: 0.8em)
      #set text(size: 11pt, fill: P.body-text)
      #sobre-texto
    ]
    #v(8mm)
    #text(font: am-font-body, size: 9.5pt, weight: 600, fill: P.navy)[#site · #"@analisemacro"]
  ]

  // ================= CTA FINAL (endcap, sem watermark — regra do DS) =================
  endcap(watermark: false)[
    #place(top + left, dx: 22mm, dy: 0mm, line(angle: 90deg, length: 100%, stroke: 0.6pt + P.blue.transparentize(55%)))
    #place(top + right, dx: -22mm, dy: 0mm, line(angle: 90deg, length: 100%, stroke: 0.6pt + P.blue.transparentize(55%)))
    #place(center + horizon, dy: -6mm, block(width: 150mm)[
      #align(center)[
        #image(am-logo, width: 30mm)
        #v(12mm)
        #set par(justify: false, leading: 0.5em)
        #set text(hyphenate: false)
        #show emph: e => text(fill: am-grad)[#e.body]
        #text(font: am-font-title, weight: 700, size: 30pt, fill: P.ink-title)[#cta.title]
        #v(10pt)
        #text(font: am-font-body, size: 11.5pt, fill: P.body-text)[#cta.subtitle]
        #v(16pt)
        #link(cta.url)[#box(fill: P.blue-cta, radius: 22pt, inset: (x: 22pt, y: 11pt),
          text(font: am-font-body, size: 11pt, weight: 700, fill: P.white)[#cta.button])]
        #v(12pt)
        #text(font: am-font-mono, size: 8.5pt, fill: P.body-muted)[#cta.url.replace("https://", "")]
      ]
    ])
    #place(bottom + center, dy: -18mm,
      text(font: am-font-body, size: 8.5pt, fill: P.body-muted)[#site · \@analisemacro])
  ]

  // ================= CONTRACAPA =================
  endcap[
    #place(center + horizon, block(width: 120mm)[
      #align(center)[
        #image(am-logo, width: 36mm)
        #v(10mm)
        #if tagline != none {
          set par(justify: false, leading: 0.55em)
          set text(hyphenate: false)
          text(font: am-font-title, weight: 700, size: 21pt, fill: P.ink-title)[#tagline]
        }
        #v(8pt)
        #text(font: am-font-body, size: 9pt, fill: P.body-muted)[#site · \@analisemacro]
      ]
    ])
  ]
}
