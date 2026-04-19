import clsx from 'clsx'

interface SummaryCardProps {
  label: string
  value: string
  trend?: 'up' | 'down' | 'neutral'
}

const TREND_BG: Record<NonNullable<SummaryCardProps['trend']>, string> = {
  up: 'bg-finance-up/10 border-finance-up/20',
  down: 'bg-finance-down/10 border-finance-down/20',
  neutral: 'bg-brand-white border-black/5',
}

const TREND_VALUE_COLOR: Record<NonNullable<SummaryCardProps['trend']>, string> =
  {
    up: 'text-finance-up',
    down: 'text-finance-down',
    neutral: 'text-fg-primary',
  }

export default function SummaryCard({
  label,
  value,
  trend = 'neutral',
}: SummaryCardProps) {
  return (
    <div
      className={clsx(
        'rounded-comfortable border p-6 transition-colors',
        TREND_BG[trend],
      )}
    >
      <div className="text-caption text-fg-tertiary">{label}</div>
      <div
        className={clsx(
          'mt-3 text-tile-heading num',
          TREND_VALUE_COLOR[trend],
        )}
      >
        {value}
      </div>
    </div>
  )
}
