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


class TestSalvarCatalogoMultilinha(unittest.TestCase):
    """Regressão do bug que corrompeu gestoras.yml em 2026-09-08.

    Um `ultima_carta` com duas séries de URL longa era serializado em DUAS linhas
    pelo safe_dump. O padrão antigo casava só a primeira, e a cauda da execução
    anterior sobrava órfã — quebrando o YAML na execução seguinte.
    """

    CATALOGO_MULTILINHA = """gestoras:

  - nome: Occam Brasil
    estrategia: html
    ultima_carta: {credito: 'https://x.com/uploads/2026/08/Carta_Credito_Julho_2026.pdf',
      principal: 'https://x.com/uploads/2026/08/Carta_Julho_2026.pdf'}
    notas: >
      Publica duas séries paralelas.

  - nome: Alaska
    estrategia: url_previsivel
    ultima_carta: {principal: 'https://y.com/julho26.pdf'}
    notas: >
      URL previsível.
"""

    def _salvar(self, catalogo_texto, estados):
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False, encoding="utf-8") as f:
            f.write(catalogo_texto)
            caminho = Path(f.name)
        catalogo = yaml.safe_load(catalogo_texto)
        for gestora, estado in zip(catalogo["gestoras"], estados):
            gestora["ultima_carta"] = estado
        salvar_catalogo(catalogo, caminho)
        return caminho

    def test_valor_multilinha_nao_deixa_orfa(self):
        novos = [
            {"credito": "https://x.com/uploads/2026/09/Carta_Credito_Agosto_2026.pdf",
             "principal": "https://x.com/uploads/2026/09/Carta_Agosto_2026.pdf"},
            {"principal": "https://y.com/agosto26.pdf"},
        ]
        caminho = self._salvar(self.CATALOGO_MULTILINHA, novos)
        texto = caminho.read_text(encoding="utf-8")

        # O arquivo tem de voltar a carregar — era exatamente isto que quebrava.
        recarregado = yaml.safe_load(texto)
        self.assertEqual(len(recarregado["gestoras"]), 2)
        self.assertEqual(recarregado["gestoras"][0]["ultima_carta"], novos[0])
        self.assertEqual(recarregado["gestoras"][1]["ultima_carta"], novos[1])

        # Nenhum resíduo do valor antigo pode sobreviver.
        self.assertNotIn("Julho_2026", texto)
        self.assertNotIn("julho26", texto)
        # E os comentários/notas seguem preservados.
        self.assertIn("Publica duas séries paralelas.", texto)
        self.assertIn("URL previsível.", texto)

    def test_estado_longo_fica_em_uma_linha(self):
        """O dump precisa caber em uma linha, para não recriar o problema."""
        novos = [
            {"credito": "https://x.com/" + "a" * 120 + ".pdf",
             "principal": "https://x.com/" + "b" * 120 + ".pdf"},
            {"principal": "https://y.com/agosto26.pdf"},
        ]
        caminho = self._salvar(self.CATALOGO_MULTILINHA, novos)
        texto = caminho.read_text(encoding="utf-8")
        yaml.safe_load(texto)  # não pode lançar
        linhas_estado = [l for l in texto.splitlines() if "ultima_carta:" in l]
        self.assertEqual(len(linhas_estado), 2)
        for linha in linhas_estado:
            self.assertTrue(linha.rstrip().endswith("}"), f"quebrou em várias linhas: {linha}")
