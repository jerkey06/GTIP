import { useEffect, useState } from 'react'
import { Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { getAuthProviders, type AuthProviders } from '../api/endpoints'
import { useAuth } from '../auth/context'
import { errorMessage } from '../lib/errors'

function loginError(error: unknown): string {
  if (error instanceof ApiError) {
    // Mismo mensaje para usuario inexistente y contraseña errónea (UI P-01).
    if (error.status === 401) return 'Usuario o contraseña incorrectos.'
    if (error.status === 403) return 'Esta cuenta está desactivada.'
    if (error.status === 429) return 'Demasiados intentos. Espera un momento.'
  }
  return errorMessage(error)
}

const OAUTH_ERRORS: Record<string, string> = {
  oauth_denied: 'Cancelaste el inicio de sesión.',
  oauth_state: 'La sesión de inicio expiró. Vuelve a intentarlo.',
  oauth_failed: 'No se pudo validar tu cuenta con el proveedor. Inténtalo de nuevo.',
  oauth_not_configured: 'Este método de acceso no está disponible.',
  account_disabled: 'Esta cuenta está desactivada.',
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20 20 20 20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z" />
      <path fill="#FF3D00" d="M6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 16.318 4 9.656 8.337 6.306 14.691z" />
      <path fill="#4CAF50" d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0124 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z" />
      <path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 01-4.087 5.571l.003-.002 6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z" />
    </svg>
  )
}

function GithubIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  )
}

const SOCIAL = [
  { key: 'google', label: 'Continuar con Google', Icon: GoogleIcon },
  { key: 'github', label: 'Continuar con GitHub', Icon: GithubIcon },
] as const

/** P-01. Entra con usuario y contraseña o con Google/GitHub (la primera vez crea la cuenta). */
export function LoginPage() {
  const { status, login, notice } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [providers, setProviders] = useState<AuthProviders | null>(null)
  const [params] = useSearchParams()
  const shownError = error ?? OAUTH_ERRORS[params.get('error') ?? ''] ?? null

  useEffect(() => {
    const controller = new AbortController()
    getAuthProviders(controller.signal)
      .then(setProviders)
      .catch(() => setProviders(null)) // sin la API solo se ofrece el formulario
    return () => controller.abort()
  }, [])

  if (status === 'authenticated') return <Navigate to={from} replace />

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSending(true)
    setError(null)
    try {
      await login(username, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(loginError(err))
      setSending(false)
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <div className="login-brand">
          <img src="/logo.svg" alt="" width="34" height="52" />
          <div>
            <strong>GTIP</strong>
            <span>Global Threat Intelligence Platform</span>
          </div>
        </div>
        {notice && !error && <p className="notice notice-warning">{notice}</p>}
        <label className="field">
          <span>Usuario</span>
          <input
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            maxLength={64}
            autoFocus
          />
        </label>
        <label className="field">
          <span>Contraseña</span>
          <span className="password-input">
            <input
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              maxLength={256}
            />
            <button
              type="button"
              className="btn btn-small btn-ghost"
              onClick={() => setShowPassword((v) => !v)}
              aria-pressed={showPassword}
            >
              {showPassword ? 'Ocultar' : 'Mostrar'}
            </button>
          </span>
        </label>
        {shownError && (
          <p className="form-error" role="alert">
            {shownError}
          </p>
        )}
        <button type="submit" className="btn btn-primary btn-block" disabled={sending}>
          {sending ? 'Entrando…' : 'Iniciar sesión'}
        </button>
        {providers && SOCIAL.some((s) => providers[s.key]) && (
          <>
            <p className="login-divider">o continúa con</p>
            <div className="social-buttons">
              {SOCIAL.filter((s) => providers[s.key]).map(({ key, label, Icon }) => (
                // Enlace normal (no fetch): el navegador debe seguir la redirección al proveedor.
                <a key={key} className="btn btn-block" href={`/api/v1/auth/oauth/${key}/login`}>
                  <Icon />
                  {label}
                </a>
              ))}
            </div>
            <p className="login-hint">
              La primera vez que entres con Google o GitHub se crea tu cuenta.
            </p>
          </>
        )}
      </form>
    </div>
  )
}
