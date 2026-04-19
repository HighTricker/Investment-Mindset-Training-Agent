import CashSection from '../components/p2_1/CashSection'
import IncomeSection from '../components/p2_1/IncomeSection'
import TargetCards from '../components/p2_1/TargetCards'
import WealthCountdown from '../components/p2_1/WealthCountdown'

export default function P2_1_WealthFreedom() {
  return (
    <div className="space-y-10 px-8 py-10">
      <header>
        <h1 className="text-section-heading text-fg-primary">
          P2.1 财富自由时间表
        </h1>
        <p className="mt-2 text-body text-fg-secondary">
          目标设置 · 现金分布 · 收入管理 · 财富自由倒计时
        </p>
      </header>

      <section>
        <h2 className="text-tile-heading text-fg-primary">目标设置</h2>
        <p className="mt-1 text-caption text-fg-tertiary">
          失焦或回车自动保存，右侧达成率实时联动
        </p>
        <div className="mt-6">
          <TargetCards />
        </div>
      </section>

      <CashSection />

      <IncomeSection />

      <WealthCountdown />
    </div>
  )
}
