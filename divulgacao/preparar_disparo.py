#!/usr/bin/env python3
"""Prepara o broadcast do ConvertKit — em RASCUNHO, nunca dispara.

Decisão do Vitor (2026-09-08): os sistemas de produção recebem preparação, não
execução. Este script cria o broadcast como rascunho e imprime o link para
revisão; o envio é feito por uma pessoa, na interface.

Uso:
    python divulgacao/preparar_disparo.py --conferir       # tag e tamanho
    python divulgacao/preparar_disparo.py --criar-rascunho # cria, não envia
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROI_ENV = Path(__file__).resolve().parents[2] / "ROI_Diagnostico" / ".env"
load_dotenv(ROI_ENV)
load_dotenv()

BASE = "https://api.convertkit.com/v3"
TAG_MERCADO_FINANCEIRO = 22406993  # conferido 2026-09-08: 530 assinantes
COPY = Path(__file__).resolve().parent / "email-lancamento.md"


def segredo() -> str:
    v = os.environ.get("CONVERTKIT_API_SECRET")
    if not v:
        raise SystemExit(f"CONVERTKIT_API_SECRET ausente (procurei em {ROI_ENV})")
    return v


def conferir() -> int:
    """Confirma que a tag existe e quantas pessoas alcançaria."""
    s = segredo()
    r = httpx.get(f"{BASE}/tags/{TAG_MERCADO_FINANCEIRO}/subscriptions",
                  params={"api_secret": s, "per_page": 1}, timeout=60)
    r.raise_for_status()
    total = r.json().get("total_subscriptions")
    print(f"Tag {TAG_MERCADO_FINANCEIRO} (Mercado Financeiro): {total} assinantes")

    r = httpx.get(f"{BASE}/subscribers", params={"api_secret": s}, timeout=60)
    r.raise_for_status()
    print(f"Base total da conta: {r.json().get('total_subscribers')}")
    return 0


def extrair_copy() -> tuple[str, str]:
    """Lê assunto e corpo do markdown, do bloco de citação (padrão da casa)."""
    if not COPY.exists():
        raise SystemExit(f"Copy não encontrada: {COPY}")
    texto = COPY.read_text(encoding="utf-8")

    m = re.search(r"## Assunto\s*\n+>\s*(.+)", texto)
    if not m:
        raise SystemExit("Não achei o assunto (linha '> ' após '## Assunto').")
    assunto = m.group(1).strip()

    corpo_bruto = texto.split("## Corpo", 1)[-1].split("## Notas de auditoria", 1)[0]
    linhas = [l[2:] if l.startswith("> ") else ("" if l.strip() == ">" else None)
              for l in corpo_bruto.splitlines()]
    corpo = "\n".join(l for l in linhas if l is not None).strip()
    if not corpo:
        raise SystemExit("Corpo vazio: o texto precisa estar em bloco de citação.")
    return assunto, corpo


def criar_rascunho() -> int:
    assunto, corpo = extrair_copy()
    print(f"Assunto: {assunto}")
    print(f"Corpo: {len(corpo)} caracteres\n")

    if "[Assinar as Cartas de Gestoras →]" in corpo:
        print("[BLOQUEADO] A copy ainda tem o placeholder do link de checkout.",
              file=sys.stderr)
        print("O produto precisa estar publicado no Woo e o carrinho testado ao vivo",
              file=sys.stderr)
        print("antes de criar o broadcast. Ver divulgacao/email-lancamento.md.",
              file=sys.stderr)
        return 1

    r = httpx.post(
        f"{BASE}/broadcasts",
        json={
            "api_secret": segredo(),
            "subject": assunto,
            "content": corpo.replace("\n\n", "</p><p>"),
            "public": False,          # rascunho: não publica
            "send_at": None,          # sem agendamento
        },
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print(f"[erro] HTTP {r.status_code}: {r.text[:400]}", file=sys.stderr)
        return 1
    b = r.json().get("broadcast", {})
    print(f"Rascunho criado: id={b.get('id')}")
    print("Revise e dispare manualmente em https://app.kit.com/campaigns")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conferir", action="store_true", help="confere a tag e o alcance")
    parser.add_argument("--criar-rascunho", action="store_true", help="cria o broadcast em rascunho")
    args = parser.parse_args()

    if args.conferir:
        return conferir()
    if args.criar_rascunho:
        return criar_rascunho()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
