export interface SearchRequest {
  question: string
  api_key?: string
  api_base?: string
  model?: string
}

export interface SearchResponse {
  question: string
  sql: string
  answer: string
  data: Record<string, unknown>[]
  columns: string[]
  row_count: number
}

export interface TableSchema {
  [column: string]: string
}

export interface TablesResponse {
  tables: string[]
  schemas: Record<string, TableSchema>
}

export interface HealthResponse {
  status: string
  version: string
}

export interface QueryHistoryItem {
  id: string
  question: string
  sql: string
  answer: string
  row_count: number
  timestamp: Date
}

export interface AppConfig {
  apiKey: string
  apiBase: string
  model: string
}

export const AVAILABLE_MODELS = [
  { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini (recomendado)' },
  { value: 'gpt-4.1-nano', label: 'GPT-4.1 Nano (mais rápido)' },
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
]

export type Provider = 'openai' | 'gemini' | 'anthropic'

export const MODELS_BY_PROVIDER: Record<Provider, { value: string; label: string }[]> = {
  openai: [
    { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini (recomendado)' },
    { value: 'gpt-4.1-nano', label: 'GPT-4.1 Nano (mais rápido)' },
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  ],
  gemini: [
    { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash (recomendado)' },
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
  ],
  anthropic: [
    { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6 (recomendado)' },
    { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
    { value: 'claude-opus-4-6', label: 'Claude Opus 4.6' },
  ],
}

export const API_BASE_DEFAULTS: Record<Provider, string> = {
  openai: '',
  gemini: 'https://generativelanguage.googleapis.com/v1beta/openai/',
  anthropic: 'https://api.anthropic.com/v1/',
}

export function detectProvider(apiKey: string): Provider {
  if (apiKey.startsWith('sk-ant-')) return 'anthropic'
  if (apiKey.startsWith('AIza')) return 'gemini'
  return 'openai'
}

export const EXAMPLE_QUESTIONS = [
  'Quais as 10 principais causas de morte no Brasil em 2019?',
  'Quantos óbitos por tuberculose em São Paulo em 2020?',
  'Número de internações por doenças cardiovasculares em 2020',
  'Taxa de mortalidade infantil por estado em 2022',
  'Quantos procedimentos ambulatoriais em Minas Gerais em 2021?',
  'Qual a distribuição de internações por faixa etária em 2020?',
]

export const DATASET_INFO: Record<string, { label: string; description: string; color: string }> = {
  sim_do: {
    label: 'SIM — Mortalidade',
    description: 'Declarações de óbito, causas de morte e perfil demográfico',
    color: 'red',
  },
  sih_rd: {
    label: 'SIH — Internações',
    description: 'Internações hospitalares, diagnósticos, tempo de permanência',
    color: 'blue',
  },
  sia_pa: {
    label: 'SIA — Ambulatorial',
    description: 'Procedimentos ambulatoriais e consultas',
    color: 'green',
  },
  ibge_pop: {
    label: 'IBGE — População',
    description: 'Dados populacionais por município, sexo e faixa etária',
    color: 'purple',
  },
}
