"""

Chat endpoints.
- POST /chat         -> conversational response (optionally stores chat_messages)
- GET  /chat/history -> last N messages (if we store server-side)

Output is ChatOut with "response" field (not "reply").
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.chat import ChatIn, ChatOut, ChatHistoryMessageOut

from app.services.chat_service import chat_reply, clear_chat_history, get_chat_history

router = APIRouter()


@router.post("", response_model=ChatOut)
def chat(payload: ChatIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return chat_reply(
        db,
        user=user,
        message=payload.message,
        history=payload.history,
        store_history=payload.store_history,
    )


@router.get("/history", response_model=list[ChatHistoryMessageOut])
def history(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_chat_history(db, user=user, limit=30)


@router.delete("/history")
def clear_history(db: Session = Depends(get_db), user=Depends(get_current_user)):
    deleted = clear_chat_history(db, user=user)
    return {"deleted": deleted}
