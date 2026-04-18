import { useEffect, useState } from 'react'
import { api } from './services/api'

interface HealthResponse {
  status: string
  timestamp: string
}

type HealthState =
  | { kind: 'loading' }
  | { kind: 'ok'; data: HealthResponse }
  | { kind: 'error'; message: string }

function App() {
  const [state, setState] = useState<HealthState>({ kind: 'loading' })

  useEffect(() => {
    api
      .get<HealthResponse>('/health')
      .then((res) => setState({ kind: 'ok', data: res.data }))
      .catch((err: Error) => setState({ kind: 'error', message: err.message }))
  }, [])

  return (
    <>
      {/* ====== Hero：黑底 + displayHero + Inter opsz 放大态 ====== */}
      <section className="bg-brand-black text-brand-white px-8 py-24 md:px-16 md:py-32">
        <h1 className="text-display-hero">还有多久可以财富自由</h1>
        <p className="mt-6 text-sub-heading opacity-80">
          个人投资组合追踪 Agent · 阶段 1 地基已搭建
        </p>
      </section>

      {/* ====== 字号层级视觉测试 ====== */}
      <section className="bg-brand-light-gray px-8 py-16 md:px-16">
        <h2 className="text-section-heading">字号层级（Inter 光学尺寸自动切换）</h2>
        <div className="mt-10 space-y-4">
          <p className="text-display-hero">Display Hero · 56px</p>
          <p className="text-section-heading">Section Heading · 40px</p>
          <p className="text-tile-heading">Tile Heading · 28px</p>
          <p className="text-card-title">Card Title · 21px · 700</p>
          <p className="text-body">
            Body · 17px · 负字距 -0.374px。Inter 在小字号会自动切换到更紧凑的
            opsz 字形，与 SF Pro Text 行为一致。
          </p>
          <p className="text-caption text-fg-secondary">Caption · 14px · 辅助信息</p>
          <p className="text-micro text-fg-tertiary">Micro · 12px · 细节标注</p>
        </div>
      </section>

      {/* ====== 涨跌色测试 + Apple Blue ====== */}
      <section className="bg-brand-white px-8 py-16 md:px-16">
        <h2 className="text-section-heading">颜色系统（绿涨红跌 + 单一彩色）</h2>
        <div className="mt-10 flex flex-wrap gap-12">
          <div>
            <div className="text-caption text-fg-tertiary">持仓收益率</div>
            <div className="num text-card-title text-finance-up mt-2">+12.34%</div>
          </div>
          <div>
            <div className="text-caption text-fg-tertiary">当月回撤</div>
            <div className="num text-card-title text-finance-down mt-2">-5.67%</div>
          </div>
          <div>
            <div className="text-caption text-fg-tertiary">Apple Blue（交互色）</div>
            <div className="text-card-title text-apple-blue mt-2">#0071e3</div>
          </div>
        </div>
      </section>

      {/* ====== 圆角 + 阴影系统 ====== */}
      <section className="bg-brand-light-gray px-8 py-16 md:px-16">
        <h2 className="text-section-heading">圆角 &amp; 阴影</h2>
        <div className="mt-10 flex flex-wrap gap-6">
          <div className="bg-brand-white px-6 py-4 rounded-standard">
            <div className="text-caption text-fg-secondary">rounded-standard</div>
            <div className="num text-body-emphasis">8px</div>
          </div>
          <div className="bg-brand-white px-6 py-4 rounded-large shadow-card">
            <div className="text-caption text-fg-secondary">rounded-large + shadow-card</div>
            <div className="num text-body-emphasis">12px</div>
          </div>
          <button className="text-button px-6 bg-apple-blue text-brand-white rounded-pill">
            Pill CTA（980px）
          </button>
        </div>
      </section>

      {/* ====== 后端联通状态 ====== */}
      <section className="bg-brand-white px-8 py-16 md:px-16">
        <h2 className="text-section-heading">后端联通状态 · /api/health</h2>
        <div className="mt-10">
          {state.kind === 'loading' && (
            <p className="text-body text-fg-secondary">⋯ 连接中…</p>
          )}
          {state.kind === 'ok' && (
            <>
              <p className="text-body">
                <span className="text-finance-up text-body-emphasis">✓ 健康</span>
                <span className="text-fg-secondary"> — status: </span>
                <span className="text-body-emphasis">{state.data.status}</span>
              </p>
              <p className="text-caption text-fg-secondary num mt-2">
                服务器 UTC 时间戳: {state.data.timestamp}
              </p>
            </>
          )}
          {state.kind === 'error' && (
            <p className="text-body text-finance-down">
              ✗ 连接失败：{state.message}
            </p>
          )}
        </div>
      </section>
    </>
  )
}

export default App
