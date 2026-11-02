import { formatDate, timeAgo } from '../lib/format'

/** Fecha local con la ISO completa en el title; «—» si la fuente no la dio (UI §4.3, §4.4). */
export function DateText({ value, relative = false }: { value: string | null | undefined; relative?: boolean }) {
  if (!value) {
    return <span title="No proporcionada por la fuente">—</span>
  }
  return (
    <time dateTime={value} title={value}>
      {formatDate(value)}
      {relative && <span className="muted"> ({timeAgo(value)})</span>}
    </time>
  )
}
