import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi, beforeEach } from "vitest"

import { Goals } from "@/pages/dashboard/goals"

let goalsState = [
  {
    id: "goal-1",
    goal_name: "Emergency fund",
    target_amount: 5000,
    current_amount: 1250,
    target_date: "2026-12-31",
    status: "active",
  },
]

function makeGetChain(url: string) {
  return {
    notFound() {
      return this
    },
    json(handler: (value: unknown) => void) {
      if (url === "/api/v1/goals") handler(goalsState)
      if (url === "/api/v1/profile") handler({ currency_code: "AED" })
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

function makePostChain(payload: Record<string, unknown>) {
  return {
    json(handler: (value: unknown) => void) {
      const created = {
        id: "goal-2",
        goal_name: payload.goal_name as string,
        target_amount: payload.target_amount as number,
        current_amount: payload.current_amount as number,
        target_date: (payload.target_date as string | undefined) ?? null,
        status: "active",
      }
      goalsState = [...goalsState, created]
      handler(created)
      return this
    },
    catch() {
      return this
    },
    finally() {
      return this
    },
  }
}

function makeDeleteChain(url: string) {
  return {
    json(handler: () => void) {
      const id = url.split("/").pop()
      goalsState = goalsState.filter((goal) => goal.id !== id)
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
    post: (payload: Record<string, unknown>) => makePostChain(payload),
    delete: (url: string) => makeDeleteChain(url),
  },
}))

describe("Goals", () => {
  beforeEach(() => {
    goalsState = [
      {
        id: "goal-1",
        goal_name: "Emergency fund",
        target_amount: 5000,
        current_amount: 1250,
        target_date: "2026-12-31",
        status: "active",
      },
    ]
  })

  it("renders goals using profile currency", async () => {
    render(<Goals />)

    await waitFor(() => expect(screen.getByText(/Emergency fund/i)).toBeInTheDocument())
    expect(screen.getAllByText(/AED/).length).toBeGreaterThan(0)
  })

  it("adds a new goal from the form", async () => {
    const user = userEvent.setup()
    render(<Goals />)

    await waitFor(() => expect(screen.getByRole("button", { name: /Add Goal/i })).toBeInTheDocument())
    await user.click(screen.getByRole("button", { name: /Add Goal/i }))
    await user.type(screen.getByLabelText(/Goal Name/i), "Laptop")
    await user.type(screen.getByLabelText(/Target Amount/i), "1500")
    await user.clear(screen.getByLabelText(/Current Saved/i))
    await user.type(screen.getByLabelText(/Current Saved/i), "200")
    await user.click(screen.getByRole("button", { name: /Save Goal/i }))

    await waitFor(() => expect(screen.getByText(/Laptop/i)).toBeInTheDocument())
  })
})
