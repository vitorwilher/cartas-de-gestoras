// Numeração por capítulo (H1 = capítulo), com suporte a apêndices.
// Espelha o numbering.typ do template de livro interno do Quarto (orange-book).
#let equation-numbering = it => {
  let pattern = if state("appendix-state", none).get() != none { "(A.1)" } else { "(1.1)" }
  numbering(pattern, counter(heading).get().first(), it)
}
#let callout-numbering = it => {
  let pattern = if state("appendix-state", none).get() != none { "A.1" } else { "1.1" }
  numbering(pattern, counter(heading).get().first(), it)
}
#let subfloat-numbering(n-super, subfloat-idx) = {
  let chapter = counter(heading).get().first()
  let pattern = if state("appendix-state", none).get() != none { "A.1a" } else { "1.1a" }
  numbering(pattern, chapter, n-super, subfloat-idx)
}
// Teoremas (theorion): herdam 1 nível (capítulo)
#let theorem-inherited-levels = 1
#let theorem-numbering(loc) = {
  if state("appendix-state", none).at(loc) != none { "A.1" } else { "1.1" }
}
#let theorem-render(prefix: none, title: "", full-title: auto, body) = {
  block(width: 100%, inset: (left: 1em), stroke: (left: 2pt + rgb("#1CA0D8")))[
    #if full-title != "" and full-title != auto and full-title != none {
      strong[#full-title]
      linebreak()
    }
    #body
  ]
}
