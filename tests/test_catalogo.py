"""Testes do gerador do catálogo que alimenta o MCP."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp"))

from gerar_catalogo import (  # noqa: E402
    corpo_do_qmd, extrair_fontes, extrair_gestoras, resumo_executivo,
    separar_exercicio,
)

QMD = """---
lang: pt-BR
---

```{=latex}
\\begin{titlepage}
\\end{titlepage}
\\clearpage
```

## Bahia Asset Management

Tese da Bahia.

## Kinea Investimentos — Série principal

Tese da Kinea.

## Convergências e divergências

Ambas veem juros longos pressionados.

## Exercício da semana: Inclinação da curva DI

Conteúdo do exercício.

---

## Cartas originais

- **Bahia Asset Management — Carta Julho** ([original](https://x/bahia.pdf))
- **Kinea Investimentos — A hora do pesadelo** ([original](https://x/kinea))
"""


class TestCatalogo(unittest.TestCase):
    def setUp(self):
        self.corpo = corpo_do_qmd(QMD)
        self.sintese, self.exercicio, self.conceito = separar_exercicio(self.corpo)

    def test_corpo_descarta_preambulo_latex(self):
        self.assertNotIn("titlepage", self.corpo)
        self.assertTrue(self.corpo.startswith("## Bahia"))

    def test_separa_exercicio_e_conceito(self):
        self.assertEqual(self.conceito, "Inclinação da curva DI")
        self.assertIn("Conteúdo do exercício", self.exercicio)
        self.assertNotIn("Conteúdo do exercício", self.sintese)

    def test_gestoras_excluem_secoes_nao_gestora(self):
        gestoras = extrair_gestoras(self.sintese)
        self.assertEqual(gestoras, ["Bahia Asset Management", "Kinea Investimentos"])

    def test_fontes_com_link(self):
        fontes = extrair_fontes(self.corpo)
        self.assertEqual(len(fontes), 2)
        self.assertEqual(fontes[0]["gestora"], "Bahia Asset Management")
        self.assertEqual(fontes[0]["url"], "https://x/bahia.pdf")

    def test_resumo_usa_comentario_quando_existe(self):
        com_comentario = QMD + "\n<!-- resumo_whatsapp: Edição com duas gestoras. -->"
        self.assertEqual(
            resumo_executivo(com_comentario, self.sintese),
            "Edição com duas gestoras.",
        )

    def test_resumo_fallback_sai_sem_markdown_nem_fontes(self):
        """O .qmd não guarda o comentário — o fallback precisa entregar texto puro."""
        texto = resumo_executivo(QMD, self.sintese)
        self.assertIn("juros longos", texto)
        self.assertNotIn("**", texto)
        self.assertNotIn("original", texto)
        self.assertNotIn("##", texto)

    def test_resumo_respeita_limite(self):
        longo = "## Convergências e divergências\n\n" + ("palavra " * 400)
        self.assertLessEqual(len(resumo_executivo("", longo)), 450)


if __name__ == "__main__":
    unittest.main()
