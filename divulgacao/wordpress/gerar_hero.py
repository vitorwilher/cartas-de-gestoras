#!/usr/bin/env python3
"""Gera a versão WEB do gráfico do exercício, para o hero da landing.

O mesmo gráfico serve dois meios com exigências opostas. No PDF ele é largo
(14x5.5, painéis lado a lado) e a página inteira o acomoda. Numa coluna de
landing essa proporção encolhe até as fontes ficarem ilegíveis — foi o que o
Vitor apontou em 09/09 ("aumenta o gráfico por amor de Deus").

Aqui os painéis vão EMPILHADOS (mais alto que largo, que é o formato de uma
coluna) e a tipografia é dimensionada para tela.

Depende de `dados.py`, extraído do bloco de código da edição — a parte que
baixa o Tesouro Direto e calcula a inclinação. Os números são os mesmos da
edição; só a apresentação muda.

Uso:
    python divulgacao/wordpress/gerar_hero.py
    # depois: subir hero-web.png à biblioteca de mídia e apontar IMG_GRAFICO
"""

# O PDF usa 14x5.5 lado a lado; numa coluna de landing isso encolhe até as
# fontes sumirem. Aqui: painéis EMPILHADOS (formato mais alto que largo) e
# tipografia dimensionada para tela.
exec(open("dados.py").read())  # noqa: S102 — o preparo vem da própria edição

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 15, "axes.titlesize": 17,
                     "axes.labelsize": 15, "legend.fontsize": 13,
                     "xtick.labelsize": 13, "ytick.labelsize": 13})

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 12.5),
                               gridspec_kw={"height_ratios": [1, 1]})

eh_ntnf = curva_hoje["Tipo Titulo"].str.contains("Juros|NTN-F")
ax1.plot(curva_hoje["prazo"], curva_hoje["taxa"], color="grey", lw=1.6, zorder=1)
ax1.scatter(curva_hoje.loc[~eh_ntnf, "prazo"], curva_hoje.loc[~eh_ntnf, "taxa"],
            marker="o", s=90, color="tab:blue", label="LTN (Tesouro Prefixado)", zorder=3)
ax1.scatter(curva_hoje.loc[eh_ntnf, "prazo"], curva_hoje.loc[eh_ntnf, "taxa"],
            marker="s", s=90, color="tab:orange", label="NTN-F (juros semestrais)", zorder=3)
ax1.scatter([TENOR_CURTO, TENOR_LONGO], [taxa_curta, taxa_longa],
            marker="D", color="black", s=130, zorder=4, label="vértices interpolados")
ax1.axvline(TENOR_CURTO, color="black", ls=":", lw=1.2)
ax1.axvline(TENOR_LONGO, color="black", ls=":", lw=1.2)
ax1.annotate("", xy=(TENOR_LONGO, taxa_longa), xytext=(TENOR_LONGO, taxa_curta),
             arrowprops=dict(arrowstyle="<->", color="tab:red", lw=2.6))
ax1.text(TENOR_LONGO + 0.25, (taxa_curta + taxa_longa) / 2,
         f"inclinação\n{atual:+.0f} bps", color="tab:red", fontsize=17,
         fontweight="bold", va="center")
ax1.set_title(f"A curva prefixada hoje ({ultima:%d/%m/%Y})", fontweight="bold", pad=12)
ax1.set_xlabel("Prazo até o vencimento (anos)")
ax1.set_ylabel("Taxa de venda (% a.a.)")
ax1.grid(alpha=0.3)
ax1.legend(loc="lower right")

ax2.plot(hist.index, hist["inclinacao_bps"], color="tab:blue", lw=1.5)
ax2.axhspan(p10, p90, color="grey", alpha=0.15, label="faixa 10%–90% da história")
ax2.axhline(mediana, color="grey", ls="--", lw=1.4, label=f"mediana ({mediana:.0f} bps)")
ax2.axhline(0, color="black", lw=0.9)
ax2.scatter([ultima], [atual], color="tab:red", s=170, zorder=5)
ax2.annotate(f"hoje: {atual:+.0f} bps\n(percentil {percentil:.0f}%)",
             xy=(ultima, atual), xytext=(-165, 55), textcoords="offset points",
             fontsize=16, color="tab:red", fontweight="bold",
             arrowprops=dict(arrowstyle="->", color="tab:red", lw=2))
ax2.set_title(f"Inclinação {TENOR_LONGO:.0f}a − {TENOR_CURTO:.0f}a desde {INICIO_HIST[:4]}",
              fontweight="bold", pad=12)
ax2.set_xlabel("Data")
ax2.set_ylabel("Inclinação (pontos-base)")
ax2.grid(alpha=0.3)
ax2.legend(loc="upper left")

fig.suptitle("Quanto de steepener já está no preço?",
             fontsize=21, fontweight="bold", y=0.985)
fig.tight_layout(rect=[0, 0, 1, 0.975])
fig.savefig("hero-web.png", dpi=150, bbox_inches="tight", facecolor="white")
print("salvo")
