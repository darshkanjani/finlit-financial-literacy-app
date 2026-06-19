import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { CheckCircle2, ShieldCheck, Sparkles, TrendingUp } from "lucide-react"

import { api } from "@/components/api"
import { hash } from "@/components/hash"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"

export function Login({ setLoggedInState }: { setLoggedInState: (value: boolean) => void }) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    const hashedPassword = await hash({ text: password })

    api
      .post({ email, password: hashedPassword }, "/api/v1/auth/login")
      .unauthorized(() => setError("Invalid email or password."))
      .json(() => {
        setLoggedInState(true)
        navigate("/dashboard", { replace: true })
      })
      .catch(() => setError("We couldn't sign you in right now. Please try again."))
      .finally(() => setSubmitting(false))
  }

  return (
    <div className="min-h-screen">
      <Navbar />

      <main className="mx-auto grid w-full max-w-6xl grid-cols-1 items-stretch gap-6 px-6 py-8 lg:grid-cols-[1.08fr_0.92fr] lg:py-12">
        <section className="relative overflow-hidden rounded-3xl border border-emerald-900/20 bg-gradient-to-br from-emerald-800 via-emerald-700 to-emerald-600 p-8 text-emerald-50 shadow-xl lg:p-10">
          <div className="absolute -right-14 -top-14 h-44 w-44 rounded-full bg-emerald-300/20 blur-2xl" />
          <div className="absolute -bottom-16 -left-10 h-40 w-40 rounded-full bg-lime-200/20 blur-2xl" />

          <div className="relative space-y-8">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.12em]">
                <Sparkles className="h-3.5 w-3.5" />
                Financial Clarity Platform
              </p>
              <h1 className="mt-4 text-3xl font-extrabold leading-tight lg:text-4xl">
                Understand your money in one place.
              </h1>
              <p className="mt-3 max-w-md text-sm text-emerald-50/85 lg:text-base">
                Track spending, test tough scenarios, and get practical guidance grounded in your real numbers.
              </p>
            </div>

            <ul className="space-y-4 text-sm">
              {[
                { icon: <TrendingUp className="h-4 w-4" />, text: "Live breakdown of needs, wants, and savings" },
                { icon: <ShieldCheck className="h-4 w-4" />, text: "Stress tests for job loss and emergency costs" },
                { icon: <CheckCircle2 className="h-4 w-4" />, text: "Actionable AI advice with confidence scoring" },
              ].map((item) => (
                <li key={item.text} className="flex items-start gap-3 rounded-xl border border-white/20 bg-white/10 px-3 py-3">
                  <span className="mt-0.5 rounded-md bg-white/15 p-1.5">{item.icon}</span>
                  <span>{item.text}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="flex items-center">
          <Card className="w-full border-white/80 bg-white/90 shadow-lg backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-2xl">Welcome back</CardTitle>
              <CardDescription>Sign in to continue to your dashboard.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit}>
                <FieldGroup>
                  <Field>
                    <FieldLabel htmlFor="email">Email</FieldLabel>
                    <Input
                      id="email"
                      type="email"
                      placeholder="m@example.com"
                      required
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </Field>

                  <Field>
                    <div className="flex items-center justify-between gap-3">
                      <FieldLabel htmlFor="password">Password</FieldLabel>
                      <Link
                        to="/forgot-password"
                        className="text-xs text-muted-foreground underline-offset-4 hover:underline"
                      >
                        Forgot password?
                      </Link>
                    </div>
                    <Input
                      id="password"
                      type="password"
                      required
                      autoComplete="current-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </Field>

                  {error && (
                    <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                      {error}
                    </div>
                  )}

                  <Field>
                    <Button type="submit" disabled={submitting} className="w-full">
                      {submitting ? "Signing in..." : "Log In"}
                    </Button>
                    <FieldDescription className="text-center">
                      Don&apos;t have an account? <Link to="/signup">Sign up</Link>
                    </FieldDescription>
                  </Field>
                </FieldGroup>
              </form>
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  )
}

export default Login
