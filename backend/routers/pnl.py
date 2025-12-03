"""
P&L API Router - Profit and Loss endpoints.

Learning points:
- Date handling in APIs
- Complex query parameters
- Response models for charts
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional

from models.base import get_db
from models.contract import CommodityType
from schemas.pnl import PnLResponse, PnLSummary, PnLTimeSeries
from services.pnl_service import PnLService

router = APIRouter(
    prefix="/api/pnl",
    tags=["pnl"],
    responses={404: {"description": "Not found"}},
)


@router.post("/calculate/{pnl_date}")
def calculate_daily_pnl(
    pnl_date: date,
    commodity: CommodityType = Query(..., description="Commodity to calculate P&L for"),
    db: Session = Depends(get_db)
):
    """
    Calculate and store P&L for a specific date.

    This triggers the P&L calculation process:
    1. Aggregates all trades up to the date
    2. Gets current market price
    3. Calculates realized and unrealized P&L
    4. Stores the daily P&L record
    """
    service = PnLService(db)
    pnl = service.calculate_daily_pnl(pnl_date, commodity)

    return {
        "message": f"P&L calculated for {pnl_date}",
        "pnl": PnLResponse.model_validate(pnl)
    }


@router.get("/summary", response_model=PnLSummary)
def get_pnl_summary(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    commodity: Optional[CommodityType] = Query(None, description="Filter by commodity"),
    db: Session = Depends(get_db)
):
    """
    Get P&L summary for a date range.

    Returns aggregated statistics:
    - Total realized and unrealized P&L
    - Number of profitable vs loss days
    - Best and worst days
    - Average daily P&L
    - Win rate percentage
    """
    service = PnLService(db)
    return service.get_pnl_summary(start_date, end_date, commodity)


@router.get("/timeseries", response_model=PnLTimeSeries)
def get_pnl_timeseries(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    commodity: Optional[CommodityType] = Query(None, description="Filter by commodity"),
    db: Session = Depends(get_db)
):
    """
    Get P&L time series for charting.

    Returns arrays suitable for line charts:
    - Dates
    - Daily realized P&L
    - Daily unrealized P&L
    - Daily total P&L
    - Cumulative P&L
    - Market prices
    """
    service = PnLService(db)
    return service.get_pnl_timeseries(start_date, end_date, commodity)


@router.get("/daily/{pnl_date}")
def get_daily_pnl(
    pnl_date: date,
    commodity: Optional[CommodityType] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get P&L for a specific date.

    If no P&L exists for the date, returns empty result.
    """
    from models.pnl import DailyPnL

    query = db.query(DailyPnL).filter(DailyPnL.pnl_date == pnl_date)

    if commodity:
        query = query.filter(DailyPnL.commodity == commodity)

    records = query.all()

    return {
        "date": pnl_date,
        "pnl_records": [PnLResponse.model_validate(r) for r in records]
    }


@router.get("/mtd")
def get_month_to_date_pnl(
    commodity: Optional[CommodityType] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get Month-to-Date P&L summary.

    Convenience endpoint for dashboard.
    """
    today = date.today()
    start_of_month = today.replace(day=1)

    service = PnLService(db)
    return service.get_pnl_summary(start_of_month, today, commodity)


@router.get("/ytd")
def get_year_to_date_pnl(
    commodity: Optional[CommodityType] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get Year-to-Date P&L summary.

    Convenience endpoint for dashboard.
    """
    today = date.today()
    start_of_year = today.replace(month=1, day=1)

    service = PnLService(db)
    return service.get_pnl_summary(start_of_year, today, commodity)
