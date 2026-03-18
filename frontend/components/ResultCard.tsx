import { Bot, BarChart2, CheckCircle2 } from 'lucide-react'
import type { SearchResponse } from '@/types'

interface ResultCardProps {
  result: SearchResponse
}

export default function ResultCard({ result }: ResultCardProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm animate-fade-in">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-start gap-3">
        <div className="w-8 h-8 bg-sus-blue-50 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
          <Bot className="w-4 h-4 text-sus-blue-600" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Análise DATASUS</h3>
          <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{result.question}</p>
        </div>
      </div>

      {/* Answer */}
      <div className="px-5 py-4">
        <p className="text-slate-700 leading-relaxed text-sm whitespace-pre-wrap">{result.answer}</p>
      </div>

      {/* Footer */}
      <div className="px-5 py-3 bg-slate-50 rounded-b-xl border-t border-slate-100 flex items-center gap-4">
        <div className="flex items-center gap-1.5 text-xs text-sus-green-700">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Consulta executada com sucesso</span>
        </div>
        {result.row_count > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <BarChart2 className="w-3.5 h-3.5" />
            <span>{result.row_count} {result.row_count === 1 ? 'linha retornada' : 'linhas retornadas'}</span>
          </div>
        )}
      </div>
    </div>
  )
}
