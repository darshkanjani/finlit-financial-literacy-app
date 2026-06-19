import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { Summary } from "@/pages/dashboard/summary"

function makeGetChain(url: string) {
  return {
    json(handler: (value: unknown) => void) {
      if (url === "/api/v1/dashboard") {
        handler({
          currency_code: "AED",
          profile_monthly_income: 5000,
          spending_breakdown: {
            categories: [
              { name: "Rent", amount: 2000, percentage: 40, type: "need" },
              { name: "Bills", amount: 500, percentage: 10, type: "need" },
            ],
            summary: {
              needs_percent: 50,
              wants_percent: 10,
              savings_percent: 40,
              target: { needs: 50, wants: 30, savings: 20 },
            },
            flags: [],
          },
          resilience: { overall_score: 7.2, rating: "strong", weakest_scenario: "job_loss" },
          goals: [],
          latest_advice_summary: null,
          has_completed_profile: true,
          has_run_stress_test: true,
          has_set_goals: false,
        })
      }
      if (url.startsWith("/api/v1/fx/rates")) {
        handler({
          base: "USD",
          source: "fallback-static",
          as_of: "2026-03-13",
          live: false,
          error: "Live FX fetch failed; using fallback rates.",
          usd_per_currency: { USD: 1, AED: 0.2723, GBP: 1.28 },
        })
      }
      return this
    },
    catch() {
      return this
    },
    finally(handler: () => void) {
      handler()
      return this
    },
  }
}

vi.mock("@/components/api", () => ({
  api: {
    get: (url: string) => makeGetChain(url),
  },
}))

describe("Summary", () => {
  it("renders currency and fx fallback information", async () => {
    render(
      <Summary
        onGoToProfile={() => {}}
        onGoToAdvice={() => {}}
        onGoToStress={() => {}}
      />,
    )

    await waitFor(() => expect(screen.getByText(/Currency Converter/i)).toBeInTheDocument())
    expect(screen.getByText(/Rates: 2026-03-13 \(fallback\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Source: fallback-static/i)).toBeInTheDocument()
    expect(screen.getByText(/Live FX fetch failed; using fallback rates./i)).toBeInTheDocument()
  })
})

