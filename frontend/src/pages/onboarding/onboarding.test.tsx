import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi, beforeEach } from "vitest"
import { MemoryRouter } from "react-router-dom"

import { Onboarding } from "@/pages/onboarding/onboarding"

const mockNavigate = vi.fn()
const postCalls: Array<{ url: string; payload: Record<string, unknown> }> = []
const fetchMock = vi.fn()

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>()
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

function makeGetChain(url: string) {
  let notFoundHandler: ((...args: never[]) => unknown) | null = null
  return {
    notFound(handler: (...args: never[]) => unknown) {
      notFoundHandler = handler
      return this
    },
    json(handler: (value: unknown) => void) {
      if (url === "/api/v1/profile") {
        if (notFoundHandler) {
          handler(notFoundHandler() as unknown)
        }
      } else if (url === "/api/v1/fx/rates") {
        handler({
          live: true,
          source: "test-live",
          as_of: "2026-03-13",
          usd_per_currency: { USD: 1, GBP: 1.28, AED: 0.2723 },
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

function makePostChain(url: string, payload: Record<string, unknown>) {
  return {
    json(handler: () => void) {
      postCalls.push({ url, payload })
      handler()
      return this
    },
    catch() {
      return this
    },
  }
}

vi.mock("@/components/api", () => ({
  api: {
    get: (url: string) => makeGetChain(url),
    post: (payload: Record<string, unknown>, url: string) => makePostChain(url, payload),
  },
}))

describe("Onboarding literacy controls", () => {
  beforeEach(() => {
    postCalls.length = 0
    mockNavigate.mockReset()
    fetchMock.mockReset()
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        transactions: [
          {
            date: "2026-03-01",
            description: "Tesco",
            amount: 45.2,
            suggested_category: "groceries",
            confidence: 0.98,
            method: "merchant_map",
          },
        ],
        category_totals: {
          rent: 0,
          bills: 0,
          subscriptions: 0,
          loan_repayments: 0,
          groceries: 45.2,
          transport: 0,
          entertainment: 0,
          eating_out: 0,
          clothing: 0,
          health: 0,
          other: 0,
        },
        warnings: [],
        parsed_count: 1,
      }),
    })
    vi.stubGlobal("fetch", fetchMock)
  })

  it("submits manual literacy score when manual mode is used", async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <Onboarding setLoggedInState={() => {}} />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/Monthly Take-Home Income/i), "2500")
    await user.selectOptions(screen.getByLabelText(/^Explanation Level \(1-5\)$/i), "4")
    await user.click(screen.getAllByRole("button", { name: /Save & Continue/i })[0])

    await waitFor(() => expect(postCalls.length).toBe(1))
    expect(postCalls[0].payload.manual_literacy_score).toBe(4)
    expect(postCalls[0].payload.literacy_answers).toBeNull()
  })

  it("submits literacy answers when quiz mode is used", async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <Onboarding setLoggedInState={() => {}} />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/Monthly Take-Home Income/i), "2500")
    await user.selectOptions(screen.getByLabelText(/How should FinLit set your explanation level/i), "quiz")
    await user.selectOptions(screen.getByLabelText(/budgeting concepts/i), "1")
    await user.selectOptions(screen.getByLabelText(/comparing financial products/i), "2")
    await user.selectOptions(screen.getByLabelText(/interpreting risk, tradeoffs/i), "3")
    await user.click(screen.getAllByRole("button", { name: /Save & Continue/i })[0])

    await waitFor(() => expect(postCalls.length).toBe(1))
    expect(postCalls[0].payload.manual_literacy_score).toBeNull()
    expect(postCalls[0].payload.literacy_answers).toEqual([1, 2, 3])
  })

  it("uploads a CSV and applies imported totals into expense fields", async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <Onboarding setLoggedInState={() => {}} />
      </MemoryRouter>,
    )

    const file = new File(["Date,Description,Amount\n2026-03-01,Tesco,-45.20"], "bank.csv", { type: "text/csv" })
    await user.upload(screen.getByLabelText(/Bank CSV file/i), file)
    await user.click(screen.getByRole("button", { name: /Upload CSV/i }))

    await waitFor(() => expect(screen.getByText(/Sample classified rows/i)).toBeInTheDocument())
    await user.click(screen.getByRole("button", { name: /Apply imported totals to expense fields/i }))

    expect(screen.getByLabelText(/Groceries/i)).toHaveValue(45.2)
    expect(screen.getByText(/Imported category totals have been copied into the expense fields below/i)).toBeInTheDocument()
  })
})
