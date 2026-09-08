#!/usr/bin/env python3
"""Gera o catalogo.json que o MCP consome, a partir dos .qmd em digests/resumo/.

O Worker busca esse artefato num release do GitHub — mesmo padrão do
`nucleos-mcp`, que lê o release `dashboard-dados`. Assim o servidor se atualiza
sem re-deploy.

Uso:
    python mcp/gerar_catalogo.py            # escreve mcp/catalogo.json
    python mcp/gerar_catalogo.py --stdout   # imprime, para inspeção
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIGESTS = RAIZ / "digests" / "resumo"


def corpo_do_qmd(texto: str) -> str:
    """Descarta o preâmbulo YAML e o bloco LaTeX da capa."""
    marcador = "\\clearpage\n```"
    return texto.split(marcador, 1)[-1].strip() if marcador in texto else texto


def separar_exercicio(corpo: str) -> tuple[str, str, str]:
    """Divide o corpo em (síntese, exercício, conceito)."""
    padrao = r"(?m)^## Exercício da semana:?\s*(.*)$"
    achado = re.search(padrao, corpo)
    if not achado:
        return corpo, "", ""
    inicio = achado.start()
    return corpo[:inicio].strip(), corpo[inicio:].strip(), achado.group(1).strip()


def extrair_fontes(corpo: str) -> list[dict]:
    """Lê a seção 'Cartas originais' no formato que escrever_qmd() produz."""
    fontes = []
    for linha in corpo.splitlines():
        m = re.match(r"-\s+\*\*(.+?)\s+—\s+(.+?)\*\*\s+\(\[original\]\((.+?)\)\)", linha.strip())
        if m:
            fontes.append({"gestora": m.group(1), "titulo": m.group(2), "url": m.group(3)})
    return fontes


def extrair_gestoras(sintese: str) -> list[str]:
    """As seções de nível 2, menos as que não são gestoras."""
    ignorar = {"convergências e divergências", "cartas originais"}
    achadas = []
    for m in re.finditer(r"(?m)^## (.+)$", sintese):
        nome = m.group(1).strip()
        if nome.lower().startswith("exercício"):
            continue
        if nome.lower() in ignorar:
            continue
        # "Kinea Investimentos — Série principal (...)" -> "Kinea Investimentos"
        achadas.append(nome.split("—")[0].strip())
    return achadas


def resumo_executivo(qmd_texto: str, sintese: str) -> str:
    """Uma linha em texto puro descrevendo a edição.

    O comentário `resumo_whatsapp` só existe na resposta bruta do modelo:
    `resumo_para_whatsapp()` o remove antes de gravar o .qmd, porque ele é
    destinado ao WhatsApp e não ao PDF. Por isso o caminho normal aqui é o
    fallback — que precisa entregar texto limpo, sem Markdown.
    """
    m = re.search(r"<!--\s*resumo_whatsapp:\s*(.*?)\s*-->", qmd_texto, re.DOTALL | re.IGNORECASE)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()

    # Preferimos a seção comparativa: é a que resume a edição inteira.
    partes = re.split(r"(?m)^##\s+Converg[êe]ncias e diverg[êe]ncias\s*$", sintese)
    trecho = partes[-1] if len(partes) > 1 else sintese
    # A lista de fontes vem logo depois e não é resumo — corta no separador.
    trecho = re.split(r"(?m)^##\s+Cartas originais\s*$|^---\s*$", trecho)[0]
    trecho = re.sub(r"(?m)^#.*$", "", trecho)          # títulos
    trecho = re.sub(r"```.*?```", "", trecho, flags=re.DOTALL)  # blocos de código
    trecho = re.sub(r"[*_`#>\[\]]", "", trecho)        # marcação inline
    trecho = re.sub(r"\s+", " ", trecho).strip()
    if len(trecho) <= 450:
        return trecho
    return trecho[:447].rsplit(" ", 1)[0] + "..."


def montar() -> dict:
    edicoes = []
    for qmd in sorted(DIGESTS.glob("resumo-*.qmd"), reverse=True):
        m = re.search(r"resumo-(\d{4}-\d{2}-\d{2})\.qmd$", qmd.name)
        if not m:
            continue
        texto = qmd.read_text(encoding="utf-8")
        corpo = corpo_do_qmd(texto)
        sintese, exercicio, conceito = separar_exercicio(corpo)
        edicoes.append({
            "data": m.group(1),
            "gestoras": extrair_gestoras(sintese),
            "conceito": conceito,
            "resumo_executivo": resumo_executivo(texto, sintese),
            "markdown": sintese,
            "exercicio": exercicio,
            "fontes": extrair_fontes(corpo),
        })
    return {
        "atualizado_em": datetime.now(timezone.utc).date().isoformat(),
        "edicoes": edicoes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdout", action="store_true", help="imprime em vez de gravar")
    args = parser.parse_args()

    catalogo = montar()
    if not catalogo["edicoes"]:
        print("Nenhum digest encontrado em digests/resumo/", file=sys.stderr)
        return 1

    saida = json.dumps(catalogo, ensure_ascii=False, indent=2)
    if args.stdout:
        print(saida)
    else:
        destino = Path(__file__).resolve().parent / "catalogo.json"
        destino.write_text(saida, encoding="utf-8")
        print(f"{len(catalogo['edicoes'])} edição(ões) em {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
