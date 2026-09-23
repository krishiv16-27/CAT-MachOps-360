import { create } from 'zustand'
import type { Alert } from '../types'

interface AlertState {
  alerts: Alert[]
  unreadCount: number
  addAlert: (alert: Alert) => void
  markAlertAcknowledged: (alertId: string) => void
  setAlerts: (alerts: Alert[]) => void
  clearUnread: () => void
}

export const useAlertStore = create<AlertState>((set) => ({
  alerts: [],
  unreadCount: 0,
  addAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts].slice(0, 100), // keep last 100
      unreadCount: state.unreadCount + 1,
    })),
  markAlertAcknowledged: (alertId) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.alert_id === alertId ? { ...a, acknowledged: true } : a
      ),
    })),
  setAlerts: (alerts) => set({ alerts }),
  clearUnread: () => set({ unreadCount: 0 }),
}))
