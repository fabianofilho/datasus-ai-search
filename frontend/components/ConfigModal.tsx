'use client'

import { useState, useEffect, useRef } from 'react'
import { X, Key, Globe, Cpu, Save, Database, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import type { AppConfig } from '@/types'
import { MODELS_BY_PROVIDER, API_BASE_DEFAULTS, detectProvider } from '@/types'
import { api } from '@/lib/api'

interface ConfigModalProps {
  isOpen: boolean
  onClose: () => void
  config: AppConfig
  onSave: (config: AppConfig) => void
}

const PROVIDER_LABELS = {
  groq: 'Groq (open-source)',
  openai: 'OpenAI',
  gemini: 'Google Gemini',
  anthropic: 'Anthropic Claude',
}

const DATASET_LABELS: Record<string, string> = {
  sim_do: 'SIM — Mortalidade',
  sih_rd: 'SIH — Internações',
  sia_pa: 'SIA — Ambulatorial',
  ibge_pop: 'IBGE — População',
}

type InitStatus = 'idle' | 'loading' | 'success' | 'error'

export default function ConfigModal({ isOpen, onClose, config, onSave }: ConfigModalProps) {
  const [local, setLocal] = useState<AppConfig>(config)
  const [initStatus, setInitStatus] = useState<InitStatus>('idle')
  const [initMessage, setInitMessage] = useState('')
  const [initProgress, setInitProgress] = useState<{ current: string; completed: string[] }>({ current: '', completed: [] })
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    setLocal(config)
    setInitStatus('idle')
    setInitMessage('')
    setInitProgress({ current: '', completed: [] })
  }, [config, isOpen])

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

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

  const handleInitDb = async () => {
    setInitStatus('loading')
    setInitMessage('')
    setInitProgress({ current: '', completed: [] })
    try {
      await api.initDb()
      // Poll status
      pollRef.current = setInterval(async () => {
        try {
          const s = await api.initDbStatus()
          setInitProgress({ current: s.current, completed: s.completed })
          if (s.status === 'done') {
            clearInterval(pollRef.current!)
            setInitStatus('success')
            setInitMessage('Banco de dados inicializado com sucesso!')
          } else if (s.status === 'error') {
            clearInterval(pollRef.current!)
            setInitStatus('error')
            setInitMessage(s.error || 'Erro ao inicializar')
          }
        } catch {}
      }, 2000)
    } catch (e) {
      setInitStatus('error')
      setInitMessage(e instanceof Error ? e.message : 'Erro ao inicializar banco de dados')
    }
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
              placeholder="gsk_... / sk-... / AIza... / sk-ant-..."
              className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sus-blue-600 focus:border-sus-blue-600 transition-all"
            />
            {local.apiKey ? (
              <p className="text-xs text-slate-500 mt-1">
                Provedor detectado: <span className="font-medium text-sus-blue-600">{PROVIDER_LABELS[provider]}</span>
              </p>
            ) : (
              <p className="text-xs text-slate-500 mt-1">
                Gratis:{' '}
                <a
                  href="https://console.groq.com/keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sus-blue-600 font-medium hover:underline"
                >
                  Groq
                </a>
                {' '}(Llama 3.3, open-source) ou{' '}
                <a
                  href="https://aistudio.google.com/api-keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sus-blue-600 font-medium hover:underline"
                >
                  Google AI Studio
                </a>
                {' '}(Gemini).
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

        {/* Init DB */}
        <div className="px-6 pb-2">
          <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
            <div className="flex items-center gap-2 mb-1">
              <Database className="w-3.5 h-3.5 text-slate-600" />
              <span className="text-sm font-medium text-slate-700">Banco de Dados DATASUS</span>
            </div>
            <p className="text-xs text-slate-500 mb-3">
              Baixa e inicializa os dados de mortalidade, internações, ambulatorial e população. Pode demorar alguns minutos.
            </p>

            {initStatus === 'loading' && (
              <div className="mb-3 space-y-1">
                {Object.entries(DATASET_LABELS).map(([key, label]) => {
                  const done = initProgress.completed.includes(key)
                  const active = initProgress.current === key
                  return (
                    <div key={key} className="flex items-center gap-2 text-xs">
                      {done ? (
                        <CheckCircle className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                      ) : active ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-sus-blue-600 flex-shrink-0" />
                      ) : (
                        <div className="w-3.5 h-3.5 rounded-full border border-slate-300 flex-shrink-0" />
                      )}
                      <span className={done ? 'text-green-700' : active ? 'text-sus-blue-700 font-medium' : 'text-slate-400'}>
                        {label}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
            {initStatus === 'success' && (
              <div className="flex items-center gap-2 text-xs text-green-700 bg-green-50 border border-green-100 rounded-lg px-3 py-2 mb-3">
                <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{initMessage}</span>
              </div>
            )}
            {initStatus === 'error' && (
              <div className="flex items-center gap-2 text-xs text-red-700 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mb-3">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="break-all">{initMessage}</span>
              </div>
            )}

            <button
              onClick={handleInitDb}
              disabled={initStatus === 'loading'}
              className="flex items-center gap-1.5 px-3 py-2 text-xs bg-slate-800 text-white rounded-lg hover:bg-slate-900 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {initStatus === 'loading' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Database className="w-3.5 h-3.5" />
              )}
              {initStatus === 'loading' ? 'Baixando dados...' : 'Inicializar Banco de Dados'}
            </button>
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
