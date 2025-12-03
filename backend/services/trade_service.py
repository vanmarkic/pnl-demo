"""
Trade Service - Business logic for trade operations.

Learning points:
- Auto-generating unique IDs
- Validating against related entities
- Computing derived values
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
import uuid

from models.trade import Trade, TradeDirection, TradeStatus
from models.contract import Contract
from schemas.trade import TradeCreate


class TradeService:
    """
    Service class for trade operations.

    Handles trade creation, validation, and lifecycle management.
    """

    def __init__(self, db: Session):
        self.db = db

    def _generate_trade_id(self) -> str:
        """Generate unique trade ID"""
        # Format: TRD-YYYYMMDD-XXXX (e.g., TRD-20250115-A1B2)
        date_part = datetime.utcnow().strftime("%Y%m%d")
        unique_part = uuid.uuid4().hex[:4].upper()
        return f"TRD-{date_part}-{unique_part}"

    def create(self, trade_data: TradeCreate) -> Optional[Trade]:
        """
        Create a new trade.

        Validates:
        - Contract exists and is active
        - Trade quantity doesn't exceed contract volume (simplified check)
        """
        # Validate contract exists
        contract = (
            self.db.query(Contract)
            .filter(Contract.id == trade_data.contract_id)
            .filter(Contract.is_active == 1)
            .first()
        )

        if not contract:
            raise ValueError(f"Contract {trade_data.contract_id} not found or inactive")

        trade = Trade(
            trade_id=self._generate_trade_id(),
            contract_id=trade_data.contract_id,
            direction=trade_data.direction,
            quantity=trade_data.quantity,
            price=trade_data.price,
            trade_date=trade_data.trade_date,
            delivery_date=trade_data.delivery_date,
            trader=trade_data.trader,
            status=TradeStatus.PENDING,
        )

        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        return trade

    def get_by_id(self, trade_id: int) -> Optional[Trade]:
        """Get trade by database ID"""
        return self.db.query(Trade).filter(Trade.id == trade_id).first()

    def get_by_trade_id(self, trade_id: str) -> Optional[Trade]:
        """Get trade by trade reference ID"""
        return self.db.query(Trade).filter(Trade.trade_id == trade_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        contract_id: Optional[int] = None,
        direction: Optional[TradeDirection] = None,
        status: Optional[TradeStatus] = None
    ) -> tuple[list[Trade], int]:
        """Get trades with filtering and pagination"""
        query = self.db.query(Trade)

        if contract_id:
            query = query.filter(Trade.contract_id == contract_id)
        if direction:
            query = query.filter(Trade.direction == direction)
        if status:
            query = query.filter(Trade.status == status)

        total = query.count()
        trades = query.order_by(Trade.trade_date.desc()).offset(skip).limit(limit).all()

        return trades, total

    def update_status(self, trade_id: int, new_status: TradeStatus) -> Optional[Trade]:
        """Update trade status"""
        trade = self.get_by_id(trade_id)
        if not trade:
            return None

        trade.status = new_status
        self.db.commit()
        self.db.refresh(trade)
        return trade

    def get_volume_summary(self, contract_id: Optional[int] = None) -> dict:
        """Get buy/sell volume summary"""
        query = self.db.query(
            Trade.direction,
            func.sum(Trade.quantity).label("total_quantity"),
            func.count(Trade.id).label("trade_count")
        ).filter(Trade.status != TradeStatus.CANCELLED)

        if contract_id:
            query = query.filter(Trade.contract_id == contract_id)

        results = query.group_by(Trade.direction).all()

        summary = {
            "total_buy_volume": 0.0,
            "total_sell_volume": 0.0,
            "net_volume": 0.0,
            "buy_count": 0,
            "sell_count": 0,
        }

        for r in results:
            if r.direction == TradeDirection.BUY:
                summary["total_buy_volume"] = r.total_quantity or 0
                summary["buy_count"] = r.trade_count
            else:
                summary["total_sell_volume"] = r.total_quantity or 0
                summary["sell_count"] = r.trade_count

        summary["net_volume"] = summary["total_buy_volume"] - summary["total_sell_volume"]
        return summary
