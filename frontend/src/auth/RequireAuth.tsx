import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Spinner } from '../components/DataState'
import { useAuth } from './context'

/** Ruta protegida: sin sesión, lleva a /login recordando a dónde se quería ir (UI §3.2). */
export function RequireAuth() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'checking') {
    return (
      <div className="fullscreen-center">
        <Spinner label="Comprobando la sesión…" />
      </div>
    )
  }
  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  }
  return <Outlet />
}
