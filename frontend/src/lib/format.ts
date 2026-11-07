const dateTime = new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeStyle: 'short' })
const dateOnly = new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeZone: 'UTC' })
const number = new Intl.NumberFormat('es')
const relative = new Intl.RelativeTimeFormat('es', { numeric: 'auto' })

/** «28 oct 2026, 14:05». Las fechas sin hora (AAAA-MM-DD) se muestran sin hora. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(value)
  const date = new Date(isDateOnly ? `${value}T00:00:00Z` : value)
  if (Number.isNaN(date.getTime())) return '—'
  return isDateOnly ? dateOnly.format(date) : dateTime.format(date)
}

export function formatNumber(value: number | null | undefined): string {
  return value === null || value === undefined ? '—' : number.format(value)
}

/** «hace 3 h», «hace 2 días». */
export function timeAgo(value: string | null | undefined, now = Date.now()): string {
  if (!value) return '—'
  const seconds = Math.round((new Date(value).getTime() - now) / 1000)
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
  ]
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) return relative.format(Math.round(seconds / size), unit)
  }
  return relative.format(seconds, 'second')
}

export function formatDuration(start: string | null, end: string | null): string {
  if (!start) return '—'
  if (!end) return 'En curso'
  const seconds = Math.max(0, Math.round((new Date(end).getTime() - new Date(start).getTime()) / 1000))
  if (seconds < 60) return `${seconds} s`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} min ${seconds % 60} s`
  return `${Math.floor(minutes / 60)} h ${minutes % 60} min`
}

export function formatInterval(minutes: number | null): string {
  if (!minutes) return 'Sin planificación'
  if (minutes % 1440 === 0) return `Cada ${minutes / 1440} día(s)`
  if (minutes % 60 === 0) return `Cada ${minutes / 60} h`
  return `Cada ${minutes} min`
}

/** Convierte AAAA-MM-DD de un <input type="date"> en el inicio o el final de ese día UTC. */
export function dayBoundary(value: string, end: boolean): string {
  return `${value}T${end ? '23:59:59' : '00:00:00'}Z`
}
