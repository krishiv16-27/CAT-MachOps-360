/**
 * WebSocket hook — connects to the backend real-time stream.
 * Incoming events update Zustand stores.
 * Components subscribe to stores, not directly to this hook.
 */
import { useEffect, useRef, useCallback } from 'react'
import { useAuthStore } from '../store/authStore'
import { useAlertStore } from '../store/alertStore'
import { useKpiStore } from '../store/kpiStore'
import { useWatchStore } from '../store/watchStore'
import type { Alert, SiteKPI } from '../types'

const WS_URL = `ws://${window.location.host}/ws`

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const token = useAuthStore((s) => s.token)
  const addAlert = useAlertStore((s) => s.addAlert)
  const markAcknowledged = useAlertStore((s) => s.markAlertAcknowledged)
  const setKpi = useKpiStore((s) => s.setKpi)
  const setActiveAlert = useWatchStore((s) => s.setActiveAlert)

  const connect = useCallback(() => {
    if (!token) return
    const url = `${WS_URL}?token=${encodeURIComponent(token)}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('[WS] Connected')
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as { type: string; payload: Record<string, unknown> }

        switch (msg.type) {
          case 'ALERT': {
            const alert = msg.payload as unknown as Alert
            addAlert(alert)
            // Push to watch if HIGH or CRITICAL
            if (alert.severity === 'HIGH' || alert.severity === 'CRITICAL') {
              setActiveAlert(alert)
            }
            break
          }
          case 'ALERT_ACKNOWLEDGED': {
            const { alert_id } = msg.payload as { alert_id: string }
            markAcknowledged(alert_id)
            break
          }
          case 'KPI_UPDATE': {
            setKpi(msg.payload as unknown as SiteKPI)
            break
          }
          case 'PING': {
            ws.send(JSON.stringify({ type: 'PONG', payload: { ts: new Date().toISOString() } }))
            break
          }
          default:
            break
        }
      } catch {
        // Ignore parse errors
      }
    }

    ws.onclose = () => {
      console.log('[WS] Disconnected — reconnecting in 3s')
      reconnectTimer.current = setTimeout(connect, 3000)
    }

    ws.onerror = (e) => {
      console.warn('[WS] Error:', e)
    }
  }, [token, addAlert, markAcknowledged, setKpi, setActiveAlert])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [connect])

  const sendAcknowledge = useCallback((alertId: string, note?: string) => {
    wsRef.current?.send(
      JSON.stringify({ type: 'ACKNOWLEDGE_ALERT', payload: { alert_id: alertId, note } })
    )
  }, [])

  return { sendAcknowledge }
}
