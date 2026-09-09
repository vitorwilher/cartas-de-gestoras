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

## Os 8 slides

| # | Tipo | Conteúdo |
|---|---|---|
| 1 | capa + gráfico | "Quatro gestoras leram a mesma inflação. Duas chegaram a apostas opostas." |
| 2 | texto | O consenso: diagnóstico igual nas quatro casas |
| 3 | texto | Onde racha: o Copom — três veem corte, Kinea vê pausa |
| 4 | definição | Por que a diferença não é sobre inflação, e sim sobre função de reação |
| 5 | texto | E isso custa dinheiro: Bahia e Occam carregam o mesmo *steepener* |
| 6 | dado | **−3,7%** — o que juros renderam em 12 meses no Bahia Mutá |
| 7 | texto | É isto que aparece lendo as cartas juntas |
| 8 | CTA | Comente `GESTORAS` + pergunta para engajamento |

## Legenda do post

> Quatro gestoras publicaram carta em agosto e concordam em quase tudo: núcleos de
> serviços pressionados, expectativas com viés de alta, atividade desacelerando,
> eleição empatada.
>
> Aí chega o Copom e elas se separam.
>
> Bahia, Occam e Legacy veem o ciclo de cortes seguindo. A Kinea vê pausa — "para
> preservar margem de manobra até que haja clareza sobre o orçamento".
>
> A diferença não é sobre inflação. É sobre a que o Banco Central reage: para
> Legacy e Occam, aos dados de atividade. Para a Kinea, à incerteza fiscal
> pós-eleitoral.
>
> E isso tem preço. Bahia e Occam carregam o mesmo trade — steepener doméstico, uma
> aposta em que o juro longo sobe mais que o curto. A pausa que a Kinea projeta é
> exatamente o cenário em que a perna curta desse trade perde.
>
> Uma carta isolada mostra a visão de uma casa. Quatro mostram onde o mercado
> concorda — e onde a mesma leitura vira apostas incompatíveis.
>
> Comenta GESTORAS que eu te mando a síntese desta semana no direct.
>
> E me conta: qual gestora você acompanha de verdade?

## Checklist antes de publicar

- [ ] 🔴 **Criar o fluxo `GESTORAS` no painel do ManyChat** — a API não cria. Sem
      ele, quem comenta não recebe nada e o lead se perde em silêncio
- [ ] Definir para onde o link da DM aponta (página de captura ou produto)
- [ ] Testar ponta a ponta comentando `GESTORAS` de uma conta que nunca interagiu
- [ ] Conferir os PNGs no celular — é de onde vem a maior parte do tráfego
- [ ] Se virar anúncio: nome de campanha/adset **sem pipe (`|`)** — a macro
      `{{campaign.name}}` entra na URL e o firewall devolve 403 de tela branca.
      Já custou R\$ 385,72 em nove dias

## Ressalva sobre o gráfico da capa

As duas trajetórias de Selic são **ilustrativas do conceito**, não projeções das
gestoras. Nenhuma das cartas publica uma trajetória ponto a ponto; o que elas dizem
é a direção ("ciclo segue" × "pausa"). O gráfico mostra a forma da divergência, e a
legenda no slide não afirma número. Se alguém do mercado perguntar, essa é a
resposta honesta.
