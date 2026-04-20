import EmailSettings from '../components/p5/EmailSettings'
import ReportPreview from '../components/p5/ReportPreview'

export default function P5_Report() {
  return (
    <div className="space-y-10 px-8 py-10">
      <header>
        <h1 className="text-section-heading text-fg-primary">
          P5 发送投资报告
        </h1>
        <p className="mt-2 text-body text-fg-secondary">
          配置收件邮箱 · 预览月报样式 · 手动或定时发送
        </p>
      </header>

      <EmailSettings />
      <ReportPreview />

      <section className="rounded-large border border-black/5 bg-brand-light-gray p-6">
        <h2 className="text-tile-heading text-fg-primary">样式与定时自定义</h2>
        <div className="mt-3 space-y-2 text-body text-fg-secondary">
          <p>
            <strong>报告视觉样式</strong>：由{' '}
            <code className="rounded-standard bg-brand-white px-1.5 py-0.5 text-caption">
              config/report_style.json
            </code>{' '}
            配置。修改文件后点击上方"生成预览"立即查看效果，无需重启后端。
            可调：颜色 token / 字号 / 圆角 / 最大宽度 / 品牌名称。
          </p>
          <p>
            <strong>定时发送</strong>：由{' '}
            <code className="rounded-standard bg-brand-white px-1.5 py-0.5 text-caption">
              backend/.env
            </code>{' '}
            的 <code>REPORT_SCHEDULE_CRON</code> 和{' '}
            <code>REPORT_SCHEDULE_ENABLED</code> 控制。生产服务器设{' '}
            <code>true</code> 启用；本地默认关闭避免意外发送。
          </p>
          <p>
            <strong>SMTP 凭证</strong>：在{' '}
            <code className="rounded-standard bg-brand-white px-1.5 py-0.5 text-caption">
              backend/.env
            </code>{' '}
            设置 <code>SMTP_HOST / PORT / USER / PASSWORD</code>。
            163 邮箱需先在邮箱网页"设置→POP3/SMTP/IMAP"中开启服务并生成授权码
            （不是登录密码）。
          </p>
        </div>
      </section>
    </div>
  )
}
