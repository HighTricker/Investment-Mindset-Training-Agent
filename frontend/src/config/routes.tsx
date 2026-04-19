import { createBrowserRouter } from 'react-router-dom'
import {
  BarChart3,
  Home,
  Mail,
  MessageCircle,
  Target,
  type LucideIcon,
} from 'lucide-react'
import MainLayout from '../components/layout/MainLayout'
import P1_Home from '../pages/P1_Home'
import P2_1_WealthFreedom from '../pages/P2_1_WealthFreedom'
import P3_1_Assets from '../pages/P3_1_Assets'
import P3_2_News from '../pages/P3_2_News'
import P3_2_NewsDetail from '../pages/P3_2_NewsDetail'
import P4_AiChat from '../pages/P4_AiChat'
import P5_Report from '../pages/P5_Report'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <P1_Home /> },
      { path: 'wealth-freedom', element: <P2_1_WealthFreedom /> },
      { path: 'assets', element: <P3_1_Assets /> },
      { path: 'news', element: <P3_2_News /> },
      { path: 'news/:asset_id', element: <P3_2_NewsDetail /> },
      { path: 'ai-chat', element: <P4_AiChat /> },
      { path: 'report', element: <P5_Report /> },
    ],
  },
])

type Version = 'V2' | 'V3'

export type NavLinkItem = {
  kind: 'link'
  path: string
  label: string
  icon: LucideIcon
  version?: Version
}

export type NavGroupItem = {
  kind: 'group'
  label: string
  icon: LucideIcon
  children: {
    path: string
    label: string
    version?: Version
  }[]
}

export type NavItem = NavLinkItem | NavGroupItem

export const navConfig: NavItem[] = [
  { kind: 'link', path: '/', label: 'P1 首页', icon: Home },
  {
    kind: 'link',
    path: '/wealth-freedom',
    label: 'P2 还有多久可以财富自由',
    icon: Target,
  },
  {
    kind: 'group',
    label: 'P3 投资行为剖析',
    icon: BarChart3,
    children: [
      { path: '/assets', label: 'P3.1 投资资产及其原因' },
      { path: '/news', label: 'P3.2 相关资产新闻', version: 'V3' },
    ],
  },
  {
    kind: 'link',
    path: '/ai-chat',
    label: 'P4 AI 对话交流',
    icon: MessageCircle,
    version: 'V3',
  },
  {
    kind: 'link',
    path: '/report',
    label: 'P5 发送投资报告',
    icon: Mail,
    version: 'V2',
  },
]
