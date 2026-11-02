import { Link, useParams } from 'react-router-dom'
import { getIngestion } from '../api/endpoints'
import type { IngestionRun } from '../api/types'
import { StatusBadge, TriggerText } from '../components/Badges'
import { ErrorState, Spinner } from '../components/DataState'
import { DateText } from '../components/DateText'
import { useApi } from '../hooks/useApi'
import { PageHeader } from '../layout/AppLayout'
import { isNotFound } from '../lib/errors'
import { formatDuration, formatNumber } from '../lib/format'
import { isActiveStatus } from '../lib/status'

const CRUMBS = [{ to: '/ingestas', label: 'Historial de ingesta' }]

/** P-11. Se actualiza cada 5 s mientras la ejecución está pendiente o en curso. */
export function IngestionDetailPage() {
  const id = useParams().runId ?? ''
  const state = useApi((signal) => getIngestion(id, signal), [id], {
    pollMs: 5000,
    shouldPoll: (run: IngestionRun) => isActiveStatus(run.status),
  })

  if (state.loading && !state.data) return <Spinner />
  if (isNotFound(state.error)) {
    return (
      <>
        <PageHeader title={`Ejecución ${id}`} crumbs={CRUMBS} />
        <div className="state state-empty">Esta ejecución no existe.</div>
      </>
    )
  }
  if (state.error || !state.data) return <ErrorState error={state.error} onRetry={state.reload} />

  const r = state.data
  const steps = [
    { label: 'Solicitada', value: r.requested_at },
    { label: 'Reclamada por el worker', value: r.claimed_at },
    { label: 'Iniciada', value: r.started_at },
    { label: 'Finalizada', value: r.finished_at },
  ]
  return (
    <>
      <PageHeader title={`Ejecución #${r.id}`} crumbs={CRUMBS}>
        <div className="badges-row">
          <StatusBadge status={r.status} />
          <span>
            <Link to={`/fuentes/${r.source.id}`}>{r.source.name}</Link> · <TriggerText trigger={r.trigger_type} />
            {r.requested_by && ` · solicitada por ${r.requested_by.username}`}
          </span>
        </div>
      </PageHeader>

      <div className="grid-2">
        <section className="panel">
          <h2>Línea de tiempo</h2>
          <ol className="timeline">
            {steps.map((s) => (
              <li key={s.label} className={s.value ? 'done' : ''}>
                <span>{s.label}</span>
                {s.value ? <DateText value={s.value} /> : <span className="muted">—</span>}
              </li>
            ))}
          </ol>
          <p className="muted">Duración: {formatDuration(r.started_at, r.finished_at)}</p>
        </section>
        <section className="panel">
          <h2>Contadores</h2>
          <dl className="details counters">
            <dt>Procesados</dt>
            <dd>{formatNumber(r.records_processed)}</dd>
            <dt>Nuevos</dt>
            <dd>{formatNumber(r.records_created)}</dd>
            <dt>Actualizados</dt>
            <dd>{formatNumber(r.records_updated)}</dd>
            <dt>Errores</dt>
            <dd>{formatNumber(r.error_count)}</dd>
          </dl>
          {isActiveStatus(r.status) && <p className="muted">Los contadores se rellenan al terminar la ejecución.</p>}
        </section>
      </div>

      <section className="panel">
        <h2>Resumen de errores</h2>
        {r.error_summary ? <pre className="error-summary">{r.error_summary}</pre> : <p className="muted">Sin errores.</p>}
      </section>
    </>
  )
}
