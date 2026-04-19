import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  ChevronDown,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
  type LucideIcon,
} from 'lucide-react'
import clsx from 'clsx'
import { navConfig, type NavItem } from '../../config/routes'

const COLLAPSED_STORAGE_KEY = 'sidebar-collapsed'

export default function Sidebar() {
  const location = useLocation()

  const [isCollapsed, setIsCollapsed] = useState<boolean>(
    () => localStorage.getItem(COLLAPSED_STORAGE_KEY) === '1'
  )

  useEffect(() => {
    localStorage.setItem(COLLAPSED_STORAGE_KEY, isCollapsed ? '1' : '0')
  }, [isCollapsed])

  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => {
    const next: Record<string, boolean> = {}
    for (const item of navConfig) {
      if (item.kind === 'group') {
        next[item.label] = item.children.some(
          (c) =>
            location.pathname === c.path ||
            location.pathname.startsWith(c.path + '/')
        )
      }
    }
    return next
  })

  const toggle = (label: string) =>
    setExpanded((prev) => ({ ...prev, [label]: !prev[label] }))

  return (
    <aside
      className={clsx(
        'shrink-0 overflow-hidden border-r border-black/10 bg-brand-light-gray',
        'transition-[width] duration-300 ease-out',
        isCollapsed ? 'w-[50px]' : 'w-[350px]'
      )}
    >
      {isCollapsed ? (
        <button
          type="button"
          onClick={() => setIsCollapsed(false)}
          className="flex h-14 w-full items-center justify-center text-fg-secondary transition-colors hover:bg-brand-white/60 hover:text-fg-primary"
          aria-label="展开侧边栏"
        >
          <PanelLeftOpen size={22} strokeWidth={1.75} />
        </button>
      ) : (
        <div className="w-[350px]">
          <div className="flex items-start justify-between px-6 py-6">
            <div className="min-w-0">
              <h1 className="text-[21.25px] leading-[1.24] tracking-[-0.374px] font-semibold text-fg-primary">
                还有多久可以财富自由
              </h1>
              <p className="mt-1 text-[15px] leading-[1.33] tracking-[-0.12px] text-fg-tertiary">
                个人投资追踪
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIsCollapsed(true)}
              className="shrink-0 rounded-standard p-1.5 text-fg-tertiary transition-colors hover:bg-brand-white/60 hover:text-fg-primary"
              aria-label="收起侧边栏"
            >
              <PanelLeftClose size={30} strokeWidth={1.75} />
            </button>
          </div>
          <nav className="px-2 pb-8">
            {navConfig.map((item) =>
              item.kind === 'link' ? (
                <SidebarLink
                  key={item.path}
                  to={item.path}
                  label={item.label}
                  Icon={item.icon}
                  version={item.version}
                />
              ) : (
                <SidebarGroup
                  key={item.label}
                  item={item}
                  isExpanded={!!expanded[item.label]}
                  onToggle={() => toggle(item.label)}
                />
              )
            )}
          </nav>
        </div>
      )}
    </aside>
  )
}

function SidebarLink({
  to,
  label,
  Icon,
  version,
  depth = 0,
}: {
  to: string
  label: string
  Icon?: LucideIcon
  version?: 'V2' | 'V3'
  depth?: number
}) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        clsx(
          'relative flex items-center gap-2 rounded-standard px-3 py-2.5 transition-colors mt-0.5',
          depth === 0
            ? 'text-[21.25px] leading-[1.47] tracking-[-0.374px]'
            : 'ml-7 text-[17.5px] leading-[1.29] tracking-[-0.224px]',
          isActive
            ? 'bg-brand-white font-semibold text-fg-primary before:absolute before:inset-y-2 before:left-0 before:w-[3px] before:rounded-r before:bg-apple-blue'
            : 'text-fg-secondary hover:bg-brand-white/60'
        )
      }
    >
      {Icon && <Icon size={18} strokeWidth={1.75} />}
      <span className="flex-1 truncate">{label}</span>
      {version && <VersionBadge version={version} />}
    </NavLink>
  )
}

function SidebarGroup({
  item,
  isExpanded,
  onToggle,
}: {
  item: Extract<NavItem, { kind: 'group' }>
  isExpanded: boolean
  onToggle: () => void
}) {
  const Icon = item.icon
  return (
    <div className="mt-0.5">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center gap-2 rounded-standard px-3 py-2.5 text-[21.25px] leading-[1.47] tracking-[-0.374px] text-fg-secondary transition-colors hover:bg-brand-white/60"
      >
        <Icon size={18} strokeWidth={1.75} />
        <span className="flex-1 text-left">{item.label}</span>
        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {isExpanded && (
        <div>
          {item.children.map((child) => (
            <SidebarLink
              key={child.path}
              to={child.path}
              label={child.label}
              version={child.version}
              depth={1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function VersionBadge({ version }: { version: 'V2' | 'V3' }) {
  return (
    <span className="rounded bg-black/5 px-1.5 py-0.5 text-[12.5px] leading-[1.47] tracking-[-0.08px] text-fg-tertiary">
      {version}
    </span>
  )
}
