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
    universais = {
        "valor_hoje": ("dr_hoje", "atual_bps", "atual", "inclinacao_atual", "valor_hoje"),
        "percentil": ("pct_hoje", "percentil", "percentil_hist"),
    }
    dados = {k: v for k, v in ns.items() if not k.startswith("__")}
    faltando = []
    for chave, candidatos in universais.items():
        for nome in candidatos:
            if nome in ns:
                dados[chave] = ns[nome]
                break
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


def grafico_divergencia() -> str:
    """A capa: três posições em Brasil que parecem diferentes e não são.

    Ilustração do CONCEITO — as três pernas do livro Brasil e o canal único que
    as liga (o prêmio de risco-país). Sem escala fechada: o ponto é a forma da
    dependência, não um valor medido. O dado real vem nos slides 6 e 7.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10.8, 8.2), dpi=100)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    pernas = [("Bolsa", 1.9), ("Juro", 5.0), ("Real", 8.1)]
    for nome, x in pernas:
        ax.add_patch(plt.Circle((x, 7.0), 0.92, color=BLUE, alpha=0.16, zorder=2))
        ax.text(x, 7.0, nome, ha="center", va="center",
                fontsize=27, color=NAVY, fontweight="bold", zorder=3)
        ax.plot([x, 5.0], [6.0, 3.6], color=MUTED, lw=2.4, ls=(0, (4, 3)), zorder=1)

    ax.add_patch(plt.Circle((5.0, 2.6), 1.35, color=NAVY, zorder=2))
    ax.text(5.0, 2.85, "MESMO", ha="center", va="center",
            fontsize=21, color="white", fontweight="bold", zorder=3)
    ax.text(5.0, 2.25, "EVENTO", ha="center", va="center",
            fontsize=21, color="white", fontweight="bold", zorder=3)
    ax.text(5.0, 0.55, "risco-país", ha="center", va="center",
            fontsize=23, color=MUTED, style="italic")

    ax.text(0, 9.55, "Três posições, um só canal de risco",
            fontsize=30, color=NAVY, fontweight="bold", va="bottom")
    ax.text(0, 9.05, "as três apostas em Brasil da Kapitalo",
            fontsize=22, color=MUTED, va="bottom")
    fig.tight_layout()
    return _fig_para_uri(fig)


def grafico_diversificacao(d: dict) -> str:
    """A razão de diversificação no tempo: quantas apostas o livro tem de fato.

    É o gráfico-chave da edição. O teto (1,73 = três pernas independentes) e o
    piso (1,00 = uma aposta só) enquadram a leitura, e o ponto de hoje é o
    assunto — círculo com halo, rótulo colado.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dr = d["dr"].dropna()
    hoje = float(d["valor_hoje"])
    pct = float(d["percentil"])

    fig, ax = plt.subplots(figsize=(10.8, 8.2), dpi=100)
    ax.plot(dr.index, dr.values, color=BLUE, lw=2.6)
    ax.axhline(1.73, color=MUTED, lw=2.0, ls=(0, (5, 4)))
    # Rótulo à DIREITA e acima: à esquerda ele caía sobre a própria série, que
    # nesta amostra passa de 1,9 em 2021.
    ax.text(dr.index[-1], 1.745, "1,73 = três apostas independentes",
            fontsize=21, color=MUTED, va="bottom", ha="right")
    ax.axhline(1.0, color="#C0392B", lw=2.0, ls=(0, (2, 3)))
    ax.text(dr.index[0], 1.015, "1,00 = uma aposta só",
            fontsize=21, color="#C0392B", va="bottom")

    ax.scatter([dr.index[-1]], [hoje], s=700, color="white", zorder=4)
    ax.scatter([dr.index[-1]], [hoje], s=380, color=NAVY, zorder=5)
    ax.annotate(f"hoje: {hoje:.2f}".replace(".", ","),
                xy=(dr.index[-1], hoje), xytext=(-18, -52),
                textcoords="offset points", ha="right",
                fontsize=28, color=NAVY, fontweight="bold")

    _limpar(ax)
    _titulo(ax, "Três posições em Brasil valem 2 apostas",
            "razão de diversificação · janela de 63 dias úteis")
    fig.tight_layout()
    return _fig_para_uri(fig)


def grafico_cauda(d: dict) -> str:
    """O teste da condição de quebra: o que cada perna faz nos piores dias do real.

    Duas barras por perna (piores 5% × demais dias). É o cruzamento que nenhuma
    carta faz sozinha — e o argumento visual mais forte da edição.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    # O exercício JÁ entrega em % ao dia (0,32 = 0,32%). Multiplicar por 100 aqui
    # produzia "-225,33%" de queda diária no real — número impossível que passaria
    # no feed como erro grosseiro de quem publicou.
    piores = d["media_piores"]
    resto = d["media_resto"]
    nomes = ["Bolsa", "Juro", "Real"]
    x = np.arange(len(nomes))
    larg = 0.36

    fig, ax = plt.subplots(figsize=(10.8, 8.2), dpi=100)
    ax.bar(x - larg / 2, piores.values, larg, color="#C0392B", label="5% piores dias do real")
    ax.bar(x + larg / 2, resto.values, larg, color=BLUE, alpha=0.55, label="demais dias")
    ax.axhline(0, color=NAVY, lw=1.8)

    # Rótulo da barra negativa vai DENTRO da barra, em branco: fora dela ele
    # colidia com o nome da perna no eixo x.
    for i, v in enumerate(piores.values):
        dentro = v < -0.5
        ax.text(i - larg / 2,
                v * 0.5 if dentro else (v - 0.06 if v < 0 else v + 0.04),
                f"{v:+.2f}%".replace(".", ","),
                ha="center", va="center" if dentro else ("top" if v < 0 else "bottom"),
                fontsize=23, color="white" if dentro else "#C0392B",
                fontweight="bold")

    ax.set_xticks(x); ax.set_xticklabels(nomes, fontsize=25, color=NAVY)
    ax.legend(fontsize=20, frameon=False, loc="lower left")
    _limpar(ax)
    _titulo(ax, "No dia em que o real quebra, a bolsa não salva",
            "retorno médio diário por perna · % ao dia")
    fig.tight_layout()
    return _fig_para_uri(fig)


def slides(d: dict) -> list[dict]:
    """Os 10 slides, na ordem em que a história se sustenta.

    A regra que organiza tudo: **nenhum gráfico aparece antes de o leitor ter
    contexto para lê-lo**. A capa mostra as três pernas ligadas ao mesmo canal de
    risco — o conceito que a manchete promete; a série da razão de diversificação
    só entra depois do slide que explica o que ela mede, porque antes disso "1,45"
    não significa nada para quem passa o polegar.

    O fecho não promete a síntese — promete o MÉTODO. Resumir carta é commodity;
    o que ninguém mais entrega é o caminho da tese até o código que a testa.

    Bullets, não parágrafos. Sem preço e sem oferta: o público está em nível 1-2
    de consciência, e nível 5 no primeiro toque é o erro documentado que rendeu
    174 mensagens e zero respostas na campanha de Claude Code T2.

    Jargão de mesa fica no PDF, não aqui: "livro" (trading book) faz o leitor
    parar para decodificar, e no feed cada palavra tem dois segundos.
    """
    dr = f"{float(d['valor_hoje']):.2f}".replace(".", ",")
    pct = f"{float(d['percentil']):.0f}"
    perdeu_bolsa = f"{float(d['freq_perda'].iloc[0]):.0f}"  # já vem em %
    return [
        {
            "kind": "capa",
            "hook": "A Kapitalo comprou Brasil em *três* frentes. O risco é *um* só.",
            "src": grafico_divergencia(),
        },
        {
            "kind": "lista",
            "title": "As *três* posições",
            "variant": "check",
            "items": [
                "Comprada em bolsa brasileira",
                "Aplicada em juro local (NTN-B)",
                "Comprada em real",
                "Três instrumentos. Três teses diferentes?",
            ],
        },
        {
            "kind": "lista",
            "title": "O problema: o *mesmo* gatilho",
            "variant": "diamond",
            "items": [
                "Todas dependem do Brasil ser reprecificado para melhor",
                "*Crise de confiança:* o prêmio de risco-país sobe",
                "Bolsa cai, curva abre, dólar dispara — juntos",
            ],
        },
        {
            "kind": "definicao",
            "title": "Como se mede isso",
            "rows": [
                {"term": "Razão de diversificação",
                 "desc": "soma das volatilidades ÷ volatilidade da carteira"},
                {"term": "1,73", "desc": "teto: três apostas realmente independentes"},
                {"term": "1,00", "desc": "piso: as três são uma aposta só"},
            ],
        },
        {
            "kind": "lista",
            "title": "E isso *custa dinheiro*",
            "variant": "diamond",
            "items": [
                "Você dimensiona como se fossem três apostas",
                "*Mas carrega o risco de menos que isso*",
                "A conta aparece justamente no dia ruim",
            ],
        },
        {
            "kind": "capa",
            "hook": f"Medido: *{dr}* — no percentil {pct} desde 2019 👇",
            "hint": False,
            "src": grafico_diversificacao(d),
        },
        {
            "kind": "capa",
            "hook": "E no dia em que o real quebra?",
            "hint": False,
            "src": grafico_cauda(d),
        },
        {
            "kind": "lista",
            "title": "O que o dado diz",
            "variant": "diamond",
            "items": [
                f"Nos 5% piores dias do real, a bolsa perdeu em *{perdeu_bolsa}%* deles",
                "A proteção some justo quando faria falta",
                "*A própria Kapitalo* nomeou essa condição de quebra",
            ],
        },
        {
            "kind": "lista",
            "title": "O caminho que eu fiz aqui",
            "variant": "number",
            "items": [
                "Li a tese: Kapitalo ampliou Brasil em três frentes",
                "Achei o *mecanismo*: as três dependem do mesmo evento",
                "Escrevi o código que mede isso com dado público",
                "*Este gráfico saiu daí* — e roda em segundos",
            ],
        },
        {
            "kind": "cta",
            "title": "Te mando o código junto",
            # A pergunta no fim puxa comentário de quem não vai digitar a
            # palavra-chave — e comentário é o que o algoritmo lê como alcance.
            "paragraph": f"Toda semana leio as cartas das 15 maiores gestoras, destrincho as teses e escrevo *um exercício em Python* que testa uma delas. Comenta *{PALAVRA_CHAVE}* que eu mando a desta semana — síntese e código — no seu direct. E me conta: qual tese você queria ver testada?",
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
