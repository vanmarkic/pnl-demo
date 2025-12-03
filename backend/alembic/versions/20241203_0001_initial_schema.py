"""Initial schema creation

Revision ID: 0001
Revises: None
Create Date: 2024-12-03

Learning points:
- Migration files track schema changes
- upgrade() applies changes
- downgrade() reverts changes
- Always test downgrade before deploying!
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""

    # Contracts table
    op.create_table(
        'contracts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reference', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('counterparty', sa.String(100), nullable=False),
        sa.Column('commodity', sa.Enum('GAS', 'ELECTRICITY', 'POWER', name='commoditytype'), nullable=False),
        sa.Column('contract_type', sa.Enum('FORWARD', 'SPOT', 'SWAP', 'OPTION', name='contracttype'), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_active', sa.Integer(), server_default='1'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contracts_id', 'contracts', ['id'])
    op.create_index('ix_contracts_reference', 'contracts', ['reference'], unique=True)

    # Trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trade_id', sa.String(50), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('direction', sa.Enum('BUY', 'SELL', name='tradedirection'), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('trade_date', sa.DateTime(), nullable=False),
        sa.Column('delivery_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'SETTLED', 'CANCELLED', name='tradestatus'),
                  server_default='PENDING'),
        sa.Column('trader', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trades_id', 'trades', ['id'])
    op.create_index('ix_trades_trade_id', 'trades', ['trade_id'], unique=True)

    # Positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('position_date', sa.Date(), nullable=False),
        sa.Column('commodity', sa.Enum('GAS', 'ELECTRICITY', 'POWER', name='commoditytype'), nullable=False),
        sa.Column('delivery_month', sa.String(7), nullable=False),
        sa.Column('net_quantity', sa.Float(), nullable=False),
        sa.Column('average_price', sa.Float(), nullable=False),
        sa.Column('market_price', sa.Float(), nullable=True),
        sa.Column('mtm_value', sa.Float(), nullable=True),
        sa.Column('unrealized_pnl', sa.Float(), nullable=True),
        sa.Column('delta', sa.Float(), nullable=True),
        sa.Column('var_95', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_positions_id', 'positions', ['id'])
    op.create_index('ix_positions_position_date', 'positions', ['position_date'])

    # Daily P&L table
    op.create_table(
        'daily_pnl',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pnl_date', sa.Date(), nullable=False),
        sa.Column('commodity', sa.Enum('GAS', 'ELECTRICITY', 'POWER', name='commoditytype'), nullable=False),
        sa.Column('opening_position_value', sa.Float(), server_default='0'),
        sa.Column('closing_position_value', sa.Float(), server_default='0'),
        sa.Column('realized_pnl', sa.Float(), server_default='0'),
        sa.Column('unrealized_pnl', sa.Float(), server_default='0'),
        sa.Column('total_pnl', sa.Float(), server_default='0'),
        sa.Column('delta_pnl', sa.Float(), server_default='0'),
        sa.Column('buy_volume', sa.Float(), server_default='0'),
        sa.Column('sell_volume', sa.Float(), server_default='0'),
        sa.Column('net_volume', sa.Float(), server_default='0'),
        sa.Column('market_price', sa.Float(), nullable=True),
        sa.Column('price_change', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_daily_pnl_id', 'daily_pnl', ['id'])
    op.create_index('ix_daily_pnl_pnl_date', 'daily_pnl', ['pnl_date'])

    # Market Prices table
    op.create_table(
        'market_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('price_date', sa.Date(), nullable=False),
        sa.Column('commodity', sa.Enum('GAS', 'ELECTRICITY', 'POWER', name='commoditytype'), nullable=False),
        sa.Column('delivery_period', sa.String(20), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), server_default='EUR'),
        sa.Column('price_type', sa.String(20), server_default='SETTLEMENT'),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('previous_price', sa.Float(), nullable=True),
        sa.Column('price_change', sa.Float(), nullable=True),
        sa.Column('price_change_pct', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_market_prices_id', 'market_prices', ['id'])
    op.create_index('ix_market_prices_price_date', 'market_prices', ['price_date'])


def downgrade() -> None:
    """Remove all tables."""
    op.drop_index('ix_market_prices_price_date', table_name='market_prices')
    op.drop_index('ix_market_prices_id', table_name='market_prices')
    op.drop_table('market_prices')

    op.drop_index('ix_daily_pnl_pnl_date', table_name='daily_pnl')
    op.drop_index('ix_daily_pnl_id', table_name='daily_pnl')
    op.drop_table('daily_pnl')

    op.drop_index('ix_positions_position_date', table_name='positions')
    op.drop_index('ix_positions_id', table_name='positions')
    op.drop_table('positions')

    op.drop_index('ix_trades_trade_id', table_name='trades')
    op.drop_index('ix_trades_id', table_name='trades')
    op.drop_table('trades')

    op.drop_index('ix_contracts_reference', table_name='contracts')
    op.drop_index('ix_contracts_id', table_name='contracts')
    op.drop_table('contracts')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS tradestatus')
    op.execute('DROP TYPE IF EXISTS tradedirection')
    op.execute('DROP TYPE IF EXISTS contracttype')
    op.execute('DROP TYPE IF EXISTS commoditytype')
