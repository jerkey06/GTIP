// Pages Function: reenvía /api/* al backend FastAPI para que el navegador use un solo
// dominio y no haga falta CORS (ADR-04). BACKEND_URL se configura en el proyecto de
// Cloudflare Pages, por ejemplo https://api.ejemplo.com
interface Env {
  BACKEND_URL?: string
}

// El plan gratuito de Render duerme el servicio tras ~15 min sin tráfico y tarda hasta
// ~1 min en despertar; mientras tanto responde 502/503/504. Las lecturas (GET/HEAD) se
// reintentan aquí hasta que el backend contesta, en vez de mostrar un error al usuario.
const WAKING_STATUSES = new Set([502, 503, 504])
const MAX_WAIT_MS = 90_000
const RETRY_DELAYS_MS = [1_000, 2_000, 3_000, 5_000]

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export const onRequest = async ({ request, env }: { request: Request; env: Env }) => {
  if (!env.BACKEND_URL) {
    return Response.json({ detail: 'Backend no configurado (BACKEND_URL)' }, { status: 503 })
  }

  const url = new URL(request.url)
  const target = new URL(url.pathname + url.search, env.BACKEND_URL)
  // redirect: 'manual': el 302 hacia Google/GitHub debe llegar al navegador, no seguirlo aquí.
  const forward = () => fetch(new Request(target, request), { redirect: 'manual' })

  // Las escrituras no se reintentan: podrían ejecutarse dos veces.
  if (request.method !== 'GET' && request.method !== 'HEAD') return forward()

  const deadline = Date.now() + MAX_WAIT_MS
  for (let attempt = 0; ; attempt++) {
    let response: Response | null = null
    try {
      response = await forward()
      if (!WAKING_STATUSES.has(response.status)) return response
    } catch {
      // Error de red hacia el backend: se trata igual que un 502 mientras quede tiempo.
    }

    const delay = RETRY_DELAYS_MS[Math.min(attempt, RETRY_DELAYS_MS.length - 1)]
    if (request.signal.aborted || Date.now() + delay >= deadline) {
      return (
        response ??
        Response.json({ detail: 'El servidor no responde. Inténtalo de nuevo.' }, { status: 502 })
      )
    }
    await response?.body?.cancel()
    await sleep(delay)
  }
}
