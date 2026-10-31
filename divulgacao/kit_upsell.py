#!/usr/bin/env python3
"""E-mails de upsell da sequência 2888305 (leads -> assinatura), em rascunho no Kit.

Pedido do Vitor em 31/10/2026: depois do boas-vindas, a sequência dos leads ganha
e-mails que incentivam a assinatura. Cada um tem UM ângulo, apoiado num caso real
de uma edição publicada (números conferidos na edição de origem), e termina no
mesmo link do carrinho.

Fatos da oferta, lidos no Woo em 31/10 (produto 73335): R$ 97,00 por mês, sem taxa
de adesão, sem período de teste, sem prazo final. NÃO há texto de garantia nem de
cancelamento no produto ou na landing — por isso nenhum e-mail promete uma coisa
nem outra até o Vitor confirmar (regra 3 da copy da casa: ressalva não se inventa).

Sem urgência: não existe data real de campanha, e escassez inventada é a regra 1.

⚠️ Ordem na sequência: rascunho na frente do publicado TRAVA a fila inteira
(kit-boas-vindas.md). Este script cria os e-mails DESPUBLICADOS no fim da
sequência; `--publicar` move os rascunhos antigos para o fim, põe estes logo
depois do boas-vindas, na ordem, e publica.

⚠️ Só quem ENTRA na sequência depois da publicação recebe. Quem já terminou o
boas-vindas (hold: false) não volta a receber.

Uso:
    python divulgacao/kit_upsell.py --dry-run     # mostra os textos
    python divulgacao/kit_upsell.py               # cria/atualiza os rascunhos no Kit
    python divulgacao/kit_upsell.py --publicar    # reordena e publica (só com ok do Vitor)
    python divulgacao/kit_upsell.py --campanha    # os mesmos textos como broadcasts agendados
                                                  # para os leads que JÁ terminaram a sequência

A campanha (pedido do Vitor em 31/10/2026): os 81 leads de setembro e outubro já
tinham saído da sequência e não receberiam nada. Recolocá-los nela repetiria o
"obrigado pelo cadastro". Então os quatro textos vão como broadcasts AGENDADOS
(canceláveis no painel até a hora) para a tag de leads — os assinantes já saíram
dela (assinatura/tag_assinantes.py). Fora das terças, que têm o e-mail da edição.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values

RAIZ = Path(__file__).resolve().parent.parent
ENV = dotenv_values(RAIZ.parent / "ROI_Diagnostico" / ".env")
SEQ = 2888305
BOAS_VINDAS = 10516834
RASCUNHOS_ANTIGOS = (10409446, 10288509, 10516933)  # 10516933: versão com o caso Kinea/IMAB11
TAG_LEADS = 23251247
AMOSTRA = ("https://analisemacro.com.br/wp-content/uploads/2026/10/"
           "sintese-cartas-gestoras-amostra-2026-10-13.pdf")
# 10h de Brasília; nenhuma terça (é o dia do e-mail da edição).
CAMPANHA = ["2026-11-05T13:00:00Z", "2026-11-09T13:00:00Z",
            "2026-11-12T13:00:00Z", "2026-11-19T13:00:00Z"]
ASSINAR = "https://aluno.analisemacro.com.br/carrinho/?add-to-cart=73335"
DIAS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

OFERTA = ("A assinatura custa R$ 97 por mês, sem taxa de adesão. Você recebe a edição "
          "completa de cada semana em que alguma gestora publica, com o exercício, e "
          "todas as edições desde agosto ficam na sua área do aluno.")
PS = ("P.S.: se você já assinou, obrigado. Este e-mail saiu antes de o sistema "
      "registrar a assinatura, e a edição completa já está na sua área do aluno.")

# (assunto, dias depois do e-mail anterior, parágrafos, texto do botão)
EMAILS = [
    ("Quatro gestoras concordaram. Quanto dinheiro estava de cada lado?", 3, [
        "Fala, {{ subscriber.first_name }}.",
        "Na edição de 13 de outubro, quatro casas chegaram à mesma conclusão por "
        "caminhos diferentes: a alternância de governo comprimiria o prêmio de risco "
        "brasileiro e abriria espaço para a Selic cair.",
        "Contar casas diz pouco. Quatro contra uma pode ser quatro fundos pequenos "
        "contra um grande. Por isso a síntese cruza cada tese com o patrimônio que a CVM "
        "registra sob mandato compatível: do lado do consenso, Legacy, Kapitalo e Dahlia "
        "somavam R$ 50,4 bi em fundos de juro e macro. A NEO, com R$ 3,1 bi, era a única "
        "que se declarava fora de apostas direcionais.",
        "E o consenso rachava no preço, não na direção. A Kapitalo, a maior do grupo, com "
        "R$ 29,5 bi, já tinha reduzido bolsa e juros. A Legacy, com R$ 17,5 bi, dizia que "
        "a assimetria sobrevivia \"mesmo após a forte reprecificação\".",
        "Nenhuma carta faz esse cruzamento sozinha. Ele só aparece com as cartas lado a "
        "lado e o patrimônio na conta, e é a seção que fecha cada edição completa. Com "
        "uma ressalva que a síntese repete sempre: mandato não é posição. A CVM diz o que "
        "o fundo pode fazer; só a carta diz o que ele fez.",
        OFERTA,
    ], "Assinar a síntese das cartas"),

    ("A Legacy viu três apostas. A conta viu uma.", 4, [
        "Fala, {{ subscriber.first_name }}.",
        "Na carta de setembro, a Legacy escreveu que câmbio, juros e bolsa carregam o "
        "mesmo prêmio de risco, o da condução da política econômica, e manteve o \"kit "
        "Brasil\" inteiro: comprada em real, aplicada em juros, comprada em bolsa.",
        "Se o prêmio é um só, as três posições são uma aposta só. O exercício da edição "
        "de 13 de outubro mediu isso. O índice de diversificação do kit, que vai de 1,00 "
        "(uma aposta com três nomes) a 1,73 (três apostas independentes), estava em 1,36 "
        "em 2 de outubro. Em 9 de outubro, caiu para 1,12, a menor leitura desde 2019. "
        "Tirando um único pregão, o de 5 de outubro, volta a 1,37.",
        # 31/10: saiu o caso da Kinea (petróleo, edição de 07/10). O exercício usou
        # IMAB11, ETF de renda fixa do Yahoo com preço CONGELADO até out/2025: a
        # "carteira" era só a metade em bolsa por quase três anos. Número contaminado.
        "O teste pode confirmar a carta ou desmenti-la; a edição mostra o que deu. É "
        "isso que vem em cada edição completa: a tese de uma casa testada com dado "
        "público, e o código em Python comentado, para você rodar e adaptar à tese que "
        "quiser checar. Não é para concordar com as gestoras. É para conseguir checar.",
        OFERTA,
    ], "Assinar a síntese das cartas"),

    ("Quando a carta não tem tese, a síntese diz", 5, [
        "Fala, {{ subscriber.first_name }}.",
        "Nem toda carta de gestora tem uma tese. Algumas são relatório de cenário e "
        "atribuição de resultado, e resumir uma carta assim com cara de análise é "
        "desperdiçar o seu tempo.",
        "Por isso a síntese diz quando não há tese. Na edição de 13 de outubro, sobre a "
        "NEO: a carta é uma leitura de cenário que termina declarando a eleição "
        "\"apertada demais para justificar apostas direcionais\". Na de 7 de outubro, "
        "sobre a Alaska: um relatório de cenário e atribuição, sem tese estruturada.",
        "Quando há tese, a síntese não para na descrição do mês. Vai ao mecanismo, a "
        "cadeia que faz a aposta se pagar, e à condição em que ela quebra. É o que "
        "separa ler o que a gestora fez de entender por que ela fez.",
        "São 15 gestoras brasileiras, e Oaktree, GMO e Bridgewater quando publicam. "
        "Dynamo e IP escrevem ensaios irregulares, os mais densos do grupo, e entram na "
        "edição da semana em que saem: você não precisa vigiar o site de ninguém.",
        OFERTA,
    ], "Assinar a síntese das cartas"),

    ("O que entra na assinatura, sem rodeio", 8, [
        "Fala, {{ subscriber.first_name }}.",
        "Você já viu a amostra e tem recebido o resumo de cada edição. Este é o último "
        "desta série de e-mails sobre a assinatura; daqui em diante, você segue "
        "recebendo o resumo de cada edição nova.",
        "O que a assinatura entrega, em cada semana em que alguma gestora publica carta "
        "nova:",
        "• a síntese completa em PDF: a tese de cada casa, o mecanismo e os riscos que "
        "ela mesma aponta;<br>• as convergências e divergências entre as casas, com o "
        "patrimônio sob mandato de cada lado;<br>• o exercício em Python que testa uma "
        "das teses com dado público, com o código comentado;<br>• todas as edições desde "
        "agosto de 2026 na sua área do aluno.",
        "Uma ressalva honesta: as cartas não têm cadência fixa. A maioria sai nas duas "
        "primeiras semanas do mês, e na semana em que nenhuma gestora publica não há "
        "edição.",
        "R$ 97 por mês, sem taxa de adesão.",
    ], "Assinar a síntese das cartas"),
]


def versao_campanha(i: int, pars: list[str]) -> list[str]:
    """Os leads antigos não receberam o boas-vindas com a amostra (entraram antes de
    31/10): o primeiro e-mail a oferece, e o último não supõe que a viram."""
    pars = list(pars)
    if i == 0:
        pars.insert(-1, f'Se você ainda não viu uma edição completa, <a href="{AMOSTRA}" '
                        'target="_blank" class="ck-link" rel="noopener noreferrer">aqui '
                        'está a de 13 de outubro</a>, inteira.')
    if i == len(EMAILS) - 1:
        pars[1] = ("Você tem recebido o resumo de cada edição. Este é o último desta série "
                   "de e-mails sobre a assinatura; daqui em diante, você segue recebendo o "
                   "resumo de cada edição nova.")
    return pars


def html(paragrafos: list[str], botao: str) -> str:
    """No molde do boas-vindas 10516834 (mesma tabela e classes do editor do Kit)."""
    p = lambda t: f'<p class="">{t}</p>'
    corpo = "".join(p(t) for t in paragrafos)
    corpo += p(f'<a href="{ASSINAR}" target="_blank" class="ck-link" rel="noopener noreferrer">{botao}</a>')
    corpo += p("Um abraço.")
    corpo += p('<strong style="font-weight:bolder">Vítor Wilher — Análise Macro</strong>'
               '<em><strong style="font-weight:bolder">&#8203;<br/>&#8203;</strong></em>'
               '<em>A verdade está nos dados</em>')
    corpo += p(f"<small>{PS}</small>")
    return f'<table cellPadding="0" cellSpacing="0" style="width:100%;margin:0 auto"><tbody><tr><td>{corpo}</td></tr></tbody></table>'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publicar", action="store_true")
    ap.add_argument("--campanha", action="store_true")
    args = ap.parse_args()

    if args.campanha:
        return campanha()
    if args.dry_run:
        for assunto, dias, pars, botao in EMAILS:
            print(f"\n=== +{dias} dias | {assunto}\n")
            print("\n\n".join(pars).replace("<br>", "\n"))
            print(f"\n[{botao}]\n\n{PS}")
        return 0

    c = httpx.Client(base_url="https://api.kit.com/v4", timeout=60,
                     headers={"X-Kit-Api-Key": ENV["CONVERT_KIT_V4"]})
    S = f"/sequences/{SEQ}/emails"
    existentes = {e["subject"]: e for e in c.get(S).json()["emails"]}
    estilo = c.get(f"{S}/{BOAS_VINDAS}").json()["email"]["content"].split("<table")[0]
    ultima = max(e["position"] for e in existentes.values())

    ids = []
    for assunto, dias, pars, botao in EMAILS:
        if assunto in existentes:
            print(f"  já existe: {existentes[assunto]['id']} {assunto}")
            ids.append(existentes[assunto]["id"])
            continue
        ultima += 1
        r = c.post(S, json={"subject": assunto, "content": estilo + html(pars, botao),
                            "published": False, "position": ultima, "delay_value": dias,
                            "delay_unit": "days", "send_days": DIAS})
        if r.status_code >= 300:
            print(f"🔴 {assunto}: HTTP {r.status_code} {r.text[:200]}", file=sys.stderr)
            return 1
        eid = r.json()["email"]["id"]
        corpo = c.get(f"{S}/{eid}").json()["email"].get("content") or ""
        if ASSINAR not in corpo:
            print(f"🔴 {eid}: o corpo não gravou (releitura sem o link)", file=sys.stderr)
            return 1
        print(f"  criado (despublicado): {eid} pos {ultima} +{dias}d {assunto}")
        ids.append(eid)

    if args.publicar:
        # Rascunhos antigos para o fim ANTES de publicar: na frente, travam a fila.
        topo = 100
        for eid in RASCUNHOS_ANTIGOS:
            topo += 1
            c.put(f"{S}/{eid}", json={"position": topo}).raise_for_status()
        # Abre espaço nas posições 1..n e põe os de upsell nelas, na ordem.
        for i, eid in enumerate(ids):
            c.put(f"{S}/{eid}", json={"position": 50 + i}).raise_for_status()
        for i, eid in enumerate(ids, start=1):
            c.put(f"{S}/{eid}", json={"position": i, "published": True}).raise_for_status()

    print("\nOrdem da sequência:")
    for e in sorted(c.get(S).json()["emails"], key=lambda e: e["position"]):
        print(f"  pos {e['position']:>3} | {'PUBLICADO' if e['published'] else 'rascunho '} | "
              f"+{e['delay_value']}d | {e['id']} | {e['subject'][:60]}")
    return 0


def campanha() -> int:
    """Agenda os quatro broadcasts. Mesmas guardas do broadcast_semanal.py: não
    duplica (assunto já pendente), confere o segmento na RELEITURA e o status."""
    from datetime import datetime, timezone
    h = {"X-Kit-Api-Key": ENV["CONVERT_KIT_V4"]}
    c = httpx.Client(base_url="https://api.kit.com/v4", timeout=90, headers=h)
    estilo = c.get(f"/sequences/{SEQ}/emails/{BOAS_VINDAS}").json()["email"]["content"].split("<table")[0]
    pendentes = {b["subject"]: b["id"] for b in c.get("/broadcasts", params={"per_page": 100}).json()["broadcasts"]
                 if b.get("status") in ("draft", "scheduled")}
    filtro = [{"all": [{"type": "tag", "ids": [TAG_LEADS]}]}]
    for i, ((assunto, _, pars, botao), quando) in enumerate(zip(EMAILS, CAMPANHA)):
        if datetime.fromisoformat(quando.replace("Z", "+00:00")) < datetime.now(timezone.utc):
            print(f"🔴 {quando} já passou — o Kit dispararia na hora. Nada criado.", file=sys.stderr)
            return 1
        if assunto in pendentes:
            print(f"  já agendado: {pendentes[assunto]} {assunto}")
            continue
        r = c.post("/broadcasts", json={"subject": assunto, "public": False, "send_at": quando,
                                        "content": estilo + html(versao_campanha(i, pars), botao),
                                        "subscriber_filter": filtro})
        if r.status_code >= 300:
            print(f"🔴 {assunto}: HTTP {r.status_code} {r.text[:200]}", file=sys.stderr)
            return 1
        bid = r.json()["broadcast"]["id"]
        b = c.get(f"/broadcasts/{bid}").json()["broadcast"]
        ok = b.get("subscriber_filter") == filtro and ASSINAR in (b.get("content") or "")
        print(f"  {'agendado' if ok else '🔴 CONFERIR'}: {bid} | {quando} | status {b.get('status')} | {assunto}")
        if not ok:
            print("   O segmento ou o corpo não bateu na releitura: CANCELE no painel.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
