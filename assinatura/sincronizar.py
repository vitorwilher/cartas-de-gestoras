#!/usr/bin/env python3
"""Sincroniza as assinaturas ativas do WooCommerce com o KV que o MCP consulta.

O MCP (mcp/src/index.ts) autoriza cada chamada consultando a chave `token:<token>`
no KV `ASSINANTES`. Este script é quem mantém esse KV em dia.

Duas formas de rodar:
  - Periodicamente (cron), reconciliando o estado inteiro. É o modo desta versão:
    não depende de o webhook do Woo chegar, e corrige divergências sozinho.
  - Sob demanda, após uma mudança conhecida.

O token de cada assinante é derivado por HMAC do id da assinatura, com um segredo
(`ASSINANTES_HMAC_SECRET`). Assim o token é reproduzível sem guardar tabela de
correspondência, e revogável trocando o segredo.

Uso:
    python assinatura/sincronizar.py --listar          # mostra assinaturas ativas
    python assinatura/sincronizar.py --gerar-comandos  # emite os wrangler kv put
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROI_ENV = Path(__file__).resolve().parents[2] / "ROI_Diagnostico" / ".env"
load_dotenv(ROI_ENV)
load_dotenv()

SLUG = "cartas-de-gestoras"
# Status do Woo Subscriptions que dão direito de acesso. `pending-cancel` entra:
# a pessoa cancelou mas o período pago ainda corre.
STATUS_COM_ACESSO = {"active", "pending-cancel"}


def credenciais() -> tuple[str, str, str]:
    url = os.environ.get("WC_URL")
    ck = os.environ.get("WC_CONSUMER_KEY")
    cs = os.environ.get("WC_CONSUMER_SECRET")
    if not (url and ck and cs):
        raise SystemExit(f"Credenciais do WooCommerce ausentes (procurei em {ROI_ENV})")
    return url.rstrip("/"), ck, cs


def token_do_assinante(subscription_id: int) -> str:
    """Token reproduzível e revogável, derivado por HMAC do id da assinatura."""
    segredo = os.environ.get("ASSINANTES_HMAC_SECRET")
    if not segredo:
        raise SystemExit(
            "ASSINANTES_HMAC_SECRET não definido. Gere um com:\n"
            "  python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
            "e guarde no .env local e nos secrets do GitHub Actions."
        )
    assinatura = hmac.new(segredo.encode(), str(subscription_id).encode(), hashlib.sha256)
    return assinatura.hexdigest()[:32]


def assinaturas_ativas() -> list[dict]:
    """Busca as assinaturas do produto, já filtradas pelos status com acesso."""
    url, ck, cs = credenciais()
    encontradas: list[dict] = []
    pagina = 1
    while True:
        r = httpx.get(
            f"{url}/wp-json/wc/v3/subscriptions",
            params={"consumer_key": ck, "consumer_secret": cs,
                    "per_page": 100, "page": pagina},
            timeout=60,
        )
        if r.status_code == 404:
            raise SystemExit(
                "Endpoint /subscriptions não existe. O WooCommerce Subscriptions "
                "expõe a REST API só a partir da v2.1 do plugin — confira a versão."
            )
        r.raise_for_status()
        lote = r.json()
        if not lote:
            break
        encontradas.extend(lote)
        pagina += 1

    relevantes = []
    for s in encontradas:
        if s.get("status") not in STATUS_COM_ACESSO:
            continue
        itens = s.get("line_items", [])
        # O produto é identificado pelo slug; o id só se conhece após criá-lo.
        if any(SLUG in (i.get("sku") or "") or SLUG in (i.get("name") or "").lower()
               for i in itens):
            relevantes.append(s)
    return relevantes


def registro(s: dict) -> dict:
    """O valor gravado no KV. Guarda STATUS, não dado pessoal."""
    return {
        "ativo": True,
        "plano": "mensal",
        "expira_em": s.get("next_payment_date_gmt") or "",
        "subscription_id": s.get("id"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listar", action="store_true", help="lista as assinaturas ativas")
    parser.add_argument("--gerar-comandos", action="store_true",
                        help="emite os comandos wrangler kv put (não executa)")
    args = parser.parse_args()

    ativas = assinaturas_ativas()
    if args.listar:
        print(f"{len(ativas)} assinatura(s) com acesso ({', '.join(sorted(STATUS_COM_ACESSO))}):")
        for s in ativas:
            print(f"  #{s['id']} — {s.get('status')} — próximo pagamento: {s.get('next_payment_date_gmt') or '?'}")
        return 0

    if args.gerar_comandos:
        if not ativas:
            print("Nenhuma assinatura ativa; nada a sincronizar.", file=sys.stderr)
            return 0
        print("# Rode a partir de mcp/ — revise antes de executar.")
        for s in ativas:
            token = token_do_assinante(s["id"])
            valor = json.dumps(registro(s), ensure_ascii=False)
            print(f"npx wrangler kv key put --binding=ASSINANTES 'token:{token}' '{valor}' --remote")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
