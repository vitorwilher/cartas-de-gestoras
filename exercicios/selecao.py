"""Casa o tema dominante das cartas da semana com um exercício do acervo.

O acervo (`acervo.json`) é um índice de TEMAS — os arquivos originais estão em
Dropbox Smart Sync e seu código é de 2022-2025, com defeitos conhecidos. Ele serve
para escolher o assunto e a abordagem didática; o código entregue ao assinante é
gerado do zero, com dados atuais.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ACERVO = Path(__file__).resolve().parent / "acervo.json"


def sem_acentos(valor: str) -> str:
    decomposto = unicodedata.normalize("NFD", valor)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


@dataclass
class Exercicio:
    """Um item do acervo, com o caminho para buscar o original via MCP."""

    data: str
    titulo: str
    linguagem: str
    caminho_dropbox: str

    def __str__(self) -> str:
        return f"{self.titulo} ({self.data}, {self.linguagem})"


# Mapa de conceito -> termos que aparecem nos títulos do acervo. As chaves são os
# mecanismos que as cartas efetivamente discutem; os valores casam com o índice.
CONCEITOS = {
    "curva de juros": ["estrutura a termo", "ettj", "juros"],
    "volatilidade": ["volatilidade", "garch", "har", "desvio padrao"],
    "portfolio": ["portfolio", "carteira", "markowitz", "hrp", "risk parity"],
    "beta e capm": ["beta", "capm", "capital asset pricing"],
    "fatores": ["fator", "momentum", "fama", "macbeth", "decompondo"],
    "pairs trading": ["cointegracao", "pairs trading"],
    "risco e retorno": ["risco e retorno", "risco x retorno", "sharpe"],
    "monte carlo": ["monte carlo", "simulac"],
    "fundamentalista": ["fundamentalista", "valuation", "dre", "demonstrativos"],
    "cambio": ["cambio", "taxa de cambio"],
    "regimes": ["regime", "hidden markov", "nao supervisionado"],
    "backtesting": ["backtesting", "vectorbt", "trading", "medias moveis"],
}


def carregar_acervo(path: Path = ACERVO) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("itens", [])


def candidatos_por_conceito(conceito: str, acervo: list[dict] | None = None) -> list[Exercicio]:
    """Devolve os exercícios do acervo que tratam de um conceito, mais recentes primeiro."""
    itens = acervo if acervo is not None else carregar_acervo()
    termos = CONCEITOS.get(conceito.lower(), [sem_acentos(conceito.lower())])
    achados = [
        item for item in itens
        if any(termo in item["busca"] for termo in termos)
    ]
    return [
        Exercicio(
            data=i["data"],
            titulo=i["titulo"],
            linguagem=i["linguagem"],
            caminho_dropbox=i["caminho_dropbox"],
        )
        for i in achados
    ]


def conceitos_disponiveis() -> list[str]:
    """Conceitos que o acervo efetivamente cobre (com ao menos um exercício)."""
    acervo = carregar_acervo()
    return [c for c in CONCEITOS if candidatos_por_conceito(c, acervo)]
