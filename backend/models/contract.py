"""
Contract Model - Represents energy supply contracts.

In energy trading:
- Contracts define the terms of buying/selling gas or electricity
- They specify counterparty, commodity type, delivery period, and volume
- Contracts are the basis for all trades and P&L calculations

Learning points:
- SQLAlchemy Column types and constraints
- Enums for type safety
- Relationships between tables
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum
from datetime import datetime
from enum import Enum

from .base import Base


class CommodityType(str, Enum):
    """Types of energy commodities traded"""
    GAS = "GAS"
    ELECTRICITY = "ELECTRICITY"
    POWER = "POWER"  # Often used interchangeably with electricity


class ContractType(str, Enum):
    """Types of contracts in energy trading"""
    FORWARD = "FORWARD"      # Fixed price delivery in future
    SPOT = "SPOT"            # Immediate delivery
    SWAP = "SWAP"            # Exchange fixed for floating price
    OPTION = "OPTION"        # Right but not obligation to buy/sell


class Contract(Base):
    """
    Energy supply contract entity.

    Example: A 12-month forward contract to buy 1000 MWh of electricity
    from ENGIE at €50/MWh starting January 2025.
    """
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)

    # Contract identification
    reference = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)

    # Counterparty - who we're trading with
    counterparty = Column(String(100), nullable=False)

    # Contract details
    commodity = Column(SQLEnum(CommodityType), nullable=False)
    contract_type = Column(SQLEnum(ContractType), nullable=False)

    # Volume and pricing
    volume = Column(Float, nullable=False)  # MWh for electricity, MWh (thermal) for gas
    unit_price = Column(Float, nullable=False)  # €/MWh or €/therm

    # Delivery period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Status
    is_active = Column(Integer, default=1)  # 1=active, 0=terminated

    def __repr__(self):
        return f"<Contract {self.reference}: {self.commodity.value} {self.volume}MWh>"
