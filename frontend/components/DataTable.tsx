'use client'

import { useState } from 'react'
import { Table, Download } from 'lucide-react'

interface DataTableProps {
  data: Record<string, unknown>[]
  columns: string[]
  rowCount: number
}

export default function DataTable({ data, columns, rowCount }: DataTableProps) {
  const [page, setPage] = useState(0)
  const pageSize = 10
  const totalPages = Math.ceil(data.length / pageSize)
  const pageData = data.slice(page * pageSize, (page + 1) * pageSize)

  const handleDownload = () => {
    const header = columns.join(',')
    const rows = data
      .map((row) =>
        columns
          .map((col) => {
            const val = row[col]
            const str = val === null || val === undefined ? '' : String(val)
            return str.includes(',') ? `"${str}"` : str
          })
          .join(',')
      )
      .join('\n')
    const csv = `${header}\n${rows}`
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'datasus_resultado.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  if (!data.length) return null

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm animate-fade-in">
      {/* Header */}
      <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-sus-green-50 rounded-lg flex items-center justify-center">
            <Table className="w-4 h-4 text-sus-green-600" />
          </div>
          <span className="text-sm font-medium text-slate-700">Dados da Consulta</span>
          <span className="px-2 py-0.5 bg-sus-green-50 text-sus-green-700 text-xs rounded-full font-medium">
            {rowCount} {rowCount === 1 ? 'linha' : 'linhas'}
          </span>
        </div>

        <button
          onClick={handleDownload}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          CSV
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-50">
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2.5 text-left font-medium text-slate-500 uppercase tracking-wider whitespace-nowrap border-b border-slate-100"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageData.map((row, i) => (
              <tr key={i} className="hover:bg-slate-50 transition-colors border-b border-slate-50">
                {columns.map((col) => (
                  <td key={col} className="px-4 py-2.5 text-slate-700 whitespace-nowrap max-w-xs truncate">
                    {row[col] === null || row[col] === undefined ? (
                      <span className="text-slate-300 italic">—</span>
                    ) : (
                      String(row[col])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-5 py-3 border-t border-slate-100 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            Mostrando {page * pageSize + 1}–{Math.min((page + 1) * pageSize, data.length)} de {data.length}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-100 rounded disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Anterior
            </button>
            <span className="px-2 py-1 text-xs text-slate-500">
              {page + 1} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page === totalPages - 1}
              className="px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-100 rounded disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
