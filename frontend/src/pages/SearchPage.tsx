import { useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { search } from '../api/endpoints'
import { CvssBadge, KevBadge, TypeBadge } from '../components/Badges'
import { DataBlock, EmptyState } from '../components/DataState'
import { IndicatorValue } from '../components/IndicatorValue'
import { useApi } from '../hooks/useApi'
import { PageHeader } from '../layout/AppLayout'
import { INDICATOR_TYPE_LABELS } from '../lib/indicators'

const EXAMPLES = ['CVE-2024-3400', '8.8.8.8', 'example.com', 'http://example.com/malware.exe', 'log4j']

/** P-07. Un solo campo para buscar CVE e indicadores en los datos almacenados. */
export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const q = (params.get('q') ?? '').trim()
  const [text, setText] = useState(q)
  const [syncedQ, setSyncedQ] = useState(q)
  if (q !== syncedQ) {
    setSyncedQ(q)
    setText(q)
  }

  const state = useApi((signal) => search(q, signal), [q], { enabled: Boolean(q) })
  const exact = q && state.data?.query === q ? state.data.exact_match : null

  if (exact?.kind === 'vulnerability' && exact.cve_id) {
    return <Navigate to={`/vulnerabilidades/${exact.cve_id}`} replace />
  }
  if (exact?.kind === 'indicator' && exact.indicator_id) {
    return <Navigate to={`/indicadores/${exact.indicator_id}`} replace />
  }

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    if (text.trim()) setParams({ q: text.trim() })
  }

  return (
    <>
      <PageHeader title="Búsqueda" />
      <form className="filters" onSubmit={submit} role="search">
        <input
          className="grow"
          type="search"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="CVE, IP, dominio, URL, hash o texto libre"
          aria-label="Buscar"
          autoFocus
        />
        <button type="submit" className="btn btn-primary">
          Buscar
        </button>
      </form>

      {!q ? (
        <section className="panel">
          <h2>¿Qué se puede buscar?</h2>
          <p>Identificadores CVE, direcciones IPv4 e IPv6, dominios, URLs, hashes MD5, SHA-1 o SHA-256 y texto libre.</p>
          <ul className="examples">
            {EXAMPLES.map((e) => (
              <li key={e}>
                <button type="button" className="link-button" onClick={() => navigate(`/buscar?q=${encodeURIComponent(e)}`)}>
                  {e}
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <DataBlock state={state}>
          {(r) => (
            <>
              <p className="muted">
                Interpretado como:{' '}
                {r.kind === 'cve'
                  ? 'identificador CVE'
                  : r.indicator_type
                    ? INDICATOR_TYPE_LABELS[r.indicator_type]
                    : 'texto libre'}
              </p>
              <section className="panel">
                <div className="panel-header">
                  <h2>Vulnerabilidades ({r.vulnerabilities.total})</h2>
                  {r.vulnerabilities.total > 0 && (
                    <Link to={`/vulnerabilidades?q=${encodeURIComponent(q)}`}>Ver todas</Link>
                  )}
                </div>
                {r.vulnerabilities.items.length === 0 ? (
                  <EmptyState>Ninguna vulnerabilidad coincide.</EmptyState>
                ) : (
                  <ul className="result-list">
                    {r.vulnerabilities.items.map((v) => (
                      <li key={v.cve_id}>
                        <Link to={`/vulnerabilidades/${v.cve_id}`}>{v.cve_id}</Link> <CvssBadge score={v.cvss_score} />{' '}
                        <KevBadge show={v.is_known_exploited} />
                        <p className="muted description">{v.description ?? v.kev_short_description}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
              <section className="panel">
                <div className="panel-header">
                  <h2>Indicadores ({r.indicators.total})</h2>
                  {r.indicators.total > 0 && <Link to={`/indicadores?value=${encodeURIComponent(q)}`}>Ver todos</Link>}
                </div>
                {r.indicators.items.length === 0 ? (
                  <EmptyState>
                    Sin coincidencias en los datos almacenados. Esto no significa que el indicador sea seguro.
                  </EmptyState>
                ) : (
                  <ul className="result-list">
                    {r.indicators.items.map((i) => (
                      <li key={i.id}>
                        <TypeBadge type={i.indicator_type} />{' '}
                        <Link to={`/indicadores/${i.id}`} className="ioc-link">
                          <IndicatorValue value={i.value} type={i.indicator_type} copy={false} truncate />
                        </Link>{' '}
                        <span className="muted">
                          Reportado por {i.source_count} {i.source_count === 1 ? 'fuente' : 'fuentes'}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </>
          )}
        </DataBlock>
      )}
    </>
  )
}
