import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { ChevronDown, ChevronRight, type LucideIcon } from 'lucide-react'
import clsx from 'clsx'
import { navConfig, type NavItem } from '../../config/routes'

export default function Sidebar() {
  const location = useLocation()
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
    <aside className="w-60 shrink-0 border-r border-black/10 bg-brand-light-gray">
      <div className="px-6 py-6">
        <h1 className="text-body-emphasis text-fg-primary">
          还有多久可以财富自由
        </h1>
        <p className="mt-1 text-micro text-fg-tertiary">个人投资追踪</p>
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
          depth === 0 ? 'text-body' : 'ml-7 text-caption',
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
        className="flex w-full items-center gap-2 rounded-standard px-3 py-2.5 text-body text-fg-secondary transition-colors hover:bg-brand-white/60"
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
    <span className="rounded bg-black/5 px-1.5 py-0.5 text-nano text-fg-tertiary">
      {version}
    </span>
  )
}
