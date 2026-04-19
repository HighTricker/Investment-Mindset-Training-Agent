import { useEffect } from 'react'
import AssetCard from '../components/common/AssetCard'
import SummaryCard from '../components/common/SummaryCard'
import { useAssets } from '../hooks/useAssets'
import { formatCurrency, formatPercent } from '../utils/formatters'

function deriveTrend(
  value: number | null | undefined,
): 'up' | 'down' | 'neutral' {
  if (value == null || value === 0) return 'neutral'
  return value > 0 ? 'up' : 'down'
}

export default function P1_Home() {
  const { assets, summary, loading, error, fetchAssets } = useAssets()

  useEffect(() => {
    void fetchAssets({ includeClosed: false })
  }, [fetchAssets])

  const totalReturnTrend = deriveTrend(summary?.total_return_rate)
  const profitLossTrend = deriveTrend(summary?.total_profit_loss_cny)

  return (
    <div className="space-y-10 px-8 py-10">
      <header>
        <h1 className="text-section-heading text-fg-primary">P1 首页</h1>
        <p className="mt-2 text-body text-fg-secondary">资产组合概览</p>
      </header>

      <section>
        <div className="grid grid-cols-4 gap-4">
          <SummaryCard
            label="总初始投入(CNY)"
            value={formatCurrency(
              summary?.total_initial_investment_cny ?? 0,
              'CNY',
            )}
          />
          <SummaryCard
            label="当前价值(CNY)"
            value={formatCurrency(
              summary?.total_current_value_cny ?? 0,
              'CNY',
            )}
          />
          <SummaryCard
            label="总收益率"
            value={formatPercent(summary?.total_return_rate ?? 0, true)}
            trend={totalReturnTrend}
          />
          <SummaryCard
            label="盈亏(CNY)"
            value={formatCurrency(
              summary?.total_profit_loss_cny ?? 0,
              'CNY',
            )}
            trend={profitLossTrend}
          />
        </div>
      </section>

      <section>
        <h2 className="text-tile-heading text-fg-primary">持仓资产</h2>
        {loading && (
          <p className="mt-4 text-body text-fg-secondary">加载中…</p>
        )}
        {error && (
          <p className="mt-4 text-body text-finance-down">⚠️ {error}</p>
        )}
        {!loading && !error && assets.length === 0 && (
          <p className="mt-4 text-body text-fg-tertiary">
            暂无持仓资产（3.2d 将加"+"新增卡实现添加）
          </p>
        )}
        {assets.length > 0 && (
          <div className="mt-6 grid grid-cols-3 gap-4">
            {assets.map((asset) => (
              <AssetCard key={asset.asset_id} asset={asset} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
