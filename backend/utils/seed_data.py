"""
Seed Data - Populate database with sample data for testing.

Learning points:
- Creating realistic test data
- Date/time handling
- Random data generation with NumPy
"""
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
import numpy as np

from models.contract import Contract, CommodityType, ContractType
from models.trade import Trade, TradeDirection, TradeStatus
from models.price import MarketPrice
from models.pnl import DailyPnL


def seed_all(db: Session) -> dict:
    """
    Seed all tables with sample data.

    Returns counts of created records.
    """
    results = {}

    # Clear existing data (for demo purposes)
    db.query(DailyPnL).delete()
    db.query(Trade).delete()
    db.query(MarketPrice).delete()
    db.query(Contract).delete()
    db.commit()

    # Seed contracts
    contracts = seed_contracts(db)
    results["contracts"] = len(contracts)

    # Seed market prices
    prices = seed_prices(db)
    results["prices"] = len(prices)

    # Seed trades
    trades = seed_trades(db, contracts)
    results["trades"] = len(trades)

    # Calculate P&L for recent dates
    pnl_records = seed_pnl(db)
    results["pnl_records"] = len(pnl_records)

    return results


def seed_contracts(db: Session) -> list[Contract]:
    """Create sample energy contracts"""
    contracts = [
        Contract(
            reference="CTR-2025-001",
            name="Q1 2025 Gas Forward - ENGIE",
            counterparty="ENGIE Trading",
            commodity=CommodityType.GAS,
            contract_type=ContractType.FORWARD,
            volume=50000,
            unit_price=35.50,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 3, 31),
        ),
        Contract(
            reference="CTR-2025-002",
            name="Q1 2025 Power Forward - EDF",
            counterparty="EDF Trading",
            commodity=CommodityType.ELECTRICITY,
            contract_type=ContractType.FORWARD,
            volume=25000,
            unit_price=85.00,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 3, 31),
        ),
        Contract(
            reference="CTR-2025-003",
            name="Gas Spot Agreement - TotalEnergies",
            counterparty="TotalEnergies Trading",
            commodity=CommodityType.GAS,
            contract_type=ContractType.SPOT,
            volume=10000,
            unit_price=34.00,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
        ),
        Contract(
            reference="CTR-2025-004",
            name="Summer 2025 Power - RWE",
            counterparty="RWE Supply & Trading",
            commodity=CommodityType.ELECTRICITY,
            contract_type=ContractType.FORWARD,
            volume=30000,
            unit_price=78.50,
            start_date=datetime(2025, 4, 1),
            end_date=datetime(2025, 9, 30),
        ),
    ]

    for contract in contracts:
        db.add(contract)
    db.commit()

    # Refresh to get IDs
    for contract in contracts:
        db.refresh(contract)

    return contracts


def seed_prices(db: Session) -> list[MarketPrice]:
    """Create sample market price history"""
    prices = []
    base_date = date.today() - timedelta(days=30)

    # Gas prices - starting at €35/MWh with daily volatility
    np.random.seed(42)
    gas_price = 35.0
    for i in range(31):
        price_date = base_date + timedelta(days=i)
        change = np.random.normal(0, 0.5)  # Daily change
        gas_price = max(25, min(50, gas_price + change))  # Keep in range

        prices.append(MarketPrice(
            price_date=price_date,
            commodity=CommodityType.GAS,
            delivery_period="SPOT",
            price=round(gas_price, 2),
            currency="EUR",
            price_type="SETTLEMENT",
            source="ICE",
        ))

    # Electricity prices - starting at €85/MWh
    elec_price = 85.0
    for i in range(31):
        price_date = base_date + timedelta(days=i)
        change = np.random.normal(0, 2.0)  # Higher volatility
        elec_price = max(60, min(120, elec_price + change))

        prices.append(MarketPrice(
            price_date=price_date,
            commodity=CommodityType.ELECTRICITY,
            delivery_period="SPOT",
            price=round(elec_price, 2),
            currency="EUR",
            price_type="SETTLEMENT",
            source="EEX",
        ))

    for price in prices:
        db.add(price)
    db.commit()

    return prices


def seed_trades(db: Session, contracts: list[Contract]) -> list[Trade]:
    """Create sample trades"""
    trades = []
    base_date = date.today() - timedelta(days=20)

    # Sample trades for gas contract
    gas_contract = contracts[0]
    trade_data = [
        (TradeDirection.BUY, 5000, 34.50, 0),
        (TradeDirection.BUY, 3000, 35.00, 2),
        (TradeDirection.SELL, 2000, 36.00, 5),
        (TradeDirection.BUY, 4000, 35.50, 7),
        (TradeDirection.SELL, 1500, 36.50, 10),
        (TradeDirection.BUY, 2500, 35.25, 12),
    ]

    for i, (direction, qty, price, day_offset) in enumerate(trade_data):
        trade_date = datetime.combine(base_date + timedelta(days=day_offset), datetime.min.time())
        trade_date = trade_date.replace(hour=10, minute=30)

        trades.append(Trade(
            trade_id=f"TRD-GAS-{i+1:04d}",
            contract_id=gas_contract.id,
            direction=direction,
            quantity=qty,
            price=price,
            trade_date=trade_date,
            delivery_date=trade_date + timedelta(days=30),
            status=TradeStatus.CONFIRMED,
            trader="Demo Trader",
        ))

    # Sample trades for electricity contract
    elec_contract = contracts[1]
    elec_trade_data = [
        (TradeDirection.BUY, 2000, 84.00, 1),
        (TradeDirection.BUY, 1500, 85.50, 3),
        (TradeDirection.SELL, 1000, 87.00, 6),
        (TradeDirection.BUY, 2500, 83.00, 9),
        (TradeDirection.SELL, 500, 88.00, 11),
    ]

    for i, (direction, qty, price, day_offset) in enumerate(elec_trade_data):
        trade_date = datetime.combine(base_date + timedelta(days=day_offset), datetime.min.time())
        trade_date = trade_date.replace(hour=14, minute=15)

        trades.append(Trade(
            trade_id=f"TRD-ELEC-{i+1:04d}",
            contract_id=elec_contract.id,
            direction=direction,
            quantity=qty,
            price=price,
            trade_date=trade_date,
            delivery_date=trade_date + timedelta(days=30),
            status=TradeStatus.CONFIRMED,
            trader="Demo Trader",
        ))

    for trade in trades:
        db.add(trade)
    db.commit()

    return trades


def seed_pnl(db: Session) -> list[DailyPnL]:
    """Create sample P&L records"""
    pnl_records = []
    base_date = date.today() - timedelta(days=15)

    # Generate P&L for gas
    np.random.seed(123)
    cumulative_pnl = 0
    prev_pnl = 0

    for i in range(16):
        pnl_date = base_date + timedelta(days=i)

        # Random daily P&L
        daily_pnl = np.random.normal(500, 2000)
        cumulative_pnl += daily_pnl

        pnl_records.append(DailyPnL(
            pnl_date=pnl_date,
            commodity=CommodityType.GAS,
            opening_position_value=prev_pnl * 35,
            closing_position_value=cumulative_pnl * 35,
            realized_pnl=daily_pnl * 0.3,
            unrealized_pnl=daily_pnl * 0.7,
            total_pnl=daily_pnl,
            delta_pnl=daily_pnl - prev_pnl if i > 0 else daily_pnl,
            buy_volume=np.random.randint(500, 2000),
            sell_volume=np.random.randint(200, 1000),
            net_volume=np.random.randint(-500, 1000),
            market_price=35 + np.random.normal(0, 1),
        ))
        prev_pnl = daily_pnl

    # Generate P&L for electricity
    cumulative_pnl = 0
    prev_pnl = 0

    for i in range(16):
        pnl_date = base_date + timedelta(days=i)

        daily_pnl = np.random.normal(800, 3000)
        cumulative_pnl += daily_pnl

        pnl_records.append(DailyPnL(
            pnl_date=pnl_date,
            commodity=CommodityType.ELECTRICITY,
            opening_position_value=prev_pnl * 85,
            closing_position_value=cumulative_pnl * 85,
            realized_pnl=daily_pnl * 0.4,
            unrealized_pnl=daily_pnl * 0.6,
            total_pnl=daily_pnl,
            delta_pnl=daily_pnl - prev_pnl if i > 0 else daily_pnl,
            buy_volume=np.random.randint(300, 1500),
            sell_volume=np.random.randint(100, 800),
            net_volume=np.random.randint(-300, 700),
            market_price=85 + np.random.normal(0, 3),
        ))
        prev_pnl = daily_pnl

    for record in pnl_records:
        db.add(record)
    db.commit()

    return pnl_records
