import { Link } from 'react-router-dom'

interface ComingSoonPageProps {
  title: string
  version: 'V2' | 'V3'
  description?: string
}

export default function ComingSoonPage({
  title,
  version,
  description,
}: ComingSoonPageProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <div className="mb-6 inline-flex items-center gap-2 rounded-pill bg-brand-light-gray px-4 py-1.5 text-caption">
        <span className="h-1.5 w-1.5 rounded-full bg-apple-blue" />
        <span className="font-semibold text-fg-primary">{version}</span>
        <span className="text-fg-tertiary">计划启用</span>
      </div>
      <h1 className="text-section-heading text-fg-primary">{title}</h1>
      {description && (
        <p className="mt-4 max-w-lg text-body text-fg-secondary">{description}</p>
      )}
      <Link
        to="/"
        className="mt-10 text-link text-apple-blue hover:underline"
      >
        ← 返回首页
      </Link>
    </div>
  )
}
