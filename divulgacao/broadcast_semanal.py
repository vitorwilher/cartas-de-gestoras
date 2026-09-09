#!/usr/bin/env python3
"""Cria o broadcast da edição da semana no ConvertKit, para a tag do projeto.

É assim que o assinante recebe a síntese toda terça — o que a página de obrigado
promete. O WhatsApp entrega só para quem escreveu (janela de 24h); o e-mail
alcança todos, sem template, sem custo por conversa e sem risco de qualidade.

Por decisão do Vitor (2026-09-09), o broadcast NASCE COMO RASCUNHO. Nada é
enviado sem revisão — a regra "preparar, nunca disparar" continua valendo para
comunicação em massa.

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

BASE = "https://api.convertkit.com/v3"
TAG_PROJETO = 23251247          # "Leads - Cartas Semanais" — só quem veio da landing
PDF = "https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf"
DIGESTS = RAIZ / "digests" / "resumo"

MESES = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def segredo() -> str:
    v = os.environ.get("CONVERTKIT_API_SECRET")
    if not v:
        raise SystemExit(f"CONVERTKIT_API_SECRET ausente (procurei em {ROI})")
    return v


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

    print(f"Edição: {data}")
    print(f"Gestoras: {', '.join(gestoras)}")
    print(f"Exercício: {conceito or '(sem exercício)'}")
    print(f"Assunto: {assunto}")
    print(f"Tag: {TAG_PROJETO} (Leads - Cartas Semanais)")

    if args.dry_run:
        print("\n--- corpo ---")
        print(html)
        print("\n[dry-run] Nada foi criado.", file=sys.stderr)
        return 0

    r = httpx.post(f"{BASE}/broadcasts", timeout=90, json={
        "api_secret": segredo(),
        "subject": assunto,
        "content": html,
        # public=False mantém como RASCUNHO: nada sai sem revisão humana.
        "public": False,
        "send_at": None,
        "email_layout_template": None,
        # ⚠️ A v3 IGNORA subscriber_filter na criação — testei: volta null. Sem
        #    filtro, o broadcast vai para a lista INTEIRA (5.118), não para a
        #    tag do projeto. Por isso o segmento é definido no painel, e o
        #    script deixa o aviso no próprio assunto até que se confirme.
    })
    if r.status_code not in (200, 201):
        print(f"[erro] HTTP {r.status_code}: {r.text[:300]}", file=sys.stderr)
        return 1
    b = r.json().get("broadcast", {})
    print(f"\nRascunho criado: id {b.get('id')}")
    print()
    print("🔴 ANTES DE ENVIAR, defina o segmento no painel:")
    print(f"   Broadcasts -> este rascunho -> Send to -> tag 'Leads - Cartas Semanais' ({TAG_PROJETO})")
    print("   A API v3 NÃO grava o subscriber_filter (testado: volta null).")
    print("   Sem esse passo, o e-mail vai para a lista INTEIRA.")
    print()
    print("Revise e envie em https://app.kit.com/campaigns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
