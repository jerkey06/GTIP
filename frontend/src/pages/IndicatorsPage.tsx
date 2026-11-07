import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listSources, searchIndicators } from '../api/endpoints'
import type { IndicatorType } from '../api/types'
import { TypeBadge } from '../components/Badges'
import { DataBlock } from '../components/DataState'
import { DateText } from '../components/DateText'
import { IndicatorValue } from '../components/IndicatorValue'
import { Pagination } from '../components/Pagination'
import { useApi } from '../hooks/useApi'
import { useUrlState } from '../hooks/useUrlState'
import { PageHeader } from '../layout/AppLayout'
import { INDICATOR_TYPE_LABELS, detectIndicatorType, validateIndicator } from '../lib/indicators'

const TYPES = Object.keys(INDICATOR_TYPE_LABELS) as IndicatorType[]

/** P-05. Busca solo en los datos almacenados; nunca consulta proveedores externos. */
export function IndicatorsPage() {
  const navigate = useNavigate()
  const { get, update, page, pageSize, params } = useUrlState()
  const [value, setValue] = useState(get('value'))
  const [type, setType] = useState(get('type'))
  const [fieldError, setFieldError] = useState<string | null>(null)
  const urlKey = `${get('value')}|${get('type')}`
  const [syncedKey, setSyncedKey] = useState(urlKey)
  if (urlKey !== syncedKey) {
    setSyncedKey(urlKey)
    setValue(get('value'))
    setType(get('type'))
  }

  const sources = useApi(listSources, [])
  const state = useApi(
    (signal) =>
      searchIndicators(
        {
          value: get('value') || undefined,
          type: get('type') || undefined,
          source_id: get('source_id') || undefined,
          page,
          page_size: pageSize,
        },
        signal,
      ),
    [params.toString()],
  )

  const detected = !type && value.trim() ? detectIndicatorType(value) : null

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    const trimmed = value.trim()
    if (trimmed && type) {
      const problem = validateIndicator(trimmed, type as IndicatorType)
      if (problem) {
        setFieldError(problem)
        return
      }
    }
    setFieldError(null)
    update({ value: trimmed, type })
  }

  const searched = Boolean(get('value'))

  return (
    <>
      <PageHeader title="Indicadores" />
      <form className="filters" onSubmit={submit} role="search">
        <label className="field grow">
          <span>Valor</span>
          <input
            value={value}
            onChange={(e) => {
              setValue(e.target.value)
              setFieldError(null)
            }}
            placeholder="IP, dominio, URL o hash"
            aria-invalid={Boolean(fieldError)}
            aria-describedby="value-help"
            spellCheck={false}
          />
          <small id="value-help" className={fieldError ? 'field-error' : 'muted'}>
            {fieldError ?? (detected ? `Detectado: ${INDICATOR_TYPE_LABELS[detected]}` : ' ')}
          </small>
        </label>
        <label className="field">
          <span>Tipo</span>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="">Detectar automáticamente</option>
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {INDICATOR_TYPE_LABELS[t]}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Fuente</span>
          <select value={get('source_id')} onChange={(e) => update({ source_id: e.target.value })}>
            <option value="">Todas</option>
            {sources.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="btn btn-primary">
          Buscar
        </button>
      </form>

      <section className="panel">
        <h2>{searched ? 'Resultados' : 'Indicadores más recientes'}</h2>
        <DataBlock
          state={state}
          isEmpty={(d) => d.total === 0}
          empty={
            searched ? (
              <>
                <strong>Sin coincidencias en los datos almacenados.</strong> Esto no significa que el indicador
                sea seguro.
              </>
            ) : (
              <>
                Aún no hay indicadores. Ejecuta una ingesta de URLhaus desde <Link to="/fuentes">Fuentes</Link>.
              </>
            )
          }
        >
          {(d) => (
            <>
              {searched && (
                <p className="muted">
                  {d.exact
                    ? `Coincidencia exacta como ${d.detected_type ? INDICATOR_TYPE_LABELS[d.detected_type] : 'indicador'} (valor normalizado).`
                    : 'Coincidencia parcial del texto en el valor normalizado.'}
                </p>
              )}
              <div className="table-wrap">
                <table className="table clickable">
                  <thead>
                    <tr>
                      <th>Tipo</th>
                      <th>Valor</th>
                      <th>Reportado por</th>
                      <th>Primera vez visto</th>
                      <th>Última vez visto</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.items.map((i) => (
                      <tr key={i.id} onClick={() => navigate(`/indicadores/${i.id}`)}>
                        <td>
                          <TypeBadge type={i.indicator_type} />
                        </td>
                        <td>
                          <Link to={`/indicadores/${i.id}`} className="ioc-link" onClick={(e) => e.stopPropagation()}>
                            <IndicatorValue value={i.value} type={i.indicator_type} copy={false} truncate />
                          </Link>
                        </td>
                        <td className="nowrap">
                          {i.source_count} {i.source_count === 1 ? 'fuente' : 'fuentes'}
                        </td>
                        <td className="nowrap">
                          <DateText value={i.first_seen_at} />
                        </td>
                        <td className="nowrap">
                          <DateText value={i.last_seen_at} />
                        </td>
                      </tr>
                    ))}
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
