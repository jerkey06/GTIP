import { useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from './context'

/** Acciones que exigen sesión (solicitar ingestas, buscar): sin sesión llevan al login y vuelven. */
export function useLoginGate() {
  const { status } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  return useCallback(
    (action: () => void) => () => {
      if (status === 'authenticated') action()
      else navigate('/login', { state: { from: location.pathname + location.search } })
    },
    [status, navigate, location.pathname, location.search],
  )
}
