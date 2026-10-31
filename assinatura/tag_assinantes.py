#!/usr/bin/env python3
"""Mantém no Kit a separação entre assinantes e leads da síntese.

Até 31/10/2026 os assinantes pagantes estavam na tag de leads e recebiam o mesmo
e-mail de terça que os leads — com o convite "assine por R$ 97" para o que já
tinham comprado, e sem o caminho para a edição completa no curso.

A v4 do Kit só aceita UM grupo de filtro por broadcast (`all`, `any` ou `none`; 422
"Only a single filter group is supported" ao combinar). Não dá para dizer "tag de
leads, menos os assinantes". Por isso a separação vive nas tags:

    assinatura ativa (ou pending-cancel)  -> TAG_ASSINANTES, sem TAG_LEADS
    deixou de ser assinante               -> TAG_LEADS de volta, sem TAG_ASSINANTES

Cada broadcast filtra uma tag só. Roda no workflow antes dos e-mails.

⚠️ A lista `GET /tags/<id>/subscribers` atrasa — inclusive mostra quem já saiu.
O estado de verdade é `GET /subscribers/<id>/tags`, por assinante (CLAUDE.md).

Uso:
    python assinatura/tag_assinantes.py --dry-run
    python assinatura/tag_assinantes.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values

RAIZ = Path(__file__).resolve().parents[1]
# Local: o .env do ROI_Diagnostico. Na CI as chaves chegam como secrets.
ENV = {**dotenv_values(RAIZ.parent / "ROI_Diagnostico" / ".env"),
       **{k: v for k, v in os.environ.items()
          if k.startswith(("WP_LOJA_", "WC_", "CONVERT_KIT_V4")) and v}}

PRODUTO = 73335                 # assinatura R$ 97/mês
TAG_LEADS = 23251247            # "Leads - Cartas Semanais"
TAG_ASSINANTES = 25233968       # "Assinantes - Cartas das Gestoras" (criada em 31/10/2026)
# pending-cancel mantém o acesso: a pessoa cancelou, mas o período pago ainda corre.
STATUS_COM_ACESSO = ("active", "pending-cancel")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0 Safari/537.36"}


def emails_assinantes() -> set[str]:
    loja = ENV["WP_LOJA_URL"].rstrip("/")
    chaves = {"consumer_key": ENV["WC_CONSUMER_KEY"], "consumer_secret": ENV["WC_CONSUMER_SECRET"]}
    emails, pagina = set(), 1
    while True:
        r = httpx.get(f"{loja}/wp-json/wc/v3/subscriptions", headers=UA, timeout=60,
                      params={**chaves, "product": PRODUTO, "per_page": 100, "page": pagina})
        r.raise_for_status()
        lote = r.json()
        emails |= {s["billing"]["email"].strip().lower() for s in lote
                   if s["status"] in STATUS_COM_ACESSO and s["billing"].get("email")}
        if len(lote) < 100:
            return emails
        pagina += 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    kit = httpx.Client(base_url="https://api.kit.com/v4", timeout=60,
                       headers={"X-Kit-Api-Key": ENV["CONVERT_KIT_V4"]})

    def achar(email: str) -> dict | None:
        r = kit.get("/subscribers", params={"email_address": email, "status": "all"}).json()
        return (r.get("subscribers") or [None])[0]

    def tags_de(sid: int) -> set[int]:
        return {t["id"] for t in kit.get(f"/subscribers/{sid}/tags").json()["tags"]}

    def acao(desc: str, fn) -> None:
        print(("  [dry-run] " if args.dry_run else "  ") + desc)
        if not args.dry_run:
            r = fn()
            if r.status_code >= 300:
                raise SystemExit(f"🔴 {desc}: HTTP {r.status_code} {r.text[:200]}")

    assinantes = emails_assinantes()
    print(f"Assinaturas com acesso no Woo: {len(assinantes)}")

    for email in sorted(assinantes):
        s = achar(email)
        if s is None:
            # Comprou com um e-mail que o Kit não conhece: cria, para receber a edição.
            acao(f"{email}: criar no Kit", lambda: kit.post("/subscribers", json={"email_address": email}))
            if args.dry_run:
                continue
            s = achar(email)
        tags = tags_de(s["id"]) if s else set()
        if TAG_ASSINANTES not in tags:
            acao(f"{email}: + tag de assinantes",
                 lambda: kit.post(f"/tags/{TAG_ASSINANTES}/subscribers", json={"email_address": email}))
        if TAG_LEADS in tags:
            acao(f"{email}: - tag de leads (para não receber o e-mail de venda)",
                 lambda: kit.delete(f"/tags/{TAG_LEADS}/subscribers/{s['id']}"))

    # Quem tem a tag de assinante mas não tem mais assinatura volta a ser lead. A
    # lista da tag pode trazer gente que já saiu (atraso do Kit), por isso cada
    # um é conferido no endpoint do próprio assinante antes de mexer.
    r = kit.get(f"/tags/{TAG_ASSINANTES}/subscribers", params={"per_page": 1000}).json()
    for s in r.get("subscribers", []):
        email = s["email_address"].strip().lower()
        if email in assinantes or TAG_ASSINANTES not in tags_de(s["id"]):
            continue
        acao(f"{email}: assinatura encerrada -> volta para a tag de leads",
             lambda: kit.post(f"/tags/{TAG_LEADS}/subscribers", json={"email_address": email}))
        acao(f"{email}: - tag de assinantes",
             lambda: kit.delete(f"/tags/{TAG_ASSINANTES}/subscribers/{s['id']}"))

    print("Sincronizado." if not args.dry_run else "[dry-run] Nada foi alterado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
