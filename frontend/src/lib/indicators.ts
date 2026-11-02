import type { IndicatorType } from '../api/types'

export const INDICATOR_TYPE_LABELS: Record<IndicatorType, string> = {
  ipv4: 'IPv4',
  ipv6: 'IPv6',
  domain: 'Dominio',
  url: 'URL',
  md5: 'MD5',
  sha1: 'SHA-1',
  sha256: 'SHA-256',
}

const HASH_LENGTHS: Record<number, IndicatorType> = { 32: 'md5', 40: 'sha1', 64: 'sha256' }
const IPV4 = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/
const IPV6 = /^\[?[0-9a-f:.]*:[0-9a-f:.]*\]?$/i
const DOMAIN = /^(?=.{1,253}\.?$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{0,61}[a-z0-9]\.?$/i
export const CVE_PATTERN = /^CVE-\d{4}-\d{4,}$/i

/** Clasificación orientativa en el navegador; la validación que vale es la del backend. */
export function detectIndicatorType(raw: string): IndicatorType | null {
  const value = raw.trim()
  if (!value) return null
  if (/^[0-9a-f]+$/i.test(value) && HASH_LENGTHS[value.length]) return HASH_LENGTHS[value.length]
  if (IPV4.test(value)) return 'ipv4'
  if (IPV6.test(value) && value.includes(':')) return 'ipv6'
  if (value.includes('://')) return 'url'
  if (DOMAIN.test(value)) return 'domain'
  return null
}

/** Mensaje de error si el valor no encaja con el tipo elegido; null si encaja. */
export function validateIndicator(raw: string, type: IndicatorType): string | null {
  const detected = detectIndicatorType(raw)
  if (detected === type) return null
  return `El valor no es un ${INDICATOR_TYPE_LABELS[type]} válido`
}

/**
 * Versión «desactivada» de un indicador para mostrarlo sin riesgo de abrirlo por
 * accidente (UI §4.5): hxxp://ejemplo[.]com. Los hashes no cambian.
 */
export function defang(value: string, type: IndicatorType): string {
  if (type === 'md5' || type === 'sha1' || type === 'sha256' || type === 'ipv6') return value
  return value
    .replace(/^http/i, (m) => (m === 'HTTP' ? 'HXXP' : 'hxxp'))
    .replace(/^ftp/i, 'fxp')
    .replace(/\./g, '[.]')
}
