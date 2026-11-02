// Una función por endpoint. Si cambian los nombres de rutas (PRD vs ADD), solo cambia aquí.
import { api, request } from './client'
import type {
  Dashboard,
  IndicatorSearchPage,
  Indicator,
  IngestionRun,
  Observation,
  Page,
  Readiness,
  SearchResult,
  Source,
  TokenResponse,
  User,
  VulnerabilityDetail,
  VulnerabilityListItem,
} from './types'

export type QueryParams = Record<string, string | number | boolean | null | undefined>

export const login = (username: string, password: string) =>
  request<TokenResponse>('POST', '/auth/login', { body: { username, password }, auth: false })

export const getMe = (signal?: AbortSignal) => api.get<User>('/auth/me', undefined, signal)

export const getReadiness = (signal?: AbortSignal) =>
  api.get<Readiness>('/health/ready', undefined, signal)

export const getDashboard = (signal?: AbortSignal) =>
  api.get<Dashboard>('/dashboard', undefined, signal)

export const listSources = (signal?: AbortSignal) => api.get<Source[]>('/sources', undefined, signal)

export const getSource = (id: number | string, signal?: AbortSignal) =>
  api.get<Source>(`/sources/${id}`, undefined, signal)

export const listVulnerabilities = (query: QueryParams, signal?: AbortSignal) =>
  api.get<Page<VulnerabilityListItem>>('/vulnerabilities', query, signal)

export const getVulnerability = (cveId: string, signal?: AbortSignal) =>
  api.get<VulnerabilityDetail>(`/vulnerabilities/${encodeURIComponent(cveId)}`, undefined, signal)

export const searchIndicators = (query: QueryParams, signal?: AbortSignal) =>
  api.get<IndicatorSearchPage>('/indicators', query, signal)

export const getIndicator = (id: number | string, signal?: AbortSignal) =>
  api.get<Indicator>(`/indicators/${id}`, undefined, signal)

export const getObservations = (id: number | string, signal?: AbortSignal) =>
  api.get<Observation[]>(`/indicators/${id}/observations`, undefined, signal)

export const listIngestions = (query: QueryParams, signal?: AbortSignal) =>
  api.get<Page<IngestionRun>>('/ingestions', query, signal)

export const getIngestion = (id: number | string, signal?: AbortSignal) =>
  api.get<IngestionRun>(`/ingestions/${id}`, undefined, signal)

export const requestIngestion = (sourceId: number) =>
  api.post<IngestionRun>('/ingestions', { source_id: sourceId })

export const search = (q: string, signal?: AbortSignal) =>
  api.get<SearchResult>('/search', { q }, signal)
