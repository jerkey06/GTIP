// Tipos de las respuestas de la API (contrato: OpenAPI en /docs del backend).

export type IndicatorType = 'ipv4' | 'ipv6' | 'domain' | 'url' | 'md5' | 'sha1' | 'sha256'

// Acepta también `success` (PRD §9.5) por si el equipo cambia los estados (UI §4.8).
export type IngestionStatus = 'pending' | 'running' | 'completed' | 'success' | 'partial' | 'failed'

export type TriggerType = 'manual' | 'scheduled'

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: number
  username: string
  is_active: boolean
  created_at: string
  last_login_at: string | null
}

export interface SourceRef {
  id: number
  provider_key: string
  name: string
}

export interface LastRunSummary {
  id: number
  status: IngestionStatus
  requested_at: string
  finished_at: string | null
  records_processed: number
  records_created: number
  records_updated: number
  error_count: number
}

export interface Source {
  id: number
  provider_key: string
  name: string
  description: string | null
  base_url: string | null
  is_enabled: boolean
  disabled_reason: string | null
  requires_api_key: boolean
  api_key_configured: boolean | null
  schedule_interval_minutes: number | null
  last_attempt_at: string | null
  last_success_at: string | null
  last_error: string | null
  last_run: LastRunSummary | null
  active_run_id: number | null
}

export interface VulnerabilityListItem {
  cve_id: string
  description: string | null
  kev_short_description: string | null
  cvss_score: number | null
  cvss_version: string | null
  published_at: string | null
  modified_at: string | null
  is_known_exploited: boolean
  kev_added_at: string | null
  created_at: string
}

export interface KevDetails {
  added_at: string | null
  vendor_project: string | null
  product: string | null
  vulnerability_name: string | null
  short_description: string | null
  required_action: string | null
  due_date: string | null
}

export interface Reference {
  url: string
  source: string | null
  tags: string[]
}

export interface Provenance {
  provider_key: string
  name: string
  last_success_at: string | null
}

export interface VulnerabilityDetail extends VulnerabilityListItem {
  cvss_vector: string | null
  updated_at: string
  kev: KevDetails | null
  references: Reference[]
  provenance: Provenance[]
}

export interface Indicator {
  id: number
  indicator_type: IndicatorType
  value: string
  normalized_value: string
  first_seen_at: string | null
  last_seen_at: string | null
  created_at: string
  source_count: number
  observation_count: number
}

export interface IndicatorSearchPage extends Page<Indicator> {
  detected_type: IndicatorType | null
  exact: boolean
}

export interface Observation {
  id: number
  source: SourceRef
  external_id: string | null
  first_seen_at: string | null
  last_seen_at: string | null
  observed_at: string
  reference_url: string | null
  source_data: Record<string, unknown>
}

export interface IngestionRun {
  id: number
  source: SourceRef
  status: IngestionStatus
  trigger_type: TriggerType
  requested_by: { id: number; username: string } | null
  requested_at: string
  claimed_at: string | null
  started_at: string | null
  finished_at: string | null
  records_processed: number
  records_created: number
  records_updated: number
  error_count: number
  error_summary: string | null
}

export interface CvssBucket {
  severity: 'critical' | 'high' | 'medium' | 'low' | 'none' | 'unscored'
  label: string
  min_score: number | null
  count: number
}

export interface RecentIndicator {
  id: number
  indicator_type: IndicatorType
  value: string
  source_names: string[]
  last_seen_at: string | null
  created_at: string
}

export interface Dashboard {
  stats: {
    vulnerabilities_total: number
    vulnerabilities_kev: number
    indicators_total: number
    observations_recent: number
    observations_recent_days: number
  }
  sources: Source[]
  cvss_distribution: CvssBucket[]
  latest_vulnerabilities: VulnerabilityListItem[]
  recent_indicators: RecentIndicator[]
  latest_runs: IngestionRun[]
}

export interface SearchResult {
  query: string
  kind: string
  indicator_type: IndicatorType | null
  exact_match: { kind: 'vulnerability' | 'indicator'; cve_id: string | null; indicator_id: number | null } | null
  vulnerabilities: { items: VulnerabilityListItem[]; total: number }
  indicators: { items: Indicator[]; total: number }
}

export interface Readiness {
  status: string
  database: string
  version: string
  environment: string
}
