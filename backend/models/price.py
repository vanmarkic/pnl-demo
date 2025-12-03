"""
Market Price Model - Historical and current prices.

In energy trading:
- Prices are essential for valuation and P&L calculation
- Prices come from exchanges (e.g., ICE, EEX) or brokers
- Forward prices: future delivery periods
- Spot prices: immediate delivery

Learning points:
- Time series data in databases
- Price curve concepts
- Settlement prices vs trading prices
"""
from sqlalchemy import Column, Integer, Float, DateTime, Date, String, Enum as SQLEnum
from datetime import datetime

from .base import Base
from .contract import CommodityType


class MarketPrice(Base):
    """
    Market price record for a commodity at a specific time.

    Used for:
    - Mark-to-Market valuations
    - P&L calculations
    - Risk metric computations
    - Historical analysis

    Price types:
    - SPOT: Current/immediate delivery price
    - FORWARD: Future delivery price for a specific month
    - SETTLEMENT: Official end-of-day price
    """
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)

    # Price identification
    price_date = Column(Date, nullable=False, index=True)
    commodity = Column(SQLEnum(CommodityType), nullable=False)
    delivery_period = Column(String(20), nullable=False)  # "SPOT" or "2025-03"

    # Price data
    price = Column(Float, nullable=False)  # €/MWh
    currency = Column(String(3), default="EUR")

    # Price metadata
    price_type = Column(String(20), default="SETTLEMENT")  # SPOT, FORWARD, SETTLEMENT
    source = Column(String(50))  # Where price came from (e.g., "ICE", "EEX")

    # For volatility calculations
    previous_price = Column(Float)
    price_change = Column(Float)  # Absolute change
    price_change_pct = Column(Float)  # Percentage change

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketPrice {self.price_date} {self.commodity.value} {self.delivery_period}: €{self.price}>"

    def calculate_change(self, previous: float) -> tuple[float, float]:
        """Calculate price change from previous value"""
        change = self.price - previous
        change_pct = (change / previous * 100) if previous else 0
        return change, change_pct
