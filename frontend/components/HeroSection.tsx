import { TrendingUp, Users, Hospital, Activity } from 'lucide-react'

export default function HeroSection() {
  return (
    <div className="text-center mb-8">
      <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-3">
        Pesquise dados de saúde pública{' '}
        <span className="text-sus-blue-600">com Inteligência Artificial</span>
      </h2>
      <p className="text-slate-500 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
        Faça perguntas em português natural sobre mortalidade, internações, procedimentos ambulatoriais
        e dados populacionais do DATASUS sem precisar saber SQL.
      </p>

      {/* Dataset pills */}
      <div className="flex flex-wrap items-center justify-center gap-2 mt-5">
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 border border-red-100 rounded-full text-xs text-red-700">
          <Activity className="w-3 h-3" />
          SIM — Mortalidade
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 border border-blue-100 rounded-full text-xs text-blue-700">
          <Hospital className="w-3 h-3" />
          SIH — Internações
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 border border-green-100 rounded-full text-xs text-green-700">
          <TrendingUp className="w-3 h-3" />
          SIA — Ambulatorial
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-50 border border-purple-100 rounded-full text-xs text-purple-700">
          <Users className="w-3 h-3" />
          IBGE — População
        </div>
      </div>
    </div>
  )
}
