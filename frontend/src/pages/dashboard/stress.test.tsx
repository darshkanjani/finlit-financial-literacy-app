import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { StressTest } from "@/pages/dashboard/stress"

function makeGetChain(url: string) {
  return {
    json(handler: (value: unknown) => void) {
      if (url === "/api/v1/stress-test/history") {
        handler([
          {
            id: "stress-1",
            scenario_type: "job_loss",
            params: {
              score_breakdown: { survival: 3.2, buffer: 2.1, cashflow: 1.5, stability: 7.0 },
              score_meta: { end_buffer: -500, target_buffer: 5400, avg_net: -300, net_volatility: 50 },
            },
            monthly_projections: [
              { month: 1, income: 0, expenses: 1950, savings_remaining: 250, net: -1950 },
              { month: 2, income: 0, expenses: 1600, savings_remaining: -1350, net: -1600 },
            ],
            months_until_broke: 1,
            month_broke: 2,
            resilience_score: 3.8,
            created_at: "2026-03-13T12:00:00Z",
          },
        ])
      }
      if (url === "/api/v1/profile") {
        handler({ monthly_income: 3000, currency_code: "GBP" })
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

describe("StressTest", () => {
  it("renders stress score explanation and scenario breakdown", async () => {
    render(<StressTest />)

    await waitFor(() => expect(screen.getByText(/Financial Stress Tests/i)).toBeInTheDocument())
    expect(screen.getByText(/40% survival \+ 30% end-buffer \+ 20% cashflow \+ 10% stability/i)).toBeInTheDocument()
    expect(screen.getByText(/How this score was built for this scenario:/i)).toBeInTheDocument()
    expect(screen.getByText(/Job Loss/i)).toBeInTheDocument()
    expect(screen.getByText(/Months until broke/i)).toBeInTheDocument()
    expect(screen.getByText(/End buffer:/i)).toBeInTheDocument()
  })
})
