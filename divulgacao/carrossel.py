#!/usr/bin/env python3
"""Monta o carrossel de Instagram da edição — HTML + PNGs 1080x1350.

Reaproveita o design system de carrossel do ../ROI_Diagnostico
(`social/carousel_post_html.py` para o HTML, `social/render.js` para rasterizar).
Nada aqui publica: gera os arquivos e para. A publicação é do Vitor, e o fluxo
do ManyChat precisa existir no painel ANTES do post ir ao ar — quem comenta a
palavra-chave antes disso não recebe nada, e o lead se perde em silêncio.

Uso:
    python divulgacao/carrossel.py            # gera HTML + PNGs
    python divulgacao/carrossel.py --so-html  # só o HTML (sem Chrome)
"""

from __future__ import annotations

import argparse
import base64
import io
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ROI = RAIZ.parent / "ROI_Diagnostico"
SAIDA = RAIZ / "divulgacao" / "carrossel"

sys.path.insert(0, str(ROI))

# Paleta do design claro da casa (espelha social/carousel_charts.py).
NAVY = "#0A1A3C"
BLUE = "#1CA0D8"
INK_SOFT = "#3A4757"
MUTED = "#8894A5"
LINE = "#E6EAF0"

PALAVRA_CHAVE = "GESTORAS"


def grafico_copom() -> str:
    """Gráfico da capa: onde as casas divergem sobre o Copom.

    Ilustração didática do racha — três casas veem o ciclo seguindo, uma vê
    pausa. NÃO é projeção: mostra o CONCEITO de duas trajetórias de Selic.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    meses = list(range(7))
    rotulos = ["set", "nov", "jan", "mar", "mai", "jul", "set"]
    ciclo = [14.00, 13.75, 13.50, 13.25, 13.00, 12.75, 12.50]   # cortes seguem
    pausa = [14.00, 14.00, 14.00, 13.75, 13.50, 13.25, 13.00]   # pausa e retoma

    fig, ax = plt.subplots(figsize=(7.2, 6.0))
    ax.plot(meses, ciclo, color=BLUE, lw=5, marker="o", markersize=9,
            solid_capstyle="round", zorder=3, label="Bahia · Occam · Legacy")
    ax.plot(meses, pausa, color=NAVY, lw=5, marker="o", markersize=9,
            linestyle="--", solid_capstyle="round", zorder=3, label="Kinea")
    ax.fill_between(meses, ciclo, pausa, color=BLUE, alpha=0.10, zorder=1)

    ax.annotate("a pausa", (2, 14.00), (2.15, 14.22), fontsize=15,
                color=NAVY, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.2))

    ax.set_xticks(meses)
    ax.set_xticklabels(rotulos, fontsize=13, color=INK_SOFT)
    ax.set_ylabel("Selic (% a.a.)", fontsize=15, color=INK_SOFT)
    ax.tick_params(axis="y", labelsize=13, colors=INK_SOFT)
    ax.set_ylim(12.2, 14.6)
    ax.grid(axis="y", color=LINE, lw=1.2)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(LINE)
    leg = ax.legend(fontsize=13, frameon=False, loc="lower left")
    for t in leg.get_texts():
        t.set_color(INK_SOFT)
    ax.set_title("Duas leituras da mesma inflação", fontsize=17,
                 color=NAVY, fontweight="bold", pad=14)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def slides() -> list[dict]:
    """Os 8 slides. Abre com CENA (nível 1-2 de consciência), fecha em salvamento.

    Sem preço e sem oferta: o público do Instagram está no topo do funil, e
    entregar nível 5 a quem está no 2 é o erro documentado que rendeu 174
    mensagens e zero respostas na campanha de Claude Code T2.
    """
    return [
        {
            "kind": "capa",
            "hook": "Quatro gestoras leram a *mesma* inflação. Duas chegaram a apostas opostas.",
            "src": grafico_copom(),
        },
        {
            "kind": "texto",
            "title": "O consenso",
            "paragraphs": [
                "Bahia, Occam, Kinea e Legacy publicaram carta em agosto e concordam no diagnóstico: núcleos de serviços pressionados, expectativas com viés de alta, atividade desacelerando e eleição empatada.",
                "Concordam até nos juros longos globais — fiscal e capex de IA disputando o mesmo capital.",
            ],
        },
        {
            "kind": "texto",
            "title": "Onde racha",
            "paragraphs": [
                "*O Copom.* Bahia, Occam e Legacy veem o ciclo de cortes seguindo. A Kinea vê pausa — \"para preservar margem de manobra até que haja clareza sobre o orçamento\".",
                "Mesmo diagnóstico. Conclusão oposta.",
            ],
        },
        {
            "kind": "definicao",
            "title": "Por que a diferença não é sobre inflação",
            "rows": [
                {"term": "Legacy e Occam", "desc": "o BC reage aos dados de atividade, como sinalizou"},
                {"term": "Kinea", "desc": "o BC reage à incerteza fiscal pós-eleitoral"},
            ],
        },
        {
            "kind": "texto",
            "title": "E isso custa dinheiro",
            "paragraphs": [
                "Bahia e Occam carregam o mesmo trade: *steepener* doméstico — aposta em que o juro longo sobe mais que o curto.",
                "A pausa que a Kinea projeta é exatamente o cenário em que a perna curta desse trade perde.",
            ],
        },
        {
            "kind": "dado",
            "value": "−3,7%",
            "label": "o que juros renderam em 12 meses no Bahia Mutá",
            "note": "No Occam Retorno Absoluto, Juros Local: −1,99% no ano. A curva brasileira já cobrou caro de quem esteve posicionado nela.",
        },
        {
            "kind": "texto",
            "title": "É isto que aparece lendo as cartas juntas",
            "paragraphs": [
                "Uma carta isolada mostra a visão de uma casa. Quatro mostram onde o mercado concorda — e onde a mesma leitura vira apostas incompatíveis.",
                "Toda semana eu leio as cartas das 12 maiores gestoras do Brasil e comparo as teses.",
            ],
        },
        {
            "kind": "cta",
            "title": "Quer a síntese desta semana?",
            "paragraph": f"Comenta *{PALAVRA_CHAVE}* aqui embaixo que eu te mando no direct. E me conta: qual gestora você acompanha de verdade?",
            "cta": f"Comente {PALAVRA_CHAVE}",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--so-html", action="store_true", help="não rasteriza os PNGs")
    args = parser.parse_args()

    from social.carousel_post_html import build

    SAIDA.mkdir(parents=True, exist_ok=True)
    html = build(slides(), fmt="post")
    destino = SAIDA / "carrossel.html"
    destino.write_text(html, encoding="utf-8")
    print(f"HTML: {destino} ({len(slides())} slides)")

    if args.so_html:
        return 0

    render = ROI / "social" / "render.js"
    if not render.exists():
        print(f"[erro] render.js não encontrado em {render}", file=sys.stderr)
        return 1
    proc = subprocess.run(
        ["node", str(render), str(destino), str(SAIDA)],
        cwd=ROI, capture_output=True, text=True,
    )
    print(proc.stdout.strip() or proc.stderr.strip()[:500])
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
