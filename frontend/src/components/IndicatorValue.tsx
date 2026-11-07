import { useState } from 'react'
import type { IndicatorType } from '../api/types'
import { defang } from '../lib/indicators'

export function CopyButton({ text, label = 'Copiar' }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async (event: React.MouseEvent) => {
    event.stopPropagation()
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }
  return (
    <button type="button" className="btn btn-small btn-ghost" onClick={copy}>
      {copied ? 'Copiado' : label}
    </button>
  )
}

/**
 * Un indicador es un dato potencialmente malicioso (UI §4.5): nunca es un enlace, se
 * muestra «desactivado» en monoespaciada y «Copiar» copia el valor original.
 */
export function IndicatorValue({
  value,
  type,
  copy = true,
  truncate = false,
}: {
  value: string
  type: IndicatorType
  copy?: boolean
  truncate?: boolean
}) {
  return (
    <span className="ioc">
      <code className={truncate ? 'truncate' : undefined} title={truncate ? defang(value, type) : undefined}>
        {defang(value, type)}
      </code>
      {copy && <CopyButton text={value} />}
    </span>
  )
}
