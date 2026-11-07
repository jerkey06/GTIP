import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { CvssBucket } from '../api/types'

const COLORS: Record<CvssBucket['severity'], string> = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#d97706',
  low: '#16a34a',
  none: '#64748b',
  unscored: '#94a3b8',
}

/** Distribución por severidad CVSS; «Sin puntuación» va aparte y rayada (UI P-02). */
export function CvssChart({ buckets, onSelect }: { buckets: CvssBucket[]; onSelect: (b: CvssBucket) => void }) {
  return (
    <div className="chart" role="img" aria-label="Distribución de vulnerabilidades por severidad CVSS">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={buckets} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
          <defs>
            <pattern id="unscored" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect width="6" height="6" fill="var(--surface-2)" />
              <line x1="0" y1="0" x2="0" y2="6" stroke={COLORS.unscored} strokeWidth="3" />
            </pattern>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
          <XAxis dataKey="label" tick={{ fill: 'var(--text)', fontSize: 12 }} />
          <YAxis allowDecimals={false} tick={{ fill: 'var(--text)', fontSize: 12 }} width={48} />
          <Tooltip
            cursor={{ fill: 'var(--surface-2)' }}
            contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
            formatter={(value) => [value, 'Vulnerabilidades']}
          />
          <Bar dataKey="count" cursor="pointer" onClick={(_, index) => onSelect(buckets[index])}>
            {buckets.map((b) => (
              <Cell key={b.severity} fill={b.severity === 'unscored' ? 'url(#unscored)' : COLORS[b.severity]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <ul className="chart-legend">
        {buckets.map((b) => (
          <li key={b.severity}>
            <button type="button" className="link-button" onClick={() => onSelect(b)}>
              {b.label}: {b.count}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
