import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import clsx from 'clsx'
import { useAssets } from '../../hooks/useAssets'
import { toReadableMessage } from '../../utils/errors'
import {
  formatCurrency,
  formatNumber,
} from '../../utils/formatters'
import {
  inputToQuantity,
  UNIT_LABELS,
  type InputUnit,
} from '../../utils/unitConverter'
import type { AssetDetail } from '../../types/entities'

type Action = 'buy' | 'sell' | 'close'

interface UpdatePositionDialogProps {
  asset: AssetDetail | null
  onClose: () => void
}

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

export default function UpdatePositionDialog({
  asset,
  onClose,
}: UpdatePositionDialogProps) {
  const { addTransaction, closeAsset, summary } = useAssets()
  const usdToCny = summary?.usd_to_cny ?? null

  const [action, setAction] = useState<Action>('buy')
  const [unit, setUnit] = useState<InputUnit>('shares')
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')
  const [exchangeRate, setExchangeRate] = useState('')
  const [date, setDate] = useState(today)
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const open = asset !== null

  useEffect(() => {
    if (open && asset) {
      setAction('buy')
      setUnit('shares')
      setQuantity('')
      setPrice(
        asset.current_price_original != null
          ? String(asset.current_price_original)
          : '',
      )
      setExchangeRate(
        asset.exchange_rate_to_cny != null
          ? String(asset.exchange_rate_to_cny)
          : '',
      )
      setDate(today())
      setReason('')
      setError(null)
      setSubmitting(false)
    }
  }, [open, asset])

  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  const handleSubmit = async () => {
    if (!asset) return
    setError(null)

    if (action === 'close') {
      setSubmitting(true)
      try {
        await closeAsset(asset.asset_id, reason.trim() || null)
        onClose()
      } catch (err) {
        setError(toReadableMessage(err))
      } finally {
        setSubmitting(false)
      }
      return
    }

    const inputVal = Number(quantity)
    const p = Number(price)
    const r = Number(exchangeRate)
    if (!Number.isFinite(inputVal) || inputVal <= 0) {
      setError(unit === 'shares' ? '数量必须大于 0' : '金额必须大于 0')
      return
    }
    if (!Number.isFinite(p) || p <= 0) {
      setError(action === 'buy' ? '买入价必须大于 0' : '卖出价必须大于 0')
      return
    }
    if (!Number.isFinite(r) || r <= 0) {
      setError('汇率必须大于 0')
      return
    }
    if (!date) {
      setError('请选择日期')
      return
    }
    if (unit === 'USD' && (!usdToCny || usdToCny <= 0)) {
      setError('USD 汇率未就绪，请先在 P1 刷新市场数据')
      return
    }
    const q = inputToQuantity({
      input: inputVal,
      unit,
      price: p,
      rateToCny: r,
      usdToCny: usdToCny ?? 0,
    })
    if (!Number.isFinite(q) || q <= 0) {
      setError('换算后股数无效，请检查输入')
      return
    }

    setSubmitting(true)
    try {
      await addTransaction({
        asset_id: asset.asset_id,
        type: action,
        quantity: q,
        price: p,
        exchange_rate_to_cny: r,
        date,
        reason: reason.trim() || null,
      })
      onClose()
    } catch (err) {
      setError(toReadableMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (!open || !asset) return null

  const submitLabel = submitting
    ? '提交中…'
    : action === 'buy'
      ? '确认加仓'
      : action === 'sell'
        ? '确认减仓'
        : '确认关闭'

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-[520px] overflow-y-auto rounded-large bg-brand-white p-8 shadow-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-tile-heading text-fg-primary">更新持仓信息</h2>
            <p className="mt-1 text-caption text-fg-tertiary">
              {asset.name} · {asset.category} · {asset.symbol}
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

        <section className="mt-6 rounded-comfortable bg-brand-light-gray px-5 py-4">
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-caption">
            <div>
              <span className="text-fg-tertiary">当前持仓：</span>
              <span className="num text-fg-primary">
                {formatNumber(asset.quantity, 4)}
              </span>
            </div>
            <div>
              <span className="text-fg-tertiary">持仓成本：</span>
              <span className="num text-fg-primary">
                {formatCurrency(asset.cost_price_original, asset.currency)}
              </span>
            </div>
            <div>
              <span className="text-fg-tertiary">现价：</span>
              <span className="num text-fg-primary">
                {formatCurrency(asset.current_price_original, asset.currency)}
              </span>
            </div>
            <div>
              <span className="text-fg-tertiary">当前价值：</span>
              <span className="num text-fg-primary">
                {formatCurrency(asset.current_value_cny, 'CNY')}
              </span>
            </div>
          </div>
        </section>

        <div className="mt-6 flex gap-1 rounded-comfortable bg-brand-light-gray p-1">
          <ActionTab
            label="加仓"
            active={action === 'buy'}
            onClick={() => setAction('buy')}
          />
          <ActionTab
            label="减仓"
            active={action === 'sell'}
            onClick={() => setAction('sell')}
          />
          <ActionTab
            label="关闭持仓"
            active={action === 'close'}
            onClick={() => setAction('close')}
            variant="danger"
          />
        </div>

        <section className="mt-6 space-y-4">
          {(action === 'buy' || action === 'sell') && (
            <>
              <QuantityField
                unit={unit}
                onUnitChange={setUnit}
                value={quantity}
                onChange={setQuantity}
                converted={inputToQuantity({
                  input: Number(quantity),
                  unit,
                  price: Number(price),
                  rateToCny: Number(exchangeRate),
                  usdToCny: usdToCny ?? 0,
                })}
                action={action}
                maxShares={action === 'sell' ? asset.quantity : null}
              />
              <Field
                label={
                  action === 'buy'
                    ? `买入价（${asset.currency}）`
                    : `卖出价（${asset.currency}）`
                }
                value={price}
                onChange={setPrice}
                type="number"
              />
              <Field
                label="汇率（对 CNY）"
                value={exchangeRate}
                onChange={setExchangeRate}
                type="number"
                disabled={asset.currency === 'CNY'}
              />
              <Field
                label="日期"
                value={date}
                onChange={setDate}
                type="date"
              />
            </>
          )}
          {action === 'close' && (
            <p className="text-body text-fg-secondary">
              关闭后该资产将从活跃列表中移除，历史交易保留可追溯（写入 close 记录）。此操作不可自动撤销。
            </p>
          )}
          <div>
            <label className="text-caption text-fg-secondary">
              {action === 'close' ? '关闭原因（可选）' : '操作理由（可选）'}
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="记录当下的决策逻辑"
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
            className={clsx(
              'rounded-standard px-5 py-2 text-body text-brand-white transition-colors disabled:cursor-not-allowed disabled:opacity-60',
              action === 'close'
                ? 'bg-finance-down hover:bg-finance-down/80'
                : 'bg-apple-blue hover:bg-apple-link-light',
            )}
          >
            {submitLabel}
          </button>
        </footer>
      </div>
    </div>
  )
}

function ActionTab({
  label,
  active,
  onClick,
  variant = 'default',
}: {
  label: string
  active: boolean
  onClick: () => void
  variant?: 'default' | 'danger'
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'flex-1 rounded-standard px-4 py-2 text-body transition-colors',
        active
          ? variant === 'danger'
            ? 'bg-brand-white font-semibold text-finance-down'
            : 'bg-brand-white font-semibold text-fg-primary'
          : 'text-fg-secondary hover:text-fg-primary',
      )}
    >
      {label}
    </button>
  )
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  disabled = false,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  type?: string
  placeholder?: string
  disabled?: boolean
}) {
  return (
    <div>
      <label className="text-caption text-fg-secondary">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="mt-1 w-full rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue disabled:bg-brand-light-gray disabled:opacity-60"
      />
    </div>
  )
}

function QuantityField({
  unit,
  onUnitChange,
  value,
  onChange,
  converted,
  action,
  maxShares,
}: {
  unit: InputUnit
  onUnitChange: (u: InputUnit) => void
  value: string
  onChange: (v: string) => void
  converted: number
  action: 'buy' | 'sell'
  maxShares: number | null
}) {
  const verb = action === 'buy' ? '加仓' : '减仓'
  const label = unit === 'shares' ? `${verb}数量（股）` : `${verb}金额（${unit}）`
  const placeholder =
    unit === 'shares'
      ? action === 'sell' && maxShares != null
        ? `最多 ${formatNumber(maxShares, 4)}`
        : '例如 5'
      : unit === 'USD'
        ? '例如 1'
        : '例如 1000'
  const showHelper = unit !== 'shares' && Number(value) > 0 && converted > 0
  return (
    <div>
      <div className="flex items-center justify-between">
        <label className="text-caption text-fg-secondary">{label}</label>
        <UnitTabs unit={unit} onChange={onUnitChange} />
      </div>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
      />
      {showHelper && (
        <p className="mt-1.5 text-caption text-fg-tertiary">
          ≈ <span className="num">{converted.toFixed(8)}</span> 股
        </p>
      )}
    </div>
  )
}

function UnitTabs({
  unit,
  onChange,
}: {
  unit: InputUnit
  onChange: (u: InputUnit) => void
}) {
  const units: InputUnit[] = ['shares', 'USD', 'CNY']
  return (
    <div className="flex gap-0.5 rounded-standard bg-brand-light-gray p-0.5">
      {units.map((u) => (
        <button
          key={u}
          type="button"
          onClick={() => onChange(u)}
          className={clsx(
            'rounded-standard px-2.5 py-0.5 text-caption transition-colors',
            unit === u
              ? 'bg-brand-white font-semibold text-fg-primary'
              : 'text-fg-tertiary hover:text-fg-secondary',
          )}
        >
          {UNIT_LABELS[u]}
        </button>
      ))}
    </div>
  )
}
