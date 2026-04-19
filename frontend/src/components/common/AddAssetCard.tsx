import { Plus } from 'lucide-react'

interface AddAssetCardProps {
  onClick: () => void
}

export default function AddAssetCard({ onClick }: AddAssetCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex min-h-[168px] flex-col items-center justify-center rounded-large border-2 border-dashed border-black/15 bg-brand-light-gray/40 p-5 text-fg-tertiary transition-colors hover:border-apple-blue hover:bg-apple-blue/5 hover:text-apple-blue"
    >
      <Plus size={32} strokeWidth={1.5} />
      <span className="mt-2 text-body">添加资产</span>
    </button>
  )
}
