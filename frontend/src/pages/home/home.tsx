import { Link } from "react-router-dom"
import {
  ArrowRight,
  BarChart3,
  Brain,
  Database,
  MessageSquare,
  Search,
  ShieldCheck,
  Target,
} from "lucide-react"

import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

export function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="flex flex-col items-center justify-center px-6 pt-24 pb-20 text-center">
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-green-500" />
          AI-powered financial planning assistant
        </div>

        <h1 className="mb-6 max-w-4xl text-5xl font-extrabold leading-tight tracking-tight md:text-6xl">
          Understand your money.
          <br />
          <span className="text-green-600">Stress test your future.</span>
        </h1>

        <p className="mb-10 max-w-2xl text-xl text-muted-foreground">
          FinLit combines deterministic simulation, ML-assisted behavior modelling, live-aware currency handling, and RAG-grounded AI guidance in one dashboard.
        </p>

        <div className="flex flex-col gap-4 sm:flex-row">
          <Link to="/signup">
            <Button size="lg" className="px-8 text-base">
              Get Started Free <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Link to="/faq">
            <Button size="lg" variant="outline" className="px-8 text-base">
              See How It Works
            </Button>
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl grid-cols-1 gap-6 px-10 pb-12 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-none bg-slate-50 transition-colors hover:bg-slate-100">
          <CardContent className="pt-6">
            <BarChart3 className="mb-4 h-9 w-9 text-green-600" />
            <h3 className="mb-1 text-base font-bold">Spending Insights</h3>
            <p className="text-sm text-muted-foreground">
              Break spending into categories and compare against 50/30/20 targets.
            </p>
          </CardContent>
        </Card>

        <Card className="border-none bg-slate-50 transition-colors hover:bg-slate-100">
          <CardContent className="pt-6">
            <Target className="mb-4 h-9 w-9 text-green-600" />
            <h3 className="mb-1 text-base font-bold">Goal Tracking</h3>
            <p className="text-sm text-muted-foreground">
              Track progress and understand how close you are to your target milestones.
            </p>
          </CardContent>
        </Card>

        <Card className="border-none bg-slate-50 transition-colors hover:bg-slate-100">
          <CardContent className="pt-6">
            <MessageSquare className="mb-4 h-9 w-9 text-green-600" />
            <h3 className="mb-1 text-base font-bold">AI Chat + Advice</h3>
            <p className="text-sm text-muted-foreground">
              Ask financial questions and get context-aware responses using your profile and history.
            </p>
          </CardContent>
        </Card>

        <Card className="border-none bg-slate-50 transition-colors hover:bg-slate-100">
          <CardContent className="pt-6">
            <ShieldCheck className="mb-4 h-9 w-9 text-green-600" />
            <h3 className="mb-1 text-base font-bold">Stress Tests</h3>
            <p className="text-sm text-muted-foreground">
              Simulate job loss, emergency costs, and income boosts with interpretable score breakdowns.
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="mx-auto max-w-6xl px-10 pb-12">
        <div className="rounded-2xl border bg-card p-6 shadow-sm">
          <h2 className="text-2xl font-bold tracking-tight">Currency + Income Handling</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            FinLit supports multi-currency profiles and net-income-first calculations to keep stress tests consistent.
          </p>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border bg-muted/20 p-4">
            <p className="text-sm font-semibold">Live FX Rates</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Currency conversion tries live providers first and falls back to safe approximate rates if live data is unavailable.
              </p>
            </div>
            <div className="rounded-xl border bg-muted/20 p-4">
              <p className="text-sm font-semibold">Profile-Wide Conversion</p>
              <p className="mt-1 text-xs text-muted-foreground">
                When you change currency, you can convert your full profile values (income, buffer, and all expense fields) in one action.
              </p>
            </div>
            <div className="rounded-xl border bg-muted/20 p-4">
              <p className="text-sm font-semibold">Net Income For Modeling</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Stress simulations use net monthly take-home income. If you only know gross, FinLit provides an estimated net workflow.
            </p>
          </div>
        </div>
      </div>
    </section>

      <section className="mx-auto max-w-6xl px-10 pb-12">
        <div className="rounded-2xl border bg-card p-6 shadow-sm">
          <h2 className="text-2xl font-bold tracking-tight">CSV Import Workflow</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Bank CSV upload now plugs directly into the existing profile form instead of creating a second data source.
          </p>

          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border bg-muted/20 p-4">
              <p className="text-sm font-semibold">Backend Parsing</p>
              <p className="mt-1 text-xs text-muted-foreground">
                The backend detects likely amount, description, and date columns, then classifies rows into your existing expense categories.
              </p>
            </div>
            <div className="rounded-xl border bg-muted/20 p-4">
              <p className="text-sm font-semibold">Preview Before Apply</p>
              <p className="mt-1 text-xs text-muted-foreground">
                You see parsed row counts, warnings, category totals, and sample classified transactions before anything is copied into your profile.
              </p>
            </div>
            <div className="rounded-xl border bg-muted/20 p-4">
              <p className="text-sm font-semibold">Profile Stays Canonical</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Imported totals only prefill the form. You still review and save normally, so the profile remains the single source of truth for dashboard, stress tests, and AI context.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-10 pb-20">
        <div className="rounded-2xl border bg-card p-6 shadow-sm">
          <h2 className="text-2xl font-bold tracking-tight">Under The Hood</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            FinLit combines deterministic finance logic with AI tooling so outputs are explainable and practical.
          </p>

          <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border bg-muted/20 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                <Brain className="h-4 w-4 text-emerald-600" />
                ML Cutback Model
              </div>
              <p className="text-xs text-muted-foreground">
                Job-loss mode can predict a realistic cutback percentage from profile features when not manually set.
              </p>
            </div>

            <div className="rounded-xl border bg-muted/20 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                <Search className="h-4 w-4 text-emerald-600" />
                RAG Pipeline
              </div>
              <p className="text-xs text-muted-foreground">
                Chat/advice retrieves relevant knowledge snippets before generation to improve factual grounding.
              </p>
            </div>

            <div className="rounded-xl border bg-muted/20 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                <Database className="h-4 w-4 text-emerald-600" />
                FAISS Index + CSV Parsing
              </div>
              <p className="text-xs text-muted-foreground">
                Retrieval uses a local FAISS vector index for efficient nearest-neighbor lookup of knowledge chunks, while CSV import uses backend categorisation rules to prefill expense categories safely.
              </p>
            </div>

            <div className="rounded-xl border bg-muted/20 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                Composite Resilience
              </div>
              <p className="text-xs text-muted-foreground">
                Stress scores use survival, buffer, cashflow, and stability, not a single simplistic metric.
              </p>
            </div>
          </div>
        </div>
      </section>

      <div className="border-t bg-slate-50">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-10 py-8 sm:flex-row">
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="font-medium text-foreground underline">
              Log in
            </Link>
          </p>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <Link to="/faq" className="transition-colors hover:text-foreground">FAQ</Link>
            <Link to="/legal" className="transition-colors hover:text-foreground">Legal</Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home
