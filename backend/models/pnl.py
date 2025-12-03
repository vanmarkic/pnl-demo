"""
P&L Model - Daily Profit and Loss tracking.

In energy trading:
- P&L is tracked daily to monitor trading performance
- Realized P&L: from settled trades (actual cash)
- Unrealized P&L: from open positions (paper gain/loss)
- Total P&L = Realized + Unrealized

Learning points:
- Daily valuation process
- MTM (Mark-to-Market) concept
- P&L attribution and decomposition
"""
from sqlalchemy import Column, Integer, Float, DateTime, Date, Enum as SQLEnum
from datetime import datetime

from .base import Base
from .contract import CommodityType


class DailyPnL(Base):
    """
    Daily P&L record for tracking trading performance.

    Key concepts:
    - Realized P&L: Locked in from closed trades
    - Unrealized P&L: Paper gain/loss on open positions
    - Delta P&L: Change from previous day

    Example daily P&L report:
    +------------------+------------+
    | Date             | 2025-01-15 |
    | Commodity        | GAS        |
    | Opening Position | €50,000    |
    | Realized P&L     | €2,000     |
    | Unrealized P&L   | €3,500     |
    | Total P&L        | €5,500     |
    | Delta from Prev  | +€1,200    |
    +------------------+------------+
    """
    __tablename__ = "daily_pnl"

    id = Column(Integer, primary_key=True, index=True)

    # Date and categorization
    pnl_date = Column(Date, nullable=False, index=True)
    commodity = Column(SQLEnum(CommodityType), nullable=False)

    # Position values
    opening_position_value = Column(Float, default=0.0)
    closing_position_value = Column(Float, default=0.0)

    # P&L components
    realized_pnl = Column(Float, default=0.0)    # From settled trades
    unrealized_pnl = Column(Float, default=0.0)  # From MTM revaluation
    total_pnl = Column(Float, default=0.0)       # realized + unrealized

    # Day-over-day change
    delta_pnl = Column(Float, default=0.0)  # Change from previous day

    # Volume traded
    buy_volume = Column(Float, default=0.0)
    sell_volume = Column(Float, default=0.0)
    net_volume = Column(Float, default=0.0)

    # Market data snapshot
    market_price = Column(Float)  # End of day market price
    price_change = Column(Float)  # Price change from previous day

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DailyPnL {self.pnl_date} {self.commodity.value}: €{self.total_pnl:,.2f}>"

    @property
    def is_profitable(self) -> bool:
        """Quick check if the day was profitable"""
        return self.total_pnl > 0
