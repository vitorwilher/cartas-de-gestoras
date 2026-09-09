#!/usr/bin/env python3
"""Monta o layout Elementor das duas landings, via REST API.

O `_elementor_data` ACEITA escrita pela REST (testado em 09/09/2026); só a
leitura volta vazia. Por isso construímos as seções aqui em vez de copiar as da
página do livro.

Usa as cores GLOBAIS do site (primary #2B3551, secondary #0098DA), então a página
herda a identidade e acompanha qualquer mudança de tema.

Uso:
    python divulgacao/wordpress/montar_layout.py --dry-run
    python divulgacao/wordpress/montar_layout.py
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth
from dotenv import dotenv_values

ROI = Path(__file__).resolve().parents[3] / "ROI_Diagnostico"
ENV = dotenv_values(ROI / ".env")
BASE = ENV["WP_FRONT_URL"].rstrip("/")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
AUTH = HTTPBasicAuth(ENV["WP_FRONT_USER"], ENV["WP_FRONT_APP_PASSWORD"])

PAGINA_CAPTURA = 78391
PAGINA_OBRIGADO = 78388
PDF = "https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf"
WHATS = ("https://wa.me/5521971167250?text=Oi!%20Acabei%20de%20me%20inscrever%20na"
         "%20S%C3%ADntese%20das%20Cartas%20das%20Gestoras%20e%20quero%20receber"
         "%20o%20PDF%20por%20aqui.")


NAVY = "#2B3551"     # global "primary"
AZUL = "#0098DA"     # global "secondary"
CINZA = "#54595F"    # global "text"
IMG_GRAFICO = "https://analisemacro.com.br/wp-content/uploads/2026/09/cartas-gestoras-exercicio.png"
IMG_GRAFICO_ID = 78378
# Mesma foto que a landing do Livro Linguagem Econômica usa.
IMG_VITOR = "https://analisemacro.com.br/wp-content/uploads/2026/08/vitor-wilher-cientista-chefe.png"
IMG_VITOR_ID = 73691


def _id() -> str:
    return uuid.uuid4().hex[:7]


def _px(v):
    return {"unit": "px", "size": v, "sizes": []}


def _pad(t, r, bo, l):
    return {"unit": "px", "top": str(t), "right": str(r),
            "bottom": str(bo), "left": str(l), "isLinked": False}


def titulo(texto, tag="h2", cor=None, tamanho=34, align="left", peso="700", mb=0):
    s = {
        "title": texto, "header_size": tag, "align": align,
        "typography_typography": "custom",
        "typography_font_size": _px(tamanho),
        "typography_font_weight": peso,
        "typography_line_height": {"unit": "em", "size": 1.18, "sizes": []},
        "typography_letter_spacing": _px(-0.5),
    }
    if mb:
        s["_margin"] = _pad(0, 0, mb, 0)
    if cor:
        s["title_color"] = cor
    else:
        s["__globals__"] = {"title_color": "globals/colors?id=primary"}
    return {"id": _id(), "elType": "widget", "widgetType": "heading", "settings": s}


def texto(html, tamanho=17, cor=None, align=None):
    s = {
        "editor": html,
        "typography_typography": "custom",
        "typography_font_size": _px(tamanho),
        "typography_line_height": {"unit": "em", "size": 1.7, "sizes": []},
    }
    if align:
        s["align"] = align
    if cor:
        s["text_color"] = cor
    else:
        s["__globals__"] = {"text_color": "globals/colors?id=text"}
    return {"id": _id(), "elType": "widget", "widgetType": "text-editor", "settings": s}


def imagem(url, mid=None, largura=100):
    s = {
        "image": {"url": url, "id": mid} if mid else {"url": url},
        "image_size": "full",
        "width": {"unit": "%", "size": largura, "sizes": []},
        "image_border_radius": {"unit": "px", "top": "10", "right": "10",
                                "bottom": "10", "left": "10", "isLinked": True},
        "image_box_shadow_box_shadow_type": "yes",
        "image_box_shadow_box_shadow": {"horizontal": 0, "vertical": 12, "blur": 34,
                                        "spread": 0, "color": "rgba(43,53,81,0.14)"},
    }
    return {"id": _id(), "elType": "widget", "widgetType": "image", "settings": s}


def icone_texto(icone, titulo_txt, descricao):
    """Caixa com ícone grande + título + descrição. É o que dá ritmo visual."""
    return {
        "id": _id(), "elType": "widget", "widgetType": "icon-box",
        "settings": {
            "selected_icon": {"value": icone, "library": "fa-solid"},
            "title_text": titulo_txt,
            "description_text": descricao,
            "position": "top",
            "primary_color": AZUL,
            "icon_size": _px(30),
            "icon_space": _px(16),
            "title_typography_typography": "custom",
            "title_typography_font_size": _px(20),
            "title_typography_font_weight": "700",
            "description_typography_typography": "custom",
            "description_typography_font_size": _px(16),
            "description_typography_line_height": {"unit": "em", "size": 1.6, "sizes": []},
            "__globals__": {
                "title_color": "globals/colors?id=primary",
                "description_color": "globals/colors?id=text",
            },
        },
    }


def caixa(filhos, fundo="#FFFFFF", borda=True, pad=32):
    """Container-cartão: fundo, cantos arredondados e sombra suave."""
    s = {
        "content_width": "full",
        "padding": _pad(pad, pad, pad, pad),
        "background_background": "classic",
        "background_color": fundo,
        "border_radius": {"unit": "px", "top": "12", "right": "12",
                          "bottom": "12", "left": "12", "isLinked": True},
        "flex_gap": {"unit": "px", "size": 14, "column": "14", "row": "14"},
    }
    if borda:
        s["box_shadow_box_shadow_type"] = "yes"
        s["box_shadow_box_shadow"] = {"horizontal": 0, "vertical": 4, "blur": 22,
                                      "spread": 0, "color": "rgba(43,53,81,0.10)"}
    return {"id": _id(), "elType": "container", "settings": s, "elements": filhos}


def colunas(cols, gap=28, pesos=None):
    """Container flex em linha — as colunas viram empilhadas no celular."""
    filhos = []
    for i, c in enumerate(cols):
        # `width` em % e `content_width: full`: com width em px 0 o container
        # colapsava e as colunas empilhavam.
        filhos.append({
            "id": _id(), "elType": "container",
            "settings": {
                "content_width": "full",
                "width": {"unit": "%", "size": (pesos[i] if pesos else round(100 / max(len(cols), 1), 2)), "sizes": []},
                "width_mobile": {"unit": "%", "size": 100, "sizes": []},
                "flex_gap": {"unit": "px", "size": 12, "column": "12", "row": "12"},
            },
            "elements": c,
        })
    return {
        "id": _id(), "elType": "container",
        "settings": {
            "content_width": "full", "flex_direction": "row",
            "flex_gap": {"unit": "px", "size": gap, "column": str(gap), "row": str(gap)},
            "flex_direction_mobile": "column",
        },
        "elements": filhos,
    }


def numero(valor, rotulo):
    """Estatística em destaque — o número grande em azul."""
    return caixa([
        titulo(valor, tag="div", tamanho=42, cor=AZUL, align="center"),
        texto(f'<p style="text-align:center;margin:0">{rotulo}</p>', tamanho=15),
    ], fundo="#FFFFFF", pad=24)


def botao(rotulo, url, align="center", cor=None):
    return {
        "id": _id(), "elType": "widget", "widgetType": "button",
        "settings": {
            "text": rotulo,
            "link": {"url": url, "is_external": "true", "nofollow": "",
                     "custom_attributes": ""},
            "size": "lg", "align": align,
            "typography_typography": "custom",
            "typography_font_size": _px(19),
            "typography_font_weight": "700",
            "border_radius": {"unit": "px", "top": "8", "right": "8",
                              "bottom": "8", "left": "8", "isLinked": True},
            "text_padding": _pad(20, 44, 20, 44),
            "background_color": cor or AZUL,
            "button_box_shadow_box_shadow_type": "yes",
            "button_box_shadow_box_shadow": {"horizontal": 0, "vertical": 8, "blur": 20,
                                             "spread": 0, "color": "rgba(0,152,218,0.32)"},
        },
    }


def divisor():
    return {"id": _id(), "elType": "widget", "widgetType": "divider",
            "settings": {"weight": _px(3), "width": {"unit": "px", "size": 64, "sizes": []},
                         "color": AZUL, "align": "left",
                         "gap": _px(18)}}


def lista(itens, icone="fas fa-check"):
    return {
        "id": _id(), "elType": "widget", "widgetType": "icon-list",
        "settings": {
            "icon_list": [
                {"_id": _id(), "text": t,
                 "selected_icon": {"value": icone, "library": "fa-solid"}}
                for t in itens
            ],
            "space_between": _px(18),
            "icon_size": _px(17),
            "text_indent": _px(14),
            "icon_typography_typography": "custom",
            "icon_typography_font_size": _px(17),
            "__globals__": {
                "icon_color": "globals/colors?id=secondary",
                "text_color": "globals/colors?id=text",
            },
        },
    }


def formulario():
    """Widget Form do Elementor: nome, e-mail e telefone (todos obrigatórios).

    O `form_id` DEVE ser "cartasgestoras" — é por ele que a ponte PHP reconhece
    o submit. Com outro valor a ponte ignora em silêncio e o telefone se perde.

    A ação nativa "ConvertKit" do Elementor não é usada: ela só escreve email e
    first_name. Quem leva os dados ao Kit é a ponte (ver README).
    """
    return {
        "id": _id(), "elType": "widget", "widgetType": "form",
        "settings": {
            "form_name": "cartasgestoras",
            "form_id": "cartasgestoras",
            "form_fields": [
                {"_id": "nome", "field_type": "text", "field_label": "Nome",
                 "placeholder": "Seu nome", "required": "true", "width": "100",
                 "custom_id": "nome"},
                {"_id": "email", "field_type": "email", "field_label": "E-mail",
                 "placeholder": "seu@email.com", "required": "true", "width": "100",
                 "custom_id": "email"},
                {"_id": "telefone", "field_type": "tel", "field_label": "WhatsApp",
                 "placeholder": "(21) 90000-0000", "required": "true", "width": "100",
                 "custom_id": "telefone"},
            ],
            "button_text": "Quero receber a síntese",
            "button_size": "lg",
            "button_align": "stretch",
            "submit_actions": ["redirect"],
            "redirect_to": "https://analisemacro.com.br/conteudo/cartas-das-gestoras-obrigado/",
            "button_background_color": AZUL,
            "button_typography_typography": "custom",
            "button_typography_font_size": _px(19),
            "button_typography_font_weight": "700",
            "field_typography_typography": "custom",
            "field_typography_font_size": _px(17),
            "row_gap": _px(16),
        },
    }


def secao(filhos, fundo=None, pad_v=76, largura=1080, direcao="column"):
    s = {
        "content_width": "boxed",
        "boxed_width": _px(largura),
        "padding": _pad(pad_v, 24, pad_v, 24),
        "flex_gap": {"unit": "px", "size": 22, "column": "22", "row": "22"},
        "flex_direction": direcao,
    }
    if fundo:
        s["background_background"] = "classic"
        s["background_color"] = fundo
    return {"id": _id(), "elType": "container", "settings": s, "elements": filhos}


def layout_captura() -> list:
    return [
        secao([
            colunas([
                [
                    texto(f'<p style="color:{AZUL};font-weight:700;letter-spacing:1.6px;margin:0">SÍNTESE SEMANAL</p>', tamanho=14),
                    titulo("Leia as cartas das 12 maiores gestoras do Brasil sem ler as doze", tag="h1", tamanho=46, mb=6),
                    texto("<p>Toda semana, a síntese das cartas novas — a tese de cada casa, o mecanismo que a sustenta e onde o consenso do mercado racha. Com um exercício em Python que testa uma dessas teses com dado público, para você <strong>conferir em vez de acreditar</strong>.</p>", tamanho=19),
                    botao("Quero receber a síntese", "#form", align="left"),
                ],
                [imagem(IMG_GRAFICO, IMG_GRAFICO_ID)],
            ], gap=36, pesos=[42, 58]),
        ], fundo="#F4F7FA", pad_v=64),

        secao([
            colunas([[numero("12", "gestoras acompanhadas")],
                     [numero("1x", "por semana, toda terça")],
                     [numero("6s", "para rodar o exercício")]], gap=20),
        ], pad_v=48),

        secao([
            titulo("O que você recebe toda semana", align="center", mb=8),
            divisor(),
            colunas([
                [caixa([icone_texto("fas fa-lightbulb", "A tese e o mecanismo",
                    "Não o resumo do mês: a cadeia causal que faz a aposta se pagar, e a condição exata em que ela quebra.")])],
                [caixa([icone_texto("fas fa-code-branch", "Convergências e divergências",
                    "Onde as casas concordam, onde discordam, e o que a divergência revela sobre premissas diferentes.")])],
                [caixa([icone_texto("fab fa-python", "O exercício em Python",
                    "Código comentado que testa uma das teses com dado do Tesouro Direto e do Banco Central. Roda em segundos.")])],
            ]),
        ], fundo="#F4F7FA"),

        secao([
            colunas([
                [titulo("Por que ler as doze juntas", mb=6), divisor(),
                 texto("<p>Uma carta isolada mostra a visão de uma casa. Doze mostram onde o mercado brasileiro concorda — e onde a mesma leitura vira apostas incompatíveis.</p>")],
                [caixa([texto('<p style="margin:0"><strong>Um caso real, de setembro:</strong> três gestoras olhando dados diferentes — inadimplência, recuperações judiciais e reestruturações de crédito — descreveram o mesmo ciclo virando.</p><p style="margin:10px 0 0"><em>Nenhuma delas disse isso sozinha. O sinal só apareceu com as cartas lado a lado.</em></p>', tamanho=17)], fundo="#EAF6FC")],
            ]),
        ]),

        secao([
            titulo("Para quem é", align="center", mb=8),
            divisor(),
            colunas([
                [caixa([icone_texto("fas fa-chart-pie", "Analistas e gestores",
                    "Você já acompanha as cartas — aqui vê as teses lado a lado, com o mecanismo de cada uma exposto.")])],
                [caixa([icone_texto("fas fa-briefcase", "Profissionais de mercado",
                    "Lê duas ou três cartas por mês e sabe que está perdendo justamente a comparação.")])],
                [caixa([icone_texto("fas fa-terminal", "Quem programa em Python",
                    "Quer aplicar o que sabe a dados de mercado brasileiros, com código que roda de verdade.")])],
            ]),
        ], fundo="#F4F7FA"),

        secao([
            titulo("As gestoras acompanhadas", align="center", tamanho=30, mb=8),
            caixa([
                texto('<p style="text-align:center;font-size:19px;margin:0"><strong>Dynamo · IP Capital Partners · Alaska · Kapitalo · Adam Capital · Legacy Capital<br>Bahia Asset · Occam Brasil · JGP · Kinea · NEO Investimentos · Dahlia Capital</strong></p>'),
                texto('<p style="text-align:center;margin:12px 0 0">As cartas não têm cadência única: dez são mensais, e Dynamo e IP publicam ensaios temáticos irregulares — justamente os de maior densidade.</p>', tamanho=16),
            ]),
        ]),

        secao([
            colunas([
                [imagem(IMG_VITOR, IMG_VITOR_ID, largura=88)],
                [titulo("Quem escreve", mb=6), divisor(),
                 texto("<p><strong>Vítor Wilher</strong> — Cientista-Chefe da Análise Macro. Bacharel e Mestre em Economia pela UFF, com pós-graduação em LLMs e IA Generativa pela PUC-Rio e doutorado em Economia em curso na EPGE/FGV. Fundou a Análise Macro, por onde já passaram mais de 5.000 alunos.</p>"),
                 caixa([texto('<p style="margin:0;font-style:italic;font-size:17px">"Todo mês eu abria seis ou sete cartas e lia duas. O que se perde não é o conteúdo de cada uma — é a comparação, que é onde está o valor."</p>')], fundo="#EAF6FC", pad=22)],
            ], pesos=[32, 68]),
        ], fundo="#F4F7FA"),

        secao([
            titulo("Receba a síntese desta semana", align="center", tamanho=38, mb=8),
            texto('<p style="text-align:center;font-size:19px">Deixe seus dados e receba o PDF na hora.</p>'),
            caixa([formulario()], pad=40),
            texto('<p style="text-align:center"><small>Não é para você concordar com as gestoras. É para conseguir checar.</small></p>', tamanho=15),
        ], fundo="#F4F7FA", pad_v=80),
    ]


def layout_obrigado() -> list:
    """Um CTA só: o WhatsApp. O PDF vai por e-mail e como link discreto aqui.

    Dois botões lado a lado competiam entre si — e empilhados ficavam feios. O
    WhatsApp é o que interessa: é ele que abre a janela de 24h e permite a
    conversa. O PDF a pessoa recebe no e-mail de qualquer forma.
    """
    return [
        secao([
            titulo("Pronto. Sua inscrição está confirmada.", tag="h1",
                   tamanho=44, align="center", mb=6),
            texto('<p style="text-align:center;font-size:20px">A síntese desta semana '
                  'está a caminho do seu e-mail — e a próxima chega toda terça.</p>'),
        ], fundo="#F4F7FA", pad_v=72),

        secao([
            titulo("Quer receber também no WhatsApp?", align="center", tamanho=34, mb=8),
            texto('<p style="text-align:center;font-size:19px">Manda um <strong>"Oi"</strong> '
                  'que eu te envio o PDF por lá na hora — e, se quiser, a síntese de toda '
                  'semana chega no mesmo lugar.</p>'),
            botao('Mandar "Oi" no WhatsApp', WHATS, cor="#25D366"),
            texto('<p style="text-align:center;margin-top:14px"><small>É você quem inicia '
                  'a conversa — assim eu posso te responder sem ficar preso a mensagem '
                  'automática. Se preferir só o e-mail, é só ignorar este passo.</small></p>',
                  tamanho=15),
        ], pad_v=64),

        # SEM link do PDF aqui: por decisão do Vitor (09/09), o download chega só
        # pelo e-mail e pelo WhatsApp. A imagem fica como prévia do que vem.
        secao([
            titulo("O que vem no PDF", align="center", tamanho=30, mb=8),
            texto('<p style="text-align:center">Além da síntese das cartas, cada edição '
                  'traz um exercício em Python que testa uma das teses com dado público. '
                  'Roda em segundos — e você adapta para a tese que quiser checar.</p>'),
            imagem(IMG_GRAFICO, IMG_GRAFICO_ID),
            texto('<p style="text-align:center"><small>O gráfico acima saiu do exercício '
                  'da edição desta semana.</small></p>', tamanho=15),
        ], fundo="#F4F7FA"),
    ]


def publicar(page_id: int, layout: list, dry: bool) -> None:
    dados = json.dumps(layout, ensure_ascii=False)
    print(f"  página {page_id}: {len(layout)} seções, {len(dados)} chars")
    if dry:
        return
    r = requests.post(
        f"{BASE}/wp-json/wp/v2/pages/{page_id}", auth=AUTH,
        headers={"User-Agent": UA},
        json={"meta": {"_elementor_data": dados,
                       "_elementor_edit_mode": "builder",
                       "_elementor_template_type": "wp-page"}},
        timeout=120,
    )
    print(f"    HTTP {r.status_code}")
    if not r.ok:
        print("   ", r.text[:300], file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("Landing de captura:")
    publicar(PAGINA_CAPTURA, layout_captura(), args.dry_run)
    print("Página de obrigado:")
    publicar(PAGINA_OBRIGADO, layout_obrigado(), args.dry_run)
    if args.dry_run:
        print("\n[dry-run] Nada foi enviado.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
