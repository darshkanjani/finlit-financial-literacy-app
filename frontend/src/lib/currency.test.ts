import { describe, expect, it } from "vitest"

import { convertCurrencyWithRates, formatCurrency, normalizeCurrencyCode } from "@/lib/currency"

describe("currency utilities", () => {
  it("normalizes unsupported currencies to GBP", () => {
    expect(normalizeCurrencyCode("zzz")).toBe("GBP")
  })

  it("converts using injected live rates", () => {
    const usdPer = {
      USD: 1,
      GBP: 1.25,
      EUR: 1.1,
      CAD: 0.73,
      AUD: 0.65,
      INR: 0.012,
      JPY: 0.0068,
      AED: 0.2723,
    }
    const converted = convertCurrencyWithRates(100, "GBP", "USD", usdPer)
    expect(converted).toBeCloseTo(125, 5)
  })

  it("formats output in requested currency", () => {
    expect(formatCurrency(1000, "AED")).toContain("AED")
  })
})

