'use client'

import { useState } from 'react'
import { Activity, LayoutGrid, Clock, BookOpen, Code2 } from 'lucide-react'
import ConfigModal from './ConfigModal'
import SchemaModal from './SchemaModal'
import type { AppConfig } from '@/types'

interface HeaderProps {
  config: AppConfig
  onConfigChange: (config: AppConfig) => void
}

export default function Header({ config, onConfigChange }: HeaderProps) {
  const [configOpen, setConfigOpen] = useState(false)
  const [schemaOpen, setSchemaOpen] = useState(false)

  return (
    <>
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-sus-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-slate-900 leading-tight tracking-tight">
                Saúde <span className="text-slate-400 font-normal">·</span> Busca
              </h1>
              <p className="text-[10px] text-slate-400 uppercase tracking-widest font-medium">
                Pesquisa em Dados de Saúde
              </p>
            </div>
          </div>

          <nav className="flex items-center gap-1">
            <button
              onClick={() => setSchemaOpen(true)}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
            >
              <LayoutGrid className="w-4 h-4" />
              <span>Esquema</span>
            </button>

            <button
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
            >
              <Clock className="w-4 h-4" />
              <span>Histórico</span>
            </button>

            <button
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
            >
              <BookOpen className="w-4 h-4" />
              <span>Documentação</span>
            </button>

            <button
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
            >
              <Code2 className="w-4 h-4" />
              <span>API</span>
            </button>

            <div className="w-px h-5 bg-slate-200 mx-2" />

            <button
              onClick={() => setConfigOpen(true)}
              className="px-4 py-1.5 text-sm font-medium text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Entrar
            </button>
          </nav>
        </div>
      </header>

      <ConfigModal
        isOpen={configOpen}
        onClose={() => setConfigOpen(false)}
        config={config}
        onSave={onConfigChange}
      />

      <SchemaModal isOpen={schemaOpen} onClose={() => setSchemaOpen(false)} />
    </>
  )
}
