import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Database, ShieldCheck, Sparkles, Workflow } from "lucide-react"

import { Navbar } from "@/components/navbar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const questions = [
  {
    value: "what-finlit-does",
    trigger: "What does FinLit actually do?",
    content:
      "FinLit helps you understand your current finances using your profile inputs, spending categories, goals, stress tests, and AI guidance. It is designed for financial education and planning support, not regulated investment advice.",
  },
  {
    value: "stress-score",
    trigger: "How is the stress-test score calculated?",
    content:
      "Each scenario uses month-by-month simulation. The resilience score is a /10 composite: 40% survival, 30% end-buffer strength, 20% cashflow health, and 10% stability. The Summary page averages your latest run for job loss, emergency expense, and promotion.",
  },
  {
    value: "job-loss-ml",
    trigger: "Where is machine learning used?",
    content:
      "ML is currently used in job-loss simulations to estimate an achievable cutback percentage when one is not manually provided. That estimate is based on profile-level features (for example needs/wants mix, debt ratio, and context fields). If a model is unavailable, the app falls back to deterministic rules.",
  },
  {
    value: "rag-faiss",
    trigger: "How do RAG and FAISS fit into chat/advice?",
    content:
      "FinLit uses Retrieval-Augmented Generation (RAG): before generating a response, it retrieves relevant knowledge snippets from a local vector index built with FAISS. Those snippets are used as supporting context so responses are grounded in known financial guidance rather than pure free-form generation.",
  },
  {
    value: "chat-persistence",
    trigger: "Does chat context persist across sessions?",
    content:
      "Yes. Chat history is stored per logged-in user and loaded when you revisit the chat tab. You can clear it using the Clear Chat action.",
  },
  {
    value: "advice-persistence",
    trigger: "Is advice history saved?",
    content:
      "Yes. Generated advice entries are saved and shown in history. You can clear saved advice using the Clear Advice action.",
  },
  {
    value: "data-input",
    trigger: "How do I provide financial data?",
    content:
      "FinLit works from profile fields (income, expenses, buffer, context) and related features in the app. You can now upload a bank CSV in onboarding/profile to prefill expense categories, review parser warnings, and then apply those totals into the profile form before saving.",
  },
  {
    value: "csv-confidence",
    trigger: "How does CSV import confidence work?",
    content:
      "CSV classification is currently rule-based, not ML probability scoring. FinLit checks known merchants first, then phrase rules, then token rules, then a fallback to 'other'. Confidence reflects how strong that match was, so a known merchant match is treated as more trustworthy than a broad fallback guess.",
  },
  {
    value: "currency-handling",
    trigger: "How does multi-currency support work?",
    content:
      "You can select your account currency in the Profile form. Amounts across Summary, Stress Tests, and Goals are displayed in that currency. If you switch currency after entering data, FinLit can convert your full saved profile values to the new currency in one action.",
  },
  {
    value: "fx-live-fallback",
    trigger: "Are currency rates live?",
    content:
      "FinLit attempts live exchange-rate providers and caches results. If live rates are unavailable, it uses fallback approximate rates and shows that status in the UI. Converted values are planning aids and may differ from bank/card settlement rates and fees.",
  },
  {
    value: "gross-net-tax",
    trigger: "Do calculations use gross income or net income?",
    content:
      "Core calculations use net monthly take-home income. If you only know gross pay, the profile form can estimate net monthly income using region-specific tax approximations. You can also set a manual net override.",
  },
  {
    value: "security",
    trigger: "How is my data handled?",
    content:
      "Your data is scoped to your account and used to power your dashboards, stress simulations, and AI outputs. FinLit is an educational platform and should not be treated as a bank-grade custody service for sensitive external credentials.",
  },
  {
    value: "legal-advice",
    trigger: "Is this financial advice?",
    content:
      "No. Outputs are informational and educational only. They are not a personal recommendation under regulated financial-advice frameworks. Use qualified professionals for legally regulated advice.",
  },
]

export function FAQ() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="mx-auto w-full max-w-6xl px-6 py-10">
        <div className="rounded-2xl border bg-card p-6 shadow-sm">
          <h1 className="text-3xl font-bold tracking-tight">Frequently Asked Questions</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Practical answers on how FinLit works, what the scores mean, and where ML/RAG are used.
          </p>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <Card className="border-emerald-200/70 bg-white/90">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Workflow className="h-4 w-4 text-emerald-600" />
                Stress Engine
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              Month-by-month simulation with composite scoring and scenario-specific assumptions.
            </CardContent>
          </Card>

          <Card className="border-emerald-200/70 bg-white/90">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Sparkles className="h-4 w-4 text-emerald-600" />
                AI + RAG
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              Responses are generated with retrieved context snippets to improve grounding and consistency.
            </CardContent>
          </Card>

          <Card className="border-emerald-200/70 bg-white/90">
            <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Database className="h-4 w-4 text-emerald-600" />
                Data + Currency
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              Chat/advice history are account-scoped and clearable. Currency preferences, profile conversion status, and CSV import suggestions are tied back to the same account-level profile flow.
            </CardContent>
          </Card>
        </div>

        <div className="mt-6 rounded-2xl border bg-card p-4 shadow-sm">
          <Accordion type="single" collapsible className="w-full">
            {questions.map((question) => (
              <AccordionItem key={question.value} value={question.value}>
                <AccordionTrigger className="text-left font-medium">{question.trigger}</AccordionTrigger>
                <AccordionContent className="leading-relaxed text-muted-foreground">{question.content}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>

        <p className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5" />
          For legal boundaries and disclosures, see the Legal page.
        </p>
      </section>
    </div>
  )
}

export default FAQ
