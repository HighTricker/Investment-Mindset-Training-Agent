import { useEffect, useState } from 'react'
import clsx from 'clsx'
import { useUserSettings } from '../../hooks/useUserSettings'
import { sendReport } from '../../services/api/report'
import { toReadableMessage } from '../../utils/errors'

type Feedback = { type: 'success' | 'error'; msg: string } | null

export default function EmailSettings() {
  const { settings, isFetched, fetchSettings, updateSettings } =
    useUserSettings()

  const [draft, setDraft] = useState('')
  const [saving, setSaving] = useState(false)
  const [sending, setSending] = useState(false)
  const [feedback, setFeedback] = useState<Feedback>(null)

  useEffect(() => {
    if (!isFetched) void fetchSettings()
  }, [isFetched, fetchSettings])

  useEffect(() => {
    if (settings?.email) setDraft(settings.email)
  }, [settings?.email])

  const savedEmail = settings?.email ?? ''
  const trimmed = draft.trim()
  const canSave = trimmed.length > 0 && trimmed !== savedEmail && !saving
  const canSend = savedEmail.length > 0 && !sending && !saving

  const handleSave = async () => {
    if (!canSave) return
    setSaving(true)
    setFeedback(null)
    try {
      await updateSettings({ email: trimmed })
      setFeedback({ type: 'success', msg: '邮箱已保存' })
    } catch (e) {
      setFeedback({ type: 'error', msg: toReadableMessage(e) })
    } finally {
      setSaving(false)
    }
  }

  const handleSend = async () => {
    if (!canSend) return
    setSending(true)
    setFeedback(null)
    try {
      const res = await sendReport()
      setFeedback({ type: 'success', msg: `报告已发送至 ${res.recipient}` })
    } catch (e) {
      setFeedback({ type: 'error', msg: toReadableMessage(e) })
    } finally {
      setSending(false)
    }
  }

  return (
    <section>
      <h2 className="text-tile-heading text-fg-primary">邮箱设置</h2>
      <p className="mt-1 text-caption text-fg-tertiary">
        报告会发送到此邮箱。SMTP 配置在 <code>backend/.env</code>（生产部署后由
        定时任务自动每月发送）
      </p>
      <div className="mt-4 flex flex-wrap items-start gap-3">
        <input
          type="email"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="your_email@163.com"
          className="min-w-[280px] flex-1 rounded-standard border border-black/15 bg-brand-white px-3 py-2 text-body text-fg-primary outline-none focus:border-apple-blue"
        />
        <button
          type="button"
          onClick={handleSave}
          disabled={!canSave}
          className="rounded-standard border border-black/15 bg-brand-white px-5 py-2 text-body text-fg-secondary transition-colors hover:bg-brand-light-gray disabled:cursor-not-allowed disabled:opacity-60"
        >
          {saving ? '保存中…' : '保存邮箱'}
        </button>
        <button
          type="button"
          onClick={handleSend}
          disabled={!canSend}
          className="rounded-standard bg-apple-blue px-5 py-2 text-body text-brand-white transition-colors hover:bg-apple-link-light disabled:cursor-not-allowed disabled:opacity-60"
        >
          {sending ? '发送中…' : '立即发送报告'}
        </button>
      </div>
      {feedback && (
        <p
          className={clsx(
            'mt-3 text-caption',
            feedback.type === 'success'
              ? 'text-finance-up'
              : 'text-finance-down',
          )}
        >
          {feedback.type === 'success' ? '✓' : '⚠️'} {feedback.msg}
        </p>
      )}
    </section>
  )
}
