"""
P&L Service - Core P&L calculation logic using Pandas/NumPy.

Learning points:
- Using Pandas for financial calculations
- NumPy for numerical operations
- Time series analysis
- P&L decomposition
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from typing import Optional
import numpy as np
import pandas as pd

from models.pnl import DailyPnL
from models.trade import Trade, TradeDirection, TradeStatus
from models.price import MarketPrice
from models.contract import CommodityType
from schemas.pnl import PnLSummary, PnLTimeSeries


class PnLService:
    """
    Service for P&L calculations.

    Uses Pandas DataFrames for efficient financial computations.
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_daily_pnl(
        self,
        pnl_date: date,
        commodity: CommodityType
    ) -> DailyPnL:
        """
        Calculate P&L for a specific date and commodity.

        Steps:
        1. Get all trades up to this date
        2. Get current market price
        3. Calculate realized P&L from settled trades
        4. Calculate unrealized P&L from open positions
        5. Store the daily P&L record
        """
        # Get trades as DataFrame for easier calculations
        trades = (
            self.db.query(Trade)
            .filter(Trade.trade_date <= datetime.combine(pnl_date, datetime.max.time()))
            .all()
        )

        if not trades:
            # No trades, create zero P&L
            return self._create_zero_pnl(pnl_date, commodity)

        # Convert to DataFrame
        df = pd.DataFrame([{
            "direction": t.direction.value,
            "quantity": t.quantity,
            "price": t.price,
            "status": t.status.value,
            "signed_qty": t.quantity if t.direction == TradeDirection.BUY else -t.quantity
        } for t in trades])

        # Get market price for valuation
        market_price = self._get_market_price(pnl_date, commodity)

        # Calculate volumes
        buy_mask = df["direction"] == "BUY"
        sell_mask = df["direction"] == "SELL"

        buy_volume = float(df.loc[buy_mask, "quantity"].sum())
        sell_volume = float(df.loc[sell_mask, "quantity"].sum())
        net_volume = buy_volume - sell_volume

        # Calculate average entry price
        if net_volume != 0:
            # Weighted average price
            total_value = (df["signed_qty"] * df["price"]).sum()
            avg_price = total_value / df["signed_qty"].sum() if df["signed_qty"].sum() != 0 else 0
        else:
            avg_price = 0

        # Calculate P&L
        # Realized: from settled trades
        settled_mask = df["status"] == "SETTLED"
        realized_pnl = 0.0
        if settled_mask.any():
            settled_df = df[settled_mask]
            # Simplified: realized = (market - entry) * settled_qty
            realized_pnl = float(((market_price - settled_df["price"]) * settled_df["signed_qty"]).sum())

        # Unrealized: from open positions
        open_mask = df["status"].isin(["PENDING", "CONFIRMED"])
        unrealized_pnl = 0.0
        if open_mask.any():
            open_df = df[open_mask]
            unrealized_pnl = float(((market_price - open_df["price"]) * open_df["signed_qty"]).sum())

        total_pnl = realized_pnl + unrealized_pnl

        # Get previous day's P&L for delta calculation
        prev_pnl = (
            self.db.query(DailyPnL)
            .filter(DailyPnL.pnl_date < pnl_date)
            .filter(DailyPnL.commodity == commodity)
            .order_by(DailyPnL.pnl_date.desc())
            .first()
        )
        delta_pnl = total_pnl - (prev_pnl.total_pnl if prev_pnl else 0)

        # MTM value
        mtm_value = net_volume * market_price

        # Create or update daily P&L record
        existing = (
            self.db.query(DailyPnL)
            .filter(DailyPnL.pnl_date == pnl_date)
            .filter(DailyPnL.commodity == commodity)
            .first()
        )

        if existing:
            pnl_record = existing
        else:
            pnl_record = DailyPnL(pnl_date=pnl_date, commodity=commodity)
            self.db.add(pnl_record)

        pnl_record.opening_position_value = prev_pnl.closing_position_value if prev_pnl else 0
        pnl_record.closing_position_value = mtm_value
        pnl_record.realized_pnl = realized_pnl
        pnl_record.unrealized_pnl = unrealized_pnl
        pnl_record.total_pnl = total_pnl
        pnl_record.delta_pnl = delta_pnl
        pnl_record.buy_volume = buy_volume
        pnl_record.sell_volume = sell_volume
        pnl_record.net_volume = net_volume
        pnl_record.market_price = market_price

        self.db.commit()
        self.db.refresh(pnl_record)
        return pnl_record

    def _create_zero_pnl(self, pnl_date: date, commodity: CommodityType) -> DailyPnL:
        """Create a zero P&L record when no trades exist"""
        pnl_record = DailyPnL(
            pnl_date=pnl_date,
            commodity=commodity,
            opening_position_value=0,
            closing_position_value=0,
            realized_pnl=0,
            unrealized_pnl=0,
            total_pnl=0,
            delta_pnl=0,
            buy_volume=0,
            sell_volume=0,
            net_volume=0,
        )
        self.db.add(pnl_record)
        self.db.commit()
        self.db.refresh(pnl_record)
        return pnl_record

    def _get_market_price(self, price_date: date, commodity: CommodityType) -> float:
        """Get market price, with fallback to simulated price"""
        price = (
            self.db.query(MarketPrice)
            .filter(MarketPrice.price_date == price_date)
            .filter(MarketPrice.commodity == commodity)
            .first()
        )

        if price:
            return price.price

        # Fallback: return a simulated price (for demo purposes)
        base_prices = {
            CommodityType.GAS: 35.0,
            CommodityType.ELECTRICITY: 85.0,
            CommodityType.POWER: 85.0,
        }
        # Add some randomness based on date
        np.random.seed(price_date.toordinal())
        variation = np.random.normal(0, 0.05)  # 5% volatility
        return base_prices.get(commodity, 50.0) * (1 + variation)

    def get_pnl_summary(
        self,
        start_date: date,
        end_date: date,
        commodity: Optional[CommodityType] = None
    ) -> PnLSummary:
        """Get P&L summary for a date range"""
        query = self.db.query(DailyPnL).filter(
            DailyPnL.pnl_date >= start_date,
            DailyPnL.pnl_date <= end_date
        )

        if commodity:
            query = query.filter(DailyPnL.commodity == commodity)

        records = query.order_by(DailyPnL.pnl_date).all()

        if not records:
            return PnLSummary(
                start_date=start_date,
                end_date=end_date,
                commodity=commodity,
                total_realized_pnl=0,
                total_unrealized_pnl=0,
                total_pnl=0,
                profitable_days=0,
                loss_days=0,
                best_day_pnl=0,
                worst_day_pnl=0,
                average_daily_pnl=0,
                total_buy_volume=0,
                total_sell_volume=0,
            )

        # Use NumPy for efficient calculations
        pnl_array = np.array([r.total_pnl for r in records])
        realized_array = np.array([r.realized_pnl for r in records])
        unrealized_array = np.array([r.unrealized_pnl for r in records])

        return PnLSummary(
            start_date=start_date,
            end_date=end_date,
            commodity=commodity,
            total_realized_pnl=float(np.sum(realized_array)),
            total_unrealized_pnl=float(unrealized_array[-1]) if len(unrealized_array) > 0 else 0,
            total_pnl=float(np.sum(pnl_array)),
            profitable_days=int(np.sum(pnl_array > 0)),
            loss_days=int(np.sum(pnl_array < 0)),
            best_day_pnl=float(np.max(pnl_array)),
            worst_day_pnl=float(np.min(pnl_array)),
            average_daily_pnl=float(np.mean(pnl_array)),
            total_buy_volume=sum(r.buy_volume for r in records),
            total_sell_volume=sum(r.sell_volume for r in records),
        )

    def get_pnl_timeseries(
        self,
        start_date: date,
        end_date: date,
        commodity: Optional[CommodityType] = None
    ) -> PnLTimeSeries:
        """Get P&L time series for charting"""
        query = self.db.query(DailyPnL).filter(
            DailyPnL.pnl_date >= start_date,
            DailyPnL.pnl_date <= end_date
        )

        if commodity:
            query = query.filter(DailyPnL.commodity == commodity)

        records = query.order_by(DailyPnL.pnl_date).all()

        dates = [r.pnl_date for r in records]
        realized = [r.realized_pnl for r in records]
        unrealized = [r.unrealized_pnl for r in records]
        total = [r.total_pnl for r in records]
        prices = [r.market_price for r in records]

        # Calculate cumulative P&L
        cumulative = list(np.cumsum(total)) if total else []

        return PnLTimeSeries(
            dates=dates,
            realized_pnl=realized,
            unrealized_pnl=unrealized,
            total_pnl=total,
            cumulative_pnl=cumulative,
            prices=prices,
        )
