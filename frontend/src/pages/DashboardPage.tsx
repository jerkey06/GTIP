import { Suspense, lazy } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getDashboard } from '../api/endpoints'
import type { CvssBucket, Dashboard } from '../api/types'
import { CvssBadge, KevBadge, SourceBadge, StatusBadge, TriggerText, TypeBadge } from '../components/Badges'
import { DataBlock, EmptyState, Spinner } from '../components/DataState'
import { DateText } from '../components/DateText'
import { IndicatorValue } from '../components/IndicatorValue'
import { useApi } from '../hooks/useApi'
import { PageHeader } from '../layout/AppLayout'
import { formatNumber, timeAgo } from '../lib/format'
import { isActiveStatus } from '../lib/status'

// Recharts pesa bastante: se carga aparte, solo en el dashboard.
const CvssChart = lazy(() => import('../components/CvssChart').then((m) => ({ default: m.CvssChart })))

function StatCard({ label, value, hint, to }: { label: string; value: number; hint?: string; to: string }) {
  return (
    <Link to={to} className="stat-card">
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{formatNumber(value)}</strong>
      {hint && <span className="muted">{hint}</span>}
    </Link>
  )
}

function bucketLink(bucket: CvssBucket): string {
  if (bucket.severity === 'unscored') return '/vulnerabilidades?has_cvss=false'
  if (bucket.severity === 'none') return '/vulnerabilidades?min_cvss=0&max_cvss=0'
  const max = { critical: 10, high: 8.9, medium: 6.9, low: 3.9 }[bucket.severity]
  return `/vulnerabilidades?min_cvss=${bucket.min_score}&max_cvss=${max}`
}

/** P-02. Todos los valores salen de la base de datos (PRD §10.1). */
export function DashboardPage() {
  const navigate = useNavigate()
  const state = useApi(getDashboard, [], {
    pollMs: 10000,
    shouldPoll: (d: Dashboard) => d.sources.some((s) => isActiveStatus(s.last_run?.status)),
  })

  return (
    <>
      <PageHeader title="Dashboard" />
      <DataBlock state={state}>
        {(d) => {
          const empty = d.stats.vulnerabilities_total === 0 && d.stats.indicators_total === 0
          return (
            <>
              {empty && (
                <div className="notice notice-info">
                  <span>Todavía no hay datos. Ve a Fuentes y ejecuta la primera ingesta.</span>
                  <Link to="/fuentes" className="btn btn-small btn-primary">
                    Ir a Fuentes
                  </Link>
                </div>
              )}

              <section className="stats-grid" aria-label="Estadísticas">
                <StatCard label="Vulnerabilidades almacenadas" value={d.stats.vulnerabilities_total} to="/vulnerabilidades" />
                <StatCard label="Vulnerabilidades en KEV" value={d.stats.vulnerabilities_kev} to="/vulnerabilidades?is_kev=true" />
                <StatCard label="Indicadores únicos" value={d.stats.indicators_total} to="/indicadores" />
                <StatCard
                  label="Observaciones recientes"
                  value={d.stats.observations_recent}
                  hint={`Últimos ${d.stats.observations_recent_days} días`}
                  to="/indicadores"
                />
              </section>

              <div className="grid-2">
                <section className="panel">
                  <h2>Estado de las fuentes</h2>
                  <ul className="source-status-list">
                    {d.sources.map((s) => (
                      <li key={s.id}>
                        <Link to={`/fuentes/${s.id}`}>{s.name}</Link>
                        {s.is_enabled ? (
                          <StatusBadge status={s.last_run?.status} />
                        ) : (
                          <span className="badge gray">Deshabilitada</span>
                        )}
                        <span className="muted">
                          Última ingesta correcta: {s.last_success_at ? timeAgo(s.last_success_at) : 'nunca'}
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>

                <section className="panel">
                  <h2>Distribución por CVSS</h2>
                  {d.cvss_distribution.every((b) => b.severity === 'unscored' || b.count === 0) ? (
                    <EmptyState>Aún no hay vulnerabilidades con puntuación CVSS.</EmptyState>
                  ) : (
                    <Suspense fallback={<Spinner label="Cargando gráfica…" />}>
                      <CvssChart buckets={d.cvss_distribution} onSelect={(b) => navigate(bucketLink(b))} />
                    </Suspense>
                  )}
                </section>
              </div>

              <div className="grid-2">
                <section className="panel">
                  <div className="panel-header">
                    <h2>Últimas vulnerabilidades registradas</h2>
                    <Link to="/vulnerabilidades?sort=-created_at">Ver todas</Link>
                  </div>
                  {d.latest_vulnerabilities.length === 0 ? (
                    <EmptyState>Aún no hay vulnerabilidades. Ejecuta una ingesta de CISA KEV desde Fuentes.</EmptyState>
                  ) : (
                    <div className="table-wrap">
                      <table className="table clickable">
                        <thead>
                          <tr>
                            <th>CVE</th>
                            <th>CVSS</th>
                            <th>KEV</th>
                            <th>Registrada</th>
                          </tr>
                        </thead>
                        <tbody>
                          {d.latest_vulnerabilities.map((v) => (
                            <tr key={v.cve_id} onClick={() => navigate(`/vulnerabilidades/${v.cve_id}`)}>
                              <td>
                                <Link to={`/vulnerabilidades/${v.cve_id}`}>{v.cve_id}</Link>
                              </td>
                              <td>
                                <CvssBadge score={v.cvss_score} />
                              </td>
                              <td>
                                <KevBadge show={v.is_known_exploited} />
                              </td>
                              <td>
                                <DateText value={v.created_at} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>

                <section className="panel">
                  <div className="panel-header">
                    <h2>Indicadores recientes</h2>
                    <Link to="/indicadores">Ver todos</Link>
                  </div>
                  {d.recent_indicators.length === 0 ? (
                    <EmptyState>Aún no hay indicadores. Ejecuta una ingesta de URLhaus desde Fuentes.</EmptyState>
                  ) : (
                    <div className="table-wrap">
                      <table className="table clickable">
                        <thead>
                          <tr>
                            <th>Tipo</th>
                            <th>Valor</th>
                            <th>Fuente</th>
                            <th>Registrado</th>
                          </tr>
                        </thead>
                        <tbody>
                          {d.recent_indicators.map((i) => (
                            <tr key={i.id} onClick={() => navigate(`/indicadores/${i.id}`)}>
                              <td>
                                <TypeBadge type={i.indicator_type} />
                              </td>
                              <td>
                                <IndicatorValue value={i.value} type={i.indicator_type} copy={false} truncate />
                              </td>
                              <td>
                                {i.source_names.map((n) => (
                                  <SourceBadge key={n} name={n} />
                                ))}
                              </td>
                              <td>
                                <DateText value={i.created_at} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>
              </div>

              <section className="panel">
                <div className="panel-header">
                  <h2>Últimas ejecuciones de ingesta</h2>
                  <Link to="/ingestas">Ver historial</Link>
                </div>
                {d.latest_runs.length === 0 ? (
                  <EmptyState>Todavía no se ha ejecutado ninguna ingesta.</EmptyState>
                ) : (
                  <div className="table-wrap">
                    <table className="table clickable">
                      <thead>
                        <tr>
                          <th>Fuente</th>
                          <th>Estado</th>
                          <th>Disparo</th>
                          <th>Solicitada</th>
                          <th className="num">Procesados</th>
                          <th className="num">Nuevos</th>
                        </tr>
                      </thead>
                      <tbody>
                        {d.latest_runs.map((r) => (
                          <tr key={r.id} onClick={() => navigate(`/ingestas/${r.id}`)}>
                            <td>
                              <Link to={`/ingestas/${r.id}`}>{r.source.name}</Link>
                            </td>
                            <td>
                              <StatusBadge status={r.status} />
                            </td>
                            <td>
                              <TriggerText trigger={r.trigger_type} />
                            </td>
                            <td>
                              <DateText value={r.requested_at} />
                            </td>
                            <td className="num">{formatNumber(r.records_processed)}</td>
                            <td className="num">{formatNumber(r.records_created)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </>
          )
        }}
      </DataBlock>
    </>
  )
}
