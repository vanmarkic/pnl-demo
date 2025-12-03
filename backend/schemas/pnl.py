"""
P&L Schemas - API models for profit and loss data.

Learning points:
- Time series data representations
- Financial metrics in APIs
- Dashboard-ready data structures
"""
from pydantic import BaseModel, computed_field
from datetime import date
from typing import Optional
from enum import Enum


class CommodityType(str, Enum):
    GAS = "GAS"
    ELECTRICITY = "ELECTRICITY"
    POWER = "POWER"


class PnLResponse(BaseModel):
    """Single day P&L record"""
    id: int
    pnl_date: date
    commodity: CommodityType
    opening_position_value: float
    closing_position_value: float
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    delta_pnl: float
    buy_volume: float
    sell_volume: float
    net_volume: float
    market_price: Optional[float]
    price_change: Optional[float]

    @computed_field
    @property
    def is_profitable(self) -> bool:
        return self.total_pnl > 0

    model_config = {"from_attributes": True}


class PnLSummary(BaseModel):
    """P&L summary for a period"""
    start_date: date
    end_date: date
    commodity: Optional[CommodityType]

    # Totals
    total_realized_pnl: float
    total_unrealized_pnl: float
    total_pnl: float

    # Statistics
    profitable_days: int
    loss_days: int
    best_day_pnl: float
    worst_day_pnl: float
    average_daily_pnl: float

    # Volume stats
    total_buy_volume: float
    total_sell_volume: float

    @computed_field
    @property
    def win_rate(self) -> float:
        """Percentage of profitable days"""
        total_days = self.profitable_days + self.loss_days
        if total_days == 0:
            return 0.0
        return (self.profitable_days / total_days) * 100


class PnLTimeSeries(BaseModel):
    """Time series data for charts"""
    dates: list[date]
    realized_pnl: list[float]
    unrealized_pnl: list[float]
    total_pnl: list[float]
    cumulative_pnl: list[float]  # Running total
    prices: list[Optional[float]]
