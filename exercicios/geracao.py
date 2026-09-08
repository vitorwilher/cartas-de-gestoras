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

MODEL = os.environ.get("ANTHROPIC_MODEL") or "claude-opus-5"

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
3. **O código** — Python, em UM bloco ```python. Deve rodar de ponta a ponta.
   Use fontes públicas e gratuitas de dados brasileiros (yfinance, python-bcb,
   pyettj, pandas). Comente em português. Sem `!pip install` (não é notebook);
   liste as dependências em texto antes do bloco.
4. **Como ler o resultado** — o que o número significa para a tese da gestora, e
   qual valor mudaria a conclusão.
5. **Vá além** — uma variação que o leitor pode tentar sozinho.

Rigor: nada de código que não roda, nada de API paga, nada de dado inventado.
Se precisar de um ticker ou série, use um real e diga qual é. Sem emojis."""


def escolher_conceito(resumo: str) -> str | None:
    """Devolve o conceito dominante da edição, ou None se o acervo não cobrir nada."""
    conceitos = conceitos_disponiveis()
    if not conceitos:
        print("Acervo vazio: exercício será pulado.", file=sys.stderr)
        return None
    prompt = PROMPT_CONCEITO.format(conceitos="\n".join(f"- {c}" for c in conceitos))
    resposta = Anthropic().messages.create(
        model=MODEL,
        max_tokens=64,
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
    with Anthropic().messages.stream(
        model=MODEL,
        max_tokens=16_000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=sistema,
        messages=[{"role": "user", "content": "Escreva o exercício desta semana."}],
    ) as stream:
        final = stream.get_final_message()
    return "\n".join(b.text for b in final.content if b.type == "text").strip()


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
        print(f"Exercício da semana falhou ({erro}); seguindo sem ele.", file=sys.stderr)
        return None
