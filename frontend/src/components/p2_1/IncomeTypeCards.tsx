import clsx from 'clsx'
import { ArrowDown, ArrowUp, Minus } from 'lucide-react'
import { formatCurrency, formatPercent } from '../../utils/formatters'
import type { IncomeCategorySummary } from '../../types/entities'
import type { IncomeCategory } from '../../types/enums'

interface IncomeTypeCardsProps {
  summary: IncomeCategorySummary[]
}

const ORDER: IncomeCategory[] = [
  '纯劳动收入',
  '代码&自媒体收入',
  '资本收入',
]

function findByCategory(
  summary: IncomeCategorySummary[],
  category: IncomeCategory,
): IncomeCategorySummary | null {
  return summary.find((s) => s.category === category) ?? null
}

export default function IncomeTypeCards({ summary }: IncomeTypeCardsProps) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {ORDER.map((category) => {
        const item = findByCategory(summary, category)
        return (
          <CategoryCard
            key={category}
            category={category}
            current={item?.current_month_total_cny ?? 0}
            growthRate={item?.growth_rate ?? null}
          />
        )
      })}
    </div>
  )
}

function CategoryCard({
  category,
  current,
  growthRate,
}: {
  category: IncomeCategory
  current: number
  growthRate: number | null
}) {
  return (
    <div className="rounded-comfortable border border-black/5 bg-brand-white p-6">
      <div className="text-caption text-fg-tertiary">{category}</div>
      <div className="mt-3 num text-tile-heading text-fg-primary">
        {formatCurrency(current, 'CNY')}
      </div>
      <GrowthRate rate={growthRate} />
    </div>
  )
}

function GrowthRate({ rate }: { rate: number | null }) {
  if (rate === null) {
    return (
      <p className="mt-2 inline-flex items-center gap-1 text-caption text-fg-tertiary">
        <Minus size={14} strokeWidth={1.5} />
        <span>上月无记录</span>
      </p>
    )
  }
  const isUp = rate > 0
  const isDown = rate < 0
  const Icon = isUp ? ArrowUp : isDown ? ArrowDown : Minus
  return (
    <p
      className={clsx(
        'mt-2 inline-flex items-center gap-1 text-caption',
        isUp && 'text-finance-up',
        isDown && 'text-finance-down',
        !isUp && !isDown && 'text-fg-tertiary',
      )}
    >
      <Icon size={14} strokeWidth={2} />
      <span className="num">{formatPercent(Math.abs(rate), false)}</span>
      <span className="text-fg-tertiary">同比上月</span>
    </p>
  )
}
