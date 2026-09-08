// MCP Análise Macro — Cartas das Gestoras
//
// Servidor MCP remoto que expõe as sínteses semanais das cartas das gestoras
// brasileiras e os exercícios em Python que as acompanham. Diferente do
// `nucleos-mcp` (authless), este é **autenticado**: o conteúdo é do produto de
// assinatura (R$ 97/mês), e cada chamada exige um token de assinante ativo.
//
// Rotas: POST /mcp (Streamable HTTP) e /sse (legado).

import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

// --- Tipos -----------------------------------------------------------------

type Digest = {
  data: string;              // ISO, data da edição
  gestoras: string[];        // gestoras cobertas nesta edição
  conceito?: string;         // conceito do exercício da semana
  resumo_executivo: string;
  markdown: string;          // síntese completa
  exercicio?: string;        // exercício em Python, quando houver
  fontes: { gestora: string; titulo: string; url: string }[];
};

type Catalogo = { atualizado_em: string; edicoes: Digest[] };

interface Env {
  ASSINANTES: KVNamespace;
  DIGESTS_URL?: string;
}

// Fonte viva: artefato publicado pelo pipeline a cada execução, no mesmo
// espírito do release `dashboard-dados` do nucleos-mcp.
const DATA_URL_PADRAO =
  "https://github.com/vitorwilher/cartas-de-gestoras/releases/download/digests/catalogo.json";
const TTL_MS = 30 * 60 * 1000; // 30 min por isolate

let cache: { at: number; data: Catalogo } | null = null;

async function carregar(env: Env): Promise<Catalogo> {
  const agora = Date.now();
  if (cache && agora - cache.at < TTL_MS) return cache.data;
  const url = env.DIGESTS_URL || DATA_URL_PADRAO;
  try {
    const res = await fetch(url, { cf: { cacheTtl: 900, cacheEverything: true } });
    if (res.ok) {
      const data = (await res.json()) as Catalogo;
      if (data?.edicoes) {
        cache = { at: agora, data };
        return data;
      }
    }
  } catch {
    // rede indisponível — preserva o último bom, se houver
  }
  if (!cache) cache = { at: agora, data: { atualizado_em: "", edicoes: [] } };
  return cache.data;
}

// --- Assinatura ------------------------------------------------------------
//
// O token do assinante chega no header `Authorization: Bearer <token>` e é
// conferido contra o KV, que o webhook do WooCommerce mantém. Guardamos o
// STATUS, não o dado pessoal: a chave é o token, o valor diz se está ativa.

type Assinatura = { ativo: boolean; expira_em?: string; plano?: string };

async function assinaturaValida(env: Env, token: string | null): Promise<boolean> {
  if (!token) return false;
  const bruto = await env.ASSINANTES.get(`token:${token}`);
  if (!bruto) return false;
  try {
    const a = JSON.parse(bruto) as Assinatura;
    if (!a.ativo) return false;
    if (a.expira_em && Date.parse(a.expira_em) < Date.now()) return false;
    return true;
  } catch {
    return false;
  }
}

function tokenDoRequest(request: Request): string | null {
  const auth = request.headers.get("authorization");
  if (auth?.toLowerCase().startsWith("bearer ")) return auth.slice(7).trim();
  return null;
}

// --- Servidor MCP ----------------------------------------------------------

export class CartasMCP extends McpAgent<Env> {
  server = new McpServer(
    {
      name: "cartas-gestoras",
      title: "MCP Análise Macro — Cartas das Gestoras",
      version: "0.1.0",
    },
    {
      instructions: [
        "Servidor das sínteses semanais das cartas das 12 maiores gestoras brasileiras",
        "(Dynamo, IP, Alaska, Kapitalo, Adam, Legacy, Bahia, Occam, JGP, Kinea, NEO, Dahlia),",
        "com o exercício em Python que destrincha tecnicamente o mecanismo da semana.",
        "",
        "Ao usar:",
        "- `cartas_ultima_edicao` dá o panorama da semana corrente; `cartas_listar_edicoes`",
        "  mostra o histórico e `cartas_edicao` recupera uma edição específica por data.",
        "- `cartas_exercicio` devolve o exercício em Python de uma edição — é o material",
        "  que mostra COMO verificar a tese, não apenas o que a gestora disse.",
        "- `cartas_por_gestora` filtra o histórico por uma gestora.",
        "- As sínteses são geradas a partir das cartas públicas das gestoras; o link do",
        "  PDF original acompanha cada citação. Ao citar um número, prefira remeter à carta",
        "  original — a síntese é interpretação, não substitui a fonte.",
        "- A cadência é semanal (terças), mas as cartas não são todas mensais: uma edição",
        "  cobre apenas as gestoras que publicaram algo novo naquela janela.",
      ].join("\n"),
    },
  );

  async init() {
    const env = this.env;

    // 1) Última edição -----------------------------------------------------
    this.server.tool(
      "cartas_ultima_edicao",
      "Retorna a síntese mais recente: gestoras cobertas, resumo executivo e o texto completo da análise.",
      {},
      async () => {
        const { edicoes } = await carregar(env);
        if (!edicoes.length) {
          return { content: [{ type: "text", text: "Nenhuma edição disponível ainda." }] };
        }
        const e = edicoes[0];
        return {
          content: [{
            type: "text",
            text: [
              `**Edição de ${e.data}**`,
              `**Gestoras cobertas:** ${e.gestoras.join(", ")}`,
              e.conceito ? `**Conceito do exercício:** ${e.conceito}` : "",
              "",
              e.markdown,
            ].filter(Boolean).join("\n"),
          }],
        };
      },
    );

    // 2) Histórico ---------------------------------------------------------
    this.server.tool(
      "cartas_listar_edicoes",
      "Lista as edições disponíveis, da mais recente para a mais antiga, com as gestoras cobertas em cada uma.",
      {},
      async () => {
        const { edicoes, atualizado_em } = await carregar(env);
        const linhas = edicoes.map(
          (e) => `- **${e.data}** — ${e.gestoras.join(", ")}${e.conceito ? ` · exercício: ${e.conceito}` : ""}`,
        );
        return {
          content: [{
            type: "text",
            text: [
              `**${edicoes.length} edição(ões)**${atualizado_em ? ` · catálogo atualizado em ${atualizado_em}` : ""}`,
              "",
              ...linhas,
            ].join("\n"),
          }],
        };
      },
    );

    // 3) Edição específica -------------------------------------------------
    this.server.tool(
      "cartas_edicao",
      "Recupera uma edição específica pela data (AAAA-MM-DD), com a síntese completa e os links das cartas originais.",
      { data: z.string().describe("Data da edição no formato AAAA-MM-DD") },
      async ({ data }) => {
        const { edicoes } = await carregar(env);
        const e = edicoes.find((x) => x.data === data);
        if (!e) {
          const proximas = edicoes.slice(0, 5).map((x) => x.data).join(", ");
          return {
            content: [{
              type: "text",
              text: `Não há edição em ${data}. Edições recentes: ${proximas || "nenhuma"}.`,
            }],
          };
        }
        const fontes = e.fontes.map((f) => `- ${f.gestora} — ${f.titulo}: ${f.url}`).join("\n");
        return {
          content: [{
            type: "text",
            text: [e.markdown, "", "## Cartas originais", fontes].join("\n"),
          }],
        };
      },
    );

    // 4) Exercício ---------------------------------------------------------
    this.server.tool(
      "cartas_exercicio",
      "Devolve o exercício em Python de uma edição: o código que verifica, com dados reais, o mecanismo por trás das teses da semana. Omita a data para obter o mais recente.",
      { data: z.string().optional().describe("Data da edição (AAAA-MM-DD); omita para a mais recente") },
      async ({ data }) => {
        const { edicoes } = await carregar(env);
        const e = data ? edicoes.find((x) => x.data === data) : edicoes.find((x) => x.exercicio);
        if (!e?.exercicio) {
          return {
            content: [{
              type: "text",
              text: data
                ? `A edição de ${data} não tem exercício.`
                : "Nenhuma edição com exercício disponível.",
            }],
          };
        }
        return {
          content: [{
            type: "text",
            text: `**Exercício da edição de ${e.data}**${e.conceito ? ` — ${e.conceito}` : ""}\n\n${e.exercicio}`,
          }],
        };
      },
    );

    // 5) Por gestora -------------------------------------------------------
    this.server.tool(
      "cartas_por_gestora",
      "Mostra em quais edições uma gestora apareceu, para acompanhar a evolução da tese dela ao longo do tempo.",
      { gestora: z.string().describe("Nome (ou parte do nome) da gestora") },
      async ({ gestora }) => {
        const { edicoes } = await carregar(env);
        const alvo = gestora.toLowerCase();
        const achadas = edicoes.filter((e) =>
          e.gestoras.some((g) => g.toLowerCase().includes(alvo)),
        );
        if (!achadas.length) {
          const todas = [...new Set(edicoes.flatMap((e) => e.gestoras))].sort();
          return {
            content: [{
              type: "text",
              text: `Nenhuma edição cobre "${gestora}". Gestoras no histórico: ${todas.join(", ") || "nenhuma"}.`,
            }],
          };
        }
        const linhas = achadas.map((e) => `- **${e.data}**: ${e.resumo_executivo}`);
        return {
          content: [{
            type: "text",
            text: [`**${gestora}** aparece em ${achadas.length} edição(ões):`, "", ...linhas].join("\n"),
          }],
        };
      },
    );
  }
}

// --- Roteamento ------------------------------------------------------------

const NAO_AUTORIZADO = JSON.stringify({
  error: "assinatura_invalida",
  message:
    "Este servidor exige assinatura ativa. Configure o header Authorization: Bearer <seu-token>. " +
    "Assine em https://analisemacro.com.br/cartas-de-gestoras",
});

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const url = new URL(request.url);

    if (url.pathname === "/" || url.pathname === "/health") {
      const { edicoes, atualizado_em } = await carregar(env);
      return new Response(
        [
          "MCP Análise Macro — Cartas das Gestoras",
          `Edições disponíveis: ${edicoes.length}${atualizado_em ? ` | Atualizado: ${atualizado_em}` : ""}`,
          `Conector MCP em: ${url.origin}/mcp (exige Authorization: Bearer <token>)`,
        ].join("\n"),
        { headers: { "content-type": "text/plain; charset=utf-8" } },
      );
    }

    // Tudo além do health check exige assinatura ativa.
    if (!(await assinaturaValida(env, tokenDoRequest(request)))) {
      return new Response(NAO_AUTORIZADO, {
        status: 401,
        headers: {
          "content-type": "application/json; charset=utf-8",
          "www-authenticate": 'Bearer realm="cartas-gestoras"',
        },
      });
    }

    if (url.pathname === "/mcp") {
      return CartasMCP.serve("/mcp").fetch(request, env as never, ctx);
    }
    if (url.pathname === "/sse" || url.pathname === "/sse/message") {
      return CartasMCP.serveSSE("/sse").fetch(request, env as never, ctx);
    }
    return new Response("Not found", { status: 404 });
  },
};
