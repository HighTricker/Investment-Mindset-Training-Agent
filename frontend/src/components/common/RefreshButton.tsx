import clsx from 'clsx'
import { RefreshCw } from 'lucide-react'
import { useAssets } from '../../hooks/useAssets'

export default function RefreshButton() {
  const { refreshing, refreshMarket } = useAssets()

  return (
    <button
      type="button"
      onClick={() => void refreshMarket()}
      disabled={refreshing}
      className={clsx(
        'inline-flex items-center gap-2 rounded-comfortable border border-black/10 bg-brand-white px-4 py-2 text-body transition-colors',
        refreshing
          ? 'cursor-not-allowed opacity-60'
          : 'hover:border-black/20 hover:bg-brand-light-gray',
      )}
    >
      <RefreshCw
        size={16}
        strokeWidth={2}
        className={refreshing ? 'animate-spin' : ''}
      />
      <span>{refreshing ? '刷新中…' : '刷新市场数据'}</span>
    </button>
  )
}
