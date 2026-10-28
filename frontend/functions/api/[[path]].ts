// Pages Function: reenvía /api/* al backend FastAPI para que el navegador use un solo
// dominio y no haga falta CORS (ADR-04). BACKEND_URL se configura en el proyecto de
// Cloudflare Pages, por ejemplo https://api.ejemplo.com
interface Env {
  BACKEND_URL?: string
}

export const onRequest = async ({ request, env }: { request: Request; env: Env }) => {
  if (!env.BACKEND_URL) {
    return Response.json({ detail: 'Backend no configurado (BACKEND_URL)' }, { status: 503 })
  }

  const url = new URL(request.url)
  const target = new URL(url.pathname + url.search, env.BACKEND_URL)
  return fetch(new Request(target, request))
}
