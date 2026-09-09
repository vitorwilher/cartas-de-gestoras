// wa-escuta — FASE 2: ouvir e REGISTRAR.
//
// Recebe o webhook `add_talk` do Kommo, resolve o telefone de quem escreveu e
// cruza com o lead que veio da landing (via ConvertKit). Guarda tudo no KV.
//
// AINDA NÃO ENVIA NADA. Nenhuma mensagem sai daqui — o objetivo é provar que
// conseguimos reconhecer quem é a pessoa antes de falar com ela.
//
// ⚠️ O Kommo bloqueou o IP do Vitor em 08/09 por excesso de requisições. Este
//    Worker faz NO MÁXIMO 1 chamada ao Kommo por evento, e guarda o resultado
//    em cache por 24h para não repetir a consulta do mesmo contato.

interface Env {
  EVENTOS: KVNamespace;
  KOMMO_TOKEN: string;
  KOMMO_SUBDOMAIN: string;
  CONVERTKIT_SECRET: string;
  WHATSAPP_TOKEN: string;
  WHATSAPP_PHONE_ID: string;
  /** Lista de permissão: só estes números recebem resposta automática.
   *  Vazio = ninguém recebe (modo observação). Separados por vírgula. */
  PERMITIDOS: string;
}

type Contato = { nome: string; telefone: string };

const AJUDA = `wa-escuta — fase 2 (ouve e registra)

POST /kommo/    recebe o webhook, resolve o contato e cruza com o lead
GET  /ultimos   o que foi registrado (mais recente primeiro)
GET  /limpar    apaga o registrado

Nada aqui envia mensagem.`;

/** Só dígitos, com DDI 55 quando vem sem. É o formato que o Kit guarda. */
function normalizar(tel: string): string {
  const d = (tel || "").replace(/\D+/g, "");
  return d && d.length <= 11 ? `55${d}` : d;
}

/** Uma chamada ao Kommo, com cache de 24h por contato. */
async function buscarContato(env: Env, contactId: string): Promise<Contato | null> {
  const cache = `contato:${contactId}`;
  const salvo = await env.EVENTOS.get(cache);
  if (salvo) return JSON.parse(salvo);

  const url = `https://${env.KOMMO_SUBDOMAIN}.kommo.com/api/v4/contacts/${contactId}`;
  const r = await fetch(url, { headers: { Authorization: `Bearer ${env.KOMMO_TOKEN}` } });
  if (!r.ok) return null;

  const d: any = await r.json();
  let telefone = "";
  for (const cf of d.custom_fields_values ?? []) {
    if (cf.field_code === "PHONE" && cf.values?.length) {
      telefone = cf.values[0].value ?? "";
      break;
    }
  }
  const contato = { nome: d.name ?? "", telefone };
  await env.EVENTOS.put(cache, JSON.stringify(contato), { expirationTtl: 86400 });
  return contato;
}

/** O telefone existe na base do Kit? É o que diz se veio da landing.
 *
 * ⚠️ A API do Kit NÃO busca por campo custom — só lista com paginação. Varrer
 *    5.118 assinantes (103 páginas) a cada mensagem seria inviável e ainda
 *    estouraria o tempo do Worker.
 *
 *    Por isso a busca é na TAG do projeto, que tem 532 pessoas em vez de 5.118,
 *    e para nas primeiras 5 páginas. Se não achar, devolve "indeterminado" —
 *    e não um falso negativo, que seria pior: diria que o lead não veio da
 *    landing quando talvez tenha vindo.
 *
 *    A solução definitiva é o próprio formulário gravar o telefone no nosso KV
 *    no momento do cadastro — aí a consulta é instantânea e exata. Fica para
 *    quando a ponte PHP for ajustada.
 */
// ⚠️ A tag do PROJETO, não a guarda-chuva. "Mercado Financeiro" (22406993) tem
//    534 pessoas, a maioria vinda de outros materiais — usá-la como critério
//    mandaria o PDF para quem nunca pediu. "Leads - Cartas Semanais" só tem quem
//    passou por ESTA landing.
const TAG_PROJETO = 23251247;   // "Leads - Cartas Semanais"

async function buscarNoKit(env: Env, telefone: string) {
  if (!env.CONVERTKIT_SECRET || !telefone) return { estado: "sem_dados" };
  const alvo = normalizar(telefone);

  // ⚠️ O Kit IGNORA per_page acima de 50 — pedir 100 devolve 50 e o campo
  //    total_pages é calculado sobre 50. Parar "quando vier menos que o pedido"
  //    faria a busca terminar na primeira página, sempre. Use total_pages.
  let totalPaginas = 1;
  for (let pagina = 1; pagina <= totalPaginas && pagina <= 12; pagina++) {
    const url = `https://api.convertkit.com/v3/tags/${TAG_PROJETO}/subscriptions`
      + `?api_secret=${env.CONVERTKIT_SECRET}&per_page=50&page=${pagina}`;
    const r = await fetch(url);
    if (!r.ok) return { estado: "erro_kit" };
    const d: any = await r.json();
    totalPaginas = d.total_pages ?? 1;
    for (const item of d.subscriptions ?? []) {
      const s = item.subscriber ?? {};
      const f = s.fields ?? {};
      if (normalizar(f.phone ?? "") === alvo || normalizar(f.whatsapp ?? "") === alvo) {
        return { estado: "encontrado", email: s.email_address,
                 nome: s.first_name, id: s.id, pagina };
      }
    }
  }
  return { estado: "nao_encontrado", paginas_varridas: totalPaginas };
}

const PDF_URL = "https://storage.googleapis.com/am-social-assets/cartas/edicao-atual.pdf";

/** Envia o PDF pela Cloud API. Só é chamada para número da lista de permissão.
 *
 * ⚠️ Isto só funciona DENTRO da janela de 24h aberta pelo próprio lead. Fora
 *    dela a Meta exige template — e usar o template UTILITY de entrega para
 *    captação é reclassificação de uso, que a Meta descarta em silêncio e ainda
 *    derruba a qualidade do número. Por isso não há fallback: se a janela
 *    fechou, não enviamos.
 */
async function enviarPDF(env: Env, telefone: string, nome: string) {
  const saudacao = nome ? `Oi, ${nome.split(" ")[0]}!` : "Oi!";
  const corpo = {
    messaging_product: "whatsapp",
    to: telefone,
    type: "document",
    document: {
      link: PDF_URL,
      filename: "sintese-cartas-das-gestoras.pdf",
      caption: `${saudacao} Aqui está a síntese das cartas das gestoras desta semana.\n\n`
        + "Dentro dela tem também o exercício em Python que testa uma das teses "
        + "com dado público — o código roda em segundos e você adapta para a tese "
        + "que quiser checar.\n\nBoa leitura!",
    },
  };
  const r = await fetch(
    `https://graph.facebook.com/v20.0/${env.WHATSAPP_PHONE_ID}/messages`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.WHATSAPP_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(corpo),
    },
  );
  const resposta: any = await r.json().catch(() => ({}));
  return {
    http: r.status,
    // O wamid é o que o suporte da Meta pede quando algo não chega.
    wamid: resposta?.messages?.[0]?.id ?? null,
    erro: resposta?.error?.message ?? null,
  };
}

/** Quem recebe a resposta automática?
 *
 * Duas portas, e ambas exigem confirmação positiva:
 *
 *  1. `veio_da_landing` — o telefone está na tag DO PROJETO ("Leads - Cartas
 *     Semanais"). É a porta de produção: quem passou pela nossa landing.
 *  2. `PERMITIDOS` — lista fixa, para teste. Independe do Kit.
 *
 * ⚠️ REGRA DA DÚVIDA (decisão do Vitor): se a busca no Kit falhar — API fora do
 *    ar, telefone em formato inesperado —, **não enviamos**. A conversa segue
 *    para a Raiane como qualquer outra. Um lead sem PDF automático é um
 *    problema pequeno; um cliente recebendo material de captação no meio de
 *    outro assunto é um problema grande.
 */
function podeReceber(env: Env, telefone: string, estadoKit: string): {
  ok: boolean; motivo: string;
} {
  const lista = (env.PERMITIDOS ?? "").split(",").map((x) => x.trim()).filter(Boolean);
  if (lista.includes(telefone)) return { ok: true, motivo: "lista de teste" };
  if (estadoKit === "encontrado") return { ok: true, motivo: "veio da landing" };
  if (estadoKit === "erro_kit") {
    return { ok: false, motivo: "Kit indisponível — na dúvida, não enviamos" };
  }
  return { ok: false, motivo: "não veio desta landing" };
}

/** Registra no lead do Kommo o que a automação enviou.
 *
 * ⚠️ POR QUE ISTO EXISTE: o Worker envia direto pela Cloud API, contornando o
 *    Kommo — e o Kommo NÃO tem como saber. Sem esta nota, a Raiane abre o card,
 *    vê só o "oi" do lead e não sabe que já respondemos. Pior: se o lead
 *    responder ao PDF, a resposta cai no Kommo e parece que ele fala sozinho.
 *
 *    A API do Kommo não injeta mensagem na thread do chat (endpoint privado,
 *    403). A nota é o que dá para fazer — e aparece no card.
 */
async function registrarNoKommo(env: Env, leadId: string, texto: string) {
  if (!leadId) return { pulado: "sem lead" };
  const url = `https://${env.KOMMO_SUBDOMAIN}.kommo.com/api/v4/leads/${leadId}/notes`;
  const r = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.KOMMO_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify([{ note_type: "common", params: { text: texto } }]),
  });
  return { http: r.status };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // O Kommo EXIGE barra final na URL ao cadastrar; aceitamos as duas formas.
    if (url.pathname === "/kommo" || url.pathname === "/kommo/") {
      let corpo = "";
      try { corpo = await request.text(); } catch { corpo = ""; }

      const p = new URLSearchParams(corpo);
      const contactId = p.get("talk[add][0][contact_id]") ?? "";
      const registro: Record<string, unknown> = {
        recebido_em: new Date().toISOString(),
        origem: p.get("talk[add][0][origin]") ?? "",
        contact_id: contactId,
        entity_id: p.get("talk[add][0][entity_id]") ?? "",
        talk_id: p.get("talk[add][0][talk_id]") ?? "",
        chat_id: p.get("talk[add][0][chat_id]") ?? "",
      };

      // Resolve quem é — e, se der, de onde veio.
      if (contactId) {
        const c = await buscarContato(env, contactId);
        if (c) {
          registro.nome = c.nome;
          registro.telefone = normalizar(c.telefone);
          const lead = await buscarNoKit(env, c.telefone);
          registro.lead = lead;
          registro.veio_da_landing = lead.estado === "encontrado";

          // FASE 3: responde com o PDF — mas SÓ para número da lista de
          // permissão. Enquanto a lista tiver poucos números, nenhum lead real
          // recebe nada por acidente.
          const tel = registro.telefone as string;
          const leadId = registro.entity_id as string;
          const decisao = podeReceber(env, tel, (lead as any).estado ?? "");
          registro.decisao = decisao;
          if (decisao.ok) {
            const envio = await enviarPDF(env, tel, c.nome);
            registro.envio = envio;
            // A nota é o que a Raiane vê. Sem ela, o atendimento fica cego
            // para o que a automação fez.
            // Nota CURTA: no celular a tela é estreita, e o wamid (longo) só
            // serve para abrir chamado na Meta — algo raro. Ele fica no nosso
            // KV, que é onde iríamos procurar de qualquer forma.
            const quando = new Date().toLocaleString("pt-BR", {
              timeZone: "America/Sao_Paulo",
              day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
            });
            const texto = envio.wamid
              ? `🤖 PDF da síntese enviado por WhatsApp — ${quando}\n`
                + `(envio automático; não aparece na conversa acima)`
              : `⚠️ FALHA ao enviar o PDF — ${quando}\n`
                + `HTTP ${envio.http}${envio.erro ? ": " + envio.erro : ""}`;
            registro.nota_kommo = await registrarNoKommo(env, leadId, texto);
          } else {
            registro.envio = { pulado: decisao.motivo };
          }
        }
      }

      const chave = `ev:${(1e13 - Date.now()).toString()}:${crypto.randomUUID().slice(0, 8)}`;
      await env.EVENTOS.put(chave, JSON.stringify(registro), { expirationTtl: 7 * 24 * 3600 });

      // 200 é obrigatório: o Kommo desativa webhook que não responde.
      return new Response("ok", { status: 200 });
    }

    if (url.pathname === "/ultimos") {
      const lista = await env.EVENTOS.list({ prefix: "ev:", limit: 50 });
      const itens = [];
      for (const k of lista.keys) {
        const v = await env.EVENTOS.get(k.name);
        if (v) itens.push(JSON.parse(v));
      }
      return new Response(JSON.stringify({ total: itens.length, eventos: itens }, null, 1), {
        headers: { "content-type": "application/json; charset=utf-8" },
      });
    }

    if (url.pathname === "/limpar") {
      const lista = await env.EVENTOS.list({ prefix: "ev:", limit: 1000 });
      for (const k of lista.keys) await env.EVENTOS.delete(k.name);
      return new Response(`apagados: ${lista.keys.length}`);
    }

    return new Response(AJUDA, { headers: { "content-type": "text/plain; charset=utf-8" } });
  },
};
