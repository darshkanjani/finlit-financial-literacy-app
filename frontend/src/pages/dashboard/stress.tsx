import { useEffect, useState } from "react"
import { Activity, Play, ShieldAlert } from "lucide-react"

import { api } from "@/components/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatCurrency, normalizeCurrencyCode } from "@/lib/currency"

interface StressResult {
  id: string
  scenario_type: string
  params: {
    score_breakdown?: {
      survival?: number
      buffer?: number
      cashflow?: number
      stability?: number
    }
    score_meta?: {
      months_survived?: number
      horizon_months?: number
      end_buffer?: number
      target_buffer?: number
      avg_net?: number
      net_volatility?: number
    }
    [key: string]: unknown
  }
  monthly_projections: { month: number; income: number; expenses: number; savings_remaining: number; net: number }[]
  months_until_broke: number | null
  month_broke: number | null
  resilience_score: number
  created_at: string | null
}

export const SCENARIOS = [
  {
    id: "job_loss",
    label: "Job Loss",
    description: "Simulate loss of income and see how long your current savings buffer can sustain you.",
    assumptions: [
      "Default assumption: income drops to 0 unless a replacement is configured.",
      "Wants can be cut in later months; fixed needs remain.",
    ],
  },
  {
    id: "emergency",
    label: "Emergency Expense",
    description: "Apply a one-off emergency equal to one month of income to measure recovery speed.",
    extraParams: (income: number) => ({ amount: income }),
    assumptions: [
      "Default emergency amount is one month of your current income.",
      "Income and normal expenses continue after the shock.",
    ],
  },
  {
    id: "promotion",
    label: "Promotion / Income Boost",
    description: "Model a 20% income increase and project the upside for savings and resilience.",
    extraParams: () => ({ income_increase_percent: 20, lifestyle_inflation_percent: 0 }),
    assumptions: [
      "Income increases by 20% in the model.",
      "Lifestyle inflation is 0% by default (expenses unchanged).",
    ],
  },
]

function resilienceTone(score: number) {
  if (score >= 8.5) return "text-emerald-600"
  if (score >= 7) return "text-green-600"
  if (score >= 5) return "text-amber-600"
  if (score >= 3) return "text-orange-600"
  return "text-red-600"
}

function resilienceLabel(score: number) {
  if (score >= 8.5) return "Excellent"
  if (score >= 7) return "Strong"
  if (score >= 5) return "Good"
  if (score >= 3) return "Moderate"
  return "Low"
}

function interpretation(score: number) {
  if (score >= 8.5) return "Very resilient in this scenario."
  if (score >= 7) return "Generally resilient, with manageable risk."
  if (score >= 5) return "Mixed resilience. A tighter plan would help."
  if (score >= 3) return "Fragile. A moderate shock may strain finances."
  return "High risk. Savings can deplete quickly."
}

export function StressTest() {
  const [results, setResults] = useState<StressResult[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [profileIncome, setProfileIncome] = useState(0)
  const [currencyCode, setCurrencyCode] = useState("GBP")

  useEffect(() => {
    Promise.all([
      api.get("/api/v1/stress-test/history").json((d: StressResult[]) => setResults(d)),
      api
        .get("/api/v1/profile")
        .json((p: { monthly_income: number; currency_code?: string }) => {
          setProfileIncome(p.monthly_income)
          setCurrencyCode(normalizeCurrencyCode(p.currency_code))
        }),
    ])
      .catch(() => setError("Failed to load stress test data. Complete your profile to run scenarios."))
      .finally(() => setLoading(false))
  }, [])

  const runScenario = (scenarioId: string) => {
    const scenario = SCENARIOS.find((s) => s.id === scenarioId)
    if (!scenario) return

    setRunning(scenarioId)
    setError(null)

    const params = scenario.extraParams ? scenario.extraParams(profileIncome) : {}

    api
      .post({ scenario_type: scenarioId, params }, "/api/v1/stress-test/run")
      .error(400, () => setError("Complete your financial profile before running stress tests."))
      .json((result: StressResult) => {
        setResults((prev) => [result, ...prev.filter((r) => r.scenario_type !== scenarioId)])
      })
      .catch(() => setError("Failed to run scenario. Please try again."))
      .finally(() => setRunning(null))
  }

  if (loading) return <p className="p-6 text-sm text-muted-foreground">Loading...</p>

  const latestByScenario: Record<string, StressResult> = {}
  for (const r of results) {
    if (!latestByScenario[r.scenario_type]) latestByScenario[r.scenario_type] = r
  }

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6 px-6 py-6">
      <div className="rounded-2xl border bg-card p-5 shadow-sm">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <ShieldAlert className="h-4 w-4 text-emerald-600" />
          Financial Stress Tests
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Run what-if scenarios to understand downside risk and the strength of your safety margin.
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          Score formula: <span className="font-medium">40% survival + 30% end-buffer + 20% cashflow + 10% stability</span>.
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Each scenario has its own score. Overall resilience on Summary is the average of your latest run for each scenario.
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Income input for these simulations is your profile net take-home income (after tax), not gross salary.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      <div className="grid gap-4">
        {SCENARIOS.map((scenario) => {
          const latest = latestByScenario[scenario.id]
          const isRunning = running === scenario.id
          const maxSavings = Math.max(...(latest?.monthly_projections.slice(0, 12).map((x) => Math.max(x.savings_remaining, 0)) ?? [0]))
          const scoreBreakdown = latest?.params?.score_breakdown
          const scoreMeta = latest?.params?.score_meta

          return (
            <Card key={scenario.id} className="overflow-hidden border-emerald-200/60 bg-white/90">
              <CardHeader className="pb-3">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <CardTitle className="text-base">{scenario.label}</CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">{scenario.description}</p>
                    <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                      {scenario.assumptions.map((item) => (
                        <li key={item}>• {item}</li>
                      ))}
                    </ul>
                  </div>
                  <Button hidden size="sm" variant="outline" onClick={() => runScenario(scenario.id)} disabled={!!running}>
                    <Play className="mr-1 h-3 w-3" />
                    {isRunning ? "Running..." : "Run"}
                  </Button>
                </div>
              </CardHeader>

              <CardContent>
                {!latest && <p className="text-sm text-muted-foreground">No run yet for this scenario.</p>}

                {latest && (
                  <div className="space-y-4 rounded-xl border bg-muted/25 p-4">
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.1em] text-muted-foreground">Resilience score</p>
                        <p className={`text-2xl font-bold tabular-nums ${resilienceTone(latest.resilience_score)}`}>
                          {latest.resilience_score.toFixed(1)}
                          <span className="text-sm font-normal">/10</span>
                        </p>
                        <p className={`text-xs font-medium ${resilienceTone(latest.resilience_score)}`}>
                          {resilienceLabel(latest.resilience_score)}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">{interpretation(latest.resilience_score)}</p>
                      </div>

                      {scenario.id !== "promotion" ? (
                        <div>
                          <p className="text-xs uppercase tracking-[0.1em] text-muted-foreground">Months until broke</p>
                          <p className="text-2xl font-bold tabular-nums">
                            {latest.months_until_broke === null ? `>${latest.monthly_projections.length}` : latest.months_until_broke === 0 ? "<1" : latest.months_until_broke}
                          </p>
                        </div>
                      ) : (
                        <div>
                          <p className="text-xs uppercase tracking-[0.1em] text-muted-foreground">Trajectory</p>
                          <p className="text-sm font-medium text-emerald-700">Growth scenario</p>
                        </div>
                      )}

                      <div>
                        <p className="text-xs uppercase tracking-[0.1em] text-muted-foreground">Last run</p>
                        <p className="text-sm">
                          {latest.created_at ? new Date(latest.created_at).toLocaleDateString() : "Unavailable"}
                        </p>
                      </div>
                    </div>

                    {scoreBreakdown && (
                      <div className="space-y-2 rounded-lg border bg-background p-3">
                        <p className="text-xs text-muted-foreground">
                          How this score was built for this scenario:
                        </p>
                        <div className="grid gap-2 sm:grid-cols-4">
                          <div>
                            <p className="text-[11px] uppercase tracking-[0.08em] text-muted-foreground">Survival</p>
                            <p className="text-sm font-semibold tabular-nums">{(scoreBreakdown.survival ?? 0).toFixed(1)}/10</p>
                          </div>
                          <div>
                            <p className="text-[11px] uppercase tracking-[0.08em] text-muted-foreground">Buffer</p>
                            <p className="text-sm font-semibold tabular-nums">{(scoreBreakdown.buffer ?? 0).toFixed(1)}/10</p>
                          </div>
                          <div>
                            <p className="text-[11px] uppercase tracking-[0.08em] text-muted-foreground">Cashflow</p>
                            <p className="text-sm font-semibold tabular-nums">{(scoreBreakdown.cashflow ?? 0).toFixed(1)}/10</p>
                          </div>
                          <div>
                            <p className="text-[11px] uppercase tracking-[0.08em] text-muted-foreground">Stability</p>
                            <p className="text-sm font-semibold tabular-nums">{(scoreBreakdown.stability ?? 0).toFixed(1)}/10</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {scoreMeta && (
                      <p className="text-xs text-muted-foreground">
                        End buffer: <span className="font-medium text-foreground">{formatCurrency(scoreMeta.end_buffer ?? 0, currencyCode)}</span>
                        {" · "}
                        Target safety buffer: <span className="font-medium text-foreground">{formatCurrency(scoreMeta.target_buffer ?? 0, currencyCode)}</span>
                        {" · "}
                        Avg monthly net: <span className="font-medium text-foreground">{formatCurrency(scoreMeta.avg_net ?? 0, currencyCode)}</span>
                      </p>
                    )}

                    {!scoreBreakdown && (
                      <p className="text-xs text-amber-700">
                        This run was generated before component breakdowns were enabled. Re-run this scenario to see full explanation data.
                      </p>
                    )}

                    {latest.monthly_projections.length > 0 && (
                      <div>
                        <p className="mb-2 flex items-center gap-1.5 text-xs uppercase tracking-[0.1em] text-muted-foreground">
                          <Activity className="h-3.5 w-3.5" />
                          Savings over time (12 months)
                        </p>
                        <div className="flex h-16 items-end gap-1 rounded-lg border bg-background px-2 py-2">
                          {latest.monthly_projections.slice(0, 12).map((month) => {
                            const h = maxSavings > 0 ? Math.max((month.savings_remaining / maxSavings) * 100, 0) : 0
                            return (
                              <div key={month.month} className="flex flex-1 flex-col items-center justify-end gap-1">
                                <div
                                  className={`w-full rounded-sm ${month.savings_remaining <= 0 ? "bg-red-400" : "bg-emerald-500"}`}
                                  style={{ height: `${Math.min(h, 100)}%` }}
                                  title={`Month ${month.month}: ${formatCurrency(month.savings_remaining, currencyCode)}`}
                                />
                                <span className="text-[9px] text-muted-foreground">{month.month}</span>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
