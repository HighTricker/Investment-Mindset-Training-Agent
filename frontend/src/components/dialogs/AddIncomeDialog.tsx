import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { useIncome } from '../../hooks/useIncome'
import { useWealthFreedom } from '../../hooks/useWealthFreedom'
import { toReadableMessage } from '../../utils/errors'
import type {
  CashOrIncomeCurrency,
  IncomeCategory,
} from '../../types/enums'

interface AddIncomeDialogProps {
  open: boolean
  onClose: () => void
}

const CATEGORIES: IncomeCategory[] = [
  '纯劳动收入',
  '代码&自媒体收入',
  '资本收入',
]

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

export default function AddIncomeDialog({
  open,
  onClose,
}: AddIncomeDialogProps) {
  const { addIncome } = useIncome()
  const { invalidate: invalidateMetrics } = useWealthFreedom()

  const [date, setDate] = useState(today)
  const [name, setName] = useState('')
  const [category, setCategory] = useState<IncomeCategory>('纯劳动收入')
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState<CashOrIncomeCurrency>('CNY')
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setDate(today())
      setName('')
      setCategory('纯劳动收入')
      setAmount('')
      setCurrency('CNY')
      setNote('')
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
    const trimmedName = name.trim()
    const n = Number(amount)
    if (!date) {
      setError('请选择日期')
      return
    }
    if (!trimmedName) {
      setError('名称不能为空')
      return
    }
    if (!Number.isFinite(n) || n === 0) {
      setError('金额必须是非 0 数字（冲正请填负数）')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await addIncome({
        date,
        name: trimmedName,
        category,
        amount: n,
        currency,
        note: note.trim() || null,
      })
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
        className="max-h-[90vh] w-[480px] overflow-y-auto rounded-large bg-brand-white p-8 shadow-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-tile-heading text-fg-primary">新增收入</h2>
            <p className="mt-1 text-caption text-fg-tertiary">
              支持负数作冲正（录错时反向记录，保留历史可复盘）
            </p>
          </div>
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
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-caption text-fg-secondary">日期</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="mt-1 w-full rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
              />
            </div>
            <div>
              <label className="text-caption text-fg-secondary">类别</label>
              <select
                value={category}
                onChange={(e) =>
                  setCategory(e.target.value as IncomeCategory)
                }
                className="mt-1 w-full rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="text-caption text-fg-secondary">名称</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：3 月工资"
              className="mt-1 w-full rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-caption text-fg-secondary">
                金额（负数=冲正）
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="例如 15000 或 -500"
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
                <option value="CNY">CNY</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-caption text-fg-secondary">
              备注（可选）
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={2}
              placeholder="补充说明"
              className="mt-1 w-full resize-none rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
            />
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
