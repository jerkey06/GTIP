import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { getToken, setToken, setUnauthorizedHandler } from '../api/client'
import { getMe, login as apiLogin } from '../api/endpoints'
import type { User } from '../api/types'
import { AuthContext, type AuthContextValue, type SessionStatus } from './context'

const EXPIRED = 'Tu sesión ha caducado. Vuelve a iniciar sesión.'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<SessionStatus>(getToken() ? 'checking' : 'anonymous')
  const [notice, setNotice] = useState<string | null>(null)

  const logout = useCallback((message?: string) => {
    setToken(null)
    setUser(null)
    setStatus('anonymous')
    setNotice(message ?? null)
  }, [])

  // Cualquier 401 de la API cierra la sesión local (UI §3.2).
  useEffect(() => {
    setUnauthorizedHandler(() => logout(EXPIRED))
    return () => setUnauthorizedHandler(null)
  }, [logout])

  // Al recargar con un token guardado, se comprueba que siga siendo válido.
  useEffect(() => {
    if (status !== 'checking') return
    const controller = new AbortController()
    getMe(controller.signal)
      .then((me) => {
        setUser(me)
        setStatus('authenticated')
      })
      .catch(() => {
        if (!controller.signal.aborted) logout()
      })
    return () => controller.abort()
  }, [status, logout])

  const login = useCallback(async (username: string, password: string) => {
    const token = await apiLogin(username, password)
    setToken(token.access_token)
    const me = await getMe()
    setUser(me)
    setNotice(null)
    setStatus('authenticated')
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, notice, login, logout }),
    [status, user, notice, login, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
