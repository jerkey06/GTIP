import type { IndicatorType, IngestionStatus, TriggerType } from '../api/types'
import { INDICATOR_TYPE_LABELS } from '../lib/indicators'
import { severityOf } from '../lib/status'

const STATUS: Record<IngestionStatus, { text: string; tone: string }> = {
  pending: { text: 'Pendiente', tone: 'gray' },
  running: { text: 'En ejecución', tone: 'blue pulse' },
  completed: { text: 'Completada', tone: 'green' },
  success: { text: 'Completada', tone: 'green' },
  partial: { text: 'Parcial', tone: 'amber' },
  failed: { text: 'Fallida', tone: 'red' },
}

export function StatusBadge({ status }: { status: IngestionStatus | null | undefined }) {
  if (!status) return <span className="badge gray">Sin ejecuciones todavía</span>
  const { text, tone } = STATUS[status] ?? { text: status, tone: 'gray' }
  return <span className={`badge ${tone}`}>{text}</span>
}

/** CVSS ausente se muestra como «Sin puntuación», nunca como 0 (UI §4.3). */
export function CvssBadge({ score }: { score: number | null }) {
  const { text, tone } = severityOf(score)
  if (score === null || score === undefined) {
    return <span className="muted" title="La fuente no ha publicado una puntuación CVSS">Sin puntuación</span>
  }
  return (
    <span className="cvss">
      <strong>{score.toFixed(1)}</strong> <span className={`badge ${tone}`}>{text}</span>
    </span>
  )
}

export function KevBadge({ show }: { show: boolean }) {
  return show ? <span className="badge red">Explotada (KEV)</span> : null
}

export function TypeBadge({ type }: { type: IndicatorType }) {
  return <span className="badge outline">{INDICATOR_TYPE_LABELS[type] ?? type}</span>
}

export function SourceBadge({ name }: { name: string }) {
  return <span className="badge source">{name}</span>
}

export function TriggerText({ trigger }: { trigger: TriggerType }) {
  return <>{trigger === 'manual' ? 'Manual' : 'Programada'}</>
}
