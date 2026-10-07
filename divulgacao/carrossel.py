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
                       "ult['corr']", "beta_hoje", "corr_hoje"),
        "percentil": ("pct_hoje", "percentil", "percentil_hist", "pct_corr",
                      # 29/09: o exercício não calcula percentil; derivamos o do
                      # beta móvel de hoje contra a própria série.
                      "(beta_movel_validos < beta_hoje).mean() * 100",
                      # 07/10: percentil da correlação móvel de hoje na própria série.
                      "(corr_movel.dropna() < corr_hoje).mean() * 100"),
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
    # Um valor que arredonda para zero sai "0,00", não "−0,00" (visto em 07/10).
    if round(x, casas) == 0:
        x = 0.0
    return f"{x:.{casas}f}".replace(".", ",").replace("-", "−")


def petroleo(d: dict) -> dict:
    """Os números da edição de 07/10, recalculados só com semanas ENCERRADAS.

    O resample "W-FRI" rotula a semana corrente, ainda aberta, com a sexta futura;
    uma semana pela metade mexe na janela móvel (mesmo cuidado do carrossel de
    29/09). Tudo o mais é o cálculo do exercício, linha a linha.
    """
    import numpy as np
    import pandas as pd
    ret = d["ret"]
    ret = ret[ret.index <= pd.Timestamp.today().normalize()]
    cart = 0.5 * ret["bolsa"] + 0.5 * ret["juros"]
    brent = ret["brent"]
    corr = cart.rolling(52).corr(brent).dropna()
    w = -(cart.rolling(52).cov(brent) / brent.rolling(52).var()).dropna()
    pesos = np.arange(0.0, 0.61, 0.02)
    vol, pior4 = [], []
    for p in pesos:
        r = cart + p * brent
        vol.append(r.std() * np.sqrt(52) * 100)
        pior4.append(((1 + r).rolling(4).apply(np.prod, raw=True) - 1).min() * 100)
    decil = pd.qcut(cart, 10, labels=False) + 1
    return {
        "inicio": ret.index[0], "fim": ret.index[-1], "n": len(ret),
        "corr": corr, "corr_hoje": float(corr.iloc[-1]),
        "pct_hoje": float((corr < corr.iloc[-1]).mean() * 100),
        "corr_total": float(cart.corr(brent)),
        "corr_max": float(corr.max()), "data_max": corr.idxmax(),
        "w_hoje": float(w.iloc[-1]),
        "pesos": pesos * 100, "vol": np.array(vol), "pior4": np.array(pior4),
        "brent_decil": brent.groupby(decil).mean() * 100,
        "cart_decil": cart.groupby(decil).mean() * 100,
    }


def grafico_decis(d: dict) -> str:
    """A capa: o Brent médio em cada decil da carteira, com o decil 1 em destaque.

    A tese da Kinea equivale a prever barra vermelha ACIMA de zero (o petróleo
    sobe nas piores semanas de bolsa + juro Brasil). O gráfico responde em dois
    segundos: ficou abaixo.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = petroleo(d)
    bd = p["brent_decil"]
    cores = ["#C0392B" if k == 1 else "#C9D3DF" for k in bd.index]
    fig, ax = plt.subplots(figsize=(10.8, 8.6), dpi=100)
    ax.bar(bd.index, bd.values, width=0.68, color=cores)
    ax.axhline(0, color=NAVY, lw=2.2)
    for k, v in bd.items():
        ax.text(k, v + (0.25 if v >= 0 else -0.25), _num(v, 1),
                ha="center", va="bottom" if v >= 0 else "top",
                fontsize=24 if k == 1 else 19,
                color="#C0392B" if k == 1 else MUTED,
                fontweight="bold" if k == 1 else "normal")
    ax.annotate("as 10% piores\nsemanas da carteira", xy=(1, bd.loc[1] - 0.9),
                xytext=(2.6, -3.6), fontsize=23, color="#C0392B", va="center",
                bbox=_FUNDO, arrowprops=dict(arrowstyle="-", color="#C0392B", lw=1.8))
    ax.set_xticks(range(1, 11))
    ax.set_xticklabels(["pior"] + [str(k) for k in range(2, 10)] + ["melhor"])
    ax.set_ylim(min(bd.min() - 2.2, -4.6), bd.max() + 1.2)
    _limpar(ax)
    _eixo_virgula(ax, 0)
    _titulo(ax, "Nas piores semanas, o petróleo caiu junto",
            f"Brent, retorno médio semanal (%) · por decil da carteira · {p['inicio']:%Y}–{p['fim']:%Y}")
    fig.tight_layout()
    return _fig_para_uri(fig)


def grafico_correlacao(d: dict) -> str:
    """Onde estamos: a correlação móvel de 52 semanas, com o ponto de hoje.

    É o "ponto de hoje contra a história" desta edição. Sem ele o carrossel
    diria só "o petróleo não protege" — e hoje a relação está perto de zero,
    entre as mais baixas da série. NÃO é "a menor": com semanas encerradas a
    mínima foi −0,02, em junho de 2026.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = petroleo(d)
    c = p["corr"]
    fig, ax = plt.subplots(figsize=(10.8, 8.2), dpi=100)
    ax.fill_between(c.index, 0, c.values, where=(c.values > 0), color=BLUE, alpha=0.15, lw=0)
    ax.plot(c.index, c.values, color=BLUE, lw=3.2)
    ax.axhline(0, color=NAVY, lw=2.0)
    ax.text(c.index[int(len(c) * 0.04)], 0.04,
            "acima de zero: petróleo e carteira\nandam juntos — não protege",
            fontsize=21, color=MUTED, va="bottom", bbox=_FUNDO, zorder=6)
    x, y = c.index[-1], p["corr_hoje"]
    ax.scatter([x], [y], s=700, color="white", zorder=4)
    ax.scatter([x], [y], s=380, color="#C0392B", zorder=5)
    ax.annotate(f"hoje: {_num(y)}\nentre as {p['pct_hoje']:.0f}% mais baixas",
                xy=(x, y), xytext=(-60, -120),
                textcoords="offset points", ha="right", fontsize=27, color="#C0392B",
                fontweight="bold", bbox=_FUNDO, zorder=6,
                arrowprops=dict(arrowstyle="-", color="#C0392B", lw=1.6))
    ax.set_ylim(-0.42, 0.72)
    _limpar(ax)
    _eixo_virgula(ax, 1)
    _titulo(ax, "Só agora a relação chegou a zero",
            "correlação de 52 semanas · Brent × carteira bolsa + juro Brasil")
    fig.tight_layout()
    return _fig_para_uri(fig)


def grafico_cauda(d: dict) -> str:
    """O custo: a pior janela de 4 semanas conforme cresce o petróleo sobreposto.

    Se fosse proteção, a curva subiria (perda menor). Ela desce: na amostra de
    2020 a hoje, mais Brent deixou o pior mês pior.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = petroleo(d)
    x, y = p["pesos"], p["pior4"]
    fig, ax = plt.subplots(figsize=(10.8, 8.2), dpi=100)
    ax.plot(x, y, color="#C0392B", lw=4.5)
    # O rótulo da ponta direita vai ABAIXO da linha: acima, ele a cruzava.
    for xi, yi, txt, dx, dy in ((x[0], y[0], f"sem petróleo\n{_num(y[0], 0)}%", 30, 18),
                                (x[-1], y[-1], f"60% em Brent\n{_num(y[-1], 0)}%", -30, -90)):
        ax.scatter([xi], [yi], s=380, color=NAVY, zorder=5)
        ax.annotate(txt, xy=(xi, yi), xytext=(dx, dy), textcoords="offset points",
                    ha="left" if dx > 0 else "right", fontsize=26, color=NAVY,
                    fontweight="bold", bbox=_FUNDO, zorder=6)
    ax.set_xlim(-4, 64)
    ax.set_ylim(y.min() - 14, y.max() + 12)
    from matplotlib.ticker import FuncFormatter
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%".replace("-", "−")))
    _limpar(ax)
    _titulo(ax, "Mais petróleo, pior o pior mês",
            "pior retorno em 4 semanas × % do patrimônio em Brent sobreposto")
    fig.tight_layout()
    return _fig_para_uri(fig)


def slides(d: dict) -> list[dict]:
    """Os 10 slides, na ordem em que a história se sustenta.

    Edição de 07/10: a Kinea diz carregar petróleo como hedge de juros aplicados e
    bolsa comprada; o exercício testa isso numa carteira 50% EWZ + 50% IMAB11.
    Capa com o gráfico que responde (pedido do Vitor em 02/10: a prova abre o post).

    Desde 07/10 a síntese completa é paga (R$ 97/mês). Pedido do Vitor: os
    carrosséis passam a dar ÊNFASE À ASSINATURA. O preço continua fora do slide —
    CTA de venda derruba alcance no feed (skill copy-analise-macro) e a regra da
    casa é "palavra-chave + pergunta, sem preço"; o preço está na landing, que é
    para onde a DM leva. A ênfase vem dos slides 9 e 10: o caminho termina na
    edição completa, e o CTA diz o que é do assinante.

    Bullets, não parágrafos. Sem preço e sem emoji.
    """
    p = petroleo(d)
    b1, c1 = p["brent_decil"].loc[1], p["cart_decil"].loc[1]
    return [
        {
            "kind": "capa",
            "hook": "A Kinea carrega petróleo para proteger juros e bolsa. *Nas piores semanas, ele protegeu?*",
            "src": grafico_decis(d),
        },
        {
            "kind": "lista",
            "title": "O que a *Kinea* argumenta",
            "variant": "check",
            "items": [
                "Carrega petróleo como proteção parcial da carteira",
                "Do outro lado: juros Brasil aplicados e bolsa comprada",
                "*Um choque de energia sobe juro e derruba bolsa — o petróleo compensa*",
            ],
        },
        {
            "kind": "lista",
            "title": "Por que isso importa *além da Kinea*",
            "variant": "diamond",
            "items": [
                "Bahia e Opportunity carregam a mesma combinação",
                "Juros aplicados e bolsa comprada, sem o petróleo do outro lado",
                "*A pergunta vale para as três casas*",
            ],
        },
        {
            "kind": "definicao",
            "title": "Como se mede isso",
            "rows": [
                {"term": "Proteção (hedge)",
                 "desc": "posição que ganha quando o resto da carteira perde"},
                {"term": "Correlação móvel",
                 "desc": "petróleo × carteira, medida nas últimas 52 semanas"},
                {"term": "Decil 1",
                 "desc": "as 10% piores semanas da carteira desde 2020"},
            ],
        },
        {
            "kind": "lista",
            "title": "O tipo de choque *decide*",
            "variant": "diamond",
            "items": [
                # Medido nesta carteira (07/10). NÃO usar 2022 como exemplo de
                # oferta: para bolsa + juro BRASIL a correlação em 2022 foi +0,40,
                # os dois subiram juntos. O choque de oferta da amostra é 2026.
                "2020, choque de demanda: o Brent caiu 25% junto com a carteira",
                "2026, choque de oferta: Brent +68% no ano, e a relação ficou negativa",
                "*A proteção da Kinea só funciona no segundo tipo*",
            ],
        },
        {
            "kind": "capa",
            "hook": f"De 2020 a hoje, mais petróleo deixou o pior mês *pior*.",
            "hint": False,
            "src": grafico_cauda(d),
        },
        {
            "kind": "capa",
            "hook": f"Mas hoje a correlação está em *{_num(p['corr_hoje'])}*: o petróleo parou de cair junto.",
            "hint": False,
            "src": grafico_correlacao(d),
        },
        {
            "kind": "lista",
            "title": "O que o dado diz",
            "variant": "diamond",
            "items": [
                f"Nas piores semanas, a carteira caiu {_num(abs(c1), 1)}% e o Brent, *{_num(abs(b1), 1)}%*",
                "Na amostra inteira, o peso de petróleo que minimiza o risco é zero",
                f"*Hoje a correlação está em {_num(p['corr_hoje'])}*: o petróleo parou de cair junto, mas ainda não protege",
                "A posição é uma aposta no tipo de choque, não um hedge medido",
            ],
        },
        {
            "kind": "lista",
            "title": "O caminho que eu fiz aqui",
            "variant": "number",
            "items": [
                "Li a carta da Kinea: petróleo contra juros e bolsa",
                "Achei o *mecanismo*: choque de oferta sobe juro e derruba bolsa",
                "Medi com dado público: EWZ + IMAB11 × Brent, semanal desde 2020",
                "*O código e a síntese completa estão na edição de assinantes*",
            ],
        },
        {
            "kind": "cta",
            "title": "A edição completa é para assinantes",
            # A pergunta no fim puxa comentário de quem não vai digitar a
            # palavra-chave — e comentário é o que o algoritmo lê como alcance.
            "paragraph": f"Toda semana em que sai carta nova, leio 15 gestoras brasileiras e Oaktree, GMO e Bridgewater. Na *assinatura*: a tese de cada casa destrinchada, as divergências e o código do exercício. Comenta *{PALAVRA_CHAVE}* que eu te mando o link no direct. E me conta: na sua carteira, o petróleo protege ou só soma risco?",
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
