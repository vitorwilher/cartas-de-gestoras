# Arquitetura da entrega semanal

O desenho vive em `arquitetura-whatsapp-hub.svg` (SVG escrito à mão; o
`.excalidraw` é a versão editável da primeira iteração, hoje defasada).

## O que o sistema faz

Toda terça, 07:00 BRT, o pipeline lê as cartas novas das 12 gestoras, escreve a
síntese, gera o exercício em Python, publica o PDF numa URL fixa e dispara dois
canais — **sem intervenção humana**.

## As quatro fases, e o que cada uma provou

| Fase | O que faz | Status |
|---|---|---|
| 1 · ouvir | Receber o `add_talk` do Kommo | ✓ provado 09/09 — Alan 21:44, Luiz 21:47 |
| 2 · registrar | Resolver nome/telefone e cruzar com a tag do Kit | ✓ provado 09/09 |
| 3 · responder | Enviar o PDF pela Cloud API | ✓ provado 09/09 — HTTP 200 + wamid |
| 4 · follow-up | Mensagem de D+1 dentro da janela de 24h | não iniciada |

## As duas decisões que sustentam tudo

**1. O Kommo avisa; nós ouvimos.** A Meta aceita um webhook por WABA, e ele é do
Kommo. Assumi-lo mataria o atendimento da Raiane. Verificamos que a alternativa
óbvia era impossível — a API do Kommo não injeta mensagem no chat nativo
(endpoint privado, 403) — e invertemos a direção: consumimos o webhook do próprio
Kommo. Ele continua dono do canal.

**2. Quem decide o envio é a tag do projeto.** `Leads - Cartas Semanais`
(23251247), não a guarda-chuva `Mercado Financeiro` (534 pessoas). Usar a
guarda-chuva mandaria PDF para gente que nunca ouviu falar do projeto.

## Os dois canais

**E-mail** (`divulgacao/broadcast_semanal.py --enviar`) — alcança todo lead
cadastrado. Agenda para +30 min em vez de disparar no ato: `scheduled` é
cancelável, envio imediato não é.

**WhatsApp** (`divulgacao/whatsapp/escuta/`) — só para quem escreveu primeiro; é
o lead que abre a janela de 24h. Na dúvida (Kit indisponível), não envia.

## Guardas que impedem o pior desfecho

O pior desfecho de um sistema de comunicação automática não é ficar mudo — é
mandar a mensagem errada para a pessoa certa. Três guardas:

1. **Frescor** — recusa edição mais velha que 2 dias. Sem isso, uma terça sem
   cartas reenviaria a edição anterior aos mesmos leads.
2. **Duplicata** — não cria broadcast se já existe um pendente com o mesmo
   assunto. Rodar duas vezes agendava dois e-mails idênticos.
3. **Segmento confirmado na releitura** — a v3 do Kit aceitava o filtro,
   respondia 200 e o descartava. Status HTTP não é prova de efeito.

## Por que vale para qualquer projeto

O Worker não sabe o que é "Cartas de Gestoras". Ele consulta um mapa: de qual
landing veio, qual PDF entregar, qual tag aplicar, qual sequência disparar.
**Projeto novo = uma linha nova no mapa.**

## Cuidados

- **IP bloqueado em 08/09** por excesso de chamadas ao Kommo. Espaçar
  requisições; não sondar endpoints em série.
- **A leitura de tags do Kit atrasa por indexação** — pode voltar vazia enquanto
  o painel já mostra a tag aplicada. Não concluir falha de uma leitura só.
- **No WordPress, escrever pela API não publica.** Limpar o cache do Elementor
  (`DELETE /wp-json/elementor/v1/cache`) e fazer o ciclo `draft → publish`.
