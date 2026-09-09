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

PAGINA_CAPTURA = 78368
PAGINA_OBRIGADO = 78374
PDF = "https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf"
WHATS = ("https://wa.me/5521971167250?text=Oi!%20Acabei%20de%20me%20inscrever%20na"
         "%20S%C3%ADntese%20das%20Cartas%20das%20Gestoras%20e%20quero%20receber"
         "%20o%20PDF%20por%20aqui.")


def _id() -> str:
    return uuid.uuid4().hex[:7]


def titulo(texto, tag="h2", cor=None, tamanho=32, align="left", peso="700"):
    s = {
        "title": texto, "header_size": tag, "align": align,
        "typography_typography": "custom",
        "typography_font_size": {"unit": "px", "size": tamanho, "sizes": []},
        "typography_font_weight": peso,
        "typography_line_height": {"unit": "em", "size": 1.2, "sizes": []},
    }
    if cor:
        s["title_color"] = cor
    else:
        s["__globals__"] = {"title_color": "globals/colors?id=primary"}
    return {"id": _id(), "elType": "widget", "widgetType": "heading", "settings": s}


def texto(html, tamanho=17, cor=None):
    s = {
        "editor": html,
        "typography_typography": "custom",
        "typography_font_size": {"unit": "px", "size": tamanho, "sizes": []},
        "typography_line_height": {"unit": "em", "size": 1.65, "sizes": []},
    }
    if cor:
        s["text_color"] = cor
    else:
        s["__globals__"] = {"text_color": "globals/colors?id=text"}
    return {"id": _id(), "elType": "widget", "widgetType": "text-editor", "settings": s}


def lista(itens, icone="fas fa-check"):
    return {
        "id": _id(), "elType": "widget", "widgetType": "icon-list",
        "settings": {
            "icon_list": [
                {"_id": _id(), "text": t,
                 "selected_icon": {"value": icone, "library": "fa-solid"}}
                for t in itens
            ],
            "space_between": {"unit": "px", "size": 16, "sizes": []},
            "icon_size": {"unit": "px", "size": 16, "sizes": []},
            "icon_typography_typography": "custom",
            "icon_typography_font_size": {"unit": "px", "size": 17, "sizes": []},
            "text_indent": {"unit": "px", "size": 12, "sizes": []},
            "__globals__": {
                "icon_color": "globals/colors?id=secondary",
                "text_color": "globals/colors?id=text",
            },
        },
    }


def botao(rotulo, url, tamanho="lg", align="left"):
    return {
        "id": _id(), "elType": "widget", "widgetType": "button",
        "settings": {
            "text": rotulo,
            "link": {"url": url, "is_external": "true", "nofollow": ""},
            "size": tamanho, "align": align,
            "typography_typography": "custom",
            "typography_font_size": {"unit": "px", "size": 18, "sizes": []},
            "typography_font_weight": "600",
            "border_radius": {"unit": "px", "top": "6", "right": "6",
                              "bottom": "6", "left": "6", "isLinked": True},
            "text_padding": {"unit": "px", "top": "18", "right": "38",
                             "bottom": "18", "left": "38", "isLinked": False},
            "__globals__": {"background_color": "globals/colors?id=secondary"},
        },
    }


def secao(filhos, fundo=None, pad_v=64, largura=980):
    s = {
        "content_width": "boxed",
        "boxed_width": {"unit": "px", "size": largura, "sizes": []},
        "padding": {"unit": "px", "top": str(pad_v), "right": "24",
                    "bottom": str(pad_v), "left": "24", "isLinked": False},
        "flex_gap": {"unit": "px", "size": 20, "column": "20", "row": "20"},
    }
    if fundo:
        s["background_background"] = "classic"
        s["background_color"] = fundo
    return {"id": _id(), "elType": "container", "settings": s, "elements": filhos}


def layout_captura() -> list:
    return [
        # Hero
        secao([
            titulo("Leia as cartas das 12 maiores gestoras do Brasil sem ler as doze",
                   tag="h1", tamanho=44),
            texto("<p>Toda semana, a síntese das cartas novas — a tese de cada casa, "
                  "o mecanismo que a sustenta, e onde o consenso do mercado racha. "
                  "Com um exercício em Python que testa uma dessas teses com dado "
                  "público, para você <strong>conferir em vez de acreditar</strong>.</p>",
                  tamanho=19),
            texto("<p><em>Para quem lê carta de gestor e quer saber o que sustenta "
                  "cada aposta.</em></p>", tamanho=16),
        ], fundo="#F7F9FB", pad_v=72),

        # O que você recebe
        secao([
            titulo("O que você recebe toda semana"),
            lista([
                "A tese de cada gestora e o mecanismo econômico que a sustenta",
                "A condição em que cada tese quebra, com os riscos que a própria gestora aponta",
                "Convergências e divergências: onde as casas concordam e onde discordam",
                "Um exercício em Python que testa uma das teses com dado público",
                "O código completo, comentado e pronto para rodar",
                "O link para a carta original de cada gestora citada",
            ]),
        ]),

        # Por que ler as doze
        secao([
            titulo("Por que ler as doze juntas"),
            texto("<p>Uma carta isolada mostra a visão de uma casa. Doze mostram onde "
                  "o mercado brasileiro concorda — e onde a mesma leitura vira apostas "
                  "incompatíveis.</p>"
                  "<p>Num exemplo real de setembro: três gestoras olhando dados "
                  "diferentes — inadimplência, recuperações judiciais e reestruturações "
                  "de crédito — descreveram o mesmo ciclo virando. Nenhuma delas disse "
                  "isso sozinha. O sinal só apareceu com as cartas lado a lado.</p>"),
        ], fundo="#F7F9FB"),

        # Para quem é
        secao([
            titulo("Para quem é"),
            lista([
                "Analistas e gestores que acompanham as cartas e querem ver as teses lado a lado",
                "Profissionais de mercado que leem duas ou três por mês e sabem que perdem a comparação",
                "Economistas que querem testar em código o que leem em prosa",
                "Quem já usa Python e quer aplicá-lo a dados de mercado brasileiros",
            ], icone="fas fa-user"),
        ]),

        # Gestoras
        secao([
            titulo("As gestoras acompanhadas", tamanho=28),
            texto("<p><strong>Dynamo · IP Capital Partners · Alaska · Kapitalo · "
                  "Adam Capital · Legacy Capital · Bahia Asset · Occam Brasil · JGP · "
                  "Kinea · NEO Investimentos · Dahlia Capital</strong></p>"
                  "<p>As cartas não têm cadência única: dez são mensais, e Dynamo e IP "
                  "publicam ensaios temáticos irregulares — justamente os de maior "
                  "densidade. A síntese cobre o que for publicado na semana.</p>"),
        ], fundo="#F7F9FB"),

        # Autor
        secao([
            titulo("Quem escreve"),
            texto("<p><strong>Vítor Wilher</strong> — Cientista-Chefe da Análise Macro. "
                  "Bacharel e Mestre em Economia pela UFF, com pós-graduação em LLMs e "
                  "IA Generativa pela PUC-Rio e doutorado em Economia em curso na "
                  "EPGE/FGV. Fundou a Análise Macro, por onde já passaram mais de "
                  "5.000 alunos.</p>"
                  "<blockquote><p>Todo mês eu abria seis ou sete cartas e lia duas. O "
                  "que se perde não é o conteúdo de cada uma — é a comparação, que é "
                  "onde está o valor. O exercício em Python existe porque ler a tese não "
                  "basta: é preciso conseguir medir se ela já está no preço.</p>"
                  "</blockquote>"),
        ]),

        # Formulário
        secao([
            titulo("Receba a síntese desta semana", align="center", tamanho=34),
            texto('<p style="text-align:center">Deixe seus dados e receba o PDF na hora.</p>'),
            texto('<p style="text-align:center;color:#B00020"><strong>[ARRASTE AQUI O '
                  'WIDGET FORM DO ELEMENTOR — id do formulário: cartasgestoras, campos '
                  'nome/email/telefone, redirect para /conteudo/cartas-das-gestoras-obrigado/]'
                  '</strong></p>'),
            texto('<p style="text-align:center"><small>Não é para você concordar com as '
                  'gestoras. É para conseguir checar.</small></p>'),
        ], fundo="#F7F9FB", pad_v=72),
    ]


def layout_obrigado() -> list:
    return [
        secao([
            titulo("Pronto. Sua inscrição está confirmada.", tag="h1",
                   tamanho=42, align="center"),
            texto('<p style="text-align:center">A síntese desta semana já está '
                  'disponível — e a próxima chega no seu e-mail toda terça.</p>',
                  tamanho=19),
        ], fundo="#F7F9FB", pad_v=72),

        secao([
            titulo("Baixe a edição desta semana", align="center"),
            texto('<p style="text-align:center">O PDF traz a síntese das cartas e o '
                  'exercício em Python da semana.</p>'),
            botao("Baixar a síntese em PDF", PDF, align="center"),
        ]),

        secao([
            titulo("Quer receber também no WhatsApp?", align="center"),
            texto('<p style="text-align:center">Manda um <strong>"Oi"</strong> no nosso '
                  'WhatsApp que eu te envio o PDF por lá — e, se quiser, a síntese de '
                  'toda semana chega no mesmo lugar.</p>'),
            botao('Mandar "Oi" no WhatsApp', WHATS, align="center"),
            texto('<p style="text-align:center"><small>É você quem inicia a conversa — '
                  'assim eu posso te responder sem ficar preso a mensagem automática. '
                  'Se preferir só o e-mail, é só ignorar este passo.</small></p>',
                  tamanho=15),
        ], fundo="#F7F9FB"),

        secao([
            titulo("Enquanto isso", tamanho=28),
            texto("<p>Abra o PDF na seção <em>Exercício da semana</em>: lá tem o código "
                  "Python que testa uma das teses das gestoras com dado público. Roda em "
                  "segundos, e você adapta para a tese que quiser checar.</p>"),
        ]),
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
