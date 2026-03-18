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
