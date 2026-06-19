"""

Purpose:
- Unit test categoriser rules without touching FastAPI/DB.

Tests:
1) Deterministic mapping:
   - "TESCO" / "ALDI" -> groceries
   - "UBER" / "TRAINLINE" -> transport
   - "NETFLIX" / "SPOTIFY" -> subscriptions
   - "Deliveroo" -> eating_out
   - "Amazon" -> other (or shopping) depending on your mapping

2) Normalisation:
   - case-insensitive
   - trims whitespace/punctuation
   - handles common prefixes/suffixes (e.g. "TESCO STORES 1234")

3) Fallback behavior:
   - unknown string -> "other"
   - returns optional confidence/method if you include it

4) Batch behaviour:
   - list of descriptions -> list of outputs (no crashes on empty/None rows)
"""
