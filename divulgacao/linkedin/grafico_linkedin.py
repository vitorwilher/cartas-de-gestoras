"""Arte de LinkedIn da edicao — SO O GRAFICO (1200x1200, padrao CLARO da casa).

Difere do `divulgacao/linkedin.py`, que monta uma peca 1200x627 com texto ao lado
do grafico. Aqui a peca e o grafico inteiro: quadrado (ocupa mais altura no feed)
e sem argumento escrito na arte — o argumento vai na copy.

Os numeros vem de `dados_do_exercicio()`, os MESMOS do PDF e do carrossel.
Tokens: padrao claro decidido em 11/09 (social/carousel_post_html.py do ROI).

Edicao de 29/09: beta do Ibovespa em dolar ao S&P 500 por regime. Painel 1 = as
semanas desde 2004, separadas por regime, com a reta de cada um (a prova);
painel 2 = a distancia do S&P 500 ate a maxima, com a linha dos -10% e o ponto
de hoje (onde estamos). As versoes anteriores estao no historico do git.
"""
import sys, pathlib
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

D = pathlib.Path(__file__).parent
sys.path.insert(0, str(D.parent))
from carrossel import dados_do_exercicio, regimes   # noqa: E402

d   = dados_do_exercicio()
r   = regimes(d)
ret = d['ret']
dd  = d['dd'] * 100                                   # semanal, como o regime
dd_x, dd_y = d['dd_diario'].dropna().index[-1], r['dd_hoje'] * 100

# --- tokens da casa (padrao CLARO) ---
PAPER, NAVY, INK   = '#FFFFFF', '#0A1A3C', '#16202E'
INK_SOFT, MUTED    = '#3A4757', '#8894A5'
LINE, BLUE         = '#E6EAF0', '#1CA0D8'
RED, AMBER         = '#E5484D', '#F5A524'

vir = lambda x, n=2: f'{x:.{n}f}'.replace('.', ',').replace('-', '−')
pct = lambda v, _=None: f'{v:.0f}%'.replace('-', '−')
CAIXA = dict(boxstyle='round,pad=.3', facecolor='white', edgecolor='none', alpha=.95)

fig, (ax, bx) = plt.subplots(
    2, 1, figsize=(10, 10), dpi=120,
    gridspec_kw={'height_ratios': [1.35, 1], 'hspace': .42})
fig.patch.set_facecolor(PAPER)

# ---------------- titulo (na FIGURA: o pad do eixo corta) ----------------
fig.text(.105, .963, 'Quando Nova York entra em correção,', fontsize=25, color=NAVY,
         weight='bold', va='top')
fig.text(.105, .925, 'o Brasil cai mais', fontsize=25, color=NAVY,
         weight='bold', va='top')
fig.text(.105, .888,
         'Retorno semanal do Ibovespa em dólar contra o do S&P 500, por regime',
         fontsize=13.5, color=INK_SOFT, va='top')
fig.text(.105, .862,
         f'correção = S&P 500 mais de 10% abaixo da máxima de 252 pregões · '
         f'{ret.index.min():%Y}–{ret.index.max():%Y}',
         fontsize=13.5, color=INK_SOFT, va='top')

# ---------------- painel 1: a dispersao por regime ----------------
ax.set_facecolor(PAPER)
for regime, cor, alfa in (('calmo', BLUE, .30), ('correção', RED, .60)):
    m = ret['correcao'] if regime == 'correção' else ~ret['correcao']
    sub = ret[m]
    b, a, _, _ = d['res'][regime]['ibov']
    ax.scatter(sub['spx'] * 100, sub['ibov'] * 100, s=14, alpha=alfa, color=cor, lw=0, zorder=3)
    xx = np.linspace(-12, 8, 50) / 100
    ax.plot(xx * 100, (a + b * xx) * 100, color=cor, lw=3.2, zorder=5)
ax.axhline(0, color=MUTED, lw=.9, zorder=2); ax.axvline(0, color=MUTED, lw=.9, zorder=2)
ax.text(-12.3, -22.6,
        f"em correção: beta {vir(r['b_corr'])}\n"
        f"{r['n_corr']} semanas · correlação {vir(r['c_corr'])}",
        fontsize=14, color=RED, weight='bold', va='center', zorder=8, bbox=CAIXA,
        linespacing=1.4)
ax.text(1.0, -17.5,
        f"mercado calmo: beta {vir(r['b_calmo'])}\n"
        f"{r['n_calmo']} semanas · correlação {vir(r['c_calmo'])}",
        fontsize=14, color=BLUE, weight='bold', va='center', zorder=8, bbox=CAIXA,
        linespacing=1.4)
ax.text(-12.3, 17,
        f"Se o S&P 500 cair 20%, o Ibovespa em US$ cai\n"
        f"{vir(abs(r['impl_calmo']) * 100, 0)}% pelo beta calmo · "
        f"{vir(abs(r['impl_corr']) * 100, 0)}% pelo beta de correção",
        fontsize=13, color=INK, va='center', zorder=8, linespacing=1.45,
        bbox=dict(boxstyle='round,pad=.45', facecolor='white', edgecolor=LINE))
ax.set_xlim(-13, 9); ax.set_ylim(-27, 22)
ax.set_xticks([-10, -5, 0, 5]); ax.set_yticks([-20, -10, 0, 10, 20])
ax.xaxis.set_major_formatter(FuncFormatter(pct)); ax.yaxis.set_major_formatter(FuncFormatter(pct))
ax.set_xlabel('S&P 500, retorno semanal', fontsize=14, color=INK_SOFT, labelpad=8)
ax.set_ylabel('Ibovespa em US$, retorno semanal', fontsize=14, color=INK_SOFT, labelpad=10)
ax.grid(True, axis='x', color=LINE, lw=.9)

# ---------------- painel 2: onde estamos ----------------
bx.set_facecolor(PAPER)
bx.fill_between(dd.index, -10, dd.values, where=(dd.values < -10), interpolate=True,
                color=RED, alpha=.25, lw=0, zorder=2)
bx.plot(dd.index, dd.values, lw=1.4, color=NAVY, zorder=4)
bx.axhline(-10, color=RED, lw=1.4, ls=(0, (5, 4)), zorder=3)
bx.text(.36, -11.5, 'abaixo de −10%: regime de correção', transform=bx.get_yaxis_transform(),
        fontsize=13, color=RED, va='top', zorder=8,
        bbox=dict(boxstyle='round,pad=.2', facecolor='white', edgecolor='none', alpha=.9))
bx.scatter([dd_x], [dd_y], s=165, c=AMBER, edgecolors='white', linewidths=1.9, zorder=7)
bx.annotate(f'hoje: {vir(dd_y, 1)}% — regime calmo', xy=(dd_x, dd_y), xytext=(-26, 24),
            textcoords='offset points', ha='right', va='bottom', fontsize=14,
            color=INK, zorder=9, bbox=CAIXA,
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=1.3, shrinkA=0, shrinkB=8))
bx.text(0, 1.10, 'E hoje? Nova York segue longe da correção',
        transform=bx.transAxes, fontsize=16.5, color=NAVY, weight='bold')
bx.text(0, 1.022, 'S&P 500: distância da máxima de 252 pregões (%) · fechamento semanal',
        transform=bx.transAxes, fontsize=13, color=INK_SOFT)
bx.set_ylim(-57, 24); bx.set_yticks([-40, -20, 0])
bx.yaxis.set_major_formatter(FuncFormatter(pct))
bx.xaxis.set_major_locator(mdates.YearLocator(4))
bx.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
bx.margins(x=.015)
bx.grid(True, axis='y', color=LINE, lw=.9)

for a in (ax, bx):
    a.tick_params(labelsize=13.5, colors=INK_SOFT, length=0)
    a.set_axisbelow(True)
    for s in ('top', 'right'): a.spines[s].set_visible(False)
    for s in ('left', 'bottom'): a.spines[s].set_color(LINE)

fig.text(.105, .022,
         'analisemacro.com.br  ·  Fonte: Yahoo Finance (^GSPC, ^BVSP, BRL=X)  ·  '
         f'S&P 500 até {d["spx"].index[-1]:%d/%m/%Y}',
         fontsize=12.3, color=MUTED)

fig.subplots_adjust(left=.105, right=.975, top=.822, bottom=.115)
fig.savefig(D / 'linkedin-sintese-cartas.png', facecolor=PAPER)
print('OK -> linkedin-sintese-cartas.png')
print(f"   beta calmo {vir(r['b_calmo'])} (n={r['n_calmo']}) · correção {vir(r['b_corr'])} (n={r['n_corr']})")
print(f"   S&P -20% -> Ibov US$ {vir(r['impl_calmo']*100,1)}% / {vir(r['impl_corr']*100,1)}%")
print(f"   dólar: {vir(r['fx_calmo'])} / {vir(r['fx_corr'])} · drawdown hoje {vir(dd_y,1)}% "
      f"· beta móvel {vir(r['beta_hoje'])} em {r['data_beta']:%d/%m} (pct {r['pct_beta']:.0f})")
