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
    ax.set_title("Inclinação da curva: 7 anos − 2 anos", fontsize=22,
                 color=NAVY, fontweight="bold", loc="left", pad=34)
    ax.text(0, 1.035, "quanto o juro longo paga a mais que o curto",
            transform=ax.transAxes, fontsize=16, color=MUTED, va="bottom")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _logo() -> str:
    from social.carousel_post_html import _logo_data_uri
    return _logo_data_uri()


def html(d: dict) -> str:
    bps = f"{d['atual_bps']:.0f}"
    pct = f"{d['percentil']:.0f}"
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  .card {{ width:{W}px; height:{H}px; background:#FFFFFF; display:flex;
           font-family:'Inter','Helvetica Neue',Arial,sans-serif; overflow:hidden; }}
  .esq {{ width:46%; padding:52px 40px 44px 56px; display:flex;
          flex-direction:column; justify-content:space-between; }}
  .dir {{ width:54%; display:flex; align-items:center; justify-content:center;
          padding:28px 44px 28px 8px; background:#FBFCFD; }}
  .dir img {{ width:100%; height:auto; }}
  .marca {{ display:flex; align-items:center; gap:12px; }}
  .marca img {{ width:38px; height:38px; }}
  .marca span {{ font-size:19px; font-weight:700; color:{NAVY}; letter-spacing:-.2px; }}
  .kicker {{ font-size:14px; font-weight:700; color:{BLUE}; letter-spacing:1.6px;
             text-transform:uppercase; margin-bottom:14px; }}
  h1 {{ font-size:40px; line-height:1.16; color:{NAVY}; font-weight:700;
        letter-spacing:-.6px; }}
  h1 em {{ font-style:normal; color:{BLUE}; }}
  p {{ font-size:19px; line-height:1.46; color:{INK_SOFT}; margin-top:18px; }}
  .pe {{ font-size:15px; color:{MUTED}; border-top:1px solid {LINE}; padding-top:14px; }}
</style></head><body>
<div class="card">
  <div class="esq">
    <div class="marca"><img src="{_logo()}"><span>Análise Macro</span></div>
    <div>
      <div class="kicker">Cartas de gestoras · síntese semanal</div>
      <h1>Quatro gestoras leram a mesma inflação.<br><em>Duas fizeram a aposta oposta.</em></h1>
      <p>Bahia e Occam estão tomadas em inclinação. A Kinea projeta a pausa
         do Copom — exatamente o cenário em que essa aposta perde.</p>
    </div>
    <div class="pe">O degrau está em <strong>+{bps} bps</strong>, percentil {pct} desde 2010.</div>
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
