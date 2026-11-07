import { Link, useNavigate } from 'react-router-dom'
import type { IngestionRun } from '../api/types'
import { formatDuration, formatNumber } from '../lib/format'
import { StatusBadge, TriggerText } from './Badges'
import { DateText } from './DateText'

/** Tabla de ejecuciones de ingesta (P-09 y P-10). */
export function RunsTable({ runs, showSource = true }: { runs: IngestionRun[]; showSource?: boolean }) {
  const navigate = useNavigate()
  return (
    <div className="table-wrap">
      <table className="table clickable">
        <thead>
          <tr>
            <th>#</th>
            {showSource && <th>Fuente</th>}
            <th>Estado</th>
            <th>Disparo</th>
            <th>Inicio</th>
            <th>Duración</th>
            <th className="num">Procesados</th>
            <th className="num">Nuevos</th>
            <th className="num">Actualizados</th>
            <th>Errores</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.id} onClick={() => navigate(`/ingestas/${r.id}`)}>
              <td>
                <Link to={`/ingestas/${r.id}`}>{r.id}</Link>
              </td>
              {showSource && <td>{r.source.name}</td>}
              <td>
                <StatusBadge status={r.status} />
              </td>
              <td>
                <TriggerText trigger={r.trigger_type} />
                {r.requested_by && <span className="muted"> ({r.requested_by.username})</span>}
              </td>
              <td className="nowrap">
                {r.started_at ? <DateText value={r.started_at} /> : <span className="muted">En cola</span>}
              </td>
              <td className="nowrap">{formatDuration(r.started_at, r.finished_at)}</td>
              <td className="num">{formatNumber(r.records_processed)}</td>
              <td className="num">{formatNumber(r.records_created)}</td>
              <td className="num">{formatNumber(r.records_updated)}</td>
              <td className="description" title={r.error_summary ?? undefined}>
                {r.error_count > 0 ? (
                  <span className="error-text">
                    {r.error_count}: {r.error_summary?.split('\n')[0]}
                  </span>
                ) : (
                  '0'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
