'use client'

import { useState, useEffect, useRef } from 'react'
import { Database, Loader2, CheckCircle, X, MapPin } from 'lucide-react'
import { api } from '@/lib/api'
import { DATASET_INFO } from '@/types'

const STATES = [
  { value: '*', label: 'Todos os estados' },
  { value: 'AC', label: 'AC' }, { value: 'AL', label: 'AL' }, { value: 'AP', label: 'AP' },
  { value: 'AM', label: 'AM' }, { value: 'BA', label: 'BA' }, { value: 'CE', label: 'CE' },
  { value: 'DF', label: 'DF' }, { value: 'ES', label: 'ES' }, { value: 'GO', label: 'GO' },
  { value: 'MA', label: 'MA' }, { value: 'MT', label: 'MT' }, { value: 'MS', label: 'MS' },
  { value: 'MG', label: 'MG' }, { value: 'PA', label: 'PA' }, { value: 'PB', label: 'PB' },
  { value: 'PR', label: 'PR' }, { value: 'PE', label: 'PE' }, { value: 'PI', label: 'PI' },
  { value: 'RJ', label: 'RJ' }, { value: 'RN', label: 'RN' }, { value: 'RS', label: 'RS' },
  { value: 'RO', label: 'RO' }, { value: 'RR', label: 'RR' }, { value: 'SC', label: 'SC' },
  { value: 'SP', label: 'SP' }, { value: 'SE', label: 'SE' }, { value: 'TO', label: 'TO' },
]

const REGIONS: Record<string, string[]> = {
  'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
  'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
  'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
  'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
  'Sul': ['PR', 'RS', 'SC'],
}

interface DownloadBannerProps {
  datasets: string[]
  years: (number | string)[]
  detectedStates: string[]
  onDone: () => void
  onRetrySearch: () => void
  onClose: () => void
}

export default function DownloadBanner({
  datasets, years, detectedStates, onDone, onRetrySearch, onClose,
}: DownloadBannerProps) {
  const [selectedStates, setSelectedStates] = useState<string[]>(detectedStates)
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [progress, setProgress] = useState({ current: '', completed: [] as string[], error: '' })
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  const toggleState = (st: string) => {
    if (st === '*') {
      setSelectedStates(['*'])
      return
    }
    const next = selectedStates.filter(s => s !== '*')
    if (next.includes(st)) {
      const filtered = next.filter(s => s !== st)
      setSelectedStates(filtered.length ? filtered : ['*'])
    } else {
      setSelectedStates([...next, st])
    }
  }

  const selectRegion = (region: string) => {
    const states = REGIONS[region]
    const allSelected = states.every(s => selectedStates.includes(s))
    if (allSelected) {
      const filtered = selectedStates.filter(s => !states.includes(s))
      setSelectedStates(filtered.length ? filtered : ['*'])
    } else {
      const merged = [...new Set([...selectedStates.filter(s => s !== '*'), ...states])]
      setSelectedStates(merged)
    }
  }

  const handleDownload = async () => {
    setStatus('loading')
    setProgress({ current: '', completed: [], error: '' })
    try {
      await api.initDb(datasets, years, selectedStates)
      pollRef.current = setInterval(async () => {
        try {
          const s = await api.initDbStatus()
          setProgress({ current: s.current, completed: s.completed, error: '' })
          if (s.status === 'done') {
            clearInterval(pollRef.current!)
            setStatus('done')
            setTimeout(() => {
              onDone()
              onRetrySearch()
            }, 800)
          } else if (s.status === 'error') {
            clearInterval(pollRef.current!)
            setStatus('error')
            setProgress(p => ({ ...p, error: s.error || 'Erro ao baixar dados' }))
          }
        } catch {}
      }, 2000)
    } catch (e) {
      setStatus('error')
      setProgress(p => ({ ...p, error: e instanceof Error ? e.message : 'Erro ao iniciar download' }))
    }
  }

  const totalSteps = datasets.length
  const completedSteps = progress.completed.length
  const pct = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0

  return (
    <div className="mb-6 bg-amber-50 border border-amber-200 rounded-xl animate-fade-in overflow-hidden">
      {/* Progress bar */}
      {status === 'loading' && (
        <div className="h-1 bg-amber-100">
          <div
            className="h-full bg-amber-500 transition-all duration-500 ease-out"
            style={{ width: `${Math.max(pct, completedSteps > 0 ? pct : 5)}%` }}
          />
        </div>
      )}
      {status === 'done' && <div className="h-1 bg-green-500" />}

      <div className="p-4">
        <div className="flex items-start gap-3">
          <Database className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-amber-800 mb-1">
              Dados necessarios nao encontrados
            </p>
            <p className="text-xs text-amber-700 mb-1">
              Dataset: <strong>{datasets.map(d => DATASET_INFO[d]?.label || d).join(', ')}</strong>
            </p>
            {years[0] !== '*' && (
              <p className="text-xs text-amber-700 mb-1">
                Ano(s): <strong>{years.join(', ')}</strong>
              </p>
            )}

            {/* State selector */}
            {status === 'idle' && (
              <div className="mt-3 mb-3">
                <div className="flex items-center gap-1.5 mb-2">
                  <MapPin className="w-3.5 h-3.5 text-amber-700" />
                  <span className="text-xs font-medium text-amber-800">
                    Selecione os estados (menos estados = download mais rapido)
                  </span>
                </div>

                {/* Region buttons */}
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {Object.keys(REGIONS).map(region => {
                    const states = REGIONS[region]
                    const allSelected = states.every(s => selectedStates.includes(s))
                    return (
                      <button
                        key={region}
                        onClick={() => selectRegion(region)}
                        className={`px-2 py-1 text-xs rounded-md border transition-colors ${
                          allSelected
                            ? 'bg-amber-700 text-white border-amber-700'
                            : 'bg-white text-amber-700 border-amber-300 hover:border-amber-500'
                        }`}
                      >
                        {region}
                      </button>
                    )
                  })}
                  <button
                    onClick={() => setSelectedStates(['*'])}
                    className={`px-2 py-1 text-xs rounded-md border transition-colors ${
                      selectedStates.includes('*')
                        ? 'bg-amber-700 text-white border-amber-700'
                        : 'bg-white text-amber-700 border-amber-300 hover:border-amber-500'
                    }`}
                  >
                    Brasil inteiro
                  </button>
                </div>

                {/* Individual state chips */}
                {!selectedStates.includes('*') && (
                  <div className="flex flex-wrap gap-1">
                    {STATES.filter(s => s.value !== '*').map(st => {
                      const selected = selectedStates.includes(st.value)
                      return (
                        <button
                          key={st.value}
                          onClick={() => toggleState(st.value)}
                          className={`px-1.5 py-0.5 text-xs rounded transition-colors ${
                            selected
                              ? 'bg-amber-600 text-white'
                              : 'bg-white text-amber-600 border border-amber-200 hover:border-amber-400'
                          }`}
                        >
                          {st.label}
                        </button>
                      )
                    })}
                  </div>
                )}

                <p className="text-xs text-amber-500 mt-2">
                  {selectedStates.includes('*')
                    ? 'Todos os estados serao baixados (pode demorar mais)'
                    : `${selectedStates.length} estado(s) selecionado(s)`}
                </p>
              </div>
            )}

            {/* Download progress */}
            {status === 'loading' && (
              <div className="mt-3 space-y-1.5">
                {datasets.map(ds => {
                  const done = progress.completed.includes(ds)
                  const active = progress.current === ds
                  const label = DATASET_INFO[ds]?.label || ds
                  return (
                    <div key={ds} className="flex items-center gap-2 text-xs">
                      {done ? (
                        <CheckCircle className="w-3.5 h-3.5 text-green-600 flex-shrink-0" />
                      ) : active ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-600 flex-shrink-0" />
                      ) : (
                        <div className="w-3.5 h-3.5 rounded-full border border-amber-300 flex-shrink-0" />
                      )}
                      <span className={done ? 'text-green-700' : active ? 'text-amber-800 font-medium' : 'text-amber-400'}>
                        {label}
                      </span>
                    </div>
                  )
                })}
                <p className="text-xs text-amber-600 mt-1">
                  {completedSteps}/{totalSteps} concluido(s)... aguarde
                </p>
              </div>
            )}

            {/* Done */}
            {status === 'done' && (
              <div className="mt-2 flex items-center gap-2 text-xs text-green-700">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Dados baixados. Executando pesquisa...</span>
              </div>
            )}

            {/* Error */}
            {status === 'error' && (
              <div className="mt-2 text-xs text-red-700 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                {progress.error}
              </div>
            )}

            {/* Download button */}
            {status === 'idle' && (
              <button
                onClick={handleDownload}
                className="mt-2 flex items-center gap-2 px-3 py-1.5 text-xs bg-amber-700 text-white rounded-lg hover:bg-amber-800 transition-colors"
              >
                <Database className="w-3.5 h-3.5" />
                Baixar e pesquisar
              </button>
            )}
          </div>
          <button onClick={onClose}>
            <X className="w-4 h-4 text-amber-500 hover:text-amber-700" />
          </button>
        </div>
      </div>
    </div>
  )
}
