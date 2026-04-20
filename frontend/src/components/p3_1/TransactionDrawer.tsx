import { useEffect, useState } from 'react'
import clsx from 'clsx'
import { X } from 'lucide-react'
import type { AssetTransactionsResponse } from '../../types/entities'
import type { TransactionType } from '../../types/enums'
import { fetchAssetTransactions } from '../../services/api/transactions'
import { useAssets } from '../../hooks/useAssets'
import {
  formatCurrency,
  formatDate,
  formatNumber,
} from '../../utils/formatters'
import { toReadableMessage } from '../../utils/errors'

interface TransactionDrawerProps {
  assetId: number | null
  onClose: () => void
}

const TYPE_META: Record<
  TransactionType,
  { label: string; className: string }
> = {
  buy: { label: '买入', className: 'bg-finance-up/10 text-finance-up' },
  sell: { label: '卖出', className: 'bg-finance-down/10 text-finance-down' },
  close: {
    label: '关闭',
    className: 'bg-fg-tertiary/10 text-fg-tertiary',
  },
}

export default function TransactionDrawer({
  assetId,
  onClose,
}: TransactionDrawerProps) {
  const { assets } = useAssets()
  const [data, setData] = useState<AssetTransactionsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const open = assetId !== null

  useEffect(() => {
    if (assetId === null) return
    let cancelled = false
    setLoading(true)
    setError(null)
    setData(null)
    fetchAssetTransactions(assetId)
      .then((res) => {
        if (!cancelled) setData(res)
      })
      .catch((err) => {
        if (!cancelled) setError(toReadableMessage(err))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [assetId])

  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  const assetInList =
    assetId != null ? assets.find((a) => a.asset_id === assetId) : undefined
  const currency = assetInList?.currency ?? 'CNY'

  return (
    <div
      className={clsx(
        'pointer-events-none fixed inset-0 z-50 transition-opacity duration-300',
        open ? 'opacity-100' : 'opacity-0',
      )}
    >
      <div className="absolute inset-0 bg-black/40" />
      <aside
        className={clsx(
          'fixed right-0 top-0 flex h-screen w-[400px] max-w-[90vw] flex-col',
          'bg-brand-white shadow-card',
          'transition-transform duration-300 ease-out',
          open && 'pointer-events-auto',
          open ? 'translate-x-0' : 'translate-x-full',
        )}
      >
        <header className="flex items-start justify-between border-b border-black/5 px-6 py-5">
          <div>
            {data ? (
              <>
                <h2 className="text-tile-heading text-fg-primary">
                  {data.asset.name}
                  <span className="ml-2 text-body text-fg-secondary">
                    {data.asset.symbol}
                  </span>
                </h2>
                <span
                  className={clsx(
                    'mt-2 inline-block rounded-standard px-2 py-0.5 text-caption',
                    data.asset.is_active
                      ? 'bg-finance-up/10 text-finance-up'
                      : 'bg-fg-tertiary/10 text-fg-tertiary',
                  )}
                >
                  {data.asset.is_active ? '活跃' : '已关闭'}
                </span>
              </>
            ) : (
              <h2 className="text-tile-heading text-fg-primary">交易历史</h2>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1 text-fg-secondary transition-colors hover:bg-brand-light-gray"
            aria-label="关闭"
          >
            <X size={20} />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-5">
          {loading && <p className="text-body text-fg-secondary">加载中…</p>}
          {error && <p className="text-body text-finance-down">⚠️ {error}</p>}
          {data && !loading && !error && (
            <ul className="space-y-5">
              {data.transactions.map((tx) => {
                const meta = TYPE_META[tx.type]
                return (
                  <li
                    key={tx.transaction_id}
                    className="border-b border-black/5 pb-4 last:border-0"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={clsx(
                          'rounded-standard px-2 py-0.5 text-caption font-semibold',
                          meta.className,
                        )}
                      >
                        {meta.label}
                      </span>
                      <span className="text-caption text-fg-secondary">
                        {formatDate(tx.date)}
                      </span>
                    </div>
                    {tx.type !== 'close' && (
                      <p className="mt-1.5 text-body text-fg-primary">
                        {formatNumber(tx.quantity, 4)} ×{' '}
                        {formatCurrency(tx.price, currency)}
                      </p>
                    )}
                    <p className="mt-1.5 text-body">
                      {tx.reason ? (
                        <span className="text-fg-secondary">{tx.reason}</span>
                      ) : (
                        <span className="italic text-fg-tertiary">
                          未填写理由
                        </span>
                      )}
                    </p>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </aside>
    </div>
  )
}
