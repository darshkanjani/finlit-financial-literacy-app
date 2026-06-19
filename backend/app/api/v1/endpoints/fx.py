from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.schemas.fx import FxRatesOut
from app.services.fx_service import get_rates

router = APIRouter()


@router.get("/rates", response_model=FxRatesOut)
def fx_rates(
    force_refresh: bool = Query(default=False),
    _user=Depends(get_current_user),
):
    return get_rates(force_refresh=force_refresh)

