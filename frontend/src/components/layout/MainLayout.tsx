import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function MainLayout() {
  return (
    <div className="flex min-h-screen bg-brand-light-gray">
      <Sidebar />
      <main className="flex-1 bg-brand-white">
        <Outlet />
      </main>
    </div>
  )
}
