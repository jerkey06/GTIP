import { Link, useParams } from 'react-router-dom'
import { getIndicator, getObservations } from '../api/endpoints'
import type { Observation } from '../api/types'
import { TypeBadge } from '../components/Badges'
import { DataBlock, ErrorState, Spinner } from '../components/DataState'
import { DateText } from '../components/DateText'
import { IndicatorValue } from '../components/IndicatorValue'
import { useApi } from '../hooks/useApi'
import { PageHeader } from '../layout/AppLayout'
import { isNotFound } from '../lib/errors'
import { formatDate } from '../lib/format'

const CRUMBS = [{ to: '/indicadores', label: 'Indicadores' }]

function groupBySource(observations: Observation[]) {
  const groups = new Map<number, { source: Observation['source']; items: Observation[] }>()
  for (const o of observations) {
    const group = groups.get(o.source.id) ?? { source: o.source, items: [] }
    group.items.push(o)
    groups.set(o.source.id, group)
  }
  return [...groups.values()]
}

function labelsOf(data: Record<string, unknown>): string {
  const parts: string[] = []
  for (const key of ['url_status', 'threat', 'status', 'classification']) {
    if (typeof data[key] === 'string' && data[key]) parts.push(String(data[key]))
  }
  if (Array.isArray(data.tags) && data.tags.length) parts.push(data.tags.join(', '))
  return parts.join(' · ') || '—'
}

/** P-06. Evidencias de un indicador agrupadas por fuente (correlación básica, PRD §10.4). */
export function IndicatorDetailPage() {
  const id = useParams().indicatorId ?? ''
  const indicator = useApi((signal) => getIndicator(id, signal), [id])
  const observations = useApi((signal) => getObservations(id, signal), [id])

  if (indicator.loading && !indicator.data) return <Spinner />
  if (isNotFound(indicator.error)) {
    return (
      <>
        <PageHeader title="Indicador" crumbs={CRUMBS} />
        <div className="state state-empty">
          <p>Este indicador no existe en GTIP.</p>
          <Link to="/indicadores">Volver al buscador</Link>
        </div>
      </>
    )
  }
  if (indicator.error || !indicator.data) return <ErrorState error={indicator.error} onRetry={indicator.reload} />

  const i = indicator.data
  return (
    <>
      <PageHeader title={<TypeBadge type={i.indicator_type} />} crumbs={CRUMBS}>
        <div className="ioc-header">
          <IndicatorValue value={i.value} type={i.indicator_type} />
        </div>
        <p className="muted">
          Reportado por {i.source_count} {i.source_count === 1 ? 'fuente' : 'fuentes'} · {i.observation_count}{' '}
          {i.observation_count === 1 ? 'observación' : 'observaciones'} · visto por primera vez el{' '}
          {formatDate(i.first_seen_at)}
        </p>
        {i.normalized_value !== i.value && (
          <p className="muted">
            Valor normalizado: <code>{i.normalized_value}</code>
          </p>
        )}
      </PageHeader>

      <DataBlock state={observations} isEmpty={(d) => d.length === 0} empty="Este indicador no tiene observaciones.">
        {(data) => {
          const groups = groupBySource(data)
          return (
            <>
              {groups.map((g) => (
                <section key={g.source.id} className="panel">
                  <div className="panel-header">
                    <h2>
                      <Link to={`/fuentes/${g.source.id}`}>{g.source.name}</Link>
                    </h2>
                    <span className="muted">{g.items.length} observaciones</span>
                  </div>
                  <div className="table-wrap">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>ID externo</th>
                          <th>Primera vez vista</th>
                          <th>Última vez vista</th>
                          <th>Obtenido por GTIP</th>
                          <th>Estado / etiquetas</th>
                          <th>Referencia</th>
                        </tr>
                      </thead>
                      <tbody>
                        {g.items.map((o) => (
                          <tr key={o.id}>
                            <td>{o.external_id ?? '—'}</td>
                            <td>
                              <DateText value={o.first_seen_at} />
                            </td>
                            <td>
                              <DateText value={o.last_seen_at} />
                            </td>
                            <td>
                              <DateText value={o.observed_at} />
                            </td>
                            <td>{labelsOf(o.source_data)}</td>
                            <td>
                              {o.reference_url ? (
                                <a href={o.reference_url} target="_blank" rel="noopener noreferrer">
                                  Ver en {g.source.name}
                                </a>
                              ) : (
                                '—'
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <details className="raw-data">
                    <summary>Ver datos originales</summary>
                    {g.items.map((o) => (
                      <pre key={o.id}>{JSON.stringify(o.source_data, null, 2)}</pre>
                    ))}
                  </details>
                </section>
              ))}

              {groups.length > 1 && (
                <section className="panel">
                  <h2>Diferencias entre fuentes</h2>
                  <div className="table-wrap">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Fuente</th>
                          <th>Primera vez vista</th>
                          <th>Última vez vista</th>
                          <th>Clasificación</th>
                        </tr>
                      </thead>
                      <tbody>
                        {groups.map((g) => {
                          const first = g.items.map((o) => o.first_seen_at).filter(Boolean).sort()[0] ?? null
                          const last = g.items.map((o) => o.last_seen_at).filter(Boolean).sort().at(-1) ?? null
                          return (
                            <tr key={g.source.id}>
                              <td>{g.source.name}</td>
                              <td>
                                <DateText value={first} />
                              </td>
                              <td>
                                <DateText value={last} />
                              </td>
                              <td>{labelsOf(g.items[0].source_data)}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}
            </>
          )
        }}
      </DataBlock>

      <p className="notice notice-info">
        La coincidencia entre fuentes no demuestra que los reportes pertenezcan a una misma campaña o actor.
      </p>
    </>
  )
}
