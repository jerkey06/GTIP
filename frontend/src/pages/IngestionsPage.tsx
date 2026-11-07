import { useState } from 'react'
import { listIngestions, listSources } from '../api/endpoints'
import type { IngestionRun, Page } from '../api/types'
import { DataBlock } from '../components/DataState'
import { useLoginGate } from '../auth/useLoginGate'
import { IngestionModal, IngestionNotice } from '../components/IngestionRequest'
import { Pagination } from '../components/Pagination'
import { RunsTable } from '../components/RunsTable'
import { useApi } from '../hooks/useApi'
import { useUrlState } from '../hooks/useUrlState'
import { PageHeader } from '../layout/AppLayout'
import { dayBoundary } from '../lib/format'
import { isActiveStatus } from '../lib/status'

const STATUSES = [
  { value: 'pending', label: 'Pendiente' },
  { value: 'running', label: 'En ejecución' },
  { value: 'completed', label: 'Completada' },
  { value: 'partial', label: 'Parcial' },
  { value: 'failed', label: 'Fallida' },
]

/** P-10. Historial de todas las ejecuciones, periódicas y manuales. */
export function IngestionsPage() {
  const { get, update, clear, page, pageSize, params } = useUrlState()
  const [modalOpen, setModalOpen] = useState(false)
  const gate = useLoginGate()
  const [created, setCreated] = useState<IngestionRun | null>(null)
  const sources = useApi(listSources, [])
  const state = useApi(
    (signal) =>
      listIngestions(
        {
          source_id: get('source_id') || undefined,
          status: get('status') || undefined,
          trigger_type: get('trigger_type') || undefined,
          requested_after: get('from') ? dayBoundary(get('from'), false) : undefined,
          requested_before: get('to') ? dayBoundary(get('to'), true) : undefined,
          page,
          page_size: pageSize,
        },
        signal,
      ),
    [params.toString()],
    { pollMs: 10000, shouldPoll: (d: Page<IngestionRun>) => d.items.some((r) => isActiveStatus(r.status)) },
  )
  const hasFilters = [...params.keys()].some((k) => k !== 'page' && k !== 'page_size')

  return (
    <>
      <PageHeader
        title="Historial de ingesta"
        actions={
          <button type="button" className="btn btn-primary" onClick={gate(() => setModalOpen(true))} disabled={!sources.data}>
            Solicitar ingesta
          </button>
        }
      />
      {created && <IngestionNotice run={created} onDismiss={() => setCreated(null)} />}
      <section className="filters" aria-label="Filtros">
        <label>
          Fuente{' '}
          <select value={get('source_id')} onChange={(e) => update({ source_id: e.target.value })}>
            <option value="">Todas</option>
            {sources.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Estado{' '}
          <select value={get('status')} onChange={(e) => update({ status: e.target.value })}>
            <option value="">Todos</option>
            {STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Disparo{' '}
          <select value={get('trigger_type')} onChange={(e) => update({ trigger_type: e.target.value })}>
            <option value="">Todos</option>
            <option value="scheduled">Programada</option>
            <option value="manual">Manual</option>
          </select>
        </label>
        <label>
          Desde <input type="date" value={get('from')} onChange={(e) => update({ from: e.target.value })} />
        </label>
        <label>
          Hasta <input type="date" value={get('to')} onChange={(e) => update({ to: e.target.value })} />
        </label>
        {hasFilters && (
          <button type="button" className="btn btn-ghost" onClick={clear}>
            Limpiar filtros
          </button>
        )}
      </section>
      <section className="panel">
        <DataBlock
          state={state}
          isEmpty={(d) => d.total === 0}
          empty={hasFilters ? 'Ninguna ejecución coincide con los filtros.' : 'Todavía no se ha ejecutado ninguna ingesta.'}
        >
          {(d) => (
            <>
              <RunsTable runs={d.items} />
              <Pagination
                page={d.page}
                pageSize={d.page_size}
                total={d.total}
                onChange={(p, size) => update({ page: p, page_size: size === 20 ? null : size }, false)}
              />
            </>
          )}
        </DataBlock>
      </section>
      {modalOpen && sources.data && (
        <IngestionModal
          sources={sources.data}
          onClose={() => setModalOpen(false)}
          onCreated={(run) => {
            setModalOpen(false)
            setCreated(run)
            state.reload()
          }}
        />
      )}
    </>
  )
}
