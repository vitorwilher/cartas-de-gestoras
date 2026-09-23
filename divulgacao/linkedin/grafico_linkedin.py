"""Arte de LinkedIn da edicao — SO O GRAFICO (1200x1200, padrao CLARO da casa).

Difere do `divulgacao/linkedin.py`, que monta uma peca 1200x627 com texto ao lado
do grafico. Aqui a peca e o grafico inteiro: quadrado (ocupa mais altura no feed)
e sem argumento escrito na arte — o argumento vai na copy.

Os numeros vem de `dados_do_exercicio()`, os MESMOS do PDF e do carrossel.
Tokens: padrao claro decidido em 11/09 (social/carousel_post_html.py do ROI).
"""
import sys, pathlib
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

D = pathlib.Path(__file__).parent
sys.path.insert(0, str(D.parent))
from carrossel import dados_do_exercicio            # noqa: E402

d       = dados_do_exercicio()
dr      = d['dr']
pernas  = d['pernas']
piores  = d['piores']
dr_hoje = float(d['dr_hoje'])
pct     = float(d['pct_hoje'])
lim     = float(d['lim'])
n_dias  = int(piores.sum())

# --- tokens da casa (padrao CLARO) ---
PAPER, NAVY, INK   = '#FFFFFF', '#0A1A3C', '#16202E'
INK_SOFT, MUTED    = '#3A4757', '#8894A5'
LINE, BLUE         = '#E6EAF0', '#1CA0D8'
BLUE_WASH          = '#BFE3F5'
RED, GREEN, AMBER  = '#E5484D', '#12B76A', '#F5A524'

vir = lambda x, n=2: f'{x:.{n}f}'.replace('.', ',')

fig, (ax, bx) = plt.subplots(
    2, 1, figsize=(10, 10), dpi=120,
    gridspec_kw={'height_ratios': [1.25, 1], 'hspace': .42})
fig.patch.set_facecolor(PAPER)

# ---------------- titulo (na FIGURA: o pad do eixo corta) ----------------
fig.text(.105, .963, 'Três posições em Brasil,', fontsize=25, color=NAVY,
         weight='bold', va='top')
fig.text(.105, .925, 'menos de duas apostas de verdade', fontsize=25, color=NAVY,
         weight='bold', va='top')
fig.text(.105, .888,
         'Bloco comprado em bolsa, aplicado em juro e comprado em real',
         fontsize=13.5, color=INK_SOFT, va='top')
fig.text(.105, .862,
         f'pesos por paridade de risco · {pernas.index.min():%Y}–{pernas.index.max():%Y}',
         fontsize=13.5, color=INK_SOFT, va='top')

# ---------------- painel 1: a razao de diversificacao ----------------
ax.set_facecolor(PAPER)
ax.fill_between(dr.index, np.percentile(dr, 10), np.percentile(dr, 90),
                color=BLUE_WASH, alpha=.35, zorder=1, linewidth=0)
ax.plot(dr.index, dr.values, lw=1.5, color=NAVY, zorder=4)
ax.axhline(1.0,  color=MUTED, lw=1.5, ls=':', zorder=3)
ax.axhline(1.73, color=GREEN, lw=1.5, ls=':', zorder=3)

ax.text(.008, 1.012, 'DR = 1 · uma aposta só', transform=ax.get_yaxis_transform(),
        ha='left', va='bottom', fontsize=13, color=INK_SOFT, zorder=8)
ax.text(.995, 1.745, 'DR = 1,73 · três apostas independentes',
        transform=ax.get_yaxis_transform(), ha='right', va='bottom',
        fontsize=13, color=INK_SOFT, zorder=8)

ax.scatter([dr.index[-1]], [dr_hoje], s=165, c=AMBER,
           edgecolors='white', linewidths=1.9, zorder=7)
ax.annotate(f'hoje: {vir(dr_hoje)}\npercentil {pct:.0f}',
            xy=(dr.index[-1], dr_hoje), xytext=(-26, -30),
            textcoords='offset points', ha='right', va='top', fontsize=14,
            color=INK, linespacing=1.45, zorder=9,
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=1.3,
                            shrinkA=0, shrinkB=8))

ax.set_ylabel('Razão de diversificação', fontsize=15, color=INK_SOFT, labelpad=12)
ax.set_ylim(.92, 2.03)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.margins(x=.015); ax.set_xlim(right=dr.index[-1] + (dr.index[-1] - dr.index[-150]))
ax.legend(handles=[
    Line2D([], [], lw=2.6, color=NAVY, label='Razão de diversificação (63 dias úteis)'),
    Line2D([], [], lw=8, color=BLUE_WASH, alpha=.55, label='Percentis 10 a 90'),
], loc='upper left', bbox_to_anchor=(.012, .995), fontsize=12.8, frameon=True,
   facecolor='white', edgecolor=LINE, labelcolor=INK_SOFT, borderpad=.75,
   framealpha=.97)

# ---------------- painel 2: a cauda ----------------
bx.set_facecolor(PAPER)
rot = ['Bolsa\n(comprado Ibov)', 'Juro\n(aplicado, IMA-B)', 'Real\n(comprado)']
x   = np.arange(3); L = .34

m_pio = np.array([pernas.loc[piores,  c].mean() for c in pernas.columns]) * 100
m_res = np.array([pernas.loc[~piores, c].mean() for c in pernas.columns]) * 100
frq   = np.array([(pernas.loc[piores, c] < 0).mean() for c in pernas.columns]) * 100

bx.bar(x - L/2, m_res, L, color=BLUE_WASH, edgecolor=BLUE, linewidth=1.1, zorder=3)
bx.bar(x + L/2, m_pio, L, color=RED, alpha=.85, zorder=3)
bx.axhline(0, color=INK_SOFT, lw=1.1, zorder=4)

for xi, (v, f) in enumerate(zip(m_pio, frq)):
    cima = v >= 0
    bx.annotate(f'{vir(v)}%\nperdeu em {f:.0f}%'.replace('-', '−'),
                xy=(xi + L/2, v), xytext=(0, 12 if cima else -40),
                textcoords='offset points', ha='center',
                fontsize=12.6, color=INK, linespacing=1.4, zorder=6)

bx.text(0, 1.10, 'O que cada perna fez nos 5% piores dias do real',
        transform=bx.transAxes, fontsize=16.5, color=NAVY, weight='bold')
bx.text(0, 1.022,
        f'{n_dias} dias com queda do real além de {vir(abs(lim*100))}% · '
        'retorno médio diário',
        transform=bx.transAxes, fontsize=13, color=INK_SOFT)
bx.set_xticks(x); bx.set_xticklabels(rot, fontsize=13.2)
bx.set_ylabel('Retorno médio (%)', fontsize=15, color=INK_SOFT, labelpad=12)
bx.set_ylim(min(m_pio) - 1.35, max(max(m_pio), max(m_res)) + .95)
bx.legend(handles=[
    Line2D([], [], lw=8, color=BLUE_WASH, label='Demais dias'),
    Line2D([], [], lw=8, color=RED, alpha=.85, label='5% piores dias do real'),
], loc='lower left', fontsize=12.8, frameon=True, facecolor='white',
   edgecolor=LINE, labelcolor=INK_SOFT, borderpad=.75, framealpha=.97)

for a in (ax, bx):
    a.tick_params(labelsize=13.5, colors=INK_SOFT, length=0)
    a.grid(True, axis='y', color=LINE, lw=.9); a.set_axisbelow(True)
    for s in ('top', 'right'): a.spines[s].set_visible(False)
    for s in ('left', 'bottom'): a.spines[s].set_color(LINE)

fig.text(.105, .022,
         'Elaborado por analisemacro.com.br  ·  Fonte: B3, Tesouro e Yahoo Finance  ·  '
         f'dados até {pernas.index.max():%d/%m/%Y}',
         fontsize=12.3, color=MUTED)

fig.subplots_adjust(left=.105, right=.975, top=.822, bottom=.115)
fig.savefig(D / 'linkedin-sintese-cartas.png', facecolor=PAPER)
print('OK -> linkedin-sintese-cartas.png')
print(f'   DR hoje {vir(dr_hoje)} (percentil {pct:.0f}) · cauda {n_dias} dias')
