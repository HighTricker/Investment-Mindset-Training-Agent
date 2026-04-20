import { useEffect, useState } from 'react'
import AssetsTable from '../components/common/AssetsTable'
import { useAssets } from '../hooks/useAssets'
import type { AssetDetail } from '../types/entities'

export default function P3_1_Assets() {
  const { assets, loading, error, fetchAssets } = useAssets()
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null)

  useEffect(() => {
    void fetchAssets({ includeClosed: true })
  }, [fetchAssets])

  const handleRowClick = (asset: AssetDetail) => {
    setSelectedAssetId((prev) =>
      prev === asset.asset_id ? null : asset.asset_id,
    )
  }

  return (
    <div className="space-y-10 px-8 py-10">
      <header>
        <h1 className="text-section-heading text-fg-primary">
          P3.1 投资资产及其原因
        </h1>
        <p className="mt-2 text-body text-fg-secondary">
          资产明细 · 点击行查看交易历史
        </p>
      </header>

      <section>
        <h2 className="text-tile-heading text-fg-primary">资产明细</h2>
        {loading && (
          <p className="mt-4 text-body text-fg-secondary">加载中…</p>
        )}
        {error && (
          <p className="mt-4 text-body text-finance-down">⚠️ {error}</p>
        )}
        {!loading && !error && (
          <div className="mt-6">
            <AssetsTable
              assets={assets}
              onRowClick={handleRowClick}
              selectedAssetId={selectedAssetId}
            />
          </div>
        )}
      </section>
    </div>
  )
}
