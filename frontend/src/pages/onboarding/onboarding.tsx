import { useNavigate } from "react-router-dom"
import { useEffect, useMemo, useState } from "react"

import { api } from "@/components/api"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Field,
  FieldDescription,
  FieldLabel,
  FieldGroup,
  FieldSet,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Navbar } from "@/components/navbar"
import { convertCurrencyWithRates, currencySymbol, normalizeCurrencyCode, type FxRatesPayload } from "@/lib/currency"

interface OnboardingProps {
  setLoggedInState: (value: boolean) => void
  /** If provided, called after a successful save instead of navigating to /dashboard */
  onSaved?: () => void
}

const MAX_MONETARY_FIELD = 1_000_000

interface ProfileResponse {
  monthly_income: number
  currency_code?: string
  literacy_score: number
  age_band: string | null
  employment_status: string | null
  occupation_category: string | null
  dependents_count: number
  savings_buffer: number
  rent: number
  bills: number
  subscriptions: number
  loan_repayments: number
  groceries: number
  transport: number
  entertainment: number
  eating_out: number
  clothing: number
  health: number
  other: number
}

interface CsvTransactionPreview {
  date: string | null
  description: string
  amount: number
  suggested_category: string | null
  confidence: number | null
  method: string | null
}

interface CsvUploadResponse {
  transactions: CsvTransactionPreview[]
  category_totals: Record<string, number>
  warnings: string[]
  parsed_count: number
}

const LITERACY_QUESTIONS = [
  {
    id: "budgeting",
    prompt: "How comfortable are you with budgeting concepts like 50/30/20, savings rate, or monthly cashflow?",
  },
  {
    id: "products",
    prompt: "How comfortable are you comparing financial products like savings accounts, credit cards, or loans?",
  },
  {
    id: "risk",
    prompt: "How comfortable are you interpreting risk, tradeoffs, and scenario-based financial planning?",
  },
]

function toInputValue(value: number | null | undefined): string {
  if (value === null || value === undefined) return "0"
  return String(value)
}

function annualIncomeTaxUk(annualGross: number) {
  const taxable = Math.max(0, annualGross)
  const personalAllowance = 12_570
  const basicRateLimit = 50_270
  const higherRateLimit = 125_140

  let tax = 0
  if (taxable > personalAllowance) {
    const basicBand = Math.min(taxable, basicRateLimit) - personalAllowance
    tax += Math.max(0, basicBand) * 0.2
  }
  if (taxable > basicRateLimit) {
    const higherBand = Math.min(taxable, higherRateLimit) - basicRateLimit
    tax += Math.max(0, higherBand) * 0.4
  }
  if (taxable > higherRateLimit) {
    tax += (taxable - higherRateLimit) * 0.45
  }
  return tax
}

function annualNationalInsuranceUk(annualGross: number) {
  const lower = 12_570
  const upper = 50_270
  const taxable = Math.max(0, annualGross)
  const mainBand = Math.max(0, Math.min(taxable, upper) - lower)
  const upperBand = Math.max(0, taxable - upper)
  return (mainBand * 0.08) + (upperBand * 0.02)
}

function annualFederalTaxUs(annualGross: number) {
  // Approximation: federal single filer + standard deduction, excluding state tax.
  const standardDeduction = 14_600
  let taxable = Math.max(0, annualGross - standardDeduction)
  const brackets: Array<[number, number]> = [
    [11_600, 0.10],
    [47_150, 0.12],
    [100_525, 0.22],
    [191_950, 0.24],
    [243_725, 0.32],
    [609_350, 0.35],
    [Infinity, 0.37],
  ]

  let tax = 0
  let lower = 0
  for (const [upper, rate] of brackets) {
    if (taxable <= 0) break
    const band = Math.min(taxable, upper - lower)
    tax += band * rate
    taxable -= band
    lower = upper
  }
  return tax
}

function annualFicaUs(annualGross: number) {
  const socialSecurityWageBase = 168_600
  const socialSecurity = Math.min(annualGross, socialSecurityWageBase) * 0.062
  const medicare = annualGross * 0.0145
  return socialSecurity + medicare
}

function estimateMonthlyNetFromAnnualGross(annualGross: number, taxRegion: "uk" | "us") {
  const gross = Math.max(0, annualGross)
  const tax = taxRegion === "us"
    ? annualFederalTaxUs(gross) + annualFicaUs(gross)
    : annualIncomeTaxUk(gross) + annualNationalInsuranceUk(gross)
  const annualNet = Math.max(0, gross - tax)
  return annualNet / 12
}

function toAnnualGross(amount: number, frequency: "monthly" | "annual" | "weekly" | "biweekly") {
  switch (frequency) {
    case "annual":
      return amount
    case "weekly":
      return amount * 52
    case "biweekly":
      return amount * 26
    case "monthly":
    default:
      return amount * 12
  }
}

export function Onboarding({ setLoggedInState, onSaved }: OnboardingProps) {
  const navigate = useNavigate()

  // Income & context
  const [monthlyIncome, setMonthlyIncome] = useState("")
  const [currencyCode, setCurrencyCode] = useState("GBP")
  const [amountsCurrencyCode, setAmountsCurrencyCode] = useState("GBP")
  const [hasExistingProfile, setHasExistingProfile] = useState(false)
  const [manualCurrencyUpdateConfirmed, setManualCurrencyUpdateConfirmed] = useState(false)
  const [fxRates, setFxRates] = useState<FxRatesPayload | null>(null)
  const [incomeInputMode, setIncomeInputMode] = useState<"net" | "gross">("net")
  const [grossPayAmount, setGrossPayAmount] = useState("")
  const [grossPayFrequency, setGrossPayFrequency] = useState<"monthly" | "annual" | "weekly" | "biweekly">("annual")
  const [taxRegion, setTaxRegion] = useState<"uk" | "us">("uk")
  const [useRecentNetAverage, setUseRecentNetAverage] = useState(false)
  const [averageWindow, setAverageWindow] = useState<3 | 6 | 12>(3)
  const [recentNetMonths, setRecentNetMonths] = useState<string[]>(["", "", ""])
  const [manualNetOverride, setManualNetOverride] = useState("")
  const [literacyMode, setLiteracyMode] = useState<"manual" | "quiz">("manual")
  const [manualLiteracyScore, setManualLiteracyScore] = useState("3")
  const [literacyAnswers, setLiteracyAnswers] = useState<string[]>(["3", "3", "3"])
  const [ageBand, setAgeBand] = useState("")
  const [employmentStatus, setEmploymentStatus] = useState("")
  const [occupationCategory, setOccupationCategory] = useState("")
  const [dependentsCount, setDependentsCount] = useState("0")
  const [savingsBuffer, setSavingsBuffer] = useState("0")

  // Fixed expenses
  const [rent, setRent] = useState("0")
  const [bills, setBills] = useState("0")
  const [subscriptions, setSubscriptions] = useState("0")
  const [loanRepayments, setLoanRepayments] = useState("0")

  // Variable expenses
  const [groceries, setGroceries] = useState("0")
  const [transport, setTransport] = useState("0")
  const [entertainment, setEntertainment] = useState("0")
  const [eatingOut, setEatingOut] = useState("0")
  const [clothing, setClothing] = useState("0")
  const [health, setHealth] = useState("0")
  const [other, setOther] = useState("0")

  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [prefillLoading, setPrefillLoading] = useState(true)
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [csvImportLoading, setCsvImportLoading] = useState(false)
  const [csvImportError, setCsvImportError] = useState<string | null>(null)
  const [csvImportResult, setCsvImportResult] = useState<CsvUploadResponse | null>(null)
  const [csvAppliedNotice, setCsvAppliedNotice] = useState<string | null>(null)

  const grossAmountNum = Number.parseFloat(grossPayAmount)
  const manualNetOverrideNum = Number.parseFloat(manualNetOverride)

  useEffect(() => {
    setRecentNetMonths((prev) => {
      if (prev.length === averageWindow) return prev
      if (prev.length > averageWindow) return prev.slice(0, averageWindow)
      return [...prev, ...Array.from({ length: averageWindow - prev.length }, () => "")]
    })
  }, [averageWindow])

  const estimatedMonthlyNet = useMemo(() => {
    if (!Number.isFinite(grossAmountNum) || grossAmountNum <= 0) return 0
    const annualGross = toAnnualGross(grossAmountNum, grossPayFrequency)
    return estimateMonthlyNetFromAnnualGross(annualGross, taxRegion)
  }, [grossAmountNum, grossPayFrequency, taxRegion])

  const recentNetAverage = useMemo(() => {
    const values = recentNetMonths
      .map((value) => Number.parseFloat(value))
      .filter((value) => Number.isFinite(value) && value >= 0)
    if (!values.length) return 0
    return values.reduce((sum, value) => sum + value, 0) / values.length
  }, [recentNetMonths])

  const estimatedLiteracyScore = useMemo(() => {
    const values = literacyAnswers
      .map((value) => Number.parseInt(value, 10))
      .filter((value) => Number.isFinite(value) && value >= 1 && value <= 5)
    if (!values.length) return 3
    return Math.round(values.reduce((sum, value) => sum + value, 0) / values.length)
  }, [literacyAnswers])

  const finalGrossModeNet = useMemo(() => {
    const baseFromGross = useRecentNetAverage && recentNetAverage > 0 ? recentNetAverage : estimatedMonthlyNet
    if (Number.isFinite(manualNetOverrideNum) && manualNetOverrideNum > 0) return manualNetOverrideNum
    return baseFromGross
  }, [estimatedMonthlyNet, manualNetOverrideNum, recentNetAverage, useRecentNetAverage])

  useEffect(() => {
    api
      .get("/api/v1/profile")
      .notFound(() => null)
      .json((profile: ProfileResponse) => {
        if (!profile) return

        const normalizedCurrency = normalizeCurrencyCode(profile.currency_code)
        setHasExistingProfile(true)
        setMonthlyIncome(toInputValue(profile.monthly_income))
        setCurrencyCode(normalizedCurrency)
        setAmountsCurrencyCode(normalizedCurrency)
        setManualLiteracyScore(String(profile.literacy_score ?? 3))
        setLiteracyAnswers(Array.from({ length: LITERACY_QUESTIONS.length }, () => String(profile.literacy_score ?? 3)))
        setAgeBand(profile.age_band ?? "")
        setEmploymentStatus(profile.employment_status ?? "")
        setOccupationCategory(profile.occupation_category ?? "")
        setDependentsCount(toInputValue(profile.dependents_count))
        setSavingsBuffer(toInputValue(profile.savings_buffer))

        setRent(toInputValue(profile.rent))
        setBills(toInputValue(profile.bills))
        setSubscriptions(toInputValue(profile.subscriptions))
        setLoanRepayments(toInputValue(profile.loan_repayments))

        setGroceries(toInputValue(profile.groceries))
        setTransport(toInputValue(profile.transport))
        setEntertainment(toInputValue(profile.entertainment))
        setEatingOut(toInputValue(profile.eating_out))
        setClothing(toInputValue(profile.clothing))
        setHealth(toInputValue(profile.health))
        setOther(toInputValue(profile.other))
      })
      .catch(() => {
        // Ignore fetch failures here so new users can still complete onboarding.
      })
      .finally(() => setPrefillLoading(false))

    api
      .get("/api/v1/fx/rates")
      .json((rates: FxRatesPayload) => {
        setFxRates(rates)
        if (!rates.live) {
          api
            .get("/api/v1/fx/rates?force_refresh=true")
            .json((fresh: FxRatesPayload) => setFxRates(fresh))
            .catch(() => {})
        }
      })
      .catch(() => setFxRates(null))
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    if (hasExistingProfile && currencyCode !== amountsCurrencyCode && !manualCurrencyUpdateConfirmed) {
      setError(
        `Your amounts are still in ${amountsCurrencyCode}. Convert all values to ${currencyCode} or confirm you already updated them manually.`
      )
      return
    }

    const netIncomeFromField = parseFloat(monthlyIncome)
    const incomeNum = incomeInputMode === "gross" ? finalGrossModeNet : netIncomeFromField
    const expenseEntries = [
      ["rent", parseFloat(rent)],
      ["bills", parseFloat(bills)],
      ["subscriptions", parseFloat(subscriptions)],
      ["loan_repayments", parseFloat(loanRepayments)],
      ["groceries", parseFloat(groceries)],
      ["transport", parseFloat(transport)],
      ["entertainment", parseFloat(entertainment)],
      ["eating_out", parseFloat(eatingOut)],
      ["clothing", parseFloat(clothing)],
      ["health", parseFloat(health)],
      ["other", parseFloat(other)],
    ] as const
    const savingsBufferNum = parseFloat(savingsBuffer)

    if (incomeInputMode === "gross" && (!Number.isFinite(grossAmountNum) || grossAmountNum <= 0)) {
      setError("Gross pay amount must be greater than 0.")
      return
    }

    if (incomeInputMode === "gross" && useRecentNetAverage && recentNetAverage <= 0) {
      setError("Enter your recent monthly net values to calculate an average.")
      return
    }

    if (incomeInputMode === "gross" && manualNetOverride.trim() && (!Number.isFinite(manualNetOverrideNum) || manualNetOverrideNum <= 0)) {
      setError("Manual net override must be greater than 0.")
      return
    }

    if (!Number.isFinite(incomeNum) || incomeNum <= 0) {
      setError("Monthly take-home income must be greater than 0.")
      return
    }

    if (incomeNum > MAX_MONETARY_FIELD) {
      setError(`Monthly take-home income looks too high. Max allowed is ${currencySymbol(currencyCode)}${MAX_MONETARY_FIELD.toLocaleString()}.`)
      return
    }

    for (const [field, value] of expenseEntries) {
      if (!Number.isFinite(value) || value < 0) {
        setError(`${field.replace(/_/g, " ")} must be 0 or more.`)
        return
      }
      if (value > MAX_MONETARY_FIELD) {
        setError(`${field.replace(/_/g, " ")} looks too high. Max allowed is ${currencySymbol(currencyCode)}${MAX_MONETARY_FIELD.toLocaleString()}.`)
        return
      }
    }

    if (!Number.isFinite(savingsBufferNum) || savingsBufferNum < 0) {
      setError("Savings buffer must be 0 or more.")
      return
    }

    if (savingsBufferNum > MAX_MONETARY_FIELD) {
      setError(`Savings buffer looks too high. Max allowed is ${currencySymbol(currencyCode)}${MAX_MONETARY_FIELD.toLocaleString()}.`)
      return
    }

    const totalExpenses = expenseEntries.reduce((sum, [, value]) => sum + value, 0)
    if (totalExpenses > incomeNum * 20 && totalExpenses > 50_000) {
      setError("Total monthly expenses look unusually high vs your income. Please check for input typos (for example extra zeros).")
      return
    }

    const manualLiteracyNum = Number.parseInt(manualLiteracyScore, 10)
    if (literacyMode === "manual" && (!Number.isFinite(manualLiteracyNum) || manualLiteracyNum < 1 || manualLiteracyNum > 5)) {
      setError("Manual literacy level must be between 1 and 5.")
      return
    }

    if (literacyMode === "quiz") {
      const invalidAnswer = literacyAnswers.some((value) => {
        const parsed = Number.parseInt(value, 10)
        return !Number.isFinite(parsed) || parsed < 1 || parsed > 5
      })
      if (invalidAnswer) {
        setError("Answer each literacy question with a score from 1 to 5.")
        return
      }
    }

    const payload = {
      monthly_income: incomeNum,
      currency_code: normalizeCurrencyCode(currencyCode),
      manual_literacy_score: literacyMode === "manual" ? manualLiteracyNum : null,
      literacy_answers: literacyMode === "quiz" ? literacyAnswers.map((value) => Number.parseInt(value, 10)) : null,
      age_band: ageBand || null,
      employment_status: employmentStatus || null,
      occupation_category: occupationCategory || null,
      dependents_count: parseInt(dependentsCount),
      savings_buffer: savingsBufferNum,
      rent: parseFloat(rent),
      bills: parseFloat(bills),
      subscriptions: parseFloat(subscriptions),
      loan_repayments: parseFloat(loanRepayments),
      groceries: parseFloat(groceries),
      transport: parseFloat(transport),
      entertainment: parseFloat(entertainment),
      eating_out: parseFloat(eatingOut),
      clothing: parseFloat(clothing),
      health: parseFloat(health),
      other: parseFloat(other),
    }

    api.post(payload, "/api/v1/profile")
      .json(() => {
        setSuccess(true)
        if (onSaved) {
          onSaved()
        } else {
          navigate("/dashboard", { replace: true })
        }
      })
      .catch(() => setError("Failed to save your profile. Please try again."))
  }

  const handleLogout = () => {
    api.post({}, "/api/v1/auth/logout")
      .json(() => {
        setLoggedInState(false)
        navigate("/login", { replace: true })
      })
      .catch(error => console.error(error))
  }

  const applyImportedExpenseTotals = (totals: Record<string, number>) => {
    setRent(toInputValue(totals.rent))
    setBills(toInputValue(totals.bills))
    setSubscriptions(toInputValue(totals.subscriptions))
    setLoanRepayments(toInputValue(totals.loan_repayments))
    setGroceries(toInputValue(totals.groceries))
    setTransport(toInputValue(totals.transport))
    setEntertainment(toInputValue(totals.entertainment))
    setEatingOut(toInputValue(totals.eating_out))
    setClothing(toInputValue(totals.clothing))
    setHealth(toInputValue(totals.health))
    setOther(toInputValue(totals.other))
    setCsvAppliedNotice("Imported category totals have been copied into the expense fields below. Review and edit them before saving.")
  }

  const handleCsvImport = async () => {
    if (!csvFile) {
      setCsvImportError("Choose a CSV file first.")
      return
    }

    setCsvImportLoading(true)
    setCsvImportError(null)
    setCsvAppliedNotice(null)

    try {
      const formData = new FormData()
      formData.append("file", csvFile)

      const response = await fetch("http://localhost:8000/api/v1/csv/upload", {
        method: "POST",
        credentials: "include",
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`)
      }

      const data = (await response.json()) as CsvUploadResponse
      setCsvImportResult(data)
    } catch {
      setCsvImportError("Failed to parse CSV. Make sure the file is a bank export with headers and try again.")
    } finally {
      setCsvImportLoading(false)
    }
  }

  const convertAllAmountsToSelectedCurrency = () => {
    const from = amountsCurrencyCode
    const to = currencyCode
    if (from === to) return

    const convertText = (value: string) => {
      const parsed = Number.parseFloat(value)
      if (!Number.isFinite(parsed)) return value
      return convertCurrencyWithRates(parsed, from, to, fxRates?.usd_per_currency).toFixed(2)
    }

    setMonthlyIncome((v) => convertText(v))
    setSavingsBuffer((v) => convertText(v))

    setRent((v) => convertText(v))
    setBills((v) => convertText(v))
    setSubscriptions((v) => convertText(v))
    setLoanRepayments((v) => convertText(v))
    setGroceries((v) => convertText(v))
    setTransport((v) => convertText(v))
    setEntertainment((v) => convertText(v))
    setEatingOut((v) => convertText(v))
    setClothing((v) => convertText(v))
    setHealth((v) => convertText(v))
    setOther((v) => convertText(v))

    setGrossPayAmount((v) => convertText(v))
    setManualNetOverride((v) => convertText(v))
    setRecentNetMonths((prev) => prev.map((v) => convertText(v)))

    setAmountsCurrencyCode(to)
    setManualCurrencyUpdateConfirmed(false)
  }

  // When embedded inside the dashboard, skip the outer navbar/card wrapper
  const isEmbedded = !!onSaved

  const formContent = (
    <form onSubmit={handleSubmit}>
      <FieldGroup>
        {prefillLoading && (
          <p className="text-xs text-muted-foreground">Loading saved profile values...</p>
        )}

        <FieldSet>
          <div className="rounded-xl border bg-muted/15 p-4 space-y-3">
            <div>
              <p className="text-sm font-semibold">Import expenses from bank CSV</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Upload a bank export to estimate category totals. This does not save anything automatically. It only fills the expense fields below after you confirm.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <Input
                aria-label="Bank CSV file"
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] ?? null)}
              />
              <Button type="button" variant="outline" onClick={handleCsvImport} disabled={!csvFile || csvImportLoading}>
                {csvImportLoading ? "Parsing..." : "Upload CSV"}
              </Button>
            </div>

            {csvImportError && (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                {csvImportError}
              </div>
            )}

            {csvAppliedNotice && (
              <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800">
                {csvAppliedNotice}
              </div>
            )}

            {csvImportResult && (
              <div className="space-y-3 rounded-lg border bg-background p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs text-muted-foreground">
                    Parsed <span className="font-medium text-foreground">{csvImportResult.parsed_count}</span> row(s).
                  </p>
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => applyImportedExpenseTotals(csvImportResult.category_totals)}
                  >
                    Apply imported totals to expense fields
                  </Button>
                </div>

                {csvImportResult.warnings.length > 0 && (
                  <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                    <p className="font-medium">Parser warnings</p>
                    <ul className="mt-1 space-y-1">
                      {csvImportResult.warnings.map((warning) => (
                        <li key={warning}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="grid gap-2 sm:grid-cols-2">
                  {Object.entries(csvImportResult.category_totals)
                    .filter(([, value]) => value > 0)
                    .sort((a, b) => b[1] - a[1])
                    .map(([category, value]) => (
                      <div key={category} className="flex items-center justify-between rounded-md border px-3 py-2 text-xs">
                        <span className="capitalize text-muted-foreground">{category.replace(/_/g, " ")}</span>
                        <span className="font-medium text-foreground">{currencySymbol(currencyCode)}{value.toFixed(2)}</span>
                      </div>
                    ))}
                </div>

                {csvImportResult.transactions.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">Sample classified rows</p>
                    <div className="space-y-2">
                      {csvImportResult.transactions.slice(0, 5).map((transaction, idx) => (
                        <div key={`${transaction.description}-${idx}`} className="rounded-md border px-3 py-2 text-xs">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-medium text-foreground">{transaction.description || "Unknown description"}</span>
                            <span>{currencySymbol(currencyCode)}{transaction.amount.toFixed(2)}</span>
                          </div>
                          <div className="mt-1 text-muted-foreground">
                            Suggested category: <span className="font-medium text-foreground">{transaction.suggested_category ?? "other"}</span>
                            {" · "}
                            Confidence: <span className="font-medium text-foreground">{transaction.confidence?.toFixed(2) ?? "n/a"}</span>
                            {" · "}
                            Method: <span className="font-medium text-foreground">{transaction.method ?? "unknown"}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </FieldSet>

        {/* --- Income --- */}
        <FieldSet>
          <Field>
            <FieldLabel htmlFor="currency-code">Currency</FieldLabel>
            <select
              id="currency-code"
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={currencyCode}
              onChange={(e) => {
                setCurrencyCode(normalizeCurrencyCode(e.target.value))
                setManualCurrencyUpdateConfirmed(false)
              }}
            >
              <option value="GBP">GBP (£)</option>
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
              <option value="CAD">CAD (C$)</option>
              <option value="AUD">AUD (A$)</option>
              <option value="INR">INR (₹)</option>
              <option value="JPY">JPY (¥)</option>
              <option value="AED">AED (د.إ)</option>
            </select>
          </Field>
          {hasExistingProfile && currencyCode !== amountsCurrencyCode && (
            <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 space-y-2">
              <p>
                Profile values are currently in <span className="font-medium">{amountsCurrencyCode}</span>. Selected currency is{" "}
                <span className="font-medium">{currencyCode}</span>.
              </p>
              <p>
                Conversion rates: {fxRates ? `${fxRates.as_of} (${fxRates.live ? "live" : "fallback"})` : "static fallback"}.
              </p>
              {!fxRates?.live && fxRates?.error && (
                <p>{fxRates.error}</p>
              )}
              <div className="flex flex-wrap items-center gap-2">
                <Button type="button" size="sm" variant="outline" onClick={convertAllAmountsToSelectedCurrency}>
                  Convert all profile amounts to {currencyCode}
                </Button>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={manualCurrencyUpdateConfirmed}
                    onChange={(e) => setManualCurrencyUpdateConfirmed(e.target.checked)}
                  />
                  I already edited the numbers manually in {currencyCode}
                </label>
              </div>
            </div>
          )}
          <Field>
            <FieldLabel htmlFor="income-mode">Income Input Mode</FieldLabel>
            <select
              id="income-mode"
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={incomeInputMode}
              onChange={(e) => setIncomeInputMode(e.target.value as "net" | "gross")}
            >
              <option value="net">I know my net monthly take-home</option>
              <option value="gross">I only know my gross pay</option>
            </select>
            <FieldDescription>
              All stress tests and spending calculations use monthly net take-home income.
            </FieldDescription>
          </Field>

          {incomeInputMode === "net" ? (
              <Field>
                <FieldLabel htmlFor="monthly-income">Monthly Take-Home Income ({currencySymbol(currencyCode)})</FieldLabel>
                <Input
                id="monthly-income"
                type="number"
                min="0"
                step="0.01"
                required
                value={monthlyIncome}
                onChange={(e) => setMonthlyIncome(e.target.value)}
              />
              <FieldDescription>
                Enter your after-tax monthly pay (money you actually receive in your bank account).
              </FieldDescription>
            </Field>
          ) : (
            <>
              {employmentStatus === "self_employed" && (
                <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                  Self-employed income can vary and tax treatment differs. For best accuracy, use recent net monthly averages or set a manual net override.
                </div>
              )}
              <Field>
                <FieldLabel htmlFor="gross-pay-amount">Gross Pay Amount ({currencySymbol(currencyCode)})</FieldLabel>
                <Input
                  id="gross-pay-amount"
                  type="number"
                  min="0"
                  step="0.01"
                  required
                  value={grossPayAmount}
                  onChange={(e) => setGrossPayAmount(e.target.value)}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="gross-pay-frequency">Gross Pay Frequency</FieldLabel>
                <select
                  id="gross-pay-frequency"
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={grossPayFrequency}
                  onChange={(e) => setGrossPayFrequency(e.target.value as "monthly" | "annual" | "weekly" | "biweekly")}
                >
                  <option value="annual">Annual salary</option>
                  <option value="monthly">Monthly gross pay</option>
                  <option value="biweekly">Biweekly gross pay</option>
                  <option value="weekly">Weekly gross pay</option>
                </select>
              </Field>
              <Field>
                <FieldLabel htmlFor="tax-region">Tax Region</FieldLabel>
                <select
                  id="tax-region"
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={taxRegion}
                  onChange={(e) => setTaxRegion(e.target.value as "uk" | "us")}
                >
                  <option value="uk">UK (PAYE + NI estimate)</option>
                  <option value="us">US Federal + FICA estimate</option>
                </select>
              </Field>
              <Field>
                <FieldLabel htmlFor="estimated-net">Estimated Monthly Take-Home ({currencySymbol(currencyCode)})</FieldLabel>
                <Input
                  id="estimated-net"
                  type="text"
                  readOnly
                  value={estimatedMonthlyNet > 0 ? estimatedMonthlyNet.toFixed(2) : "0.00"}
                />
                <FieldDescription>
                  Estimate only. UK excludes pension/student loan and US excludes state/local taxes.
                </FieldDescription>
              </Field>
              <Field>
                <label htmlFor="use-recent-net-average" className="flex items-center gap-2 text-sm">
                  <input
                    id="use-recent-net-average"
                    type="checkbox"
                    checked={useRecentNetAverage}
                    onChange={(e) => setUseRecentNetAverage(e.target.checked)}
                  />
                  Use average of recent net months (recommended for irregular/self-employed income)
                </label>
              </Field>
              {useRecentNetAverage && (
                <>
                  <Field>
                    <FieldLabel htmlFor="average-window">Average Window</FieldLabel>
                    <select
                      id="average-window"
                      className="w-full rounded-md border px-3 py-2 text-sm"
                      value={averageWindow}
                      onChange={(e) => setAverageWindow(Number(e.target.value) as 3 | 6 | 12)}
                    >
                      <option value={3}>Last 3 months</option>
                      <option value={6}>Last 6 months</option>
                      <option value={12}>Last 12 months</option>
                    </select>
                  </Field>
                  {recentNetMonths.map((value, idx) => (
                    <Field key={`recent-net-${idx}`}>
                      <FieldLabel htmlFor={`recent-net-${idx}`}>Net take-home month {idx + 1} ({currencySymbol(currencyCode)})</FieldLabel>
                      <Input
                        id={`recent-net-${idx}`}
                        type="number"
                        min="0"
                        step="0.01"
                        value={value}
                        onChange={(e) => {
                          const next = [...recentNetMonths]
                          next[idx] = e.target.value
                          setRecentNetMonths(next)
                        }}
                      />
                    </Field>
                  ))}
                  <Field>
                    <FieldLabel htmlFor="average-net-result">Average Net (Monthly) ({currencySymbol(currencyCode)})</FieldLabel>
                    <Input
                      id="average-net-result"
                      type="text"
                      readOnly
                      value={recentNetAverage > 0 ? recentNetAverage.toFixed(2) : "0.00"}
                    />
                  </Field>
                </>
              )}
              <Field>
                <FieldLabel htmlFor="manual-net-override">Manual Net Override (Optional) ({currencySymbol(currencyCode)})</FieldLabel>
                <Input
                  id="manual-net-override"
                  type="number"
                  min="0"
                  step="0.01"
                  value={manualNetOverride}
                  onChange={(e) => setManualNetOverride(e.target.value)}
                />
                <FieldDescription>
                  If entered, this value is used as your monthly net income for calculations.
                </FieldDescription>
              </Field>
              <Field>
                <FieldLabel htmlFor="final-net-used">Final Monthly Net Used ({currencySymbol(currencyCode)})</FieldLabel>
                <Input
                  id="final-net-used"
                  type="text"
                  readOnly
                  value={finalGrossModeNet > 0 ? finalGrossModeNet.toFixed(2) : "0.00"}
                />
                <FieldDescription>
                  Source: {manualNetOverrideNum > 0 ? "manual override" : useRecentNetAverage ? "recent net average" : "gross tax estimate"}.
                </FieldDescription>
              </Field>
            </>
          )}
          <Field>
            <FieldLabel htmlFor="savings-buffer">Current Savings / Cash Buffer ({currencySymbol(currencyCode)})</FieldLabel>
            <Input
              id="savings-buffer"
              type="number"
              min="0"
              step="0.01"
              value={savingsBuffer}
              onChange={(e) => setSavingsBuffer(e.target.value)}
            />
          </Field>
        </FieldSet>

        <FieldSet>
          <p className="text-sm font-semibold text-muted-foreground">Financial Literacy</p>
          <Field>
            <FieldLabel htmlFor="literacy-mode">How should FinLit set your explanation level?</FieldLabel>
            <select
              id="literacy-mode"
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={literacyMode}
              onChange={(e) => setLiteracyMode(e.target.value as "manual" | "quiz")}
            >
              <option value="manual">Let me choose it directly</option>
              <option value="quiz">Estimate it from a few questions</option>
            </select>
            <FieldDescription>
              This changes how simple or technical chat and advice responses are.
            </FieldDescription>
          </Field>

          {literacyMode === "manual" ? (
            <Field>
              <FieldLabel htmlFor="manual-literacy-score">Explanation Level (1-5)</FieldLabel>
              <select
                id="manual-literacy-score"
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={manualLiteracyScore}
                onChange={(e) => setManualLiteracyScore(e.target.value)}
              >
                <option value="1">1 - Very simple</option>
                <option value="2">2 - Simple</option>
                <option value="3">3 - Balanced</option>
                <option value="4">4 - Detailed</option>
                <option value="5">5 - More technical</option>
              </select>
            </Field>
          ) : (
            <>
              {LITERACY_QUESTIONS.map((question, idx) => (
                <Field key={question.id}>
                  <FieldLabel htmlFor={`literacy-${question.id}`}>{question.prompt}</FieldLabel>
                  <select
                    id={`literacy-${question.id}`}
                    className="w-full rounded-md border px-3 py-2 text-sm"
                    value={literacyAnswers[idx]}
                    onChange={(e) => {
                      const next = [...literacyAnswers]
                      next[idx] = e.target.value
                      setLiteracyAnswers(next)
                    }}
                  >
                    <option value="1">1 - Not comfortable</option>
                    <option value="2">2 - Slightly comfortable</option>
                    <option value="3">3 - Moderately comfortable</option>
                    <option value="4">4 - Comfortable</option>
                    <option value="5">5 - Very comfortable</option>
                  </select>
                </Field>
              ))}
              <div className="rounded-md border bg-muted/20 px-3 py-2 text-sm text-muted-foreground">
                Estimated explanation level: <span className="font-medium text-foreground">{estimatedLiteracyScore}/5</span>
              </div>
            </>
          )}
        </FieldSet>

        {/* --- Context --- */}
        <FieldSet>
          <Field>
            <FieldLabel htmlFor="age-band">Age Band</FieldLabel>
            <select
              id="age-band"
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={ageBand}
              onChange={(e) => setAgeBand(e.target.value)}
            >
              <option value="">Prefer not to say</option>
              <option value="18-24">18-24</option>
              <option value="25-34">25-34</option>
              <option value="35-44">35-44</option>
              <option value="45-54">45-54</option>
              <option value="55+">55+</option>
            </select>
          </Field>
          <Field>
            <FieldLabel htmlFor="employment-status">Employment Status</FieldLabel>
            <select
              id="employment-status"
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={employmentStatus}
              onChange={(e) => setEmploymentStatus(e.target.value)}
            >
              <option value="">Prefer not to say</option>
              <option value="student">Student</option>
              <option value="employed">Employed</option>
              <option value="self_employed">Self-employed</option>
              <option value="unemployed">Unemployed</option>
            </select>
          </Field>
          <Field>
            <FieldLabel htmlFor="occupation">Occupation Category</FieldLabel>
            <select
              id="occupation"
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={occupationCategory}
              onChange={(e) => setOccupationCategory(e.target.value)}
            >
              <option value="">Prefer not to say</option>
              <option value="tech">Tech</option>
              <option value="finance">Finance</option>
              <option value="retail">Retail</option>
              <option value="healthcare">Healthcare</option>
              <option value="other">Other</option>
            </select>
          </Field>
          <Field>
            <FieldLabel htmlFor="dependents">Number of Dependents</FieldLabel>
            <Input
              id="dependents"
              type="number"
              min="0"
              max="20"
              value={dependentsCount}
              onChange={(e) => setDependentsCount(e.target.value)}
            />
          </Field>
        </FieldSet>

        {/* --- Fixed Expenses --- */}
        <FieldSet>
          <p className="text-sm font-semibold text-muted-foreground">Fixed Monthly Expenses ({currencySymbol(currencyCode)})</p>
          <Field>
            <FieldLabel htmlFor="rent">Rent / Mortgage</FieldLabel>
            <Input id="rent" type="number" min="0" step="0.01" value={rent} onChange={(e) => setRent(e.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="bills">Bills (utilities, council tax, etc.)</FieldLabel>
            <Input id="bills" type="number" min="0" step="0.01" value={bills} onChange={(e) => setBills(e.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="subscriptions">Subscriptions</FieldLabel>
            <Input id="subscriptions" type="number" min="0" step="0.01" value={subscriptions} onChange={(e) => setSubscriptions(e.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="loan-repayments">Loan Repayments</FieldLabel>
            <Input id="loan-repayments" type="number" min="0" step="0.01" value={loanRepayments} onChange={(e) => setLoanRepayments(e.target.value)} />
          </Field>
        </FieldSet>

        {/* --- Variable Expenses --- */}
        <FieldSet>
          <p className="text-sm font-semibold text-muted-foreground">Variable Monthly Expenses ({currencySymbol(currencyCode)})</p>
          <Field>
            <FieldLabel htmlFor="groceries">Groceries</FieldLabel>
            <Input id="groceries" type="number" min="0" step="0.01" value={groceries} onChange={(e) => setGroceries(e.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="transport">Transport</FieldLabel>
            <Input id="transport" type="number" min="0" step="0.01" value={transport} onChange={(e) => setTransport(e.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="entertainment">Entertainment</FieldLabel>
            <Input id="entertainment" type="number" min="0" step="0.01" value={entertainment} onChange={(e) => setEntertainment(e.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="eating-out">Eating Out</FieldLabel>
            <Input id="eating-out" type="number" min="0" step="0.01" value={eatingOut} onChange={(e) => setEatingOut(e.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="clothing">Clothing</FieldLabel>
            <Input id="clothing" type="number" min="0" step="0.01" value={clothing} onChange={(e) => setClothing(e.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="health">Health</FieldLabel>
            <Input id="health" type="number" min="0" step="0.01" value={health} onChange={(e) => setHealth(e.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="other">Other</FieldLabel>
            <Input id="other" type="number" min="0" step="0.01" value={other} onChange={(e) => setOther(e.target.value)} />
          </Field>
        </FieldSet>

        {error && (
          <div className="rounded-md bg-red-50 p-3 border border-red-200">
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        )}

        {success && (
          <div className="rounded-md bg-green-50 p-3 border border-green-200">
            <p className="text-sm font-medium text-green-800">Profile saved successfully.</p>
          </div>
        )}

        <Field orientation="horizontal">
          <Button type="submit">Save & Continue</Button>
          {!isEmbedded && (
            <Button variant="outline" type="button" onClick={handleLogout}>
              Logout
            </Button>
          )}
        </Field>

      </FieldGroup>
    </form>
  )

  // When embedded in dashboard, render form directly without page chrome
  if (isEmbedded) {
    return (
      <div className="max-w-lg">
        {formContent}
      </div>
    )
  }

  // Standalone onboarding page (after signup)
  return (
    <div>
      <Navbar />
      <div className="flex flex-1 items-center justify-center py-8">
        <div className="w-full max-w-lg">
          <Card>
            <CardHeader>
              <CardTitle>Let&apos;s set up your account</CardTitle>
            </CardHeader>
            <CardContent>
              {formContent}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default Onboarding
