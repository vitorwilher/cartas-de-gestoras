"""
Cruza as conexões do LinkedIn do Vitor com as gestoras registradas na CVM.

Responde: em quais gestoras ele já tem contato, quem é a pessoa, se é decisora,
e quais casas relevantes não têm contato nenhum.

FONTES
  ../../ROI_Diagnostico/data/Basic_LinkedInDataExport_08-22-2026.zip/Connections.csv
      ⚠️ apesar do nome, é uma PASTA já descompactada, não um .zip. `unzip` falha.
      Exportado em 22/08/2026. Traz nome, empresa, cargo — e-mail quase sempre
      vazio (o LinkedIn só o inclui se a pessoa liberou).
  analises/gestoras_consolidado.csv  : as 1.260 gestoras com fundo (via CVM)
  analises/cad_adm_cart_resp.csv     : diretores e responsáveis por CNPJ
  analises/cad_adm_cart_socios.csv   : sócios por CNPJ

⚠️ O CASAMENTO É POR NOME, e nome é chave ruim. No LinkedIn as pessoas escrevem
"Verde Asset"; na CVM está "VERDE ASSET MANAGEMENT S.A.". A normalização abaixo
remove sufixos societários, acentos e pontuação, e exige que o núcleo do nome
da gestora apareça na empresa declarada. Isso gera DOIS tipos de erro:

  - Falso positivo: "NEO" casaria com "Neoenergia", "Neon". Por isso núcleos com
    menos de 5 caracteres só casam com o nome inteiro, nunca por conteúdo.
  - Falso negativo: quem escreveu a empresa de um jeito não previsto fica de fora.

Por isso a saída traz a coluna `confianca` e o script imprime os casos para
revisão humana. NÃO usar a lista sem olhar.

⚠️ LGPD: a saída contém nome, empresa e cargo de pessoas reais. É base de
prospecção, não lista de e-mails — o LinkedIn não fornece e-mail, e deduzir
`nome@gestora.com.br` a partir do domínio é justamente o que NÃO se deve fazer.
Abordar pelo LinkedIn ou pelo contato institucional da casa.

Uso:
    python3 cruzar_linkedin.py
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent
LINKEDIN = (AQUI / ".." / ".." / "ROI_Diagnostico" / "data"
            / "Basic_LinkedInDataExport_08-22-2026.zip" / "Connections.csv")

# Sufixos societários e termos genéricos que não ajudam a identificar a casa.
RUIDO = {
    "ltda", "sa", "s a", "me", "epp", "eireli", "holding", "participacoes",
    "gestora", "gestao", "gestor", "de", "do", "da", "dos", "das", "e",
    "recursos", "investimentos", "investimento", "asset", "management",
    "capital", "administradora", "administracao", "valores", "mobiliarios",
    "distribuidora", "titulos", "financeira", "consultoria", "patrimonial",
    "brasil", "ltd", "inc", "group", "partners", "servicos", "fundos",
}

# Cargos que indicam poder de decisão sobre compra de formação/dados.
CARGOS_DECISORES = (
    "socio", "sócio", "partner", "founder", "fundador", "ceo", "diretor",
    "director", "head", "gestor", "portfolio manager", "cio", "coo", "cfo",
    "superintendente", "chief", "presidente", "managing",
)

# ⚠️ O casamento por palavra-chave marcava "Coordenador Gestão de TI" e "Agente
# de negócios" como decisores — "gestor"/"negócio" aparecem em cargo operacional.
# Estes termos DESQUALIFICAM, mesmo que o cargo contenha uma palavra da lista
# acima: são funções de apoio, não quem decide compra de formação ou dado.
CARGOS_NAO_DECISORES = (
    " ti", "tecnologia da informacao", "infraestrutura", "suporte",
    "estagi", "intern", "trainee", "junior", "assistente", "auxiliar",
    "agente de negocio", "atendimento", "recursos humanos", "rh ",
    "marketing", "comunicacao", "juridico", "facilities", "recrutamento",
)

# Casas que aparecem sob mais de uma razão social na CVM mas são a MESMA porta
# comercial. Sem isso as mesmas 73 pessoas do Itaú eram contadas duas vezes,
# em "ITAU UNIBANCO" e "ITAU UNIBANCO ASSET MANAGEMENT LTDA.".
GRUPO_ECONOMICO = {
    "itau": "Itaú", "bradesco": "Bradesco", "santander": "Santander",
    "bb ": "Banco do Brasil", "banco do brasil": "Banco do Brasil",
    "caixa": "Caixa", "btg": "BTG Pactual", "safra": "Safra",
    "xp ": "XP", "sicredi": "Sicredi", "ubs": "UBS", "bnp": "BNP Paribas",
}


def grupo_de(nome: str) -> str:
    """Consolida razões sociais do mesmo conglomerado num rótulo só."""
    n = normalizar(nome) + " "
    for chave, rotulo in GRUPO_ECONOMICO.items():
        if n.startswith(chave) or f" {chave}" in n:
            return rotulo
    return nome


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, sem pontuação, espaços colapsados."""
    if not isinstance(texto, str):
        return ""
    t = "".join(c for c in unicodedata.normalize("NFKD", texto)
                if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def nucleo(nome: str) -> str:
    """Tira sufixos societários e termos genéricos, deixando o nome da casa.

    'VERDE ASSET MANAGEMENT S.A.' -> 'verde'
    'KAPITALO INVESTIMENTOS LTDA' -> 'kapitalo'
    """
    palavras = [p for p in normalizar(nome).split() if p not in RUIDO]
    return " ".join(palavras).strip()


def carregar_conexoes() -> pd.DataFrame:
    # As 3 primeiras linhas são um aviso do LinkedIn, não cabeçalho.
    df = pd.read_csv(LINKEDIN, skiprows=3, dtype=str).fillna("")
    df["empresa_norm"] = df["Company"].apply(normalizar)

    def eh_decisor(cargo: str) -> bool:
        c = normalizar(cargo) + " "
        if any(bloq in c for bloq in CARGOS_NAO_DECISORES):
            return False
        return any(termo in c for termo in CARGOS_DECISORES)

    df["decisor"] = df["Position"].apply(eh_decisor)
    return df


def carregar_gestoras() -> pd.DataFrame:
    g = pd.read_csv(AQUI / "gestoras_consolidado.csv", dtype=str)
    g["pl_total"] = pd.to_numeric(g["pl_total"], errors="coerce").fillna(0)
    g["n_fundos"] = pd.to_numeric(g["n_fundos"], errors="coerce").fillna(0)
    g["nucleo"] = g["nome"].apply(nucleo)
    g = g[g["nucleo"].str.len() >= 3]
    return g.sort_values("pl_total", ascending=False)


def cruzar(conexoes: pd.DataFrame, gestoras: pd.DataFrame) -> pd.DataFrame:
    achados = []
    for _, g in gestoras.iterrows():
        nuc = g["nucleo"]
        if len(nuc) >= 5:
            # Núcleo longo: pode casar por conteúdo, com limite de palavra.
            padrao = re.compile(rf"\b{re.escape(nuc)}\b")
            bate = conexoes["empresa_norm"].apply(lambda e: bool(padrao.search(e)))
            confianca = "alta"
        else:
            # Núcleo curto ("neo", "jgp", "ip"): só igualdade exata, senão
            # "NEO" casaria com "Neoenergia" e a lista viraria lixo.
            bate = conexoes["empresa_norm"] == nuc
            confianca = "exata"
        for _, c in conexoes[bate].iterrows():
            achados.append({
                "gestora": g["nome"], "pl_bi": round(g["pl_total"] / 1e9, 2),
                "n_fundos": int(g["n_fundos"]), "uf": g.get("UF", ""),
                "pessoa": f"{c['First Name']} {c['Last Name']}".strip(),
                "cargo": c["Position"], "empresa_declarada": c["Company"],
                "decisor": c["decisor"], "url": c["URL"],
                "conectado_em": c["Connected On"], "confianca": confianca,
            })
    return pd.DataFrame(achados)


def main() -> None:
    conexoes = carregar_conexoes()
    gestoras = carregar_gestoras()
    print(f"conexões no LinkedIn: {len(conexoes):,}")
    print(f"gestoras com fundo (CVM): {len(gestoras):,}\n")

    df = cruzar(conexoes, gestoras)
    if df.empty:
        print("Nenhum casamento — verifique a normalização.")
        return

    # Consolida conglomerados e remove a mesma pessoa contada em duas razões
    # sociais do mesmo grupo.
    df["grupo"] = df["gestora"].apply(grupo_de)
    df = df.drop_duplicates(subset=["grupo", "pessoa"])
    df = df.sort_values(["pl_bi", "decisor"], ascending=[False, False])
    df.to_csv(AQUI / "linkedin_x_gestoras.csv", index=False)

    casas = df["grupo"].nunique()
    decisores = df[df["decisor"]]
    print(f"CONTATOS EM GESTORAS: {len(df)} pessoas, em {casas} casas")
    print(f"  dos quais decisores (sócio/diretor/head/gestor): {len(decisores)}")
    print(f"  PL somado das casas alcançadas: R$ "
          f"{df.drop_duplicates('grupo')['pl_bi'].sum():,.1f} bi\n")

    print("-- TOP 25 CASAS ONDE VOCÊ JÁ TEM CONTATO (por PL) --")
    topo = (df.groupby("grupo")
              .agg(pl_bi=("pl_bi", "max"), contatos=("pessoa", "nunique"),
                   decisores=("decisor", "sum"))
              .sort_values("pl_bi", ascending=False).head(25))
    print(topo.to_string())

    print("\n-- DECISORES NAS 15 MAIORES CASAS ALCANÇADAS --")
    for casa in topo.head(15).index:
        dec = decisores[decisores["grupo"] == casa]
        if dec.empty:
            continue
        print(f"\n  {casa}")
        for _, r in dec.head(4).iterrows():
            print(f"    · {r['pessoa']:<28} — {r['cargo'][:52]}")

    # A lacuna: casas grandes sem nenhum contato. Compara por GRUPO, senão
    # "ITAU UNIBANCO" apareceria como sem contato mesmo havendo 73 pessoas na
    # razão social irmã "ITAU UNIBANCO ASSET MANAGEMENT".
    grupos_alcancados = set(df["grupo"])
    lacuna = gestoras[~gestoras["nome"].apply(grupo_de).isin(grupos_alcancados)].head(20)
    print("\n-- 20 MAIORES GESTORAS SEM NENHUM CONTATO SEU --")
    for _, g in lacuna.iterrows():
        print(f"    R$ {g['pl_total']/1e9:>8,.1f} bi  {g['nome'][:58]}")

    print(f"\n[saída] linkedin_x_gestoras.csv — {len(df)} linhas."
          f"\n⚠️ Casamento por NOME: revisar antes de usar. Ver `confianca`.")


if __name__ == "__main__":
    main()
