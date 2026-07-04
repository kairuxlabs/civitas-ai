import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWebSocket } from '../../hooks/useWebSocket'

// Minimal WebSocket mock with controllable callbacks
type WsCallback = ((e?: MessageEvent | CloseEvent | Event) => void) | null

let mockWsInstance: {
  onopen: WsCallback
  onmessage: WsCallback
  onclose: WsCallback
  onerror: WsCallback
  close: ReturnType<typeof vi.fn>
  readyState: number
}

const MockWebSocket = vi.fn(() => {
  mockWsInstance = {
    onopen: null,
    onmessage: null,
    onclose: null,
    onerror: null,
    close: vi.fn(),
    readyState: 0,
  }
  return mockWsInstance
})

vi.mock('../../services/api', () => ({
  createWebSocket: () => MockWebSocket(),
}))

beforeEach(() => {
  vi.useFakeTimers()
  MockWebSocket.mockClear()
})

afterEach(() => {
  vi.useRealTimers()
  vi.clearAllMocks()
})

describe('useWebSocket', () => {
  it('starts disconnected', () => {
    const onEvent = vi.fn()
    const { result } = renderHook(() => useWebSocket(onEvent))
    expect(result.current.connected).toBe(false)
  })

  it('sets connected=true when WebSocket opens', () => {
    const onEvent = vi.fn()
    const { result } = renderHook(() => useWebSocket(onEvent))

    act(() => {
      mockWsInstance.onopen?.(new Event('open'))
    })

    expect(result.current.connected).toBe(true)
  })

  it('calls onEvent when a message arrives', () => {
    const onEvent = vi.fn()
    renderHook(() => useWebSocket(onEvent))

    act(() => {
      mockWsInstance.onopen?.(new Event('open'))
    })

    const payload = { type: 'agent_update', agent: 'Traffic Agent', status: 'running', detail: '', ts: '2024-01-01T00:00:00Z' }
    act(() => {
      mockWsInstance.onmessage?.({ data: JSON.stringify(payload) } as MessageEvent)
    })

    expect(onEvent).toHaveBeenCalledTimes(1)
    expect(onEvent).toHaveBeenCalledWith(payload)
  })

  it('sets connected=false and schedules reconnect on close', () => {
    const onEvent = vi.fn()
    const { result } = renderHook(() => useWebSocket(onEvent))

    act(() => {
      mockWsInstance.onopen?.(new Event('open'))
    })
    expect(result.current.connected).toBe(true)

    act(() => {
      mockWsInstance.onclose?.()
    })
    expect(result.current.connected).toBe(false)

    // After 3s reconnect timer fires and a new WebSocket is created
    act(() => { vi.advanceTimersByTime(3000) })
    expect(MockWebSocket).toHaveBeenCalledTimes(2)
  })

  it('ignores malformed JSON messages without throwing', () => {
    const onEvent = vi.fn()
    renderHook(() => useWebSocket(onEvent))

    act(() => {
      mockWsInstance.onopen?.(new Event('open'))
    })
    expect(() => {
      act(() => {
        mockWsInstance.onmessage?.({ data: 'not-json{{{' } as MessageEvent)
      })
    }).not.toThrow()

    expect(onEvent).not.toHaveBeenCalled()
  })

  it('closes WebSocket on unmount', () => {
    const onEvent = vi.fn()
    const { unmount } = renderHook(() => useWebSocket(onEvent))

    act(() => {
      mockWsInstance.onopen?.(new Event('open'))
    })
    unmount()

    expect(mockWsInstance.close).toHaveBeenCalled()
  })
})
