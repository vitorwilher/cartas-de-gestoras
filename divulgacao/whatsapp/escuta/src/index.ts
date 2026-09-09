// wa-escuta — FASE 1 do plano: só OUVIR.
//
// Recebe o webhook `add_talk` do Kommo, guarda o payload no KV e permite lê-lo
// depois. Não responde mensagem, não fala com a Meta, não altera nada no Kommo.
//
// A leitura do resultado é feita AQUI (GET /ultimos), e não no Kommo — o IP do
// Vitor foi bloqueado em 08/09 por excesso de requisições àquela API.

interface Env {
  EVENTOS: KVNamespace;
}

const HTML_AJUDA = `wa-escuta — fase 1 (só ouve)

POST /kommo     recebe o webhook do Kommo e guarda o payload
GET  /ultimos   lista o que chegou (mais recente primeiro)
GET  /limpar    apaga o que foi guardado

Nada aqui envia mensagem nem altera configuração.`;

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // --- recebe o evento -----------------------------------------------
    // O Kommo EXIGE barra final na URL (sem ela: "Invalid URL" no cadastro).
    if (url.pathname === "/kommo" || url.pathname === "/kommo/") {
      // O Kommo manda form-urlencoded, não JSON. Guardamos o corpo cru para
      // não perder nada por causa de parsing errado.
      let corpo = "";
      try {
        corpo = await request.text();
      } catch {
        corpo = "(corpo ilegível)";
      }
      const registro = {
        recebido_em: new Date().toISOString(),
        metodo: request.method,
        content_type: request.headers.get("content-type") ?? "",
        corpo,
      };
      // A chave começa com o timestamp invertido, então o mais recente vem
      // primeiro numa listagem alfabética.
      const chave = `ev:${(1e13 - Date.now()).toString()}:${crypto.randomUUID().slice(0, 8)}`;
      await env.EVENTOS.put(chave, JSON.stringify(registro), {
        expirationTtl: 7 * 24 * 3600,   // some sozinho em 7 dias
      });

      // 200 é obrigatório: o Kommo desativa o webhook que não responde.
      return new Response("ok", { status: 200 });
    }

    // --- lê o que chegou -----------------------------------------------
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

    return new Response(HTML_AJUDA, {
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  },
};
