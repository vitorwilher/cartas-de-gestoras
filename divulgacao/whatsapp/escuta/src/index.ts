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
const TAG_PROJETO = 22406993;   // "Mercado Financeiro"

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
