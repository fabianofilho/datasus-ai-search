'use client'

import { useState } from 'react'
import { Settings, Database, Activity } from 'lucide-react'
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
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-sus-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-slate-900 leading-tight">
                DATASUS AI Search
              </h1>
              <p className="text-xs text-slate-500 hidden sm:block">
                Análise de dados de saúde pública com IA
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSchemaOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <Database className="w-4 h-4" />
              <span className="hidden sm:inline">Schema</span>
            </button>

            <button
              onClick={() => setConfigOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <Settings className="w-4 h-4" />
              <span className="hidden sm:inline">Configurar</span>
            </button>

            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-sus-green-50 text-sus-green-700 rounded-lg">
              <div className="w-2 h-2 bg-sus-green-600 rounded-full animate-pulse" />
              <span className="text-xs font-medium">SUS</span>
            </div>
          </div>
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
