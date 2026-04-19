import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { useIncome } from '../../hooks/useIncome'
import IncomeTypeCards from './IncomeTypeCards'
import IncomeTable from './IncomeTable'
import AddIncomeDialog from '../dialogs/AddIncomeDialog'

export default function IncomeSection() {
  const { data, loading, error, fetchIncome } = useIncome()
  const [dialogOpen, setDialogOpen] = useState(false)

  useEffect(() => {
    void fetchIncome()
  }, [fetchIncome])

  return (
    <section>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-tile-heading text-fg-primary">收入管理</h2>
          <p className="mt-1 text-caption text-fg-tertiary">
            {data ? `当前查看月份 ${data.view_month}` : '当月聚合'} · 不支持删除，录错请新增负数冲正
          </p>
        </div>
        <button
          type="button"
          onClick={() => setDialogOpen(true)}
          className="inline-flex items-center gap-2 rounded-comfortable bg-apple-blue px-4 py-2 text-body text-brand-white transition-colors hover:bg-apple-link-light"
        >
          <Plus size={16} strokeWidth={2} />
          <span>新增收入</span>
        </button>
      </div>

      {loading && !data && (
        <p className="mt-4 text-body text-fg-secondary">加载中…</p>
      )}
      {error && <p className="mt-4 text-body text-finance-down">⚠️ {error}</p>}
      {data && (
        <>
          <div className="mt-6">
            <IncomeTypeCards summary={data.summary} />
          </div>
          <div className="mt-6">
            <IncomeTable records={data.records} />
          </div>
        </>
      )}

      <AddIncomeDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
    </section>
  )
}
