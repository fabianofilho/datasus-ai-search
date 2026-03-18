'use client'

import { useState } from 'react'
import { Code2, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react'

interface SQLViewerProps {
  sql: string
}

export default function SQLViewer({ sql }: SQLViewerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm animate-fade-in">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-3.5 flex items-center justify-between hover:bg-slate-50 transition-colors rounded-xl"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-amber-50 rounded-lg flex items-center justify-center">
            <Code2 className="w-4 h-4 text-amber-600" />
          </div>
          <span className="text-sm font-medium text-slate-700">SQL Gerado</span>
          <span className="px-2 py-0.5 bg-slate-100 text-slate-500 text-xs rounded-full">DuckDB</span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        )}
      </button>

      {isOpen && (
        <div className="px-5 pb-4 border-t border-slate-100">
          <div className="relative mt-3">
            <pre className="code-block bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto scrollbar-thin text-xs leading-relaxed">
              <code>{sql}</code>
            </pre>
            <button
              onClick={handleCopy}
              className="absolute top-2 right-2 p-1.5 bg-slate-700 hover:bg-slate-600 rounded-md transition-colors"
              title="Copiar SQL"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-green-400" />
              ) : (
                <Copy className="w-3.5 h-3.5 text-slate-300" />
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
