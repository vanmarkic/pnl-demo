"""
Trades API Router - Endpoints for trade management.

Learning points:
- Path parameters vs query parameters
- Error handling and validation
- Returning computed properties
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from models.base import get_db
from models.trade import TradeDirection, TradeStatus
from schemas.trade import TradeCreate, TradeResponse, TradeList
from services.trade_service import TradeService

router = APIRouter(
    prefix="/api/trades",
    tags=["trades"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=TradeResponse, status_code=201)
def create_trade(
    trade: TradeCreate,
    db: Session = Depends(get_db)
):
    """
    Execute a new trade.

    Creates a trade linked to an existing contract.
    Trade ID is auto-generated in format: TRD-YYYYMMDD-XXXX

    Example:
    ```json
    {
        "contract_id": 1,
        "direction": "BUY",
        "quantity": 500,
        "price": 36.25,
        "trade_date": "2025-01-15T10:30:00",
        "delivery_date": "2025-02-01T00:00:00",
        "trader": "John Smith"
    }
    ```
    """
    service = TradeService(db)

    try:
        return service.create(trade)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=TradeList)
def list_trades(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    contract_id: Optional[int] = Query(None, description="Filter by contract"),
    direction: Optional[TradeDirection] = Query(None, description="BUY or SELL"),
    status: Optional[TradeStatus] = Query(None, description="Trade status"),
    db: Session = Depends(get_db)
):
    """
    List trades with filtering and pagination.

    Returns trade list with volume summary.
    """
    service = TradeService(db)
    skip = (page - 1) * size

    trades, total = service.get_all(
        skip=skip,
        limit=size,
        contract_id=contract_id,
        direction=direction,
        status=status
    )

    # Get volume summary
    summary = service.get_volume_summary(contract_id)

    return TradeList(
        items=trades,
        total=total,
        total_buy_volume=summary["total_buy_volume"],
        total_sell_volume=summary["total_sell_volume"],
        net_volume=summary["net_volume"]
    )


@router.get("/summary")
def get_trade_summary(
    contract_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get trade volume summary.

    Returns:
    - Total buy volume
    - Total sell volume
    - Net position
    - Trade counts
    """
    service = TradeService(db)
    return service.get_volume_summary(contract_id)


@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Get a specific trade by ID."""
    service = TradeService(db)
    trade = service.get_by_id(trade_id)

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    return trade


@router.patch("/{trade_id}/status")
def update_trade_status(
    trade_id: int,
    status: TradeStatus,
    db: Session = Depends(get_db)
):
    """
    Update trade status.

    Status transitions:
    - PENDING -> CONFIRMED (trade confirmed by both parties)
    - CONFIRMED -> SETTLED (delivery completed, payment made)
    - Any -> CANCELLED (trade cancelled)
    """
    service = TradeService(db)
    trade = service.update_status(trade_id, status)

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    return {"message": f"Trade status updated to {status.value}", "trade_id": trade.trade_id}
