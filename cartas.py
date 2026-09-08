#!/usr/bin/env python3
"""Coleta e sintetiza cartas novas das gestoras brasileiras.

Uso seguro para inspeção (não altera estado):
    python cartas.py --discover-only

Pipeline completo:
    python cartas.py                 # gera o .qmd
    python cartas.py --pdf           # gera .qmd e PDF
    python cartas.py --pdf --send    # gera, renderiza e envia por WhatsApp

O estado só é persistido depois que a síntese foi escrita com sucesso. Uma
falha de uma gestora é isolada e não interrompe as demais.
"""

from __future__ import annotations

import argparse
import calendar
import html
import io
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, urljoin, urlparse
from xml.etree import ElementTree

import httpx
import pdfplumber
import yaml
from anthropic import Anthropic
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from exercicios.geracao import exercicio_da_semana

load_dotenv()

ROOT = Path(__file__).resolve().parent
CATALOGO = ROOT / "gestoras" / "gestoras.yml"
OUTPUT_DIR = ROOT / "digests" / "resumo"
TEMP_DIR = ROOT / "cartas"
MODEL = os.environ.get("ANTHROPIC_MODEL") or "claude-opus-5"
META_API_VERSION = "v20.0"
WABA_PRODUCAO = "1421867178829333"
MAX_TEXT_CHARS = 45_000
USER_AGENT = (
    "CartasGestoras/1.0 (+https://github.com/vitorwilher; "
    "contato: pesquisa Analise Macro)"
)

MESES = {
    "jan": 1, "janeiro": 1, "feb": 2, "fev": 2, "fevereiro": 2,
    "mar": 3, "marco": 3, "março": 3, "apr": 4, "abr": 4, "abril": 4,
    "may": 5, "mai": 5, "maio": 5, "jun": 6, "junho": 6,
    "jul": 7, "julho": 7, "aug": 8, "ago": 8, "agosto": 8,
    "sep": 9, "set": 9, "setembro": 9, "oct": 10, "out": 10,
    "outubro": 10, "nov": 11, "novembro": 11, "dec": 12, "dez": 12,
    "dezembro": 12,
}
MESES_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def sem_acentos(valor: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", valor) if not unicodedata.combining(c)
    ).lower()


def texto_limpo(valor: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(valor or "")).strip()


def data_do_texto(valor: str, fallback: date | None = None) -> date:
    """Extrai mês/ano do rótulo; usa a data editorial apenas como fallback."""
    limpo = sem_acentos(texto_limpo(valor))
    ano = re.search(r"\b(20\d{2})\b", limpo)
    for nome, numero in sorted(MESES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(sem_acentos(nome))}\b", limpo):
            return date(int(ano.group(1)) if ano else (fallback or date.today()).year, numero, 1)
    if ano:
        return date(int(ano.group(1)), (fallback or date.today()).month, 1)
    return fallback or date.today()


def _mes_anterior(valor: date) -> date:
    total = valor.year * 12 + valor.month - 2
    ano, mes0 = divmod(total, 12)
    return date(ano, mes0 + 1, 1)


def serie_do_titulo(nome: str, titulo: str) -> str:
    t = sem_acentos(titulo)
    if "occam" in sem_acentos(nome):
        return "credito" if "credito" in t else "principal"
    if "legacy" in sem_acentos(nome):
        return "credito" if "credito" in t else "macro"
    return "principal"


@dataclass(order=True)
class Carta:
    data_referencia: date
    identificador: str = field(compare=False)
    gestora: str = field(compare=False)
    serie: str = field(compare=False)
    titulo: str = field(compare=False)
    url: str = field(compare=False)
    formato: str = field(compare=False, default="pdf")
    texto: str = field(compare=False, default="")

    def resumo_json(self) -> dict[str, str]:
        return {
            "gestora": self.gestora,
            "serie": self.serie,
            "data": self.data_referencia.isoformat(),
            "titulo": self.titulo,
            "url": self.url,
            "identificador": self.identificador,
        }


class Coletor:
    def __init__(self, pausa: float = 0.5):
        self.pausa = pausa
        self.client = httpx.Client(
            headers={"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"},
            timeout=60,
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        try:
            resposta = self.client.get(url, **kwargs)
        except httpx.ConnectError as exc:
            # O servidor da JGP ocasionalmente entrega a cadeia intermediária TLS
            # incompleta. O fallback fica estritamente limitado ao host oficial.
            if urlparse(url).hostname != "www.jgp.com.br" or "CERTIFICATE_VERIFY_FAILED" not in str(exc):
                raise
            print("  [aviso] JGP: cadeia TLS incompleta; repetindo no host oficial sem validação", file=sys.stderr)
            with httpx.Client(headers=self.client.headers, timeout=60, follow_redirects=True, verify=False) as inseguro:
                resposta = inseguro.get(url, **kwargs)
        resposta.raise_for_status()
        time.sleep(self.pausa)
        return resposta

    def descobrir(self, cfg: dict[str, Any]) -> list[Carta]:
        estrategia = cfg["estrategia"]
        metodo = getattr(self, f"descobrir_{estrategia}")
        cartas = metodo(cfg)
        unicas = {c.identificador: c for c in cartas if c.url}
        return sorted(unicas.values(), reverse=True)

    def descobrir_wp_rest(self, cfg: dict[str, Any]) -> list[Carta]:
        itens = self.get(cfg["listagem"]).json()
        nome = cfg["nome"]
        resultado: list[Carta] = []
        for item in itens:
            titulo = texto_limpo(BeautifulSoup(
                item.get("title", {}).get("rendered", ""), "html.parser"
            ).get_text(" "))
            slug = item.get("slug", "")
            fonte = item.get("source_url") or item.get("guid", {}).get("rendered", "")
            link = item.get("link", "")
            publicado = date.fromisoformat(item.get("date", date.today().isoformat())[:10])

            if nome == "JGP" and "carta macro" not in sem_acentos(titulo):
                continue
            if nome == "IP Capital Partners" and "ip_rg" not in sem_acentos(titulo + fonte):
                continue

            corpo = item.get("content", {}).get("rendered", "")
            if nome == "Bahia Asset Management":
                tax = " ".join(item.get("class_list", [])) + " " + slug + " " + titulo
                referencia = data_do_texto(tax, _mes_anterior(publicado))
                mmm = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][referencia.month]
                fonte = urljoin(cfg["site"], f"/wp-content/uploads/{publicado:%Y/%m}/carta_do_gestor_{mmm}{str(referencia.year)[2:]}.pdf")
            elif cfg["formato"] == "html":
                fonte = link
            elif nome == "JGP":
                # Resolver o PDF apenas se esta carta for delta. Buscar cada post
                # aqui transformaria uma listagem REST em dezenas de requests.
                fonte = link
            elif not fonte.lower().split("?", 1)[0].endswith(".pdf"):
                fonte = self._pdf_em_pagina(link or fonte) or fonte

            fallback = _mes_anterior(publicado) if nome == "Bahia Asset Management" else publicado
            referencia = data_do_texto(titulo + " " + slug, fallback)
            resultado.append(Carta(
                referencia, slug or fonte, nome, serie_do_titulo(nome, titulo),
                titulo or f"Carta de {referencia:%m/%Y}", fonte, cfg["formato"],
                self._html_para_texto(corpo) if cfg["formato"] == "html" else "",
            ))
        return resultado

    def descobrir_rss(self, cfg: dict[str, Any]) -> list[Carta]:
        raiz = ElementTree.fromstring(self.get(cfg["listagem"]).content)
        resultado: list[Carta] = []
        for item in raiz.findall(".//item"):
            titulo = texto_limpo(item.findtext("title", ""))
            link = texto_limpo(item.findtext("link", ""))
            publicado_txt = item.findtext("pubDate", "")
            try:
                publicado = datetime.strptime(publicado_txt[:25], "%a, %d %b %Y %H:%M:%S").date()
            except ValueError:
                publicado = date.today()
            t = sem_acentos(titulo)
            nome = cfg["nome"]
            if nome == "Dynamo" and not re.match(r"^carta\s+(dynamo\s+)?\d+\b", t):
                continue
            if nome == "NEO Investimentos" and "carta" not in t:
                continue
            if nome == "Dahlia Capital" and "carta" not in t:
                categorias = " ".join(x.text or "" for x in item.findall("category"))
                if "carta" not in sem_acentos(categorias):
                    continue
            fallback = _mes_anterior(publicado) if nome == "Dahlia Capital" else publicado
            resultado.append(Carta(
                data_do_texto(titulo, fallback), link, nome,
                serie_do_titulo(nome, titulo), titulo, link, cfg["formato"], "",
            ))
        return resultado

    def descobrir_html(self, cfg: dict[str, Any]) -> list[Carta]:
        soup = BeautifulSoup(self.get(cfg["listagem"]).text, "html.parser")
        resultado: list[Carta] = []
        kapitalo_ano = date.today().year
        kapitalo_mes_anterior = 13
        for a in soup.find_all("a", href=True):
            href = urljoin(cfg["site"], a["href"])
            contexto = texto_limpo(a.get_text(" ") + " " + (a.parent.get_text(" ") if a.parent else ""))
            if ".pdf" not in href.lower().split("?", 1)[0]:
                continue
            if cfg["nome"] == "Occam Brasil" and "carta mensal" not in sem_acentos(contexto):
                continue
            if cfg["nome"] == "Kapitalo Investimentos" and "carta" not in sem_acentos(contexto + href):
                continue
            titulo = contexto[:240] or Path(urlparse(href).path).stem
            fonte_data = contexto
            data_referencia: date | None = None
            # O K10 não imprime o ano junto ao rótulo; nessa trilha o ano do
            # upload não é confiável. Como a lista vem em ordem decrescente,
            # a virada dezembro→janeiro determina o ano sem usar o filename.
            if cfg["nome"] == "Kapitalo Investimentos":
                mes_rotulo = data_do_texto(contexto, date(kapitalo_ano, 1, 1)).month
                if mes_rotulo > kapitalo_mes_anterior:
                    kapitalo_ano -= 1
                kapitalo_mes_anterior = mes_rotulo
                data_referencia = date(kapitalo_ano, mes_rotulo, 1)
            elif cfg["nome"] == "Adam Capital":
                fonte_data += " " + Path(urlparse(href).path).name
            resultado.append(Carta(
                data_referencia or data_do_texto(fonte_data), href, cfg["nome"],
                serie_do_titulo(cfg["nome"], contexto), titulo, href, "pdf",
            ))
        return resultado

    def descobrir_ajax(self, cfg: dict[str, Any]) -> list[Carta]:
        # O endpoint configurado aponta sempre para o ano vigente.
        return self._descobrir_html_de_resposta(cfg, self.get(cfg["listagem"]).text)

    def _descobrir_html_de_resposta(self, cfg: dict[str, Any], corpo: str) -> list[Carta]:
        soup = BeautifulSoup(corpo, "html.parser")
        resultado = []
        for a in soup.find_all("a", href=True):
            href = urljoin(cfg["site"], a["href"].replace("http://", "https://"))
            if ".pdf" not in href.lower():
                continue
            contexto = texto_limpo(a.parent.get_text(" ") if a.parent else a.get_text(" "))
            resultado.append(Carta(
                data_do_texto(contexto), href, cfg["nome"],
                serie_do_titulo(cfg["nome"], contexto), contexto[:240], href, "pdf",
            ))
        return resultado

    def descobrir_url_previsivel(self, cfg: dict[str, Any]) -> list[Carta]:
        hoje = date.today()
        resultado = []
        # Consulta no máximo o mês corrente e os dois anteriores; 404 é esperado.
        for deslocamento in range(3):
            total = hoje.year * 12 + hoje.month - 1 - deslocamento
            ano, mes0 = divmod(total, 12)
            mes = mes0 + 1
            url = cfg["url_template"].format(
                ano=ano, mes=sem_acentos(MESES_PT[mes]), aa=str(ano)[2:]
            )
            resposta = self.client.get(url)
            time.sleep(self.pausa)
            if resposta.status_code == 404:
                continue
            resposta.raise_for_status()
            if "pdf" not in resposta.headers.get("content-type", "").lower() and not resposta.content.startswith(b"%PDF"):
                continue
            resultado.append(Carta(
                date(ano, mes, 1), url, cfg["nome"], "principal",
                f"Carta Mensal — {MESES_PT[mes].title()} de {ano}", url, "pdf",
            ))
        return resultado

    def _pdf_em_pagina(self, url: str) -> str:
        if not url:
            return ""
        return self._pdf_no_soup(BeautifulSoup(self.get(url).text, "html.parser"))

    @staticmethod
    def _pdf_no_soup(soup: BeautifulSoup) -> str:
        for a in soup.find_all("a", href=True):
            if ".pdf" in a["href"].lower().split("?", 1)[0]:
                return a["href"]
        return ""

    @staticmethod
    def _html_para_texto(corpo: str) -> str:
        soup = BeautifulSoup(corpo, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "form"]):
            tag.decompose()
        return soup.get_text("\n", strip=True)[:MAX_TEXT_CHARS]

    def extrair_texto(self, carta: Carta) -> str:
        if carta.texto:
            return carta.texto[:MAX_TEXT_CHARS]
        resposta = self.get(carta.url)
        tipo = resposta.headers.get("content-type", "").lower()
        if "pdf" not in tipo and not resposta.content.startswith(b"%PDF"):
            soup = BeautifulSoup(resposta.text, "html.parser")
            pdf = self._pdf_no_soup(soup)
            if pdf:
                resposta = self.get(urljoin(str(resposta.url), pdf))
                tipo = resposta.headers.get("content-type", "").lower()
            elif carta.formato in {"html", "pdf+html"}:
                texto = self._html_para_texto(str(soup))
                if texto:
                    return texto
            if "pdf" not in tipo and not resposta.content.startswith(b"%PDF"):
                raise ValueError(f"conteúdo não é PDF ({tipo or 'sem content-type'})")
        with pdfplumber.open(io.BytesIO(resposta.content)) as pdf:
            paginas = [(p.extract_text() or "") for p in pdf.pages]
        texto = "\n\n".join(paginas).strip()
        if not texto:
            raise ValueError("PDF sem texto extraível (possível documento escaneado)")
        return texto[:MAX_TEXT_CHARS]


def carregar_catalogo(path: Path = CATALOGO) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def marcadores(cfg: dict[str, Any]) -> dict[str, str]:
    novos = cfg.get("ultimas_cartas")
    if isinstance(novos, dict):
        return {str(k): str(v) for k, v in novos.items()}
    antigo = cfg.get("ultima_carta")
    if isinstance(antigo, dict):
        return {str(k): str(v) for k, v in antigo.items()}
    return {"principal": str(antigo)} if antigo else {}


def selecionar_novas(cartas: list[Carta], cfg: dict[str, Any]) -> list[Carta]:
    """Retorna delta por série; vazio significa primeira execução = só a mais recente."""
    por_serie: dict[str, list[Carta]] = {}
    for carta in cartas:
        por_serie.setdefault(carta.serie, []).append(carta)
    estado = marcadores(cfg)
    novas: list[Carta] = []
    for serie, itens in por_serie.items():
        itens.sort(reverse=True)
        marcador = estado.get(serie, "")
        if not marcador:
            novas.append(itens[0])
            continue
        for item in itens:
            if item.identificador == marcador:
                break
            novas.append(item)
    return sorted(novas, reverse=True)


def atualizar_estado(catalogo: dict[str, Any], processadas: Iterable[Carta]) -> None:
    por_nome = {g["nome"]: g for g in catalogo["gestoras"]}
    for carta in sorted(processadas):
        cfg = por_nome[carta.gestora]
        estado = marcadores(cfg)
        estado[carta.serie] = carta.identificador
        cfg["ultima_carta"] = estado


SYSTEM_PROMPT = """Você é um analista de investimentos que ensina profissionais do mercado
financeiro a DESTRINCHAR TECNICAMENTE as teses das gestoras brasileiras.

O leitor é do mercado: ele já sabe o que é duration, carrego e long&short. Ele não
paga por um resumo do que a carta diz — ele paga para entender COMO se analisa uma
carta: que mecanismo econômico sustenta a aposta, sob quais condições ela se paga,
e o que precisaria ser verdade para ela falhar.

Produza uma síntese em português (pt-BR), Markdown para Quarto, baseada SOMENTE no corpus.

Estrutura:
- Uma seção de nível 2 (##) por gestora, não por tema.
- Em cada seção, nesta ordem:
  1. **A tese em uma frase** — a aposta central, não a descrição do mês.
  2. **O mecanismo** — por que a gestora acha que isso se paga. Qual a cadeia causal
     (ex.: "inclinação tomada se paga se o BC cortar menos que o precificado, porque
     a ponta curta ancora e a longa carrega prêmio de risco fiscal"). Este é o item
     mais importante: é ele que ensina o leitor a pensar.
  3. **Posicionamento e números** — posições, retornos e atribuição, quando houver.
  4. **O que mudou** — somente quando o corpus trouxer comparação explícita.
  5. **Riscos** — os que a própria gestora aponta, e sob que condição a tese quebra.
- Quando a carta for essencialmente descritiva e não expuser tese estruturada, DIGA
  ISSO explicitamente e explique o que a ausência de tese sugere sobre o mandato do
  fundo. Não infle uma seção vazia com paráfrase.
- Quando houver mais de uma série da mesma gestora, identifique-as claramente.
- Termine com "## Convergências e divergências", comparando apenas gestoras presentes.
  Aqui o valor é apontar onde o consenso se forma e onde racha, e o que a divergência
  revela sobre premissas diferentes — não listar quem concorda com quem.
- Ao final, depois dessa seção, inclua um comentário HTML exatamente no formato
  `<!-- resumo_whatsapp: TEXTO -->`: uma síntese executiva específica da edição,
  em uma única linha, sem Markdown, com no máximo 450 caracteres.

Rigor:
- Distinga fato da carta de interpretação sua. Quando interpretar, sinalize.
- Não invente posições, retornos ou comparações. Preserve números importantes.
- Sem emojis, sem preâmbulo, sem seção de fontes (o programa a adiciona)."""


def montar_corpus(cartas: list[Carta]) -> str:
    blocos = []
    for i, carta in enumerate(cartas, 1):
        blocos.append(
            f"### Documento {i}\n"
            f"Gestora: {carta.gestora}\nSérie: {carta.serie}\n"
            f"Título: {carta.titulo}\nData de referência: {carta.data_referencia.isoformat()}\n"
            f"URL original: {carta.url}\n\n{carta.texto}"
        )
    return "\n\n---\n\n".join(blocos)


def sintetizar(cartas: list[Carta]) -> str:
    with Anthropic().messages.stream(
        model=MODEL,
        max_tokens=32000,
        thinking={"type": "adaptive"},
        output_config={"effort": "xhigh"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": montar_corpus(cartas)}],
    ) as stream:
        final = stream.get_final_message()
    return "\n".join(b.text for b in final.content if b.type == "text").strip()


def resumo_para_whatsapp(resumo: str) -> tuple[str, str]:
    """Separa a chamada executiva do documento; nunca envia Markdown/newlines."""
    padrao = r"\s*<!--\s*resumo_whatsapp:\s*(.*?)\s*-->\s*"
    achado = re.search(padrao, resumo, flags=re.IGNORECASE | re.DOTALL)
    if achado:
        chamada = achado.group(1)
        documento = re.sub(padrao, "\n", resumo, flags=re.IGNORECASE | re.DOTALL).strip()
    else:
        # Fallback defensivo: usa o começo da seção comparativa se o modelo
        # omitir o comentário contratado.
        trecho = re.split(r"## Convergências e divergências", resumo, flags=re.IGNORECASE)
        chamada = trecho[-1] if len(trecho) > 1 else resumo
        documento = resumo
    chamada = re.sub(r"[*_#>`\[\]()]", "", chamada)
    chamada = re.sub(r"\s+", " ", chamada).strip()
    if len(chamada) > 450:
        chamada = chamada[:447].rsplit(" ", 1)[0] + "..."
    return documento, chamada


QMD_TEMPLATE = r"""---
lang: pt-BR
format:
  pdf:
    pdf-engine: xelatex
    toc: false
    geometry: [margin=2.5cm]
    fontsize: 11pt
header-includes:
  - |
    \usepackage{graphicx}
    \usepackage{hyperref}
    \renewcommand{\maketitle}{}
---

```{=latex}
\begin{titlepage}
\thispagestyle{empty}
\centering
\includegraphics[width=4cm]{../../AM.png}\par
\vspace{0.8cm}
{\huge\bfseries Síntese das Cartas das Gestoras\par}
\vspace{1em}
{\Large Teses, mudanças de posicionamento e riscos\par}
\vspace{1.5em}
{\large Vitor Wilher\footnote{Bacharel e Mestre em Economia pela UFF, Candidato ao PhD em Economia pela EPGE/FGV. Especialista em Ciências de Dados e Inteligência Artificial Generativa pela PUC-Rio e Data Tech Lead na Análise Macro.}\par}
\vspace{0.5em}
{\normalsize __DATA__\par}
\vfill
\end{titlepage}
\begingroup\small
\tableofcontents
\endgroup
\clearpage
```

__RESUMO__

---

## Cartas originais

__FONTES__
"""


def escrever_qmd(resumo: str, cartas: list[Carta], exercicio: str = "") -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    hoje = date.today()
    fontes = "\n".join(
        f"- **{c.gestora} — {c.titulo}** ([original]({c.url}))" for c in cartas
    )
    corpo = f"{resumo}\n\n{exercicio}" if exercicio else resumo
    conteudo = (QMD_TEMPLATE.replace("__DATA__", f"{hoje.day} de {MESES_PT[hoje.month]} de {hoje.year}")
                .replace("__RESUMO__", corpo).replace("__FONTES__", fontes))
    caminho = OUTPUT_DIR / f"resumo-{hoje.isoformat()}.qmd"
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def renderizar(qmd: Path) -> Path:
    subprocess.run(["quarto", "render", str(qmd), "--to", "pdf"], check=True)
    pdf = qmd.with_suffix(".pdf")
    if not pdf.exists():
        raise FileNotFoundError(f"Quarto não criou {pdf}")
    return pdf


def enviar_whatsapp(pdf: Path, cartas: list[Carta], resumo_executivo: str) -> None:
    token = os.environ["WHATSAPP_TOKEN"]
    phone_id = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
    destino = os.environ["WHATSAPP_TO_NUMBER"]
    template = (
        os.environ.get("WHATSAPP_CARTAS_TEMPLATE")
        or "sintese_cartas_gestoras"
    )
    base = f"https://graph.facebook.com/{META_API_VERSION}/{phone_id}"
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=60) as client:
        waba = os.environ.get("WHATSAPP_WABA_ID") or WABA_PRODUCAO
        status_resp = client.get(
            f"https://graph.facebook.com/{META_API_VERSION}/{waba}/message_templates",
            headers=headers,
            params={"name": template, "fields": "name,status,category"},
        )
        status_resp.raise_for_status()
        candidatos = status_resp.json().get("data", [])
        if not candidatos or candidatos[0].get("status") != "APPROVED":
            status = candidatos[0].get("status") if candidatos else "INEXISTENTE"
            raise RuntimeError(f"template {template!r} ainda não está aprovado: {status}")
        with pdf.open("rb") as arquivo:
            resp = client.post(
                f"{base}/media", headers=headers,
                data={"messaging_product": "whatsapp", "type": "application/pdf"},
                files={"file": (pdf.name, arquivo, "application/pdf")},
            )
        if resp.status_code >= 400:
            raise RuntimeError(f"Falha no upload: {resp.status_code} {resp.text}")
        media_id = resp.json()["id"]
        nomes = " · ".join(dict.fromkeys(c.gestora for c in cartas))
        payload = {
            "messaging_product": "whatsapp", "to": destino, "type": "template",
            "template": {"name": template, "language": {"code": "pt_BR"}, "components": [
                {"type": "header", "parameters": [{"type": "document", "document": {"id": media_id, "filename": pdf.name}}]},
                {"type": "body", "parameters": [
                    {"type": "text", "text": date.today().strftime("%d/%m/%Y")},
                    {"type": "text", "text": nomes},
                    {"type": "text", "text": resumo_executivo},
                ]},
            ]},
        }
        resp = client.post(f"{base}/messages", headers={**headers, "Content-Type": "application/json"}, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"Falha ao enviar mensagem: {resp.status_code} {resp.text}")
        dados = resp.json()
        wamid = (dados.get("messages") or [{}])[0].get("id", "não informado")
        print(f"WhatsApp aceito pela API; wamid={wamid}")


def salvar_catalogo(catalogo: dict[str, Any], path: Path = CATALOGO) -> None:
    """Atualiza só as linhas de estado, preservando comentários e notas do catálogo.

    O bloco de um `ultima_carta` pode ocupar MAIS DE UMA LINHA: o `safe_dump` de um
    mapa longo (Occam e Legacy, com duas séries de URL longa) quebra a linha. O
    padrão precisa consumir a linha do campo e todas as continuações — que são as
    linhas seguintes com indentação MENOR que a do campo, produzidas pelo dump.
    Casar só a primeira linha deixava a cauda antiga órfã e corrompia o YAML: foi
    o que aconteceu na execução de 2026-09-08, que quebrou o catálogo da Occam.
    """
    estados = iter(g.get("ultima_carta", "") for g in catalogo["gestoras"])

    def serializar(valor: Any, indent: str) -> str:
        bruto = yaml.safe_dump(
            valor, allow_unicode=True, default_flow_style=True, sort_keys=True,
            width=10**6,  # linha única: evita a quebra que gerava a órfã
        ).strip()
        return f"{indent}ultima_carta: {bruto}"

    def substituir(match: re.Match[str]) -> str:
        return serializar(next(estados), match.group(1))

    original = path.read_text(encoding="utf-8")
    # O valor é um mapa em fluxo (`{...}`) ou uma string simples. Quando é mapa e
    # o dump o quebrou, a continuação segue até a chave de fechamento — é isso que
    # o primeiro ramo consome. O segundo cobre o valor de linha única (mapa curto,
    # string ou vazio).
    padrao = (
        r"(?m)^([ \t]*)ultima_carta:[ \t]*"
        r"(?:\{[^{}]*\}|.*)"
    )
    novo, quantidade = re.subn(padrao, substituir, original, flags=re.DOTALL)
    esperado = len(catalogo["gestoras"])
    if quantidade != esperado:
        raise ValueError(f"catálogo tem {quantidade} linhas de estado; esperado: {esperado}")

    # Rede de segurança: nunca gravar um catálogo que não volta a carregar.
    try:
        conferido = yaml.safe_load(novo)
        if len(conferido["gestoras"]) != esperado:
            raise ValueError("contagem de gestoras mudou após a serialização")
    except Exception as erro:
        raise ValueError(f"serialização produziu YAML inválido: {erro}") from erro

    path.write_text(novo, encoding="utf-8")


def executar(args: argparse.Namespace) -> int:
    catalogo = carregar_catalogo()
    coletor = Coletor(pausa=args.pausa)
    novas: list[Carta] = []
    try:
        for cfg in catalogo["gestoras"]:
            try:
                encontradas = coletor.descobrir(cfg)
                delta = selecionar_novas(encontradas, cfg)
                novas.extend(delta)
                print(f"{cfg['nome']}: {len(encontradas)} encontrada(s), {len(delta)} nova(s)")
                if args.discover_only:
                    for carta in delta:
                        print("  " + json.dumps(carta.resumo_json(), ensure_ascii=False))
            except Exception as exc:
                print(f"[aviso] {cfg['nome']}: {exc}", file=sys.stderr)
    finally:
        coletor.close()

    if args.discover_only:
        return 0
    if not novas:
        print("Nenhuma carta nova; encerrando sem gerar ou enviar.")
        return 0

    coletor = Coletor(pausa=args.pausa)
    processadas: list[Carta] = []
    try:
        for carta in novas:
            try:
                print(f"Extraindo: {carta.gestora} — {carta.titulo}")
                carta.texto = coletor.extrair_texto(carta)
                processadas.append(carta)
            except Exception as exc:
                print(f"[aviso] extração de {carta.gestora}: {exc}", file=sys.stderr)
    finally:
        coletor.close()
    if not processadas:
        print("Nenhuma carta pôde ser extraída; estado preservado.", file=sys.stderr)
        return 1

    resumo_documento, resumo_executivo = resumo_para_whatsapp(sintetizar(processadas))
    exercicio = ""
    if not args.sem_exercicio:
        resultado = exercicio_da_semana(resumo_documento)
        if resultado is not None:
            conceito, exercicio = resultado
            print(f"Exercício da semana: {conceito}")
    qmd = escrever_qmd(resumo_documento, processadas, exercicio)
    print(f"Gerado: {qmd}")
    pdf = renderizar(qmd) if args.pdf else None
    if pdf:
        print(f"Gerado: {pdf}")
    if args.send:
        if not pdf:
            raise ValueError("--send exige --pdf")
        enviar_whatsapp(pdf, processadas, resumo_executivo)
    atualizar_estado(catalogo, processadas)
    salvar_catalogo(catalogo)
    print("Estado atualizado em gestoras/gestoras.yml")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discover-only", action="store_true", help="descobre o delta sem baixar, sintetizar ou alterar estado")
    parser.add_argument("--pdf", action="store_true", help="renderiza PDF com Quarto")
    parser.add_argument("--send", action="store_true", help="envia o PDF pelo WhatsApp (exige --pdf)")
    parser.add_argument("--sem-exercicio", action="store_true", help="pula o exercício em Python da semana")
    parser.add_argument("--pausa", type=float, default=0.5, help="pausa educada entre requests (segundos)")
    args = parser.parse_args()
    if args.send and not args.pdf:
        parser.error("--send exige --pdf")
    return args


if __name__ == "__main__":
    raise SystemExit(executar(parse_args()))
