'use client'

import { useState, useEffect } from 'react'
import { X, Key, Globe, Cpu, Save } from 'lucide-react'
import type { AppConfig } from '@/types'
import { MODELS_BY_PROVIDER, API_BASE_DEFAULTS, detectProvider } from '@/types'

interface ConfigModalProps {
  isOpen: boolean
  onClose: () => void
  config: AppConfig
  onSave: (config: AppConfig) => void
}

const PROVIDER_LABELS = {
  openai: 'OpenAI',
  gemini: 'Google Gemini',
  anthropic: 'Anthropic Claude',
}

export default function ConfigModal({ isOpen, onClose, config, onSave }: ConfigModalProps) {
  const [local, setLocal] = useState<AppConfig>(config)

  useEffect(() => {
    setLocal(config)
  }, [config, isOpen])

  if (!isOpen) return null

  const provider = detectProvider(local.apiKey)
  const models = MODELS_BY_PROVIDER[provider]

  const handleApiKeyChange = (apiKey: string) => {
    const newProvider = detectProvider(apiKey)
    const newModels = MODELS_BY_PROVIDER[newProvider]
    const defaultBase = API_BASE_DEFAULTS[newProvider]

    // Auto-switch apiBase when provider changes (only if it was a known default or empty)
    const knownBases = Object.values(API_BASE_DEFAULTS)
    const shouldUpdateBase = knownBases.includes(local.apiBase) || local.apiBase === ''

    setLocal({
      ...local,
      apiKey,
      model: newModels[0].value,
      apiBase: shouldUpdateBase ? defaultBase : local.apiBase,
    })
  }

  const handleSave = () => {
    onSave(local)
    localStorage.setItem('datasus_config', JSON.stringify(local))
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md animate-fade-in">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Configurações</h2>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              <div className="flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" />
                API Key
              </div>
            </label>
            <input
              type="password"
              value={local.apiKey}
              onChange={(e) => handleApiKeyChange(e.target.value)}
              placeholder="sk-... / AIza... / sk-ant-..."
              className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sus-blue-600 focus:border-sus-blue-600 transition-all"
            />
            {local.apiKey && (
              <p className="text-xs text-slate-500 mt-1">
                Provedor detectado: <span className="font-medium text-sus-blue-600">{PROVIDER_LABELS[provider]}</span>
              </p>
            )}
          </div>

          {/* API Base URL */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              <div className="flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5" />
                API Base URL <span className="text-slate-400 font-normal">(opcional)</span>
              </div>
            </label>
            <input
              type="text"
              value={local.apiBase}
              onChange={(e) => setLocal({ ...local, apiBase: e.target.value })}
              placeholder="https://api.openai.com/v1"
              className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sus-blue-600 focus:border-sus-blue-600 transition-all"
            />
            <p className="text-xs text-slate-500 mt-1">
              Preenchido automaticamente conforme o provedor detectado.
            </p>
          </div>

          {/* Model */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              <div className="flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" />
                Modelo
              </div>
            </label>
            <select
              value={local.model}
              onChange={(e) => setLocal({ ...local, model: e.target.value })}
              className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sus-blue-600 focus:border-sus-blue-600 transition-all bg-white"
            >
              {models.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            className="flex items-center gap-1.5 px-4 py-2 text-sm bg-sus-blue-600 text-white rounded-lg hover:bg-sus-blue-700 transition-colors"
          >
            <Save className="w-3.5 h-3.5" />
            Salvar
          </button>
        </div>
      </div>
    </div>
  )
}
