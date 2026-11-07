import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'
import { Spinner } from '../components/DataState'

/** Destino del login con Google/GitHub: la API entrega el token en el fragmento (#access_token). */
export function AuthCallbackPage() {
  const { loginWithToken } = useAuth()
  const navigate = useNavigate()
  const [token] = useState(() =>
    new URLSearchParams(window.location.hash.slice(1)).get('access_token'),
  )
  const [failed, setFailed] = useState(token === null)
  const started = useRef(false)

  useEffect(() => {
    // El token no debe quedarse en la barra de direcciones ni en el historial.
    window.history.replaceState(null, '', window.location.pathname)
    if (!token || started.current) return // StrictMode ejecuta el efecto dos veces
    started.current = true
    loginWithToken(token)
      .then(() => navigate('/', { replace: true }))
      .catch(() => setFailed(true))
  }, [token, loginWithToken, navigate])

  if (failed) {
    return (
      <div className="fullscreen-center">
        <p className="form-error" role="alert">
          No se pudo completar el inicio de sesión. <Link to="/login">Volver a intentarlo</Link>
        </p>
      </div>
    )
  }
  return (
    <div className="fullscreen-center">
      <Spinner label="Iniciando sesión…" />
    </div>
  )
}
