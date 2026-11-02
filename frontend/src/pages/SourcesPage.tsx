import { useState } from 'react'
import { Link } from 'react-router-dom'
import { listSources } from '../api/endpoints'
import type { IngestionRun, Source } from '../api/types'
import { StatusBadge } from '../components/Badges'
import { DataBlock } from '../components/DataState'
import { DateText } from '../components/DateText'
import { IngestionModal, IngestionNotice } from '../components/IngestionRequest'
import { useApi } from '../hooks/useApi'
import { PageHeader } from '../layout/AppLayout'
import { formatInterval, formatNumber } from '../lib/format'
import { ingestBlockedReason, isActiveStatus } from '../lib/status'

export function SourceCard({ source, onIngest }: { source: Source; onIngest: (s: Source) => void }) {
  const blocked = ingestBlockedReason(source)
  const run = source.last_run
  return (
    <article className="panel source-card">
      <div className="panel-header">
        <h2>
          <Link to={`/fuentes/${source.id}`}>{source.name}</Link>
        </h2>
        {source.is_enabled ? <StatusBadge status={run?.status} /> : <span className="badge gray">Deshabilitada</span>}
      </div>
      {source.description && <p>{source.description}</p>}
      <dl className="details">
        <dt>Habilitada</dt>
        <dd>{source.is_enabled ? 'Sí' : `No — ${source.disabled_reason}`}</dd>
        <dt>Planificación</dt>
        <dd>{formatInterval(source.schedule_interval_minutes)}</dd>
        <dt>Último intento</dt>
        <dd>
          <DateText value={source.last_attempt_at} />
        </dd>
        <dt>Última ingesta correcta</dt>
        <dd>
          <DateText value={source.last_success_at} relative />
        </dd>
        <dt>Última ejecución</dt>
        <dd>
          {run
            ? `${formatNumber(run.records_processed)} procesados / ${formatNumber(run.records_created)} nuevos / ${formatNumber(run.records_updated)} actualizados`
            : 'Sin ejecuciones todavía'}
        </dd>
        {source.last_error && (
          <>
            <dt>Último error</dt>
            <dd className="error-text">{source.last_error.split('\n')[0]}</dd>
          </>
        )}
      </dl>
      <div className="card-actions">
        <Link to={`/fuentes/${source.id}`} className="btn">
          Ver detalle
        </Link>
        <button
          type="button"
          className="btn btn-primary"
          disabled={Boolean(blocked)}
          title={blocked ?? undefined}
          onClick={() => onIngest(source)}
        >
          Ejecutar ingesta
        </button>
      </div>
    </article>
  )
}

/** P-08. El estado se basa en las ejecuciones, no en la configuración (PRD §10.5). */
export function SourcesPage() {
  const [modalSource, setModalSource] = useState<Source | null>(null)
  const [created, setCreated] = useState<IngestionRun | null>(null)
  const state = useApi(listSources, [], {
    pollMs: 10000,
    shouldPoll: (sources: Source[]) => sources.some((s) => isActiveStatus(s.last_run?.status)),
  })

  const onCreated = (run: IngestionRun) => {
    setModalSource(null)
    setCreated(run)
    state.reload()
  }

  return (
    <>
      <PageHeader title="Fuentes de inteligencia">
        <p className="muted">
          El estado indica el resultado técnico de la ingesta, no la exactitud ni la completitud de los datos.
        </p>
      </PageHeader>
      {created && <IngestionNotice run={created} onDismiss={() => setCreated(null)} />}
      <DataBlock state={state}>
        {(sources) => (
          <div className="cards-grid">
            {sources.map((s) => (
              <SourceCard key={s.id} source={s} onIngest={setModalSource} />
            ))}
          </div>
        )}
      </DataBlock>
      {modalSource && state.data && (
        <IngestionModal
          key={modalSource.id}
          sources={state.data}
          initialSourceId={modalSource.id}
          onClose={() => setModalSource(null)}
          onCreated={onCreated}
        />
      )}
    </>
  )
}
