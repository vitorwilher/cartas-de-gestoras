"""
Mapa da indústria brasileira de gestão de recursos.

Cruza três bases públicas da CVM (Dados Abertos):
  - registro_fundo.csv   : cadastro vigente de fundos, com Gestor e PL
  - registro_classe.csv  : as classes de cada fundo, com Classificacao_Anbima
  - cad_adm_cart_pj.csv  : as PJ autorizadas a administrar carteira de valores
                           mobiliários — o universo formal de "gestora"

⚠️ NÃO usar `cad_fi.csv` para retrato do presente. Apesar do nome, aquele arquivo
é o cadastro do regime ANTIGO: 46.575 dos 46.806 registros estão "CANCELADA" e
apenas 22 em funcionamento. Depois da Resolução CVM 175 o cadastro vivo migrou
para `registro_fundo_classe.zip`. Um script apontado para cad_fi.csv devolve
"13 fundos no Brasil" sem emitir erro nenhum.

A chave do cruzamento é sempre o CNPJ (só dígitos), nunca o nome: a mesma casa
aparece grafada de formas diferentes em cada base.

⚠️ Sobre o PL: cada fundo informa o PL na sua própria data de referência. A soma
dá a ORDEM DE GRANDEZA da indústria, não um consolidado oficial — a ANBIMA
publica o dela por outra metodologia e com outra data-base. A data-base aqui é
majoritariamente 2025 (15.399 fundos) e 2024 (9.370).

⚠️ TRÊS LIMPEZAS OBRIGATÓRIAS, todas descobertas rodando (sem elas o resultado é
silenciosamente absurdo):

1. **Três fundos com PL impossível.** SOLE, MARE e SERENA (gestora Genesis
   Capital) declaram R$ 16,68 TRILHÕES cada — valor idêntico, mesma data. Somam
   R$ 50 tri, mais que o PIB do país, e sozinhos faziam a Genesis aparecer como
   78% da indústria, à frente de BB e Itaú. É erro de preenchimento na fonte.
   Cortados por PL > R$ 10 tri.
2. **Fundos com mais de um gestor.** 614 fundos aparecem em 2+ linhas (ex.: o
   BB RF IV, listado sob BB Gestão e sob a PREVI), inflando o total em R$ 0,56
   tri. Deduplicado por CNPJ do fundo, ficando a linha de maior PL.
3. **PL ausente em 25,7% dos fundos.** Não é erro, mas o denominador precisa
   dizer isso: as somas cobrem os 24.788 fundos com PL informado, não os 33.448.

Com as três aplicadas, o PL somado fica em ~R$ 13,3 tri — ordem de grandeza
compatível com a indústria. Sem elas, R$ 63,9 tri.

Saídas (em analises/):
  gestoras_consolidado.csv — uma linha por gestora
  divisao_macro.csv        — distribuição por classificação ANBIMA
  resumo.json              — os números que o relatório cita
"""

import json
import re
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent
ATIVO = "Em Funcionamento Normal"

# Acima disto o PL declarado é erro de preenchimento, não fundo grande: o maior
# fundo legítimo do país tem ~R$ 300 bi. Ver limpeza 1 no cabeçalho.
TETO_PL_PLAUSIVEL = 1e13


def so_digitos(v) -> str:
    return re.sub(r"\D", "", str(v)) if pd.notna(v) else ""


def ler(nome: str) -> pd.DataFrame:
    return pd.read_csv(
        AQUI / nome, sep=";", encoding="latin-1", low_memory=False, dtype=str
    )


def carregar() -> tuple:
    fundos = ler("registro_fundo.csv")
    classes = ler("registro_classe.csv")
    gestoras = ler("cad_adm_cart_pj.csv")

    fundos = fundos[fundos["Situacao"] == ATIVO].copy()
    fundos = fundos[fundos["Tipo_Pessoa_Gestor"] == "PJ"].copy()
    fundos["PL"] = pd.to_numeric(fundos["Patrimonio_Liquido"], errors="coerce")
    fundos["CNPJ_GESTOR"] = fundos["CPF_CNPJ_Gestor"].apply(so_digitos)

    # Limpeza 2: um fundo com vários gestores vira várias linhas. Fica a de
    # maior PL, para não contar o mesmo patrimônio duas vezes.
    n_linhas = len(fundos)
    fundos = fundos.sort_values("PL", ascending=False).drop_duplicates("CNPJ_Fundo")
    dedup_removidas = n_linhas - len(fundos)

    # Limpeza 1: PL impossível (ver cabeçalho).
    absurdos = fundos[fundos["PL"] > TETO_PL_PLAUSIVEL]
    fundos = fundos[~(fundos["PL"] > TETO_PL_PLAUSIVEL)].copy()

    classes = classes[classes["Situacao"] == ATIVO].copy()
    classes["PL"] = pd.to_numeric(classes["Patrimonio_Liquido"], errors="coerce")
    classes = classes[~(classes["PL"] > TETO_PL_PLAUSIVEL)].copy()

    print(f"[limpeza] linhas duplicadas por multi-gestor removidas: {dedup_removidas}")
    print(f"[limpeza] fundos com PL impossível removidos: {len(absurdos)}"
          f" (somavam R$ {absurdos['PL'].sum()/1e12:.1f} tri)")
    if len(absurdos):
        for _, r in absurdos.iterrows():
            print(f"           - {r['Denominacao_Social'][:55]} | {r['Gestor'][:35]}")
    print(f"[limpeza] fundos sem PL informado: {fundos['PL'].isna().sum()}"
          f" de {len(fundos)} ({100*fundos['PL'].isna().mean():.1f}%)")

    gestoras = gestoras[gestoras["SIT"] == "EM FUNCIONAMENTO NORMAL"].copy()
    gestoras["CNPJ_LIMPO"] = gestoras["CNPJ"].apply(so_digitos)
    return fundos, classes, gestoras


def faixa_porte(pl: float) -> str:
    """Cortes de ordem de grandeza, escolhidos aqui — não são da ANBIMA."""
    if pd.isna(pl) or pl <= 0:
        return "F6 · sem PL informado"
    bi = pl / 1e9
    if bi >= 100:
        return "F1 · 100 bi+"
    if bi >= 10:
        return "F2 · 10 a 100 bi"
    if bi >= 1:
        return "F3 · 1 a 10 bi"
    if bi >= 0.1:
        return "F4 · 100 mi a 1 bi"
    return "F5 · abaixo de 100 mi"


def macro_categoria(c: str) -> str:
    """Agrupa a classificação ANBIMA nos grandes blocos da indústria."""
    if not isinstance(c, str) or not c.strip():
        return "Não classificado"
    u = c.upper()
    if u.startswith("PREVID"):
        return "Previdência"
    if u.startswith("MULTIMERCADOS"):
        return "Multimercado"
    if u.startswith("RENDA FIXA"):
        return "Renda Fixa"
    if u.startswith("AÇÕES") or u.startswith("ACOES"):
        return "Ações"
    if u.startswith("CAMBIAL"):
        return "Cambial"
    return "Outros (FII/FIDC/FIP e afins)"


def main() -> None:
    fundos, classes, gestoras_cad = carregar()

    cons = (
        fundos.groupby("CNPJ_GESTOR")
        .agg(
            n_fundos=("CNPJ_Fundo", "nunique"),
            pl_total=("PL", "sum"),
            nome_em_registro=("Gestor", "first"),
        )
        .reset_index()
    )
    cons = cons.merge(
        gestoras_cad[
            ["CNPJ_LIMPO", "DENOM_SOCIAL", "DENOM_COMERC", "MUN", "UF",
             "CONTROLE_ACIONARIO", "DT_REG", "SITE_ADMIN"]
        ],
        left_on="CNPJ_GESTOR", right_on="CNPJ_LIMPO", how="left",
    )
    # ⚠️ DENOM_COMERC vem como o literal "--" quando não há nome fantasia — não
    # como vazio. Sem tratar, 136 gestoras ficam chamadas "--", entre elas o
    # Santander (R$ 573 bi) e a Kinea (R$ 169 bi), sumindo de qualquer ranking
    # por nome.
    # O placeholder aparece com número variável de traços ("--", "-----"), daí a regex.
    comerc = cons["DENOM_COMERC"].replace(r"^\s*-+\s*$", None, regex=True).replace("", None)
    cons["nome"] = comerc.fillna(cons["DENOM_SOCIAL"]).fillna(cons["nome_em_registro"])
    cons["faixa_porte"] = cons["pl_total"].apply(faixa_porte)
    cons = cons.sort_values("pl_total", ascending=False).reset_index(drop=True)

    pl_total = cons["pl_total"].sum()
    cons["share_pct"] = 100 * cons["pl_total"] / pl_total

    conc = {
        f"top{n}_pct": round(100 * cons.head(n)["pl_total"].sum() / pl_total, 2)
        for n in (5, 10, 20, 50, 100, 200)
    }

    # Divisão macro: classificação ANBIMA, no nível da CLASSE (é onde ela existe)
    classes["macro"] = classes["Classificacao_Anbima"].apply(macro_categoria)
    por_macro = (
        classes.groupby("macro")
        .agg(n_classes=("CNPJ_Classe", "nunique"), pl=("PL", "sum"))
        .sort_values("pl", ascending=False)
        .reset_index()
    )
    por_macro["pl_pct"] = 100 * por_macro["pl"] / por_macro["pl"].sum()

    por_anbima = (
        classes.groupby("Classificacao_Anbima")
        .agg(n_classes=("CNPJ_Classe", "nunique"), pl=("PL", "sum"))
        .sort_values("pl", ascending=False)
        .reset_index()
        .head(20)
    )

    por_publico = (
        classes.groupby("Publico_Alvo")
        .agg(n_classes=("CNPJ_Classe", "nunique"), pl=("PL", "sum"))
        .sort_values("pl", ascending=False)
        .reset_index()
    )

    por_porte = (
        cons.groupby("faixa_porte")
        .agg(n_gestoras=("CNPJ_GESTOR", "nunique"), pl=("pl_total", "sum"))
        .reset_index()
        .sort_values("faixa_porte")
    )

    por_uf = (
        cons.groupby("UF")
        .agg(n_gestoras=("CNPJ_GESTOR", "nunique"), pl=("pl_total", "sum"))
        .sort_values("pl", ascending=False)
        .reset_index()
        .head(10)
    )

    por_controle = (
        cons.groupby("CONTROLE_ACIONARIO")
        .agg(n_gestoras=("CNPJ_GESTOR", "nunique"), pl=("pl_total", "sum"))
        .sort_values("pl", ascending=False)
        .reset_index()
    )

    # As 12 do produto. ⚠️ Os nomes de fantasia não batem com a razão social na
    # CVM: a IP é "INVESTIDOR PROFISSIONAL", a Adam é "ADAMCAPITAL" (sem espaço),
    # a Bahia é "BAHIA AM", e Kinea/NEO/Bahia/JGP/Kapitalo têm VÁRIAS PJ
    # distintas (por mandato: renda fixa, equities, private equity...). Buscar
    # por "IP CAPITAL" ou "ADAM CAPITAL" devolve vazio em silêncio.
    alvo = (r"DYNAMO|INVESTIDOR PROFISSIONAL|ALASKA|KAPITALO|ADAMCAPITAL|ADAM CAPITAL"
            r"|LEGACY|BAHIA AM|OCCAM|JGP|KINEA|NEO MULTIMERCADO|NEO EQUITIES"
            r"|NEO GESTAO|SPECIAL SITUATIONS NEO|DAHLIA")
    busca = (cons["nome"].fillna("") + " | " + cons["nome_em_registro"].fillna("")).str.upper()
    nossas = cons[busca.str.contains(alvo, regex=True, na=False)].copy()
    nossas = nossas.sort_values("pl_total", ascending=False)

    # Consolida as várias PJ de uma mesma casa no grupo econômico — é assim que
    # o mercado (e o produto) fala delas.
    def grupo(txt: str) -> str:
        u = txt.upper()
        for chave, rot in [
            ("DYNAMO", "Dynamo"), ("INVESTIDOR PROFISSIONAL", "IP Capital"),
            ("ALASKA", "Alaska"), ("KAPITALO", "Kapitalo"),
            ("ADAMCAPITAL", "Adam"), ("ADAM CAPITAL", "Adam"),
            ("LEGACY", "Legacy"), ("BAHIA AM", "Bahia Asset"),
            ("OCCAM", "Occam"), ("JGP", "JGP"), ("KINEA", "Kinea"),
            ("NEO", "NEO"), ("DAHLIA", "Dahlia"),
        ]:
            if chave in u:
                return rot
        return "?"

    nossas["grupo"] = busca.loc[nossas.index].apply(grupo)
    por_grupo = (
        nossas.groupby("grupo")
        .agg(n_pj=("CNPJ_GESTOR", "nunique"), n_fundos=("n_fundos", "sum"),
             pl=("pl_total", "sum"))
        .sort_values("pl", ascending=False)
        .reset_index()
    )
    por_grupo["pl_bi"] = (por_grupo["pl"] / 1e9).round(2)
    por_grupo["share_industria_pct"] = (100 * por_grupo["pl"] / pl_total).round(4)

    cons.to_csv(AQUI / "gestoras_consolidado.csv", index=False)
    por_macro.to_csv(AQUI / "divisao_macro.csv", index=False)

    resumo = {
        "gerado_em": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "fonte": "CVM Dados Abertos — registro_fundo_classe.zip + cad_adm_cart_pj.csv",
        "universo": {
            "gestoras_pj_autorizadas_ativas": int(len(gestoras_cad)),
            "gestoras_com_fundo_sob_gestao": int(len(cons)),
            "gestoras_autorizadas_sem_fundo": int(len(gestoras_cad) - len(cons)),
            "fundos_em_funcionamento": int(fundos["CNPJ_Fundo"].nunique()),
            "fundos_com_PL_informado": int(fundos["PL"].notna().sum()),
            "pct_fundos_sem_PL": round(100 * fundos["PL"].isna().mean(), 1),
            "classes_em_funcionamento": int(classes["CNPJ_Classe"].nunique()),
            "pl_total_trilhoes": round(pl_total / 1e12, 3),
            "obs_pl": ("soma sobre os fundos COM PL informado, após remover 3 "
                       "fundos de PL impossível e deduplicar multi-gestor"),
        },
        "concentracao_pct_do_PL": conc,
        "mediana_fundos_por_gestora": float(cons["n_fundos"].median()),
        "mediana_pl_por_gestora_milhoes": round(cons["pl_total"].median() / 1e6, 1),
        "por_porte": por_porte.to_dict("records"),
        "divisao_macro": por_macro.to_dict("records"),
        "top_classificacoes_anbima": por_anbima.to_dict("records"),
        "por_publico_alvo": por_publico.to_dict("records"),
        "por_controle_acionario": por_controle.to_dict("records"),
        "por_uf": por_uf.to_dict("records"),
        "as_12_do_produto_por_grupo": por_grupo.to_dict("records"),
        "as_12_do_produto_por_pj": nossas[
            ["grupo", "nome", "n_fundos", "pl_total", "share_pct", "UF"]
        ].to_dict("records"),
        "top30_gestoras": cons.head(30)[
            ["nome", "n_fundos", "pl_total", "share_pct", "UF"]
        ].to_dict("records"),
    }
    (AQUI / "resumo.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2, default=str), encoding="utf8"
    )

    print(f"gestoras PJ autorizadas (ativas): {len(gestoras_cad):>7,}")
    print(f"  dessas, com fundo sob gestão:   {len(cons):>7,}")
    print(f"fundos em funcionamento:          {fundos['CNPJ_Fundo'].nunique():>7,}")
    print(f"classes em funcionamento:         {classes['CNPJ_Classe'].nunique():>7,}")
    print(f"PL somado:                        R$ {pl_total/1e12:>6.2f} tri")
    print(f"\nconcentração do PL: {conc}")
    print(f"mediana de fundos por gestora: {cons['n_fundos'].median():.0f}")
    print(f"mediana de PL por gestora: R$ {cons['pl_total'].median()/1e6:,.1f} mi")
    print("\n-- porte --"); print(por_porte.to_string(index=False))
    print("\n-- divisão macro (ANBIMA) --"); print(por_macro.to_string(index=False))
    print("\n-- público-alvo --"); print(por_publico.to_string(index=False))
    print("\n-- top 15 gestoras --")
    print(cons.head(15)[["nome", "n_fundos", "pl_total", "share_pct"]].to_string(index=False))
    print("\n-- as 12 do produto, por grupo econômico --")
    print(por_grupo[["grupo", "n_pj", "n_fundos", "pl_bi", "share_industria_pct"]]
          .to_string(index=False))
    print(f"\n  as 12 juntas: R$ {por_grupo['pl'].sum()/1e9:,.1f} bi"
          f" = {100*por_grupo['pl'].sum()/pl_total:.2f}% da indústria")


if __name__ == "__main__":
    main()
