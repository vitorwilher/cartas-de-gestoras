#!/usr/bin/env python3
"""Monta a assinatura na loja: curso LearnDash + produto de assinatura, ligados.

Mesmo molde do workshop (curso 73259 <-> produto 73260, em
../ROI_Diagnostico/cursos/imersoes/engenharia-ia-gestores-recursos/landing/):

    produto  --_related_course-->  curso   (a assinatura ativa libera o acesso)
    curso    --price_type closed + botão-->  carrinho/?add-to-cart=<produto>

Cada edição em digests/resumo/*.pdf vira uma aula com o PDF em "Materiais".
Tudo nasce em RASCUNHO; publicar é decisão do Vitor (`--publicar`).

Idempotente: curso, produto, mídias e aulas são procurados pelo slug antes de
criar. Rodar de novo só acrescenta as edições que faltam.

Uso:
    python assinatura/curso.py              # cria/atualiza em rascunho
    python assinatura/curso.py --publicar   # publica curso, aulas e produto
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).resolve().parent))
import woo  # noqa: E402  (copy e payload da assinatura)

RAIZ = Path(__file__).resolve().parents[1]
ENV = dotenv_values(RAIZ.parent / "ROI_Diagnostico" / ".env")
LOJA = ENV["WP_LOJA_URL"].rstrip("/")
WP_AUTH = (ENV["WP_LOJA_USER"], ENV["WP_LOJA_APP_PASSWORD"])
WC = {"consumer_key": ENV["WC_CONSUMER_KEY"], "consumer_secret": ENV["WC_CONSUMER_SECRET"]}
# Sem User-Agent de navegador o WAF responde 403 (ver CLAUDE.md, Code Snippets).
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0 Safari/537.36"}
# O Download Monitor ignora a senha de aplicação: só aceita a chave dele (gerada no
# painel, Downloads -> Configurações -> API). É o que serve o PDF em /download/<id>.
DLM = {"X-DLM-API-KEY": ENV.get("DLM_API_PUBLIC_KEY") or "",
       "X-DLM-API-SECRET": ENV.get("DLM_API_SECRET_KEY") or ""}

NOME_CURSO = "Síntese das Cartas das Gestoras"
SLUG = woo.SLUG
CAPA = RAIZ / "assinatura" / "capa" / "produto-sintese-cartas.png"
EDICOES = RAIZ / "digests" / "resumo"
CAT_CURSO = 3340     # "Especiais", a mesma do workshop
CAT_PRODUTO = 1696   # "Cursos Livres"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _ok(r: httpx.Response, o_que: str) -> dict | list:
    if r.status_code not in (200, 201):
        sys.exit(f"[erro] {o_que}: HTTP {r.status_code} {r.text[:300]}")
    return r.json()


def _wp(c: httpx.Client, metodo: str, caminho: str, **kw) -> httpx.Response:
    return c.request(metodo, f"{LOJA}/wp-json/{caminho}", auth=WP_AUTH, headers={**UA, **kw.pop("headers", {})}, **kw)


def subir_midia(c: httpx.Client, arquivo: Path, tipo: str) -> dict:
    """Envia à biblioteca de mídia, reaproveitando se o slug já existir."""
    slug = re.sub(r"[^a-z0-9-]", "-", arquivo.stem.lower())
    achado = _ok(_wp(c, "GET", "wp/v2/media", params={"slug": slug}), f"busca da mídia {slug}")
    if achado:
        return achado[0]
    return _ok(_wp(c, "POST", "wp/v2/media", content=arquivo.read_bytes(),
                   headers={"Content-Type": tipo,
                            "Content-Disposition": f'attachment; filename="{arquivo.name}"'}),
               f"upload de {arquivo.name}")


def garantir_download(c: httpx.Client, titulo: str, url_arquivo: str) -> int:
    """O PDF atrás de /download/<id>, só para quem está logado (`_members_only`).

    Procura pelo título antes de criar: rodar de novo não duplica o download.
    """
    achado = _ok(_wp(c, "GET", "wp/v2/dlm_download", params={"search": titulo, "status": "any"}),
                 f"busca do download {titulo}")
    for d in achado:
        if html.unescape(d["title"]["rendered"]) == titulo:
            return d["id"]
    novo = _ok(c.post(f"{LOJA}/wp-json/download-monitor/v1/download", headers={**UA, **DLM},
                      json={"title": titulo, "status": "publish", "_members_only": "yes",
                            # Fora de dlm_uploads o plugin não serve o arquivo (devolve HTML);
                            # a REST não consegue gravar lá, então ele só confere o login e redireciona.
                            "_redirect_only": "yes"}),
               f"criação do download {titulo}")
    _ok(c.post(f"{LOJA}/wp-json/download-monitor/v1/version", headers={**UA, **DLM},
               json={"download_id": novo["download_id"], "version": "1", "url": url_arquivo}),
        f"versão do download {titulo}")
    return novo["download_id"]


def titulo_edicao(qmd: Path, data: str) -> str:
    """'Edição de 29 de setembro de 2026 — Bridgewater, GMO', a partir do .qmd."""
    a, m, d = (int(x) for x in data.split("-"))
    titulo = f"Edição de {d} de {MESES[m - 1]} de {a}"
    sub = re.search(r'^subtitle:\s*"[^"]*—\s*(.+?)"', qmd.read_text(encoding="utf-8"), re.M) if qmd.exists() else None
    return f"{titulo} — {sub.group(1)}" if sub else titulo


def garantir_curso(c: httpx.Client, url_carrinho: str | None, capa_id: int) -> dict:
    achado = _ok(_wp(c, "GET", "ldlms/v2/sfwd-courses", params={"slug": SLUG, "status": "any", "context": "edit"}),
                 "busca do curso")
    corpo = {"title": NOME_CURSO, "slug": SLUG, "content": woo.DESCRICAO, "price_type": "closed",
             "ld_course_category": [CAT_CURSO], "featured_media": capa_id}
    if url_carrinho:
        corpo["price_type_closed_custom_button_url"] = url_carrinho
    if achado:
        return _ok(_wp(c, "POST", f"ldlms/v2/sfwd-courses/{achado[0]['id']}", json=corpo), "atualização do curso")
    return _ok(_wp(c, "POST", "ldlms/v2/sfwd-courses", json={**corpo, "status": "draft"}), "criação do curso")


def garantir_produto(c: httpx.Client, curso_id: int, capa_id: int) -> dict:
    achado = _ok(c.get(f"{LOJA}/wp-json/wc/v3/products", params={**WC, "slug": SLUG, "status": "any"}),
                 "busca do produto")
    corpo = woo.payload_produto("draft")
    corpo["categories"] = [{"id": CAT_PRODUTO}]
    corpo["images"] = [{"id": capa_id}]
    corpo["meta_data"].append({"key": "_related_course", "value": [curso_id]})
    if achado:
        corpo.pop("status")
        return _ok(c.put(f"{LOJA}/wp-json/wc/v3/products/{achado[0]['id']}", params=WC, json=corpo),
                   "atualização do produto")
    return _ok(c.post(f"{LOJA}/wp-json/wc/v3/products", params=WC, json=corpo), "criação do produto")


def garantir_aulas(c: httpx.Client, curso_id: int) -> list[int]:
    """Uma aula por edição, da mais recente para a mais antiga."""
    pdfs = sorted(EDICOES.glob("resumo-*.pdf"), reverse=True)
    ids = []
    for ordem, pdf in enumerate(pdfs, start=1):
        data = pdf.stem.removeprefix("resumo-")
        slug = f"cartas-edicao-{data}"
        midia = subir_midia(c, pdf, "application/pdf")
        dl = garantir_download(c, f"Síntese das Cartas das Gestoras — {data}", midia["source_url"])
        # dlm-no-xhr-download: sem ela o script do plugin baixa por XHR, recebe o
        # redirect num cabeçalho e salva o corpo vazio como "download.html".
        materiais = (f'<a class="dlm-no-xhr-download" href="{LOJA}/download/{dl}/" target="_blank" rel="noopener">'
                     f"Baixar o PDF da edição</a>")
        corpo = {"title": titulo_edicao(pdf.with_suffix(".qmd"), data), "slug": slug, "course": curso_id,
                 "menu_order": ordem, "materials_enabled": True, "materials": materiais}
        achado = _ok(_wp(c, "GET", "ldlms/v2/sfwd-lessons", params={"slug": slug, "status": "any", "context": "edit"}),
                     f"busca da aula {slug}")
        if achado:
            aula = _ok(_wp(c, "POST", f"ldlms/v2/sfwd-lessons/{achado[0]['id']}", json=corpo), f"aula {slug}")
        else:
            aula = _ok(_wp(c, "POST", "ldlms/v2/sfwd-lessons", json={**corpo, "status": "draft"}), f"aula {slug}")
        print(f"  aula {aula['id']}: {corpo['title']}")
        ids.append(aula["id"])
    return ids


def publicar(c: httpx.Client, curso_id: int, produto_id: int, aulas: list[int]) -> None:
    for a in aulas:
        _ok(_wp(c, "POST", f"ldlms/v2/sfwd-lessons/{a}", json={"status": "publish"}), f"publicação da aula {a}")
    _ok(_wp(c, "POST", f"ldlms/v2/sfwd-courses/{curso_id}", json={"status": "publish"}), "publicação do curso")
    _ok(c.put(f"{LOJA}/wp-json/wc/v3/products/{produto_id}", params=WC, json={"status": "publish"}),
        "publicação do produto")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--publicar", action="store_true", help="publica curso, aulas e produto")
    args = ap.parse_args()

    with httpx.Client(timeout=120) as c:
        capa = subir_midia(c, CAPA, "image/png")
        curso = garantir_curso(c, None, capa["id"])
        produto = garantir_produto(c, curso["id"], capa["id"])
        carrinho = f"{LOJA}/carrinho/?add-to-cart={produto['id']}"
        curso = garantir_curso(c, carrinho, capa["id"])
        print(f"Curso {curso['id']} ({curso['status']}) · produto {produto['id']} ({produto['status']})")

        aulas = garantir_aulas(c, curso["id"])
        if args.publicar:
            publicar(c, curso["id"], produto["id"], aulas)

        # Releitura: o 200 da escrita não prova efeito.
        p = _ok(c.get(f"{LOJA}/wp-json/wc/v3/products/{produto['id']}", params=WC), "releitura do produto")
        k = _ok(_wp(c, "GET", f"ldlms/v2/sfwd-courses/{curso['id']}", params={"context": "edit"}), "releitura do curso")
        passos = _ok(_wp(c, "GET", f"ldlms/v2/sfwd-courses/{curso['id']}/steps"), "passos do curso")
        meta = {m["key"]: m["value"] for m in p["meta_data"]}
        print(f"  produto: {p['status']} · tipo {p['type']} · R$ {meta.get('_subscription_price')}"
              f"/{meta.get('_subscription_period')} · _related_course={meta.get('_related_course')}")
        print(f"  curso:   {k['status']} · botão={k['price_type_closed_custom_button_url']}")
        print(f"  aulas no curso: {len(passos.get('h', {}).get('sfwd-lessons', {}) or [])} de {len(aulas)}")
        print(f"\nEditar curso:   {LOJA}/wp-admin/post.php?post={curso['id']}&action=edit")
        print(f"Editar produto: {LOJA}/wp-admin/post.php?post={produto['id']}&action=edit")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
