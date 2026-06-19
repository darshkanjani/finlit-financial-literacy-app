# Financial Stress Testing (FinLit Method)

## What Stress Testing Means in FinLit

A stress test simulates your money month-by-month under a specific scenario.

For each month, FinLit calculates:
- income
- expenses
- net cashflow (`income - expenses`)
- remaining savings buffer

This gives a timeline, not just one headline number.

## Why We Run 3 Scenarios

FinLit uses three complementary scenarios:

1. **Job Loss** (downside)
- Models sharp income shock.
- Tests whether your current buffer can protect essentials.

2. **Emergency Expense** (shock event)
- Models a one-off unexpected cost.
- Tests ability to absorb and recover.

3. **Promotion / Income Boost** (upside)
- Models higher income and potential lifestyle inflation.
- Tests whether extra income actually strengthens resilience.

## Composite Resilience Score (0-10)

Each scenario gets its own resilience score from `0` to `10`.

The score is a weighted composite:
- **40% Survival**: how much of the horizon you survive before savings hit zero
- **30% End-Buffer Strength**: savings left at the end vs a target safety buffer
- **20% Cashflow Health**: average monthly net cashflow quality
- **10% Stability**: consistency of month-to-month net cashflow

So the score is not only "did you survive". It also reflects quality and robustness.

## Interpreting Score Bands

Recommended interpretation:
- `0.0 - 2.9`: Low
- `3.0 - 4.9`: Moderate
- `5.0 - 6.9`: Good
- `7.0 - 8.4`: Strong
- `8.5 - 10`: Excellent

## Important: Scenario Scores Are Separate

A user can have:
- weak job-loss score,
- but strong promotion score.

That is expected. Different shocks create different cashflow paths.

FinLit's dashboard-level resilience should be interpreted as the average of latest scenario runs.

## Job Loss Scenario Details

Typical assumptions:
- income replacement may drop sharply (often near 0)
- essentials remain difficult to cut
- discretionary spend may be reduced over time

What to watch:
- months until broke
- end-buffer after horizon
- average monthly deficit under reduced income

## Emergency Scenario Details

Typical assumptions:
- emergency amount added over one or several months
- normal income/expenses continue unless otherwise configured

What to watch:
- whether buffer remains positive after shock
- recovery speed of savings trajectory
- whether one emergency pushes finances into sustained deficit

## Promotion Scenario Details

Typical assumptions:
- income increases (e.g., +20%)
- optional lifestyle inflation can raise expenses

What to watch:
- whether extra income becomes real monthly surplus
- whether end-buffer improves materially
- whether spending expands so fast that resilience gain is limited

## How To Use Stress Tests Well

1. Run all 3 scenarios with current profile.
2. Identify weakest scenario.
3. Take one concrete action (cut fixed cost, increase buffer, reduce debt, increase income).
4. Re-run scenarios and compare component shifts.

Stress tests are most useful as an iterative planning loop, not a one-time score.
