import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { useCashAccounts } from '../../hooks/useCashAccounts'
import CashAccountCard from './CashAccountCard'
import AddCashAccountDialog from '../dialogs/AddCashAccountDialog'

export default function CashSection() {
  const { accounts, loading, error, fetchAccounts } = useCashAccounts()
  const [dialogOpen, setDialogOpen] = useState(false)

  useEffect(() => {
    void fetchAccounts()
  }, [fetchAccounts])

  return (
    <section>
      <h2 className="text-tile-heading text-fg-primary">现金分布</h2>
      <p className="mt-1 text-caption text-fg-tertiary">
        金额失焦自动保存；删除为软删除（数据保留可复盘）
      </p>
      {loading && accounts.length === 0 && (
        <p className="mt-4 text-body text-fg-secondary">加载中…</p>
      )}
      {error && (
        <p className="mt-4 text-body text-finance-down">⚠️ {error}</p>
      )}
      {!error && (
        <div className="mt-6 grid grid-cols-4 gap-4">
          {accounts.map((account) => (
            <CashAccountCard key={account.account_id} account={account} />
          ))}
          <button
            type="button"
            onClick={() => setDialogOpen(true)}
            className="flex min-h-[138px] flex-col items-center justify-center rounded-comfortable border-2 border-dashed border-black/15 bg-brand-light-gray/40 text-fg-tertiary transition-colors hover:border-apple-blue hover:bg-apple-blue/5 hover:text-apple-blue"
          >
            <Plus size={28} strokeWidth={1.5} />
            <span className="mt-2 text-body">新增账户</span>
          </button>
        </div>
      )}
      <AddCashAccountDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
    </section>
  )
}
