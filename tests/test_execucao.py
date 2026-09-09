"""Testes da execução do código do exercício (o gráfico que entra no PDF)."""

import sys
import tempfile
import unittest
from pathlib import Path

from exercicios.execucao import (
    NOME_GRAFICO, extrair_codigo, gerar_grafico, remover_referencia,
)

MD_COM_GRAFICO = """### O código

```python
import matplotlib
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])
plt.savefig("grafico-exercicio.png", dpi=80)
```

![A curva mostra o mecanismo](grafico-exercicio.png)

### Como ler
"""

MD_SEM_CODIGO = "### O conceito\n\nTexto sem bloco de código.\n"


class TestExecucaoExercicio(unittest.TestCase):
    def test_extrai_bloco_python(self):
        codigo = extrair_codigo(MD_COM_GRAFICO)
        self.assertIn("savefig", codigo)
        self.assertNotIn("```", codigo)

    def test_sem_bloco_devolve_none(self):
        self.assertIsNone(extrair_codigo(MD_SEM_CODIGO))

    def test_remove_referencia_da_imagem(self):
        """Some a linha ![...](png), mas o savefig DENTRO do código permanece."""
        limpo = remover_referencia(MD_COM_GRAFICO)
        self.assertNotIn(f"]({NOME_GRAFICO})", limpo)   # a referência markdown saiu
        self.assertNotIn("A curva mostra o mecanismo", limpo)
        self.assertIn("### Como ler", limpo)            # o resto sobrevive
        self.assertIn(f'savefig("{NOME_GRAFICO}"', limpo)  # o código fica intacto

    def test_gera_o_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / NOME_GRAFICO
            saida = gerar_grafico(MD_COM_GRAFICO, destino, python=sys.executable)
            self.assertIsNotNone(saida, "o código válido deveria gerar o PNG")
            self.assertTrue(destino.exists())
            self.assertGreater(destino.stat().st_size, 0)

    def test_codigo_quebrado_nao_levanta(self):
        """Falha do exercício não pode derrubar a edição."""
        md = "```python\nraise ValueError('boom')\n```\n"
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / NOME_GRAFICO
            self.assertIsNone(gerar_grafico(md, destino, python=sys.executable))
            self.assertFalse(destino.exists())

    def test_codigo_sem_figura_devolve_none(self):
        md = "```python\nprint('sem gráfico')\n```\n"
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / NOME_GRAFICO
            self.assertIsNone(gerar_grafico(md, destino, python=sys.executable))


if __name__ == "__main__":
    unittest.main()
