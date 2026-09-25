'use client'

import { useState, useEffect } from 'react'
import { X, Key, Cpu, Save, Database, ExternalLink, ChevronDown } from 'lucide-react'
import type { AppConfig } from '@/types'
import { MODELS_BY_PROVIDER, API_BASE_DEFAULTS, detectProvider } from '@/types'

interface ConfigModalProps {
  isOpen: boolean
  onClose: () => void
  config: AppConfig
  onSave: (config: AppConfig) => void
}

const PROVIDER_LABELS: Record<string, { name: string; badge?: string; color: string }> = {
  groq: { name: 'Groq', badge: 'Grátis', color: 'text-orange-600' },
  openai: { name: 'OpenAI', color: 'text-green-600' },
  gemini: { name: 'Google Gemini', badge: 'Grátis', color: 'text-blue-600' },
  anthropic: { name: 'Anthropic', color: 'text-purple-600' },
}

const QUICK_PROVIDERS = [
  {
    id: 'groq',
    name: 'Groq',
    badge: 'Grátis',
    description: 'Llama 3.3 70B — rápido e sem custo',
    link: 'https://console.groq.com/keys',
    linkLabel: 'Criar chave no Groq',
    prefix: 'gsk_',
    color: 'border-orange-200 bg-orange-50 hover:border-orange-300',
    badgeColor: 'bg-orange-100 text-orange-700',
  },
  {
    id: 'gemini',
    name: 'Google Gemini',
    badge: 'Grátis',
    description: 'Gemini Flash — plano gratuito generoso',
    link: 'https://aistudio.google.com/api-keys',
    linkLabel: 'Criar chave no AI Studio',
    prefix: 'AIza',
    color: 'border-blue-200 bg-blue-50 hover:border-blue-300',
    badgeColor: 'bg-blue-100 text-blue-700',
  },
]

export default function ConfigModal({ isOpen, onClose, config, onSave }: ConfigModalProps) {
  const [local, setLocal] = useState<AppConfig>(config)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const hasKey = !!local.apiKey.trim()
  const provider = detectProvider(local.apiKey)
  const models = MODELS_BY_PROVIDER[provider]
  const providerInfo = PROVIDER_LABELS[provider]

  useEffect(() => {
    setLocal(config)
    setShowAdvanced(false)
  }, [config, isOpen])

  if (!isOpen) return null

  const handleApiKeyChange = (apiKey: string) => {
    const newProvider = detectProvider(apiKey)
    const newModels = MODELS_BY_PROVIDER[newProvider]
    const defaultBase = API_BASE_DEFAULTS[newProvider]
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
          <div>
            <h2 className="text-base font-semibold text-slate-900">Conectar IA</h2>
            <p className="text-xs text-slate-400 mt-0.5">Escolha um provedor gratuito para começar</p>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* Quick provider cards */}
          {!hasKey && (
            <div className="space-y-2">
              {QUICK_PROVIDERS.map((p) => (
                <a
                  key={p.id}
                  href={p.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-colors ${p.color}`}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-800">{p.name}</span>
                      <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${p.badgeColor}`}>
                        {p.badge}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{p.description}</p>
                  </div>
                  <div className="flex items-center gap-1 text-xs font-medium text-slate-600 flex-shrink-0 ml-3">
                    {p.linkLabel}
                    <ExternalLink className="w-3 h-3" />
                  </div>
                </a>
              ))}
            </div>
          )}

          {/* API Key input */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              <div className="flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" />
                {hasKey ? 'Chave de API' : 'Cole sua chave aqui'}
              </div>
            </label>
            <input
              type="password"
              value={local.apiKey}
              onChange={(e) => handleApiKeyChange(e.target.value)}
              placeholder="Cole sua chave aqui (gsk_... ou AIza...)"
              className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sus-green-600 focus:border-sus-green-600 transition-all"
            />
            {hasKey && (
              <p className="text-xs text-slate-500 mt-1">
                Provedor: <span className={`font-semibold ${providerInfo?.color}`}>{providerInfo?.name}</span>
                {providerInfo?.badge && (
                  <span className="ml-1 text-slate-400">({providerInfo.badge})</span>
                )}
              </p>
            )}
          </div>

          {/* Model — only show when key is set */}
          {hasKey && (
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
                className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sus-green-600 focus:border-sus-green-600 transition-all bg-white"
              >
                {models.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
          )}

          {/* Advanced toggle (API Base URL) */}
          {hasKey && (
            <div>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600 transition-colors"
              >
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
                Configurações avançadas
              </button>
              {showAdvanced && (
                <div className="mt-3">
                  <label className="block text-xs font-medium text-slate-600 mb-1">
                    API Base URL
                  </label>
                  <input
                    type="text"
                    value={local.apiBase}
                    onChange={(e) => setLocal({ ...local, apiBase: e.target.value })}
                    placeholder="https://api.openai.com/v1"
                    className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sus-green-600 transition-all"
                  />
                  <p className="text-xs text-slate-400 mt-1">Preenchido automaticamente pelo provedor.</p>
                </div>
              )}
            </div>
          )}

          {/* Dados DATASUS */}
          <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
            <div className="flex items-center gap-2 mb-1">
              <Database className="w-3.5 h-3.5 text-slate-600" />
              <span className="text-sm font-medium text-slate-700">Dados DATASUS</span>
            </div>
            <p className="text-xs text-slate-500">
              Os dados sao baixados sob demanda. Faca uma pergunta: se faltar dado, um aviso pede o
              estado e o ano, e o download fica limitado a poucas combinacoes por vez.
            </p>
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
            disabled={!hasKey}
            className="flex items-center gap-1.5 px-4 py-2 text-sm bg-sus-green-700 text-white rounded-lg hover:bg-sus-green-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Save className="w-3.5 h-3.5" />
            Salvar
          </button>
        </div>
      </div>
    </div>
  )
}
