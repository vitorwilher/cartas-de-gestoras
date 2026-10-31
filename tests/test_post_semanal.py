"""As checagens do post semanal: é o que impede um post errado de ir ao ar sozinho."""

import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "divulgacao"))

from post_semanal import (  # noqa: E402
    PALAVRA_CHAVE, link_linkedin, numeros_sem_fonte, proxima_quarta_meio_dia, validar,
)

FONTES = """O índice de diversificação foi a 1,12 em 9 de outubro (era 1,36).
Vol do kit: 11.734 % a.a. Correlação 0.68. 3.000 sorteios. Ibovespa +7,7%."""
LINK = link_linkedin(dt.date(2026, 10, 13))


def _post_ok(canal: str) -> str:
    corpo = ("A Legacy escreveu na carta que o prêmio é um só. " * 16 +
             "O índice foi de 1,36 a 1,12, com 3.000 sorteios e vol de 11,7%. "
             "Nada disso é recomendação.\n")
    if canal == "linkedin":
        return corpo + "Deixei uma edição completa de amostra, grátis:\n" + LINK
    return corpo + f"Comenta {PALAVRA_CHAVE} que eu te mando a amostra no direct."


class TestNumeros(unittest.TestCase):
    def test_numero_da_fonte_passa(self):
        self.assertEqual(numeros_sem_fonte("caiu para 1,12", FONTES), [])

    def test_arredondamento_passa(self):
        # 11.734 na saída do terminal vira 11,7 no post
        self.assertEqual(numeros_sem_fonte("vol de 11,7% ao ano", FONTES), [])

    def test_fracao_vira_percentual(self):
        self.assertEqual(numeros_sem_fonte("correlação de 68%", FONTES), [])

    def test_numero_inventado_e_pego(self):
        self.assertEqual(numeros_sem_fonte("o índice foi a 1,47", FONTES), ["1,47"])
        self.assertEqual(numeros_sem_fonte("subiu 25%", FONTES), ["25%"])

    def test_contagens_e_anos_sao_isentos(self):
        self.assertEqual(numeros_sem_fonte("15 gestoras desde 2019, em 3 posições", FONTES), [])

    def test_milhar_com_ponto(self):
        self.assertEqual(numeros_sem_fonte("3.000 sorteios", FONTES), [])

    def test_numero_da_url_e_ignorado(self):
        self.assertEqual(numeros_sem_fonte(LINK, FONTES), [])


class TestValidar(unittest.TestCase):
    def test_posts_bons_passam(self):
        self.assertEqual(validar("linkedin", _post_ok("linkedin"), FONTES, LINK), [])
        self.assertEqual(validar("instagram", _post_ok("instagram"), FONTES, LINK), [])

    def test_preco_reprova(self):
        p = _post_ok("linkedin") + "\nA assinatura custa R$ 97 por mês."
        self.assertTrue(any("preço" in x for x in validar("linkedin", p, FONTES, LINK)))

    def test_linkedin_sem_link_reprova(self):
        p = _post_ok("linkedin").replace(LINK, "")
        self.assertTrue(any("link" in x for x in validar("linkedin", p, FONTES, LINK)))

    def test_instagram_sem_palavra_chave_reprova(self):
        p = _post_ok("instagram").replace(PALAVRA_CHAVE, "o nome")
        self.assertTrue(any(PALAVRA_CHAVE in x for x in validar("instagram", p, FONTES, LINK)))

    def test_emoji_e_hashtag_reprovam(self):
        p = _post_ok("instagram") + "\n#investimentos 🚀"
        problemas = validar("instagram", p, FONTES, LINK)
        self.assertTrue(any("emoji" in x for x in problemas))
        self.assertTrue(any("hashtag" in x for x in problemas))

    def test_longo_demais_reprova(self):
        p = _post_ok("instagram") + "x" * 3000
        self.assertTrue(any("máximo" in x for x in validar("instagram", p, FONTES, LINK)))


class TestAgenda(unittest.TestCase):
    def test_terca_agenda_para_quarta(self):
        self.assertEqual(proxima_quarta_meio_dia(dt.date(2026, 11, 3)), "2026-11-04T12:00:00-03:00")

    def test_quarta_vai_para_a_seguinte(self):
        # edição extra numa quarta: não agenda para o mesmo dia, que pode já ter passado
        self.assertEqual(proxima_quarta_meio_dia(dt.date(2026, 11, 4)), "2026-11-11T12:00:00-03:00")


if __name__ == "__main__":
    unittest.main()
