'use client'

import { useState, KeyboardEvent } from 'react'
import { Search, Loader2, X } from 'lucide-react'
import { EXAMPLE_QUESTIONS } from '@/types'

interface SearchBarProps {
  onSearch: (question: string) => void
  isLoading: boolean
}

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

  const handleExample = (q: string) => {
    setQuestion(q)
    onSearch(q)
  }

  return (
    <div className="w-full">
      {/* Main input */}
      <div className="relative bg-white rounded-xl border border-slate-200 shadow-sm focus-within:ring-2 focus-within:ring-sus-blue-600 focus-within:border-sus-blue-600 transition-all">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Digite sua pergunta sobre dados de saúde pública... (ex: Quantos óbitos por tuberculose em SP em 2020?)"
          rows={3}
          className="w-full px-4 pt-4 pb-12 text-slate-800 placeholder-slate-400 bg-transparent resize-none outline-none text-base"
          disabled={isLoading}
        />

        {/* Actions inside textarea */}
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          {question && (
            <button
              onClick={() => setQuestion('')}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={handleSubmit}
            disabled={!question.trim() || isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-sus-blue-600 text-white rounded-lg font-medium text-sm hover:bg-sus-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analisando...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Pesquisar
              </>
            )}
          </button>
        </div>
      </div>

      {/* Example questions */}
      <div className="mt-3">
        <p className="text-xs text-slate-500 mb-2">Exemplos de perguntas:</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((q, i) => (
            <button
              key={i}
              onClick={() => handleExample(q)}
              disabled={isLoading}
              className="px-3 py-1.5 text-xs bg-white border border-slate-200 text-slate-600 rounded-full hover:border-sus-blue-300 hover:text-sus-blue-700 hover:bg-sus-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {q.length > 50 ? q.slice(0, 50) + '…' : q}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
