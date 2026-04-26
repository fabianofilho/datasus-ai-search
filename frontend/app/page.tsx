'use client'

import { useState, useEffect, useCallback } from 'react'
import { AlertCircle, X, LayoutGrid, Clock, Database, Info } from 'lucide-react'
import Header from '@/components/Header'
import HeroSection from '@/components/HeroSection'
import SearchBar from '@/components/SearchBar'
import ResultCard from '@/components/ResultCard'
import SQLViewer from '@/components/SQLViewer'
import DataTable from '@/components/DataTable'
import QueryHistory from '@/components/QueryHistory'
import DownloadBanner from '@/components/DownloadBanner'
import { api, NeedsInitError } from '@/lib/api'
import type { SearchResponse, QueryHistoryItem, AppConfig } from '@/types'
import { EXAMPLE_QUESTIONS } from '@/types'

const DEFAULT_CONFIG: AppConfig = { apiKey: '', apiBase: 'https://api.groq.com/openai/v1', model: 'llama-3.3-70b-versatile' }

const STATS = [
  { icon: LayoutGrid, label: '14 fontes integradas' },
  { icon: Clock, label: 'Atualizado em 22/abr/2026' },
  { icon: Database, label: '2.847 tabelas · 41k colunas' },
  { icon: Info, label: 'Toda consulta retorna SQL revisável' },
]

const EXAMPLE_DOT_COLORS = ['bg-red-500', 'bg-blue-500', 'bg-teal-500']

export default function HomePage() {
  const [config, setConfig] = useState<AppConfig>(DEFAULT_CONFIG)
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<QueryHistoryItem[]>([])
  const [missingDatasets, setMissingDatasets] = useState<string[] | null>(null)
  const [missingYears, setMissingYears] = useState<(number | string)[]>(['*'])
  const [missingStates, setMissingStates] = useState<string[]>(['*'])
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null)

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
        setMissingDatasets(null)
        const res = await api.search({
          question,
          api_key: config.apiKey,
          api_base: config.apiBase || undefined,
          model: config.model,
        })

        setResult(res)
        setPendingQuestion(null)

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
        if (e instanceof NeedsInitError) {
          setMissingDatasets(e.datasets)
          setMissingYears(e.years)
          setMissingStates(e.states)
          setPendingQuestion(question)
        } else {
          const msg = e instanceof Error ? e.message : 'Erro desconhecido'
          setError(msg)
        }
      } finally {
        setIsLoading(false)
      }
    },
    [config]
  )

  const handleDownloadDone = useCallback(() => {
    setMissingDatasets(null)
  }, [])

  const handleRetrySearch = useCallback(() => {
    if (pendingQuestion) handleSearch(pendingQuestion)
  }, [pendingQuestion, handleSearch])

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Header config={config} onConfigChange={setConfig} />

      <main className="flex-1">
        {/* Hero area with background circle decoration */}
        <div className="relative overflow-hidden">
          {/* Decorative circles */}
          <svg
            className="absolute right-0 top-1/2 -translate-y-1/2 opacity-[0.07] pointer-events-none"
            width="520"
            height="520"
            viewBox="0 0 520 520"
            fill="none"
            aria-hidden="true"
          >
            <circle cx="420" cy="260" r="200" stroke="#1e293b" strokeWidth="1.5" />
            <circle cx="420" cy="260" r="150" stroke="#1e293b" strokeWidth="1.5" />
            <circle cx="420" cy="260" r="100" stroke="#1e293b" strokeWidth="1.5" />
            <circle cx="420" cy="260" r="50" stroke="#1e293b" strokeWidth="1.5" />
          </svg>

          <div className="max-w-4xl mx-auto px-6 pt-16 pb-4">
            <HeroSection />

            {/* Search box */}
            <SearchBar onSearch={handleSearch} isLoading={isLoading} />

            {/* Stats row */}
            <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
              {STATS.map(({ icon: Icon, label }) => (
                <div key={label} className="flex items-center gap-1.5 text-xs text-slate-400">
                  <Icon className="w-3.5 h-3.5" />
                  <span>{label}</span>
                </div>
              ))}
            </div>

            {/* TENTE: section */}
            <div className="mt-8 flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest flex-shrink-0">
                Tente:
              </span>
              {EXAMPLE_QUESTIONS.slice(0, 3).map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSearch(q)}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs text-slate-600 hover:border-slate-300 hover:text-slate-800 transition-colors disabled:opacity-50"
                >
                  <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${EXAMPLE_DOT_COLORS[i]}`} />
                  {q.length > 50 ? q.slice(0, 50) + '...' : q}
                </button>
              ))}
              <button className="text-xs text-sus-green-700 hover:text-sus-green-800 font-medium">
                Ver mais &middot;
              </button>
            </div>
          </div>
        </div>

        {/* Results area */}
        <div className="max-w-4xl mx-auto px-6 pb-16">
          {/* Missing datasets banner */}
          {missingDatasets && (
            <DownloadBanner
              datasets={missingDatasets}
              years={missingYears}
              detectedStates={missingStates}
              onDone={handleDownloadDone}
              onRetrySearch={handleRetrySearch}
              onClose={() => setMissingDatasets(null)}
            />
          )}

          {/* Error */}
          {error && (
            <div className="mt-6 flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-xl text-sm text-red-700 animate-fade-in">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <p className="flex-1">{error}</p>
              <button onClick={() => setError(null)} className="flex-shrink-0 hover:text-red-900">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Loading skeleton */}
          {isLoading && (
            <div className="mt-8 space-y-4 animate-pulse">
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <div className="flex gap-3 mb-4">
                  <div className="w-8 h-8 bg-slate-100 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-slate-100 rounded w-1/4" />
                    <div className="h-3 bg-slate-100 rounded w-1/2" />
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="h-3 bg-slate-100 rounded" />
                  <div className="h-3 bg-slate-100 rounded w-5/6" />
                  <div className="h-3 bg-slate-100 rounded w-4/6" />
                </div>
              </div>
              <div className="h-12 bg-white rounded-xl border border-slate-200" />
            </div>
          )}

          {/* Results */}
          {result && !isLoading && (
            <div className="mt-8 space-y-4">
              <ResultCard result={result} />
              <SQLViewer sql={result.sql} />
              {result.data.length > 0 && (
                <DataTable data={result.data} columns={result.columns} rowCount={result.row_count} />
              )}
            </div>
          )}

          {/* History */}
          <QueryHistory history={history} onSelect={handleSearch} />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 py-6">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
            Saude · Busca · V4.2
          </span>
          <div className="flex items-center gap-4">
            {['Privacidade', 'Fontes', 'API', 'Contato'].map((link) => (
              <button key={link} className="text-xs text-slate-500 hover:text-slate-300 transition-colors">
                {link}
              </button>
            ))}
          </div>
        </div>
      </footer>
    </div>
  )
}
