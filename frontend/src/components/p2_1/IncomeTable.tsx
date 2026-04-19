import clsx from 'clsx'
import { formatCurrency, formatDate } from '../../utils/formatters'
import type { IncomeRecord } from '../../types/entities'

interface IncomeTableProps {
  records: IncomeRecord[]
}

export default function IncomeTable({ records }: IncomeTableProps) {
  if (records.length === 0) {
    return (
      <p className="text-body text-fg-tertiary">本月暂无收入记录</p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-comfortable border border-black/10">
      <table className="w-full border-collapse text-caption">
        <thead className="bg-brand-light-gray">
          <tr>
            <th className="whitespace-nowrap px-3 py-3 text-left font-semibold text-fg-secondary">
              日期
            </th>
            <th className="px-3 py-3 text-left font-semibold text-fg-secondary">
              名称
            </th>
            <th className="whitespace-nowrap px-3 py-3 text-left font-semibold text-fg-secondary">
              类别
            </th>
            <th className="whitespace-nowrap px-3 py-3 text-right font-semibold text-fg-secondary">
              金额
            </th>
            <th className="whitespace-nowrap px-3 py-3 text-left font-semibold text-fg-secondary">
              币种
            </th>
            <th className="px-3 py-3 text-left font-semibold text-fg-secondary">
              备注
            </th>
          </tr>
        </thead>
        <tbody>
          {records.map((rec) => {
            const isReversal = rec.amount < 0
            return (
              <tr
                key={rec.income_id}
                className="border-t border-black/5 transition-colors hover:bg-brand-light-gray/50"
              >
                <td className="num whitespace-nowrap px-3 py-3">
                  {formatDate(rec.date)}
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2">
                    <span>{rec.name}</span>
                    {isReversal && (
                      <span className="rounded bg-finance-down/10 px-1.5 py-0.5 text-nano text-finance-down">
                        冲正
                      </span>
                    )}
                  </div>
                </td>
                <td className="whitespace-nowrap px-3 py-3 text-fg-secondary">
                  {rec.category}
                </td>
                <td
                  className={clsx(
                    'num whitespace-nowrap px-3 py-3 text-right',
                    isReversal ? 'text-finance-down' : 'text-fg-primary',
                  )}
                >
                  {formatCurrency(rec.amount, rec.currency)}
                </td>
                <td className="num px-3 py-3">{rec.currency}</td>
                <td className="px-3 py-3 text-fg-secondary">
                  {rec.note || '—'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
