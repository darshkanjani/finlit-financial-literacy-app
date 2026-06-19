"""

Legal/static endpoints.
Frontend can display these on footer pages.

Keep these simple. No DB.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/privacy")
def privacy():
    return {
        "text": (
            "FinLit is a university demo project. We store only the profile totals you enter "
            "(income and category totals), plus optional advice/chat history if enabled. "
            "We do not store raw CSV transaction rows."
        )
    }


@router.get("/disclaimer")
def disclaimer():
    return {
        "text": (
            "FinLit provides educational guidance only and is not financial advice. "
            "Always verify important decisions with official sources or a qualified professional."
        )
    }
