import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import { requestIngestion } from '../api/endpoints'
import type { IngestionRun, Source } from '../api/types'
import { errorMessage } from '../lib/errors'

/** M-01: modal «Solicitar ingesta manual» (UI §7). */
export function IngestionModal({
  sources,
  initialSourceId,
  onClose,
  onCreated,
}: {
  sources: Source[]
  initialSourceId?: number
  onClose: () => void
  onCreated: (run: IngestionRun) => void
}) {
  const enabled = sources.filter((s) => s.is_enabled)
  const [sourceId, setSourceId] = useState<number | undefined>(initialSourceId ?? enabled[0]?.id)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<{ message: string; activeRunId?: number } | null>(null)
  const dialogRef = useRef<HTMLDialogElement>(null)
  const source = sources.find((s) => s.id === sourceId)

  useEffect(() => {
    dialogRef.current?.showModal()
  }, [])

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!sourceId) return
    setSending(true)
    setError(null)
    try {
      onCreated(await requestIngestion(sourceId))
    } catch (err) {
      const activeRunId =
        err instanceof ApiError && typeof err.body?.active_run_id === 'number' ? err.body.active_run_id : undefined
      setError({
        message:
          err instanceof ApiError && err.status === 403
            ? 'No tienes permiso para solicitar ingestas.'
            : errorMessage(err),
        activeRunId,
      })
      setSending(false)
    }
  }

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose} aria-labelledby="ingest-title">
      <form onSubmit={submit}>
        <h2 id="ingest-title">Solicitar ingesta manual</h2>
        {initialSourceId === undefined && (
          <label className="field">
            <span>Fuente</span>
            <select value={sourceId ?? ''} onChange={(e) => setSourceId(Number(e.target.value))}>
              {enabled.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
        )}
        {source ? (
          <p>
            Se pedirá al worker que sincronice «{source.name}». La ingesta se ejecuta en segundo plano; puedes
            seguir usando la aplicación.
          </p>
        ) : (
          <p>No hay fuentes habilitadas.</p>
        )}
        {error && (
          <p className="form-error" role="alert">
            {error.message}{' '}
            {error.activeRunId && <Link to={`/ingestas/${error.activeRunId}`}>Ver esa ejecución</Link>}
          </p>
        )}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={!source || sending}>
            {sending ? 'Solicitando…' : 'Solicitar ingesta'}
          </button>
        </div>
      </form>
    </dialog>
  )
}

/** Aviso tras solicitar una ingesta, con enlace al progreso. */
export function IngestionNotice({ run, onDismiss }: { run: IngestionRun; onDismiss: () => void }) {
  return (
    <div className="notice notice-success" role="status">
      <span>
        Ingesta de {run.source.name} solicitada. <Link to={`/ingestas/${run.id}`}>Ver progreso</Link>
      </span>
      <button type="button" className="btn btn-small btn-ghost" onClick={onDismiss} aria-label="Cerrar aviso">
        ×
      </button>
    </div>
  )
}
