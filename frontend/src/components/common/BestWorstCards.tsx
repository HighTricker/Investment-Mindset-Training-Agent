import clsx from 'clsx'
import type { BestWorstAsset } from '../../types/entities'
import { formatPercent } from '../../utils/formatters'

interface BestWorstCardsProps {
  best: BestWorstAsset | null
  worst: BestWorstAsset | null
}

type Variant = 'up' | 'down'

const CARD_BG: Record<Variant, string> = {
  up: 'bg-finance-up/10 border-finance-up/20',
  down: 'bg-finance-down/10 border-finance-down/20',
}

const RATE_COLOR: Record<Variant, string> = {
  up: 'text-finance-up',
  down: 'text-finance-down',
}

function Card({
  title,
  asset,
  variant,
}: {
  title: string
  asset: BestWorstAsset | null
  variant: Variant
}) {
  return (
    <div className={clsx('rounded-comfortable border p-6', CARD_BG[variant])}>
      <div className="text-caption text-fg-tertiary">{title}</div>
      {asset ? (
        <>
          <div className="mt-2 truncate text-body-emphasis text-fg-primary">
            {asset.name}
          </div>
          <div className="mt-1 text-caption text-fg-secondary">
            {asset.category}
          </div>
          <div
            className={clsx('mt-4 text-tile-heading num', RATE_COLOR[variant])}
          >
            {formatPercent(asset.monthly_return_rate, true)}
          </div>
        </>
      ) : (
        <div className="mt-4 text-body text-fg-tertiary">此处无内容</div>
      )}
    </div>
  )
}

export default function BestWorstCards({ best, worst }: BestWorstCardsProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <Card title="本月最佳" asset={best} variant="up" />
      <Card title="本月最差" asset={worst} variant="down" />
    </div>
  )
}
