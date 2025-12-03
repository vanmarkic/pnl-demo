"""
Trade Schemas - API models for trade operations.

Learning points:
- Validation with Pydantic Field
- Enum handling in APIs
- Computed properties in schemas
"""
from pydantic import BaseModel, Field, computed_field
from datetime import datetime
from typing import Optional
from enum import Enum


class TradeDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"


class TradeCreate(BaseModel):
    """Schema for creating a new trade"""
    contract_id: int = Field(..., description="ID of the parent contract")
    direction: TradeDirection
    quantity: float = Field(..., gt=0, description="Volume in MWh")
    price: float = Field(..., gt=0, description="Price in €/MWh")
    trade_date: datetime
    delivery_date: datetime
    trader: Optional[str] = Field(None, max_length=100)

    model_config = {
        "json_schema_extra": {
            "example": {
                "contract_id": 1,
                "direction": "BUY",
                "quantity": 500.0,
                "price": 36.25,
                "trade_date": "2025-01-15T10:30:00",
                "delivery_date": "2025-02-01T00:00:00",
                "trader": "John Smith"
            }
        }
    }


class TradeResponse(BaseModel):
    """Schema for trade responses"""
    id: int
    trade_id: str
    contract_id: int
    direction: TradeDirection
    quantity: float
    price: float
    trade_date: datetime
    delivery_date: datetime
    status: TradeStatus
    trader: Optional[str]
    created_at: datetime

    @computed_field
    @property
    def notional_value(self) -> float:
        """Total value = quantity * price"""
        return self.quantity * self.price

    @computed_field
    @property
    def signed_quantity(self) -> float:
        """Positive for BUY, negative for SELL"""
        return self.quantity if self.direction == TradeDirection.BUY else -self.quantity

    model_config = {"from_attributes": True}


class TradeList(BaseModel):
    """List of trades with metadata"""
    items: list[TradeResponse]
    total: int
    total_buy_volume: float
    total_sell_volume: float
    net_volume: float
