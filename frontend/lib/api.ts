import type { SearchRequest, SearchResponse, TablesResponse, HealthResponse } from '@/types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class NeedsInitError extends Error {
  datasets: string[]
  years: (number | string)[]
  states: string[]
  constructor(datasets: string[], years: (number | string)[], states: string[]) {
    super('needs_init')
    this.datasets = datasets
    this.years = years
    this.states = states
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, options)
  if (!res.ok) {
    const json = await res.json().catch(() => null)
    if (json?.detail?.needs_init) {
      throw new NeedsInitError(json.detail.missing_datasets, json.detail.years ?? ['*'], json.detail.states ?? ['*'])
    }
    const text = JSON.stringify(json) || `HTTP ${res.status}`
    throw new Error(text)
  }
  return res.json() as Promise<T>
}

export const api = {
  search: (body: SearchRequest): Promise<SearchResponse> =>
    request<SearchResponse>('/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),

  tables: (): Promise<TablesResponse> =>
    request<TablesResponse>('/tables'),

  health: (): Promise<HealthResponse> =>
    request<HealthResponse>('/health'),

  initDb: (datasets?: string[], years?: (number | string)[], states?: string[]): Promise<{ status: string; message: string }> =>
    request('/init-db', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ datasets: datasets ?? null, years: years ?? null, states: states ?? null }),
    }),

  initDbStatus: (): Promise<{
    status: 'idle' | 'running' | 'done' | 'error'
    current: string
    completed: string[]
    error: string
  }> => request('/init-db/status'),
}
