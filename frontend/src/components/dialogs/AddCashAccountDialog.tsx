import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { useCashAccounts } from '../../hooks/useCashAccounts'
import { useWealthFreedom } from '../../hooks/useWealthFreedom'
import { toReadableMessage } from '../../utils/errors'
import type { CashOrIncomeCurrency } from '../../types/enums'

interface AddCashAccountDialogProps {
  open: boolean
  onClose: () => void
}

export default function AddCashAccountDialog({
  open,
  onClose,
}: AddCashAccountDialogProps) {
  const { addAccount } = useCashAccounts()
  const { invalidate: invalidateMetrics } = useWealthFreedom()

  const [name, setName] = useState('')
  const [amount, setAmount] = useState('0')
  const [currency, setCurrency] = useState<CashOrIncomeCurrency>('CNY')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setName('')
      setAmount('0')
      setCurrency('CNY')
      setError(null)
      setSubmitting(false)
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  const handleSubmit = async () => {
    const trimmed = name.trim()
    const n = Number(amount)
    if (!trimmed) {
      setError('账户名称不能为空')
      return
    }
    if (!Number.isFinite(n) || n < 0) {
      setError('金额必须 ≥ 0')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await addAccount({ name: trimmed, amount: n, currency })
      invalidateMetrics()
      onClose()
    } catch (err) {
      setError(toReadableMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={onClose}
    >
      <div
        className="w-[440px] rounded-large bg-brand-white p-8 shadow-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-start justify-between">
          <h2 className="text-tile-heading text-fg-primary">新增现金账户</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-standard p-1.5 text-fg-tertiary transition-colors hover:bg-brand-light-gray hover:text-fg-primary"
            aria-label="关闭"
          >
            <X size={20} />
          </button>
        </div>

        <section className="mt-6 space-y-4">
          <div>
            <label className="text-caption text-fg-secondary">账户名称</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：招商银行储蓄卡"
              className="mt-1 w-full rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
            />
          </div>
          <div>
            <label className="text-caption text-fg-secondary">初始金额</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="num mt-1 w-full rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
            />
          </div>
          <div>
            <label className="text-caption text-fg-secondary">币种</label>
            <select
              value={currency}
              onChange={(e) =>
                setCurrency(e.target.value as CashOrIncomeCurrency)
              }
              className="mt-1 w-full rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
            >
              <option value="CNY">CNY 人民币</option>
              <option value="USD">USD 美元</option>
            </select>
          </div>
        </section>

        {error && (
          <p className="mt-4 text-caption text-finance-down">{error}</p>
        )}

        <footer className="mt-8 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-standard border border-black/15 bg-brand-white px-5 py-2 text-body text-fg-secondary transition-colors hover:bg-brand-light-gray"
          >
            取消
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            className="rounded-standard bg-apple-blue px-5 py-2 text-body text-brand-white transition-colors hover:bg-apple-link-light disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? '提交中…' : '新增'}
          </button>
        </footer>
      </div>
    </div>
  )
}
