import { AlertTriangle, FileText, Scale, ShieldCheck } from "lucide-react"

import { Navbar } from "@/components/navbar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const sections = [
  {
    title: "Educational Use Only",
    body: "FinLit provides educational and informational outputs. It does not provide regulated financial advice, investment recommendations, or tax/legal advice.",
  },
  {
    title: "Model And Data Limitations",
    body: "Outputs are generated from user-provided data, deterministic simulation logic, currency conversion logic, and AI models. If your inputs are incomplete or outdated, outputs may be inaccurate.",
  },
  {
    title: "Stress Test Interpretation",
    body: "Stress-test scores are scenario-model outputs, not guarantees. They estimate resilience under configured assumptions and should be treated as planning aids.",
  },
  {
    title: "AI, RAG, And Knowledge Sources",
    body: "Chat and advice may use retrieval-augmented generation (RAG) with a local FAISS index. Retrieved snippets provide context, but generated responses can still contain errors.",
  },
  {
    title: "Currency Conversion Scope",
    body: "Currency conversion uses live exchange-rate providers where available and fallback approximate rates when not. Converted outputs are indicative planning values and do not include bank spreads, card fees, or execution-time slippage.",
  },
  {
    title: "Gross-To-Net Estimation Scope",
    body: "When users enter gross pay, FinLit can estimate net monthly income using simplified regional tax assumptions. These estimates may exclude user-specific tax details and should not be used as formal tax advice.",
  },
  {
    title: "Data Handling",
    body: "Account data is used to render dashboards and support analysis features. Chat and advice histories are persisted per account and can be cleared from the interface. CSV uploads are used to generate suggested category totals and an audit record; they do not silently overwrite profile values.",
  },
  {
    title: "CSV Import Limitations",
    body: "CSV categorisation currently uses rule-based merchant and text matching with confidence indicators. Imported categories are suggestions for review, not guaranteed classifications, and users remain responsible for checking applied totals before saving their profile.",
  },
  {
    title: "User Responsibility",
    body: "You remain responsible for financial decisions. For regulated advice, major investment decisions, or legal/tax determinations, consult qualified professionals.",
  },
]

export function Legal() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="mx-auto w-full max-w-6xl px-6 py-10">
        <div className="rounded-2xl border bg-card p-6 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Legal</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Terms, Scope, And Disclosures</h1>
          <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
            This page outlines what FinLit is designed to do, what it is not designed to do, and how technical outputs should be interpreted.
          </p>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <Card className="border-emerald-200/70 bg-white/90">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Scale className="h-4 w-4 text-emerald-600" />
                Not Regulated Advice
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              FinLit supports planning and literacy. It does not replace licensed financial advisory services.
            </CardContent>
          </Card>

          <Card className="border-emerald-200/70 bg-white/90">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <FileText className="h-4 w-4 text-emerald-600" />
                Scenario Outputs
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              Stress-test results are model-based estimates under explicit assumptions, not promises of future outcomes.
            </CardContent>
          </Card>

          <Card className="border-emerald-200/70 bg-white/90">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                Account Data Controls
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              You can clear stored chat and advice history directly from the dashboard.
            </CardContent>
          </Card>
        </div>

        <div className="mt-6 space-y-4">
          {sections.map((section) => (
            <Card key={section.title} className="bg-card/95">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{section.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed text-muted-foreground">{section.body}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <p className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4" />
            If you are making high-impact financial decisions, use FinLit as a decision-support tool and seek independent regulated advice.
          </p>
        </div>
      </section>
    </div>
  )
}

export default Legal
