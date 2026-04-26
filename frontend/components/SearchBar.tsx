'use client'

import { useState, KeyboardEvent } from 'react'
import { Search, Loader2 } from 'lucide-react'

interface SearchBarProps {
  onSearch: (question: string) => void
  isLoading: boolean
}

const DATASET_PILLS = [
  { key: 'SIM', label: 'Mortalidade', color: 'bg-red-500' },
  { key: 'SIH', label: 'Internações', color: 'bg-blue-500' },
  { key: 'SIA', label: 'Ambulatorial', color: 'bg-sus-green-600' },
  { key: 'IBGE', label: 'População', color: 'bg-purple-500' },
]

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [question, setQuestion] = useState('')

  const handleSubmit = () => {
    const q = question.trim()
    if (!q || isLoading) return
    onSearch(q)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-200">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
            Pergunta Livre &middot; IA Traduz para SQL &middot; Você Revisa
          </span>
          <span className="flex items-center gap-1 px-2 py-0.5 border border-slate-200 rounded text-[10px] text-slate-400 font-mono bg-white">
            <span>⌘</span>
            <span>K</span>
          </span>
        </div>

        {/* Input area */}
        <div className="flex items-start gap-3 px-4 pt-4 pb-3">
          <Search className="w-5 h-5 text-slate-300 mt-0.5 flex-shrink-0" />
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ex.: óbitos por dengue em municípios do Nordeste, 2019-2024, agrupado por mês"
            rows={2}
            className="w-full text-slate-800 placeholder-slate-300 bg-transparent resize-none outline-none text-base leading-relaxed"
            disabled={isLoading}
          />
        </div>

        {/* Bottom bar */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
          <div className="flex items-center gap-2 flex-wrap">
            {DATASET_PILLS.map((pill) => (
              <div key={pill.key} className="flex items-center gap-1.5 text-xs text-slate-600">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${pill.color}`} />
                <span className="font-semibold">{pill.key}</span>
                <span className="text-slate-400">&middot; {pill.label}</span>
              </div>
            ))}
          </div>

          <button
            onClick={handleSubmit}
            disabled={!question.trim() || isLoading}
            className="flex items-center gap-2 px-5 py-2 bg-sus-green-700 text-white rounded-lg font-medium text-sm hover:bg-sus-green-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analisando...
              </>
            ) : (
              <>
                Perguntar
                <span className="text-sus-green-300">→</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
