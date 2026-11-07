import type { IngestionStatus, Source } from '../api/types'

export function isActiveStatus(status: IngestionStatus | null | undefined): boolean {
  return status === 'pending' || status === 'running'
}

export function severityOf(score: number | null): { text: string; tone: string } {
  if (score === null || score === undefined) return { text: 'Sin puntuación', tone: 'muted' }
  if (score >= 9) return { text: 'Crítica', tone: 'red' }
  if (score >= 7) return { text: 'Alta', tone: 'orange' }
  if (score >= 4) return { text: 'Media', tone: 'amber' }
  if (score > 0) return { text: 'Baja', tone: 'green' }
  return { text: 'Ninguna', tone: 'gray' }
}

/** Motivo por el que no se puede pedir una ingesta de esta fuente, o null. */
export function ingestBlockedReason(source: Source): string | null {
  if (!source.is_enabled) return source.disabled_reason ?? 'La fuente no está habilitada'
  if (source.active_run_id || isActiveStatus(source.last_run?.status)) {
    return 'Ya hay una ingesta pendiente o en ejecución'
  }
  return null
}
