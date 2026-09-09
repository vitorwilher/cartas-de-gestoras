#!/usr/bin/env python3
"""Gera a arte 1200x627 para o LinkedIn, com o gráfico real da edição.

O LinkedIn é outro público que o Instagram: menos "arraste para ver", mais
"isto aqui é sério". Por isso a arte é UMA peça horizontal, com o gráfico
ocupando metade e o argumento do lado — não um carrossel.

Reaproveita `dados_do_exercicio()` do carrossel, então os números são os mesmos
do PDF e do post do Instagram.

Uso:
    python divulgacao/linkedin.py            # gera HTML + PNG
    python divulgacao/linkedin.py --so-html
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
SAIDA = RAIZ / "divulgacao" / "linkedin"

sys.path.insert(0, str(RAIZ / "divulgacao"))
sys.path.insert(0, str(ROI))

from carrossel import (  # noqa: E402
    BLUE, INK_SOFT, LINE, MUTED, NAVY, dados_do_exercicio,
)

W, H = 1200, 627


def grafico_horizontal(d: dict) -> str:
    """A série da inclinação, em proporção larga e com o ponto de hoje no centro
    da atenção. Mesma medida do PDF e do carrossel."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    hist = d["hist"]
    x, y = hist.index, hist["inclinacao_bps"]
    atual, p10, p90 = d["atual_bps"], d["p10"], d["p90"]

    fig, ax = plt.subplots(figsize=(7.4, 5.4))
    ax.axhspan(p10, p90, color=BLUE, alpha=0.09, zorder=1)
    ax.plot(x, y, color=BLUE, lw=2.2, zorder=3)
    ax.axhline(d["mediana"], color=MUTED, lw=1.6, linestyle=(0, (6, 5)), zorder=2)
    ax.plot([x[-1]], [atual], "o", color="white", markersize=22, zorder=5)
    ax.plot([x[-1]], [atual], "o", color=NAVY, markersize=15, zorder=6)
    ax.annotate(f"hoje: +{atual:.0f} bps", (x[-1], atual),
                xytext=(-12, 74), textcoords="offset points",
                fontsize=20, color=NAVY, fontweight="bold", ha="right",
                arrowprops=dict(arrowstyle="-", color=NAVY, lw=1.8,
                                connectionstyle="arc3,rad=-0.25"))

    for lado in ("top", "right", "left", "bottom"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(labelsize=16, colors=MUTED, length=0, pad=8)
    ax.grid(axis="y", color=LINE, lw=1.3)
    ax.set_axisbelow(True)
    ax.yaxis.tick_right()
    ax.margins(x=0.02)
    ax.set_yticks([0, 100, 200, 300])
    ax.set_yticklabels(["0", "100", "200", "300 bps"])
    ax.set_title("Inclinação da curva: 7 anos − 2 anos", fontsize=20,
                 color=NAVY, fontweight="bold", loc="left", pad=32)
    ax.text(0, 1.04, "exemplo do exercício desta semana",
            transform=ax.transAxes, fontsize=15, color=MUTED, va="bottom")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _logo() -> str:
    from social.carousel_post_html import _logo_data_uri
    return _logo_data_uri()


def html(d: dict) -> str:
    """A arte vende o PRODUTO, não a edição.

    O objetivo do post é a captura no ConvertKit, então a peça precisa dizer o
    que a pessoa passa a receber toda semana — não a manchete de uma edição, que
    envelhece no dia seguinte e não se sustenta se a composição de gestoras mudar
    (a Kinea, por exemplo, caiu do PDF de 09/09 por rate limit na coleta).

    O gráfico continua: é a prova visual de que existe código de verdade por trás.
    Mas entra como amostra do que se recebe, não como o assunto.
    """
    bps = f"{d['atual_bps']:.0f}"
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  .card {{ width:{W}px; height:{H}px; background:#FFFFFF; display:flex;
           font-family:'Inter','Helvetica Neue',Arial,sans-serif; overflow:hidden; }}
  .esq {{ width:50%; padding:48px 36px 44px 56px; display:flex;
          flex-direction:column; justify-content:space-between; }}
  .dir {{ width:50%; display:flex; align-items:center; justify-content:center;
          padding:26px 40px 26px 6px; background:#FBFCFD; }}
  .dir img {{ width:100%; height:auto; }}
  .marca {{ display:flex; align-items:center; gap:12px; }}
  .marca img {{ width:36px; height:36px; }}
  .marca span {{ font-size:18px; font-weight:700; color:{NAVY}; letter-spacing:-.2px; }}
  .kicker {{ font-size:13px; font-weight:700; color:{BLUE}; letter-spacing:1.7px;
             text-transform:uppercase; margin-bottom:12px; }}
  h1 {{ font-size:37px; line-height:1.14; color:{NAVY}; font-weight:700;
        letter-spacing:-.6px; }}
  h1 em {{ font-style:normal; color:{BLUE}; }}
  ul {{ list-style:none; margin-top:20px; }}
  li {{ font-size:18px; line-height:1.36; color:{INK_SOFT}; margin-bottom:11px;
        display:flex; gap:11px; align-items:flex-start; }}
  li b {{ color:{NAVY}; font-weight:600; }}
  .dot {{ width:8px; height:8px; border-radius:50%; background:{BLUE};
          margin-top:8px; flex:0 0 8px; }}
  .pe {{ font-size:15px; color:{MUTED}; border-top:1px solid {LINE}; padding-top:13px; }}
</style></head><body>
<div class="card">
  <div class="esq">
    <div class="marca"><img src="{_logo()}"><span>Análise Macro</span></div>
    <div>
      <div class="kicker">Síntese semanal</div>
      <h1>As cartas das 12 maiores gestoras do Brasil,<br><em>destrinchadas em Python.</em></h1>
      <ul>
        <li><span class="dot"></span><span>A <b>tese de cada casa</b> e o mecanismo que a sustenta</span></li>
        <li><span class="dot"></span><span>Onde o consenso se forma — e <b>onde racha</b></span></li>
        <li><span class="dot"></span><span>Um <b>exercício em Python</b> que testa uma das teses</span></li>
      </ul>
    </div>
    <div class="pe">Dynamo · IP · Alaska · Kapitalo · Adam · Legacy · Bahia · Occam · JGP · Kinea · NEO · Dahlia</div>
  </div>
  <div class="dir"><img src="{grafico_horizontal(d)}"></div>
</div>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--so-html", action="store_true")
    args = parser.parse_args()

    print("Rodando o exercício da edição para obter os dados...")
    d = dados_do_exercicio()
    print(f"  inclinação {d['atual_bps']:.0f} bps, percentil {d['percentil']:.0f}")

    SAIDA.mkdir(parents=True, exist_ok=True)
    destino = SAIDA / "linkedin.html"
    destino.write_text(html(d), encoding="utf-8")
    print(f"HTML: {destino}")
    if args.so_html:
        return 0

    render = ROI / "social" / "render.js"
    proc = subprocess.run(
        ["node", str(render), str(destino), str(SAIDA)],
        cwd=ROI, capture_output=True, text=True,
        env={**__import__("os").environ, "SELECTOR": ".card",
             "VW": str(W), "VH": str(H), "PREFIX": "linkedin"},
    )
    print(proc.stdout.strip() or proc.stderr.strip()[:400])
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
