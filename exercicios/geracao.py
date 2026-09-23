"""Gera o exercício em Python da semana, a partir do conceito dominante nas cartas.

Dois estágios de LLM:
  1. `escolher_conceito` — lê a síntese e devolve o mecanismo que mais aparece,
     restrito aos conceitos que o acervo cobre.
  2. `gerar_exercicio` — escreve o exercício novo. O item do acervo entra apenas
     como referência de abordagem didática: o código de 2022 tem defeitos e não
     pode ser reentregue (ver CLAUDE.md).
"""

from __future__ import annotations

import os
import sys

from anthropic import Anthropic

from .selecao import Exercicio, candidatos_por_conceito, conceitos_disponiveis

MODEL = os.environ.get("ANTHROPIC_MODEL") or "claude-fable-5-1"
# A escolha do conceito é classificação, não redação: modelo menor, resposta direta.
MODELO_CLASSIFICACAO = "claude-sonnet-5"

PROMPT_CONCEITO = """Leia a síntese das cartas de gestoras abaixo e identifique qual
mecanismo quantitativo é o mais central nas teses desta edição.

Responda com EXATAMENTE um dos conceitos desta lista, sem nenhuma outra palavra:
{conceitos}

Escolha o conceito que um profissional do mercado precisaria dominar para avaliar
criticamente as apostas descritas — não o mais citado, e sim o mais decisivo para
as teses."""

PROMPT_EXERCICIO = """Você escreve o exercício prático de um produto de assinatura
para profissionais do mercado financeiro brasileiro.

A promessa do produto: ensinar a DESTRINCHAR TECNICAMENTE as teses das gestoras.
O exercício é a prova dessa promessa — ele pega um mecanismo citado nas cartas da
semana e mostra, em código, como se verifica aquilo com dados reais.

Conceito da semana: {conceito}

Trecho da síntese que motiva o exercício:
{contexto}

Escreva em Markdown para Quarto, começando com "## Exercício da semana: <título>".
Estrutura:
1. **Por que isto importa esta semana** — ligue explicitamente à tese de uma gestora
   citada na síntese. Uma frase ou duas.
2. **O conceito** — a intuição econômica antes da fórmula. O leitor é do mercado:
   não explique o óbvio, explique o mecanismo.
3. **O código** — Python, em UM bloco ```python. Deve rodar de ponta a ponta
   **num terminal, sem interação**. Use SOMENTE estas bibliotecas, que são as
   instaladas no ambiente: pandas, numpy, matplotlib, requests, python-bcb (`from
   bcb import sgs`), yfinance e pyettj. Qualquer outra falha com ModuleNotFoundError
   e a edição sai sem o gráfico. Comente em português.
   Sem `!pip install` (não é notebook); liste as dependências em texto antes do
   bloco. Toda leitura de rede leva timeout explícito.

   **Use a biblioteca, nunca raspe o site.** Cada fonte tem um caminho oficial:
   - curva de juros / ETTJ / DI futuro / taxa a termo → `from pyettj import ettj;
     ettj.get_ettj("DD/MM/AAAA")`. **NUNCA** montar request para
     `www2.bmf.com.br/pages/portal/...lum-taxas-referenciais-bmf` — esse endpoint
     responde HTTP 200 com página VAZIA (sem tabela), então o código falha sem
     erro de rede e o exercício sai sem gráfico. Aconteceu em 15/09/2026.
     `get_ettj` levanta HolidayError em fim de semana/feriado: trate voltando ao
     dia útil anterior.
     **Formato da saída (pyettj 0.4.x): tabela LONGA, uma linha por vértice e
     curva**, colunas `refdate, curva, descricao, dias_corridos, dias_uteis,
     taxa, vertice`. A curva DI x pré é `curva == "PRE"`; `taxa` já vem em
     DECIMAL (0.1365 = 13,65% a.a., base 252). NÃO procure coluna "DI x pré 252"
     nem divida por 100: esse era o formato largo antigo, e o código que o
     assume quebra com IndexError (23/09/2026).
   - séries do Banco Central (Selic, IPCA, câmbio, crédito) → `from bcb import sgs`.
     **NUNCA use a série 7 (Ibovespa) do SGS: ela está CONGELADA desde 30/09/2019**
     e o BCB a devolve normalmente, sem erro — alinhar qualquer coisa com ela
     trunca a amostra em 2019 e o gráfico sai com sete anos de atraso exibindo
     "hoje". Para Ibovespa use `yfinance` (`^BVSP`).
   - preços de ativos → `yfinance`

   **Toda série precisa passar por um teste de frescor.** Depois de baixar, cheque
   que a última data está a menos de ~10 dias da data de hoje; se não estiver, a
   fonte morreu em silêncio — troque de fonte ou levante erro explicando. Um HTTP
   200 não prova que o dado está atualizado. Isso já derrubou dois exercícios:
   a curva da B3 (página vazia) e o Ibovespa do SGS (série parada em 2019).

   **O exercício SEMPRE produz um gráfico** — é ele que faz o argumento visual.
   Regras invioláveis:
   - **Nunca `plt.show()`**: bloqueia esperando alguém fechar a janela e trava o
     script. Use `plt.savefig("grafico-exercicio.png", dpi=150, bbox_inches="tight")`
     com exatamente esse nome de arquivo.
   - O gráfico precisa mostrar o MECANISMO em discussão, não enfeitar: se o tema é
     inclinação de curva, plote a curva e a série histórica da inclinação; marque no
     desenho o ponto de hoje contra a distribuição passada.
   - Rotule os eixos em português, com unidade. Anote no próprio gráfico o número
     que sustenta a conclusão.
   - **Nunca descarte amostra sem perceber.** `DataFrame.dropna()` sem argumento
     exige TODAS as colunas preenchidas: com três séries móveis, um buraco isolado
     em qualquer uma apaga a linha inteira. Em 15/09/2026 isso cortou 847 das 1.358
     observações e o painel mostrou só o último ano, enquanto a legenda prometia
     quatro. Use `dropna(how="all")` ou descarte coluna a coluna, e **confira o
     alcance real da série que plotou antes de descrevê-lo na legenda** — a legenda
     é conferida contra a figura, e divergência ali derruba a credibilidade do
     documento inteiro.

4. **O gráfico no texto** — logo após o bloco de código, insira a linha
   `![Legenda](grafico-exercicio.png)` para que a imagem entre no PDF.
   A legenda descreve **o que o leitor vê**, painel por painel, com os valores e
   prazos EXATOS que o seu código usou — nada de arredondar ou trocar o vértice.
   Ela é a primeira coisa que alguém confere contra o gráfico; se divergir, o
   documento inteiro perde credibilidade.

5. **Como o gráfico foi construído** — antes ou depois da figura, explique em 2-3
   frases as decisões de construção que um leitor técnico questionaria: por que
   estes vértices e não outros, de onde vem cada série, como foi feita a
   interpolação, e que ajuste os dados exigiram. O leitor quer poder refazer o
   gráfico, não só olhar.
6. **Como ler o resultado** — o que o número significa para a tese da gestora, e
   qual valor mudaria a conclusão. Cite o que o gráfico mostra.
7. **Vá além** — uma variação que o leitor pode tentar sozinho.

Rigor: nada de código que não roda, nada de API paga, nada de dado inventado.
Se precisar de um ticker ou série, use um real e diga qual é. Sem emojis."""


def escolher_conceito(resumo: str) -> str | None:
    """Devolve o conceito dominante da edição, ou None se o acervo não cobrir nada."""
    conceitos = conceitos_disponiveis()
    if not conceitos:
        print("Acervo vazio: exercício será pulado.", file=sys.stderr)
        return None
    prompt = PROMPT_CONCEITO.format(conceitos="\n".join(f"- {c}" for c in conceitos))
    # Classificação simples: Sonnet a effort baixo basta e responde direto. No
    # Fable 5.1 com thinking sempre ativo, um teto de 64 tokens é consumido
    # pensando e a resposta volta vazia — verificado em 2026-09-08.
    resposta = Anthropic().messages.create(
        model=MODELO_CLASSIFICACAO,
        max_tokens=512,
        output_config={"effort": "low"},
        system=prompt,
        messages=[{"role": "user", "content": resumo[:20_000]}],
    )
    escolha = "".join(b.text for b in resposta.content if b.type == "text").strip().lower()
    # O modelo pode devolver o conceito com pontuação ou aspas; casa por continência.
    for c in conceitos:
        if c in escolha:
            return c
    print(f"Conceito não reconhecido na resposta: {escolha!r}", file=sys.stderr)
    return None


def gerar_exercicio(conceito: str, resumo: str, referencia: Exercicio | None = None) -> str:
    """Escreve o exercício da semana. `referencia` só orienta a abordagem."""
    contexto = resumo[:12_000]
    sistema = PROMPT_EXERCICIO.format(conceito=conceito, contexto=contexto)
    if referencia is not None:
        sistema += (
            f"\n\nO acervo da casa já tratou este tema em '{referencia.titulo}' "
            f"({referencia.data}). Use isso apenas como referência de abordagem "
            "didática — aquele código é antigo e não deve ser reproduzido."
        )
    # effort "high", não "max": com `max` o Fable 5.1 gasta o orçamento inteiro
    # pensando e a resposta sai truncada (stop_reason=max_tokens) — mesma
    # armadilha da síntese em cartas.py, verificada em 2026-09-08.
    with Anthropic().messages.stream(
        model=MODEL,
        max_tokens=48_000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=sistema,
        messages=[{"role": "user", "content": "Escreva o exercício desta semana."}],
    ) as stream:
        final = stream.get_final_message()

    if final.stop_reason == "max_tokens":
        raise RuntimeError("exercício cortado por max_tokens; sairia incompleto")
    texto = "\n".join(b.text for b in final.content if b.type == "text").strip()
    if not texto:
        raise RuntimeError(f"exercício voltou vazio (stop_reason={final.stop_reason})")
    return texto


def exercicio_da_semana(resumo: str) -> tuple[str, str] | None:
    """Orquestra os dois estágios. Devolve (conceito, markdown) ou None.

    Falha aqui NUNCA derruba a síntese: o exercício é um adicional do produto,
    e a carta já tem valor sem ele.
    """
    try:
        conceito = escolher_conceito(resumo)
        if conceito is None:
            return None
        candidatos = candidatos_por_conceito(conceito)
        referencia = candidatos[0] if candidatos else None
        return conceito, gerar_exercicio(conceito, resumo, referencia)
    except Exception as erro:  # noqa: BLE001 — degradação proposital
        # A síntese já tem valor sozinha, então a falha não derruba o pipeline —
        # mas precisa aparecer: um `0 chars` silencioso custou uma rodada de
        # depuração em 2026-09-08.
        print(f"[erro] exercício da semana: {type(erro).__name__}: {erro}", file=sys.stderr)
        print("Seguindo sem o exercício.", file=sys.stderr)
        return None
