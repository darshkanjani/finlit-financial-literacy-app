"""

Transaction categoriser.

Purpose:
- Convert messy CSV transaction descriptions into one of our known expense categories.
- Uni-project friendly: explainable rules first, optional LLM fallback second.

Design:
- Rule-based categorisation (keywords/merchant patterns) => deterministic + explainable.
- Optional LLM fallback via app.services.llm_service.call_llm_json (JSON-only).
- If LLM not configured, fallback returns "other".

Output shape:
- category: one of CATEGORY_FIELDS (matches FinancialProfile columns)
- confidence: 0..1
- method: "rules" | "llm" | "fallback"
- rationale: short explanation (useful for debug/demo)

IMPORTANT:
- Keep CATEGORY_FIELDS consistent with FinancialProfile columns and spending_service.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.services.llm_service import call_llm_json


CATEGORY_FIELDS = [
    "rent",
    "bills",
    "subscriptions",
    "loan_repayments",
    "groceries",
    "transport",
    "entertainment",
    "eating_out",
    "clothing",
    "health",
    "other",
]


@dataclass
class CategoriseResult:
    category: str
    confidence: float
    method: str
    rationale: str


# --- Rule dictionaries (small but effective) ---

# Note: Put "strong signals" first (rent, loan, etc.), then softer signals.
_RULES: list[tuple[str, list[str], float]] = [
    # rent / housing
    ("rent", ["rent", "landlord", "letting", "property mgmt", "rightmove", "zoopla"], 0.92),

    # bills / utilities
    ("bills", ["electric", "gas", "water", "council tax", "internet", "broadband", "wifi", "utility", "edf", "british gas", "octopus", "ovo", "thames water"], 0.88),

    # subscriptions
    ("subscriptions", ["netflix", "spotify", "amazon prime", "prime video", "disney", "apple music", "icloud", "google one", "microsoft 365", "adobe", "subscription", "membership"], 0.86),

    # loan repayments / credit
    ("loan_repayments", ["loan", "repayment", "klarna", "affirm", "afterpay", "credit card", "barclaycard", "amex", "visa payment", "mastercard payment"], 0.90),

    # groceries
    ("groceries", ["tesco", "sainsbury", "asda", "aldi", "lidl", "morrisons", "waitrose", "marks and spencer", "m&s", "co-op", "coop", "grocer", "supermarket"], 0.84),

    # transport
    ("transport", ["uber", "bolt", "train", "rail", "tfl", "bus", "tram", "metro", "fuel", "petrol", "diesel", "shell", "bp", "esso", "parking"], 0.82),

    # eating out
    ("eating_out", ["restaurant", "cafe", "coffee", "starbucks", "pret", "mcdonald", "kfc", "burger king", "deliveroo", "ubereats", "just eat", "takeaway"], 0.82),

    # entertainment
    ("entertainment", ["cinema", "movie", "theatre", "concert", "ticketmaster", "steam", "playstation", "xbox", "nintendo", "game"], 0.80),

    # clothing
    ("clothing", ["zara", "hm", "h&m", "uniqlo", "nike", "adidas", "asos", "primark", "clothes", "apparel", "footwear", "shoe"], 0.78),

    # health
    ("health", ["pharmacy", "boots", "superdrug", "dentist", "gp", "hospital", "clinic", "med", "medicine", "prescription", "therapy", "optician"], 0.78),
]


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def categorise_transaction(
    *,
    description: str,
    merchant: Optional[str] = None,
    amount: Optional[float] = None,
    allow_llm: bool = True,
) -> CategoriseResult:
    """
    Categorise a single transaction using:
    1) Rules (fast, deterministic)
    2) Optional LLM fallback (JSON only)
    3) Final fallback => "other"

    amount is optional; sometimes can help LLM, but rules ignore it.
    """
    text = _norm(f"{merchant or ''} {description or ''}".strip())

    if not text:
        return CategoriseResult(category="other", confidence=0.2, method="fallback", rationale="Empty description")

    # 1) Rules
    for cat, keywords, conf in _RULES:
        for kw in keywords:
            if kw in text:
                return CategoriseResult(
                    category=cat,
                    confidence=conf,
                    method="rules",
                    rationale=f"Matched keyword '{kw}'",
                )

    # 2) LLM fallback (optional)
    if allow_llm:
        system = (
            "You are a transaction categoriser.\n"
            "Return JSON only with keys: category, confidence, rationale.\n"
            f"category must be one of: {CATEGORY_FIELDS}.\n"
            "confidence must be 0..1.\n"
            "Be conservative: if unsure, choose 'other'."
        )
        user_msg = f"description={description!r}\nmerchant={merchant!r}\namount={amount!r}"
        out = call_llm_json(system=system, user=user_msg)

        if out:
            cat = str(out.get("category", "other"))
            if cat not in CATEGORY_FIELDS:
                cat = "other"
            try:
                conf = float(out.get("confidence", 0.55))
            except Exception:
                conf = 0.55
            conf = max(0.0, min(1.0, conf))
            rationale = str(out.get("rationale", "LLM categorisation"))
            return CategoriseResult(category=cat, confidence=conf, method="llm", rationale=rationale)

    # 3) Final fallback
    return CategoriseResult(category="other", confidence=0.35, method="fallback", rationale="No rule match")


def categorise_many(
    transactions: list[dict],
    *,
    allow_llm: bool = True,
) -> list[dict]:
    """
    Batch categorisation helper for csv_service.

    Expected input per txn (flexible):
      { "description": "...", "merchant": "...", "amount": 12.34 }

    Output adds:
      category, confidence, method, rationale
    """
    out: list[dict] = []
    for t in transactions:
        r = categorise_transaction(
            description=str(t.get("description", "")),
            merchant=(str(t.get("merchant")) if t.get("merchant") is not None else None),
            amount=(float(t["amount"]) if t.get("amount") is not None else None),
            allow_llm=allow_llm,
        )
        merged = dict(t)
        merged.update(
            {
                "category": r.category,
                "confidence": round(r.confidence, 3),
                "method": r.method,
                "rationale": r.rationale,
            }
        )
        out.append(merged)
    return out
