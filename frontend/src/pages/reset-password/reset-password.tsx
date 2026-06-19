import { useNavigate } from "react-router-dom"
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
import { hash } from "@/components/hash"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Navbar } from "@/components/navbar"

export function ResetPassword() {
  // Token is passed as ?token=... in the URL from the email link
  const token = new URLSearchParams(window.location.search).get("token") ?? ""

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
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

    if (!token) {
      setError("Invalid or missing reset token. Please request a new reset link.")
      return
    }

    setIsLoading(true)
    const hashedPassword = await hash({ text: password })

    api.post({ email, newpassword: hashedPassword, token }, "/api/v1/auth/reset-password")
      .error(401, () => setError("Reset link has expired or is invalid. Please request a new one."))
      .json(() => {
        navigate("/login", { replace: true })
      })
      .catch(() => setError("An error occurred. Please try again."))
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
              <CardTitle>Reset Your Password</CardTitle>
              <CardDescription>
                Enter your email and choose a new password
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
                      required
                      autoComplete="email"
                      placeholder="m@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={isLoading}
                    />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="password">New Password</FieldLabel>
                    <Input
                      id="password"
                      type="password"
                      required
                      autoComplete="new-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={isLoading}
                    />
                    <FieldDescription>Must be at least 8 characters long.</FieldDescription>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="confirm-password">Confirm Password</FieldLabel>
                    <Input
                      id="confirm-password"
                      type="password"
                      required
                      autoComplete="new-password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={isLoading}
                    />
                  </Field>

                  {error && (
                    <div className="rounded-md bg-red-50 p-3 border border-red-200">
                      <p className="text-sm font-medium text-red-800">{error}</p>
                    </div>
                  )}

                  <Field>
                    <Button type="submit" disabled={isLoading} className="w-full">
                      {isLoading ? "Resetting..." : "Reset Password"}
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

export default ResetPassword
