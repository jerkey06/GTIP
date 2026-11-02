import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
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

/** P-01. Sin registro ni recuperación de contraseña: las cuentas se crean en el backend. */
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
          <img src="/favicon.svg" alt="" width="44" height="44" />
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
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-primary btn-block" disabled={sending}>
          {sending ? 'Entrando…' : 'Iniciar sesión'}
        </button>
      </form>
    </div>
  )
}
