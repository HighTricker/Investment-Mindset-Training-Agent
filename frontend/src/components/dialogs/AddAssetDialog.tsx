import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import clsx from 'clsx'
import { useAssets } from '../../hooks/useAssets'
import { lookupSymbol } from '../../services/api/market'
import { toReadableMessage } from '../../utils/errors'
import {
  inputToQuantity,
  UNIT_LABELS,
  type InputUnit,
} from '../../utils/unitConverter'
import type { SymbolLookupResponse } from '../../types/api'

interface AddAssetDialogProps {
  open: boolean
  onClose: () => void
}

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

export default function AddAssetDialog({
  open,
  onClose,
}: AddAssetDialogProps) {
  const { addAsset } = useAssets()

  const [symbol, setSymbol] = useState('')
  const [lookup, setLookup] = useState<SymbolLookupResponse | null>(null)
  const [lookingUp, setLookingUp] = useState(false)
  const [lookupError, setLookupError] = useState<string | null>(null)

  const [quantity, setQuantity] = useState('')
  const [unit, setUnit] = useState<InputUnit>('shares')
  const [price, setPrice] = useState('')
  const [exchangeRate, setExchangeRate] = useState('')
  const [date, setDate] = useState(today)
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setSymbol('')
      setLookup(null)
      setLookupError(null)
      setQuantity('')
      setUnit('shares')
      setPrice('')
      setExchangeRate('')
      setDate(today())
      setReason('')
      setSubmitError(null)
      setLookingUp(false)
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

  const handleLookup = async () => {
    const trimmed = symbol.trim()
    if (!trimmed) return
    setLookingUp(true)
    setLookupError(null)
    try {
      const result = await lookupSymbol(trimmed)
      setLookup(result)
      setPrice(String(result.current_price_original))
      setExchangeRate(String(result.exchange_rate_to_cny))
    } catch (err) {
      setLookup(null)
      setLookupError(toReadableMessage(err))
    } finally {
      setLookingUp(false)
    }
  }

  const handleResetLookup = () => {
    setLookup(null)
    setLookupError(null)
    setSymbol('')
    setQuantity('')
    setPrice('')
    setExchangeRate('')
    setReason('')
    setSubmitError(null)
  }

  const handleSubmit = async () => {
    if (!lookup) return
    const inputVal = Number(quantity)
    const p = Number(price)
    const r = Number(exchangeRate)
    if (!Number.isFinite(inputVal) || inputVal <= 0) {
      setSubmitError(
        unit === 'shares' ? '持仓数量必须大于 0' : '投入金额必须大于 0',
      )
      return
    }
    if (!Number.isFinite(p) || p <= 0) {
      setSubmitError('买入价必须大于 0')
      return
    }
    if (!Number.isFinite(r) || r <= 0) {
      setSubmitError('汇率必须大于 0')
      return
    }
    if (!date) {
      setSubmitError('请选择买入日期')
      return
    }
    const q = inputToQuantity({
      input: inputVal,
      unit,
      price: p,
      rateToCny: r,
      usdToCny: lookup.usd_to_cny,
    })
    if (!Number.isFinite(q) || q <= 0) {
      setSubmitError('换算后的股数无效，请检查价格和汇率')
      return
    }
    setSubmitting(true)
    setSubmitError(null)
    try {
      await addAsset({
        symbol: lookup.symbol,
        name: lookup.name,
        category: lookup.category,
        currency: lookup.currency,
        quantity: q,
        price: p,
        exchange_rate_to_cny: r,
        date,
        reason: reason.trim() || null,
      })
      onClose()
    } catch (err) {
      setSubmitError(toReadableMessage(err))
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
        className="max-h-[90vh] w-[520px] overflow-y-auto rounded-large bg-brand-white p-8 shadow-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-tile-heading text-fg-primary">添加资产</h2>
            <p className="mt-1 text-caption text-fg-tertiary">
              输入交易代码查询后补全持仓信息
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

        <section className="mt-6">
          <label className="text-caption text-fg-secondary">交易代码</label>
          <div className="mt-1 flex gap-2">
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="AAPL / 00700.HK / BTC-USD / 600519"
              className="flex-1 rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue disabled:bg-brand-light-gray"
              disabled={lookingUp || !!lookup}
            />
            {lookup ? (
              <button
                type="button"
                onClick={handleResetLookup}
                className="rounded-standard border border-black/15 bg-brand-white px-4 py-2 text-body text-fg-secondary transition-colors hover:bg-brand-light-gray"
              >
                重查
              </button>
            ) : (
              <button
                type="button"
                onClick={handleLookup}
                disabled={!symbol.trim() || lookingUp}
                className="rounded-standard bg-apple-blue px-4 py-2 text-body text-brand-white transition-colors hover:bg-apple-link-light disabled:cursor-not-allowed disabled:opacity-60"
              >
                {lookingUp ? '查询中…' : '查询'}
              </button>
            )}
          </div>
          {lookupError && (
            <p className="mt-2 text-caption text-finance-down">{lookupError}</p>
          )}
        </section>

        {lookup && (
          <>
            <section className="mt-6 rounded-comfortable bg-brand-light-gray px-5 py-4">
              <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-caption">
                <div>
                  <span className="text-fg-tertiary">资产名称：</span>
                  <span className="text-fg-primary">{lookup.name}</span>
                </div>
                <div>
                  <span className="text-fg-tertiary">类别：</span>
                  <span className="text-fg-primary">{lookup.category}</span>
                </div>
                <div>
                  <span className="text-fg-tertiary">币种：</span>
                  <span className="num text-fg-primary">{lookup.currency}</span>
                </div>
                <div>
                  <span className="text-fg-tertiary">最新价：</span>
                  <span className="num text-fg-primary">
                    {lookup.current_price_original}
                  </span>
                </div>
              </div>
            </section>

            <section className="mt-6 space-y-4">
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
                  usdToCny: lookup.usd_to_cny,
                })}
              />
              <Field
                label={`买入价（${lookup.currency}）`}
                value={price}
                onChange={setPrice}
                type="number"
                placeholder="默认预填当前价，可修改"
              />
              <Field
                label="汇率（对 CNY）"
                value={exchangeRate}
                onChange={setExchangeRate}
                type="number"
                placeholder="默认预填当前汇率，可修改"
                disabled={lookup.currency === 'CNY'}
              />
              <Field
                label="买入日期"
                value={date}
                onChange={setDate}
                type="date"
              />
              <div>
                <label className="text-caption text-fg-secondary">
                  购买理由（可选）
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={3}
                  placeholder="记录当下的投资逻辑，便于日后复盘"
                  className="mt-1 w-full resize-none rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
                />
              </div>
            </section>

            {submitError && (
              <p className="mt-4 text-caption text-finance-down">
                {submitError}
              </p>
            )}
          </>
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
            disabled={!lookup || submitting}
            className="rounded-standard bg-apple-blue px-5 py-2 text-body text-brand-white transition-colors hover:bg-apple-link-light disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? '提交中…' : '提交'}
          </button>
        </footer>
      </div>
    </div>
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
}: {
  unit: InputUnit
  onUnitChange: (u: InputUnit) => void
  value: string
  onChange: (v: string) => void
  converted: number
}) {
  const label = unit === 'shares' ? '持仓数量' : `投入金额（${unit}）`
  const placeholder =
    unit === 'shares' ? '例如 10' : unit === 'USD' ? '例如 1' : '例如 1000'
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
