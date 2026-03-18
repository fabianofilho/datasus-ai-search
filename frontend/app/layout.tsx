import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DATASUS AI Search — Análise de Dados de Saúde com IA',
  description:
    'Pesquise dados epidemiológicos do DATASUS usando linguagem natural. Análise de mortalidade, internações, procedimentos ambulatoriais e dados populacionais.',
  keywords: ['DATASUS', 'SUS', 'saúde pública', 'epidemiologia', 'IA', 'dados de saúde', 'Brasil'],
  authors: [{ name: 'DATASUS AI Search' }],
  openGraph: {
    title: 'DATASUS AI Search',
    description: 'Análise de dados de saúde pública com Inteligência Artificial',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-slate-50">{children}</body>
    </html>
  )
}
