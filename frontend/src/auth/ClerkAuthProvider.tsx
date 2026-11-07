import { useAuth as useClerkAuth, useClerk, useUser } from '@clerk/clerk-react'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setTokenProvider, setUnauthorizedHandler } from '../api/client'
import { getMe } from '../api/endpoints'
import type { User } from '../api/types'
import { AuthContext, type AuthContextValue, type SessionStatus } from './context'

/** Misma interfaz que AuthProvider, pero la sesión la gestiona Clerk (Google, GitHub, correo). */
export function ClerkAuthProvider({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, getToken } = useClerkAuth()
  const { user: clerkUser } = useUser()
  const { signOut } = useClerk()
  // Perfil de la API junto con el usuario de Clerk al que pertenece (evita mostrar uno ajeno).
  const [loaded, setLoaded] = useState<{ clerkId: string; profile: User } | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  // Cada petición a la API lleva un token de Clerk recién emitido.
  useEffect(() => {
    if (!isSignedIn) return
    setTokenProvider(() => getToken())
    return () => setTokenProvider(null)
  }, [isSignedIn, getToken])

  const logout = useCallback(
    (message?: string) => {
      setNotice(message ?? null)
      void signOut()
    },
    [signOut],
  )

  useEffect(() => {
    setUnauthorizedHandler(() => logout('Tu sesión ha caducado. Vuelve a iniciar sesión.'))
    return () => setUnauthorizedHandler(null)
  }, [logout])

  // Con sesión de Clerk, la API crea o devuelve la cuenta local (/auth/me).
  const clerkId = clerkUser?.id
  useEffect(() => {
    if (!isLoaded || !isSignedIn || !clerkId) return
    const controller = new AbortController()
    // El proveedor de token se instala en el efecto anterior; esperamos un ciclo.
    const timer = setTimeout(() => {
      getMe(controller.signal)
        .then((profile) => setLoaded({ clerkId, profile }))
        .catch(() => {
          if (!controller.signal.aborted) void signOut()
        })
    }, 0)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [isLoaded, isSignedIn, clerkId, signOut])

  const me = loaded && loaded.clerkId === clerkId ? loaded.profile : null
  const status: SessionStatus = !isLoaded
    ? 'checking'
    : !isSignedIn
      ? 'anonymous'
      : me
        ? 'authenticated'
        : 'checking'

  // El nombre visible viene de Clerk; el resto del perfil, de la API.
  const user = useMemo<User | null>(() => {
    if (!me) return null
    const display =
      clerkUser?.username ??
      clerkUser?.fullName ??
      clerkUser?.primaryEmailAddress?.emailAddress?.split('@')[0] ??
      me.username
    return { ...me, username: display }
  }, [me, clerkUser])

  const unsupported = useCallback(async () => {
    throw new Error('El acceso se hace con Clerk (Google, GitHub o correo).')
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, notice, login: unsupported, loginWithToken: unsupported, logout }),
    [status, user, notice, unsupported, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
