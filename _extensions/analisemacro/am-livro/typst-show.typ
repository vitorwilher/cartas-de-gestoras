// Chamada do template com os metadados do livro + tokens do brand.yml.
// (brand-color só existe a partir daqui — por isso entra por parâmetro.)
#show: doc => am-livro(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(by-author)$
  authors: ($for(by-author)$"$it.name.literal$",$endfor$),
$endif$
$if(date)$
  date: "$date$",
$endif$
$if(lang)$
  lang: "$lang$",
$endif$
$if(livro.category)$
  category: "$livro.category$",
$endif$
$if(livro.kicker)$
  kicker: "$livro.kicker$",
$endif$
$if(livro.edition)$
  edition: "$livro.edition$",
$endif$
$if(livro.tagline)$
  tagline: [$livro.tagline$],
$endif$
$if(livro.capa-imagem)$
  capa-imagem: "$livro.capa-imagem$",
$endif$
$if(livro.capa-layout)$
  capa-layout: "$livro.capa-layout$",
$endif$
$if(livro.sobre)$
  sobre: [$livro.sobre$],
$endif$
$if(livro.cta)$
  cta: (
$if(livro.cta.title)$
    title: [$livro.cta.title$],
$endif$
$if(livro.cta.subtitle)$
    subtitle: [$livro.cta.subtitle$],
$endif$
$if(livro.cta.button)$
    button: "$livro.cta.button$",
$endif$
$if(livro.cta.url)$
    url: "$livro.cta.url$",
$endif$
  ),
$endif$
$if(section-numbering)$
  sectionnumbering: "$section-numbering$",
$endif$
$if(toc)$
  toc: $toc$,
$endif$
$if(toc-title)$
  toc_title: [$toc-title$],
$endif$
  toc_depth: $toc-depth$,
  palette: brand-color,
  doc,
)
