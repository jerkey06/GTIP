import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

/**
 * Filtros, orden y página guardados en la URL (UI §4.7): el botón Atrás funciona y
 * las búsquedas se pueden compartir.
 */
export function useUrlState() {
  const [params, setParams] = useSearchParams()

  const get = useCallback((key: string, fallback = '') => params.get(key) ?? fallback, [params])

  const update = useCallback(
    (changes: Record<string, string | number | boolean | null | undefined>, resetPage = true) => {
      setParams(
        (current) => {
          const next = new URLSearchParams(current)
          for (const [key, value] of Object.entries(changes)) {
            if (value === null || value === undefined || value === '' || value === false) next.delete(key)
            else next.set(key, String(value))
          }
          if (resetPage && !('page' in changes)) next.delete('page')
          return next
        },
        { replace: false },
      )
    },
    [setParams],
  )

  const clear = useCallback(() => setParams(new URLSearchParams()), [setParams])

  const page = Math.max(1, Number(params.get('page')) || 1)
  const pageSize = [20, 50, 100].includes(Number(params.get('page_size')))
    ? Number(params.get('page_size'))
    : 20

  return { params, get, update, clear, page, pageSize }
}
