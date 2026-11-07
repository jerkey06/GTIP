import { formatNumber } from '../lib/format'

const PAGE_SIZES = [20, 50, 100]

export function Pagination({
  page,
  pageSize,
  total,
  onChange,
}: {
  page: number
  pageSize: number
  total: number
  onChange: (page: number, pageSize: number) => void
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  const first = total === 0 ? 0 : (page - 1) * pageSize + 1
  const last = Math.min(total, page * pageSize)
  return (
    <div className="pagination">
      <span>
        {formatNumber(first)}–{formatNumber(last)} de {formatNumber(total)}
      </span>
      <div className="pagination-controls">
        <label>
          Filas{' '}
          <select value={pageSize} onChange={(e) => onChange(1, Number(e.target.value))}>
            {PAGE_SIZES.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="btn btn-small" disabled={page <= 1} onClick={() => onChange(page - 1, pageSize)}>
          Anterior
        </button>
        <span>
          Página {page} de {pages}
        </span>
        <button
          type="button"
          className="btn btn-small"
          disabled={page >= pages}
          onClick={() => onChange(page + 1, pageSize)}
        >
          Siguiente
        </button>
      </div>
    </div>
  )
}
