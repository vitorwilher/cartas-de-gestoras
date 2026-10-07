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


def _limpar(ax, eixo_y_direita: bool = True):
    """Visual de feed, não de relatório: sem molduras, poucos ticks, texto grande.

    Num slide o leitor passa 2 segundos. Cada elemento que não conta a história
    (moldura, ticks miúdos, rótulo de eixo óbvio) rouba atenção do que conta.
    """
    for lado in ("top", "right", "left", "bottom"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(labelsize=21, colors=MUTED, length=0, pad=12)
    ax.grid(axis="y", color=LINE, lw=1.6)
    ax.set_axisbelow(True)
    if eixo_y_direita:
        ax.yaxis.tick_right()


def _titulo(ax, titulo: str, medida: str):
    """Título + o que a medida É — sem isso o gráfico não se explica sozinho.

    Ao "limpar para o feed" eu havia removido os títulos, e a capa virou uma
    série de 16 anos sem dizer o que estava no eixo. Num carrossel o leitor não
    tem legenda nem texto de apoio: o gráfico precisa se apresentar.
    """
    ax.set_title(titulo, fontsize=30, color=NAVY, fontweight="bold",
                 loc="left", pad=44)
    ax.text(0, 1.035, medida, transform=ax.transAxes,
            fontsize=22, color=MUTED, va="bottom")


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
    # O exercício é reescrito a cada edição, então o comentário que abre a seção
    # de gráfico muda de texto. Cortamos no primeiro marcador que existir — e, na
    # falta de todos, no primeiro `plt.subplots`, que é onde a paisagem começa.
    for marca in ("# ---------------------------------------------------------------- Gráfico",
                  "# 5. Gráfico", "# ---- Gráfico", "# --- Gráfico",
                  "# Gráfico", "fig, ", "plt.subplots"):
        if marca in codigo:
            codigo = codigo[:codigo.index(marca)]
            break

    ns: dict = {"__name__": "__main__"}
    with contextlib.redirect_stdout(_io.StringIO()):
        exec(compile(codigo, "exercicio", "exec"), ns)

    # O exercício é escrito pelo modelo a cada edição, então os nomes das variáveis
    # variam. Só duas grandezas são UNIVERSAIS, porque o SYSTEM_PROMPT do exercício sempre
    # pede "o ponto de hoje contra a distribuição passada": o valor atual e o
    # percentil dele. Tudo o mais varia com o tema da semana, então o namespace
    # inteiro volta e cada gráfico pega o que precisa — em vez de uma lista fixa
    # que quebrava a cada edição nova (era o caso em 15/09, com o exercício de
    # diversificação: 12 variáveis "faltando" que simplesmente não existiam ali).
    # Candidatos são EXPRESSÕES avaliadas no namespace do exercício: em 23/09 o
    # valor de hoje só existia como `ult["corr"]`, campo de uma Series.
    universais = {
        "valor_hoje": ("dr_hoje", "atual_bps", "atual", "inclinacao_atual", "valor_hoje",
                       "ult['corr']", "beta_hoje"),
        "percentil": ("pct_hoje", "percentil", "percentil_hist", "pct_corr",
                      # 29/09: o exercício não calcula percentil; derivamos o do
                      # beta móvel de hoje contra a própria série.
                      "(beta_movel_validos < beta_hoje).mean() * 100"),
    }
    dados = {k: v for k, v in ns.items() if not k.startswith("__")}
    faltando = []
    for chave, candidatos in universais.items():
        for nome in candidatos:
            try:
                dados[chave] = eval(nome, {}, ns)  # noqa: S307 — nomes fixos, acima
                break
            except Exception:
                continue
        else:
            faltando.append(chave)
    if faltando:
        raise SystemExit(
            f"O exercício de {digests[0].name} não expõe: {', '.join(faltando)}. "
            "Todo exercício precisa do valor de hoje e do percentil — é o que o "
            "SYSTEM_PROMPT pede. Acrescente o nome usado nesta edição aos alias "
            "em dados_do_exercicio()."
        )
    return dados


def _virg(x: float, casas: int = 2) -> str:
    return f"{x:+.{casas}f}".replace(".", ",")


# Fundo branco atrás de rótulo que cai sobre a série: sem ele "mediana" e
# "hoje" ficavam ilegíveis no meio das linhas (visto na prancha de 23/09).
_FUNDO = dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none", alpha=0.92)


def _eixo_virgula(ax, casas: int = 1):
    """Peça em português usa vírgula decimal — o eixo também."""
    from matplotlib.ticker import FuncFormatter
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.{casas}f}".replace(".", ",")))


def _pct(x: float, casas: int = 0) -> str:
    """Percentual com vírgula e sinal de menos tipográfico: −27%."""
    return f"{x * 100:.{casas}f}%".replace(".", ",").replace("-", "−")


def _num(x: float, casas: int = 2) -> str:
    return f"{x:.{casas}f}".replace(".", ",").replace("-", "−")


def regimes(d: dict) -> dict:
    """Os números da edição de 29/09, lidos do namespace do exercício.

    O beta por regime e o choque implícito vêm direto do exercício. O beta móvel
    "de hoje" NÃO: o resample semanal rotula a semana corrente, ainda aberta, com a
    sexta-feira futura — e um beta de 26 semanas com a última semana pela metade
    oscila muito (0,09 com a semana aberta, 0,30 com a última fechada, medido em
    01/10). Para a peça usamos só semanas encerradas.
    """
    import pandas as pd
    bm = d["beta_movel_validos"]
    fechadas = bm[bm.index <= pd.Timestamp.today().normalize()]
    return {
        "b_calmo": float(d["b_calmo"]), "b_corr": float(d["b_corr"]),
        "n_calmo": int(d["n_calmo"]), "n_corr": int(d["n_corr"]),
        "c_calmo": float(d["c_calmo"]), "c_corr": float(d["c_corr"]),
        "fx_calmo": float(d["bfx_calmo"]), "fx_corr": float(d["bfx_corr"]),
        "impl_calmo": float(d["impl_calmo"]), "impl_corr": float(d["impl_corr"]),
        "dd_hoje": float(d["dd_hoje"]), "data_dd": d["dd_diario"].dropna().index[-1],
        "beta_hoje": float(fechadas.iloc[-1]), "data_beta": fechadas.index[-1],
        "pct_beta": float((fechadas < fechadas.iloc[-1]).mean() * 100),
        "inicio": d["ret"].index[0],
    }


def grafico_choque(d: dict) -> str:
    """A capa: o mesmo choque de −20% no S&P 500, lido por dois betas.

    Só duas barras, para a capa se ler em dois segundos. É a pergunta da manchete
    respondida com o número do exercício: −20% em Nova York vira −19% com o beta
    de mercado calmo e −27% com o beta medido nas correções.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r = regimes(d)
    vals = [r["impl_calmo"] * 100, r["impl_corr"] * 100]
    fig, ax = plt.subplots(figsize=(10.8, 8.2), dpi=100)
    ax.bar([0, 1], vals, width=0.56, color=[BLUE, "#C0392B"])
    ax.axhline(0, color=NAVY, lw=2.2)
    for x, v, cor in ((0, vals[0], BLUE), (1, vals[1], "#C0392B")):
        ax.text(x, v - 0.8, _pct(v / 100), ha="center", va="top",
                fontsize=44, color=cor, fontweight="bold")
    ax.text(0, 0.8, f"com o beta de\nmercado calmo ({_num(r['b_calmo'])})",
            ha="center", va="bottom", fontsize=23, color=NAVY)
    ax.text(1, 0.8, f"com o beta medido\nnas correções ({_num(r['b_corr'])})",
            ha="center", va="bottom", fontsize=23, color=NAVY)
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(min(vals) - 7, 8)
    ax.set_xticks([])
    ax.set_yticks([])
    _limpar(ax)
    ax.grid(False)
    _titulo(ax, "Se o S&P 500 cair 20%",
            "queda implícita do Ibovespa em dólar · beta semanal desde 2004")
    fig.tight_layout()
    return _fig_para_uri(fig)


def grafico_dispersao(d: dict) -> str:
    """A prova: as semanas de 2004 a hoje, separadas por regime, com a reta de cada um.

    Duas nuvens, duas inclinações — e o rótulo de cada reta diz o beta. O leitor
    não precisa saber o que é mínimos quadrados para ver que a reta vermelha é
    mais íngreme.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    ret = d["ret"]
    r = regimes(d)
    fig, ax = plt.subplots(figsize=(10.8, 8.6), dpi=100)
    for regime, cor in (("calmo", BLUE), ("correção", "#C0392B")):
        mask = ret["correcao"] if regime == "correção" else ~ret["correcao"]
        sub = ret[mask]
        b, a, _, _ = d["res"][regime]["ibov"]
        ax.scatter(sub["spx"] * 100, sub["ibov"] * 100, s=34,
                   alpha=0.30 if regime == "calmo" else 0.55, color=cor, lw=0)
        xx = np.linspace(-12, 8, 50) / 100
        ax.plot(xx * 100, (a + b * xx) * 100, color=cor, lw=5)
    ax.axhline(0, color=MUTED, lw=1.2)
    ax.axvline(0, color=MUTED, lw=1.2)
    ax.text(-11.5, -21.5, f"em correção\nbeta {_num(r['b_corr'])}", fontsize=28,
            color="#C0392B", fontweight="bold", va="center", bbox=_FUNDO, zorder=6)
    ax.text(0.8, -18.5, f"mercado calmo\nbeta {_num(r['b_calmo'])}", fontsize=28,
            color=BLUE, fontweight="bold", va="center", bbox=_FUNDO, zorder=6)
    ax.set_xlim(-13, 9)
    ax.set_ylim(-28, 22)
    _limpar(ax)
    ax.grid(axis="both", color=LINE, lw=1.4)
    from matplotlib.ticker import FuncFormatter
    fmt = FuncFormatter(lambda v, _: f"{v:.0f}%".replace("-", "−"))
    ax.set_xticks([-10, -5, 0, 5])
    ax.set_yticks([-20, -10, 0, 10, 20])
    ax.xaxis.set_major_formatter(fmt)
    ax.yaxis.set_major_formatter(fmt)
    _titulo(ax, "Em correção, o Brasil cai mais",
            "cada ponto é uma semana · S&P 500 (→) × Ibovespa em US$ (↑)")
    fig.tight_layout()
    return _fig_para_uri(fig)


def grafico_drawdown(d: dict) -> str:
    """Onde estamos: a distância do S&P 500 até a própria máxima, com a linha dos −10%.

    É o "ponto de hoje contra a história" desta edição: o regime que o exercício
    usa é observável, e hoje ele diz "calmo". Sem este gráfico o carrossel
    sugeriria que a correção já está em curso.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r = regimes(d)
    # Semanal (sexta), como o regime do exercício: a série diária é tão densa que
    # a linha cobria o sombreado das correções curtas (2020, 2022). Semanas sem
    # dado (o buraco do BRL=X no Yahoo, out/2004 a mar/2006) ficam como lacuna.
    dd = d["dd"] * 100
    hoje_x, hoje_y = d["dd_diario"].dropna().index[-1], r["dd_hoje"] * 100
    fig, ax = plt.subplots(figsize=(10.8, 8.2), dpi=100)
    ax.fill_between(dd.index, -10, dd.values, where=(dd.values < -10),
                    interpolate=True, color="#C0392B", alpha=0.35, lw=0)
    ax.plot(dd.index, dd.values, color=BLUE, lw=2.2)
    ax.axhline(-10, color="#C0392B", lw=2.0, ls=(0, (5, 4)))
    ax.text(dd.index[int(len(dd) * 0.42)], -11.5, "abaixo de −10%: correção",
            fontsize=22, color="#C0392B", va="top", bbox=_FUNDO, zorder=6)
    ax.scatter([hoje_x], [hoje_y], s=700, color="white", zorder=4)
    ax.scatter([hoje_x], [hoje_y], s=380, color=NAVY, zorder=5)
    # O rótulo vai para a faixa vazia acima de zero: abaixo ele brigava com a
    # linha dos −10% e com a série.
    ax.annotate(f"hoje: {_pct(r['dd_hoje'], 1)}", xy=(hoje_x, hoje_y),
                xytext=(-30, 52), textcoords="offset points", ha="right",
                fontsize=28, color=NAVY, fontweight="bold", bbox=_FUNDO, zorder=6,
                arrowprops=dict(arrowstyle="-", color=NAVY, lw=1.6))
    ax.set_ylim(-57, 11)
    from matplotlib.ticker import FuncFormatter
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%".replace("-", "−")))
    _limpar(ax)
    _titulo(ax, "E hoje? Nova York segue calma",
            "S&P 500: distância da máxima de 252 pregões · %")
    fig.tight_layout()
    return _fig_para_uri(fig)


def slides(d: dict) -> list[dict]:
    """Os 10 slides, na ordem em que a história se sustenta.

    Edição de 29/09: só GMO e Bridgewater publicaram, e o exercício mede quanto do
    "vento contrário de 20 pontos" que a GMO projeta para o S&P 500 chega ao
    Brasil — o beta do Ibovespa em dólar ao S&P 500, separado por regime. A regra
    era "nenhum gráfico antes do contexto", com as barras na capa; em 02/10 o Vitor
    pediu a dispersão na capa — ela tem título e legenda e se explica sozinha. As
    barras passaram ao slide 6, que traz os betas medidos.

    Bullets, não parágrafos. Sem preço, sem oferta e sem emoji.
    """
    r = regimes(d)
    fx_c, fx_k = _num(abs(r["fx_calmo"])), _num(abs(r["fx_corr"]))
    return [
        {
            "kind": "capa",
            "hook": "A GMO vê 20 pontos de vento contra o S&P 500. *Quanto disso chega ao Brasil?*",
            # A dispersão na capa foi pedido do Vitor (02/10): a prova abre o post.
            "src": grafico_dispersao(d),
        },
        {
            "kind": "lista",
            "title": "O que a *GMO* argumenta",
            "variant": "check",
            "items": [
                "O gatilho da bolha de IA não é a demanda: é a oferta de ações",
                "SpaceX, OpenAI, Anthropic e emissões das gigantes de nuvem",
                "Pela conta da casa, ~20 pontos a menos no S&P 500 em 12 a 18 meses",
            ],
        },
        {
            "kind": "lista",
            "title": "Onde isso pesa: *o Brasil*",
            "variant": "diamond",
            "items": [
                "Na correção, o gestor global vende o que é líquido, não o que é caro",
                "Bolsa e real brasileiros viram fonte de caixa",
                "*A conta “20% × beta de sempre” pode sair curta*",
            ],
        },
        {
            "kind": "definicao",
            "title": "Como se mede isso",
            "rows": [
                {"term": "Beta",
                 "desc": "quanto o Ibovespa em dólar anda para cada 1% do S&P 500"},
                {"term": "Correção",
                 "desc": "S&P 500 mais de 10% abaixo da máxima de 252 pregões"},
                {"term": "Beta por regime",
                 "desc": "o mesmo beta, medido só nas semanas calmas ou só nas de correção"},
            ],
        },
        {
            "kind": "lista",
            "title": "E isso *custa dinheiro*",
            "variant": "diamond",
            "items": [
                "O beta médio mistura dois mundos",
                "O hedge dimensionado pela média fica curto na hora que importa",
                "*Para quem mede em dólar, a bolsa e o real caem juntos*",
            ],
        },
        {
            "kind": "capa",
            "hook": f"Medido: *{_num(r['b_corr'])}* em correção, {_num(r['b_calmo'])} no calmo.",
            "hint": False,
            "src": grafico_choque(d),   # as barras traduzem os dois betas em queda
        },
        {
            "kind": "capa",
            "hook": f"Hoje o S&P 500 está a *{_pct(abs(r['dd_hoje']), 1)}* da máxima.",
            "hint": False,
            "src": grafico_drawdown(d),
        },
        {
            "kind": "lista",
            "title": "O que o dado diz",
            "variant": "diamond",
            "items": [
                f"Em correção, o beta sobe de {_num(r['b_calmo'])} para *{_num(r['b_corr'])}*",
                f"O dólar sobe {fx_k}% a cada 1% de queda do S&P (calmo: {fx_c}%)",
                "*Hoje o regime é calmo* — a correção não começou",
                f"{r['n_corr']} semanas de correção desde 2004, de causas variadas: âncora, não previsão",
            ],
        },
        {
            "kind": "lista",
            "title": "O caminho que eu fiz aqui",
            "variant": "number",
            "items": [
                "Li a carta da GMO: 20 pontos contra o S&P 500",
                "Achei o *mecanismo*: venda forçada do que é líquido",
                "Medi com dado público: Ibovespa em dólar × S&P, semanal desde 2004",
                "*Estes gráficos saíram daí* — e o código roda em segundos",
            ],
        },
        {
            "kind": "cta",
            "title": "Te mando o código junto",
            # A pergunta no fim puxa comentário de quem não vai digitar a
            # palavra-chave — e comentário é o que o algoritmo lê como alcance.
            "paragraph": f"Leio as cartas de 15 gestoras brasileiras e de Oaktree, GMO e Bridgewater. Destrincho as teses e escrevo *um exercício em Python* que testa uma delas. Comenta *{PALAVRA_CHAVE}* que eu mando a edição — síntese e código — no seu direct. E me conta: na sua conta de risco, o beta do Brasil é um número só?",
            "cta": f"Comente {PALAVRA_CHAVE}",
        },
    ]


def ocupar_o_slide(html: str) -> str:
    """Distribui o conteúdo na altura do slide, em vez de amontoá-lo no topo.

    O `.bd` do design system usa `justify-content:flex-start`, pensado para
    slides densos. Com bullets curtos sobra um vazio enorme embaixo — o conteúdo
    ocupava menos de metade dos 1350px. Aqui centramos verticalmente, damos ar
    entre os itens e aumentamos o corpo do texto, que no feed é lido no celular.

    O override é aplicado ao HTML gerado, não ao design system em
    ../ROI_Diagnostico — os carrosséis dos outros produtos seguem como estão.
    """
    override = """
    /* --- ajustes deste carrossel (ver ocupar_o_slide) --- */
    /* Distribui na altura: com bullets curtos, flex-start deixava metade do
       slide em branco. `space-between` empurra o último item para a base. */
    .bd { justify-content: space-between; padding: 30px 0 10px; }
    .lst { flex: 1 1 auto; justify-content: space-evenly; gap: 0; }
    .li { font-size: 54px; line-height: 1.26; }
    .title { font-size: 68px; line-height: 1.14; margin-bottom: 10px; }
    .def-list { flex: 1 1 auto; justify-content: space-evenly; gap: 0; }
    .def-term { font-size: 50px; }
    .def-desc { font-size: 44px; line-height: 1.30; }
    .body { font-size: 48px; line-height: 1.40; }
    .mk-dia, .mk-check, .mk-num { transform: scale(1.15); }
    /* Slides com gráfico: a imagem ganha o espaço que sobra. */
    .capa-media-wrap { flex: 1 1 auto; display: flex; align-items: center;
                       margin-top: 20px; }
    .capa-media { width: 100%; height: auto; }
    .stat { margin: 20px 0; }
    """
    return html.replace("</style>", override + "</style>", 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--so-html", action="store_true", help="não rasteriza os PNGs")
    args = parser.parse_args()

    from social.carousel_post_html import build

    print("Rodando o exercício da edição para obter os dados...")
    dados = dados_do_exercicio()
    # Genérico: a grandeza muda a cada edição, só "valor de hoje + percentil" é fixo.
    print(f"  valor de hoje {float(dados['valor_hoje']):.2f}, "
          f"percentil {float(dados['percentil']):.0f}")

    SAIDA.mkdir(parents=True, exist_ok=True)
    lista = slides(dados)
    html = build(lista, fmt="post")
    html = ocupar_o_slide(html)
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
