import { useEffect, useMemo, useRef, useState } from "react"
import { Bot, Sparkles, Trash2, User2 } from "lucide-react"

import { api } from "@/components/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface Message {
  role: "user" | "assistant"
  content: string
  sources?: { title?: string; text?: string }[]
  createdAt: string
}

function formatTime(dateIso: string) {
  const d = new Date(dateIso)
  if (Number.isNaN(d.getTime())) return ""
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

const CHAT_SUGGESTION_POOL = [
  "Given my profile, where can I cut £200/month with the lowest pain?",
  "What is my weakest stress-test scenario and why?",
  "How should I split extra monthly income between savings and debt?",
  "Give me a 4-week plan to improve my resilience score.",
  "Can you explain my spending breakdown in plain English?",
  "What are my biggest fixed-cost pressure points?",
  "If I lose my job, what should I cut first and second?",
  "How much emergency fund do I need based on my expenses?",
  "What one change would improve my stress scores fastest?",
  "Should I clear debt first or increase savings buffer first?",
  "How can I reduce wants spending without feeling deprived?",
  "Review my budget and suggest a realistic weekly spending cap.",
  "How much can I safely spend on fun this month?",
  "Which subscriptions look least valuable to keep?",
  "What are my top three overspending categories?",
  "How far am I from a 20% savings rate?",
  "Show me a low-effort plan to save £100 this month.",
  "If rent increases by £150, what should I adjust?",
  "How should I budget if my income is irregular?",
  "Can I afford a £1,000 purchase in the next two months?",
  "How much buffer do I need to survive 3 months with no income?",
  "What would happen if I cut eating out by 40%?",
  "What spending category gives the highest savings leverage?",
  "Give me a paycheck allocation template based on my profile.",
  "How can I make my budget less fragile to shocks?",
  "What should my monthly debt repayment target be?",
  "Can you spot warning signs in my current cashflow?",
  "How can I recover quickly after an emergency expense?",
  "What would improve my job-loss score by at least 1 point?",
  "Should I build emergency fund or invest first?",
  "How do I plan for annual costs in a monthly budget?",
  "What is a realistic no-buy challenge for me this month?",
  "How can I reduce transport costs without major lifestyle changes?",
  "How much should I keep in instant-access cash?",
  "If I get a 10% raise, how should I allocate it?",
  "Can you draft a weekly spending check-in routine?",
  "What are my best quick wins in the next 7 days?",
  "How can I avoid lifestyle inflation after a pay rise?",
  "How should I budget when debt payments are high?",
  "What is my likely break-even monthly expense level?",
  "Can you compare my current spending to 50/30/20 targets?",
  "Where am I most likely underestimating expenses?",
  "How can I keep motivation while paying off debt?",
  "What should I automate to improve money discipline?",
  "Can you create a monthly reset checklist for my finances?",
  "What habits would improve my financial stability over 90 days?",
  "How can I protect myself from a one-time £2,000 shock?",
  "If I lose 20% income, what is my best fallback plan?",
  "How can I increase my monthly surplus without side income?",
  "Can you help me build a minimalist emergency budget?",
  "What should I change first if my bills keep creeping up?",
  "How do I decide between paying extra debt vs building cash?",
  "Can you estimate how much monthly slack I really have?",
  "What if I pause all subscriptions for 60 days?",
  "Which category should I cap first for fastest impact?",
  "How can I set spending limits that I will stick to?",
  "Can you draft a no-spend weekend plan that still feels fun?",
  "What is a sensible grocery budget for my profile?",
  "How can I reduce impulse purchases this month?",
  "How should I handle a month with unexpected travel costs?",
  "What budget guardrails should I set before payday?",
  "Can you suggest a daily money habit that improves control?",
  "How can I stop drifting above my planned wants budget?",
  "What should I do if I keep dipping into overdraft?",
  "How much should I target for a mini emergency buffer first?",
  "Can you estimate the financial impact of one fewer takeaway per week?",
  "What trade-offs should I make if I want to save £250/month?",
  "How do I make my pay rise actually improve resilience?",
  "Which debts are hurting my flexibility the most?",
  "Can you give me a crisis plan if my income pauses for 2 months?",
  "How do I budget for gifts and holidays without blowing my plan?",
  "Can you help me set category ceilings for the next 4 weeks?",
  "What should I do if my variable expenses spike unpredictably?",
  "How can I build a buffer while still repaying debt steadily?",
  "What should I review every Sunday for better cashflow control?",
  "Can you suggest a fallback budget for worst-case months?",
  "What can I sell or cut to quickly raise £500 cash buffer?",
  "How do I avoid using credit for small emergencies?",
  "Can you turn my monthly plan into simple weekly targets?",
  "How much could I save by reducing entertainment by 25%?",
  "What if I cap clothing spend for 8 weeks?",
  "Can you build me a low-stress austerity plan for one month?",
  "What should my next paycheck priorities be in order?",
  "How do I decide when to re-run stress tests?",
  "Can you explain where my resilience score is leaking points?",
  "What one fixed-cost negotiation should I attempt this week?",
  "How can I lower my monthly burn rate without major disruption?",
  "Can you suggest a realistic target for monthly surplus?",
  "How should I plan if utility bills rise another 10%?",
  "What warning signals should make me tighten spending immediately?",
  "How do I preserve savings momentum during expensive months?",
  "Can you draft a 14-day stabilization plan for my cashflow?",
  "What should I stop buying first if I need emergency savings fast?",
  "How do I keep progress visible so I stay motivated?",
  "Can you suggest a low-friction envelope-style budget for me?",
  "What is the safest way to handle a temporary income dip?",
  "How much flexibility do I have before resilience turns moderate?",
  "What monthly checklist would keep my finances resilient?",
  "Can you simplify my budget into must-pay, should-pay, and optional?",
  "How can I prepare now for a potential large home repair?",
]

function pickRandomSuggestions(pool: string[], count: number): string[] {
  const shuffled = [...pool].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, Math.min(count, pool.length))
}

interface ChatProps {
  embedded?: boolean
}

export function Chat({ embedded = false }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const suggestions = useMemo(() => pickRandomSuggestions(CHAT_SUGGESTION_POOL, 5), [])

  useEffect(() => {
    api
      .get("/api/v1/chat/history")
      .json((history: { role: string; content: string; sources?: { title?: string; text?: string }[]; created_at?: string }[]) => {
        setMessages(
          history.map((m, index) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
            sources: m.sources,
            createdAt: m.created_at ?? new Date(Date.now() - (history.length - index) * 45000).toISOString(),
          }))
        )
      })
      .catch(() => {
        /* user can still chat */
      })
      .finally(() => setHistoryLoaded(true))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  const sendMessage = () => {
    const text = input.trim()
    if (!text || loading || clearing) return
    setError(null)

    const now = new Date().toISOString()
    const newMessages: Message[] = [...messages, { role: "user", content: text, createdAt: now }]
    setMessages(newMessages)
    setInput("")
    setLoading(true)

    api
      .post(
        {
          message: text,
          history: newMessages.slice(0, -1).map((m) => ({ role: m.role, content: m.content })),
          store_history: true,
        },
        "/api/v1/chat"
      )
      .json((res: { response: string; sources: { title?: string; text?: string }[] }) => {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: res.response,
            sources: res.sources,
            createdAt: new Date().toISOString(),
          },
        ])
      })
      .catch(() => {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Sorry, something went wrong. Please try again.",
            createdAt: new Date().toISOString(),
          },
        ])
        setError("Unable to send message right now.")
      })
      .finally(() => setLoading(false))
  }

  const clearChat = () => {
    if (loading || clearing) return
    setClearing(true)
    setError(null)

    api
      .delete("/api/v1/chat/history")
      .json(() => {
        setMessages([])
      })
      .catch(() => setError("Couldn't clear chat history. Please try again."))
      .finally(() => setClearing(false))
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const applySuggestion = (question: string) => {
    if (loading || clearing) return
    setInput(question)
  }

  return (
    <div className={`${embedded ? "flex h-[calc(100vh-18rem)] w-full flex-col" : "mx-auto flex h-full w-full max-w-5xl flex-col px-6 py-6"}`}>
      <div className={`${embedded ? "mb-4 rounded-2xl border bg-card px-5 py-4 shadow-sm" : "mb-4 rounded-2xl border bg-card px-5 py-4 shadow-sm"}`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Sparkles className="h-4 w-4 text-emerald-600" />
            Financial Assistant Chat
          </h2>
          <Button variant="outline" size="sm" onClick={clearChat} disabled={clearing || loading || messages.length === 0}>
            <Trash2 className="h-3.5 w-3.5" />
            {clearing ? "Clearing..." : "Clear Chat"}
          </Button>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">Ask about budgeting, debt, savings, and scenario planning.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {suggestions.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => applySuggestion(q)}
              className="rounded-full border bg-background px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {!historyLoaded && <p className="text-sm text-muted-foreground">Loading history...</p>}

          {historyLoaded && messages.length === 0 && (
            <p className="rounded-xl border border-dashed px-4 py-8 text-center text-sm text-muted-foreground">
              Ask a question to get personalized financial guidance.
            </p>
          )}

          {messages.map((msg, i) => {
            const isUser = msg.role === "user"
            const uniqueSources =
              msg.sources
                ?.map((s) => s.title ?? "reference")
                .filter((title, idx, arr) => arr.indexOf(title) === idx) ?? []

            return (
              <div key={`${msg.role}-${i}`} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] space-y-1 ${isUser ? "items-end" : "items-start"}`}>
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm shadow-sm ${
                      isUser
                        ? "bg-gradient-to-br from-emerald-600 to-emerald-500 text-white"
                        : "border bg-muted/40 text-foreground"
                    }`}
                  >
                    <div className="mb-1.5 flex items-center gap-1.5 text-[11px] opacity-80">
                      {isUser ? <User2 className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                      <span>{isUser ? "You" : "FinLit Assistant"}</span>
                    </div>
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    {uniqueSources.length > 0 && !isUser && (
                      <p className="mt-2 text-xs opacity-70">Sources: {uniqueSources.join(", ")}</p>
                    )}
                  </div>
                  <p className="px-1 text-[11px] text-muted-foreground">{formatTime(msg.createdAt)}</p>
                </div>
              </div>
            )
          })}

          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl border bg-muted/40 px-4 py-3 text-sm text-muted-foreground">Thinking...</div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="border-t bg-background/65 p-4 backdrop-blur">
          <div className="flex gap-2">
            <Input
              placeholder="Ask about your finances..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading || clearing}
              className="h-11 flex-1"
            />
            <Button onClick={sendMessage} disabled={loading || clearing || !input.trim()} className="h-11 px-5">
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
