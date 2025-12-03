"""
Position Model - Aggregated exposure from trades.

In energy trading:
- Position = net exposure from all trades in a commodity/period
- Long position = we own/will receive the commodity
- Short position = we owe/will deliver the commodity
- Position management is crucial for risk control

Learning points:
- Aggregation concepts in trading
- Position vs Trade relationship
- Greeks and risk metrics
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum as SQLEnum
from datetime import datetime, date

from .base import Base
from .contract import CommodityType


class Position(Base):
    """
    Aggregated position for a commodity at a point in time.

    Example:
    - We have BUY trades totaling 500 MWh gas for March 2025
    - We have SELL trades totaling 300 MWh gas for March 2025
    - Net position = +200 MWh (long)

    Risk implication: If gas prices fall, our long position loses value
    """
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)

    # Position identification
    position_date = Column(Date, nullable=False, index=True)
    commodity = Column(SQLEnum(CommodityType), nullable=False)
    delivery_month = Column(String(7), nullable=False)  # Format: "2025-03"

    # Position metrics
    net_quantity = Column(Float, nullable=False)  # MWh, positive=long, negative=short
    average_price = Column(Float, nullable=False)  # Weighted average entry price

    # Current valuation
    market_price = Column(Float)  # Current market price
    mtm_value = Column(Float)     # Mark-to-Market value
    unrealized_pnl = Column(Float)  # Unrealized P&L

    # Risk metrics (simplified)
    delta = Column(Float)  # Price sensitivity: how much P&L changes per €1 price move
    var_95 = Column(Float)  # Value at Risk at 95% confidence

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        direction = "LONG" if self.net_quantity > 0 else "SHORT"
        return f"<Position {self.delivery_month} {self.commodity.value}: {direction} {abs(self.net_quantity)}MWh>"

    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized P&L based on current market price.

        Formula: (Current Price - Entry Price) * Quantity
        - If long (quantity > 0) and price went up: profit
        - If short (quantity < 0) and price went up: loss
        """
        return (current_price - self.average_price) * self.net_quantity
