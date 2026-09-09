#!/usr/bin/env python3
"""Publica o PDF da edição no GCS, numa URL FIXA que nunca muda.

O fluxo do ManyChat e a landing do ConvertKit apontam sempre para o mesmo
endereço; o pipeline sobrescreve o arquivo toda terça. Assim o material da
semana chega sem ninguém trocar link em painel nenhum.

Além do arquivo fixo, guardamos uma cópia datada — quem recebeu o link numa
semana continua conseguindo abrir aquela edição depois, e é o que permite
auditar o que foi entregue.

Uso:
    python divulgacao/publicar_pdf.py --dry-run   # mostra o que faria
    python divulgacao/publicar_pdf.py             # publica a edição mais recente
"""

from __future__ import annotations

import argparse
import mimetypes
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
ROI = RAIZ.parent / "ROI_Diagnostico"
DIGESTS = RAIZ / "digests" / "resumo"

load_dotenv(ROI / ".env")
load_dotenv(RAIZ / ".env")

BUCKET = os.getenv("SOCIAL_GCS_BUCKET", "am-social-assets")
CREDS = os.getenv("GCS_CREDENTIALS_PATH", "ga4_credentials.json")
BASE = f"https://storage.googleapis.com/{BUCKET}"

# A URL que vai no ManyChat e na landing. NUNCA muda.
CHAVE_FIXA = "cartas/edicao-atual.pdf"
URL_FIXA = f"{BASE}/{CHAVE_FIXA}"


def edicao_mais_recente() -> Path:
    pdfs = sorted(DIGESTS.glob("resumo-*.pdf"), reverse=True)
    if not pdfs:
        raise SystemExit(f"Nenhum PDF em {DIGESTS}")
    return pdfs[0]


def _fs():
    import gcsfs
    caminho = CREDS if os.path.isabs(CREDS) else str(ROI / CREDS)
    if not os.path.exists(caminho):
        raise SystemExit(
            f"Credenciais do GCS não encontradas em {caminho}. "
            "Confira GCS_CREDENTIALS_PATH no .env do ROI_Diagnostico."
        )
    return gcsfs.GCSFileSystem(token=caminho)


def publicar(local: Path, chave: str) -> str:
    """Sobe o arquivo e devolve a URL pública."""
    chave = chave.lstrip("/")
    ctype = mimetypes.guess_type(str(local))[0] or "application/pdf"
    fs = _fs()
    with open(local, "rb") as src, fs.open(f"{BUCKET}/{chave}", "wb",
                                           content_type=ctype) as dst:
        dst.write(src.read())
    return f"{BASE}/{chave}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="não envia nada")
    parser.add_argument("--pdf", help="caminho de um PDF específico")
    args = parser.parse_args()

    pdf = Path(args.pdf) if args.pdf else edicao_mais_recente()
    if not pdf.exists():
        raise SystemExit(f"PDF não encontrado: {pdf}")

    # resumo-2026-09-09.pdf -> 2026-09-09
    data = pdf.stem.replace("resumo-", "")
    chave_datada = f"cartas/{data}.pdf"

    print(f"PDF: {pdf.name} ({pdf.stat().st_size // 1024} KB)")
    print(f"  fixo:   {URL_FIXA}")
    print(f"  datado: {BASE}/{chave_datada}")

    if args.dry_run:
        print("\n[dry-run] Nada foi enviado.", file=sys.stderr)
        return 0

    publicar(pdf, chave_datada)
    publicar(pdf, CHAVE_FIXA)
    print("\nPublicado. O link do ManyChat e da landing não mudam.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
