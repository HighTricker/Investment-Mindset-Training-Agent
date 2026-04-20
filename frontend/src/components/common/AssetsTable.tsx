import clsx from 'clsx'
import type { AssetDetail } from '../../types/entities'
import {
  formatCurrency,
  formatNumber,
  formatPercent,
} from '../../utils/formatters'

interface AssetsTableProps {
  assets: AssetDetail[]
  onRowClick?: (asset: AssetDetail) => void
  selectedAssetId?: number | null
}

const COLUMNS: { key: string; label: string; align?: 'left' | 'right' }[] = [
  { key: 'index', label: '序号', align: 'right' },
  { key: 'symbol', label: '代码' },
  { key: 'name', label: '资产名称' },
  { key: 'category', label: '类别' },
  { key: 'initial_investment_cny', label: '初始投入(CNY)', align: 'right' },
  { key: 'quantity', label: '持仓数量', align: 'right' },
  { key: 'cost_price_original', label: '持仓成本(原币)', align: 'right' },
  { key: 'current_price_original', label: '现价(原币)', align: 'right' },
  { key: 'position_ratio', label: '仓位占比', align: 'right' },
  { key: 'exchange_rate_to_cny', label: '当前汇率', align: 'right' },
  { key: 'current_value_cny', label: '当前价值(CNY)', align: 'right' },
  { key: 'cumulative_return_rate', label: '累计收益率', align: 'right' },
  { key: 'monthly_return_rate', label: '本月收益率', align: 'right' },
]

function rateClass(value: number | null): string {
  if (value == null || value === 0) return ''
  return value > 0 ? 'text-finance-up' : 'text-finance-down'
}

export default function AssetsTable({
  assets,
  onRowClick,
  selectedAssetId,
}: AssetsTableProps) {
  if (assets.length === 0) {
    return (
      <p className="text-body text-fg-tertiary">暂无持仓数据</p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-comfortable border border-black/10">
      <table className="w-full border-collapse text-caption">
        <thead className="bg-brand-light-gray">
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                className={clsx(
                  'whitespace-nowrap px-3 py-3 font-semibold text-fg-secondary',
                  col.align === 'right' ? 'text-right' : 'text-left',
                )}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {assets.map((asset, idx) => (
            <tr
              key={asset.asset_id}
              onClick={onRowClick ? () => onRowClick(asset) : undefined}
              className={clsx(
                'border-t border-black/5 transition-colors',
                onRowClick && 'cursor-pointer',
                !asset.is_active && 'italic text-fg-tertiary',
                selectedAssetId === asset.asset_id
                  ? 'bg-blue-50 hover:bg-blue-50'
                  : 'hover:bg-brand-light-gray/50',
              )}
            >
              <td className="num px-3 py-3 text-right">{idx + 1}</td>
              <td className="num whitespace-nowrap px-3 py-3">
                {asset.symbol}
              </td>
              <td className="px-3 py-3">{asset.name}</td>
              <td className="whitespace-nowrap px-3 py-3">{asset.category}</td>
              <td className="num whitespace-nowrap px-3 py-3 text-right">
                {formatCurrency(asset.initial_investment_cny, 'CNY')}
              </td>
              <td className="num px-3 py-3 text-right">
                {formatNumber(asset.quantity, 4)}
              </td>
              <td className="num whitespace-nowrap px-3 py-3 text-right">
                {formatCurrency(asset.cost_price_original, asset.currency)}
              </td>
              <td className="num whitespace-nowrap px-3 py-3 text-right">
                {formatCurrency(asset.current_price_original, asset.currency)}
              </td>
              <td className="num px-3 py-3 text-right">
                {formatPercent(asset.position_ratio)}
              </td>
              <td className="num px-3 py-3 text-right">
                {formatNumber(asset.exchange_rate_to_cny, 4)}
              </td>
              <td className="num whitespace-nowrap px-3 py-3 text-right">
                {formatCurrency(asset.current_value_cny, 'CNY')}
              </td>
              <td
                className={clsx(
                  'num px-3 py-3 text-right',
                  rateClass(asset.cumulative_return_rate),
                )}
              >
                {formatPercent(asset.cumulative_return_rate, true)}
              </td>
              <td
                className={clsx(
                  'num px-3 py-3 text-right',
                  rateClass(asset.monthly_return_rate),
                )}
              >
                {formatPercent(asset.monthly_return_rate, true)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
