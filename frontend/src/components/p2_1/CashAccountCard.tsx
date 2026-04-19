import { useEffect, useState } from 'react'
import { Trash2 } from 'lucide-react'
import { useCashAccounts } from '../../hooks/useCashAccounts'
import { useWealthFreedom } from '../../hooks/useWealthFreedom'
import { toReadableMessage } from '../../utils/errors'
import type { CashAccount } from '../../types/entities'

interface CashAccountCardProps {
  account: CashAccount
}

export default function CashAccountCard({ account }: CashAccountCardProps) {
  const { updateAccount, deleteAccount } = useCashAccounts()
  const { invalidate: invalidateMetrics } = useWealthFreedom()

  const [draft, setDraft] = useState(String(account.amount))
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setDraft(String(account.amount))
  }, [account.amount])

  const commitAmount = async () => {
    const n = Number(draft)
    if (!Number.isFinite(n) || n < 0) {
      setDraft(String(account.amount))
      setError('金额必须 ≥ 0')
      return
    }
    setError(null)
    if (n === account.amount) return
    try {
      await updateAccount(account.account_id, { amount: n })
      invalidateMetrics()
    } catch (err) {
      setDraft(String(account.amount))
      setError(toReadableMessage(err))
    }
  }

  const handleDelete = async () => {
    const confirmed = window.confirm(
      `确定删除账户「${account.name}」吗？\n删除后该账户将从活跃列表中移除（软删除，数据保留）。`,
    )
    if (!confirmed) return
    setDeleting(true)
    setError(null)
    try {
      await deleteAccount(account.account_id)
      invalidateMetrics()
    } catch (err) {
      setError(toReadableMessage(err))
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="rounded-comfortable border border-black/5 bg-brand-white p-5">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="truncate text-body-emphasis text-fg-primary">
            {account.name}
          </div>
          <div className="text-caption text-fg-tertiary">{account.currency}</div>
        </div>
        <button
          type="button"
          onClick={handleDelete}
          disabled={deleting}
          className="rounded-standard p-1.5 text-fg-tertiary transition-colors hover:bg-finance-down/10 hover:text-finance-down disabled:cursor-not-allowed disabled:opacity-60"
          aria-label="删除账户"
        >
          <Trash2 size={16} strokeWidth={1.75} />
        </button>
      </div>
      <div className="mt-4">
        <input
          type="number"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={() => void commitAmount()}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.currentTarget.blur()
            }
          }}
          className="num w-full rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-tile-heading text-fg-primary outline-none focus:border-apple-blue"
        />
      </div>
      {error && (
        <p className="mt-2 text-caption text-finance-down">{error}</p>
      )}
    </div>
  )
}
