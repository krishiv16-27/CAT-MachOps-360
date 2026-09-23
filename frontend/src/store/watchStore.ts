import { create } from 'zustand'
import type { Alert } from '../types'

export type WatchScreen =
  | 'home' | 'current-task' | 'task-progress' | 'next-task'
  | 'safety-status' | 'active-alert' | 'break-recommendation'
  | 'machine-status' | 'emergency' | 'shift-summary'
  | 'todays-tasks' | 'safety-events' | 'qr-code' | 'training'

const SCREENS: WatchScreen[] = [
  'home', 'current-task', 'task-progress', 'next-task',
  'safety-status', 'active-alert', 'break-recommendation',
  'machine-status', 'emergency', 'shift-summary',
  'todays-tasks', 'safety-events', 'qr-code', 'training',
]

interface WatchState {
  currentScreen: WatchScreen
  screens: WatchScreen[]
  activeAlert: Alert | null
  isVibrating: boolean
  setScreen: (screen: WatchScreen) => void
  nextScreen: () => void
  prevScreen: () => void
  setActiveAlert: (alert: Alert | null) => void
  clearAlert: () => void
  triggerVibration: () => void
}

export const useWatchStore = create<WatchState>((set, get) => ({
  currentScreen: 'home',
  screens: SCREENS,
  activeAlert: null,
  isVibrating: false,

  setScreen: (screen) => set({ currentScreen: screen }),

  nextScreen: () => {
    const { currentScreen, screens } = get()
    const idx = screens.indexOf(currentScreen)
    const next = screens[(idx + 1) % screens.length]
    set({ currentScreen: next })
  },

  prevScreen: () => {
    const { currentScreen, screens } = get()
    const idx = screens.indexOf(currentScreen)
    const prev = screens[(idx - 1 + screens.length) % screens.length]
    set({ currentScreen: prev })
  },

  setActiveAlert: (alert) => {
    if (alert) {
      set({ activeAlert: alert, currentScreen: 'active-alert' })
      // Trigger haptic vibration
      if (typeof navigator !== 'undefined' && navigator.vibrate) {
        if (alert.severity === 'CRITICAL') {
          navigator.vibrate([500, 100, 500, 100, 500])
        } else if (alert.severity === 'HIGH') {
          navigator.vibrate([300, 100, 300])
        } else {
          navigator.vibrate([200])
        }
      }
      set({ isVibrating: true })
      setTimeout(() => set({ isVibrating: false }), 1500)
    } else {
      set({ activeAlert: null })
    }
  },

  clearAlert: () => {
    set({ activeAlert: null, currentScreen: 'home' })
  },

  triggerVibration: () => {
    set({ isVibrating: true })
    setTimeout(() => set({ isVibrating: false }), 1500)
  },
}))
