"""
Risk API Router - Risk metrics endpoints.

Learning points:
- Risk management concepts
- VaR calculation methods
- Position monitoring
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from models.base import get_db
from models.contract import CommodityType
from services.risk_service import RiskService

router = APIRouter(
    prefix="/api/risk",
    tags=["risk"],
    responses={404: {"description": "Not found"}},
)


@router.get("/metrics/{commodity}")
def get_risk_metrics(
    commodity: CommodityType,
    as_of_date: Optional[date] = Query(None, description="Valuation date"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive risk metrics for a commodity.

    Returns:
    - Net position (MWh)
    - Average entry price
    - Current market price
    - Mark-to-Market value
    - Unrealized P&L
    - Delta (price sensitivity)
    - VaR at 95% and 99% confidence (1-day and 10-day)

    Example response:
    ```json
    {
        "commodity": "GAS",
        "net_position": 1000,
        "average_price": 35.50,
        "market_price": 36.00,
        "mtm_value": 36000,
        "unrealized_pnl": 500,
        "delta": 1000,
        "var_95_1d": 720,
        "var_99_1d": 1008,
        "var_95_10d": 2277
    }
    ```
    """
    service = RiskService(db)
    return service.calculate_position_metrics(commodity, as_of_date)


@router.get("/var/{commodity}")
def calculate_var(
    commodity: CommodityType,
    position_value: float = Query(..., description="Current position value in €"),
    confidence: float = Query(0.95, ge=0.9, le=0.99, description="Confidence level"),
    holding_period: int = Query(1, ge=1, le=30, description="Holding period in days"),
    method: str = Query("historical", description="VaR method: historical, parametric, monte_carlo"),
    db: Session = Depends(get_db)
):
    """
    Calculate Value at Risk (VaR) for a position.

    VaR answers: "What is the maximum loss with X% confidence over Y days?"

    Methods:
    - **historical**: Uses actual historical returns
    - **parametric**: Assumes normal distribution
    - **monte_carlo**: Simulates price paths

    Example:
    VaR(95%, 1-day) = €10,000 means we're 95% confident
    we won't lose more than €10,000 tomorrow.
    """
    service = RiskService(db)
    var = service.calculate_var(
        commodity=commodity,
        position_value=position_value,
        confidence_level=confidence,
        holding_period=holding_period,
        method=method
    )

    return {
        "commodity": commodity.value,
        "position_value": position_value,
        "confidence_level": confidence,
        "holding_period_days": holding_period,
        "method": method,
        "var": round(var, 2),
        "interpretation": f"With {confidence*100}% confidence, maximum {holding_period}-day loss is €{var:,.2f}"
    }


@router.get("/dashboard")
def get_risk_dashboard(db: Session = Depends(get_db)):
    """
    Get risk dashboard data for all commodities.

    Returns aggregated risk metrics for the dashboard overview.
    """
    service = RiskService(db)

    commodities = [CommodityType.GAS, CommodityType.ELECTRICITY]
    dashboard = []

    for commodity in commodities:
        metrics = service.calculate_position_metrics(commodity)
        dashboard.append(metrics)

    # Calculate totals
    total_mtm = sum(d["mtm_value"] for d in dashboard)
    total_pnl = sum(d["unrealized_pnl"] for d in dashboard)
    total_var = sum(d["var_95_1d"] for d in dashboard)

    return {
        "by_commodity": dashboard,
        "totals": {
            "total_mtm_value": round(total_mtm, 2),
            "total_unrealized_pnl": round(total_pnl, 2),
            "total_var_95_1d": round(total_var, 2),
        }
    }


@router.get("/stress-test/{commodity}")
def run_stress_test(
    commodity: CommodityType,
    price_shock_pct: float = Query(..., description="Price shock in % (e.g., -10 for 10% drop)"),
    db: Session = Depends(get_db)
):
    """
    Run a simple stress test.

    Calculates P&L impact of a given price shock.

    Example: price_shock_pct=-10 simulates a 10% price drop
    """
    service = RiskService(db)
    metrics = service.calculate_position_metrics(commodity)

    net_position = metrics["net_position"]
    current_price = metrics["market_price"]
    shocked_price = current_price * (1 + price_shock_pct / 100)
    pnl_impact = net_position * (shocked_price - current_price)

    return {
        "commodity": commodity.value,
        "current_price": current_price,
        "price_shock_pct": price_shock_pct,
        "shocked_price": round(shocked_price, 2),
        "net_position": net_position,
        "pnl_impact": round(pnl_impact, 2),
        "interpretation": f"A {price_shock_pct}% price move would result in €{pnl_impact:,.2f} P&L change"
    }
