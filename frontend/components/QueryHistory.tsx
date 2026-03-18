'use client'

import { History, ChevronDown, ChevronUp, Clock } from 'lucide-react'
import { useState } from 'react'
import type { QueryHistoryItem } from '@/types'

interface QueryHistoryProps {
  history: QueryHistoryItem[]
  onSelect: (question: string) => void
}

export default function QueryHistory({ history, onSelect }: QueryHistoryProps) {
  const [isOpen, setIsOpen] = useState(true)

  if (!history.length) return null

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-3.5 flex items-center justify-between hover:bg-slate-50 transition-colors rounded-xl"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-slate-100 rounded-lg flex items-center justify-center">
            <History className="w-4 h-4 text-slate-500" />
          </div>
          <span className="text-sm font-medium text-slate-700">Histórico de Consultas</span>
          <span className="px-2 py-0.5 bg-slate-100 text-slate-500 text-xs rounded-full">
            {history.length}
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        )}
      </button>

      {isOpen && (
        <div className="border-t border-slate-100 divide-y divide-slate-50">
          {history.map((item) => (
            <button
              key={item.id}
              onClick={() => onSelect(item.question)}
              className="w-full px-5 py-3.5 text-left hover:bg-slate-50 transition-colors group"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm text-slate-700 font-medium group-hover:text-sus-blue-700 truncate transition-colors">
                    {item.question}
                  </p>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                    {item.answer.slice(0, 120)}
                    {item.answer.length > 120 ? '…' : ''}
                  </p>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0 text-xs text-slate-400">
                  <Clock className="w-3 h-3" />
                  {formatTime(item.timestamp)}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
