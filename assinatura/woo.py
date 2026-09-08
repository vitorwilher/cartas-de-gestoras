#!/usr/bin/env python3
"""Prepara o produto de assinatura no WooCommerce — SEM publicar.

Os conectores do ../ROI_Diagnostico são somente leitura (alimentam o dashboard);
esta é a camada de escrita. Por decisão do Vitor (2026-09-08), NADA aqui publica
sozinho: o produto nasce como rascunho e a publicação é ação humana.

Uso:
    python assinatura/woo.py --verificar      # checa credenciais e plugin
    python assinatura/woo.py --dry-run        # mostra o payload, não envia
    python assinatura/woo.py --criar-rascunho # cria o produto em status=draft
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# As credenciais do Woo vivem no .env do ROI_Diagnostico, que já as usa.
ROI_ENV = Path(__file__).resolve().parents[2] / "ROI_Diagnostico" / ".env"
load_dotenv(ROI_ENV)
load_dotenv()  # um .env local, se houver, tem precedência

PRECO_MENSAL = "97.00"
SLUG = "cartas-de-gestoras"
NOME = "Cartas de Gestoras — assinatura mensal"

DESCRICAO_CURTA = (
    "Toda semana, a síntese técnica das cartas das 12 maiores gestoras do Brasil "
    "— com o exercício em Python que mostra como verificar cada tese."
)

DESCRICAO = """<p><strong>Você não paga para saber o que as gestoras disseram. Você paga
para aprender a destrinchar tecnicamente o que elas disseram.</strong></p>

<p>Toda terça, o pipeline lê as cartas novas das 12 maiores gestoras do Brasil
(Dynamo, IP, Alaska, Kapitalo, Adam, Legacy, Bahia, Occam, JGP, Kinea, NEO e
Dahlia) e entrega:</p>

<ul>
  <li><strong>A tese de cada gestora e o mecanismo por trás dela</strong> — não o
  resumo do mês, mas a cadeia causal que faz a aposta se pagar e a condição em que
  ela quebra.</li>
  <li><strong>Convergências e divergências</strong> — onde o consenso se forma,
  onde racha, e o que a divergência revela sobre premissas diferentes.</li>
  <li><strong>Um exercício em Python</strong> — código que roda, com dados
  públicos brasileiros, verificando o mecanismo da semana. É a prova de que dá
  para checar a tese em vez de acreditar nela.</li>
  <li><strong>Acesso via MCP</strong> — consulte o histórico direto do Claude Code
  ou do Codex, com as ferramentas do servidor da Análise Macro.</li>
  <li><strong>Entrega no WhatsApp</strong> — o PDF chega assim que sai.</li>
</ul>

<p>As cartas não são todas mensais: Dynamo e IP publicam ensaios temáticos
irregulares, e são justamente os de maior densidade. A cadência semanal existe
para não perder nenhum — quando não há carta nova, não há edição.</p>

<p><em>As cartas originais pertencem às respectivas gestoras. A assinatura dá
acesso à análise, sempre com o link para o documento original.</em></p>
"""


def credenciais() -> tuple[str, str, str]:
    url = os.environ.get("WC_URL")
    ck = os.environ.get("WC_CONSUMER_KEY")
    cs = os.environ.get("WC_CONSUMER_SECRET")
    faltando = [n for n, v in (("WC_URL", url), ("WC_CONSUMER_KEY", ck), ("WC_CONSUMER_SECRET", cs)) if not v]
    if faltando:
        raise SystemExit(f"Credenciais ausentes: {', '.join(faltando)} (procurei em {ROI_ENV})")
    return url.rstrip("/"), ck, cs


def api(caminho: str, params: dict | None = None) -> httpx.Response:
    """GET na REST API do Woo. Timeout de 60s, mesma escolha do resto do projeto."""
    url, ck, cs = credenciais()
    p = dict(params or {})
    p.update({"consumer_key": ck, "consumer_secret": cs})
    return httpx.get(f"{url}/wp-json/wc/v3/{caminho}", params=p, timeout=60)


def payload_produto(status: str = "draft") -> dict:
    """O produto de assinatura. `subscription` exige o WooCommerce Subscriptions."""
    return {
        "name": NOME,
        "slug": SLUG,
        "type": "subscription",
        "status": status,
        "catalog_visibility": "visible",
        "description": DESCRICAO,
        "short_description": DESCRICAO_CURTA,
        "regular_price": PRECO_MENSAL,
        "virtual": True,
        "downloadable": False,
        "meta_data": [
            {"key": "_subscription_price", "value": PRECO_MENSAL},
            {"key": "_subscription_period", "value": "month"},
            {"key": "_subscription_period_interval", "value": "1"},
            {"key": "_subscription_length", "value": "0"},        # sem fim
            {"key": "_subscription_sign_up_fee", "value": "0"},
            {"key": "_subscription_trial_length", "value": "0"},
        ],
    }


def verificar() -> int:
    """Confere credenciais e se o WooCommerce Subscriptions está instalado."""
    url, _, _ = credenciais()
    print(f"Loja: {url}")

    r = api("system_status")
    if r.status_code != 200:
        print(f"[erro] system_status devolveu HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
        return 1

    dados = r.json()
    ativos = dados.get("active_plugins", [])
    nomes = [p.get("name", "") for p in ativos]
    subs = [n for n in nomes if "subscription" in n.lower()]
    print(f"Plugins ativos: {len(nomes)}")
    if subs:
        print(f"  Subscriptions: {', '.join(subs)}")
    else:
        print("  [ATENÇÃO] Nenhum plugin de Subscriptions encontrado.", file=sys.stderr)
        print("  O produto type='subscription' será REJEITADO sem ele.", file=sys.stderr)

    # O slug já existe? Evita criar produto duplicado.
    r = api("products", {"slug": SLUG})
    if r.status_code == 200 and r.json():
        for p in r.json():
            print(f"  [já existe] id={p['id']} status={p['status']} — {p['name']}")
    else:
        print(f"  Slug '{SLUG}' está livre.")
    return 0 if subs else 2


def criar_rascunho(dry_run: bool) -> int:
    corpo = payload_produto("draft")
    if dry_run:
        print(json.dumps(corpo, ensure_ascii=False, indent=2))
        print("\n[dry-run] Nada foi enviado.", file=sys.stderr)
        return 0

    r = api("products", {"slug": SLUG})
    if r.status_code == 200 and r.json():
        print(f"[erro] já existe produto com slug '{SLUG}'. Nada foi criado.", file=sys.stderr)
        return 1

    url, ck, cs = credenciais()
    resp = httpx.post(
        f"{url}/wp-json/wc/v3/products",
        params={"consumer_key": ck, "consumer_secret": cs},
        json=corpo,
        timeout=60,
    )
    if resp.status_code not in (200, 201):
        print(f"[erro] HTTP {resp.status_code}: {resp.text[:400]}", file=sys.stderr)
        return 1
    p = resp.json()
    print(f"Rascunho criado: id={p['id']} status={p['status']}")
    print(f"Revise e publique em: {url}/wp-admin/post.php?post={p['id']}&action=edit")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true", help="checa credenciais e plugin")
    parser.add_argument("--dry-run", action="store_true", help="mostra o payload sem enviar")
    parser.add_argument("--criar-rascunho", action="store_true", help="cria o produto em status=draft")
    args = parser.parse_args()

    if args.verificar:
        return verificar()
    if args.criar_rascunho or args.dry_run:
        return criar_rascunho(dry_run=args.dry_run and not args.criar_rascunho)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
