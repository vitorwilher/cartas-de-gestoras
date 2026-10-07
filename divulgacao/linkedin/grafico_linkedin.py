"""Arte de LinkedIn da edicao — SO O GRAFICO (1200x1200, padrao CLARO da casa).

Difere do `divulgacao/linkedin.py`, que monta uma peca 1200x627 com texto ao lado
do grafico. Aqui a peca e o grafico inteiro: quadrado (ocupa mais altura no feed)
e sem argumento escrito na arte — o argumento vai na copy.

Os numeros vem de `petroleo()` do carrossel, os MESMOS do post do Instagram
(semanas encerradas). Tokens: padrao claro decidido em 11/09.

Edicao de 07/10: a Kinea carrega petroleo como hedge de juros aplicados e bolsa
comprada. Painel 1 = o Brent medio em cada decil da carteira 50% EWZ + 50%
IMAB11 (a prova: no decil 1 ele caiu); painel 2 = a correlacao movel de 52
semanas e o ponto de hoje (onde estamos). As versoes anteriores estao no git.
"""
import sys, pathlib
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

D = pathlib.Path(__file__).parent
sys.path.insert(0, str(D.parent))
from carrossel import dados_do_exercicio, petroleo   # noqa: E402

d = dados_do_exercicio()
p = petroleo(d)
bd, cd = p['brent_decil'], p['cart_decil']
c = p['corr']

# --- tokens da casa (padrao CLARO) ---
PAPER, NAVY, INK   = '#FFFFFF', '#0A1A3C', '#16202E'
INK_SOFT, MUTED    = '#3A4757', '#8894A5'
LINE, BLUE         = '#E6EAF0', '#1CA0D8'
RED, AMBER         = '#E5484D', '#F5A524'

def vir(x, n=2):
    if round(x, n) == 0:
        x = 0.0
    return f'{x:.{n}f}'.replace('.', ',').replace('-', '−')

CAIXA = dict(boxstyle='round,pad=.3', facecolor='white', edgecolor='none', alpha=.95)

fig, (ax, bx) = plt.subplots(
    2, 1, figsize=(10, 10), dpi=120,
    gridspec_kw={'height_ratios': [1.25, 1], 'hspace': .62})
fig.patch.set_facecolor(PAPER)

# ---------------- titulo (na FIGURA: o pad do eixo corta) ----------------
fig.text(.105, .963, 'Nas piores semanas de bolsa e juro Brasil,', fontsize=25,
         color=NAVY, weight='bold', va='top')
fig.text(.105, .925, 'o petróleo caiu junto', fontsize=25, color=NAVY,
         weight='bold', va='top')
fig.text(.105, .888,
         'Retorno médio semanal do Brent em cada decil da carteira 50% EWZ + 50% IMAB11',
         fontsize=13.5, color=INK_SOFT, va='top')
fig.text(.105, .862,
         f'decil 1 = as 10% piores semanas da carteira · '
         f'{p["inicio"]:%m/%Y} a {p["fim"]:%d/%m/%Y}, {p["n"]} semanas',
         fontsize=13.5, color=INK_SOFT, va='top')

# ---------------- painel 1: Brent por decil ----------------
ax.set_facecolor(PAPER)
cores = [RED if k == 1 else '#C9D3DF' for k in bd.index]
ax.bar(bd.index, bd.values, width=.66, color=cores, zorder=3)
ax.axhline(0, color=NAVY, lw=1.4, zorder=4)
for k, v in bd.items():
    ax.text(k, v + (.18 if v >= 0 else -.18), vir(v, 1), ha='center',
            va='bottom' if v >= 0 else 'top', fontsize=15 if k == 1 else 12.5,
            color=RED if k == 1 else MUTED, weight='bold' if k == 1 else 'normal')
ax.text(2.5, bd.loc[1] - .55,
        f'nas piores semanas, a carteira caiu {vir(abs(cd.loc[1]), 1)}%\n'
        f'e o Brent, {vir(abs(bd.loc[1]), 1)}% — caiu junto, não protegeu',
        fontsize=13.5, color=RED, weight='bold', va='center', zorder=8, bbox=CAIXA,
        linespacing=1.4)
ax.set_xticks(range(1, 11))
ax.set_xticklabels(['1\npior'] + [str(k) for k in range(2, 10)] + ['10\nmelhor'])
ax.set_ylim(min(bd.min() - 1.6, -3.8), bd.max() + 1)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.0f}%'.replace('-', '−')))
ax.set_xlabel('decil do retorno semanal da carteira', fontsize=14, color=INK_SOFT, labelpad=8)
ax.grid(True, axis='y', color=LINE, lw=.9)

# ---------------- painel 2: onde estamos ----------------
bx.set_facecolor(PAPER)
bx.fill_between(c.index, 0, c.values, where=(c.values > 0), color=BLUE, alpha=.14, lw=0, zorder=2)
bx.plot(c.index, c.values, lw=1.8, color=NAVY, zorder=4)
bx.axhline(0, color=MUTED, lw=1.1, zorder=3)
x, y = c.index[-1], p['corr_hoje']
bx.scatter([x], [y], s=165, c=AMBER, edgecolors='white', linewidths=1.9, zorder=7)
bx.annotate(f'hoje: {vir(y)} — entre as {p["pct_hoje"]:.0f}% mais baixas',
            xy=(x, y), xytext=(-26, -46), textcoords='offset points', ha='right',
            va='top', fontsize=14, color=INK, zorder=9, bbox=CAIXA,
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=1.3, shrinkA=0, shrinkB=8))
bx.text(0, 1.10, 'E hoje? O petróleo parou de cair junto — mas ainda não protege',
        transform=bx.transAxes, fontsize=16.5, color=NAVY, weight='bold')
bx.text(0, 1.022, 'Correlação de 52 semanas, Brent × carteira · acima de zero, andam juntos',
        transform=bx.transAxes, fontsize=13, color=INK_SOFT)
bx.set_ylim(-.45, .75)
bx.yaxis.set_major_formatter(FuncFormatter(lambda v, _: vir(v, 1)))
bx.xaxis.set_major_locator(mdates.YearLocator(1))
bx.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
bx.margins(x=.015)
bx.grid(True, axis='y', color=LINE, lw=.9)

for a in (ax, bx):
    a.tick_params(labelsize=13.5, colors=INK_SOFT, length=0)
    a.set_axisbelow(True)
    for s in ('top', 'right'): a.spines[s].set_visible(False)
    for s in ('left', 'bottom'): a.spines[s].set_color(LINE)

fig.text(.105, .022,
         'analisemacro.com.br  ·  Yahoo Finance (EWZ, IMAB11.SA, BZ=F)  ·  '
         f'até {p["fim"]:%d/%m/%Y}',
         fontsize=12.3, color=MUTED)

fig.subplots_adjust(left=.105, right=.975, top=.822, bottom=.115)
fig.savefig(D / 'linkedin-sintese-cartas.png', facecolor=PAPER)
print('OK -> linkedin-sintese-cartas.png')
print(f"   decil 1: carteira {vir(cd.loc[1], 2)}%/sem, Brent {vir(bd.loc[1], 2)}%/sem")
print(f"   correlação hoje {vir(y, 3)} (pct {p['pct_hoje']:.0f}) · amostra inteira {vir(p['corr_total'])}")
print(f"   pior 4 semanas: {vir(p['pior4'][0], 1)}% sem Brent, {vir(p['pior4'][-1], 1)}% com 60%")
