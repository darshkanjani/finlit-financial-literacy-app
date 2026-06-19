"""

Purpose:
- Unit-test retriever itself (not through endpoints).

Tests:
- retrieve(query) returns [] when index files missing (should not crash)
- when index exists: retrieve("budget") returns chunks with score > min_score
- to_source_dicts shape is stable
"""
