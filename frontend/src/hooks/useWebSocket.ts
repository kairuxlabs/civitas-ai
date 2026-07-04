import { useEffect, useRef, useCallback, useState } from 'react'
import { createWebSocket } from '../services/api'
import type { AgentEvent } from '../types'

export function useWebSocket(onEvent: (e: AgentEvent) => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent
  const [connected, setConnected] = useState(false)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    const ws = createWebSocket()
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      setTimeout(connect, 3000)
    }
    ws.onerror = () => ws.close()
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as AgentEvent
        onEventRef.current(data)
      } catch { /* ignore malformed */ }
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])

  return { connected }
}
