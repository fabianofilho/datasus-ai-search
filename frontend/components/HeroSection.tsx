export default function HeroSection() {
  return (
    <div className="text-center mb-10">
      <div className="inline-flex items-center gap-2 mb-6">
        <span className="text-sus-green-700 text-xs font-semibold tracking-widest uppercase">
          {'--- Plataforma de Pesquisa em Dados Públicos de Saúde'}
        </span>
      </div>

      <h2 className="text-4xl sm:text-5xl font-bold text-slate-900 leading-tight mb-4">
        {'Pergunte sobre '}
        <span className="text-sus-green-700">{'saúde pública'}</span>
        <br />
        {'em '}
        <span
          className="text-sus-green-600 italic"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          {'português'}
        </span>
        {'.'}
      </h2>

      <p className="text-slate-500 text-lg max-w-xl mx-auto">
        {'Sem SQL. Sem fricção. Resposta em segundos.'}
      </p>
    </div>
  )
}
