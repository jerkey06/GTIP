/** Clave publicable de Clerk (es pública). Sin ella la app usa el login propio de la API. */
export const CLERK_PUBLISHABLE_KEY: string | undefined =
  import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || undefined
