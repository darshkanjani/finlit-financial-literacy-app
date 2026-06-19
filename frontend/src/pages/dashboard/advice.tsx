import { useEffect, useMemo, useState } from "react"
import { ChevronDown, ChevronUp, Sparkles, Trash2 } from "lucide-react"

import { api } from "@/components/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

interface AdviceItem {
  id: string
  question?: string | null
  advice: string
  action_items: string[]
  sources: { title: string; url?: string }[]
  confidence: number
  created_at: string
}

function formatDate(iso: string) {
  if (!iso) return ""
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleDateString()
}

function AdviceCard({ item }: { item: AdviceItem }) {
  const [expanded, setExpanded] = useState(false)

  const uniqueSources = item.sources.filter((s, i, arr) => arr.findIndex((x) => x.title === s.title) === i)

  return (
    <Card className="overflow-hidden border-emerald-200/60 bg-white/95">
      <CardContent className="pt-5">
        {item.question && (
          <div className="mb-3 rounded-lg border bg-muted/20 px-3 py-2">
            <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">You asked</p>
            <p className="mt-1 text-sm">{item.question}</p>
          </div>
        )}
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{item.advice}</p>

        {item.action_items.length > 0 && (
          <div className="mt-4 rounded-xl border bg-muted/25 p-3">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">Action items</p>
            <ul className="space-y-1.5">
              {item.action_items.map((action, i) => (
                <li key={action} className="flex gap-2 text-sm">
                  <span className="font-semibold text-emerald-700">{i + 1}.</span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-3">
            <span>Confidence: {Math.round(item.confidence * 100)}%</span>
            {uniqueSources.length > 0 && (
              <button
                onClick={() => setExpanded((v) => !v)}
                className="inline-flex items-center gap-0.5 rounded-full border bg-background px-2 py-0.5 hover:text-foreground"
              >
                {uniqueSources.length} source{uniqueSources.length > 1 ? "s" : ""}
                {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>
            )}
          </div>
          {formatDate(item.created_at) && <span>{formatDate(item.created_at)}</span>}
        </div>

        {expanded && uniqueSources.length > 0 && (
          <div className="mt-2 space-y-1 border-t pt-2">
            {uniqueSources.map((source) => (
              <p key={source.title} className="text-xs text-muted-foreground">
                {source.title}
              </p>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

const ADVICE_SUGGESTION_POOL = [
  "Review my spending and give 3 high-impact improvements.",
  "Build me a debt-vs-savings priority order for this month.",
  "What should I do first to improve job-loss resilience?",
  "Create a realistic 90-day financial improvement plan.",
  "Give me a simple emergency-fund build strategy from my current numbers.",
  "What actions can improve my composite resilience score in 30 days?",
  "Suggest a monthly plan to hit my goal faster without burnout.",
  "Identify unnecessary expense categories and propose replacements.",
  "How should I adjust if my income drops by 20% next month?",
  "Prioritize my next three financial actions with reasons.",
  "Create a debt payoff + savings buffer hybrid plan for me.",
  "Give me a low-risk plan to stabilize cashflow over the next quarter.",
  "Design a 30-day spending reset plan tailored to my profile.",
  "Give me a practical plan to save £300 over the next 8 weeks.",
  "How can I improve savings rate without cutting essentials?",
  "What is the best sequence to improve all three stress scenarios?",
  "Create a weekly debt payoff routine I can actually follow.",
  "Recommend a realistic emergency-fund target and timeline.",
  "Give me a 3-tier expense cutback plan (easy, medium, hard).",
  "How can I reduce fixed costs over the next month?",
  "What should I do if my expenses are volatile month to month?",
  "Build a plan for handling irregular annual bills.",
  "Recommend a budget split based on my current spending behavior.",
  "How can I improve buffer score specifically?",
  "How can I improve stability score specifically?",
  "How can I improve cashflow score specifically?",
  "How can I improve survival score specifically?",
  "Give me an emergency expense recovery plan for 60 days.",
  "Create a side-income use plan: debt, buffer, and goals allocation.",
  "Draft a monthly money review template for me.",
  "What should I stop, start, and continue financially this month?",
  "Create a conservative plan for uncertain income months.",
  "Give me a pay-rise allocation strategy to avoid lifestyle inflation.",
  "What actions should I take before rerunning stress tests?",
  "How can I turn my weakest scenario into at least 'good'?",
  "Build a plan to move from moderate to strong resilience.",
  "Suggest realistic spending guardrails for each week.",
  "How should I balance debt repayment and emergency savings now?",
  "Give me a plan to cut wants without reducing quality of life too much.",
  "Recommend a habit stack for better financial discipline.",
  "What should my top three money priorities be this quarter?",
  "Create a debt avalanche plan using my likely profile context.",
  "Create a debt snowball plan and compare trade-offs.",
  "Give me a low-friction automation plan (standing orders, pots, limits).",
  "How can I prepare for a possible job-loss risk in the next 6 months?",
  "Give me a realistic plan to increase monthly surplus by £150.",
  "How should I split savings across emergency fund and goals?",
  "What financial actions give highest ROI for me this month?",
  "Design a 12-week resilience improvement roadmap.",
  "What should I do this week to avoid relying on credit in emergencies?",
  "Create a 60-day plan to increase my cash buffer by £500.",
  "Build a realistic debt reduction plan for the next 12 weeks.",
  "Recommend a strict but sustainable version of my monthly budget.",
  "Give me a balanced plan for debt, emergency fund, and goals.",
  "What should I prioritize if my expenses rise suddenly?",
  "Design a fallback budget for lower-income months.",
  "How can I improve resilience without feeling overly restricted?",
  "Give me a practical 'first 5 actions' checklist for this month.",
  "Create a monthly plan for reducing wants spending by 20%.",
  "What is the fastest safe path to a 3-month emergency fund?",
  "Propose a 4-step plan to reduce fixed costs over the next quarter.",
  "How should I respond if my stress score drops after rerun?",
  "Give me an action plan for recovering after an expensive month.",
  "Design a weekly budget rhythm I can realistically maintain.",
  "Recommend a plan to avoid overdraft use entirely.",
  "How should I sequence goals if I can only fund one at a time?",
  "Create an annual-expense sinking fund plan for me.",
  "Give me a robust plan for managing irregular costs.",
  "What should my monthly review template include?",
  "Build a realistic plan to improve my weakest scenario first.",
  "How can I protect gains after my resilience improves?",
  "Suggest a resilient paycheck allocation model for my situation.",
  "What should I automate immediately to reduce decision fatigue?",
  "Create a low-burn emergency mode plan for 8 weeks.",
  "How can I set limits that prevent end-of-month overspending?",
  "Propose a plan to improve buffer and stability together.",
  "Give me a conservative strategy for uncertain job outlook.",
  "How can I make goal saving consistent during debt payoff?",
  "Recommend a plan for coping with one-off bills without debt.",
  "What should I change if promotion gains are being eaten by spending?",
  "Create a three-phase financial stabilization strategy.",
  "How should I rebalance priorities after a financial setback?",
  "Give me a plan to raise monthly surplus by £200 in 6 weeks.",
  "What would a resilient quarter look like for my finances?",
  "Suggest an anti-lifestyle-inflation checklist for pay rises.",
  "How can I improve financial discipline with minimal friction?",
  "Build a practical no-credit emergency protocol for me.",
  "Give me an expense triage playbook for difficult months.",
  "How can I tighten spending while preserving essentials and wellbeing?",
  "Design a monthly cashflow stabilization plan with milestones.",
  "What should I do first if my debt-to-income ratio feels high?",
  "Create a weekly plan to stay within spending limits.",
  "Give me a stronger emergency scenario response plan.",
  "How can I move from good to strong resilience this quarter?",
  "Recommend a phased debt repayment strategy with checkpoints.",
  "Build me a realistic financial habit plan for the next 30 days.",
  "How should I prepare now for potential job instability later this year?",
  "What’s my best plan if I want both security and progress?",
  "Create a practical money operating system I can follow monthly.",
]

function pickRandomSuggestions(pool: string[], count: number): string[] {
  const shuffled = [...pool].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, Math.min(count, pool.length))
}

interface AdviceProps {
  embedded?: boolean
}

export function Advice({ embedded = false }: AdviceProps) {
  const [history, setHistory] = useState<AdviceItem[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [message, setMessage] = useState("")
  const [error, setError] = useState<string | null>(null)
  const suggestions = useMemo(() => pickRandomSuggestions(ADVICE_SUGGESTION_POOL, 5), [])

  useEffect(() => {
    api
      .get("/api/v1/advice/history")
      .json((data: AdviceItem[]) => setHistory(data))
      .catch(() => setError("Failed to load advice history."))
      .finally(() => setLoading(false))
  }, [])

  const generate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    setGenerating(true)
    setError(null)

    api
      .post({ message: message.trim() }, "/api/v1/advice")
      .error(400, () => setError("Complete your financial profile before generating advice."))
      .json((item: AdviceItem) => {
        setHistory((prev) => [item, ...prev])
        setMessage("")
      })
      .catch(() => setError("Failed to generate advice. Please try again."))
      .finally(() => setGenerating(false))
  }

  const clearAdvice = () => {
    if (clearing || generating || history.length === 0) return
    setClearing(true)
    setError(null)

    api
      .delete("/api/v1/advice/history")
      .json(() => setHistory([]))
      .catch(() => setError("Failed to clear advice history. Please try again."))
      .finally(() => setClearing(false))
  }

  const applySuggestion = (question: string) => {
    if (generating || clearing) return
    setMessage(question)
  }

  if (loading) return <p className="p-6 text-sm text-muted-foreground">Loading...</p>

  return (
    <div className={`${embedded ? "w-full space-y-6" : "mx-auto w-full max-w-5xl space-y-6 px-6 py-6"}`}>
      <div className="rounded-2xl border bg-card p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Sparkles className="h-4 w-4 text-emerald-600" />
            AI Financial Advice
          </h2>
          <Button variant="outline" size="sm" onClick={clearAdvice} disabled={clearing || generating || history.length === 0}>
            <Trash2 className="h-3.5 w-3.5" />
            {clearing ? "Clearing..." : "Clear Advice"}
          </Button>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Ask for practical recommendations using your profile, spending behavior, and goals.
        </p>
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

      <Card className="border-emerald-200/60 bg-gradient-to-br from-emerald-50/70 to-lime-50/50">
        <CardHeader>
          <CardTitle className="text-base">Get New Advice</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={generate} className="flex flex-col gap-2 sm:flex-row">
            <Input
              placeholder="e.g. How can I improve my savings rate?"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={generating || clearing}
              className="h-11 flex-1 bg-white"
            />
            <Button type="submit" disabled={generating || clearing || !message.trim()} className="h-11 px-5">
              {generating ? "Generating..." : "Ask"}
            </Button>
          </form>
          <p className="mt-2 text-xs text-muted-foreground">
            Try: "Review my spending", "How do I build an emergency fund?", "Should I pay debt or save first?"
          </p>
        </CardContent>
      </Card>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      {history.length === 0 ? (
        <div className="rounded-2xl border border-dashed bg-card px-5 py-10 text-center text-sm text-muted-foreground">
          No advice generated yet. Ask a question above to get started.
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <AdviceCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}
