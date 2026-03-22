import type { SearchRequest, SearchResponse, TablesResponse, HealthResponse } from '@/types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, options)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
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

  initDb: (datasets?: string[]): Promise<{ status: string; message: string }> =>
    request('/init-db', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ datasets: datasets ?? null }),
    }),
}
