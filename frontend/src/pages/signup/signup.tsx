import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { CheckCircle2, PiggyBank, Sparkles, Target } from "lucide-react"

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

export function Signup({ setLoggedInState }: { setLoggedInState: (value: boolean) => void }) {
  const [fullName, setFullName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const hasSpecialChar = /[/[\]!@(){}|,.?"':;<>^%&*$£]/.test(password)

    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      return
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long")
      return
    }

    if (!hasSpecialChar){
      setError("Password must contain at least one special character")
      return
    }

    setSubmitting(true)

    const hashedPassword = await hash({ text: password })

    api
      .post({ name: fullName, email, password: hashedPassword }, "/api/v1/auth/register")
      .json(() => {
        setLoggedInState(true)
        navigate("/onboarding", { replace: true })
      })
      .catch(() => setError("We couldn't create your account right now. Please try again."))
      .finally(() => setSubmitting(false))
  }

  return (
    <div className="min-h-screen">
      <Navbar />

      <main className="mx-auto grid w-full max-w-6xl grid-cols-1 items-stretch gap-6 px-6 py-8 lg:grid-cols-[1.08fr_0.92fr] lg:py-12">
        <section className="relative overflow-hidden rounded-3xl border border-emerald-900/20 bg-gradient-to-br from-emerald-900 via-emerald-800 to-green-700 p-8 text-emerald-50 shadow-xl lg:p-10">
          <div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-lime-200/20 blur-2xl" />
          <div className="absolute -bottom-20 -left-12 h-44 w-44 rounded-full bg-emerald-200/15 blur-2xl" />

          <div className="relative space-y-8">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.12em]">
                <Sparkles className="h-3.5 w-3.5" />
                Start Your Journey
              </p>
              <h1 className="mt-4 text-3xl font-extrabold leading-tight lg:text-4xl">
                Build stronger money habits from day one.
              </h1>
              <p className="mt-3 max-w-md text-sm text-emerald-50/85 lg:text-base">
                Create your account and get tailored recommendations from your spending profile, goals, and stress scenarios.
              </p>
            </div>

            <ul className="space-y-4 text-sm">
              {[
                { icon: <PiggyBank className="h-4 w-4" />, text: "Set realistic savings goals and track progress" },
                { icon: <Target className="h-4 w-4" />, text: "Plan for milestones like emergency fund or debt payoff" },
                { icon: <CheckCircle2 className="h-4 w-4" />, text: "Get clear weekly actions to improve your finances" },
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
              <CardTitle className="text-2xl">Create your account</CardTitle>
              <CardDescription>Set up your profile in under a minute.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit}>
                <FieldGroup>
                  <Field>
                    <FieldLabel htmlFor="full-name">Full name</FieldLabel>
                    <Input
                      id="full-name"
                      type="text"
                      placeholder="John Doe"
                      required
                      autoComplete="name"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                    />
                  </Field>

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
                    <FieldLabel htmlFor="password">Password</FieldLabel>
                    <Input
                      id="password"
                      type="password"
                      required
                      autoComplete="new-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                    <FieldDescription>Use at least 8 characters.</FieldDescription>
                  </Field>

                  <Field>
                    <FieldLabel htmlFor="confirm-password">Confirm password</FieldLabel>
                    <Input
                      id="confirm-password"
                      type="password"
                      required
                      autoComplete="new-password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                  </Field>

                  {error && (
                    <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                      {error}
                    </div>
                  )}

                  <Field>
                    <Button type="submit" disabled={submitting} className="w-full">
                      {submitting ? "Creating account..." : "Create Account"}
                    </Button>
                    <FieldDescription className="text-center">
                      Already have an account? <Link to="/login">Sign in</Link>
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

export default Signup
