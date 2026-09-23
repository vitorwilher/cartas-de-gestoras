"""Arte de LinkedIn da edicao — SO O GRAFICO (1200x1200, padrao CLARO da casa).

Difere do `divulgacao/linkedin.py`, que monta uma peca 1200x627 com texto ao lado
do grafico. Aqui a peca e o grafico inteiro: quadrado (ocupa mais altura no feed)
e sem argumento escrito na arte — o argumento vai na copy.

Os numeros vem de `dados_do_exercicio()`, os MESMOS do PDF e do carrossel.
Tokens: padrao claro decidido em 11/09 (social/carousel_post_html.py do ROI).

Edicao de 23/09: o Treasury longo em reais (TLT x dolar) ainda protege a bolsa
brasileira? Painel 1 = correlacao movel; painel 2 = quanto risco a carteira 50/50
ainda apaga. A versao anterior (edicao de 15/09) esta no historico do git.
"""
import sys, pathlib
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

D = pathlib.Path(__file__).parent
sys.path.insert(0, str(D.parent))
from carrossel import dados_do_exercicio            # noqa: E402

d        = dados_do_exercicio()
painel   = d['painel']
corr     = painel['corr'].dropna()
ben      = painel['beneficio'].dropna()
c_hoje   = float(d['valor_hoje'])
pct      = float(d['percentil'])
c_med    = float(d['med_corr'])
b_hoje   = float(d['ult']['beneficio'])
b_med    = float(ben.median())
desde_24 = (corr.loc['2024':] > 0).mean() * 100

# --- tokens da casa (padrao CLARO) ---
PAPER, NAVY, INK   = '#FFFFFF', '#0A1A3C', '#16202E'
INK_SOFT, MUTED    = '#3A4757', '#8894A5'
LINE, BLUE         = '#E6EAF0', '#1CA0D8'
RED, AMBER         = '#E5484D', '#F5A524'

vir = lambda x, n=2: f'{x:.{n}f}'.replace('.', ',')
sinal = lambda x, n=2: f'{x:+.{n}f}'.replace('.', ',').replace('-', '−')

fig, (ax, bx) = plt.subplots(
    2, 1, figsize=(10, 10), dpi=120,
    gridspec_kw={'height_ratios': [1.25, 1], 'hspace': .42})
fig.patch.set_facecolor(PAPER)

# ---------------- titulo (na FIGURA: o pad do eixo corta) ----------------
fig.text(.105, .963, 'O seguro do investidor brasileiro', fontsize=25, color=NAVY,
         weight='bold', va='top')
fig.text(.105, .925, 'mudou de sinal', fontsize=25, color=NAVY,
         weight='bold', va='top')
fig.text(.105, .888,
         'Correlação entre Ibovespa e Treasury longo em reais (ETF TLT × dólar)',
         fontsize=13.5, color=INK_SOFT, va='top')
fig.text(.105, .862,
         f'retornos diários · janela móvel de 126 dias úteis · {corr.index.min():%Y}–{corr.index.max():%Y}',
         fontsize=13.5, color=INK_SOFT, va='top')

# ---------------- painel 1: a correlacao ----------------
ax.set_facecolor(PAPER)
ax.fill_between(corr.index, 0, corr.values, where=corr.values > 0,
                color=RED, alpha=.14, zorder=1, linewidth=0)
ax.plot(corr.index, corr.values, lw=1.5, color=NAVY, zorder=4)
ax.axhline(0, color=INK_SOFT, lw=1.1, zorder=3)
ax.axhline(c_med, color=MUTED, lw=1.5, ls=':', zorder=3)
ax.text(.008, c_med - .02, f'mediana {sinal(c_med)}', transform=ax.get_yaxis_transform(),
        ha='left', va='top', fontsize=13, color=INK_SOFT, zorder=8,
        bbox=dict(boxstyle='round,pad=.2', facecolor='white', edgecolor='none', alpha=.9))

ax.scatter([corr.index[-1]], [c_hoje], s=165, c=AMBER,
           edgecolors='white', linewidths=1.9, zorder=7)
ax.annotate(f'hoje: {sinal(c_hoje)}\nacima de {pct:.0f}% dos dias',
            xy=(corr.index[-1], c_hoje), xytext=(corr.index[int(len(corr) * .47)], .31),
            textcoords='data', ha='left', va='center', fontsize=14,
            color=INK, linespacing=1.45, zorder=9,
            bbox=dict(boxstyle='round,pad=.3', facecolor='white', edgecolor='none', alpha=.95),
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=1.3, shrinkA=0, shrinkB=8))

ax.set_ylabel('Correlação', fontsize=15, color=INK_SOFT, labelpad=12)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: vir(v, 1).replace('-', '−')))
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.margins(x=.015)
ax.legend(handles=[
    Line2D([], [], lw=2.6, color=NAVY, label='Correlação móvel'),
    Line2D([], [], lw=8, color=RED, alpha=.3, label='Acima de zero: soma risco'),
], loc='lower right', fontsize=12.8, frameon=True,
   facecolor='white', edgecolor=LINE, labelcolor=INK_SOFT, borderpad=.75,
   framealpha=.97)

# ---------------- painel 2: o risco que a mistura ainda apaga ----------------
bx.set_facecolor(PAPER)
bx.plot(ben.index, ben.values, lw=1.5, color=BLUE, zorder=4)
bx.axhline(b_med, color=MUTED, lw=1.5, ls=':', zorder=3)
bx.text(.008, b_med + .6, f'mediana {vir(b_med, 0)}%', transform=bx.get_yaxis_transform(),
        ha='left', va='bottom', fontsize=13, color=INK_SOFT, zorder=8,
        bbox=dict(boxstyle='round,pad=.2', facecolor='white', edgecolor='none', alpha=.9))
bx.scatter([ben.index[-1]], [b_hoje], s=165, c=AMBER,
           edgecolors='white', linewidths=1.9, zorder=7)
bx.annotate(f'hoje: {vir(b_hoje, 0)}%', xy=(ben.index[-1], b_hoje), xytext=(-26, 26),
            textcoords='offset points', ha='right', va='bottom', fontsize=14,
            color=INK, zorder=9,
            bbox=dict(boxstyle='round,pad=.3', facecolor='white', edgecolor='none', alpha=.95),
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=1.3, shrinkA=0, shrinkB=8))

bx.text(0, 1.10, 'Quanto risco a carteira 50/50 ainda apaga',
        transform=bx.transAxes, fontsize=16.5, color=NAVY, weight='bold')
bx.text(0, 1.022,
        '% da volatilidade média que a correlação elimina · rebalanceada diariamente',
        transform=bx.transAxes, fontsize=13, color=INK_SOFT)
bx.set_ylabel('Benefício (%)', fontsize=15, color=INK_SOFT, labelpad=12)
bx.xaxis.set_major_locator(mdates.YearLocator(2))
bx.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
bx.margins(x=.015)

for a in (ax, bx):
    a.tick_params(labelsize=13.5, colors=INK_SOFT, length=0)
    a.grid(True, axis='y', color=LINE, lw=.9); a.set_axisbelow(True)
    for s in ('top', 'right'): a.spines[s].set_visible(False)
    for s in ('left', 'bottom'): a.spines[s].set_color(LINE)

fig.text(.105, .022,
         'analisemacro.com.br  ·  Fonte: Yahoo Finance (^BVSP, TLT, BRL=X)  ·  '
         f'dados até {corr.index.max():%d/%m/%Y}',
         fontsize=12.3, color=MUTED)

fig.subplots_adjust(left=.105, right=.975, top=.822, bottom=.115)
fig.savefig(D / 'linkedin-sintese-cartas.png', facecolor=PAPER)
print('OK -> linkedin-sintese-cartas.png')
print(f'   correlação hoje {sinal(c_hoje)} (acima de {pct:.0f}% dos dias; mediana {sinal(c_med)})')
print(f'   positiva em {desde_24:.0f}% dos dias desde 2024 · benefício {vir(b_hoje, 1)}% (mediana {vir(b_med, 1)}%)')
