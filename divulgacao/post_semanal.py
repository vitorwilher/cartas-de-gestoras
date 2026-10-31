#!/usr/bin/env python3
"""Gera o pacote de divulgação da edição: post do LinkedIn + legenda do Instagram.

Até 13/10/2026 as peças de cada edição eram escritas à mão, numa sessão por semana.
Quando as sessões pararam, os posts pararam — e o tráfego da landing caiu de
~100 visitantes/semana para 5–16 (GA4). Este script tira o humano do caminho: roda
no workflow logo depois da edição e deixa o pacote em `divulgacao/semana/AAAA-MM-DD/`.
Quem publica é a rotina agendada na nuvem, pelo mLabs (ver `divulgacao/semana/README.md`).

O post só pode citar número que esteja na edição ou na saída do exercício
(`digests/resumo/saida-exercicio.txt`). `validar()` confere isso, além de preço,
link, palavra-chave e tamanho, e o pacote NÃO é gravado se a checagem falhar: um
post errado vai ao ar sozinho; um post que não sai é só uma semana sem post.

Uso:
    python divulgacao/post_semanal.py            # gera o pacote da edição mais recente
    python divulgacao/post_semanal.py --dry-run  # mostra, não grava
    python divulgacao/post_semanal.py --forcar   # regera mesmo se o pacote existir
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIGESTS = RAIZ / "digests" / "resumo"
SEMANA = RAIZ / "divulgacao" / "semana"
GRAFICO = DIGESTS / "grafico-exercicio.png"
SAIDA = DIGESTS / "saida-exercicio.txt"

MODEL = os.environ.get("ANTHROPIC_MODEL") or "claude-fable-5-1"
LANDING = "https://analisemacro.com.br/conteudo/cartas-das-gestoras/"
PALAVRA_CHAVE = "GESTORAS"     # o fluxo do ManyChat responde a ela com o link da landing
MAX_LINKEDIN = 2900            # o limite do LinkedIn é 3.000
MAX_INSTAGRAM = 2100           # o do Instagram é 2.200
FRESCOR_DIAS = 2               # mesma guarda do broadcast_semanal.py

SISTEMA = """Você escreve, em nome do Vítor Wilher (Cientista-Chefe da Análise Macro), o
post semanal que divulga a Síntese das Cartas das Gestoras. Recebe a edição da semana
(as teses de cada gestora e o exercício em Python), a saída do terminal do exercício
e o gráfico que ele gerou.

Quem lê é frio: chega pelo feed do LinkedIn ou do Instagram, não conhece o produto e
é do mercado — economista, analista, gestor. Confere número. Uma frase de exagero
custa mais do que dez frases precisas ganham.

ESTRUTURA (os dois textos):
1. Abra com o que UMA gestora escreveu na carta — um fato ou uma afirmação concreta,
   com o nome da casa. Nunca abra com o produto, com pergunta retórica ou com rótulo.
2. O mecanismo: por que a afirmação faria sentido, em duas ou três frases.
3. O teste: o que o exercício mediu, com que dado, e o resultado COM NÚMEROS.
4. O limite: a ressalva que muda a leitura, ou o que o teste não prova.
5. "Nada disso é recomendação." e uma linha sobre o método (a carta afirma o
   mecanismo; a conta que o testa não está nela).
6. A chamada (abaixo) e uma pergunta final para quem é do mercado.

NÚMEROS — regra inviolável: só cite número que apareça literalmente na edição ou na
saída do terminal. O gráfico serve para você ENTENDER o resultado, não como fonte de
número: valores lidos no olho não entram. Arredondar é permitido (11,73 -> 11,7). Se
a saída do terminal não trouxer o número do resultado, descreva a direção sem número.
Use vírgula decimal.

A CHAMADA — o objetivo é o cadastro gratuito, não a venda:
- LinkedIn: termine o corpo com a oferta grátis e o link exato abaixo, numa linha
  própria: "Deixei uma edição completa de amostra, grátis, e o resumo de cada edição
  nova por e-mail neste link:" seguido do LINK.
- Instagram: "Comenta GESTORAS que eu te mando, no direct, uma edição completa de
  amostra, grátis." (é o fluxo do ManyChat que responde à palavra).
- Pode dizer que a edição completa desta semana é para assinantes. NUNCA cite preço,
  valor, desconto ou "R$".

TOM: primeira pessoa do Vítor ("testei", "medi"). Português direto, frase curta,
verbo forte. Sem superlativo vazio (revolucionário, incrível, definitivo), sem
jargão de marketing, sem emoji, sem hashtag, sem negrito em markdown.

TAMANHO: LinkedIn entre 1.600 e 2.700 caracteres. Instagram entre 1.000 e 1.900,
parágrafos de no máximo três linhas.

Responda SÓ com os dois blocos, nesta forma:
<linkedin>
...texto...
</linkedin>
<instagram>
...texto...
</instagram>"""

# Referência de tom: o post de 13/10 escrito à mão (sem a chamada antiga, que
# levava à assinatura). Mostra o padrão "carta -> mecanismo -> conta -> limite".
REFERENCIA = """A Legacy escreveu na carta de setembro que câmbio, juros e bolsa carregam o mesmo
prêmio de risco: o da condução da política econômica. Por isso a casa não escolhe
entre eles e mantém o "kit Brasil" equilibrado — comprada em real, aplicada em juros,
comprada em bolsa.

Se o prêmio é um só, as três posições são uma aposta só. Isso dá para medir.

Coloquei as três pernas na mesma escala de risco e medi, em janelas de 63 dias úteis
desde 2019, quanto o kit diversifica de fato. Em 2 de outubro, o índice estava em
1,36. Em 9 de outubro, foi a 1,12, a menor leitura desde 2019.

O detalhe que importa: um único pregão fez isso. Tirando o dia 5 de outubro da
janela, o índice volta a 1,37. A diversificação do kit existe nos dias comuns e some
no dia que decide o resultado.

Nada disso é recomendação. O ponto é o método: a carta afirma o mecanismo, e a conta
que o testa não está nela."""


# ---------------------------------------------------------------- entrada

def edicao_mais_recente() -> Path:
    qmds = sorted(DIGESTS.glob("resumo-*.qmd"), reverse=True)
    if not qmds:
        raise SystemExit("Nenhuma edição em digests/resumo/")
    return qmds[0]


def data_da_edicao(qmd: Path) -> dt.date:
    return dt.date.fromisoformat(qmd.stem.removeprefix("resumo-"))


def texto_da_edicao(qmd: Path) -> str:
    """A edição sem o código (longo e sem número de resultado) e sem os links finais."""
    md = qmd.read_text(encoding="utf-8")
    md = re.sub(r"```python\n.*?```", "[código do exercício omitido]", md, flags=re.DOTALL)
    return md.split("## Cartas originais")[0]


def gestoras_da_edicao(md: str) -> list[str]:
    ignorar = ("Nesta edição", "Exercício", "Convergências", "Cartas originais", "O olhar de fora")
    return [t for t in re.findall(r"(?m)^## (.+)$", md) if not t.startswith(ignorar)]


def link_linkedin(data: dt.date) -> str:
    return (f"{LANDING}?utm_source=linkedin&utm_medium=organic"
            f"&utm_campaign=cartas-de-gestoras&utm_content=post-{data.isoformat()}")


# ---------------------------------------------------------------- checagem

_NUM = re.compile(r"[−-]?\d+(?:[.,]\d+)*\s?%?")
_EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF]")


def _valor(token: str) -> tuple[float, int] | None:
    """'1,36' -> (1.36, 2); '7,7%' -> (7.7, 1); '3.000' -> (3000.0, 0)."""
    t = token.replace("−", "-").replace("%", "").replace(" ", "").lstrip("-")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):        # milhar com ponto
        return float(t.replace(".", "")), 0
    t = t.replace(",", ".")
    if t.count(".") > 1:
        return None
    casas = len(t.split(".")[1]) if "." in t else 0
    try:
        return float(t), casas
    except ValueError:
        return None


def _valores(texto: str) -> list[float]:
    """Valores das FONTES. "11.734" é ambíguo — decimal na saída do Python, milhar no
    texto em português — e vale nas duas leituras."""
    vs = []
    for m in _NUM.finditer(texto):
        v = _valor(m.group())
        if v is not None:
            vs.append(v[0])
        t = m.group().replace("%", "").replace(" ", "").replace("−", "").lstrip("-")
        if re.fullmatch(r"\d{1,3}\.\d{3}", t):
            vs.append(float(t))
    return vs


def numeros_sem_fonte(post: str, fontes: str) -> list[str]:
    """Números do post que não aparecem nas fontes, nem arredondados.

    Isentos: inteiros abaixo de 100 sem % (contagens: "15 gestoras", "3 posições",
    dias do mês) e anos de 1990 a 2040. O resto precisa de lastro.
    """
    sem_url = re.sub(r"https?://\S+", "", post)
    fonte_vs = _valores(fontes)
    faltando = []
    for m in _NUM.finditer(sem_url):
        tok = m.group().strip()
        v = _valor(tok)
        if v is None:
            continue
        valor, casas = v
        if "%" not in tok and casas == 0 and (valor < 100 or 1990 <= valor <= 2040):
            continue
        ok = any(round(s, casas) == round(valor, casas) or round(s * 100, casas) == round(valor, casas)
                 for s in fonte_vs)
        if not ok:
            faltando.append(tok)
    return faltando


def validar(canal: str, texto: str, fontes: str, link: str) -> list[str]:
    problemas = []
    limite = MAX_LINKEDIN if canal == "linkedin" else MAX_INSTAGRAM
    if len(texto) > limite:
        problemas.append(f"{len(texto)} caracteres (máximo {limite})")
    if len(texto) < 800:
        problemas.append(f"curto demais ({len(texto)} caracteres)")
    if re.search(r"R\$|\b97\b|reais por mês|desconto", texto, re.IGNORECASE):
        problemas.append("cita preço — a chamada é a amostra grátis")
    if _EMOJI.search(texto):
        problemas.append("tem emoji")
    if re.search(r"\{\{|\[[^\]]*\]|XX|TODO|<[a-z]+>", texto):
        problemas.append("tem placeholder, colchete ou tag")
    if "**" in texto or re.search(r"(?m)^#", texto):
        problemas.append("tem markdown ou hashtag")
    if canal == "linkedin" and link not in texto:
        problemas.append("falta o link da landing com UTM")
    if canal == "instagram" and PALAVRA_CHAVE not in texto:
        problemas.append(f"falta a palavra-chave {PALAVRA_CHAVE}")
    if canal == "instagram" and "http" in texto:
        problemas.append("link no Instagram não é clicável — use a palavra-chave")
    soltos = numeros_sem_fonte(texto, fontes)
    if soltos:
        problemas.append(f"números sem fonte na edição/saída: {', '.join(soltos[:8])}")
    return problemas


# ---------------------------------------------------------------- geração

def escrever(edicao: str, saida: str, grafico: Path | None, link: str,
             correcao: str = "") -> tuple[str, str]:
    from anthropic import Anthropic

    conteudo: list[dict] = []
    if grafico is not None:
        conteudo.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/png",
            "data": base64.b64encode(grafico.read_bytes()).decode()}})
    pedido = (
        f"LINK (use exatamente este, no LinkedIn):\n{link}\n\n"
        f"REFERÊNCIA DE TOM (um post anterior, sem a chamada):\n{REFERENCIA}\n\n"
        f"SAÍDA DO TERMINAL DO EXERCÍCIO:\n{saida or '(não disponível — não cite número de resultado)'}\n\n"
        f"EDIÇÃO DA SEMANA:\n{edicao}"
    )
    if correcao:
        pedido += f"\n\nA VERSÃO ANTERIOR FOI RECUSADA PELA CHECAGEM. Corrija:\n{correcao}"
    conteudo.append({"type": "text", "text": pedido})

    # effort "high", não "max": com `max` o Fable 5.1 gasta o orçamento pensando e
    # trunca (ver cartas.py). stop_reason é conferido sempre.
    with Anthropic().messages.stream(
        model=MODEL, max_tokens=16_000,
        thinking={"type": "adaptive"}, output_config={"effort": "high"},
        system=SISTEMA, messages=[{"role": "user", "content": conteudo}],
    ) as stream:
        final = stream.get_final_message()
    if final.stop_reason == "max_tokens":
        raise RuntimeError("post cortado por max_tokens")
    resposta = "\n".join(b.text for b in final.content if b.type == "text")
    blocos = {c: re.search(rf"<{c}>\s*(.*?)\s*</{c}>", resposta, re.DOTALL) for c in ("linkedin", "instagram")}
    if not all(blocos.values()):
        raise RuntimeError("resposta sem os blocos <linkedin> e <instagram>")
    return blocos["linkedin"].group(1).strip(), blocos["instagram"].group(1).strip()


def proxima_quarta_meio_dia(data: dt.date) -> str:
    """Quarta é o dia da trilha C no calendário de iscas; meio-dia de Brasília."""
    dias = (2 - data.weekday()) % 7 or 7
    return f"{(data + dt.timedelta(days=dias)).isoformat()}T12:00:00-03:00"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--forcar", action="store_true", help="regera mesmo se o pacote existir")
    args = ap.parse_args()

    qmd = edicao_mais_recente()
    data = data_da_edicao(qmd)
    idade = (dt.date.today() - data).days
    if idade > FRESCOR_DIAS and not args.forcar:
        # Terça sem carta nova: a edição mais recente é a da semana passada, e o
        # post dela já saiu. Silêncio é resultado normal, não falha.
        print(f"[nada a fazer] A edição mais recente é de {data} ({idade} dias).")
        return 0

    destino = SEMANA / data.isoformat()
    if (destino / "pacote.json").exists() and not args.forcar:
        print(f"[nada a fazer] O pacote de {data} já existe em {destino.relative_to(RAIZ)}.")
        return 0

    edicao = texto_da_edicao(qmd)
    md_completo = qmd.read_text(encoding="utf-8")
    # O gráfico e a saída são sobrescritos a cada edição; só valem se ESTA edição
    # referencia o gráfico (sem a referência, o exercício falhou e o PNG é velho).
    tem_grafico = GRAFICO.exists() and "](grafico-exercicio.png)" in md_completo
    grafico = GRAFICO if tem_grafico else None
    saida = SAIDA.read_text(encoding="utf-8")[-6000:] if (tem_grafico and SAIDA.exists()) else ""
    fontes = edicao + "\n" + saida
    link = link_linkedin(data)

    correcao = ""
    for tentativa in (1, 2):
        linkedin, instagram = escrever(edicao, saida, grafico, link, correcao)
        problemas = {c: validar(c, t, fontes, link) for c, t in (("linkedin", linkedin), ("instagram", instagram))}
        if not any(problemas.values()):
            break
        correcao = "\n".join(f"- {c}: {p}" for c, ps in problemas.items() for p in ps)
        print(f"[tentativa {tentativa}] recusado pela checagem:\n{correcao}", file=sys.stderr)
    else:
        print("🔴 Pacote NÃO gerado: o post não passou na checagem duas vezes.", file=sys.stderr)
        return 1

    pacote = {
        "edicao": data.isoformat(),
        "gestoras": gestoras_da_edicao(md_completo),
        "status": "pendente",                 # a rotina do mLabs troca para "agendado"
        "agendar_para": proxima_quarta_meio_dia(data),
        "imagem": "imagem.png" if grafico else None,
        "link_linkedin": link,
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "modelo": MODEL,
    }
    print(f"--- LinkedIn ({len(linkedin)} caracteres)\n{linkedin}\n")
    print(f"--- Instagram ({len(instagram)} caracteres)\n{instagram}\n")
    print(json.dumps(pacote, ensure_ascii=False, indent=2))
    if args.dry_run:
        print("\n[dry-run] Nada foi gravado.", file=sys.stderr)
        return 0

    destino.mkdir(parents=True, exist_ok=True)
    (destino / "post-linkedin.txt").write_text(linkedin + "\n", encoding="utf-8")
    (destino / "legenda-instagram.txt").write_text(instagram + "\n", encoding="utf-8")
    if grafico:
        shutil.copy2(grafico, destino / "imagem.png")
    (destino / "pacote.json").write_text(json.dumps(pacote, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nPacote gravado em {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
