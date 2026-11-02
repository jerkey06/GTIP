import { useCallback, useEffect, useRef, useState } from 'react'

export interface ApiState<T> {
  data: T | undefined
  error: unknown
  loading: boolean
  reload: () => void
}

/**
 * Carga datos de la API y vuelve a cargarlos cuando cambian las dependencias.
 * Cancela la petición anterior para que una respuesta lenta no pise a una nueva.
 * Con `pollMs`, vuelve a consultar mientras `shouldPoll(data)` sea verdadero.
 */
export function useApi<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: readonly unknown[],
  options: { pollMs?: number; shouldPoll?: (data: T) => boolean; enabled?: boolean } = {},
): ApiState<T> {
  const [data, setData] = useState<T>()
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(options.enabled !== false)
  const [version, setVersion] = useState(0)
  const fetcherRef = useRef(fetcher)
  const optionsRef = useRef(options)

  useEffect(() => {
    fetcherRef.current = fetcher
    optionsRef.current = options
  })

  const reload = useCallback(() => setVersion((v) => v + 1), [])
  const enabled = options.enabled !== false
  // Las dependencias son valores simples (ids, parámetros de la URL).
  const depsKey = JSON.stringify(deps)

  useEffect(() => {
    if (!enabled) return
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    let first = true

    const load = async () => {
      if (first) setLoading(true)
      try {
        const result = await fetcherRef.current(controller.signal)
        if (controller.signal.aborted) return
        setData(result)
        setError(null)
        const { pollMs, shouldPoll } = optionsRef.current
        if (pollMs && shouldPoll?.(result)) timer = setTimeout(load, pollMs)
      } catch (err) {
        if (controller.signal.aborted) return
        setError(err)
      } finally {
        if (!controller.signal.aborted && first) setLoading(false)
        first = false
      }
    }
    void load()
    return () => {
      controller.abort()
      if (timer) clearTimeout(timer)
    }
  }, [depsKey, version, enabled])

  return { data, error, loading, reload }
}
