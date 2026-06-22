import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Send, Bot, User } from 'lucide-react'
import { api } from '../services/api'
import type { DecisionOut, District } from '../types'

type Message =
  | { role: 'assistant'; text: string }
  | { role: 'user'; text: string }
  | { role: 'assistant-decision'; text: string; decision: DecisionOut }

const WELCOME: Message = {
  role: 'assistant',
  text: 'Xin chào, tôi là Civitas AI. Tôi có thể giúp gì cho việc quản lý thành phố hôm nay? Hãy chọn quận và đặt câu hỏi.',
}

function DecisionCard({ decision }: { decision: DecisionOut }) {
  return (
    <div className="mt-3 space-y-3 text-sm">
      {decision.recommendations.length > 0 && (
        <div>
          <p className="text-blue-300 font-medium mb-1">Khuyến nghị:</p>
          <ul className="space-y-1">
            {decision.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-slate-300">
                <span className="text-blue-400 mt-0.5 shrink-0">•</span> {r}
              </li>
            ))}
          </ul>
        </div>
      )}
      {Object.keys(decision.prediction).length > 0 && (
        <div className="grid grid-cols-1 gap-1">
          {Object.entries(decision.prediction).map(([k, v]) => (
            <div key={k} className="flex justify-between text-xs py-1 border-b border-slate-600/40">
              <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
              <span className="text-slate-200 font-medium">{v}</span>
            </div>
          ))}
        </div>
      )}
      <div className="flex items-center gap-2 pt-1">
        <div className="flex-1 h-1 bg-slate-600 rounded-full">
          <div className="h-1 bg-blue-500 rounded-full" style={{ width: `${decision.confidence}%` }} />
        </div>
        <span className="text-xs text-slate-400">Confidence {Math.round(decision.confidence)}%</span>
      </div>
    </div>
  )
}

function ChatBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${isUser ? 'bg-slate-700' : 'bg-blue-600'}`}>
        {isUser ? <User size={15} className="text-slate-300" /> : <Bot size={15} className="text-white" />}
      </div>
      <div className={`max-w-[78%] p-4 rounded-2xl shadow-sm ${
        isUser
          ? 'bg-blue-600 text-white rounded-tr-none'
          : 'bg-slate-700 text-slate-200 rounded-tl-none border border-slate-600'
      }`}>
        <p className="text-sm leading-relaxed">{msg.text}</p>
        {msg.role === 'assistant-decision' && <DecisionCard decision={msg.decision} />}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
        <Bot size={15} className="text-white" />
      </div>
      <div className="bg-slate-700 px-5 py-4 rounded-2xl rounded-tl-none border border-slate-600 flex items-center gap-1.5">
        {[0, 200, 400].map(delay => (
          <div key={delay} className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: `${delay}ms` }} />
        ))}
      </div>
    </div>
  )
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([WELCOME])
  const [query, setQuery] = useState('')
  const [districtId, setDistrictId] = useState<number>(1)
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: districts = [] } = useQuery<District[]>({ queryKey: ['districts'], queryFn: api.getDistricts })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const districtName = districts.find(d => d.id === districtId)?.name ?? 'quận đã chọn'

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || loading) return

    const userText = query.trim()
    setMessages(prev => [...prev, { role: 'user', text: userText }])
    setQuery('')
    setLoading(true)

    try {
      const decision = await api.chat(userText, districtId)
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant-decision',
          text: `Dựa trên dữ liệu thời gian thực tại ${districtName}, đây là phân tích của tôi:`,
          decision,
        },
      ])
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', text: 'Xin lỗi, có lỗi kết nối đến hệ thống. Vui lòng thử lại sau.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-sm"
      style={{ height: 'calc(100vh - 12rem)' }}>

      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-700 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Bot className="text-white w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-slate-100">Civitas AI Copilot</h3>
            <p className="text-xs text-green-400 flex items-center gap-1 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-green-500 inline-block animate-pulse" /> Trực tuyến
            </p>
          </div>
        </div>
        <select
          value={districtId}
          onChange={e => setDistrictId(Number(e.target.value))}
          className="text-sm bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-blue-500"
        >
          {districts.map((d: District) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar bg-slate-800/50">
        {messages.map((msg, i) => <ChatBubble key={i} msg={msg} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-slate-900 border-t border-slate-700">
        <form onSubmit={handleSend} className="relative flex items-center">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder={`Hỏi về tình hình đô thị tại ${districtName}...`}
            className="w-full bg-slate-800 border border-slate-600 rounded-xl py-3 pl-4 pr-12 text-slate-200 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-sm"
          />
          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="absolute right-2 p-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white transition-colors"
          >
            <Send size={17} />
          </button>
        </form>
        <p className="text-center text-xs text-slate-500 mt-3">
          Civitas AI có thể cung cấp thông tin chưa chuẩn xác. Hãy luôn đối chiếu với dữ liệu thực tế.
        </p>
      </div>
    </div>
  )
}
