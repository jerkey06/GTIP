import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { getSource, listIngestions, listSources } from '../api/endpoints'
import type { IngestionRun, Page, Source } from '../api/types'
import { StatusBadge } from '../components/Badges'
import { DataBlock, ErrorState, Spinner } from '../components/DataState'
import { DateText } from '../components/DateText'
import { IngestionModal, IngestionNotice } from '../components/IngestionRequest'
import { Pagination } from '../components/Pagination'
import { RunsTable } from '../components/RunsTable'
import { useApi } from '../hooks/useApi'
import { PageHeader } from '../layout/AppLayout'
import { isNotFound } from '../lib/errors'
import { formatInterval } from '../lib/format'
import { ingestBlockedReason, isActiveStatus } from '../lib/status'

const CRUMBS = [{ to: '/fuentes', label: 'Fuentes de inteligencia' }]

/** P-09. Información de una fuente y su historial completo. */
export function SourceDetailPage() {
  const id = useParams().sourceId ?? ''
  const [page, setPage] = useState({ page: 1, size: 20 })
  const [modalOpen, setModalOpen] = useState(false)
  const [created, setCreated] = useState<IngestionRun | null>(null)

  const source = useApi((signal) => getSource(id, signal), [id], {
    pollMs: 10000,
    shouldPoll: (s: Source) => isActiveStatus(s.last_run?.status),
  })
  const allSources = useApi(listSources, [], { enabled: modalOpen })
  const runs = useApi(
    (signal) => listIngestions({ source_id: id, page: page.page, page_size: page.size }, signal),
    [id, page.page, page.size, source.data?.last_run?.status],
    { pollMs: 10000, shouldPoll: (d: Page<IngestionRun>) => d.items.some((r) => isActiveStatus(r.status)) },
  )

  if (source.loading && !source.data) return <Spinner />
  if (isNotFound(source.error)) {
    return (
      <>
        <PageHeader title="Fuente" crumbs={CRUMBS} />
        <div className="state state-empty">Esta fuente no existe.</div>
      </>
    )
  }
  if (source.error || !source.data) return <ErrorState error={source.error} onRetry={source.reload} />

  const s = source.data
  const blocked = ingestBlockedReason(s)
  return (
    <>
      <PageHeader
        title={s.name}
        crumbs={CRUMBS}
        actions={
          <button
            type="button"
            className="btn btn-primary"
            disabled={Boolean(blocked)}
            title={blocked ?? undefined}
            onClick={() => setModalOpen(true)}
          >
            Ejecutar ingesta
          </button>
        }
      >
        {s.is_enabled ? <StatusBadge status={s.last_run?.status} /> : <span className="badge gray">Deshabilitada</span>}
      </PageHeader>
      {created && <IngestionNotice run={created} onDismiss={() => setCreated(null)} />}

      <div className="grid-2">
        <section className="panel">
          <h2>Datos de la fuente</h2>
          <dl className="details">
            <dt>Descripción</dt>
            <dd>{s.description ?? '—'}</dd>
            <dt>Documentación</dt>
            <dd>
              {s.base_url ? (
                <a href={s.base_url} target="_blank" rel="noopener noreferrer">
                  {s.base_url}
                </a>
              ) : (
                '—'
              )}
            </dd>
            <dt>Identificador</dt>
            <dd>
              <code>{s.provider_key}</code>
            </dd>
            <dt>Requiere clave</dt>
            <dd>{s.requires_api_key ? 'Sí' : 'No'}</dd>
            <dt>Clave configurada</dt>
            <dd>{s.api_key_configured === null ? 'No usa clave' : s.api_key_configured ? 'Configurada' : 'No configurada'}</dd>
            <dt>Habilitada</dt>
            <dd>{s.is_enabled ? 'Sí' : `No — ${s.disabled_reason}`}</dd>
            <dt>Frecuencia</dt>
            <dd>{formatInterval(s.schedule_interval_minutes)}</dd>
          </dl>
        </section>
        <section className="panel">
          <h2>Métricas</h2>
          <dl className="details">
            <dt>Último intento</dt>
            <dd>
              <DateText value={s.last_attempt_at} />
            </dd>
            <dt>Última ingesta correcta</dt>
            <dd>
              <DateText value={s.last_success_at} relative />
            </dd>
            <dt>Último error</dt>
            <dd>{s.last_error ? <pre className="error-summary">{s.last_error}</pre> : 'Ninguno'}</dd>
          </dl>
        </section>
      </div>

      <section className="panel">
        <h2>Historial de ejecuciones</h2>
        <DataBlock state={runs} isEmpty={(d) => d.total === 0} empty="Esta fuente no tiene ejecuciones todavía.">
          {(d) => (
            <>
              <RunsTable runs={d.items} showSource={false} />
              <Pagination
                page={d.page}
                pageSize={d.page_size}
                total={d.total}
                onChange={(p, size) => setPage({ page: p, size })}
              />
            </>
          )}
        </DataBlock>
      </section>

      {modalOpen && allSources.data && (
        <IngestionModal
          sources={allSources.data}
          initialSourceId={s.id}
          onClose={() => setModalOpen(false)}
          onCreated={(run) => {
            setModalOpen(false)
            setCreated(run)
            source.reload()
          }}
        />
      )}
    </>
  )
}
