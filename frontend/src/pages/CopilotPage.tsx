import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { MessageSquare, Send, Loader2, AlertCircle } from 'lucide-react'
import { copilotApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Record<string, unknown>[]
  mock?: boolean
}

const EXAMPLE_QUERIES = [
  'Why is EXC001 showing a hydraulic warning?',
  'What maintenance is due for EXC002?',
  'Which operators have pending safety training?',
  "Show today's proximity incidents",
  'What does the manual recommend for fault E-HYD-042?',
]

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello. I\'m the CAT MachOps Engineer Copilot. Ask me about machine health, maintenance, safety incidents, operator training, or site documentation.\n\n⚠ Disclaimer: Responses are generated from synthetic demo documents — not validated CAT documentation.',
    },
  ])
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const queryMutation = useMutation({
    mutationFn: (question: string) => copilotApi.query(question),
    onSuccess: (data, question) => {
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: question },
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          mock: data.mock,
        },
      ])
    },
    onError: () => {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }])
    },
  })

  function handleSend() {
    if (!input.trim() || queryMutation.isPending) return
    const q = input.trim()
    setInput('')
    queryMutation.mutate(q)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="AI Engineer Copilot"
        subtitle="Intelligent assistant for machine, safety, and maintenance queries"
        icon={<MessageSquare size={20} />}
      />

      <div className="flex-1 flex flex-col overflow-hidden p-6 gap-4">
        {/* Disclaimer banner */}
        <div className="flex items-center gap-2 bg-yellow-900/20 border border-yellow-800/30 rounded-lg px-4 py-2 text-xs text-yellow-400">
          <AlertCircle size={14} />
          Demo mode — responses generated from synthetic documents. Not validated CAT technical content.
        </div>

        {/* Example query chips */}
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => { setInput(q) }}
              className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1.5 rounded-full transition-colors"
              aria-label={`Use example query: ${q}`}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Chat messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-2xl rounded-xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-amber-500 text-slate-900'
                  : 'bg-slate-800 border border-slate-700 text-slate-200'
              }`}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-700">
                    <p className="text-xs text-slate-500 mb-1">Sources:</p>
                    {msg.sources.map((src, j) => (
                      <div key={j} className="text-xs text-slate-400 flex items-center gap-1">
                        <span className="text-amber-400">📄</span>
                        <span>{src.document as string}</span>
                        <span className="text-slate-600">— {src.chunk as string}</span>
                        <span className="text-slate-600 ml-auto">{((src.relevance as number) * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                    {msg.mock && <p className="text-xs text-slate-600 mt-1">Mock response — RAG model available in full deployment</p>}
                  </div>
                )}
              </div>
            </div>
          ))}
          {queryMutation.isPending && (
            <div className="flex justify-start">
              <div className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 flex items-center gap-2">
                <Loader2 size={14} className="animate-spin text-amber-400" />
                <span className="text-xs text-slate-400">Searching documentation…</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about machines, safety, maintenance, or operators…"
            className="flex-1 bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500"
            aria-label="Copilot query input"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || queryMutation.isPending}
            className="btn-primary px-4 disabled:opacity-50"
            aria-label="Send query"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
