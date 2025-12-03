"""
Contract Schemas - Pydantic models for API validation.

Learning points:
- Pydantic for data validation
- Separation of Create/Update/Response schemas
- Type hints for better IDE support and documentation
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class CommodityType(str, Enum):
    GAS = "GAS"
    ELECTRICITY = "ELECTRICITY"
    POWER = "POWER"


class ContractType(str, Enum):
    FORWARD = "FORWARD"
    SPOT = "SPOT"
    SWAP = "SWAP"
    OPTION = "OPTION"


class ContractBase(BaseModel):
    """Base schema with common fields"""
    name: str = Field(..., min_length=1, max_length=200)
    counterparty: str = Field(..., min_length=1, max_length=100)
    commodity: CommodityType
    contract_type: ContractType
    volume: float = Field(..., gt=0, description="Volume in MWh")
    unit_price: float = Field(..., gt=0, description="Price in €/MWh")
    start_date: datetime
    end_date: datetime


class ContractCreate(ContractBase):
    """Schema for creating a new contract"""
    reference: str = Field(..., min_length=1, max_length=50)

    model_config = {
        "json_schema_extra": {
            "example": {
                "reference": "CTR-2025-001",
                "name": "Q1 2025 Gas Forward",
                "counterparty": "ENGIE Trading",
                "commodity": "GAS",
                "contract_type": "FORWARD",
                "volume": 10000.0,
                "unit_price": 35.50,
                "start_date": "2025-01-01T00:00:00",
                "end_date": "2025-03-31T23:59:59"
            }
        }
    }


class ContractUpdate(BaseModel):
    """Schema for updating a contract - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    counterparty: Optional[str] = Field(None, min_length=1, max_length=100)
    volume: Optional[float] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    is_active: Optional[int] = Field(None, ge=0, le=1)


class ContractResponse(ContractBase):
    """Schema for contract responses"""
    id: int
    reference: str
    is_active: int
    created_at: datetime
    updated_at: datetime

    # Calculate notional value
    @property
    def notional_value(self) -> float:
        return self.volume * self.unit_price

    model_config = {"from_attributes": True}


class ContractList(BaseModel):
    """Schema for list of contracts with pagination"""
    items: list[ContractResponse]
    total: int
    page: int
    size: int
    pages: int
