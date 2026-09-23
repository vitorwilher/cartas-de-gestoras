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
    for marca in ("# 5. Gráfico", "# ---- Gráfico", "# --- Gráfico",
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
                       "ult['corr']"),
        "percentil": ("pct_hoje", "percentil", "percentil_hist", "pct_corr"),
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


def grafico_sinal(d: dict) -> str:
    """A capa: o mesmo seguro em dois momentos, com o sinal trocado.

    Dado real, não ilustração — mas só dois números, para a capa se ler em dois
    segundos: o fundo de março de 2020 (o seguro pagando) e o ponto de hoje. A
    série inteira só entra no slide 6, depois de o slide 4 dizer o que é a medida.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    corr = d["painel"]["corr"]
    data_min, v_min = corr.idxmin(), float(corr.min())
    v_hoje = float(d["valor_hoje"])
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    rot_min = f"{meses[data_min.month - 1]}/{data_min.year}"

    fig, ax = plt.subplots(figsize=(10.8, 8.2), dpi=100)
    xs = [0, 1]
    vals = [v_min, v_hoje]
    cores = [BLUE, "#C0392B"]
    ax.bar(xs, vals, width=0.56, color=cores)
    ax.axhline(0, color=NAVY, lw=2.2)
    ax.text(0, v_min - 0.03, _virg(v_min), ha="center", va="top",
            fontsize=40, color=BLUE, fontweight="bold")
    ax.text(1, v_hoje + 0.03, _virg(v_hoje), ha="center", va="bottom",
            fontsize=40, color="#C0392B", fontweight="bold")
    ax.text(0, 0.05, f"{rot_min}\nprotegia", ha="center", va="bottom",
            fontsize=25, color=NAVY)
    ax.text(1, -0.05, "hoje\nanda junto", ha="center", va="top",
            fontsize=25, color=NAVY)
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(v_min - 0.2, max(v_hoje, 0.2) + 0.17)
    ax.set_xticks([])
    ax.set_yticks([])
    _limpar(ax)
    ax.grid(False)
    _titulo(ax, "O seguro mudou de sinal",
            "correlação Ibovespa × Treasury longo em reais · 6 meses")
    fig.tight_layout()
    return _fig_para_uri(fig)


def grafico_correlacao(d: dict) -> str:
    """A série inteira da correlação, com zero, mediana e o ponto de hoje.

    A faixa acima de zero é o assunto: é onde o Treasury deixa de proteger. O
    ponto de hoje ganha halo e rótulo colado, como nos carrosséis anteriores.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    corr = d["painel"]["corr"].dropna()
    hoje = float(d["valor_hoje"])
    med = float(d["med_corr"])

    fig, ax = plt.subplots(figsize=(10.8, 8.2), dpi=100)
    ax.fill_between(corr.index, 0, corr.values, where=corr.values > 0,
                    color="#C0392B", alpha=0.16, lw=0)
    ax.plot(corr.index, corr.values, color=BLUE, lw=2.2)
    ax.axhline(0, color=NAVY, lw=1.8)
    ax.axhline(med, color=MUTED, lw=2.0, ls=(0, (5, 4)))
    ax.text(corr.index[0], med - 0.03, f"mediana {_virg(med)}",
            fontsize=21, color=MUTED, va="top", bbox=_FUNDO, zorder=6)
    ax.text(corr.index[0], 0.30, "acima de zero:\nsoma risco",
            fontsize=21, color="#C0392B", va="center")

    ax.scatter([corr.index[-1]], [hoje], s=700, color="white", zorder=4)
    ax.scatter([corr.index[-1]], [hoje], s=380, color=NAVY, zorder=5)
    # O rótulo vai para o vazio no alto do gráfico (2018-2023 fica abaixo de 0,3);
    # colado ao ponto ele cobria a série ou o eixo zero.
    ax.annotate(f"hoje: {_virg(hoje)}", xy=(corr.index[-1], hoje),
                xytext=(corr.index[int(len(corr) * 0.45)], 0.33),
                textcoords="data", ha="left", va="center",
                fontsize=28, color=NAVY, fontweight="bold", bbox=_FUNDO, zorder=6,
                arrowprops=dict(arrowstyle="-", color=NAVY, lw=1.6))

    _limpar(ax)
    _eixo_virgula(ax)
    _titulo(ax, "Acima de 89% dos dias desde 2012",
            "correlação móvel · 126 dias úteis · retornos diários")
    fig.tight_layout()
    return _fig_para_uri(fig)


def grafico_beneficio(d: dict) -> str:
    """Quanto risco a carteira 50/50 ainda apaga — hoje contra a própria história.

    É a ressalva honesta em forma de gráfico: a mistura ainda diversifica (o
    dólar ajuda), só que perto do mínimo da série. Sem ela o carrossel diria que
    o Treasury "não protege nada", o que o próprio dado desmente.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ben = d["painel"]["beneficio"].dropna()
    hoje = float(d["ult"]["beneficio"])
    med = float(ben.median())

    fig, ax = plt.subplots(figsize=(10.8, 8.2), dpi=100)
    ax.plot(ben.index, ben.values, color=BLUE, lw=2.2)
    ax.axhline(med, color=MUTED, lw=2.0, ls=(0, (5, 4)))
    ax.text(ben.index[0], med + 0.8, f"mediana {med:.0f}%".replace(".", ","),
            fontsize=21, color=MUTED, va="bottom", bbox=_FUNDO, zorder=6)
    ax.scatter([ben.index[-1]], [hoje], s=700, color="white", zorder=4)
    ax.scatter([ben.index[-1]], [hoje], s=380, color=NAVY, zorder=5)
    ax.annotate(f"hoje: {hoje:.0f}%".replace(".", ","), xy=(ben.index[-1], hoje),
                xytext=(-20, -58), textcoords="offset points", ha="right",
                fontsize=28, color=NAVY, fontweight="bold", bbox=_FUNDO, zorder=6)
    _limpar(ax)
    _titulo(ax, "A mistura ainda protege, bem menos",
            "% do risco apagado pela correlação · carteira 50/50")
    fig.tight_layout()
    return _fig_para_uri(fig)


def slides(d: dict) -> list[dict]:
    """Os 10 slides, na ordem em que a história se sustenta.

    Edição de 23/09: o exercício mede se o Treasury longo, convertido a reais,
    ainda protege a bolsa brasileira. A regra que organiza tudo continua a mesma:
    **nenhum gráfico aparece antes de o leitor ter contexto para lê-lo**. A capa
    mostra só dois números (março de 2020 e hoje); a série inteira entra depois
    do slide que explica o que a correlação mede.

    Bullets, não parágrafos. Sem preço, sem oferta e sem emoji. Sem o jargão
    "livro" (carteira de mesa), que faz o leitor parar para decodificar.
    """
    corr = d["painel"]["corr"]
    hoje = _virg(float(d["valor_hoje"]))
    med = _virg(float(d["med_corr"]))
    v_min = _virg(float(corr.min()))
    ano_min = corr.idxmin().year
    desde_2024 = f"{(corr.loc['2024':] > 0).mean() * 100:.0f}"
    ben_hoje = f"{float(d['ult']['beneficio']):.0f}"
    ben_med = f"{float(d['painel']['beneficio'].median()):.0f}"
    return [
        {
            "kind": "capa",
            "hook": "O seguro *mais clássico* do investidor brasileiro mudou de sinal.",
            "src": grafico_sinal(d),
        },
        {
            "kind": "lista",
            "title": "No que as cartas *concordam*",
            "variant": "check",
            "items": [
                "Genoa: o Fed corre risco de subir juros ainda em 2026",
                "Howard Marks (Oaktree): o juro longo americano está alto por fundamento",
                "Inflação, déficit e demanda por capital — não acidente",
            ],
        },
        {
            "kind": "lista",
            "title": "Onde isso pesa: *o seguro*",
            "variant": "diamond",
            "items": [
                "Para se proteger do Brasil, compra-se Treasury longo em dólar",
                "A lógica: na crise, o real cai e o Treasury sobe",
                "*Com juro americano subindo*, o Treasury pode cair junto",
            ],
        },
        {
            "kind": "definicao",
            "title": "Como se mede isso",
            "rows": [
                {"term": "Correlação negativa",
                 "desc": "o Treasury sobe quando a bolsa cai: protege"},
                {"term": "Perto de zero", "desc": "só dilui o risco"},
                {"term": "Positiva", "desc": "os dois caem juntos: soma risco"},
            ],
        },
        {
            "kind": "lista",
            "title": "E isso *custa dinheiro*",
            "variant": "diamond",
            "items": [
                "A carteira mista fica mais arriscada do que parece",
                "O peso certo em Treasury depende do sinal",
                "*A proteção falha justo quando a inflação americana sobe*",
            ],
        },
        {
            "kind": "capa",
            "hook": f"Medido: *{hoje}*. A mediana desde 2012 é {med}.",
            "hint": False,
            "src": grafico_correlacao(d),
        },
        {
            "kind": "capa",
            "hook": "Ainda protege alguma coisa?",
            "hint": False,
            "src": grafico_beneficio(d),
        },
        {
            "kind": "lista",
            "title": "O que o dado diz",
            "variant": "diamond",
            "items": [
                f"Desde 2024, a correlação ficou positiva em *{desde_2024}%* dos dias",
                f"Em {ano_min} ela chegou a {v_min}: ali o seguro pagou",
                f"A mistura ainda apaga *{ben_hoje}%* do risco, contra {ben_med}% típicos",
                "Janela de 6 meses: é retrato, não previsão",
            ],
        },
        {
            "kind": "lista",
            "title": "O caminho que eu fiz aqui",
            "variant": "number",
            "items": [
                "Li as cartas: Genoa e Marks veem juro americano alto",
                "Achei o *mecanismo*: o seguro depende do sinal da correlação",
                "Medi com dado público: Ibovespa × Treasury em reais",
                "*Estes gráficos saíram daí* — e o código roda em segundos",
            ],
        },
        {
            "kind": "cta",
            "title": "Te mando o código junto",
            # A pergunta no fim puxa comentário de quem não vai digitar a
            # palavra-chave — e comentário é o que o algoritmo lê como alcance.
            "paragraph": f"Leio as cartas de 15 gestoras brasileiras e, agora, de Oaktree, GMO e Bridgewater. Destrincho as teses e escrevo *um exercício em Python* que testa uma delas. Comenta *{PALAVRA_CHAVE}* que eu mando a edição — síntese e código — no seu direct. E me conta: você ainda usa Treasury como seguro?",
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
