"""epub-prep.py — prepara os insumos do EPUB depois que o PDF já foi renderizado.
Chamado pelo render.ps1 entre o render do PDF e o do EPUB. Uso:

    python epub-prep.py <raiz-do-livro> <livro.pdf>

1) Capa: a página 1 do PDF (capa V1 montada pelo Typst) rasterizada em imagens/capa-epub.jpg.
2) Figuras SVG da marca -> PNG em imagens/_epub-png/<nome>.png, renderizadas pelo Typst
   (mesmas fontes embutidas do PDF). Leitores de EPUB/Kindle lidam mal com SVG e não têm a Inter.
O filtro am-livro.lua usa esses arquivos quando existem; sem eles, cai para a foto bruta e os SVGs.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pymupdf

raiz = pathlib.Path(sys.argv[1]).resolve()
pdf = pathlib.Path(sys.argv[2]).resolve()
imagens = raiz / "imagens"
fontes = raiz / "_extensions" / "analisemacro" / "am-livro" / "fonts"

# 1) capa
capa = imagens / "capa-epub.jpg"
page = pymupdf.open(pdf)[0]
zoom = 1600 / page.rect.width          # ~1600 px de largura (recomendação Kindle/Apple Books)
pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
pix.save(capa, jpg_quality=88)
print(f"capa do EPUB: {capa.name} ({pix.width}x{pix.height})")

# 2) SVG -> PNG via Typst (quarto typst compile)
quarto = shutil.which("quarto")
svgs = [p for p in sorted(imagens.glob("*.svg")) if not p.name.startswith("_")]
if svgs and quarto:
    out_dir = imagens / "_epub-png"
    out_dir.mkdir(exist_ok=True)
    for svg in svgs:
        rel = svg.relative_to(raiz).as_posix()
        typ = raiz / f"_epub-fig-{svg.stem}.typ"
        typ.write_text(
            f'#set page(width: auto, height: auto, margin: 0pt, fill: white)\n#image("{rel}")\n',
            encoding="utf-8",
        )
        png = out_dir / f"{svg.stem}.png"
        try:
            subprocess.run(
                [quarto, "typst", "compile", str(typ), str(png), "--root", str(raiz),
                 "--font-path", str(fontes), "--ppi", "192"],
                check=True, capture_output=True, text=True, cwd=raiz,
            )
            print(f"figura: {rel} -> {png.relative_to(raiz).as_posix()}")
        except subprocess.CalledProcessError as e:
            print(f"AVISO: {rel} ficou como SVG ({e.stderr.strip()[:200]})")
        finally:
            typ.unlink(missing_ok=True)
