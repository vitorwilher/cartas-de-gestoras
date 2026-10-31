# Post da semana — pacotes para o mLabs

Cada edição com carta nova gera, no workflow de terça, uma pasta `AAAA-MM-DD/`:

| Arquivo | O que é |
|---|---|
| `post-linkedin.txt` | texto do LinkedIn, com o link da landing (UTM `post-AAAA-MM-DD`) |
| `legenda-instagram.txt` | legenda do Instagram, com a palavra-chave `GESTORAS` (ManyChat) |
| `imagem.png` | o gráfico do exercício da edição |
| `pacote.json` | metadados; `status` = `pendente` → `agendado` (com os ids do mLabs) |

Quem gera: `divulgacao/post_semanal.py` (Claude + checagem). Quem publica: a rotina
agendada na nuvem, que roda às terças à tarde, sobe a imagem e **agenda** os posts no
mLabs para quarta, 12h (Brasília). Entre o agendamento e a publicação, dá para
editar ou cancelar no painel do mLabs.

## A rotina

`trig_012qUk3QKHn4HSaGhqH7VKJF` — https://claude.ai/code/routines/trig_012qUk3QKHn4HSaGhqH7VKJF
Terças, 17h (Brasília) = `0 20 * * 2` UTC; o workflow começa entre 11h e 13h20 e leva
~15 min, então há folga. Modelo Sonnet 5.5, conector mLabs. Sobe a imagem pela URL
`raw.githubusercontent.com` (o repositório é público) — o `prepare_media_upload` com
PUT na URL assinada deu `SignatureDoesNotMatch` no teste de 31/10. Cria dois
agendamentos (LinkedIn página + pessoal juntos; Instagram à parte) e commita o
`pacote.json` como `agendado`, com os ids do mLabs.

Perfil mLabs `ext_Mzk2NzU0MQ.Wr5lJ4X2bSpmcYBqTWG_uw` ("Equipe de conteúdo"). Para
cancelar uma semana: apagar os agendamentos no painel do mLabs até quarta 12h.

## Decisão (31/10/2026)

O Vitor escolheu **publicação automática via mLabs** e **post + imagem única** (não o
carrossel de 10 slides). Até 13/10 as peças eram escritas à mão numa sessão por
semana; quando as sessões pararam, os posts pararam e o tráfego da landing caiu de
~100 para 5–16 visitantes/semana.

## As guardas

O pacote só é gravado se o post passar em `validar()`:

- todo número precisa estar na edição ou em `digests/resumo/saida-exercicio.txt`
  (arredondar é permitido); contagens < 100 e anos são isentos;
- nada de preço (`R$`, `97`), emoji, hashtag, markdown ou placeholder;
- LinkedIn com o link exato da landing; Instagram com `GESTORAS` e sem link;
- tamanho dentro do limite de cada rede.

Duas tentativas; se a segunda falhar, não há pacote — **uma semana sem post, nunca um
post errado no ar**. O resultado aparece no Resumo do run.

⚠️ A saída do exercício só existe a partir das edições geradas depois de 31/10/2026:
`exercicios/execucao.py` passou a gravá-la (e a imprimir a tabela do pandas inteira —
antes, as colunas do meio viravam "...").
