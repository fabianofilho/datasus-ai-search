import Link from 'next/link'
import { ArrowLeft, Plug, ShieldCheck, Database } from 'lucide-react'

// A URL do connector vem do ambiente de build (Vercel), nunca do código:
// o repositório é público e o endereço do servidor não deve ficar nele.
const MCP_URL = process.env.NEXT_PUBLIC_OMNISUS_MCP_URL || ''

const FERRAMENTAS = [
  { nome: 'listar_bases', descricao: 'Bases do lake com recortes carregados (UF e anos) e número de linhas.' },
  { nome: 'descrever_colunas', descricao: 'Colunas de uma base, com tipo, rótulo e códigos (sexo, raça/cor, local).' },
  { nome: 'buscar_codigos', descricao: 'Código CID-10, de município, UF, ocupação ou país pelo nome, com a faixa pronta para o filtro.' },
  { nome: 'consultar_sql', descricao: 'Um SELECT DuckDB somente leitura, até 50 linhas, pela mesma guarda de segurança.' },
  { nome: 'citar', descricao: 'Citação do arquivo original do DATASUS, com SHA-256 e snapshot, para publicar um número.' },
]

export const metadata = {
  title: 'MCP do omnisus | Saúde · Busca',
  description: 'Use os dados abertos do DATASUS direto no Claude, pelo servidor MCP do omnisus.',
}

export default function McpPage() {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800">
          <ArrowLeft className="w-4 h-4" /> Voltar para a busca
        </Link>

        <h1 className="mt-6 text-3xl font-semibold text-slate-900 tracking-tight">
          Dados do DATASUS no seu Claude
        </h1>
        <p className="mt-3 text-slate-600 leading-relaxed">
          O MCP do omnisus é um servidor do Model Context Protocol que dá ao Claude acesso de leitura a um lake
          DuckDB com dados abertos do DATASUS (SIM, SINASC, SIH, CNES) e população do IBGE, montado pela biblioteca{' '}
          <a href="https://github.com/raphaelfh/omnisus" className="text-sus-blue-600 hover:underline">omnisus</a>.
          O Claude escreve o SQL, as ferramentas resolvem os códigos e cada resposta pode trazer a citação do arquivo
          original.
        </p>

        <section className="mt-10 bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
            <Plug className="w-5 h-5 text-sus-blue-600" /> Como conectar
          </h2>
          {MCP_URL ? (
            <>
              <p className="mt-3 text-sm text-slate-600">Endereço do servidor (Streamable HTTP, sem autenticação):</p>
              <pre className="mt-2 bg-slate-900 text-slate-100 text-sm rounded-lg px-4 py-3 overflow-x-auto">{MCP_URL}</pre>
              <ol className="mt-4 space-y-2 text-sm text-slate-700 list-decimal list-inside">
                <li>No claude.ai: Configurações, Conectores, Adicionar conector personalizado, e cole o endereço acima.</li>
                <li>
                  No Claude Code:{' '}
                  <code className="bg-slate-100 rounded px-1.5 py-0.5">claude mcp add --transport http omnisus {MCP_URL}</code>
                </li>
                <li>Depois, pergunte em português, por exemplo: quantos óbitos por tuberculose houve em Roraima em 2022?</li>
              </ol>
            </>
          ) : (
            <p className="mt-3 text-sm text-slate-600">
              O endereço público do servidor ainda não está configurado neste site.
            </p>
          )}
        </section>

        <section className="mt-6 bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
            <Database className="w-5 h-5 text-sus-blue-600" /> Ferramentas
          </h2>
          <ul className="mt-4 space-y-3">
            {FERRAMENTAS.map((f) => (
              <li key={f.nome} className="text-sm">
                <code className="font-medium text-slate-900">{f.nome}</code>
                <span className="text-slate-600">: {f.descricao}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-6 bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
            <ShieldCheck className="w-5 h-5 text-sus-blue-600" /> O que esperar
          </h2>
          <ul className="mt-4 space-y-2 text-sm text-slate-700 list-disc list-inside">
            <li>Somente leitura: um SELECT por chamada, sem acesso a arquivos nem à rede, com limite de requisições.</li>
            <li>É um lake de demonstração: hoje cobre recortes de Roraima (SIM e SINASC 2022, SIH e CNES de janeiro de 2023) e o censo IBGE 2022.</li>
            <li>Dados abertos e públicos; nenhum dado pessoal identificável.</li>
            <li>O servidor roda numa máquina de pesquisa e pode ficar indisponível sem aviso.</li>
          </ul>
        </section>
      </div>
    </main>
  )
}
