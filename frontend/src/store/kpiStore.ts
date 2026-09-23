import { create } from 'zustand'
import type { SiteKPI } from '../types'

interface KpiState {
  kpi: SiteKPI | null
  setKpi: (kpi: SiteKPI) => void
}

export const useKpiStore = create<KpiState>((set) => ({
  kpi: null,
  setKpi: (kpi) => set({ kpi }),
}))
