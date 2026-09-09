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


def _fig_para_uri(fig) -> str:
    """Fecha a figura e devolve o PNG como data-URI, para embutir no HTML."""
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _estilo(ax):
    """Aplica o visual claro da casa: sem molduras, grade suave, texto em INK_SOFT."""
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(LINE)
    ax.tick_params(labelsize=15, colors=INK_SOFT)
    ax.grid(axis="y", color=LINE, lw=1.2)
    ax.set_axisbelow(True)


def dados_do_exercicio() -> dict:
    """Roda a parte de DADOS do exercício da edição mais recente.

    Os gráficos do carrossel precisam mostrar os MESMOS números do PDF — se o
    carrossel disser 48 bps e o documento disser outra coisa, a inconsistência é
    checável por quem lê os dois. Por isso reexecutamos o próprio código do
    exercício, cortando antes da seção de gráfico (que é paisagem e não serve
    para o formato retrato do Instagram).
    """
    import contextlib
    import io as _io
    import re

    digests = sorted((RAIZ / "digests" / "resumo").glob("resumo-*.qmd"), reverse=True)
    if not digests:
        raise SystemExit("Nenhuma edição em digests/resumo/")
    md = digests[0].read_text(encoding="utf-8")
    achado = re.search(r"```python\n(.*?)```", md, re.DOTALL)
    if not achado:
        raise SystemExit(f"{digests[0].name} não tem bloco python no exercício")

    codigo = achado.group(1)
    marca = "# 5. Gráfico"
    codigo = codigo[:codigo.index(marca)] if marca in codigo else codigo

    ns: dict = {"__name__": "__main__"}
    with contextlib.redirect_stdout(_io.StringIO()):
        exec(compile(codigo, "exercicio", "exec"), ns)

    # O exercício é escrito pelo modelo a cada edição, então os nomes das variáveis
    # variam. Normalizamos o que os gráficos usam, com alternativas conhecidas, e
    # falhamos alto se algo essencial não estiver lá — melhor do que um KeyError
    # no meio do render.
    alias = {
        "atual_bps": ("atual_bps", "atual", "inclinacao_atual"),
        "percentil": ("percentil", "percentil_hist"),
        "mediana": ("mediana", "mediana_bps"),
        "p10": ("p10",), "p90": ("p90",),
        "taxa_curta": ("taxa_curta",), "taxa_longa": ("taxa_longa",),
        "TENOR_CURTO": ("TENOR_CURTO",), "TENOR_LONGO": ("TENOR_LONGO",),
        "hist": ("hist",), "curva_hoje": ("curva_hoje",), "ultima": ("ultima",),
    }
    dados = {}
    faltando = []
    for chave, candidatos in alias.items():
        for nome in candidatos:
            if nome in ns:
                dados[chave] = ns[nome]
                break
        else:
            faltando.append(chave)
    if faltando:
        raise SystemExit(
            f"O exercício de {digests[0].name} não expõe: {', '.join(faltando)}. "
            "Os gráficos do carrossel dependem dessas variáveis — ajuste os alias "
            "em dados_do_exercicio()."
        )
    return dados


def grafico_curva(d: dict) -> str:
    """A curva pré de hoje, com a inclinação entre os dois vértices anotada."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    curva = d["curva_hoje"].sort_values("prazo")
    x = list(curva["prazo"])
    y = list(curva["taxa"])

    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    ax.plot(x, y, color=BLUE, lw=4, marker="o", markersize=10,
            solid_capstyle="round", zorder=3)

    tc, tl = d["TENOR_CURTO"], d["TENOR_LONGO"]
    yc, yl = d["taxa_curta"], d["taxa_longa"]
    ax.annotate("", xy=(tl, yl), xytext=(tl, yc),
                arrowprops=dict(arrowstyle="<->", color=NAVY, lw=2.5))
    ax.annotate(f"+{d['atual_bps']:.0f} bps", (tl, (yc + yl) / 2),
                xytext=(tl - 3.4, (yc + yl) / 2), fontsize=19,
                color=NAVY, fontweight="bold", va="center")
    for t, v in ((tc, yc), (tl, yl)):
        ax.plot([t], [v], "o", color=NAVY, markersize=12, zorder=4)
        ax.axvline(t, color=LINE, lw=1.4, zorder=1)

    _estilo(ax)
    ax.set_xlabel("prazo até o vencimento (anos)", fontsize=16, color=INK_SOFT)
    ax.set_ylabel("taxa (% a.a.)", fontsize=16, color=INK_SOFT)
    ax.set_title(f"Curva prefixada em {d['ultima']:%d/%m/%Y}", fontsize=19,
                 color=NAVY, fontweight="bold", pad=16)
    return _fig_para_uri(fig)


def grafico_historico(d: dict) -> str:
    """A inclinação no tempo, com a faixa 10-90% e o ponto de hoje destacado."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    hist = d["hist"]
    x = hist.index
    y = hist["inclinacao_bps"]

    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    ax.axhspan(d["p10"], d["p90"], color=BLUE, alpha=0.10, zorder=1)
    ax.plot(x, y, color=BLUE, lw=2, zorder=3)
    ax.axhline(d["mediana"], color=MUTED, lw=1.6, linestyle="--", zorder=2)
    ax.plot([x[-1]], [d["atual_bps"]], "o", color=NAVY, markersize=16, zorder=5)
    # Rótulo perto do ponto: com xytext em fração dos eixos a linha atravessava o
    # gráfico inteiro e cruzava a série.
    ax.annotate(f"hoje: +{d['atual_bps']:.0f} bps\npercentil {d['percentil']:.0f}%",
                (x[-1], d["atual_bps"]),
                xytext=(-30, -95), textcoords="offset points",
                fontsize=17, color=NAVY, fontweight="bold", ha="right",
                arrowprops=dict(arrowstyle="-", color=NAVY, lw=1.6,
                                connectionstyle="arc3,rad=0.2"))

    _estilo(ax)
    ax.set_ylabel("inclinação (pontos-base)", fontsize=16, color=INK_SOFT)
    ax.set_title(f"Inclinação {d['TENOR_LONGO']:.0f}a − {d['TENOR_CURTO']:.0f}a "
                 f"desde {x[0]:%Y}", fontsize=19, color=NAVY,
                 fontweight="bold", pad=16)
    return _fig_para_uri(fig)


def slides(d: dict) -> list[dict]:
    """Os 9 slides. Abre com CENA (nível 1-2 de consciência), fecha em salvamento.

    Bullets, não parágrafos: no feed o texto compete com o polegar. Os dois
    gráficos são os MESMOS do exercício da edição, redesenhados em retrato.

    Sem preço e sem oferta — o público do Instagram está no topo do funil, e
    entregar nível 5 a quem está no 2 é o erro documentado que rendeu 174
    mensagens e zero respostas na campanha de Claude Code T2.
    """
    bps = f"{d['atual_bps']:.0f}"
    pct = f"{d['percentil']:.0f}"
    return [
        {
            "kind": "capa",
            "hook": "Quatro gestoras leram a *mesma* inflação. Duas fizeram a aposta oposta.",
            "src": grafico_historico(d),
        },
        {
            "kind": "lista",
            "title": "No que elas *concordam*",
            "variant": "check",
            "items": [
                "Núcleos de serviços ainda pressionados",
                "Expectativas com viés de alta",
                "Atividade desacelerando",
                "Eleição empatada",
            ],
        },
        {
            "kind": "lista",
            "title": "Onde *racha*: o Copom",
            "variant": "diamond",
            "items": [
                "*Bahia, Occam e Legacy:* o ciclo de cortes segue",
                "*Kinea:* pausa, até haver clareza sobre o orçamento",
                "Mesmo diagnóstico. Conclusão oposta.",
            ],
        },
        {
            "kind": "definicao",
            "title": "A diferença não é sobre inflação",
            "rows": [
                {"term": "Legacy e Occam", "desc": "o BC reage aos dados de atividade"},
                {"term": "Kinea", "desc": "o BC reage à incerteza fiscal pós-eleitoral"},
            ],
        },
        {
            "kind": "lista",
            "title": "E isso *custa dinheiro*",
            "variant": "diamond",
            "items": [
                "Bahia e Occam carregam o mesmo trade",
                "*Steepener:* aposta em que o juro longo sobe mais que o curto",
                "A pausa da Kinea é o cenário em que a perna curta perde",
            ],
        },
        {
            "kind": "capa",
            "hook": "Dá para medir *quanto* dessa aposta já está no preço 👇",
            "hint": False,
            "src": grafico_curva(d),
        },
        {
            "kind": "dado",
            "value": f"+{bps} bps",
            "label": f"a inclinação da curva hoje — percentil {pct} desde 2010",
            "note": "Nem esticada, nem comprimida. O steepener não está barato na entrada.",
        },
        {
            "kind": "lista",
            "title": "Por que ler as *doze* juntas",
            "variant": "diamond",
            "items": [
                "Uma carta mostra a visão de uma casa",
                "Doze mostram onde o mercado concorda",
                "E onde a mesma leitura vira apostas incompatíveis",
            ],
        },
        {
            "kind": "cta",
            "title": "Quer a síntese desta semana?",
            "paragraph": f"Comenta *{PALAVRA_CHAVE}* que eu mando no direct. E me conta: qual gestora você acompanha de verdade?",
            "cta": f"Comente {PALAVRA_CHAVE}",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--so-html", action="store_true", help="não rasteriza os PNGs")
    args = parser.parse_args()

    from social.carousel_post_html import build

    print("Rodando o exercício da edição para obter os dados...")
    dados = dados_do_exercicio()
    print(f"  inclinação {dados['atual_bps']:.0f} bps, percentil {dados['percentil']:.0f}")

    SAIDA.mkdir(parents=True, exist_ok=True)
    lista = slides(dados)
    html = build(lista, fmt="post")
    destino = SAIDA / "carrossel.html"
    destino.write_text(html, encoding="utf-8")
    print(f"HTML: {destino} ({len(lista)} slides)")

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
