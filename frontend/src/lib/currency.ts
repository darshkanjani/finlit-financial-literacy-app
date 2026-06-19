export type CurrencyCode = "GBP" | "USD" | "EUR" | "CAD" | "AUD" | "INR" | "JPY" | "AED"

const DEFAULT_CURRENCY: CurrencyCode = "GBP"
const SUPPORTED_CURRENCIES = new Set<CurrencyCode>(["GBP", "USD", "EUR", "CAD", "AUD", "INR", "JPY", "AED"])
export const FX_RATES_AS_OF = "static approx"

// Approximate rates against USD for lightweight client-side conversion.
// These are not live and should be treated as indicative.
const USD_PER_CURRENCY: Record<CurrencyCode, number> = {
  USD: 1,
  GBP: 1.28,
  EUR: 1.09,
  CAD: 0.74,
  AUD: 0.66,
  INR: 0.012,
  JPY: 0.0067,
  AED: 0.2723,
}

export interface FxRatesPayload {
  base: string
  source: string
  as_of: string
  live: boolean
  error?: string | null
  usd_per_currency: Record<string, number>
}

export function normalizeCurrencyCode(value: string | null | undefined): CurrencyCode {
  const code = String(value ?? "").toUpperCase()
  if (SUPPORTED_CURRENCIES.has(code as CurrencyCode)) return code as CurrencyCode
  return DEFAULT_CURRENCY
}

export function listSupportedCurrencies(): CurrencyCode[] {
  return ["GBP", "USD", "EUR", "CAD", "AUD", "INR", "JPY", "AED"]
}

export function formatCurrency(value: number, currencyCode: string | null | undefined): string {
  const code = normalizeCurrencyCode(currencyCode)
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: code,
    maximumFractionDigits: 0,
  }).format(value)
}

export function currencySymbol(currencyCode: string | null | undefined): string {
  const code = normalizeCurrencyCode(currencyCode)
  const parts = new Intl.NumberFormat("en-GB", { style: "currency", currency: code }).formatToParts(0)
  return parts.find((p) => p.type === "currency")?.value ?? code
}

export function convertCurrency(amount: number, fromCode: string | null | undefined, toCode: string | null | undefined): number {
  return convertCurrencyWithRates(amount, fromCode, toCode, undefined)
}

export function convertCurrencyWithRates(
  amount: number,
  fromCode: string | null | undefined,
  toCode: string | null | undefined,
  usdPerCurrency: Record<string, number> | undefined,
): number {
  const from = normalizeCurrencyCode(fromCode)
  const to = normalizeCurrencyCode(toCode)
  if (!Number.isFinite(amount)) return 0
  if (from === to) return amount
  const fromUsd = usdPerCurrency?.[from] ?? USD_PER_CURRENCY[from]
  const toUsd = usdPerCurrency?.[to] ?? USD_PER_CURRENCY[to]
  if (!fromUsd || !toUsd) return amount
  const inUsd = amount * fromUsd
  return inUsd / toUsd
}
