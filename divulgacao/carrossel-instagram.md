# Carrossel de Instagram — teste do produto Cartas de Gestoras

**Status: PNGs gerados, NÃO publicado.**

Este é o **teste que precede a construção do produto** (decisão do Vitor em
2026-09-09): antes de publicar a assinatura no Woo, medir se o conteúdo desperta
interesse no Instagram.

- **Arquivos:** `divulgacao/carrossel/slide-01.png` … `slide-08.png` (1080×1350)
- **Gerador:** `python divulgacao/carrossel.py`
- **Palavra-chave da DM:** `GESTORAS` — ver `manychat-gestoras.md`

## Por que este ângulo

O carrossel mostra **as convergências e divergências da semana**, não o exercício.
O racha sobre o Copom é a melhor história disponível: quatro casas leem a mesma
inflação e duas chegam a apostas incompatíveis — e isso só aparece lendo as cartas
juntas, que é exatamente a promessa do produto.

Abre com **cena**, não com rótulo: está medido no canal que série aberta por
rótulo engaja metade. Sem preço e sem oferta — o público do Instagram está em
nível 1-2 de consciência, e entregar nível 5 a quem está no 2 é o erro documentado
que rendeu 174 mensagens e zero respostas em Claude Code T2.

## Os 9 slides

**A regra que organiza a ordem:** nenhum gráfico aparece antes de o leitor ter
contexto para lê-lo. Foi o erro da versão anterior — a capa trazia a série da
inclinação da curva enquanto a manchete falava de inflação e gestoras, e "48 bps"
não significa nada para quem passa o polegar sem saber do que é a medida.

| # | Tipo | Conteúdo |
|---|---|---|
| 1 | capa + gráfico | A divergência do Copom: duas trajetórias de Selic, cada casa nomeada na ponta |
| 2 | lista ✓ | No que elas concordam — 4 bullets |
| 3 | lista | Onde racha: o Copom — 3 bullets |
| 4 | definição | A diferença não é sobre inflação: Legacy/Occam × Kinea |
| 5 | lista | E isso custa dinheiro — o *steepener* explicado, **antes** dos gráficos de curva |
| 6 | capa + gráfico | "É esse degrau que elas estão comprando" — a curva de hoje |
| 7 | capa + gráfico | "+48 bps, percentil 45" — a inclinação contra a própria história |
| 8 | lista | O que isso quer dizer — e você não precisou acreditar em ninguém |
| 9 | lista numerada | **O caminho que eu fiz aqui** — tese → mecanismo → código → gráfico |
| 10 | CTA | "Te mando o código junto" + `GESTORAS` + pergunta |

### O eixo do fecho: o método, não a síntese

Resumir carta é commodity — qualquer um faz, e a IA faz de graça. O que ninguém
mais entrega é **o caminho da tese até o código que a testa**. Por isso o slide 9
mostra esse caminho em quatro passos numerados, e só então o CTA oferece o
exercício *junto* com a síntese.

A versão anterior fechava com "Quer a síntese desta semana?" — prometia justamente
a parte replicável por qualquer um. O ativo é o script que roda.

**Todo gráfico leva título e subtítulo dizendo o que a medida é** (ex.: "Inclinação
da curva: 7 anos − 2 anos" / "quanto o juro longo paga a mais que o curto"). Num
carrossel não há legenda nem texto de apoio: o gráfico precisa se apresentar.

⚠️ **Os números vêm do próprio exercício.** `carrossel.py` reexecuta o bloco de
código da edição mais recente (cortando antes da parte de gráfico) e lê as
variáveis de lá. Se o carrossel dissesse 48 bps e o PDF outra coisa, a
inconsistência seria checável por quem lê os dois.

⚠️ O exercício é reescrito pelo modelo a cada edição e os **nomes das variáveis
mudam**. `dados_do_exercicio()` normaliza por alias e **falha alto** se faltar algo
essencial — melhor do que um KeyError no meio do render.

## Legenda do post

> Quatro gestoras publicaram carta em agosto e concordam em quase tudo: núcleos de
> serviços pressionados, expectativas com viés de alta, atividade desacelerando,
> eleição empatada.
>
> Aí chega o Copom e elas se separam. Bahia, Occam e Legacy veem o ciclo de cortes
> seguindo. A Kinea vê pausa.
>
> A diferença não é sobre inflação — é sobre a que o Banco Central reage. E tem
> preço: Bahia e Occam carregam o mesmo steepener, e a pausa que a Kinea projeta é
> exatamente o cenário em que a perna curta desse trade perde.
>
> Mas aqui está a parte que interessa a quem quer aprender:
>
> Você não precisa acreditar em nenhuma delas. Dá para ler a tese, achar o
> mecanismo que a sustenta e escrever o código que mede se ele já está no preço.
> Foi o que fiz no slide 6 e 7 — dado público do Tesouro Direto, seis segundos de
> execução, e a resposta: +48 bps, percentil 45 desde 2010. O degrau está na média
> histórica. A aposta não está barata na entrada.
>
> É isso que eu faço toda semana: leio as cartas das 12 maiores gestoras do Brasil,
> destrincho as teses e escrevo um exercício em Python que testa uma delas.
>
> Comenta GESTORAS que eu mando a desta semana — a síntese e o código — no direct.
>
> E me conta: qual tese você queria ver testada?

## Checklist antes de publicar

- [ ] 🔴 **Criar o fluxo `GESTORAS` no painel do ManyChat** — a API não cria. Sem
      ele, quem comenta não recebe nada e o lead se perde em silêncio
- [ ] Definir para onde o link da DM aponta (página de captura ou produto)
- [ ] Testar ponta a ponta comentando `GESTORAS` de uma conta que nunca interagiu
- [ ] Conferir os PNGs no celular — é de onde vem a maior parte do tráfego
- [ ] Se virar anúncio: nome de campanha/adset **sem pipe (`|`)** — a macro
      `{{campaign.name}}` entra na URL e o firewall devolve 403 de tela branca.
      Já custou R\$ 385,72 em nove dias

## Sobre os gráficos

Os slides 6 e 7 são **dados reais**, do mesmo código do exercício que está no PDF:
curva prefixada do Tesouro Direto em 08/09/2026 e a série da inclinação 7a−2a desde
2010. A inclinação de **+48 bps no percentil 45** é medida, não estimada.

⚠️ **O gráfico da capa é ilustrativo do conceito.** As cartas dizem a direção
("ciclo segue" × "pausa"), não uma trajetória de Selic ponto a ponto. Por isso o
eixo x é relativo (hoje, +6m, +12m, +18m) e não afirma data nem valor futuro —
mostra a forma da divergência. Se alguém do mercado perguntar, essa é a resposta.
