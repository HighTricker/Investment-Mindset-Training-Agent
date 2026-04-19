import { useEffect, useState } from 'react'
import clsx from 'clsx'
import { useUserSettings } from '../../hooks/useUserSettings'
import { useWealthFreedom } from '../../hooks/useWealthFreedom'
import { formatPercent } from '../../utils/formatters'
import type { CashOrIncomeCurrency } from '../../types/enums'

type TargetKey = 'monthly_living' | 'passive_income' | 'cash_savings'

interface TargetDef {
  key: TargetKey
  label: string
  amountField: 'target_monthly_living' | 'target_passive_income' | 'target_cash_savings'
  currencyField:
    | 'target_living_currency'
    | 'target_passive_currency'
    | 'target_cash_currency'
}

const TARGETS: TargetDef[] = [
  {
    key: 'monthly_living',
    label: '目标生活水平（月）',
    amountField: 'target_monthly_living',
    currencyField: 'target_living_currency',
  },
  {
    key: 'passive_income',
    label: '目标被动收入（月）',
    amountField: 'target_passive_income',
    currencyField: 'target_passive_currency',
  },
  {
    key: 'cash_savings',
    label: '目标现金储蓄',
    amountField: 'target_cash_savings',
    currencyField: 'target_cash_currency',
  },
]

export default function TargetCards() {
  const { settings, fetchSettings } = useUserSettings()
  const { metrics } = useWealthFreedom()

  useEffect(() => {
    void fetchSettings()
  }, [fetchSettings])

  return (
    <div className="grid grid-cols-4 gap-4">
      {TARGETS.map((def) => (
        <TargetInputCard
          key={def.key}
          def={def}
          amount={settings?.[def.amountField] ?? 0}
          currency={settings?.[def.currencyField] ?? 'CNY'}
        />
      ))}
      <AchievementCard rate={metrics?.achievement_rate ?? null} />
    </div>
  )
}

function TargetInputCard({
  def,
  amount,
  currency,
}: {
  def: TargetDef
  amount: number
  currency: CashOrIncomeCurrency
}) {
  const { updateSettings } = useUserSettings()
  const { invalidate: invalidateMetrics } = useWealthFreedom()
  const [draft, setDraft] = useState<string>(String(amount))
  const [localError, setLocalError] = useState<string | null>(null)

  useEffect(() => {
    setDraft(String(amount))
  }, [amount])

  const commitAmount = async () => {
    const n = Number(draft)
    if (!Number.isFinite(n) || n < 0) {
      setLocalError('金额必须 ≥ 0')
      setDraft(String(amount))
      return
    }
    setLocalError(null)
    if (n === amount) return
    try {
      await updateSettings({ [def.amountField]: n })
      invalidateMetrics()
    } catch {
      setDraft(String(amount))
      setLocalError('保存失败')
    }
  }

  const commitCurrency = async (value: CashOrIncomeCurrency) => {
    if (value === currency) return
    try {
      await updateSettings({ [def.currencyField]: value })
      invalidateMetrics()
    } catch {
      setLocalError('保存失败')
    }
  }

  return (
    <div className="rounded-comfortable border border-black/5 bg-brand-white p-6">
      <div className="text-caption text-fg-tertiary">{def.label}</div>
      <div className="mt-3 flex items-center gap-2">
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
        <select
          value={currency}
          onChange={(e) =>
            void commitCurrency(e.target.value as CashOrIncomeCurrency)
          }
          className="rounded-standard border border-black/15 bg-brand-white px-2 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
        >
          <option value="CNY">CNY</option>
          <option value="USD">USD</option>
        </select>
      </div>
      {localError && (
        <p className="mt-2 text-caption text-finance-down">{localError}</p>
      )}
    </div>
  )
}

function AchievementCard({ rate }: { rate: number | null }) {
  const trend = rate == null || rate === 0 ? 'neutral' : rate >= 1 ? 'up' : 'down'
  return (
    <div
      className={clsx(
        'rounded-comfortable border p-6',
        trend === 'up' && 'bg-finance-up/10 border-finance-up/20',
        trend === 'down' && 'bg-brand-white border-black/5',
        trend === 'neutral' && 'bg-brand-white border-black/5',
      )}
    >
      <div className="text-caption text-fg-tertiary">达成目标率</div>
      <div
        className={clsx(
          'mt-3 text-tile-heading num',
          trend === 'up' && 'text-finance-up',
          trend !== 'up' && 'text-fg-primary',
        )}
      >
        {formatPercent(rate, false)}
      </div>
      <p className="mt-2 text-caption text-fg-tertiary">
        当前资产 / 目标资产
      </p>
    </div>
  )
}
