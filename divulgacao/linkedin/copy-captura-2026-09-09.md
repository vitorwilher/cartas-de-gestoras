# LinkedIn — copy de captura (produto recorrente)

**Status: copy pronta, NÃO publicada.** Publicação é manual — não há automação de
LinkedIn na casa.

- **Landing:** https://analisemacro.com.br/projetos/cartas-das-gestoras/
- **Arte sugerida:** `divulgacao/linkedin/linkedin-01.png` (1200×627) — ou uma nova
  peça sem número de edição, ver Notas
- **Peça anterior:** `divulgacao/linkedin.md` (copy de 09/09, foco em produto também)

---

## Copy do post

> Bahia e Occam chegaram ao mesmo trade por caminhos opostos. As duas estão tomadas
> na inclinação da curva brasileira. Nenhuma das duas cartas diz quanto dessa aposta
> já está no preço.
>
> Essa é a lacuna que interessa. A carta de uma gestora te dá a visão de uma casa.
> Doze cartas lidas juntas te dão outra coisa: o mapa de onde o mercado brasileiro
> concorda, onde ele racha, e — o mais útil — quais premissas cada casa precisa que
> sejam verdadeiras para ganhar dinheiro.
>
> Ninguém lê as doze. Não por falta de disciplina: são centenas de páginas por mês,
> em periodicidades diferentes, e o trabalho de comparar é maior que o de ler.
>
> Foi por isso que montei a Síntese das Cartas das Gestoras.
>
> O que vai em cada edição:
>
> → A tese de cada casa reduzida ao mecanismo. Não "a gestora está otimista com
> Brasil", mas a cadeia causal que faz a posição se pagar — e a condição específica
> em que ela quebra. Quando a carta é só descritiva, a síntese diz isso, em vez de
> parafrasear.
>
> → As convergências e as divergências. Casas que concordam nos fatos e discordam
> no coeficiente: mesma leitura do Fed, posições opostas em dólar. É aí que está a
> informação — o consenso todo mundo já sabe.
>
> → Um exercício em Python que mede uma das teses com dado público. Se duas casas
> estão tomadas em inclinação, o código busca a curva do Tesouro Direto, calcula o
> spread 7 anos menos 2 anos e o coloca contra a própria história. Roda em segundos.
> Você replica, adapta e discorda com número na mão.
>
> A promessa não é te poupar leitura. É te dar o caminho que vai da tese ao código
> que a testa — o mesmo caminho que você faria se tivesse a semana livre.
>
> Dynamo, IP, Alaska, Kapitalo, Adam, Legacy, Bahia, Occam, JGP, Kinea, NEO e Dahlia.
>
> Para receber:
> https://analisemacro.com.br/projetos/cartas-das-gestoras/
>
> #mercadofinanceiro #rendafixa #python #gestãodeativos

---

## Notas

### O gancho

As duas primeiras linhas são um fato verificável da edição de 09/09 — Bahia e Occam
tomadas em inclinação, cada uma por um caminho argumentativo diferente — seguido de
uma lacuna nomeada: *nenhuma das duas cartas diz quanto já está no preço*.

Por que essa escolha:

1. **Nome de gestora na primeira linha para no scroll.** Quem é do mercado reconhece
   as duas casas. "Toda semana, doze gestoras publicam suas cartas" (abertura da copy
   anterior) é uma premissa geral — o leitor concorda e segue rolando, porque nada
   foi afirmado que ele não soubesse.
2. **A lacuna é a proposta de valor inteira, em três linhas.** O produto não é o
   resumo; é o que as cartas não fazem. Abrir pela lacuna faz o gancho e a oferta
   coincidirem, sem precisar de transição.
3. **É concreto sem ser datado.** O leitor não precisa que o trade ainda esteja de pé
   — o exemplo ilustra o tipo de leitura que a síntese entrega. Ainda assim, ver a
   ressalva de validade abaixo.

### O que foi evitado, e por quê

- **"De graça toda semana"** — rejeitado pelo Vitor. Além disso, gratuidade como
  chamada principal ancora o valor percebido em zero, o que atrapalha a conversão do
  produto de assinatura que vem depois. A copy nunca menciona preço: o custo aparece
  como "seu e-mail", implícito na landing.
- **Repetir a abertura da peça anterior.** A copy de `linkedin.md` abre em
  "Toda semana, doze gestoras brasileiras publicam suas cartas. Você lê duas ou três".
  O argumento da comparação continua sendo o certo, mas foi reescrito e movido para o
  segundo bloco — o leitor que viu as duas peças não lê a mesma frase duas vezes.
- **O exemplo do ciclo de crédito** (três mesas descrevendo o mesmo ciclo virando)
  também já foi usado na peça anterior. Ficou de fora; entrou o steepener, que aqui
  tem função dupla: é o gancho e é o exemplo do exercício.
- **CTA de comentário / palavra-chave.** `GESTORAS` é do fluxo do ManyChat, que é do
  Instagram. No LinkedIn o link vai no texto.
- **Emoji, "🚀", "imperdível", números de vaidade.** O público confere. As setas (→)
  são separadores de lista, não decoração.
- **A tensão eleitoral e o "Fed vai subir juros".** São a manchete da edição de 09/09,
  não do produto. Uma copy de captura construída sobre a manchete envelhece em uma
  semana e precisa ser reescrita a cada publicação — decisão já registrada em
  `linkedin.md` (09/09).

### Escolhas de estrutura

- **Três blocos com →, não bullets.** O LinkedIn colapsa o texto depois de ~3 linhas;
  os blocos dão pontos de retomada visual para quem abre "ver mais".
- **O fecho contrasta com a promessa óbvia.** "A promessa não é te poupar leitura" —
  porque poupar leitura é o que qualquer LLM entrega hoje, de graça, e o leitor sabe
  disso. O ativo é o caminho tese → mecanismo → código, mesmo eixo do slide 9 do
  carrossel.
- **Os doze nomes aparecem antes do CTA.** Funcionam como prova de escopo e como a
  única lista que o leitor de mercado escaneia sem esforço.
- **A lista de gestoras é do catálogo, não da edição.** A edição de 09/09 tem quatro
  casas (a Kinea caiu por rate limit na coleta). O post é sobre o produto: a lista
  correta é a das doze cobertas.

### Ressalvas antes de publicar

- ⚠️ **Conferir a URL da landing.** A copy usa
  `https://analisemacro.com.br/projetos/cartas-das-gestoras/`, informada no briefing.
  O `divulgacao/wordpress/README.md` registra a página de captura em
  `/conteudo/cartas-das-gestoras/` (id 78395). Se o slug mudou, o README está
  desatualizado; se não mudou, a copy precisa do slug antigo. **Não publicar sem
  abrir o link.** (Sem acesso de rede aqui — não foi possível verificar.)
- ⚠️ **Validade do gancho.** O steepener de Bahia e Occam é de agosto/2026, publicado
  em setembro. Se o post sair semanas depois, trocar o exemplo pelo da edição vigente
  — o formato do gancho ("duas casas, mesmo trade, a pergunta que nenhuma responde")
  se reaproveita.
- **Arte.** `linkedin-01.png` traz "hoje: +48 bps", número medido em 08/09/2026. Numa
  peça de captura que deve durar, o ideal é uma versão sem o valor pontual — ou aceitar
  que a arte também tem validade. O gráfico da inclinação, com título e subtítulo
  dizendo o que a medida é, continua sendo a peça certa.
- A afirmação "roda em segundos" está calibrada: o exercício de 09/09 executa rápido,
  mas baixa um CSV de dezenas de MB na primeira chamada. Evitado o "seis segundos" da
  peça anterior, que não inclui o download.
