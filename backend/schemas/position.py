"""
Position Schemas - API models for position data.

Learning points:
- Risk metrics in API responses
- Aggregated data representations
"""
from pydantic import BaseModel, computed_field
from datetime import date
from typing import Optional
from enum import Enum


class CommodityType(str, Enum):
    GAS = "GAS"
    ELECTRICITY = "ELECTRICITY"
    POWER = "POWER"


class PositionResponse(BaseModel):
    """Single position record"""
    id: int
    position_date: date
    commodity: CommodityType
    delivery_month: str
    net_quantity: float
    average_price: float
    market_price: Optional[float]
    mtm_value: Optional[float]
    unrealized_pnl: Optional[float]
    delta: Optional[float]
    var_95: Optional[float]

    @computed_field
    @property
    def direction(self) -> str:
        """Human-readable position direction"""
        if self.net_quantity > 0:
            return "LONG"
        elif self.net_quantity < 0:
            return "SHORT"
        return "FLAT"

    model_config = {"from_attributes": True}


class PositionSummary(BaseModel):
    """Aggregated position summary for dashboard"""
    commodity: CommodityType
    total_long: float
    total_short: float
    net_position: float
    total_mtm_value: float
    total_unrealized_pnl: float
    total_var_95: float
    position_count: int

    @computed_field
    @property
    def overall_direction(self) -> str:
        if self.net_position > 0:
            return "NET LONG"
        elif self.net_position < 0:
            return "NET SHORT"
        return "FLAT"
