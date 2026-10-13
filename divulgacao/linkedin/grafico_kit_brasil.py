"""Arte de LinkedIn da edição de 13/10/2026 — os gráficos do exercício "kit Brasil".

Os números saem do PRÓPRIO código do exercício (o bloco ```python da edição),
executado até o diagnóstico; aqui só se redesenha no padrão CLARO da casa, com
título e medida em cada painel (ver `grafico_linkedin.py`, peça de 07/10).
Painel 1 = índice de diversificação (o veredito); painel 2 = fração do risco no
primeiro componente principal (a mesma história em outra métrica).
"""
import os, re, sys, pathlib, tempfile
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

D = pathlib.Path(__file__).parent
QMD = D.parents[1] / 'digests' / 'resumo' / 'resumo-2026-10-13.qmd'

codigo = re.search(r"```python\n(.*?)```", QMD.read_text(encoding='utf-8'), re.S).group(1)
codigo = codigo.split('# ---------------------------------------------------------------- gráfico')[0]
ns = {}
with tempfile.TemporaryDirectory() as tmp:
    os.chdir(tmp)
    exec(compile(codigo, 'exercicio', 'exec'), ns)
diag, esc = ns['diag'], ns['esc']
dr, pc1 = diag['dr'], diag['pc1']
hoje = diag.index[-1]
antes = diag.loc[:'2026-10-02'].iloc[-1]
pct = (dr < dr.iloc[-1]).mean() * 100

# --- tokens da casa (padrao CLARO) ---
PAPER, NAVY, INK   = '#FFFFFF', '#0A1A3C', '#16202E'
INK_SOFT, MUTED    = '#3A4757', '#8894A5'
LINE, BLUE         = '#E6EAF0', '#1CA0D8'
RED, AMBER         = '#E5484D', '#F5A524'
CAIXA = dict(boxstyle='round,pad=.35', facecolor='white', edgecolor='none', alpha=.95)

def vir(x, n=2):
    return f'{x:.{n}f}'.replace('.', ',').replace('-', '−')

fig, (ax, bx) = plt.subplots(2, 1, figsize=(10, 12.5), dpi=120,
                             gridspec_kw={'height_ratios': [1.15, 1], 'hspace': .42})
fig.patch.set_facecolor(PAPER)

fig.text(.105, .968, 'Depois do primeiro turno, o "kit Brasil"', fontsize=25,
         color=NAVY, weight='bold', va='top')
fig.text(.105, .936, 'virou uma aposta só', fontsize=25, color=NAVY, weight='bold', va='top')
fig.text(.105, .903, 'Real comprado, juros aplicados e Ibovespa comprado, cada perna a 10% de vol ao ano',
         fontsize=13.5, color=INK_SOFT, va='top')
fig.text(.105, .882, f'janelas móveis de 63 dias úteis · {esc.index[0]:%m/%Y} a {hoje:%d/%m/%Y}',
         fontsize=13.5, color=INK_SOFT, va='top')

# ---------------- painel 1: índice de diversificação ----------------
ax.set_facecolor(PAPER)
ax.plot(dr.index, dr.values, lw=1.7, color=NAVY, zorder=4)
for nivel, rot in ((3 ** .5, '1,73 = três apostas independentes'), (1.0, '1,00 = uma aposta só')):
    ax.axhline(nivel, color=MUTED, lw=1.1, ls=(0, (3, 3)), zorder=2)
    ax.text(dr.index[0], nivel + .025, rot, fontsize=12.5, color=MUTED, va='bottom')
ax.scatter([hoje], [dr.iloc[-1]], s=170, c=RED, edgecolors='white', linewidths=1.9, zorder=7)
ax.annotate(f'09/10: {vir(dr.iloc[-1])}, a menor leitura desde 2019\n'
            f'(era {vir(antes["dr"])} em 02/10, antes do 1º turno)',
            xy=(hoje, dr.iloc[-1]), xytext=(-30, -6), textcoords='offset points', ha='right',
            va='center', fontsize=14, color=RED, weight='bold', zorder=9, bbox=CAIXA,
            linespacing=1.4, arrowprops=dict(arrowstyle='-', color=RED, lw=1.2, shrinkB=8))
ax.text(0, 1.10, 'Quanto o kit diversifica de fato', transform=ax.transAxes,
        fontsize=16.5, color=NAVY, weight='bold')
ax.text(0, 1.03, 'Índice de diversificação: média das vols das pernas ÷ vol do kit',
        transform=ax.transAxes, fontsize=13, color=INK_SOFT)
ax.set_ylim(.9, 1.85)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: vir(v, 1)))

# ---------------- painel 2: fração do risco no 1º fator ----------------
bx.set_facecolor(PAPER)
bx.fill_between(pc1.index, 1 / 3, pc1.values, color=BLUE, alpha=.14, lw=0, zorder=2)
bx.plot(pc1.index, pc1.values, lw=1.7, color=NAVY, zorder=4)
bx.axhline(1 / 3, color=MUTED, lw=1.1, ls=(0, (3, 3)), zorder=2)
bx.text(pc1.index[0], 1 / 3 - .03, '1/3 = nada em comum', fontsize=12.5, color=MUTED, va='top')
bx.scatter([hoje], [pc1.iloc[-1]], s=170, c=RED, edgecolors='white', linewidths=1.9, zorder=7)
bx.annotate(f'09/10: {pc1.iloc[-1]:.0%} do risco num fator só'.replace('%', ' %').replace(' %', '%'),
            xy=(hoje, pc1.iloc[-1]), xytext=(-30, 0), textcoords='offset points', ha='right',
            va='center', fontsize=14, color=RED, weight='bold', zorder=9, bbox=CAIXA,
            arrowprops=dict(arrowstyle='-', color=RED, lw=1.2, shrinkB=8))
bx.text(0, 1.10, 'Quanto do risco vem de um único fator', transform=bx.transAxes,
        fontsize=16.5, color=NAVY, weight='bold')
bx.text(0, 1.03, 'Fração da variância no 1º componente principal · 1 = um fator só',
        transform=bx.transAxes, fontsize=13, color=INK_SOFT)
bx.set_ylim(.2, .9)
bx.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.0%}'))

for a in (ax, bx):
    a.tick_params(labelsize=13.5, colors=INK_SOFT, length=0)
    a.set_axisbelow(True)
    a.grid(True, axis='y', color=LINE, lw=.9)
    a.xaxis.set_major_locator(mdates.YearLocator(1))
    a.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    a.margins(x=.015)
    for s in ('top', 'right'): a.spines[s].set_visible(False)
    for s in ('left', 'bottom'): a.spines[s].set_color(LINE)

fig.text(.105, .018,
         'analisemacro.com.br  ·  Yahoo Finance (USDBRL=X, ^BVSP) e Tesouro Direto (IPCA+ 2035)',
         fontsize=12.3, color=MUTED)
fig.subplots_adjust(left=.105, right=.975, top=.80, bottom=.06)
fig.savefig(D / 'linkedin-kit-brasil.png', facecolor=PAPER)

# --- conferência: quanto do resultado é o pregão de 05/10 ---
import numpy as np
W = esc.iloc[-63:]; Wx = W.drop(pd_idx := W.index[W.index == '2026-10-05'])
def _dr(w): return w.std().mean() / w.mean(axis=1).std()
def _pc1(w): return np.linalg.eigvalsh(np.corrcoef(w.values, rowvar=False))[-1] / 3
print('OK -> linkedin-kit-brasil.png')
print(f'   09/10: DR {vir(dr.iloc[-1], 3)} (pct {pct:.0f}) · PC1 {vir(pc1.iloc[-1], 3)} · 02/10: DR {vir(antes["dr"], 3)} PC1 {vir(antes["pc1"], 3)}')
print(f'   sem o pregão de 05/10: DR {vir(_dr(Wx), 3)} · PC1 {vir(_pc1(Wx), 3)}')
print(f'   vol kit {W.mean(axis=1).std()*252**.5:.1%} vs indep {W.std().mean()*252**.5/3**.5:.1%}')
print(f'   correlações 63d:\n{W.corr().round(2).to_string()}')
print(f'   DR histórico: média {vir(dr.mean())}, 2ª menor leitura fora de out/26 {vir(dr.loc[:"2026-10-02"].min())} em {dr.loc[:"2026-10-02"].idxmin():%d/%m/%Y}')
print(f'   retornos de 05/10 (escalados): {esc.loc["2026-10-05"].round(4).to_dict()}')
