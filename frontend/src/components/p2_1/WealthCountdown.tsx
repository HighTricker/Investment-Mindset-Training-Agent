import { useEffect } from 'react'
import clsx from 'clsx'
import { useWealthFreedom } from '../../hooks/useWealthFreedom'
import { formatCurrency, formatPercent } from '../../utils/formatters'
import type { WealthFreedomMetrics } from '../../types/entities'

function formatChineseDate(date: string | null): string {
  if (!date) return '—'
  const [y, m, d] = date.split('-')
  if (!y || !m || !d) return date
  return `${y} 年 ${Number(m)} 月 ${Number(d)} 日`
}

function deriveNoPredictionMessage(m: WealthFreedomMetrics): string {
  if (m.current_total_investment_cny === 0) {
    return '请先在首页添加资产，才能进行财富自由预测'
  }
  if (
    m.current_annualized_return_rate !== null &&
    m.current_annualized_return_rate <= 0
  ) {
    return '当前亏损，无法预测财富自由日期'
  }
  if (m.current_annualized_return_rate === null) {
    return '数据不足或持仓周期过短，暂无预测'
  }
  return '暂无预测'
}

export default function WealthCountdown() {
  const { metrics, loading, error, isFetched, fetchMetrics } =
    useWealthFreedom()

  useEffect(() => {
    if (!isFetched) {
      void fetchMetrics()
    }
  }, [isFetched, fetchMetrics])

  if (loading && !metrics) {
    return (
      <section>
        <h2 className="text-tile-heading text-fg-primary">财富自由倒计时</h2>
        <p className="mt-4 text-body text-fg-secondary">加载中…</p>
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <h2 className="text-tile-heading text-fg-primary">财富自由倒计时</h2>
        <p className="mt-4 text-body text-finance-down">⚠️ {error}</p>
      </section>
    )
  }

  if (!metrics) return null

  const gap = metrics.asset_gap_cny
  const gapColor =
    gap > 0 ? 'text-finance-down' : 'text-finance-up'
  const noPredictionMsg = deriveNoPredictionMessage(metrics)

  return (
    <section>
      <h2 className="text-tile-heading text-fg-primary">财富自由倒计时</h2>
      <p className="mt-1 text-caption text-fg-tertiary">
        基于当前资产、现金、收入实时联动；修改目标/现金/收入后自动刷新
      </p>

      {/* 资产差距 3 卡 */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <MetricCard
          label="目标总资产(CNY)"
          value={formatCurrency(metrics.target_total_assets_cny, 'CNY')}
        />
        <MetricCard
          label="当前总资产(CNY)"
          value={formatCurrency(metrics.current_total_assets_cny, 'CNY')}
          hint={`现金 ${formatCurrency(metrics.current_total_cash_cny, 'CNY')} + 投资 ${formatCurrency(metrics.current_total_investment_cny, 'CNY')}`}
        />
        <MetricCard
          label="资产差距(CNY)"
          value={formatCurrency(gap, 'CNY')}
          valueClass={gapColor}
        />
      </div>

      {/* 时薪 + 预计日期 */}
      {metrics.has_prediction ? (
        <div className="mt-6 grid grid-cols-2 gap-4">
          <div className="rounded-comfortable border border-black/5 bg-brand-white p-6">
            <div className="text-caption text-fg-tertiary">时薪对比（CNY）</div>
            <div className="mt-3 flex items-baseline gap-4">
              <div>
                <div className="text-caption text-fg-tertiary">当前</div>
                <div className="num text-tile-heading text-fg-primary">
                  {formatCurrency(metrics.current_hourly_income_cny, 'CNY')}
                </div>
              </div>
              <div className="text-fg-tertiary">/</div>
              <div>
                <div className="text-caption text-fg-tertiary">目标</div>
                <div className="num text-tile-heading text-fg-secondary">
                  {formatCurrency(metrics.target_hourly_income_cny, 'CNY')}
                </div>
              </div>
            </div>
          </div>
          <div className="rounded-comfortable border border-finance-up/20 bg-finance-up/10 p-6">
            <div className="text-caption text-fg-tertiary">预计达成日期</div>
            <div className="mt-3 text-tile-heading text-finance-up">
              {formatChineseDate(metrics.predicted_freedom_date)}
            </div>
            <p className="mt-1 text-caption text-fg-secondary">
              还需 {metrics.years_months_remaining}
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-6 rounded-comfortable border border-dashed border-black/15 bg-brand-light-gray/40 p-8 text-center">
          <p className="text-body text-fg-secondary">{noPredictionMsg}</p>
        </div>
      )}

      {/* 分析文案 */}
      {metrics.has_prediction && metrics.analysis_text && (
        <div className="mt-6 rounded-comfortable border border-black/5 bg-brand-white p-6">
          <div className="text-caption text-fg-tertiary">收益率分析</div>
          <p className="mt-3 text-body text-fg-primary">
            {metrics.analysis_text.line1}
          </p>
          <p className="mt-2 text-body text-fg-primary">
            {metrics.analysis_text.line2}
          </p>
          {metrics.current_annualized_return_rate !== null && (
            <p className="mt-3 text-caption text-fg-tertiary">
              当前年化收益率{' '}
              <span className="num text-fg-secondary">
                {formatPercent(metrics.current_annualized_return_rate, true)}
              </span>
            </p>
          )}
        </div>
      )}
    </section>
  )
}

function MetricCard({
  label,
  value,
  hint,
  valueClass = 'text-fg-primary',
}: {
  label: string
  value: string
  hint?: string
  valueClass?: string
}) {
  return (
    <div className="rounded-comfortable border border-black/5 bg-brand-white p-6">
      <div className="text-caption text-fg-tertiary">{label}</div>
      <div className={clsx('mt-3 text-tile-heading num', valueClass)}>
        {value}
      </div>
      {hint && <p className="mt-2 text-caption text-fg-tertiary">{hint}</p>}
    </div>
  )
}
