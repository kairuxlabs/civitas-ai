import '@testing-library/jest-dom'
import { beforeAll, afterAll } from 'vitest'

// Stub WebSocket so hooks that reference WebSocket.OPEN don't crash in jsdom
if (typeof global.WebSocket === 'undefined') {
  class MockWS {
    static OPEN = 1
    static CLOSING = 2
    static CLOSED = 3
    static CONNECTING = 0
    readyState = 0
    onopen: (() => void) | null = null
    onmessage: ((e: MessageEvent) => void) | null = null
    onclose: (() => void) | null = null
    onerror: ((e: Event) => void) | null = null
    close() {}
  }
  global.WebSocket = MockWS as unknown as typeof WebSocket
}

// Mock window.matchMedia (not available in jsdom)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Stub Element.prototype.scrollIntoView (not implemented in jsdom)
Element.prototype.scrollIntoView = vi.fn()

// Silence known jsdom SVG warnings
const originalError = console.error
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    if (typeof args[0] === 'string' && args[0].includes('Not implemented: SVGElement')) return
    originalError(...args)
  }
})
afterAll(() => { console.error = originalError })
