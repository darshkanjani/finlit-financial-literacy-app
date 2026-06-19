import { useEffect, useMemo, useState } from "react"
import { AlertTriangle, ArrowUpRight, BadgePoundSterling, PiggyBank, ShieldAlert } from "lucide-react"

import { api } from "@/components/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  convertCurrencyWithRates,
  formatCurrency,
  FX_RATES_AS_OF,
  listSupportedCurrencies,
  normalizeCurrencyCode,
  type FxRatesPayload,
} from "@/lib/currency"

interface SpendingCategory {
  name: string
  amount: number
  percentage: number
  type: string
}

interface SpendingSummary {
  needs_percent: number
  wants_percent: number
  savings_percent: number
  target: { needs: number; wants: number; savings: number }
}

interface SpendingFlag {
  category: string
  status: string
  difference: number
  message: string
}

interface SpendingBreakdown {
  categories: SpendingCategory[]
  summary: SpendingSummary
  flags: SpendingFlag[]
}

interface ResilienceSummary {
  overall_score: number
  rating: string
  weakest_scenario: string | null
}

interface Goal {
  id: string
  goal_name: string
  target_amount: number
  current_amount: number
  target_date: string | null
  status: string
}

interface DashboardData {
  currency_code: string
  profile_monthly_income: number | null
  spending_breakdown: SpendingBreakdown | null
  resilience: ResilienceSummary | null
  goals: Goal[]
  latest_advice_summary: string | null
  has_completed_profile: boolean
  has_run_stress_test: boolean
  has_set_goals: boolean
}

interface SummaryProps {
  onGoToProfile: () => void
  onGoToAdvice: () => void
  onGoToStress: () => void
}

function getResilienceTone(score: number) {
  if (score >= 8.5) return "text-emerald-600"
  if (score >= 7) return "text-green-600"
  if (score >= 5) return "text-amber-600"
  if (score >= 3) return "text-orange-600"
  return "text-red-600"
}

export function Summary({ onGoToProfile, onGoToAdvice, onGoToStress }: SummaryProps) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [convertAmount, setConvertAmount] = useState("1000")
  const [fromCurrency, setFromCurrency] = useState("GBP")
  const [toCurrency, setToCurrency] = useState("USD")
  const [fxRates, setFxRates] = useState<FxRatesPayload | null>(null)

  useEffect(() => {
    api
      .get("/api/v1/dashboard")
      .json((d: DashboardData) => {
        setData(d)
        const base = normalizeCurrencyCode(d.currency_code)
        setFromCurrency(base)
        setToCurrency(base === "USD" ? "GBP" : "USD")
      })
      .catch(() => setError("Failed to load dashboard data."))
      .finally(() => setLoading(false))

    api
      .get("/api/v1/fx/rates")
      .json((rates: FxRatesPayload) => {
        setFxRates(rates)
        if (!rates.live) {
          api
            .get("/api/v1/fx/rates?force_refresh=true")
            .json((fresh: FxRatesPayload) => setFxRates(fresh))
            .catch(() => {})
        }
      })
      .catch(() => setFxRates(null))
  }, [])

  const computed = useMemo(() => {
    if (!data?.spending_breakdown) {
      return {
        totalMonthlySpend: 0,
        impliedIncome: 0,
        profileIncome: data?.profile_monthly_income ?? 0,
        monthlyNet: 0,
        hasInconsistency: false,
        inconsistencyDiff: 0,
        inconsistencyPct: 0,
      }
    }

    const totalMonthlySpend = data.spending_breakdown.categories.reduce((sum, cat) => sum + cat.amount, 0)
    const savingsRate = data.spending_breakdown.summary.savings_percent / 100
    const impliedIncome = savingsRate < 1 ? totalMonthlySpend / (1 - savingsRate) : 0
    const profileIncome = data.profile_monthly_income ?? 0
    const monthlyNet = profileIncome - totalMonthlySpend

    const inconsistencyDiff = Math.abs(profileIncome - impliedIncome)
    const inconsistencyPct = profileIncome > 0 ? inconsistencyDiff / profileIncome : 0
    const hasInconsistency = profileIncome > 0 && impliedIncome > 0 && inconsistencyDiff >= 300 && inconsistencyPct >= 0.2

    return {
      totalMonthlySpend,
      impliedIncome,
      profileIncome,
      monthlyNet,
      hasInconsistency,
      inconsistencyDiff,
      inconsistencyPct,
    }
  }, [data])

  if (loading) return <p className="p-6 text-sm text-muted-foreground">Loading...</p>
  if (error) return <p className="p-6 text-sm text-red-600">{error}</p>
  if (!data) return null
  const converterInput = Number.parseFloat(convertAmount)
  const converted = convertCurrencyWithRates(
    Number.isFinite(converterInput) ? converterInput : 0,
    fromCurrency,
    toCurrency,
    fxRates?.usd_per_currency,
  )

  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 px-6 py-6">
      {!data.has_completed_profile && (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-amber-200 bg-amber-50/90 px-4 py-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-600" />
            <p className="text-sm text-amber-900">
              Complete your financial profile to unlock accurate spending insights, stress tests, and personalized advice.
            </p>
          </div>
          <Button size="sm" variant="outline" onClick={onGoToProfile} className="border-amber-400 bg-white text-amber-900">
            Set up profile
          </Button>
        </div>
      )}

      {computed.hasInconsistency && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-amber-200 bg-amber-50/90 px-4 py-3">
          <p className="text-sm text-amber-900">
            Your profile income and model-implied income differ by {formatCurrency(computed.inconsistencyDiff, data.currency_code)} ({(computed.inconsistencyPct * 100).toFixed(0)}%).
            Please review your profile values for potential input errors.
          </p>
          <Button size="sm" variant="outline" className="border-amber-300 bg-white text-amber-900" onClick={onGoToProfile}>
            Review profile
          </Button>
        </div>
      )}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="border-emerald-200/70 bg-white/85">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Profile Net Income</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums">{formatCurrency(computed.profileIncome, data.currency_code)}</p>
            <p className="mt-1 text-xs text-muted-foreground">After-tax monthly take-home used in calculations</p>
          </CardContent>
        </Card>

        <Card className="border-emerald-200/70 bg-white/85">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Model-Implied Income</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums">{formatCurrency(computed.impliedIncome, data.currency_code)}</p>
            <p className="mt-1 text-xs text-muted-foreground">Derived from spend + savings rate</p>
          </CardContent>
        </Card>

        <Card className="border-emerald-200/70 bg-white/85">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Monthly Spend</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums">{formatCurrency(computed.totalMonthlySpend, data.currency_code)}</p>
            <p className="mt-1 text-xs text-muted-foreground">All tracked spending categories</p>
          </CardContent>
        </Card>

        <Card className="border-emerald-200/70 bg-white/85">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Resilience</CardTitle>
          </CardHeader>
          <CardContent>
            <p className={`text-2xl font-bold tabular-nums ${data.resilience ? getResilienceTone(data.resilience.overall_score) : "text-muted-foreground"}`}>
              {data.resilience ? `${data.resilience.overall_score.toFixed(1)}/10` : "N/A"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {data.resilience?.rating ? `Rating: ${data.resilience.rating}` : "Run a stress test to generate score"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Based on latest scenario runs (job loss, emergency, promotion).
            </p>
            <p className={`mt-1 text-xs ${computed.monthlyNet < 0 ? "text-red-600" : "text-muted-foreground"}`}>
              Monthly net from profile: {formatCurrency(computed.monthlyNet, data.currency_code)}
            </p>
          </CardContent>
        </Card>
      </section>

      <div className="rounded-xl border bg-muted/30 px-4 py-3 text-xs text-muted-foreground">
        Income note: stress tests and spending percentages use your profile <span className="font-medium text-foreground">net monthly income</span> (after tax).
      </div>

      <section className="rounded-2xl border bg-card p-5 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Currency Converter</h2>
          <p className="text-xs text-muted-foreground">
            Rates: {fxRates ? `${fxRates.as_of} (${fxRates.live ? "live" : "fallback"})` : FX_RATES_AS_OF}
          </p>
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          <Input
            type="number"
            min="0"
            step="0.01"
            value={convertAmount}
            onChange={(e) => setConvertAmount(e.target.value)}
            placeholder="Amount"
          />
          <select
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={fromCurrency}
            onChange={(e) => setFromCurrency(normalizeCurrencyCode(e.target.value))}
          >
            {listSupportedCurrencies().map((code) => (
              <option key={`from-${code}`} value={code}>{code}</option>
            ))}
          </select>
          <select
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={toCurrency}
            onChange={(e) => setToCurrency(normalizeCurrencyCode(e.target.value))}
          >
            {listSupportedCurrencies().map((code) => (
              <option key={`to-${code}`} value={code}>{code}</option>
            ))}
          </select>
          <div className="rounded-md border bg-muted/20 px-3 py-2 text-sm font-medium">
            {formatCurrency(converted, toCurrency)}
          </div>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Approximate converter for planning only. Final bank/card rates and fees may differ.
        </p>
        {fxRates?.source && (
          <p className="mt-1 text-xs text-muted-foreground">Source: {fxRates.source}</p>
        )}
        {!fxRates?.live && fxRates?.error && (
          <p className="mt-1 text-xs text-amber-700">{fxRates.error}</p>
        )}
      </section>

      {data.spending_breakdown && (
        <section className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Spending Breakdown</h2>
            <p className="text-xs text-muted-foreground">50/30/20 targets</p>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {[
              {
                label: "Needs",
                value: data.spending_breakdown.summary.needs_percent,
                target: data.spending_breakdown.summary.target.needs,
                tone: "from-emerald-600 to-emerald-500",
              },
              {
                label: "Wants",
                value: data.spending_breakdown.summary.wants_percent,
                target: data.spending_breakdown.summary.target.wants,
                tone: "from-teal-600 to-cyan-600",
              },
              {
                label: "Savings",
                value: data.spending_breakdown.summary.savings_percent,
                target: data.spending_breakdown.summary.target.savings,
                tone: "from-lime-600 to-emerald-500",
              },
            ].map(({ label, value, target, tone }) => (
              <div key={label} className="rounded-xl border bg-muted/25 p-4">
                <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div className={`h-full rounded-full bg-gradient-to-r ${tone}`} style={{ width: `${Math.min(value, 100)}%` }} />
                </div>
                <div className="mt-3 flex items-end justify-between">
                  <p className="text-2xl font-bold tabular-nums">{value.toFixed(0)}%</p>
                  <p className="text-xs text-muted-foreground">Target {target}%</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-5 space-y-3">
            {data.spending_breakdown.categories.map((cat) => (
              <div key={cat.name} className="grid grid-cols-[minmax(86px,130px)_1fr_auto_auto] items-center gap-3">
                <span className="text-sm capitalize text-muted-foreground">{cat.name.replace(/_/g, " ")}</span>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-emerald-500 transition-all"
                    style={{ width: `${Math.min(cat.percentage, 100)}%` }}
                  />
                </div>
                <span className="text-sm tabular-nums">{formatCurrency(cat.amount, data.currency_code)}</span>
                <span className="text-xs tabular-nums text-muted-foreground">{cat.percentage.toFixed(0)}%</span>
              </div>
            ))}
          </div>

          {data.spending_breakdown.flags.length > 0 && (
            <div className="mt-4 space-y-2">
              {data.spending_breakdown.flags.map((flag, i) => (
                <div key={`${flag.category}-${i}`} className="rounded-xl border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-orange-900">
                  {flag.message}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      <section className="grid gap-4 lg:grid-cols-2">
        <Card className="border-l-4 border-l-emerald-500">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <ShieldAlert className="h-4 w-4 text-emerald-600" />
              Financial Resilience
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {data.resilience ? (
              <>
                <p className="text-muted-foreground">
                  Overall score: <span className={`font-semibold ${getResilienceTone(data.resilience.overall_score)}`}>{data.resilience.overall_score.toFixed(1)}/10</span>
                </p>
                <p className="text-muted-foreground">
                  Composite score uses survival, end-buffer, cashflow, and stability.
                </p>
                {data.resilience.weakest_scenario && (
                  <p className="text-muted-foreground">
                    Weakest scenario: <span className="font-medium capitalize text-foreground">{data.resilience.weakest_scenario.replace(/_/g, " ")}</span>
                  </p>
                )}
              </>
            ) : (
              <p className="text-muted-foreground">No stress test run yet.</p>
            )}
            <Button size="sm" variant="outline" onClick={onGoToStress} className="mt-2">
              Open Stress Tests
            </Button>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-lime-500">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <PiggyBank className="h-4 w-4 text-emerald-600" />
              Goal Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.goals.length === 0 ? (
              <p className="text-sm text-muted-foreground">No goals set yet. Add a savings goal to start tracking progress.</p>
            ) : (
              <div className="space-y-3">
                {data.goals.slice(0, 3).map((goal) => {
                  const progress = goal.target_amount > 0 ? Math.min((goal.current_amount / goal.target_amount) * 100, 100) : 0
                  return (
                    <div key={goal.id} className="space-y-1.5">
                      <div className="flex items-center justify-between gap-2 text-sm">
                        <span className="font-medium">{goal.goal_name}</span>
                        <span className="tabular-nums text-muted-foreground">{progress.toFixed(0)}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-muted">
                        <div className="h-full rounded-full bg-gradient-to-r from-lime-500 to-emerald-500" style={{ width: `${progress}%` }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {data.latest_advice_summary && (
        <section>
          <Card className="overflow-hidden border-emerald-200/60 bg-gradient-to-br from-emerald-50 to-lime-50">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <BadgePoundSterling className="h-4 w-4 text-emerald-700" />
                  Latest Advice Snapshot
                </CardTitle>
                <Button size="sm" variant="outline" className="bg-white" onClick={onGoToAdvice}>
                  Open Assistant <ArrowUpRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-emerald-950/85">{data.latest_advice_summary}</p>
            </CardContent>
          </Card>
        </section>
      )}
    </div>
  )
}
