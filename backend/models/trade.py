"""
Trade Model - Individual transactions within contracts.

In energy trading:
- Trades represent actual buy/sell transactions
- They're linked to contracts but represent specific executions
- Each trade has a direction (BUY/SELL) and affects our position

Learning points:
- Foreign key relationships in SQLAlchemy
- Trade direction and quantity concepts
- Mark-to-market valuation
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from .base import Base


class TradeDirection(str, Enum):
    """Trade direction - are we buying or selling?"""
    BUY = "BUY"    # We're buying energy (long position)
    SELL = "SELL"  # We're selling energy (short position)


class TradeStatus(str, Enum):
    """Lifecycle status of a trade"""
    PENDING = "PENDING"        # Not yet confirmed
    CONFIRMED = "CONFIRMED"    # Confirmed by both parties
    SETTLED = "SETTLED"        # Delivered and paid
    CANCELLED = "CANCELLED"    # Cancelled before settlement


class Trade(Base):
    """
    Individual trade/transaction entity.

    Example: On Jan 15, we execute a BUY trade for 100 MWh at €52/MWh
    under contract CTR-2025-001.

    P&L Impact:
    - If we bought at €52 and market is now €55, unrealized P&L = 100 * (55-52) = €300
    - If we sold at €52 and market is now €55, unrealized P&L = 100 * (52-55) = -€300
    """
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)

    # Trade identification
    trade_id = Column(String(50), unique=True, nullable=False, index=True)

    # Link to contract
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)

    # Trade details
    direction = Column(SQLEnum(TradeDirection), nullable=False)
    quantity = Column(Float, nullable=False)  # MWh
    price = Column(Float, nullable=False)     # €/MWh

    # Execution details
    trade_date = Column(DateTime, nullable=False)
    delivery_date = Column(DateTime, nullable=False)

    # Status tracking
    status = Column(SQLEnum(TradeStatus), default=TradeStatus.PENDING)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    trader = Column(String(100))  # Who executed the trade

    def __repr__(self):
        return f"<Trade {self.trade_id}: {self.direction.value} {self.quantity}MWh @ €{self.price}>"

    @property
    def notional_value(self) -> float:
        """Total value of the trade = quantity * price"""
        return self.quantity * self.price

    @property
    def signed_quantity(self) -> float:
        """Quantity with sign: positive for BUY, negative for SELL"""
        return self.quantity if self.direction == TradeDirection.BUY else -self.quantity
