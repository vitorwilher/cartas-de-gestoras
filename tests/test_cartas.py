from datetime import date
from pathlib import Path
import tempfile
import unittest

import yaml

from cartas import (
    Carta, data_do_texto, marcadores, salvar_catalogo, selecionar_novas,
    serie_do_titulo, resumo_para_whatsapp,
)


def carta(identificador: str, mes: int, serie: str = "principal") -> Carta:
    return Carta(date(2026, mes, 1), identificador, "Gestora", serie, identificador, f"https://x/{identificador}.pdf")


class TestEstadoEDatas(unittest.TestCase):
    def test_data_do_texto_prioriza_rotulo(self):
        self.assertEqual(data_do_texto("Carta do Gestor — Julho 2026"), date(2026, 7, 1))
        self.assertEqual(data_do_texto("Relatório março de 2025"), date(2025, 3, 1))

    def test_primeira_execucao_pega_apenas_mais_recente_por_serie(self):
        itens = [carta("jul", 7), carta("jun", 6), carta("cred-jul", 7, "credito")]
        novas = selecionar_novas(itens, {"ultima_carta": ""})
        self.assertEqual({x.identificador for x in novas}, {"jul", "cred-jul"})

    def test_delta_para_no_marcador(self):
        itens = [carta("ago", 8), carta("jul", 7), carta("jun", 6)]
        novas = selecionar_novas(itens, {"ultimas_cartas": {"principal": "jul"}})
        self.assertEqual([x.identificador for x in novas], ["ago"])

    def test_series_paralelas(self):
        self.assertEqual(serie_do_titulo("Occam Brasil", "Carta Mensal Crédito"), "credito")
        self.assertEqual(serie_do_titulo("Occam Brasil", "Carta Mensal"), "principal")

    def test_ultima_carta_aceita_mapa_por_serie(self):
        self.assertEqual(
            marcadores({"ultima_carta": {"principal": "a", "credito": "b"}}),
            {"principal": "a", "credito": "b"},
        )

    def test_salvar_catalogo_preserva_comentarios(self):
        texto = "# comentário importante\ngestoras:\n  - nome: A\n    ultima_carta: \"\"\n"
        catalogo = {"gestoras": [{"nome": "A", "ultima_carta": {"principal": "id:1"}}]}
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "gestoras.yml"
            caminho.write_text(texto, encoding="utf-8")
            salvar_catalogo(catalogo, caminho)
            salvo = caminho.read_text(encoding="utf-8")
            self.assertIn("# comentário importante", salvo)
            self.assertEqual(
                yaml.safe_load(salvo)["gestoras"][0]["ultima_carta"],
                {"principal": "id:1"},
            )

    def test_resumo_whatsapp_e_removido_do_documento(self):
        documento, chamada = resumo_para_whatsapp(
            "## Gestora\nTexto\n<!-- resumo_whatsapp: Juros e petróleo dominaram a edição. -->"
        )
        self.assertNotIn("resumo_whatsapp", documento)
        self.assertEqual(chamada, "Juros e petróleo dominaram a edição.")


if __name__ == "__main__":
    unittest.main()
