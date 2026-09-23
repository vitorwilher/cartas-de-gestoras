"""Coleta das gestoras internacionais (piloto de 2026-09-23), sem rede.

Cada teste reproduz uma armadilha verificada nos sites reais — ver as `notas`
de Oaktree, GMO e Bridgewater em gestoras/gestoras.yml.
"""
from datetime import date
from types import SimpleNamespace
import unittest

from bs4 import BeautifulSoup

from cartas import Carta, Coletor, data_em_ingles, montar_corpus


class ColetorFalso(Coletor):
    """Serve HTML fixo por URL no lugar da rede."""

    def __init__(self, paginas: dict[str, str]):
        super().__init__(pausa=0)
        self.paginas = paginas

    def get(self, url, **kwargs):
        return SimpleNamespace(text=self.paginas[url])


OAKTREE = {
    "nome": "Oaktree Capital", "site": "https://www.oaktreecapital.com",
    "listagem": "https://oak/memos", "estrategia": "html_posts",
    "padrao_link": "/insights/memo/", "regiao": "internacional", "formato": "pdf",
}


class TestDataEmIngles(unittest.TestCase):
    def test_abreviado_e_por_extenso(self):
        self.assertEqual(data_em_ingles("Sep 22, 2026 Shall We Repeal"), date(2026, 9, 22))
        self.assertEqual(data_em_ingles("Title | August 4, 2026 | Greg Jensen"), date(2026, 8, 4))

    def test_sem_data_devolve_none_e_nao_hoje(self):
        # Datar com hoje faria o item vencer sempre e travar o delta (caso Genoa).
        self.assertIsNone(data_em_ingles("The Complete Collection"))


class TestHtmlPosts(unittest.TestCase):
    def test_oaktree_descarta_item_sem_data(self):
        html = """
        <div><a href="/docs/default-source/memos/the-complete-collection.pdf">The Complete Collection</a></div>
        <div>Sep 22, 2026 <a href="/insights/memo/shall-we">Shall We Repeal</a></div>
        <div>Apr 9, 2026 <a href="/insights/memo/private-credit">Private Credit</a></div>
        <div><a href="/insights/memo/sem-data">Sem data</a></div>
        """
        cartas = ColetorFalso({"https://oak/memos": html}).descobrir(OAKTREE)
        self.assertEqual([c.titulo for c in cartas], ["Shall We Repeal", "Private Credit"])
        self.assertEqual(cartas[0].url, "https://www.oaktreecapital.com/insights/memo/shall-we")
        self.assertEqual(cartas[0].regiao, "internacional")

    def test_bridgewater_fica_so_com_artigo(self):
        cfg = {**OAKTREE, "nome": "Bridgewater", "site": "https://www.bridgewater.com",
               "listagem": "https://bw/ri", "padrao_link": r"bridgewater\.com/",
               "seletor": 'ps-promo[data-content-type="article"]', "formato": "html"}
        html = """
        <ps-promo data-content-type="video"><a href="https://www.bridgewater.com/research-and-insights/v">Vídeo</a> July 28, 2026</ps-promo>
        <ps-promo data-content-type="article"><a href="https://www.bridgewater.com/raiz"></a>
          <a href="https://www.bridgewater.com/raiz">Artigo na raiz</a> August 27, 2026</ps-promo>
        """
        cartas = ColetorFalso({"https://bw/ri": html}).descobrir(cfg)
        self.assertEqual([(c.titulo, c.data_referencia) for c in cartas],
                         [("Artigo na raiz", date(2026, 8, 27))])


class TestPdfDaPagina(unittest.TestCase):
    CFG = {"nome": "GMO", "site": "https://www.gmo.com", "listagem": "https://gmo/lib",
           "estrategia": "pdf_da_pagina", "padrao_link": "_gmoquarterlyletter/",
           "padrao_pdf": r"quarterly-letter/.*\.pdf", "formato": "pdf"}

    def test_trimestre_vem_do_nome_do_pdf(self):
        paginas = {
            "https://gmo/lib": '<a href="/americas/research-library/part-1-x_gmoquarterlyletter/">Letter</a>',
            "https://www.gmo.com/americas/research-library/part-1-x_gmoquarterlyletter/":
                '<meta property="og:title" content="What Barbarians Like">'
                '<a href="https://outro.com/relatorio.pdf">citação</a>'
                '<a href="/globalassets/articles/quarterly-letter/2026/gmo-quarterly-letter_2q-2026.pdf">PDF</a>',
        }
        [carta] = ColetorFalso(paginas).descobrir(self.CFG)
        self.assertEqual(carta.data_referencia, date(2026, 6, 1))
        self.assertTrue(carta.url.endswith("gmo-quarterly-letter_2q-2026.pdf"))
        self.assertIn("2Q 2026", carta.titulo)

    def test_sem_trimestre_nao_inventa_data(self):
        paginas = {
            "https://gmo/lib": '<a href="/x_gmoquarterlyletter/">Letter</a>',
            "https://www.gmo.com/x_gmoquarterlyletter/":
                '<a href="/globalassets/articles/quarterly-letter/carta.pdf">PDF</a>',
        }
        self.assertEqual(ColetorFalso(paginas).descobrir(self.CFG), [])


class TestPdfEmJavascript(unittest.TestCase):
    def test_oaktree_openpdf(self):
        soup = BeautifulSoup(
            """<a href="javascript:openPDF('Shall We','https://www.oaktreecapital.com/docs/memo.pdf?sfvrsn=1')">PDF</a>
               <a href="/docs/default-source/memos/2008-antigo.pdf">memo citado</a>""",
            "html.parser",
        )
        self.assertEqual(Coletor._pdf_no_soup(soup),
                         "https://www.oaktreecapital.com/docs/memo.pdf?sfvrsn=1")


class TestCorpus(unittest.TestCase):
    def test_regiao_chega_ao_modelo(self):
        c = Carta(date(2026, 9, 22), "id", "Oaktree Capital", "principal", "t", "u",
                  regiao="internacional")
        self.assertIn("Região: internacional", montar_corpus([c]))
        self.assertIn("Região: brasil", montar_corpus([Carta(date(2026, 8, 1), "i", "G", "principal", "t", "u")]))


if __name__ == "__main__":
    unittest.main()
