"""Testes da seleção do exercício da semana.

Cobrem só a lógica determinística (índice e casamento por conceito). A geração
em si chama a API e não é testada aqui.
"""

import json
import tempfile
import unittest
from pathlib import Path

from exercicios.selecao import (
    CONCEITOS, Exercicio, candidatos_por_conceito, carregar_acervo,
    conceitos_disponiveis, sem_acentos,
)

ACERVO_FALSO = {
    "itens": [
        {"data": "2024-01-09", "titulo": "analisando a volatilidade do ibovespa usando garch",
         "linguagem": "Python", "caminho_dropbox": "/x/garch",
         "busca": "analisando a volatilidade do ibovespa usando garch"},
        {"data": "2022-05-17", "titulo": "estrutura a termo da taxa de juros em python",
         "linguagem": "Python", "caminho_dropbox": "/x/ettj",
         "busca": "estrutura a termo da taxa de juros em python"},
        {"data": "2023-09-26", "titulo": "selecao de carteira e teoria de markowitz",
         "linguagem": "Python", "caminho_dropbox": "/x/markowitz",
         "busca": "selecao de carteira e teoria de markowitz"},
    ]
}


class TestSelecaoExercicio(unittest.TestCase):
    def test_sem_acentos(self):
        self.assertEqual(sem_acentos("cointegração"), "cointegracao")
        self.assertEqual(sem_acentos("câmbio"), "cambio")

    def test_casa_conceito_com_acervo(self):
        achados = candidatos_por_conceito("volatilidade", ACERVO_FALSO["itens"])
        self.assertEqual(len(achados), 1)
        self.assertIn("garch", achados[0].caminho_dropbox)

    def test_conceito_sem_correspondencia_devolve_vazio(self):
        self.assertEqual(candidatos_por_conceito("pairs trading", ACERVO_FALSO["itens"]), [])

    def test_curva_de_juros_casa_por_sinonimo(self):
        """'curva de juros' precisa achar 'estrutura a termo' — os termos diferem."""
        achados = candidatos_por_conceito("curva de juros", ACERVO_FALSO["itens"])
        self.assertEqual(len(achados), 1)
        self.assertIn("ettj", achados[0].caminho_dropbox)

    def test_acervo_ausente_nao_quebra(self):
        with tempfile.TemporaryDirectory() as tmp:
            inexistente = Path(tmp) / "nao-existe.json"
            self.assertEqual(carregar_acervo(inexistente), [])

    def test_acervo_real_cobre_conceitos(self):
        """O índice versionado precisa cobrir os conceitos que as cartas tratam."""
        disponiveis = conceitos_disponiveis()
        self.assertIn("volatilidade", disponiveis)
        self.assertIn("curva de juros", disponiveis)
        self.assertIn("portfolio", disponiveis)

    def test_todo_conceito_tem_termos(self):
        for conceito, termos in CONCEITOS.items():
            self.assertTrue(termos, f"conceito sem termos de busca: {conceito}")


if __name__ == "__main__":
    unittest.main()
