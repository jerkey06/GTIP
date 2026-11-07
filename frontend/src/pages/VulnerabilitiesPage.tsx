import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listVulnerabilities } from '../api/endpoints'
import { CvssBadge, KevBadge } from '../components/Badges'
import { DataBlock } from '../components/DataState'
import { DateText } from '../components/DateText'
import { Pagination } from '../components/Pagination'
import { useApi } from '../hooks/useApi'
import { useUrlState } from '../hooks/useUrlState'
import { PageHeader } from '../layout/AppLayout'
import { dayBoundary } from '../lib/format'
import { CVE_PATTERN } from '../lib/indicators'

const SORTS = [
  { value: '-published_at', label: 'Publicación ↓' },
  { value: 'published_at', label: 'Publicación ↑' },
  { value: '-modified_at', label: 'Modificación ↓' },
  { value: '-cvss_score', label: 'CVSS ↓' },
  { value: '-created_at', label: 'Registro en GTIP ↓' },
]

/** P-03. Filtros, orden y página viven en la URL (UI §4.7). */
export function VulnerabilitiesPage() {
  const navigate = useNavigate()
  const { get, update, clear, page, pageSize, params } = useUrlState()
  const q = get('q')
  const [text, setText] = useState(q)
  const [syncedQ, setSyncedQ] = useState(q)
  if (q !== syncedQ) {
    setSyncedQ(q)
    setText(q)
  }

  const query = {
    q: q || undefined,
    is_kev: get('is_kev') === 'true' ? true : undefined,
    min_cvss: get('min_cvss') || undefined,
    max_cvss: get('max_cvss') || undefined,
    has_cvss: get('has_cvss') || undefined,
    published_after: get('published_after') ? dayBoundary(get('published_after'), false) : undefined,
    published_before: get('published_before') ? dayBoundary(get('published_before'), true) : undefined,
    sort: get('sort') || undefined,
    page,
    page_size: pageSize,
  }
  const state = useApi((signal) => listVulnerabilities(query, signal), [params.toString()])
  const hasFilters = [...params.keys()].some((k) => k !== 'page' && k !== 'page_size')

  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault()
    const value = text.trim()
    update({ q: CVE_PATTERN.test(value) ? value.toUpperCase() : value })
  }

  return (
    <>
      <PageHeader title="Vulnerabilidades" />
      <section className="filters" aria-label="Filtros">
        <form onSubmit={submitSearch} className="filter-search">
          <input
            type="search"
            placeholder="Buscar por CVE o texto"
            value={text}
            onChange={(e) => setText(e.target.value)}
            aria-label="Buscar por CVE o texto"
          />
          <button type="submit" className="btn">
            Buscar
          </button>
        </form>
        <label className="toggle">
          <input
            type="checkbox"
            checked={get('is_kev') === 'true'}
            onChange={(e) => update({ is_kev: e.target.checked })}
          />
          Solo explotadas (KEV)
        </label>
        <label>
          CVSS mínimo{' '}
          <select
            value={get('has_cvss') === 'false' ? 'none' : get('min_cvss')}
            onChange={(e) =>
              e.target.value === 'none'
                ? update({ min_cvss: null, max_cvss: null, has_cvss: 'false' })
                : update({ min_cvss: e.target.value, max_cvss: null, has_cvss: null })
            }
          >
            <option value="">Cualquiera</option>
            <option value="4">4.0</option>
            <option value="7">7.0</option>
            <option value="9">9.0</option>
            <option value="none">Sin puntuación</option>
          </select>
        </label>
        <label>
          Publicada desde{' '}
          <input
            type="date"
            value={get('published_after')}
            onChange={(e) => update({ published_after: e.target.value })}
          />
        </label>
        <label>
          hasta{' '}
          <input
            type="date"
            value={get('published_before')}
            onChange={(e) => update({ published_before: e.target.value })}
          />
        </label>
        <label>
          Ordenar por{' '}
          <select value={get('sort', '-published_at')} onChange={(e) => update({ sort: e.target.value })}>
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
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
          empty={
            hasFilters ? (
              <>
                Ninguna vulnerabilidad coincide con los filtros.{' '}
                <button type="button" className="link-button" onClick={clear}>
                  Limpiar filtros
                </button>
              </>
            ) : (
              <>
                Aún no hay vulnerabilidades. Ejecuta una ingesta de CISA KEV desde <Link to="/fuentes">Fuentes</Link>.
              </>
            )
          }
        >
          {(d) => (
            <>
              {q && CVE_PATTERN.test(q) && d.items.some((v) => v.cve_id === q.toUpperCase()) && (
                <p className="notice notice-info">
                  <Link to={`/vulnerabilidades/${q.toUpperCase()}`}>Ir al detalle de {q.toUpperCase()}</Link>
                </p>
              )}
              <div className="table-wrap">
                <table className="table clickable">
                  <thead>
                    <tr>
                      <th>CVE</th>
                      <th>Descripción</th>
                      <th>CVSS</th>
                      <th>KEV</th>
                      <th>Publicada</th>
                      <th>Modificada</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.items.map((v) => {
                      const description = v.description ?? v.kev_short_description
                      return (
                        <tr key={v.cve_id} onClick={() => navigate(`/vulnerabilidades/${v.cve_id}`)}>
                          <td className="nowrap">
                            <Link to={`/vulnerabilidades/${v.cve_id}`}>{v.cve_id}</Link>
                          </td>
                          <td className="description" title={description ?? undefined}>
                            {description ?? <span className="muted">Sin descripción</span>}
                          </td>
                          <td className="nowrap">
                            <CvssBadge score={v.cvss_score} />
                          </td>
                          <td>
                            <KevBadge show={v.is_known_exploited} />
                          </td>
                          <td className="nowrap">
                            <DateText value={v.published_at} />
                          </td>
                          <td className="nowrap">
                            <DateText value={v.modified_at} />
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
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
    </>
  )
}
