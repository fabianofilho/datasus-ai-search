'use client'

import { useState, useEffect, useCallback } from 'react'
import { AlertCircle, X } from 'lucide-react'
import Header from '@/components/Header'
import HeroSection from '@/components/HeroSection'
import SearchBar from '@/components/SearchBar'
import ResultCard from '@/components/ResultCard'
import SQLViewer from '@/components/SQLViewer'
import DataTable from '@/components/DataTable'
import QueryHistory from '@/components/QueryHistory'
import { api } from '@/lib/api'
import type { SearchResponse, QueryHistoryItem, AppConfig } from '@/types'

const DEFAULT_CONFIG: AppConfig = { apiKey: '', apiBase: '', model: 'gpt-4.1-mini' }

export default function HomePage() {
  const [config, setConfig] = useState<AppConfig>(DEFAULT_CONFIG)
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<QueryHistoryItem[]>([])

  // Load config from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('datasus_config')
      if (saved) setConfig(JSON.parse(saved))
    } catch {}
  }, [])

  const handleSearch = useCallback(
    async (question: string) => {
      if (!config.apiKey) {
        setError('Configure sua API Key nas configurações antes de pesquisar.')
        return
      }

      setIsLoading(true)
      setError(null)
      setResult(null)

      try {
        const res = await api.search({
          question,
          api_key: config.apiKey,
          api_base: config.apiBase || undefined,
          model: config.model,
        })

        setResult(res)

        // Add to history
        const historyItem: QueryHistoryItem = {
          id: `${Date.now()}`,
          question: res.question,
          sql: res.sql,
          answer: res.answer,
          row_count: res.row_count,
          timestamp: new Date(),
        }
        setHistory((prev) => [historyItem, ...prev].slice(0, 10))
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Erro desconhecido'
        setError(msg)
      } finally {
        setIsLoading(false)
      }
    },
    [config]
  )

  return (
    <div className="min-h-screen bg-slate-50">
      <Header config={config} onConfigChange={setConfig} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
        <HeroSection />

        {/* Search */}
        <div className="mb-8">
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-xl text-sm text-red-700 animate-fade-in">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <p className="flex-1">{error}</p>
            <button onClick={() => setError(null)} className="flex-shrink-0 hover:text-red-900">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Loading skeleton */}
        {isLoading && (
          <div className="space-y-4 animate-pulse mb-8">
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="flex gap-3 mb-4">
                <div className="w-8 h-8 bg-slate-200 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-slate-200 rounded w-1/4" />
                  <div className="h-3 bg-slate-200 rounded w-1/2" />
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-3 bg-slate-200 rounded" />
                <div className="h-3 bg-slate-200 rounded w-5/6" />
                <div className="h-3 bg-slate-200 rounded w-4/6" />
              </div>
            </div>
            <div className="h-12 bg-white rounded-xl border border-slate-200" />
          </div>
        )}

        {/* Results */}
        {result && !isLoading && (
          <div className="space-y-4 mb-8">
            <ResultCard result={result} />
            <SQLViewer sql={result.sql} />
            {result.data.length > 0 && (
              <DataTable data={result.data} columns={result.columns} rowCount={result.row_count} />
            )}
          </div>
        )}

        {/* History */}
        <QueryHistory history={history} onSelect={handleSearch} />

        {/* Empty state */}
        {!result && !isLoading && !error && history.length === 0 && (
          <div className="text-center py-16 text-slate-400">
            <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <p className="text-sm font-medium">Faça sua primeira pesquisa</p>
            <p className="text-xs mt-1">Digite uma pergunta acima ou clique em um exemplo</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white mt-16 py-6">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center text-xs text-slate-400">
          <p>DATASUS AI Search — Dados de Saúde Pública Brasileira</p>
          <p className="mt-1">
            Powered by{' '}
            <span className="text-sus-blue-600 font-medium">DATASUS / SUS</span>
            {' · '}
            Desenvolvido com Next.js + FastAPI
          </p>
        </div>
      </footer>
    </div>
  )
}
