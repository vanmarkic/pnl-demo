"""
Risk Service - Risk metrics calculation using NumPy.

Learning points:
- Value at Risk (VaR) calculation
- Position delta and sensitivity analysis
- Monte Carlo simulation basics
- Risk aggregation
"""
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional
import numpy as np
import pandas as pd

from models.position import Position
from models.price import MarketPrice
from models.trade import Trade, TradeDirection
from models.contract import CommodityType


class RiskService:
    """
    Service for risk metric calculations.

    Implements common risk measures used in energy trading:
    - VaR (Value at Risk)
    - Delta (price sensitivity)
    - Position limits monitoring
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_var(
        self,
        commodity: CommodityType,
        position_value: float,
        confidence_level: float = 0.95,
        holding_period: int = 1,
        method: str = "historical"
    ) -> float:
        """
        Calculate Value at Risk (VaR).

        VaR answers: "What is the maximum loss we could experience
        with X% confidence over Y days?"

        Parameters:
        - position_value: Current position value in €
        - confidence_level: Typically 95% or 99%
        - holding_period: Number of days (usually 1 or 10)
        - method: 'historical', 'parametric', or 'monte_carlo'

        Example:
        VaR(95%, 1-day) = €10,000 means:
        "We are 95% confident we won't lose more than €10,000 tomorrow"
        """
        # Get historical price data
        prices = self._get_historical_prices(commodity, days=252)  # 1 year of data

        if len(prices) < 30:
            # Not enough data, use parametric with assumed volatility
            assumed_volatility = 0.02  # 2% daily volatility
            return self._parametric_var(
                position_value, assumed_volatility,
                confidence_level, holding_period
            )

        # Calculate returns
        returns = np.diff(prices) / prices[:-1]

        if method == "historical":
            return self._historical_var(
                position_value, returns,
                confidence_level, holding_period
            )
        elif method == "parametric":
            volatility = np.std(returns)
            return self._parametric_var(
                position_value, volatility,
                confidence_level, holding_period
            )
        else:  # monte_carlo
            return self._monte_carlo_var(
                position_value, returns,
                confidence_level, holding_period
            )

    def _historical_var(
        self,
        position_value: float,
        returns: np.ndarray,
        confidence_level: float,
        holding_period: int
    ) -> float:
        """
        Historical VaR - uses actual historical returns.

        Steps:
        1. Take historical returns
        2. Find the percentile corresponding to (1 - confidence)
        3. Scale by position value and holding period
        """
        # For multi-day VaR, use square root of time rule
        scaling_factor = np.sqrt(holding_period)

        # Find the loss at the given percentile
        var_percentile = np.percentile(returns, (1 - confidence_level) * 100)

        return abs(position_value * var_percentile * scaling_factor)

    def _parametric_var(
        self,
        position_value: float,
        volatility: float,
        confidence_level: float,
        holding_period: int
    ) -> float:
        """
        Parametric VaR - assumes normal distribution.

        Formula: VaR = Position × σ × Z × √t

        Where:
        - σ = daily volatility
        - Z = z-score for confidence level
        - t = holding period in days
        """
        from scipy import stats

        # Z-score for confidence level
        z_score = stats.norm.ppf(confidence_level)

        # Square root of time scaling
        time_scale = np.sqrt(holding_period)

        return position_value * volatility * z_score * time_scale

    def _monte_carlo_var(
        self,
        position_value: float,
        returns: np.ndarray,
        confidence_level: float,
        holding_period: int,
        n_simulations: int = 10000
    ) -> float:
        """
        Monte Carlo VaR - simulates many possible price paths.

        Steps:
        1. Estimate return distribution parameters
        2. Simulate n_simulations price paths
        3. Calculate P&L for each path
        4. Find VaR from simulated P&L distribution
        """
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Simulate returns for holding period
        simulated_returns = np.random.normal(
            mean_return * holding_period,
            std_return * np.sqrt(holding_period),
            n_simulations
        )

        # Calculate simulated P&L
        simulated_pnl = position_value * simulated_returns

        # VaR is the loss at the given percentile
        var = np.percentile(simulated_pnl, (1 - confidence_level) * 100)

        return abs(var)

    def _get_historical_prices(
        self,
        commodity: CommodityType,
        days: int = 252
    ) -> np.ndarray:
        """Get historical prices for VaR calculation"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        prices = (
            self.db.query(MarketPrice.price)
            .filter(MarketPrice.commodity == commodity)
            .filter(MarketPrice.price_date >= start_date)
            .order_by(MarketPrice.price_date)
            .all()
        )

        return np.array([p.price for p in prices])

    def calculate_delta(
        self,
        commodity: CommodityType,
        net_position: float
    ) -> float:
        """
        Calculate position delta (price sensitivity).

        Delta = How much P&L changes for a €1 move in price

        For a simple linear position:
        Delta = Net Position (MWh)

        Example:
        - Position: Long 1000 MWh
        - Delta: 1000
        - If price moves up €1, P&L increases by €1000
        """
        return net_position

    def calculate_position_metrics(
        self,
        commodity: CommodityType,
        as_of_date: Optional[date] = None
    ) -> dict:
        """
        Calculate comprehensive position and risk metrics.

        Returns all key risk indicators for a commodity.
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get all trades
        trades = self.db.query(Trade).all()

        if not trades:
            return {
                "commodity": commodity.value,
                "as_of_date": as_of_date.isoformat(),
                "net_position": 0,
                "average_price": 0,
                "market_price": 0,
                "mtm_value": 0,
                "unrealized_pnl": 0,
                "delta": 0,
                "var_95_1d": 0,
                "var_99_1d": 0,
                "var_95_10d": 0,
            }

        # Calculate net position
        buy_qty = sum(t.quantity for t in trades if t.direction == TradeDirection.BUY)
        sell_qty = sum(t.quantity for t in trades if t.direction == TradeDirection.SELL)
        net_position = buy_qty - sell_qty

        # Calculate weighted average price
        buy_value = sum(t.quantity * t.price for t in trades if t.direction == TradeDirection.BUY)
        sell_value = sum(t.quantity * t.price for t in trades if t.direction == TradeDirection.SELL)

        if net_position != 0:
            avg_price = (buy_value - sell_value) / net_position
        else:
            avg_price = 0

        # Get current market price
        market_price = self._get_current_price(commodity)

        # Calculate MTM and unrealized P&L
        mtm_value = net_position * market_price
        unrealized_pnl = (market_price - avg_price) * net_position if net_position != 0 else 0

        # Calculate risk metrics
        delta = self.calculate_delta(commodity, net_position)
        var_95_1d = self.calculate_var(commodity, abs(mtm_value), 0.95, 1)
        var_99_1d = self.calculate_var(commodity, abs(mtm_value), 0.99, 1)
        var_95_10d = self.calculate_var(commodity, abs(mtm_value), 0.95, 10)

        return {
            "commodity": commodity.value,
            "as_of_date": as_of_date.isoformat(),
            "net_position": net_position,
            "average_price": round(avg_price, 2),
            "market_price": round(market_price, 2),
            "mtm_value": round(mtm_value, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "delta": delta,
            "var_95_1d": round(var_95_1d, 2),
            "var_99_1d": round(var_99_1d, 2),
            "var_95_10d": round(var_95_10d, 2),
        }

    def _get_current_price(self, commodity: CommodityType) -> float:
        """Get most recent market price"""
        price = (
            self.db.query(MarketPrice)
            .filter(MarketPrice.commodity == commodity)
            .order_by(MarketPrice.price_date.desc())
            .first()
        )

        if price:
            return price.price

        # Fallback prices
        defaults = {
            CommodityType.GAS: 35.0,
            CommodityType.ELECTRICITY: 85.0,
            CommodityType.POWER: 85.0,
        }
        return defaults.get(commodity, 50.0)
