// Cliente HTTP de la API. Siempre usa rutas relativas /api/v1 (el proxy de Vite, de
// Cloudflare Pages o de nginx las reenvía al backend).

const BASE = '/api/v1'
const TOKEN_KEY = 'gtip.token'

// Token en sessionStorage: sobrevive a recargar la pestaña pero no al cerrarla, y no se
// comparte entre pestañas (decisión del UI §3.2 / ADD §22.3). Nunca en localStorage.
let token: string | null = readStoredToken()
let onUnauthorized: (() => void) | null = null
// Con Clerk el token de sesión dura ~60 s: se pide uno vigente en cada petición.
let tokenProvider: (() => Promise<string | null>) | null = null

function readStoredToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function getToken(): string | null {
  return token
}

export function setToken(value: string | null): void {
  token = value
  try {
    if (value) sessionStorage.setItem(TOKEN_KEY, value)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    // Sin almacenamiento (modo privado estricto): el token queda solo en memoria.
  }
}

export function setTokenProvider(provider: (() => Promise<string | null>) | null): void {
  tokenProvider = provider
}

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

export class ApiError extends Error {
  readonly status: number
  readonly detail: string | null
  readonly body: Record<string, unknown> | null

  constructor(status: number, detail: string | null, body: Record<string, unknown> | null) {
    super(detail ?? `HTTP ${status}`)
    this.status = status
    this.detail = detail
    this.body = body
  }
}

type Query = Record<string, string | number | boolean | null | undefined>

function buildUrl(path: string, query?: Query): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value))
  }
  const qs = params.toString()
  return `${BASE}${path}${qs ? `?${qs}` : ''}`
}

function detailFrom(body: unknown): string | null {
  if (!body || typeof body !== 'object') return null
  const detail = (body as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  // Errores de validación de FastAPI: [{loc, msg, type}]
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: unknown }
    if (typeof first.msg === 'string') return first.msg.replace(/^Value error, /, '')
  }
  return null
}

export async function request<T>(
  method: 'GET' | 'POST',
  path: string,
  options: { query?: Query; body?: unknown; signal?: AbortSignal; auth?: boolean } = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (options.auth !== false) {
    const bearer = tokenProvider ? await tokenProvider() : token
    if (bearer) headers.Authorization = `Bearer ${bearer}`
  }

  let response: Response
  try {
    response = await fetch(buildUrl(path, options.query), {
      method,
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, null, null)
  }

  let body: unknown = null
  const text = await response.text()
  if (text) {
    try {
      body = JSON.parse(text)
    } catch {
      body = null
    }
  }

  if (!response.ok) {
    if (response.status === 401 && options.auth !== false) onUnauthorized?.()
    throw new ApiError(
      response.status,
      detailFrom(body),
      body && typeof body === 'object' ? (body as Record<string, unknown>) : null,
    )
  }
  return body as T
}

export const api = {
  get: <T>(path: string, query?: Query, signal?: AbortSignal) =>
    request<T>('GET', path, { query, signal }),
  post: <T>(path: string, body: unknown) => request<T>('POST', path, { body }),
}
