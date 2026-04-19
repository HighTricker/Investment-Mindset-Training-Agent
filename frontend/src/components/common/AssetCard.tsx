import clsx from 'clsx'
import type { AssetDetail } from '../../types/entities'
import { formatPercent } from '../../utils/formatters'

interface AssetCardProps {
  asset: AssetDetail
  onUpdate?: (asset: AssetDetail) => void
}

function deriveTrend(
  rate: number | null,
): 'up' | 'down' | 'neutral' {
  if (rate == null || rate === 0) return 'neutral'
  return rate > 0 ? 'up' : 'down'
}

const CARD_BG: Record<'up' | 'down' | 'neutral', string> = {
  up: 'bg-finance-up/10 border-finance-up/20',
  down: 'bg-finance-down/10 border-finance-down/20',
  neutral: 'bg-brand-light-gray border-black/5',
}

const RATE_COLOR: Record<'up' | 'down' | 'neutral', string> = {
  up: 'text-finance-up',
  down: 'text-finance-down',
  neutral: 'text-fg-secondary',
}

export default function AssetCard({ asset, onUpdate }: AssetCardProps) {
  const trend = deriveTrend(asset.monthly_return_rate)

  return (
    <div
      className={clsx(
        'flex flex-col rounded-large border p-5 transition-colors',
        CARD_BG[trend],
      )}
    >
      <div className="text-caption text-fg-tertiary">{asset.category}</div>
      <div className="mt-2 truncate text-body-emphasis text-fg-primary">
        {asset.name}
      </div>
      <div className="mt-4 text-caption text-fg-tertiary">本月收益率</div>
      <div className={clsx('mt-1 text-tile-heading num', RATE_COLOR[trend])}>
        {formatPercent(asset.monthly_return_rate, true)}
      </div>
      {onUpdate && asset.is_active && (
        <button
          type="button"
          onClick={() => onUpdate(asset)}
          className="mt-5 self-start rounded-standard border border-black/10 bg-brand-white/70 px-3 py-1.5 text-caption text-fg-secondary transition-colors hover:border-black/20 hover:bg-brand-white hover:text-fg-primary"
        >
          更新持仓信息
        </button>
      )}
    </div>
  )
}
