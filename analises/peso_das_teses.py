"""
Peso patrimonial das teses — o cruzamento que a síntese não fazia.

O que resolve: a síntese diz que N casas defendem a tese X. Isso trata Dynamo
(R$ 20 bi) e Dahlia (R$ 4,6 bi) como se pesassem igual. Aqui cada casa entra com
o patrimônio que de fato está exposto àquele tipo de aposta.

⚠️ A ARMADILHA CENTRAL, e por que este arquivo não usa o PL total da gestora:

O PL que a CVM informa por gestora soma TODOS os fundos dela — macro, crédito,
previdência, ações. Atribuir esse total à tese da carta macro é errado, e o erro
não é pequeno. Medido em 11/09/2026:

    Kinea    R$ 177,3 bi totais →  apenas  6% em multimercado (o resto é
                                   crédito e previdência imobiliária)
    Dynamo   R$  20,0 bi totais →  apenas  3% em multimercado (96% é ações)
    Alaska   R$   8,8 bi totais →           0% em multimercado
    Kapitalo R$  42,4 bi totais →          81% em multimercado
    Bahia    R$   6,4 bi totais →          83% em multimercado

Uma conta sobre "quem aposta em queda de juro" somando PL TOTAL faria a Kinea
dominar o resultado com R$ 177 bi que estão em crédito imobiliário, não em juro.

A saída: a CVM classifica por FUNDO (Classificacao_Anbima no registro_classe).
Então cada tese recebe só o PL dos fundos da classe correspondente. A carta macro
da Legacy fala pelos R$ 16,9 bi de multimercado dela, não pelos R$ 25,2 bi totais.

⚠️ Isto continua sendo uma APROXIMAÇÃO, e a síntese deve dizer isso:
  - Um fundo "Multimercados Macro" está exposto a juro, câmbio E bolsa. Não dá
    para saber pela CVM quanto está em cada um — só a carta diz, em texto.
  - A classe diz o MANDATO, não a POSIÇÃO. Um macro pode estar zerado em juro.
  - O PL é da última data informada por fundo, majoritariamente 2025.
  Por isso a saída fala em "patrimônio sob mandato compatível com a tese",
  nunca em "patrimônio apostando em X".

Uso:
    python3 peso_das_teses.py
    # e, no pipeline, importar peso_por_casa() e passar ao prompt da síntese
"""

import json
import re
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent
TETO_PL_PLAUSIVEL = 1e13

# Cada tese econômica só pode ser sustentada por fundos com mandato compatível.
# O casamento é por prefixo da Classificacao_Anbima.
MANDATO_POR_EIXO = {
    "juro_e_macro": ("MULTIMERCADOS MACRO", "MULTIMERCADOS LIVRE",
                     "MULTIMERCADOS ESTRAT", "MULTIMERCADOS JUROS",
                     "RENDA FIXA DURAÇÃO LIVRE SOBERANO",
                     "RENDA FIXA DURAÇÃO ALTA SOBERANO"),
    "credito": ("RENDA FIXA DURAÇÃO LIVRE CRÉDITO", "RENDA FIXA DURAÇÃO BAIXA",
                "RENDA FIXA DURAÇÃO MÉDIA", "RENDA FIXA DURAÇÃO ALTA GRAU",
                "RENDA FIXA DURAÇÃO LIVRE GRAU"),
    "bolsa_brasil": ("AÇÕES LIVRE", "AÇÕES VALOR", "AÇÕES DIVIDENDOS",
                     "AÇÕES SMALL CAPS", "AÇÕES ÍNDICE ATIVO", "AÇÕES SETORIAIS"),
    "exterior": ("MULTIMERCADOS INVEST. NO EXTERIOR", "AÇÕES INVEST. NO EXTERIOR",
                 "RENDA FIXA INVEST. NO EXTERIOR"),
    "cambio": ("CAMBIAL",),
}

# As casas cobertas pela síntese. A chave é o termo que aparece em `Gestor`.
CASAS = {
    "DYNAMO": "Dynamo", "INVESTIDOR PROFISSIONAL": "IP Capital",
    "ALASKA": "Alaska", "KAPITALO": "Kapitalo", "ADAMCAPITAL": "Adam",
    "LEGACY": "Legacy", "BAHIA AM": "Bahia Asset", "OCCAM": "Occam",
    "JGP": "JGP", "KINEA": "Kinea", "NEO ": "NEO", "DAHLIA": "Dahlia",
}


def eixo_do_mandato(classif) -> str:
    if not isinstance(classif, str) or not classif.strip():
        return "nao_classificado"
    u = classif.upper()
    for eixo, prefixos in MANDATO_POR_EIXO.items():
        if any(u.startswith(p) for p in prefixos):
            return eixo
    if u.startswith("PREVID"):
        return "previdencia"
    return "outros"


def carregar() -> pd.DataFrame:
    """Devolve um fundo por linha, já com o eixo de mandato e o PL."""
    f = pd.read_csv(AQUI / "registro_fundo.csv", sep=";", encoding="latin-1",
                    low_memory=False, dtype=str)
    cl = pd.read_csv(AQUI / "registro_classe.csv", sep=";", encoding="latin-1",
                     low_memory=False, dtype=str)

    f = f[(f["Situacao"] == "Em Funcionamento Normal")
          & (f["Tipo_Pessoa_Gestor"] == "PJ")].copy()
    f["PL"] = pd.to_numeric(f["Patrimonio_Liquido"], errors="coerce")
    f = f.sort_values("PL", ascending=False).drop_duplicates("CNPJ_Fundo")
    f = f[~(f["PL"] > TETO_PL_PLAUSIVEL)].copy()

    cl = cl[cl["Situacao"] == "Em Funcionamento Normal"].copy()
    cl = cl.drop_duplicates("ID_Registro_Fundo")

    m = f.merge(cl[["ID_Registro_Fundo", "Classificacao_Anbima"]],
                on="ID_Registro_Fundo", how="left")
    m["eixo"] = m["Classificacao_Anbima"].apply(eixo_do_mandato)
    return m


def peso_por_casa(casas: dict = None) -> pd.DataFrame:
    """PL de cada casa QUEBRADO POR EIXO de mandato. É a tabela que o prompt usa."""
    casas = casas or CASAS
    m = carregar()
    linhas = []
    for termo, rotulo in casas.items():
        sub = m[m["Gestor"].fillna("").str.upper().str.contains(
            termo, na=False, regex=False)]
        if not len(sub):
            continue
        total = sub["PL"].sum()
        por_eixo = sub.groupby("eixo")["PL"].sum()
        linha = {"casa": rotulo, "pl_total_bi": round(total / 1e9, 2),
                 "n_fundos": int(sub["CNPJ_Fundo"].nunique())}
        for eixo in list(MANDATO_POR_EIXO) + ["previdencia", "outros",
                                              "nao_classificado"]:
            linha[f"{eixo}_bi"] = round(por_eixo.get(eixo, 0) / 1e9, 2)
        linhas.append(linha)
    return pd.DataFrame(linhas).sort_values("pl_total_bi", ascending=False)


def contexto_para_prompt(df: pd.DataFrame) -> str:
    """Bloco de texto que entra no prompt da síntese, com as ressalvas junto."""
    partes = [
        "PESO PATRIMONIAL DAS CASAS, POR TIPO DE MANDATO (CVM, data-base 2025).",
        "Use para dimensionar convergências: 'N casas, somando R$ X bi sob mandato",
        "compatível, defendem...'. REGRAS:",
        "  - Cite o PL do EIXO da tese, nunca o PL total da casa.",
        "  - Mandato NÃO é posição: diz o que o fundo PODE fazer, não o que fez.",
        "    Escreva 'sob mandato compatível', nunca 'apostando'.",
        "  - Se a tese não casar com nenhum eixo, não invente número.",
        "",
        f"{'casa':<13}{'total':>8}{'juro/macro':>12}{'crédito':>9}{'bolsa':>8}{'exterior':>10}",
    ]
    for _, r in df.iterrows():
        partes.append(
            f"{r['casa']:<13}{r['pl_total_bi']:>8.1f}{r['juro_e_macro_bi']:>12.1f}"
            f"{r['credito_bi']:>9.1f}{r['bolsa_brasil_bi']:>8.1f}{r['exterior_bi']:>10.1f}"
        )
    partes.append("(valores em R$ bilhões)")
    return "\n".join(partes)


def main() -> None:
    df = peso_por_casa()
    df.to_csv(AQUI / "peso_das_teses.csv", index=False)
    (AQUI / "peso_das_teses_prompt.txt").write_text(
        contexto_para_prompt(df), encoding="utf8")

    print(contexto_para_prompt(df))
    print("\n\n--- por que isso importa: total vs. eixo ---")
    for _, r in df.iterrows():
        if r["pl_total_bi"] <= 0:
            continue
        pct = 100 * r["juro_e_macro_bi"] / r["pl_total_bi"]
        print(f"  {r['casa']:<13} total R$ {r['pl_total_bi']:>7.1f} bi → "
              f"juro/macro R$ {r['juro_e_macro_bi']:>6.1f} bi ({pct:>3.0f}%)")


if __name__ == "__main__":
    main()
