#!/usr/bin/env python3
"""Cria o broadcast da edição da semana no ConvertKit, para a tag do projeto.

É assim que o assinante recebe a síntese toda terça — o que a página de obrigado
promete. O WhatsApp entrega só para quem escreveu (janela de 24h); o e-mail
alcança todos, sem template, sem custo por conversa e sem risco de qualidade.

Por decisão do Vitor (2026-09-09), o broadcast NASCE COMO RASCUNHO. Nada é
enviado sem revisão — a regra "preparar, nunca disparar" continua valendo para
comunicação em massa.

⚠️ Usa a API **v4** (`api.kit.com/v4`, header `X-Kit-Api-Key`). A v3 aceita o
`subscriber_filter` no POST e no PUT, responde 200 e **descarta o campo em
silêncio** — volta `null`. Um broadcast criado pela v3 sai para a lista INTEIRA
(5.118 pessoas), não para a tag do projeto. A v4 grava e devolve o filtro; este
script confere a leitura depois de escrever e falha se não bater.

Uso:
    python divulgacao/broadcast_semanal.py --dry-run   # mostra o que enviaria
    python divulgacao/broadcast_semanal.py            # cria o rascunho no Kit
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
ROI = RAIZ.parent / "ROI_Diagnostico"
load_dotenv(ROI / ".env")
load_dotenv(RAIZ / ".env")

BASE = "https://api.kit.com/v4"
TAG_PROJETO = 23251247          # "Leads - Cartas Semanais" — só quem veio da landing
PDF = "https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf"
DIGESTS = RAIZ / "digests" / "resumo"

MESES = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def cabecalhos() -> dict[str, str]:
    """A v4 autentica por header. Bearer NÃO funciona — só `X-Kit-Api-Key`."""
    v = os.environ.get("CONVERT_KIT_V4")
    if not v:
        raise SystemExit(f"CONVERT_KIT_V4 ausente (procurei em {ROI})")
    return {"X-Kit-Api-Key": v, "Content-Type": "application/json"}


def alcance(headers: dict[str, str]) -> int | None:
    """Quantas pessoas a tag alcança hoje. None se a API não responder.

    A contagem vem da v3: o endpoint da v4 lista os assinantes com cursor, e a
    indexação atrasa alguns minutos depois de uma marcação nova.
    """
    segredo = os.environ.get("CONVERTKIT_API_SECRET")
    if not segredo:
        return None
    try:
        r = httpx.get(f"https://api.convertkit.com/v3/tags/{TAG_PROJETO}/subscriptions",
                      params={"api_secret": segredo, "per_page": 1}, timeout=60)
        return r.json().get("total_subscriptions") if r.status_code == 200 else None
    except httpx.HTTPError:
        return None


def edicao_mais_recente() -> tuple[str, list[str], str]:
    """Devolve (data, gestoras, conceito do exercício) da última edição."""
    qmds = sorted(DIGESTS.glob("resumo-*.qmd"), reverse=True)
    if not qmds:
        raise SystemExit(f"Nenhuma edição em {DIGESTS}")
    texto = qmds[0].read_text(encoding="utf-8")
    data = re.search(r"resumo-(\d{4}-\d{2}-\d{2})", qmds[0].name).group(1)

    gestoras, conceito = [], ""
    for m in re.finditer(r"(?m)^## (.+)$", texto):
        nome = m.group(1).strip()
        baixo = nome.lower()
        if baixo.startswith("exercício"):
            conceito = nome.split(":", 1)[-1].strip()
            continue
        if baixo in ("nesta edição", "convergências e divergências", "cartas originais"):
            continue
        gestoras.append(nome.split("—")[0].strip())
    return data, gestoras, conceito


def corpo(data: str, gestoras: list[str], conceito: str) -> str:
    a, m, d = data.split("-")
    quando = f"{int(d)} de {MESES[int(m)]}"
    lista = ", ".join(gestoras[:-1]) + f" e {gestoras[-1]}" if len(gestoras) > 1 else (gestoras[0] if gestoras else "")
    return f"""<p>Olá, {{{{ subscriber.first_name }}}}.</p>

<p>Saiu a síntese das cartas desta semana, com <strong>{lista}</strong>.</p>

<p>Como sempre: a tese de cada casa e o mecanismo que a sustenta, onde o consenso
se forma e onde racha — e o exercício em Python da semana{f", sobre <strong>{conceito}</strong>" if conceito else ""}.</p>

<p><a href="{PDF}">📄 Baixar a edição de {quando}</a></p>

<p>O código do exercício roda em segundos, com dado público. Você replica,
adapta e discorda — que é o ponto.</p>

<p>Boa leitura.</p>

<p>Vítor Wilher — Análise Macro</p>"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data, gestoras, conceito = edicao_mais_recente()
    a, m, d = data.split("-")
    assunto = f"Cartas das gestoras — edição de {int(d)} de {MESES[int(m)]}"
    html = corpo(data, gestoras, conceito)

    headers = cabecalhos()
    total = alcance(headers)

    print(f"Edição: {data}")
    print(f"Gestoras: {', '.join(gestoras)}")
    print(f"Exercício: {conceito or '(sem exercício)'}")
    print(f"Assunto: {assunto}")
    print(f"Tag: {TAG_PROJETO} (Leads - Cartas Semanais)"
          + (f" — {total} pessoa(s)" if total is not None else " — alcance não verificado"))

    if args.dry_run:
        print("\n--- corpo ---")
        print(html)
        print("\n[dry-run] Nada foi criado.", file=sys.stderr)
        return 0

    if not total:
        print("\n[erro] A tag do projeto está vazia. Um broadcast sem destinatário",
              file=sys.stderr)
        print("       não entrega nada — o único desfecho possível é erro.", file=sys.stderr)
        return 1

    # O filtro é o que separa "os leads deste projeto" de "a lista inteira".
    # Vai já na criação: um rascunho sem filtro nasce apontado para todo mundo,
    # e basta um clique errado no painel para ele sair assim.
    filtro = [{"all": [{"type": "tag", "ids": [TAG_PROJETO]}]}]

    r = httpx.post(f"{BASE}/broadcasts", timeout=90, headers=headers, json={
        "subject": assunto,
        "content": html,
        # public=False e send_at=None mantêm como RASCUNHO: nada sai sem revisão.
        "public": False,
        "send_at": None,
        "subscriber_filter": filtro,
    })
    if r.status_code not in (200, 201):
        print(f"[erro] HTTP {r.status_code}: {r.text[:300]}", file=sys.stderr)
        return 1
    b = r.json().get("broadcast", {})
    bid = b.get("id")

    # Reler é o que prova que gravou. A v3 respondia 200 e descartava o filtro;
    # confiar no status HTTP foi exatamente o que quase mandou e-mail para 5.118
    # pessoas. Um GET custa uma chamada e fecha essa porta.
    conferido = httpx.get(f"{BASE}/broadcasts/{bid}", timeout=60, headers=headers)
    gravado = conferido.json().get("broadcast", {}).get("subscriber_filter")
    if gravado != filtro:
        print(f"\n🔴 Rascunho {bid} criado, mas o SEGMENTO NÃO GRAVOU.", file=sys.stderr)
        print(f"   esperado: {filtro}", file=sys.stderr)
        print(f"   gravado:  {gravado}", file=sys.stderr)
        print("   NÃO ENVIE: defina o segmento no painel antes.", file=sys.stderr)
        return 1

    print(f"\nRascunho criado: id {bid}")
    print(f"Segmento confirmado na leitura: tag {TAG_PROJETO} — {total} destinatário(s).")
    print("\nRevise e envie em https://app.kit.com/campaigns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
