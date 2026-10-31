"""Regressões do broadcast semanal.

As duas guardas testadas aqui nasceram de falhas reais em 2026-09-09, e as duas
mandariam e-mail indevido para a base — o tipo de erro que não dá para desfazer.
"""

import datetime
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent


def carregar():
    """Importa o script pelo caminho: ele não é um pacote."""
    spec = importlib.util.spec_from_file_location(
        "broadcast_semanal", RAIZ / "divulgacao" / "broadcast_semanal.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestGuardaDeFrescor(unittest.TestCase):
    """`cartas.py` sai com 0 quando nenhuma gestora publicou, e o acervo de
    .qmd é versionado — então o broadcast SEMPRE acha uma edição para enviar.
    Sem guarda, uma terça quieta reenvia a edição anterior aos mesmos leads."""

    def test_edicao_velha_nao_e_reenviada(self):
        m = carregar()
        edicao = datetime.date(2026, 9, 9)

        class HojeUmaSemanaDepois(datetime.date):
            @classmethod
            def today(cls):
                return edicao + datetime.timedelta(days=7)

        with mock.patch.object(m, "date", HojeUmaSemanaDepois), \
             mock.patch.object(m, "edicao_mais_recente",
                               return_value=("2026-09-09", ["Dynamo"], "curva")), \
             mock.patch.object(sys, "argv", ["broadcast_semanal.py", "--enviar"]), \
             mock.patch.object(m, "cabecalhos", return_value={}), \
             mock.patch.object(m, "alcance", return_value=10), \
             mock.patch.object(m, "httpx") as http:
            self.assertEqual(m.main(), 0, "deve terminar em silêncio, não em erro")
            http.post.assert_not_called()

    def test_edicao_de_hoje_segue_o_fluxo(self):
        """A guarda não pode barrar o caso normal — a edição recém-gerada."""
        m = carregar()
        hoje = datetime.date(2026, 9, 9)

        class Hoje(datetime.date):
            @classmethod
            def today(cls):
                return hoje

        with mock.patch.object(m, "date", Hoje), \
             mock.patch.object(m, "edicao_mais_recente",
                               return_value=("2026-09-09", ["Dynamo"], "curva")), \
             mock.patch.object(sys, "argv", ["broadcast_semanal.py", "--enviar"]), \
             mock.patch.object(m, "cabecalhos", return_value={}), \
             mock.patch.object(m, "alcance", return_value=10), \
             mock.patch.object(m, "ja_existe", return_value=None), \
             mock.patch.object(m, "httpx") as http:
            http.post.return_value.status_code = 201
            http.post.return_value.json.return_value = {"broadcast": {"id": 1}}
            m.main()
            http.post.assert_called_once()


class TestGuardaDeDuplicata(unittest.TestCase):
    """Rodar duas vezes na mesma semana agendava DOIS e-mails idênticos."""

    def test_nao_cria_se_ja_existe_com_o_mesmo_assunto(self):
        m = carregar()
        hoje = datetime.date(2026, 9, 9)

        class Hoje(datetime.date):
            @classmethod
            def today(cls):
                return hoje

        with mock.patch.object(m, "date", Hoje), \
             mock.patch.object(m, "edicao_mais_recente",
                               return_value=("2026-09-09", ["Dynamo"], "curva")), \
             mock.patch.object(sys, "argv", ["broadcast_semanal.py", "--enviar"]), \
             mock.patch.object(m, "cabecalhos", return_value={}), \
             mock.patch.object(m, "alcance", return_value=10), \
             mock.patch.object(m, "ja_existe", return_value=25844122), \
             mock.patch.object(m, "httpx") as http:
            self.assertEqual(m.main(), 0)
            http.post.assert_not_called()

    def test_ja_existe_ignora_broadcast_enviado(self):
        """Um `completed` da semana passada não pode bloquear a edição de hoje."""
        m = carregar()
        with mock.patch.object(m, "httpx") as http:
            http.get.return_value.status_code = 200
            http.get.return_value.json.return_value = {"broadcasts": [
                {"id": 1, "subject": "Cartas das gestoras — edição de 2 de setembro",
                 "status": "completed"},
            ]}
            self.assertIsNone(m.ja_existe({}, "Cartas das gestoras — edição de 9 de setembro"))


if __name__ == "__main__":
    unittest.main()


class TestGestorasDoEmail(unittest.TestCase):
    """A lista do e-mail sai dos títulos de nível 2 da edição."""

    def test_secoes_do_bloco_internacional(self):
        bs = carregar()
        edicao = (
            "## Nesta edição\n\ntexto\n\n## Genoa Capital\n\n"
            "## Convergências e divergências\n\n"
            "## Oaktree Capital — internacional\n\n## GMO — internacional\n\n"
            "## O olhar de fora\n\n## Exercício da semana: curva\n\n## Cartas originais\n"
        )
        with mock.patch.object(bs, "DIGESTS") as pasta:
            arquivo = mock.Mock()
            arquivo.name = "resumo-2026-09-29.qmd"
            arquivo.read_text.return_value = edicao
            pasta.glob.return_value = [arquivo]
            data, gestoras, conceito = bs.edicao_mais_recente()
        self.assertEqual(gestoras, ["Genoa Capital", "Oaktree Capital", "GMO"])
        self.assertEqual(conceito, "curva")



class TestDoisPublicos(unittest.TestCase):
    """Até 31/10/2026 o assinante recebia o e-mail de venda do que já tinha comprado."""

    def setUp(self):
        self.bs = carregar()

    def test_assinante_nao_recebe_preco_e_recebe_o_curso(self):
        html = self.bs.corpo_assinantes("2026-10-20", ["Dynamo"], "um conceito")
        self.assertNotIn("R$", html)
        self.assertNotIn("add-to-cart", html)
        self.assertIn(self.bs.CURSO, html)

    def test_lead_recebe_amostra_e_convite_sem_o_bloco_congelado(self):
        html = self.bs.corpo("2026-10-20", ["Dynamo"], "um conceito")
        self.assertIn(self.bs.AMOSTRA, html)
        self.assertIn("add-to-cart=73335", html)
        self.assertNotIn("Uma mudança, a partir desta edição", html)

    def test_cada_publico_tem_sua_tag(self):
        self.assertNotEqual(self.bs.TAG_PROJETO, self.bs.TAG_ASSINANTES)


class TestTeseDoEmail(unittest.TestCase):
    """O e-mail lista a tese de cada casa; o rótulo muda de formato entre edições."""

    def setUp(self):
        self.bs = carregar()

    def test_rotulo_em_negrito_na_mesma_linha(self):
        secao = "**Série:** macro.\n\n**A tese em uma frase.** O prêmio é um só.\n\n**O mecanismo.** ..."
        self.assertEqual(self.bs._tese(secao), "O prêmio é um só.")

    def test_rotulo_como_subtitulo_com_a_tese_abaixo(self):
        secao = "### 1. A tese em uma frase\n\nCada erro é evidência forte.\n\n### 2. O mecanismo\n\n..."
        self.assertEqual(self.bs._tese(secao), "Cada erro é evidência forte.")

    def test_secao_sem_tese_devolve_vazio(self):
        self.assertEqual(self.bs._tese("Só descrição do mês.\n\n### Riscos\n\n..."), "")

    def test_email_nao_copia_paragrafos_de_bastidor(self):
        # O "Nesta edição" de 20/10 trazia "O corpus não informa..." e "a seguir".
        html = self.bs.corpo_assinantes("2026-10-20", ["Dynamo"], "um conceito")
        self.assertNotIn("corpus", html)
        self.assertNotIn("a seguir", html)
