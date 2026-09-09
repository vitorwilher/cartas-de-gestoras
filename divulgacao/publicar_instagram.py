#!/usr/bin/env python3
"""Publica o carrossel da edição no Instagram.

Reaproveita a infra do ../ROI_Diagnostico: `assets_gcs` sobe os PNGs para o
bucket público (o Graph API baixa as imagens de forma ANÔNIMA, por isso elas
precisam de URL pública) e `InstagramConnector.publish_carousel` faz o fluxo de
containers da Graph API.

⚠️ Este script PUBLICA DE VERDADE. Diferente do resto de `divulgacao/`, que
prepara rascunhos, aqui o post vai ao ar. Por isso o padrão é `--dry-run`: sem
`--publicar`, ele sobe as imagens e mostra a legenda, mas não posta.

A legenda sai de `carrossel-instagram.md` (bloco "## Legenda do post"), para não
haver duas versões do texto — a do arquivo e a do código.

Uso:
    python divulgacao/publicar_instagram.py              # sobe e mostra
    python divulgacao/publicar_instagram.py --publicar   # publica no feed
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
ROI = RAIZ.parent / "ROI_Diagnostico"
load_dotenv(ROI / ".env")
load_dotenv(RAIZ / ".env")

sys.path.insert(0, str(ROI))

BUCKET = os.getenv("SOCIAL_GCS_BUCKET", "am-social-assets")
CREDS = os.getenv("GCS_CREDENTIALS_PATH", "ga4_credentials.json")

SLIDES = RAIZ / "divulgacao" / "carrossel"
FONTE_LEGENDA = RAIZ / "divulgacao" / "carrossel-instagram.md"


def legenda() -> str:
    """Extrai a legenda do markdown — a fonte única do texto.

    O bloco está em citação (linhas com "> ") sob "## Legenda do post".
    Mantê-la lá evita a divergência clássica: alguém edita o .md, e o post sai
    com o texto antigo que estava embutido no script.
    """
    texto = FONTE_LEGENDA.read_text(encoding="utf-8")
    m = re.search(r"## Legenda do post\n(.*?)(?=\n## )", texto, re.S)
    if not m:
        raise SystemExit(f"Bloco '## Legenda do post' não achado em {FONTE_LEGENDA}")
    linhas = [re.sub(r"^> ?", "", l) for l in m.group(1).strip().splitlines()]
    return "\n".join(linhas).strip()


def subir(arquivos: list[Path], prefixo: str) -> list[str]:
    """Sobe os PNGs ao bucket público e devolve as URLs.

    Não reusa `social/assets_gcs.py` do ROI porque lá o caminho da credencial é
    relativo ao diretório daquele projeto — rodando daqui, o gcsfs não a acha.
    Mesma resolução que `publicar_pdf.py` já faz.
    """
    import gcsfs

    caminho = CREDS if os.path.isabs(CREDS) else str(ROI / CREDS)
    if not os.path.exists(caminho):
        raise SystemExit(
            f"Credenciais do GCS não encontradas em {caminho}. "
            "Confira GCS_CREDENTIALS_PATH no .env do ROI_Diagnostico.")

    fs = gcsfs.GCSFileSystem(token=caminho)
    urls = []
    for arq in arquivos:
        chave = f"{BUCKET}/{prefixo}/{arq.name}"
        with fs.open(chave, "wb", content_type="image/png") as destino:
            destino.write(arq.read_bytes())
        urls.append(f"https://storage.googleapis.com/{BUCKET}/{prefixo}/{arq.name}")
    return urls


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--publicar", action="store_true",
                    help="publica no feed (sem isso, só sobe as imagens e mostra)")
    args = ap.parse_args()

    pngs = sorted(SLIDES.glob("slide-*.png"))
    if not 2 <= len(pngs) <= 10:
        raise SystemExit(f"O carrossel exige de 2 a 10 imagens; achei {len(pngs)}")

    cap = legenda()
    print(f"Slides: {len(pngs)} ({pngs[0].name} … {pngs[-1].name})")
    print(f"Legenda: {len(cap)} caracteres")
    if len(cap) > 2200:
        raise SystemExit(f"Legenda tem {len(cap)} caracteres; o limite do IG é 2.200")

    prefixo = f"cartas/carrossel/{date.today():%Y-%m-%d}"
    urls = subir(pngs, prefixo)
    print(f"\nImagens no GCS ({prefixo}):")
    for u in urls:
        print("  ", u)

    if not args.publicar:
        print("\n--- legenda ---")
        print(cap)
        print("\n[dry-run] Nada foi publicado. Use --publicar para postar.",
              file=sys.stderr)
        return 0

    from connectors.instagram import InstagramConnector  # noqa: E402

    ig = InstagramConnector(os.environ["IG_ACCESS_TOKEN"], os.environ["IG_USER_ID"])
    res = ig.publish_carousel(urls, cap)
    print(f"\nPublicado: {res.get('permalink') or res.get('id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
