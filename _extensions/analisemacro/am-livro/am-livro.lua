-- am-livro.lua — filtro do design system de livros digitais da Análise Macro
-- 1) Sintaxe de autoria da casa (divs) -> Typst (wrappers) ou EPUB/HTML (divs .am-caixa + CSS)
-- 2) Partes/apêndices do livro no Typst
-- 3) Validação da categoria editorial (uma das 4 oficiais)
-- 4) EPUB/HTML: capa, páginas finais (Sobre, CTA, contracapa) e colofão — o que no PDF o
--    typst-template.typ desenha sozinho

local CATEGORIAS = {
  ["Mercado Financeiro"] = true,
  ["Macroeconomia"] = true,
  ["Análise de Dados"] = true,
  ["Inteligência Artificial"] = true,
}

-- classe no .qmd -> função/ícone (kind) da caixa
local CALLOUTS = {
  ["definicao"]  = { kind = "definicao" },
  ["atencao"]    = { kind = "atencao" },
  ["na-pratica"] = { kind = "pratica" },
  ["dica"]       = { kind = "dica" },
  ["exemplo"]    = { kind = "exemplo" },
  ["objetivos"]  = { kind = "objetivos" },
  ["resumo"]     = { kind = "resumo" },
  ["saiba-mais"] = { kind = "saiba-mais" },
  ["exercicio"]  = { kind = "exercicio" },
  ["solucao"]    = { kind = "solucao" },
  ["checagem"]   = { kind = "checagem" },
}
local LABELS = {
  definicao = "Definição", atencao = "Atenção", ["na-pratica"] = "Na prática", dica = "Dica",
  exemplo = "Exemplo", objetivos = "Neste capítulo", resumo = "Em resumo", ["saiba-mais"] = "Saiba mais",
  exercicio = "Exercício", solucao = "Solução", checagem = "Teste seu entendimento",
}

local SITE = "analisemacro.com.br"
-- Pasta da extensão (para o Pandoc achar logo e ícones no EPUB/HTML: caminhos a partir da raiz do livro)
local EXT_DIR = pandoc.path.directory(PANDOC_SCRIPT_FILE)
local LOGO = pandoc.path.join({ EXT_DIR, "assets", "logo-am-cor.png" })
local function icone(kind) return pandoc.path.join({ EXT_DIR, "assets", "icones-png", "am-icone-" .. kind .. ".png" }) end

local function is_typst() return quarto.doc.is_format("typst") end

local function file_exists(p)
  local f = io.open(p, "rb")
  if f then f:close(); return true end
  return false
end

-- markdown (string) -> inlines / blocks
local function md_inlines(s)
  local b = pandoc.read(s, "markdown").blocks
  return (b[1] and b[1].content) or pandoc.Inlines({})
end
local function md_blocks(s) return pandoc.read(s, "markdown").blocks end

-- MetaValue -> inlines (MetaInlines/MetaString) ou nil
local function meta_inlines(v)
  if v == nil then return nil end
  if type(v) == "table" and v.t == "MetaInlines" then return pandoc.Inlines(v) end
  return pandoc.Inlines({ pandoc.Str(pandoc.utils.stringify(v)) })
end
-- MetaValue -> blocks (MetaBlocks/MetaInlines/MetaString) ou nil
local function meta_blocks(v)
  if v == nil then return nil end
  if type(v) == "table" and v.t == "MetaBlocks" then return pandoc.Blocks(v) end
  return pandoc.Blocks({ pandoc.Para(meta_inlines(v)) })
end

-- Envolve o conteúdo do div em `#fn(...)[` … `]` mantendo o pipeline do Quarto dentro do bloco
local function typst_wrap(open, content)
  local blocks = pandoc.List({ pandoc.RawBlock("typst", open) })
  blocks:extend(content)
  blocks:insert(pandoc.RawBlock("typst", "]"))
  return blocks
end

local function typst_string(s)
  return '"' .. s:gsub('\\', '\\\\'):gsub('"', '\\"') .. '"'
end
-- string Typst de várias linhas (quebras viram \n)
local function typst_string_ml(s)
  return '"' .. s:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n') .. '"'
end

-- Caixa da casa em EPUB/HTML: cabeçalho (ícone + rótulo + título) e corpo, estilizados pelo CSS
local function html_caixa(cls, spec, title, content)
  local cab = pandoc.List({
    pandoc.Plain({
      pandoc.Image({}, icone(spec.kind), "", pandoc.Attr("", { "am-icone" })),
      pandoc.Span({ pandoc.Str(pandoc.text.upper(LABELS[cls])) }, pandoc.Attr("", { "am-rotulo" })),
    }),
  })
  if title then
    cab:insert(pandoc.Plain({ pandoc.Span(md_inlines(title), pandoc.Attr("", { "am-titulo" })) }))
  end
  return pandoc.Div({
    pandoc.Div(cab, pandoc.Attr("", { "am-caixa-cab" })),
    pandoc.Div(content, pandoc.Attr("", { "am-caixa-corpo" })),
  }, pandoc.Attr("", { "am-caixa", "am-" .. cls }))
end

-- Páginas finais do EPUB/HTML (no PDF o template Typst as desenha)
local function paginas_finais(meta)
  local livro = meta["livro"] or {}
  local out = pandoc.List({})

  -- Sobre a Análise Macro + colofão
  local sobre = meta_blocks(livro["sobre"]) or md_blocks(
    "A Análise Macro é uma plataforma brasileira de educação, consultoria e análise de dados focada em " ..
    "economia, finanças e ciência de dados. Ela surgiu para preencher a lacuna prática deixada pelas " ..
    "faculdades, unindo a teoria econômica ao uso de ferramentas como Python, R e inteligência artificial " ..
    "para o tratamento de séries temporais e conjuntura.")
  out:insert(pandoc.Header(1, "Sobre a Análise Macro", pandoc.Attr("sobre-a-analise-macro", { "unnumbered" })))
  local sobre_div = pandoc.List({ pandoc.Plain({ pandoc.Image({}, LOGO, "", pandoc.Attr("", { "am-logo" })) }) })
  sobre_div:extend(sobre)
  sobre_div:insert(pandoc.Para({ pandoc.Span({ pandoc.Str(SITE .. " · @analisemacro") }, pandoc.Attr("", { "am-site" })) }))
  out:insert(pandoc.Div(sobre_div, pandoc.Attr("", { "am-sobre" })))

  local data = meta["date"] and pandoc.utils.stringify(meta["date"]) or nil
  -- (\@ para o Pandoc não ler @analisemacro como citação)
  local colofao = "© " .. os.date("%Y") .. " Análise Macro · " .. SITE .. " · \\@analisemacro\\\n" ..
    "Material de apoio ao ensino. Reprodução total ou parcial só com autorização da Análise Macro.\\\n" ..
    "Encontrou um erro ou tem uma sugestão? Fale com a equipe pelo WhatsApp — " ..
    "[analisemacro.com.br/zap](https://analisemacro.com.br/zap) — ou por email: comercial@analisemacro.com.br."
  -- a edicao entra no colofao do EPUB como ja entra no do PDF (livro.edition)
  local edicao = livro["edition"] and pandoc.utils.stringify(livro["edition"]) or nil
  if edicao then colofao = colofao .. "\\\n" .. edicao .. "." end
  if data then colofao = colofao .. "\\\nVersão de " .. data .. "." end
  out:insert(pandoc.Div(md_blocks(colofao), pandoc.Attr("", { "am-colofao" })))

  -- CTA final (default: Boletim AM; sem produtos/formações/cursos — regra da casa)
  local cta = livro["cta"] or {}
  local cta_title  = meta_inlines(cta["title"])    or md_inlines("Este livro acabou.\
A *prática*, não.")
  local cta_sub    = meta_inlines(cta["subtitle"]) or md_inlines("Receba todos os dias, direto no seu e-mail, um insight sobre estatística, econometria e IA aplicadas.")
  local cta_button = cta["button"] and pandoc.utils.stringify(cta["button"]) or "Quero receber →"
  local cta_url    = cta["url"] and pandoc.utils.stringify(cta["url"]) or "https://analisemacro.com.br/boletim-am"
  out:insert(pandoc.Header(1, cta_title, pandoc.Attr("boletim-am", { "unnumbered", "am-cta-titulo" })))
  out:insert(pandoc.Div({
    pandoc.Plain({ pandoc.Image({}, LOGO, "", pandoc.Attr("", { "am-logo" })) }),
    pandoc.Div({ pandoc.Para(cta_sub) }, pandoc.Attr("", { "am-cta-sub" })),
    pandoc.Para({ pandoc.Link({ pandoc.Str(cta_button) }, cta_url, "", pandoc.Attr("", { "am-botao" })) }),
    pandoc.Para({ pandoc.Span({ pandoc.Str((cta_url:gsub("^https?://", ""))) }, pandoc.Attr("", { "am-url" })) }),
  }, pandoc.Attr("", { "am-cta" })))

  -- Contracapa: lema + site
  local tagline = meta_inlines(livro["tagline"])
  local contra = pandoc.List({})
  if tagline then contra:insert(pandoc.Para({ pandoc.Span(tagline, pandoc.Attr("", { "am-tagline" })) })) end
  contra:insert(pandoc.Para({ pandoc.Span({ pandoc.Str(SITE .. " · @analisemacro") }, pandoc.Attr("", { "am-site" })) }))
  out:insert(pandoc.Div(contra, pandoc.Attr("", { "am-contracapa" })))
  return out
end

return {
  {
    Meta = function(meta)
      local livro = meta["livro"]
      local cat = livro and livro["category"] and pandoc.utils.stringify(livro["category"]) or nil
      if cat == nil or cat == "" then
        error("[am-livro] Falta `livro.category` no _quarto.yml (uma das 4 categorias oficiais: " ..
              "Mercado Financeiro · Macroeconomia · Análise de Dados · Inteligência Artificial).")
      end
      if not CATEGORIAS[cat] then
        error("[am-livro] `livro.category: " .. cat .. "` não é uma categoria oficial. Use: " ..
              "Mercado Financeiro · Macroeconomia · Análise de Dados · Inteligência Artificial.")
      end
      -- Capa do EPUB: a página 1 do PDF rasterizada (render.ps1 gera imagens/capa-epub.jpg);
      -- sem ela, a foto bruta de livro.capa-imagem.
      if not is_typst() and meta["cover-image"] == nil and meta["epub-cover-image"] == nil then
        local capa = nil
        if file_exists("imagens/capa-epub.jpg") then
          capa = "imagens/capa-epub.jpg"
        elseif livro and livro["capa-imagem"] then
          capa = pandoc.utils.stringify(livro["capa-imagem"])
        end
        if capa then
          meta["cover-image"] = pandoc.MetaString(capa)
          meta["epub-cover-image"] = pandoc.MetaString(capa)
        end
      end
      return meta
    end,

    Div = function(div)
      -- callouts da casa
      for cls, spec in pairs(CALLOUTS) do
        if div.classes:includes(cls) then
          local title = div.attributes["title"]
          if is_typst() then
            local t = ""
            if title then
              -- título como conteúdo Typst (permite *ênfase* etc.)
              local title_typ = pandoc.write(pandoc.Pandoc({ pandoc.Plain(md_inlines(title)) }), "typst")
              t = ", title: [" .. title_typ:gsub("\n$", "") .. "]"
            end
            return typst_wrap("#am-callout(kind: " .. typst_string(spec.kind) .. t .. ")[", div.content)
          else
            return html_caixa(cls, spec, title, div.content)
          end
        end
      end
      -- lead do capítulo
      if div.classes:includes("lead") then
        if is_typst() then return typst_wrap("#am-lead[", div.content) end
        div.classes:insert("am-lead")
        return div
      end
      -- destaque (pull-quote)
      if div.classes:includes("destaque") then
        if is_typst() then return typst_wrap("#am-destaque[", div.content) end
        div.classes:insert("am-destaque")
        return div
      end
      -- faixa de CTA no meio do texto: ::: {.cta title="..." button="..." url="..."}
      if div.classes:includes("cta") then
        local title  = div.attributes["title"]
        local button = div.attributes["button"]
        local url    = div.attributes["url"]
        if is_typst() then
          local args = {}
          if title then
            local t = pandoc.write(pandoc.Pandoc({ pandoc.Plain(md_inlines(title)) }), "typst")
            table.insert(args, "title: [" .. t:gsub("\n$", "") .. "]")
          end
          if button then table.insert(args, "button: " .. typst_string(button)) end
          if url then table.insert(args, "url: " .. typst_string(url)) end
          local sep = #args > 0 and (table.concat(args, ", ")) or ""
          return typst_wrap("#am-cta-faixa(" .. sep .. ")[", div.content)
        end
        local blocos = {}
        if title then
          table.insert(blocos, pandoc.Div({ pandoc.Para(md_inlines(title)) },
            pandoc.Attr("", { "am-cta-faixa-titulo" })))
        end
        for _, b in ipairs(div.content) do table.insert(blocos, b) end
        if button and url then
          table.insert(blocos, pandoc.Para({
            pandoc.Link({ pandoc.Str(button) }, url, "", pandoc.Attr("", { "am-botao" })) }))
        end
        return pandoc.Div(blocos, pandoc.Attr("", { "am-cta-faixa" }))
      end
      return nil
    end,

    CodeBlock = function(cb)
      -- Saída de código: ```{.saida} … ``` logo abaixo do bloco que a produz
      if not cb.classes:includes("saida") then return nil end
      if is_typst() then
        return pandoc.RawBlock("typst", "#am-saida(" .. typst_string_ml(cb.text) .. ")")
      end
      return pandoc.Div({
        pandoc.Plain({ pandoc.Span({ pandoc.Str("SAÍDA") }, pandoc.Attr("", { "am-saida-rotulo" })) }),
        pandoc.CodeBlock(cb.text),
      }, pandoc.Attr("", { "am-saida" }))
    end,

    Image = function(img)
      -- EPUB/HTML: figura SVG da marca -> PNG gerado pelo epub-prep.py (imagens/_epub-png/<nome>.png), se existir
      if is_typst() then return nil end
      local dir, nome = img.src:match("^(.-)([^/\\]+)%.svg$")
      if nome then
        local png = dir .. "_epub-png/" .. nome .. ".png"
        if file_exists(png) then img.src = png; return img end
      end
      return nil
    end,

    Header = function(el)
      -- partes e apêndices do livro no Typst (o Quarto marca o arquivo com bookItemType)
      if is_typst() and el.level == 1 then
        local fs = quarto.doc.file_metadata()
        if fs and fs.file and fs.file.bookItemType == "part" then
          local t = pandoc.utils.stringify(el.content)
          return pandoc.RawBlock("typst",
            "#pagebreak()\n#align(horizon + center)[#text(font: \"Space Grotesk\", weight: 700, size: 34pt)[" .. t .. "]]\n#pagebreak()")
        end
      end
      return nil
    end,

    Pandoc = function(doc)
      -- EPUB/HTML: páginas finais no fim do livro (o Typst as desenha no template)
      if is_typst() then return nil end
      doc.blocks:extend(paginas_finais(doc.meta))
      return doc
    end,
  }
}
