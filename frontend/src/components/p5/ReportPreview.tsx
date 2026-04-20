import { useState } from 'react'
import { previewReport } from '../../services/api/report'
import { toReadableMessage } from '../../utils/errors'

export default function ReportPreview() {
  const [html, setHtml] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handlePreview = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await previewReport()
      setHtml(result)
    } catch (e) {
      setError(toReadableMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-tile-heading text-fg-primary">报告预览</h2>
          <p className="mt-1 text-caption text-fg-tertiary">
            以"今日"为基准日生成 HTML，上月收益率取上一自然月首末交易日 close
            差值
          </p>
        </div>
        <button
          type="button"
          onClick={handlePreview}
          disabled={loading}
          className="shrink-0 rounded-standard bg-apple-blue px-4 py-2 text-body text-brand-white transition-colors hover:bg-apple-link-light disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? '生成中…' : '生成预览'}
        </button>
      </div>
      {error && <p className="mt-3 text-body text-finance-down">⚠️ {error}</p>}
      <div className="mt-4 overflow-hidden rounded-large border border-black/10 bg-brand-white">
        {html ? (
          <iframe
            srcDoc={html}
            title="投资月报预览"
            sandbox="allow-same-origin"
            className="h-[800px] w-full border-0"
          />
        ) : (
          <div className="flex h-[400px] items-center justify-center px-8 text-center text-body text-fg-tertiary">
            点击右上角"生成预览"，基于当前 11 资产持仓生成最新月报预览
          </div>
        )}
      </div>
    </section>
  )
}
