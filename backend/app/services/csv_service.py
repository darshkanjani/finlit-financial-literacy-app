"""

CSV parsing + aggregation.

Expected CSV columns vary by bank.
We keep this robust:
- detect likely amount/description columns
- normalise amounts
- categorise using simple rules for now (until ml/categoriser.py exists)
- return totals + warnings
- optionally store category_totals in CsvUpload table

TODO (Ethan):
- Replace simple categoriser with ml/categoriser.py when ready
"""

import csv
import io
import re
from typing import Any

from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.db.models import User, CsvUpload


CATEGORIES = [
    "rent", "bills", "subscriptions", "loan_repayments",
    "groceries", "transport", "entertainment", "eating_out",
    "clothing", "health", "other",
]

_MERCHANT_MAP: dict[str, tuple[str, float]] = {
    "netflix": ("subscriptions", 0.99),
    "spotify": ("subscriptions", 0.99),
    "amazon prime": ("subscriptions", 0.95),
    "disney plus": ("subscriptions", 0.98),
    "uber": ("transport", 0.97),
    "bolt": ("transport", 0.97),
    "deliveroo": ("eating_out", 0.98),
    "ubereats": ("eating_out", 0.98),
    "uber eats": ("eating_out", 0.98),
    "just eat": ("eating_out", 0.98),
    "tesco": ("groceries", 0.98),
    "sainsbury": ("groceries", 0.98),
    "aldi": ("groceries", 0.98),
    "lidl": ("groceries", 0.98),
    "asda": ("groceries", 0.98),
    "waitrose": ("groceries", 0.98),
}

_PHRASE_RULES: list[tuple[list[str], str, float]] = [
    (["council tax", "broadband", "internet", "wifi"], "bills", 0.92),
    (["electric", "gas", "water"], "bills", 0.9),
    (["landlord", "letting", "accommodation"], "rent", 0.9),
    (["mcdonald", "restaurant", "cafe", "kfc"], "eating_out", 0.85),
]

_TOKEN_RULES: list[tuple[set[str], str, float]] = [
    ({"uber", "bolt", "tfl", "train", "bus", "rail", "transport"}, "transport", 0.8),
    ({"rent", "landlord", "letting", "accommodation"}, "rent", 0.82),
    ({"pharmacy", "boots", "gp", "dentist", "hospital"}, "health", 0.82),
]


def _guess_columns(headers: list[str]) -> dict:
    lower = [h.lower().strip() for h in headers]

    def find_any(options: list[str]) -> str | None:
        for opt in options:
            if opt in lower:
                return headers[lower.index(opt)]
        return None

    amount_col = find_any(["amount", "value", "transaction amount", "debit", "money out"])
    desc_col = find_any(["description", "merchant", "narrative", "details", "transaction description"])
    date_col = find_any(["date", "transaction date", "booking date"])

    return {"amount": amount_col, "description": desc_col, "date": date_col}


def _simple_categorise(text: str) -> str:
    t = (text or "").lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", t).strip()
    tokens = set(normalized.split()) if normalized else set()

    for merchant, (category, confidence) in _MERCHANT_MAP.items():
        if merchant in normalized:
            return category, confidence, "merchant_map"

    if "co op" in normalized or "coop" in normalized:
        return "groceries", 0.92, "merchant_map"

    for phrases, category, confidence in _PHRASE_RULES:
        if any(phrase in normalized for phrase in phrases):
            return category, confidence, "phrase_rule"

    for token_set, category, confidence in _TOKEN_RULES:
        if tokens.intersection(token_set):
            return category, confidence, "token_rule"

    if any(x in normalized for x in ["prime", "subscription"]):
        return "subscriptions", 0.72, "broad_rule"

    return "other", 0.35, "fallback"


async def parse_and_aggregate_csv(
    db: Session,
    *,
    user: User,
    upload: UploadFile,
    save_audit: bool = True,
) -> dict:
    raw = await upload.read()
    text = raw.decode("utf-8", errors="ignore")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return {"transactions": [], "category_totals": {}, "warnings": ["CSV has no header row"], "parsed_count": 0}

    cols = _guess_columns(reader.fieldnames)
    warnings: list[str] = []

    if not cols["amount"]:
        warnings.append("Could not detect amount column (expected something like Amount/Value).")
    if not cols["description"]:
        warnings.append("Could not detect description/merchant column; categorisation may be poor.")

    totals = {c: 0.0 for c in CATEGORIES}
    transactions: list[dict[str, Any]] = []
    parsed_count = 0

    for row in reader:
        parsed_count += 1

        amt_raw = row.get(cols["amount"]) if cols["amount"] else None
        desc = row.get(cols["description"]) if cols["description"] else ""
        date_value = row.get(cols["date"]) if cols["date"] else None

        try:
            amt = float(str(amt_raw).replace("£", "").replace(",", "").strip()) if amt_raw is not None else 0.0
        except Exception:
            amt = 0.0
            warnings.append(f"Row {parsed_count}: failed to parse amount '{amt_raw}'")

        # Some exports have debits as negative already; we want "spend" positive
        spend = abs(amt) if amt < 0 else amt

        cat, confidence, method = _simple_categorise(desc)
        if cat not in totals:
            cat = "other"
        totals[cat] += spend
        transactions.append(
            {
                "date": str(date_value).strip() if date_value else None,
                "description": str(desc or "").strip(),
                "amount": round(spend, 2),
                "suggested_category": cat,
                "confidence": round(float(confidence), 2),
                "method": method,
            }
        )

    totals = {k: round(v, 2) for k, v in totals.items()}

    if save_audit:
        db.add(
            CsvUpload(
                user_id=user.id,
                filename=upload.filename,
                category_totals=totals,
                warnings=warnings,
            )
        )
        db.commit()

    return {
        "transactions": transactions,
        "category_totals": totals,
        "warnings": warnings,
        "parsed_count": parsed_count,
    }
