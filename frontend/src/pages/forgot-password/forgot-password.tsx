import { useState } from "react"

import { api } from "@/components/api"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Field,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Navbar } from "@/components/navbar"

export function ForgotPassword() {
  const [email, setEmail] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage(null)
    setIsLoading(true)

    // Backend constructs the email link as: `{link}/reset-password?token=TOKEN`
    // So we send our origin (e.g. http://localhost:5173)
    api.post({ email, link: window.location.origin }, "/api/v1/auth/forgot-password")
      .error(400, () => setMessage({ type: "error", text: "No account found with that email address." }))
      .json(() => {
        setMessage({ type: "success", text: "Check your email for a password reset link" })
        setEmail("")
      })
      .catch(() => setMessage({ type: "error", text: "An error occurred. Please check your connection and try again." }))
      .finally(() => setIsLoading(false))
  }

  return (
    <div className="flex flex-col h-screen">
      <div>
        <Navbar />
      </div>
      <div className="flex flex-1 items-center justify-center">
        <div className="w-full max-w-sm">
          <Card>
            <CardHeader>
              <CardTitle>Forgot Password</CardTitle>
              <CardDescription>
                Enter your email below and we will send you a link to reset your password
              </CardDescription>
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
                      disabled={isLoading}
                    />
                  </Field>

                  {message?.type === "success" && (
                    <div className="rounded-md bg-green-50 p-3 border border-green-200">
                      <p className="text-sm font-medium text-green-800">{message.text}</p>
                    </div>
                  )}

                  {message?.type === "error" && (
                    <div className="rounded-md bg-red-50 p-3 border border-red-200">
                      <p className="text-sm font-medium text-red-800">{message.text}</p>
                    </div>
                  )}

                  <Field>
                    <Button type="submit" disabled={isLoading} className="w-full">
                      {isLoading ? "Sending..." : "Send Reset Link"}
                    </Button>
                  </Field>
                </FieldGroup>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default ForgotPassword
