import { createContext, useContext } from 'react'
import type { User } from '../api/types'

export type SessionStatus = 'checking' | 'authenticated' | 'anonymous'

export interface AuthContextValue {
  status: SessionStatus
  user: User | null
  /** Mensaje para la pantalla de login (p. ej. sesión caducada). */
  notice: string | null
  login: (username: string, password: string) => Promise<void>
  /** Cierra el login social: guarda el token que entregó la API y carga el perfil. */
  loginWithToken: (accessToken: string) => Promise<void>
  logout: (notice?: string) => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return value
}
