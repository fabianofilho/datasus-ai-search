'use client'

import { useEffect, useState } from 'react'
import { X, Database, Loader2, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { api } from '@/lib/api'
import type { TablesResponse } from '@/types'
import { DATASET_INFO } from '@/types'

interface SchemaModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function SchemaModal({ isOpen, onClose }: SchemaModalProps) {
  const [data, setData] = useState<TablesResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<string[]>([])

  useEffect(() => {
    if (!isOpen) return
    setLoading(true)
    setError(null)
    api
      .tables()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [isOpen])

  if (!isOpen) return null

  const toggleTable = (table: string) => {
    setExpanded((prev) =>
      prev.includes(table) ? prev.filter((t) => t !== table) : [...prev, table]
    )
  }

  const getColor = (table: string) => {
    const info = DATASET_INFO[table]
    if (!info) return { bg: 'bg-slate-100', text: 'text-slate-600' }
    const colorMap: Record<string, { bg: string; text: string }> = {
      red: { bg: 'bg-red-50', text: 'text-red-700' },
      blue: { bg: 'bg-blue-50', text: 'text-blue-700' },
      green: { bg: 'bg-green-50', text: 'text-green-700' },
      purple: { bg: 'bg-purple-50', text: 'text-purple-700' },
    }
    return colorMap[info.color] || { bg: 'bg-slate-100', text: 'text-slate-600' }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col animate-fade-in">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-sus-blue-600" />
            <h2 className="text-base font-semibold text-slate-900">Schema do Banco de Dados</h2>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-5">
          {loading && (
            <div className="flex items-center justify-center py-12 gap-2 text-slate-500">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-sm">Carregando schema...</span>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-100 rounded-lg text-sm text-red-700">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Erro ao carregar schema</p>
                <p className="text-red-600 mt-0.5">{error}</p>
                <p className="text-red-500 mt-1 text-xs">
                  Verifique se o banco de dados foi inicializado.
                </p>
              </div>
            </div>
          )}

          {data && (
            <div className="space-y-3">
              {data.tables.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">
                  <Database className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p>Nenhuma tabela encontrada.</p>
                  <p className="text-xs mt-1">Inicialize o banco de dados nas configurações.</p>
                </div>
              ) : (
                data.tables.map((table) => {
                  const info = DATASET_INFO[table]
                  const colors = getColor(table)
                  const schema = data.schemas[table] || {}
                  const isExpanded = expanded.includes(table)

                  return (
                    <div key={table} className="border border-slate-200 rounded-xl overflow-hidden">
                      <button
                        onClick={() => toggleTable(table)}
                        className="w-full px-4 py-3.5 flex items-center justify-between hover:bg-slate-50 transition-colors text-left"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className={`px-2 py-0.5 text-xs font-medium rounded-full ${colors.bg} ${colors.text}`}
                          >
                            {table}
                          </span>
                          {info && (
                            <div>
                              <p className="text-sm font-medium text-slate-700">{info.label}</p>
                              <p className="text-xs text-slate-500">{info.description}</p>
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-400">
                            {Object.keys(schema).length} colunas
                          </span>
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-slate-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-slate-400" />
                          )}
                        </div>
                      </button>

                      {isExpanded && (
                        <div className="border-t border-slate-100 bg-slate-50 px-4 py-3">
                          <div className="grid grid-cols-2 gap-1.5">
                            {Object.entries(schema).map(([col, type]) => (
                              <div key={col} className="flex items-center justify-between gap-2 px-2.5 py-1.5 bg-white rounded-lg border border-slate-100">
                                <span className="text-xs font-mono text-slate-700 truncate">{col}</span>
                                <span className="text-xs text-slate-400 flex-shrink-0">{String(type)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
