# Síntese das Cartas das Gestoras

Pipeline semanal que encontra novas cartas de 12 gestoras brasileiras, extrai o
conteúdo, compara teses e riscos com Claude, renderiza uma síntese em PDF e a
entrega pelo WhatsApp.

![Pipeline de engenharia](assets/linkedin/pipeline-engenharia-linkedin.png)

## O que há de engenharia aqui

- cinco estratégias de coleta (`wp_rest`, `rss`, `html`, `ajax` e URL previsível);
- estado incremental por gestora e por série, evitando reprocessar o histórico;
- suporte a cartas em PDF e HTML, com falhas isoladas por fonte;
- síntese comparativa via Anthropic Claude;
- PDF produzido com Quarto + XeLaTeX;
- entrega pela WhatsApp Cloud API com template `UTILITY` aprovado;
- execução semanal e persistência do estado via GitHub Actions;
- testes unitários para as regras de delta, séries e formatação.

## Fluxo

```text
GitHub Actions → 12 gestoras → detecção do delta → PDF/HTML
               → normalização → Claude → Quarto → WhatsApp
```

O diagrama editável está em
[`docs/pipeline-cartas.excalidraw`](docs/pipeline-cartas.excalidraw), acompanhado
de um [preview em SVG](docs/pipeline-cartas-preview.svg). Uma síntese real de
exemplo está em
[`digests/resumo/resumo-2026-08-11.pdf`](digests/resumo/resumo-2026-08-11.pdf).

## Executar localmente

Requisitos: Python 3.12+, Quarto e uma distribuição LaTeX com XeLaTeX.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python cartas.py --pdf
```

Para enviar o documento após renderizá-lo:

```bash
python cartas.py --pdf --send
```

As credenciais da Anthropic e da Meta ficam exclusivamente no `.env` local ou
nos GitHub Actions Secrets. Consulte `.env.example` para os nomes exigidos.

## Automação

O workflow [`.github/workflows/cartas.yml`](.github/workflows/cartas.yml) roda às
terças-feiras, 07:00 BRT, também aceita disparo manual e executa os testes antes
da coleta. Quando há cartas novas, commita a síntese e o novo marcador de estado.
Quando não há delta, não envia mensagem.

## Testes

```bash
python -m unittest discover -s tests -v
```

## Licença

Código distribuído sob a licença MIT. As cartas originais pertencem às
respectivas gestoras e não são redistribuídas neste repositório.
