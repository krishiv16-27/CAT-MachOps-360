import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Truck, Users, ClipboardList, Bell,
  AlertTriangle, GraduationCap, BarChart3, Watch,
  ShieldCheck, Camera, MessageSquare, Settings, LogOut, Zap,
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { useAlertStore } from '../../store/alertStore'
import { useWebSocket } from '../../hooks/useWebSocket'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../../services/api'
import { useKpiStore } from '../../store/kpiStore'
import { useEffect } from 'react'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Command Center', icon: LayoutDashboard, roles: ['engineer', 'supervisor', 'admin', 'safety_officer', 'maintenance_engineer'] },
  { path: '/operator', label: 'My Dashboard', icon: LayoutDashboard, roles: ['operator'] },
  { path: '/watch', label: 'Watch', icon: Watch, roles: ['operator', 'engineer', 'admin'] },
  { path: '/machines', label: 'Machines', icon: Truck, roles: ['engineer', 'supervisor', 'admin', 'maintenance_engineer'] },
  { path: '/operators', label: 'Operators', icon: Users, roles: ['engineer', 'supervisor', 'admin', 'safety_officer'] },
  { path: '/tasks', label: 'Tasks', icon: ClipboardList, roles: ['engineer', 'supervisor', 'admin', 'operator'] },
  { path: '/alerts', label: 'Alerts', icon: Bell, roles: ['engineer', 'supervisor', 'admin', 'safety_officer', 'operator'] },
  { path: '/incidents', label: 'Incidents', icon: AlertTriangle, roles: ['engineer', 'supervisor', 'admin', 'safety_officer'] },
  { path: '/prestart', label: 'Pre-Start', icon: ShieldCheck, roles: ['operator', 'engineer', 'supervisor', 'admin'] },
  { path: '/dashcam', label: 'Dashcam', icon: Camera, roles: ['engineer', 'supervisor', 'admin', 'safety_officer'] },
  { path: '/training', label: 'Training', icon: GraduationCap, roles: ['operator', 'engineer', 'supervisor', 'admin', 'safety_officer'] },
  { path: '/analytics', label: 'Analytics', icon: BarChart3, roles: ['engineer', 'supervisor', 'admin'] },
  { path: '/copilot', label: 'AI Copilot', icon: MessageSquare, roles: ['engineer', 'admin'] },
  { path: '/settings', label: 'Settings', icon: Settings, roles: ['engineer', 'admin', 'supervisor'] },
]

export default function AppLayout() {
  const { user, clearAuth } = useAuthStore()
  const { unreadCount } = useAlertStore()
  const { setKpi } = useKpiStore()
  const navigate = useNavigate()
  useWebSocket()

  const { data: kpiData } = useQuery({
    queryKey: ['site-overview'],
    queryFn: () => analyticsApi.siteOverview(),
    refetchInterval: 30_000,
  })

  useEffect(() => {
    if (kpiData) setKpi(kpiData)
  }, [kpiData, setKpi])

  const visibleNav = NAV_ITEMS.filter(
    (item) => user && item.roles.includes(user.role)
  )

  function handleLogout() {
    clearAuth()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-slate-900 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-800 border-r border-slate-700 flex flex-col flex-shrink-0">
        {/* Logo */}
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-amber-500 rounded-lg flex items-center justify-center">
              <Zap size={18} className="text-slate-900" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-100">MachOps 360</div>
              <div className="text-xs text-amber-400">CAT Intelligence</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-2">
          {visibleNav.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                  isActive
                    ? 'bg-amber-500/10 text-amber-400 border-r-2 border-amber-400'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-700/50'
                }`
              }
              aria-label={`Navigate to ${item.label}`}
            >
              <item.icon size={16} />
              <span>{item.label}</span>
              {item.path === '/alerts' && unreadCount > 0 && (
                <span className="ml-auto bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="p-4 border-t border-slate-700">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-7 h-7 bg-amber-500/20 rounded-full flex items-center justify-center text-amber-400 text-xs font-bold">
              {user?.name?.[0] ?? '?'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium text-slate-200 truncate">{user?.name}</div>
              <div className="text-xs text-slate-500 capitalize">{user?.role?.replace('_', ' ')}</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-xs text-slate-500 hover:text-red-400 transition-colors"
            aria-label="Logout"
          >
            <LogOut size={12} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
