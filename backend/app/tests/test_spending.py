"""

Tests for GET /spending/breakdown:

1) Without profile:
   - returns 404 Profile not found
2) With profile:
   - response contains categories[] + summary + flags
   - sums make sense:
     - categories amounts match profile input
     - savings_percent computed correctly (>=0)
3) Needs/wants classification:
   - known need fields tagged as "need"
   - known wants tagged as "want"
4) Flags:
   - overspend/undersave flags appear when expected (use crafted profile inputs)

Important:
- Avoid over-testing exact floating values; check ranges/keys.
"""
