import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  icon?: ReactNode
  testId?: string
  children: ReactNode
}

export default function Modal({ open, onClose, title, icon, testId, children }: ModalProps) {
  useEffect(() => {
    if (!open) return
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div
      role="presentation"
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/70 backdrop-blur-sm p-4 animate-[modal-fade_150ms_ease-out]"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        data-testid={testId}
        onClick={event => event.stopPropagation()}
        className="w-full max-w-lg max-h-[85vh] flex flex-col bg-surface-container-low border border-outline-variant rounded-2xl shadow-2xl overflow-hidden animate-[modal-in_180ms_ease-out]"
      >
        <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-outline-variant shrink-0">
          <h2 className="text-sm font-bold flex items-center gap-2 text-on-surface">
            {icon}{title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="p-1.5 rounded-full text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors"
          >
            <X size={18} />
          </button>
        </div>
        <div className="overflow-y-auto custom-scrollbar p-5">
          {children}
        </div>
      </div>
    </div>,
    document.body,
  )
}
