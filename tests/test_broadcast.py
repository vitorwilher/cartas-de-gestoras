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
