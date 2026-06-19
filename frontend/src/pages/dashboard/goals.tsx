import { useEffect, useState } from "react"
import { Plus, Target, Trash2, CircleDollarSign } from "lucide-react"

import { api } from "@/components/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { currencySymbol, formatCurrency, normalizeCurrencyCode } from "@/lib/currency"

interface Goal {
  id: string
  goal_name: string
  target_amount: number
  current_amount: number
  target_date: string | null
  status: string
}

export function Goals() {
  const [goals, setGoals] = useState<Goal[]>([])
  const [currencyCode, setCurrencyCode] = useState("GBP")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [showForm, setShowForm] = useState(false)
  const [goalName, setGoalName] = useState("")
  const [targetAmount, setTargetAmount] = useState("")
  const [currentAmount, setCurrentAmount] = useState("0")
  const [targetDate, setTargetDate] = useState("")
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const [updatingGoalId, setUpdatingGoalId] = useState<string | null>(null)
  const [addAmount, setAddAmount] = useState("")
  const [updating, setUpdating] = useState(false)

  const loadGoals = () => {
    setLoading(true)
    Promise.all([
      api.get("/api/v1/goals").json((data: Goal[]) => setGoals(data)),
      api
        .get("/api/v1/profile")
        .notFound(() => ({ currency_code: "GBP" }))
        .json((p: { currency_code?: string }) => setCurrencyCode(normalizeCurrencyCode(p.currency_code))),
    ])
      .catch(() => setError("Failed to load goals."))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadGoals()
  }, [])

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setSaving(true)

    const payload: Record<string, unknown> = {
      goal_name: goalName,
      target_amount: parseFloat(targetAmount),
      current_amount: parseFloat(currentAmount || "0"),
    }
    if (targetDate) payload.target_date = targetDate

    api
      .post(payload, "/api/v1/goals")
      .json((g: Goal) => {
        setGoals((prev) => [...prev, g])
        setGoalName("")
        setTargetAmount("")
        setCurrentAmount("0")
        setTargetDate("")
        setShowForm(false)
      })
      .catch(() => setFormError("Failed to add goal. Please try again."))
      .finally(() => setSaving(false))
  }

  const handleDelete = (id: string) => {
    api
      .delete(`/api/v1/goals/${id}`)
      .json(() => setGoals((prev) => prev.filter((g) => g.id !== id)))
      .catch(() => setError("Failed to delete goal."))
  }

  const handleAddFunds = (goal: Goal) => {
    setUpdating(true)

    const amount = parseFloat(addAmount)
    if (Number.isNaN(amount) || amount <= 0) return

    const payload: Record<string, unknown> = {
      goal_name: goal.goal_name,
      target_amount: goal.target_amount,
      current_amount: goal.current_amount + amount,
      target_date: goal.target_date,
    }

    api
      .put(payload, `/api/v1/goals/${goal.id}`)
      .json((updated_g: Goal) => {
        setGoals((prev) => prev.map((g) => (g.id === updated_g.id ? updated_g : g)))
        setAddAmount("")
        setUpdatingGoalId(null)
      })
      .catch(() => setError("Failed to add funds. Please try again."))
      .finally(() => setUpdating(false))
  }

  if (loading) return <p className="p-6 text-sm text-muted-foreground">Loading goals...</p>

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6 px-6 py-6">
      <div className="rounded-2xl border bg-card p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Target className="h-4 w-4 text-emerald-600" />
              Financial Goals
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">Set targets and keep momentum with visible progress bars.</p>
          </div>
          <Button size="sm" onClick={() => setShowForm((v) => !v)}>
            <Plus className="mr-1 h-4 w-4" />
            {showForm ? "Close" : "Add Goal"}
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {showForm && (
        <Card className="border-emerald-200/60">
          <CardHeader>
            <CardTitle className="text-base">New Goal</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAdd}>
              <FieldGroup className="gap-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <Field>
                    <FieldLabel htmlFor="goal-name">Goal Name</FieldLabel>
                    <Input
                      id="goal-name"
                      placeholder="Emergency fund"
                      required
                      value={goalName}
                      onChange={(e) => setGoalName(e.target.value)}
                    />
                  </Field>

                  <Field>
                    <FieldLabel htmlFor="target-amount">Target Amount ({currencySymbol(currencyCode)})</FieldLabel>
                    <Input
                      id="target-amount"
                      type="number"
                      min="1"
                      step="0.01"
                      required
                      value={targetAmount}
                      onChange={(e) => setTargetAmount(e.target.value)}
                    />
                  </Field>

                  <Field>
                    <FieldLabel htmlFor="current-amount">Current Saved ({currencySymbol(currencyCode)})</FieldLabel>
                    <Input
                      id="current-amount"
                      type="number"
                      min="0"
                      step="0.01"
                      value={currentAmount}
                      onChange={(e) => setCurrentAmount(e.target.value)}
                    />
                  </Field>

                  <Field>
                    <FieldLabel htmlFor="target-date">Target Date (optional)</FieldLabel>
                    <Input
                      id="target-date"
                      type="date"
                      value={targetDate}
                      onChange={(e) => setTargetDate(e.target.value)}
                    />
                  </Field>
                </div>

                {formError && (
                  <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{formError}</div>
                )}

                <div className="flex gap-2">
                  <Button type="submit" disabled={saving}>
                    {saving ? "Saving..." : "Save Goal"}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                    Cancel
                  </Button>
                </div>
              </FieldGroup>
            </form>
          </CardContent>
        </Card>
      )}

      {goals.length === 0 ? (
        <div className="rounded-2xl border border-dashed bg-card px-5 py-10 text-center text-sm text-muted-foreground">
          No goals yet. Add one to start tracking progress.
        </div>
      ) : (
        <div className="space-y-3">
          {goals.map((goal) => {
            const progress = goal.target_amount > 0 ? Math.min((goal.current_amount / goal.target_amount) * 100, 100) : 0
            const remaining = Math.max(goal.target_amount - goal.current_amount, 0)

            return (
              <Card key={goal.id} className="overflow-hidden border-emerald-200/50 bg-white/90">
                <CardContent className="pt-5 pb-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1 space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="truncate font-semibold">{goal.goal_name}</p>
                        <span className="rounded-full border px-2 py-0.5 text-[11px] capitalize text-muted-foreground">
                          {goal.status}
                        </span>
                      </div>

                      <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-lime-500 to-emerald-500 transition-all"
                          style={{ width: `${progress}%` }}
                        />
                      </div>

                      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                        <span className="tabular-nums">
                          {formatCurrency(goal.current_amount, currencyCode)} saved • {formatCurrency(remaining, currencyCode)} remaining
                        </span>
                        <span className="tabular-nums">
                          Target {formatCurrency(goal.target_amount, currencyCode)}{goal.target_date ? ` • by ${goal.target_date}` : ""}
                        </span>
                      </div>
                    </div>

                    <div className="flex shrink-0 items-center gap-1">
                      {updatingGoalId === goal.id ? (
                        <div className="flex items-center gap-1">
                          <Input
                            type="number"
                            min="0.01"
                            step="0.01"
                            placeholder="Amount"
                            className="h-7 w-20 text-sm"
                            value={addAmount}
                            onChange={(e) => setAddAmount(e.target.value)}
                          />
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleAddFunds(goal)}
                            disabled={updating || !addAmount}
                            className="h-7 px-2 text-emerald-600 hover:text-emerald-700"
                          >
                            ✓
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setUpdatingGoalId(null)
                              setAddAmount("")
                            }}
                            className="h-7 px-2 text-muted-foreground"
                          >
                            ✕
                          </Button>
                        </div>
                      ) : (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setUpdatingGoalId(goal.id)}
                            className="shrink-0 text-emerald-600 hover:text-emerald-700"
                            title="Add funds"
                          >
                            <CircleDollarSign className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(goal.id)}
                            className="shrink-0 text-muted-foreground hover:text-red-600"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
