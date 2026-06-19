"""

CSV upload endpoint.
Accepts a bank export CSV, aggregates totals, and stores an audit row.
"""

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.csv import CsvUploadOut
from app.services.csv_service import parse_and_aggregate_csv

router = APIRouter()


@router.post("/upload", response_model=CsvUploadOut)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return await parse_and_aggregate_csv(db, user=user, upload=file, save_audit=True)
