import type { ReactNode } from 'react'
import { errorMessage } from '../lib/errors'

export function Spinner({ label = 'Cargando…' }: { label?: string }) {
  return (
    <div className="spinner" role="status">
      <span className="spinner-dot" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div className="state state-error" role="alert">
      <p>{errorMessage(error)}</p>
      {onRetry && (
        <button type="button" className="btn btn-small" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  )
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="state state-empty">{children}</div>
}

/**
 * Los cuatro estados de un bloque que carga datos (UI §4.1): cargando, error, vacío
 * y con datos. Un bloque con error no afecta al resto de la pantalla.
 */
export function DataBlock<T>({
  state,
  isEmpty,
  empty,
  children,
}: {
  state: { data: T | undefined; error: unknown; loading: boolean; reload: () => void }
  isEmpty?: (data: T) => boolean
  empty?: ReactNode
  children: (data: T) => ReactNode
}) {
  if (state.loading && state.data === undefined) return <Spinner />
  if (state.error && state.data === undefined) {
    return <ErrorState error={state.error} onRetry={state.reload} />
  }
  if (state.data === undefined) return null
  if (isEmpty?.(state.data)) return <EmptyState>{empty}</EmptyState>
  return <>{children(state.data)}</>
}
