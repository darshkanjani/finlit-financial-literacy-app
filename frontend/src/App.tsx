import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { useState, useEffect } from "react"

import { api } from "@/components/api"
import { Dashboard } from "@/pages/dashboard/dashboard"
import { FAQ } from "@/pages/faq/faq"
import { ForgotPassword } from "@/pages/forgot-password/forgot-password"
import { Home } from "@/pages/home/home"
import { Legal } from "@/pages/legal/legal"
import { Login } from "@/pages/login/login"
import { Onboarding } from "@/pages/onboarding/onboarding"
import { ProtectedRoute } from "@/components/protected"
import { ResetPassword } from "@/pages/reset-password/reset-password"
import { Signup } from "@/pages/signup/signup"

export function App() {
  const [loggedIn, setLoggedIn] = useState(false)
  const [authChecked, setAuthChecked] = useState(false)

  useEffect(() => {
    api.get("/api/v1/auth/me")
      .json(() => setLoggedIn(true))
      .catch(() => setLoggedIn(false))
      .finally(() => setAuthChecked(true))
  }, [])

  if (!authChecked) return null

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/faq" element={<FAQ />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/legal" element={<Legal />} />
        <Route path="/login" element={<Login setLoggedInState={setLoggedIn} />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/signup" element={<Signup setLoggedInState={setLoggedIn} />} />
        <Route path="/dashboard" element={
          <ProtectedRoute isLoggedIn={loggedIn}>
            <Dashboard setLoggedInState={setLoggedIn} />
          </ProtectedRoute>
        } />
        <Route path="/onboarding" element={
          <ProtectedRoute isLoggedIn={loggedIn}>
            <Onboarding setLoggedInState={setLoggedIn} />
          </ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
