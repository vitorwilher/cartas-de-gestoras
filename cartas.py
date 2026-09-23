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
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from email.utils import parsedate_to_datetime
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

from exercicios.execucao import NOME_GRAFICO, gerar_grafico, remover_referencia
from exercicios.geracao import exercicio_da_semana

load_dotenv()

ROOT = Path(__file__).resolve().parent
CATALOGO = ROOT / "gestoras" / "gestoras.yml"
OUTPUT_DIR = ROOT / "digests" / "resumo"
TEMP_DIR = ROOT / "cartas"
# Modelo mais capaz disponível. No Fable 5.1 o thinking é SEMPRE ativo: passar
# `thinking` explícito com qualquer coisa que não seja adaptive devolve 400.
MODEL = os.environ.get("ANTHROPIC_MODEL") or "claude-fable-5-1"
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


# Detecta se um trecho já contém nome de mês (sem acento, minúsculo). Usado para
# decidir se vale subir na árvore do HTML atrás do rótulo com a data.
_TEM_MES = re.compile(
    r"\b(" + "|".join(sem_acentos(m) for m in MESES_PT if m) + r")\b"
)


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


_DATA_EN = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2}),\s+(20\d{2})\b"
)


def data_em_ingles(valor: str) -> date | None:
    """"Sep 22, 2026" / "August 4, 2026" -> date. None quando não há data.

    Devolve None em vez de cair no fallback de hoje: um item sem data datado
    com hoje vira sempre o "mais recente" e trava o delta (caso Genoa, 23/09).
    """
    achado = _DATA_EN.search(sem_acentos(texto_limpo(valor)))
    if not achado:
        return None
    mes, dia, ano = achado.groups()
    return date(int(ano), MESES[mes], int(dia))


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
    regiao: str = field(compare=False, default="brasil")

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
        for carta in cartas:
            carta.regiao = cfg.get("regiao", "brasil")
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
            # Na Genoa o rótulo do link é só "PDF" e a data ("Carta Mensal /
            # Agosto/2026") vive no AVÔ, não no pai. Sem subir um nível, toda
            # carta cairia no fallback de hoje e as 78 ficariam com a mesma data
            # — falha silenciosa, sem exceção nenhuma. Só sobe quando o contexto
            # imediato não tem mês, para não mudar o comportamento das demais.
            if a.parent is not None and a.parent.parent is not None \
                    and not _TEM_MES.search(sem_acentos(contexto)):
                contexto = texto_limpo(a.parent.parent.get_text(" "))
            if cfg["nome"] == "Occam Brasil" and "carta mensal" not in sem_acentos(contexto):
                continue
            # A página da Genoa mistura cartas com white papers sem mês no rótulo.
            # Sem data, o item caía no fallback de hoje, virava sempre o "mais
            # recente" e o delta parava nele: a série travava sem erro nenhum.
            if cfg["nome"] == "Genoa Capital" and "carta mensal" not in sem_acentos(contexto):
                continue
            if cfg["nome"] == "Kapitalo Investimentos" and "carta" not in sem_acentos(contexto + href):
                continue
            # A página da Adam lista, sob o mesmo rótulo, os Relatórios Gerenciais
            # por fundo. Só a carta interessa; o nome do arquivo é o que distingue.
            if cfg["nome"] == "Adam Capital" and "carta" not in Path(urlparse(href).path).name.lower():
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
                # "Carta_Mensal_AGOSTO_2026.pdf": o "_" é caractere de palavra e
                # anula o \b da busca do mês — a carta caía no fallback de hoje.
                fonte_data += " " + re.sub(r"[_\-.]+", " ", Path(urlparse(href).path).name)
            resultado.append(Carta(
                data_referencia or data_do_texto(fonte_data), href, cfg["nome"],
                serie_do_titulo(cfg["nome"], contexto), titulo, href, "pdf",
            ))
        return resultado

    def descobrir_html_posts(self, cfg: dict[str, Any]) -> list[Carta]:
        """Listagem de posts com data em inglês no cartão (Oaktree, Bridgewater).

        `seletor` (CSS) escolhe os cartões; sem ele, o cartão é o pai de cada link
        que casa `padrao_link`. Cartão sem data é DESCARTADO, nunca datado com hoje.
        """
        soup = BeautifulSoup(self.get(cfg["listagem"]).text, "html.parser")
        padrao = re.compile(cfg["padrao_link"])
        if cfg.get("seletor"):
            cartoes = [
                (c, next((a for a in c.find_all("a", href=True) if padrao.search(a["href"])), None))
                for c in soup.select(cfg["seletor"])
            ]
        else:
            cartoes = [(a.parent, a) for a in soup.find_all("a", href=padrao)]
        resultado: list[Carta] = []
        for cartao, link in cartoes:
            if cartao is None or link is None:
                continue
            data = data_em_ingles(cartao.get_text(" "))
            if data is None:
                continue
            titulos = [texto_limpo(a.get_text(" ")) for a in cartao.find_all("a", href=True)
                       if padrao.search(a["href"])]
            titulo = next((t for t in titulos if t), "") or Path(urlparse(link["href"]).path).name
            href = urljoin(cfg["site"], link["href"])
            resultado.append(Carta(data, href, cfg["nome"], "principal", titulo, href, cfg["formato"]))
        return resultado

    def descobrir_pdf_da_pagina(self, cfg: dict[str, Any]) -> list[Carta]:
        """Carta trimestral da GMO: a listagem só aponta a edição corrente.

        A página da carta traz o PDF inteiro (`padrao_pdf`). O trimestre não está
        escrito em lugar nenhum do texto da página, só no nome do arquivo
        (`gmo-quarterly-letter_2q-2026.pdf`) — exceção à regra da data do texto,
        como na Adam. Sem trimestre reconhecível, nada é devolvido.
        """
        soup = BeautifulSoup(self.get(cfg["listagem"]).text, "html.parser")
        link = soup.find("a", href=re.compile(cfg["padrao_link"]))
        if link is None:
            return []
        pagina = urljoin(cfg["site"], link["href"])
        soup = BeautifulSoup(self.get(pagina).text, "html.parser")
        pdf = soup.find("a", href=re.compile(cfg["padrao_pdf"]))
        if pdf is None:
            return []
        href = urljoin(cfg["site"], pdf["href"])
        trimestre = re.search(r"([1-4])q-?(20\d{2})", Path(urlparse(href).path).name, re.I)
        if not trimestre:
            return []
        q, ano = int(trimestre.group(1)), int(trimestre.group(2))
        titulo_pagina = soup.find("meta", property="og:title")
        titulo = f"Quarterly Letter {q}Q {ano}"
        if titulo_pagina and titulo_pagina.get("content"):
            titulo += f" — {texto_limpo(titulo_pagina['content'])}"
        return [Carta(date(ano, 3 * q, 1), href, cfg["nome"], "principal", titulo, href, "pdf")]

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

    def descobrir_url_serial(self, cfg: dict[str, Any]) -> list[Carta]:
        """URL com contador AAAAMM, para quando a listagem HTML está desatualizada.

        Nasceu da Sparta: a tabela da página congelou em 202512, mas os PDFs de
        2026 existem no mesmo padrão e simplesmente não foram listados. Um
        coletor de `href` perderia 8 meses de cartas SEM ERRO NENHUM — só
        devolveria menos itens. É a exceção que confirma a regra de ouro: aqui
        templar a URL é mais confiável que confiar na página.

        Varre do mês corrente para trás; 404 é resposta esperada (a carta do mês
        ainda não saiu), não falha.
        """
        hoje = date.today()
        janela = int(cfg.get("meses_para_tras", 3))
        resultado: list[Carta] = []
        for deslocamento in range(janela):
            total = hoje.year * 12 + hoje.month - 1 - deslocamento
            ano, mes0 = divmod(total, 12)
            mes = mes0 + 1
            url = cfg["url_template"].format(ano=ano, mes=f"{mes:02d}", aa=str(ano)[2:])
            resposta = self.client.get(url)
            time.sleep(self.pausa)
            if resposta.status_code == 404:
                continue
            resposta.raise_for_status()
            if not resposta.content.startswith(b"%PDF"):
                continue
            resultado.append(Carta(
                date(ano, mes, 1), url, cfg["nome"], "principal",
                f"Carta Mensal — {MESES_PT[mes].title()} de {ano}", url, "pdf",
            ))
        return resultado

    def descobrir_url_fixa(self, cfg: dict[str, Any]) -> list[Carta]:
        """Um único PDF numa URL que é SOBRESCRITA a cada edição (Opportunity).

        ⚠️ Aqui a URL NÃO identifica a carta — ela é sempre a mesma. Usar a URL
        como identificador faria o pipeline ver a mesma carta para sempre e
        nunca detectar novidade.

        O identificador sai do CONTEÚDO: a data impressa na capa ("Agosto 2026"),
        que é a regra de ouro da data do projeto aplicada ao caso extremo. O
        `Last-Modified` do servidor serve de desempate quando o texto falha
        (verificado: devolve data coerente com a publicação).
        """
        resposta = self.get(cfg["listagem"])
        if not resposta.content.startswith(b"%PDF"):
            raise RuntimeError(
                f"{cfg['nome']}: a URL fixa não devolveu PDF "
                f"(content-type={resposta.headers.get('content-type')!r})."
            )

        texto_capa = ""
        try:
            with pdfplumber.open(io.BytesIO(resposta.content)) as pdf:
                texto_capa = " ".join(
                    (p.extract_text() or "") for p in pdf.pages[:2]
                )
        except Exception as exc:  # noqa: BLE001 — extrair data é best-effort
            print(f"  [aviso] {cfg['nome']}: não consegui ler a capa ({exc}); "
                  f"caindo no Last-Modified.", file=sys.stderr)

        fallback = date.today()
        cabecalho = resposta.headers.get("last-modified", "")
        if cabecalho:
            try:
                fallback = parsedate_to_datetime(cabecalho).date()
            except (TypeError, ValueError):
                pass

        referencia = data_do_texto(texto_capa[:600], fallback)
        return [Carta(
            referencia, f"{cfg['nome']}-{referencia:%Y-%m}", cfg["nome"], "principal",
            f"Carta de Gestão — {MESES_PT[referencia.month].title()} de {referencia.year}",
            cfg["listagem"], "pdf",
        )]

    def _pdf_em_pagina(self, url: str) -> str:
        if not url:
            return ""
        return self._pdf_no_soup(BeautifulSoup(self.get(url).text, "html.parser"))

    @staticmethod
    def _pdf_no_soup(soup: BeautifulSoup) -> str:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Oaktree: href="javascript:openPDF('Título','https://.../memo.pdf')".
            # Devolver o href cru faria o urljoin montar uma URL inválida.
            if href.lower().startswith("javascript:"):
                embutida = re.search(r"https?://[^'\"]+?\.pdf[^'\"]*", href, re.I)
                if embutida:
                    return embutida.group(0)
                continue
            if ".pdf" in href.lower().split("?", 1)[0]:
                return href
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
financeiro a DESTRINCHAR TECNICAMENTE as teses das gestoras brasileiras — e, quando
houver, das grandes gestoras internacionais que o corpus trouxer.

O leitor é do mercado: ele já sabe o que é duration, carrego e long&short. Ele não
paga por um resumo do que a carta diz — ele paga para entender COMO se analisa uma
carta: que mecanismo econômico sustenta a aposta, sob quais condições ela se paga,
e o que precisaria ser verdade para ela falhar.

Produza uma síntese em português (pt-BR), Markdown para Quarto, baseada SOMENTE no corpus.

Estrutura:
- **Abra com uma seção `## Nesta edição`** de 2 a 4 parágrafos, antes de qualquer
  gestora. Ela situa o leitor: que semana foi esta nos mercados, quais casas
  publicaram e por quê isso importa, e qual é a tensão central que atravessa as
  cartas desta edição. Termine dizendo, em uma frase, o que o leitor vai encontrar
  adiante. Não é sumário — é a leitura editorial que dá sentido ao conjunto.
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
- Cada documento traz o campo "Região". As seções acima são das gestoras de região
  "brasil"; as de região "internacional" seguem regras próprias, descritas adiante.
- Depois das brasileiras, "## Convergências e divergências", comparando apenas
  gestoras BRASILEIRAS presentes. Se houver menos de duas, omita esta seção.
  Aqui o valor é apontar onde o consenso se forma e onde racha, e o que a divergência
  revela sobre premissas diferentes — não listar quem concorda com quem.
  **DIMENSIONE o consenso.** Quando o bloco PESO PATRIMONIAL estiver no contexto,
  não diga apenas quantas casas estão de cada lado: diga quanto patrimônio sob
  mandato compatível cada lado representa. "Quatro casas, somando R$ 58 bi sob
  mandato de juro e macro, veem o ciclo virando; duas, com R$ 12 bi, discordam"
  informa muito mais que "quatro contra duas" — mostra se o consenso é da maioria
  ou de quem carrega o risco. Regras inegociáveis ao usar esses números:
    · Use o PL do EIXO correspondente à tese, NUNCA o PL total da casa. A Kinea
      tem R$ 177 bi totais e só R$ 9,3 bi em juro/macro; usar o total numa conta
      sobre juro atribui a ela patrimônio que está em crédito imobiliário.
    · Mandato não é posição. Escreva "sob mandato compatível com a tese", jamais
      "apostando" ou "posicionado" — a CVM diz o que o fundo PODE fazer, e só a
      carta diz o que ele fez.
    · Se a tese em discussão não corresponder a nenhum eixo da tabela, compare
      sem número. Não force o cruzamento.
- **Gestoras internacionais** (região "internacional"), SOMENTE quando o corpus
  as trouxer. Vêm DEPOIS das brasileiras e da seção de convergências, uma seção
  de nível 2 por gestora, com o título exatamente "## <Gestora> — internacional".
  Mesma estrutura de cinco itens, mais um sexto:
  6. **Leitura para o Brasil** — por qual canal a tese chega aos ativos
     brasileiros (dólar, juro longo americano, prêmio de risco de emergentes,
     commodities, fluxo estrangeiro na bolsa). É SEMPRE interpretação sua:
     sinalize como tal, e diga "sem canal relevante" quando não houver um.
  Os textos são em inglês: escreva em português e traduza os termos, mas
  preserve entre parênteses o título original e expressões que o próprio autor
  cunhou (ex.: "second-level thinking" do Howard Marks).
  O bloco PESO PATRIMONIAL é da CVM e cobre só as brasileiras: NUNCA atribua
  patrimônio a uma gestora internacional.
- Havendo gestora internacional, feche com "## O olhar de fora": onde as teses
  de fora coincidem ou colidem com as das brasileiras desta edição (ou entre si,
  se não houver brasileiras). É a ponte que o leitor brasileiro não faz sozinho.
- Ao final, depois dessa seção, inclua um comentário HTML exatamente no formato
  `<!-- resumo_whatsapp: TEXTO -->`: uma síntese executiva específica da edição,
  em uma única linha, sem Markdown, com no máximo 450 caracteres.

Vocabulário — o leitor é do mercado, mas não é operador de renda fixa:
- **Todo termo técnico é explicado na primeira vez que aparece**, em aposto curto,
  sem interromper a leitura. Exemplos do registro certo: "tomado em inclinação
  (*steepener*: uma aposta em que o juro longo sobe mais que o curto, ou cai
  menos)"; "carrego (o retorno que a posição rende só pela passagem do tempo)".
- Isso vale para termos em inglês, jargão de mesa e siglas de instrumento —
  steepener, flattener, carrego, duration, breakeven, DI1, NTN-B, long&short.
- Uma explicação por termo, na primeira ocorrência. Não repita nas seguintes, e
  não explique o que é trivial para quem lê carta de gestora (Selic, Ibovespa, CDI).

Rigor:
- Distinga fato da carta de interpretação sua. Quando interpretar, sinalize.
- Não invente posições, retornos ou comparações. Preserve números importantes.
- Sem emojis, sem preâmbulo, sem seção de fontes (o programa a adiciona)."""


def montar_corpus(cartas: list[Carta]) -> str:
    blocos = []
    for i, carta in enumerate(cartas, 1):
        blocos.append(
            f"### Documento {i}\n"
            f"Gestora: {carta.gestora}\nRegião: {carta.regiao}\nSérie: {carta.serie}\n"
            f"Título: {carta.titulo}\nData de referência: {carta.data_referencia.isoformat()}\n"
            f"URL original: {carta.url}\n\n{carta.texto}"
        )
    return "\n\n---\n\n".join(blocos)


def contexto_patrimonial() -> str:
    """Tabela de PL por casa e por eixo de mandato, vinda da CVM.

    É o que permite dimensionar o consenso ("N casas somando R$ X bi") em vez de
    só contá-lo. Gerada por `analises/peso_das_teses.py`.

    Falha aqui NUNCA derruba a síntese — mesmo princípio da falha isolada por
    gestora. Sem o arquivo, a edição sai sem os números de peso, que é o
    comportamento de antes desta função existir.
    """
    caminho = Path(__file__).parent / "analises" / "peso_das_teses_prompt.txt"
    try:
        texto = caminho.read_text(encoding="utf8").strip()
    except OSError as e:
        print(f"[peso] contexto patrimonial indisponível ({e}); "
              f"a síntese sai sem dimensionar o consenso.", file=sys.stderr)
        return ""
    if not texto:
        return ""
    return f"\n\n---\n\n{texto}\n"


def sintetizar(cartas: list[Carta], nota: str = "") -> str:
    corpus = montar_corpus(cartas) + contexto_patrimonial()
    if nota:
        # O modelo precisa saber da nota para "Nesta edição" não contradizê-la;
        # o texto da nota entra no documento por fora, em escrever_qmd.
        corpus += (f"\n\n---\n\nNOTA EDITORIAL DESTA EDIÇÃO (contexto, não é documento; "
                   f"o leitor já a lê numa caixa acima da síntese — não a repita):\n{nota}\n")
    with Anthropic().messages.stream(
        model=MODEL,
        # 64k de saída e effort "high": com `max`, o Fable 5.1 gasta o orçamento
        # inteiro pensando e a resposta é cortada (stop_reason=max_tokens) —
        # verificado em 2026-09-08, 32k de saída rendiam 2 KB de texto truncado.
        max_tokens=64000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": corpus}],
    ) as stream:
        final = stream.get_final_message()

    if final.stop_reason == "max_tokens":
        raise RuntimeError(
            "A síntese foi cortada por max_tokens: o documento sairia incompleto. "
            "Aumente max_tokens ou reduza o effort."
        )
    texto = "\n".join(b.text for b in final.content if b.type == "text").strip()
    if not texto:
        raise RuntimeError(
            f"A síntese voltou vazia (stop_reason={final.stop_reason}). Nada foi gravado."
        )
    return texto


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


QMD_TEMPLATE = """---
title: "Cartas de *Gestoras*"
subtitle: "__SUBTITULO__"
author: "Vitor Wilher"
date: "__DATA_ISO__"
date-format: "D [de] MMMM [de] YYYY"
lang: pt-BR
livro:
  category: "Mercado Financeiro"
  kicker: "SÍNTESE SEMANAL"
  edition: "__DATA__"
  tagline: "A verdade está nos dados."
format:
  am-livro-typst:
    toc-depth: 2
---

__RESUMO__

## Cartas originais

__FONTES__
"""


def escrever_qmd(resumo: str, cartas: list[Carta], exercicio: str = "",
                 ilegiveis: list[Carta] | None = None, nota: str = "") -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    hoje = date.today()
    fontes = "\n".join(
        f"- **{c.gestora} — {c.titulo}** ([original]({c.url}))" for c in cartas
    )
    # Carta que saiu mas não pôde ser lida (PDF escaneado) é anunciada com o link:
    # o assinante precisa saber que ela existe, senão a ausência parece cobertura
    # completa. O texto diz o motivo para não soar como falha de curadoria.
    if ilegiveis:
        avisos = "\n".join(
            f"- **{c.gestora} — {c.titulo}** ([original]({c.url}))" for c in ilegiveis
        )
        fontes += (
            "\n\n### Publicada nesta janela, fora da síntese\n\n"
            "O PDF não expõe camada de texto (documento escaneado), então não foi"
            " possível analisá-lo automaticamente. O original está aqui:\n\n"
            f"{avisos}"
        )
    if exercicio:
        # O texto do exercício referencia grafico-exercicio.png. Rodamos o código
        # para produzir a figura AO LADO do .qmd; se falhar, tiramos a referência —
        # senão o Typst aborta o documento inteiro por uma imagem ausente.
        if gerar_grafico(exercicio, OUTPUT_DIR / NOME_GRAFICO) is None:
            exercicio = remover_referencia(exercicio)
    corpo = f"{resumo}\n\n{exercicio}" if exercicio else resumo
    if nota:
        # Caixa, não seção: um título ## seria lido como gestora pelo e-mail e
        # pelo catálogo do MCP, que listam as gestoras pelos títulos de nível 2.
        # Vai DENTRO de "Nesta edição": cada ## abre página nova no am-livro, e
        # a caixa antes do primeiro título ficava sozinha numa página em branco.
        caixa = f'::: {{.saiba-mais title="Nota desta edição"}}\n{nota}\n:::\n\n'
        corpo, n = re.subn(r"(?m)^(## Nesta edição[^\n]*\n)", lambda m: m.group(1) + "\n" + caixa, corpo, count=1)
        if not n:
            corpo = caixa + corpo
    data_extenso = f"{hoje.day} de {MESES_PT[hoje.month]} de {hoje.year}"
    nomes = sorted({c.gestora.split()[0] for c in cartas})
    subtitulo = "Teses, mecanismos e riscos — " + (
        ", ".join(nomes) if len(nomes) <= 4 else f"{len(nomes)} gestoras nesta edição"
    )
    conteudo = (QMD_TEMPLATE
                .replace("__DATA_ISO__", hoje.isoformat())
                .replace("__DATA__", f"Edição de {data_extenso}")
                .replace("__SUBTITULO__", subtitulo)
                .replace("__RESUMO__", corpo)
                .replace("__FONTES__", fontes))
    caminho = OUTPUT_DIR / f"resumo-{hoje.isoformat()}.qmd"
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def renderizar(qmd: Path) -> Path:
    """Renderiza com a extensão `am-livro` (Typst), o design system da casa.

    O Quarto 1.9+ traz o Typst embutido — não é preciso TinyTeX neste projeto.

    O render acontece num diretório temporário com o `.qmd` AO LADO de
    `_extensions/` e `_brand.yml`. Isso não é capricho: o Quarto resolve extensão
    e brand a partir do diretório DO ARQUIVO, e não sobe para a raiz do projeto
    nem com um `_quarto.yml` declarado — um `.qmd` em `digests/resumo/` falha com
    "Unable to read the extension 'am-livro'". Copiar é mais simples e mais
    robusto do que espalhar caminhos relativos pelos .qmd.
    """
    with tempfile.TemporaryDirectory(prefix="cartas-render-") as tmp:
        trabalho = Path(tmp)
        shutil.copytree(ROOT / "_extensions", trabalho / "_extensions")
        shutil.copy2(ROOT / "_brand.yml", trabalho / "_brand.yml")
        alvo = trabalho / qmd.name
        shutil.copy2(qmd, alvo)
        # A figura do exercício mora ao lado do .qmd e precisa acompanhá-lo.
        figura = qmd.parent / NOME_GRAFICO
        if figura.exists():
            shutil.copy2(figura, trabalho / NOME_GRAFICO)

        subprocess.run(
            ["quarto", "render", alvo.name, "--to", "am-livro-typst"],
            cwd=trabalho,
            check=True,
        )

        gerado = alvo.with_suffix(".pdf")
        if not gerado.exists():
            raise FileNotFoundError(f"Quarto não criou {gerado.name}")
        pdf = qmd.with_suffix(".pdf")
        shutil.copy2(gerado, pdf)
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
    # O valor é um mapa em fluxo (`{...}`) — que o dump pode ter quebrado em várias
    # linhas — ou um escalar de uma linha (string vazia na inicialização).
    #
    # `[^\n]*` no segundo ramo, e NÃO `.*` com re.DOTALL: com DOTALL o ponto casa
    # newline e o ramo escalar engoliria o resto do arquivo. Só o primeiro ramo
    # precisa atravessar linhas, e ele já o faz sozinho por causa da classe negada.
    padrao = r"(?m)^([ \t]*)ultima_carta:[ \t]*(?:\{[^{}]*\}|[^\n]*)"
    novo, quantidade = re.subn(padrao, substituir, original)
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
    ilegiveis: list[Carta] = []
    try:
        for carta in novas:
            try:
                print(f"Extraindo: {carta.gestora} — {carta.titulo}")
                carta.texto = coletor.extrair_texto(carta)
                processadas.append(carta)
            except Exception as exc:
                print(f"[aviso] extração de {carta.gestora}: {exc}", file=sys.stderr)
                ilegiveis.append(carta)
    finally:
        coletor.close()
    if not processadas:
        # Sem nada sintetizável não há edição — mas o estado AVANÇA sobre as
        # ilegíveis. Preservá-lo fazia a mesma carta ser retentada toda terça,
        # falhando igual: um PDF escaneado da Adam deixou os runs de 18/08 e
        # 25/08 vermelhos, e teria travado todas as seguintes.
        print("Nenhuma carta pôde ser extraída; marcando como vistas.", file=sys.stderr)
        atualizar_estado(catalogo, ilegiveis)
        salvar_catalogo(catalogo)
        return 0

    resumo_documento, resumo_executivo = resumo_para_whatsapp(sintetizar(processadas, args.nota))
    exercicio = ""
    if not args.sem_exercicio:
        resultado = exercicio_da_semana(resumo_documento)
        if resultado is not None:
            conceito, exercicio = resultado
            print(f"Exercício da semana: {conceito}")
    qmd = escrever_qmd(resumo_documento, processadas, exercicio, ilegiveis, args.nota)
    print(f"Gerado: {qmd}")
    pdf = renderizar(qmd) if args.pdf else None
    if pdf:
        print(f"Gerado: {pdf}")
    if args.send:
        if not pdf:
            raise ValueError("--send exige --pdf")
        enviar_whatsapp(pdf, processadas, resumo_executivo)
    # As ilegíveis entram no estado junto com as sintetizadas: já foram anunciadas
    # no documento, e retentá-las repetiria a mesma falha toda semana.
    atualizar_estado(catalogo, [*processadas, *ilegiveis])
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
    parser.add_argument("--nota", default="", help="nota editorial da edição (caixa no topo do PDF)")
    args = parser.parse_args()
    if args.send and not args.pdf:
        parser.error("--send exige --pdf")
    return args


if __name__ == "__main__":
    raise SystemExit(executar(parse_args()))
