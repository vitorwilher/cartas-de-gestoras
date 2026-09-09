"""Executa o código do exercício para produzir o gráfico que entra no PDF.

O modelo escreve um bloco ```python que salva `grafico-exercicio.png`, e o texto
referencia essa imagem. Sem alguém rodar o código, o Typst aborta com
"file not found" — o documento inteiro se perde por causa de uma figura.

Este módulo roda o bloco num diretório temporário, com timeout, e devolve o
caminho do PNG. Falha aqui não derruba a edição: a referência à imagem é removida
do texto e a síntese segue sem a figura.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

NOME_GRAFICO = "grafico-exercicio.png"
TIMEOUT_S = 180


def extrair_codigo(markdown: str) -> str | None:
    """Devolve o primeiro bloco ```python do exercício."""
    achado = re.search(r"```python\n(.*?)```", markdown, re.DOTALL)
    return achado.group(1) if achado else None


def remover_referencia(markdown: str) -> str:
    """Tira a linha ![...](grafico-exercicio.png) quando não há figura.

    Sem isso o Typst aborta o documento inteiro por causa de uma imagem ausente.
    """
    padrao = rf"(?m)^!\[[^\]]*\]\({re.escape(NOME_GRAFICO)}\)\s*$\n?"
    return re.sub(padrao, "", markdown)


def gerar_grafico(markdown: str, destino: Path, python: str | None = None) -> Path | None:
    """Roda o código do exercício e copia o PNG para `destino`.

    Devolve o caminho do arquivo, ou None se o código falhar, estourar o tempo ou
    simplesmente não gerar figura.
    """
    codigo = extrair_codigo(markdown)
    if not codigo:
        print("[aviso] exercício sem bloco python; sem gráfico.", file=sys.stderr)
        return None

    executavel = python or sys.executable
    with tempfile.TemporaryDirectory(prefix="cartas-exercicio-") as tmp:
        trabalho = Path(tmp)
        script = trabalho / "exercicio.py"
        # Backend não-interativo: um plt.show() esquecido travaria o pipeline.
        script.write_text(
            'import matplotlib\nmatplotlib.use("Agg")\n' + codigo, encoding="utf-8"
        )
        try:
            proc = subprocess.run(
                [executavel, script.name],
                cwd=trabalho, capture_output=True, text=True, timeout=TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            print(f"[aviso] exercício excedeu {TIMEOUT_S}s; sem gráfico.", file=sys.stderr)
            return None

        if proc.returncode != 0:
            erro = (proc.stderr or "").strip().splitlines()
            print(f"[aviso] exercício falhou: {erro[-1] if erro else '?'}", file=sys.stderr)
            return None

        origem = trabalho / NOME_GRAFICO
        if not origem.exists():
            achados = sorted(trabalho.glob("*.png"))
            if not achados:
                print("[aviso] exercício rodou mas não gerou PNG.", file=sys.stderr)
                return None
            origem = achados[0]  # salvou com outro nome; aproveitamos assim mesmo

        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, destino)
        return destino
