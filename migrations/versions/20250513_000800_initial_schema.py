"""Initial database schema

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2025-05-13 00:08:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create user_roles table
    op.create_table(
        'user_roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('user_id', 'role', name='uq_user_role')
    )
    
    # Create stocks table
    op.create_table(
        'stocks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('symbol', sa.String(20), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('exchange', sa.String(20), nullable=False),
        sa.Column('sector', sa.String(50), nullable=True),
        sa.Column('industry', sa.String(50), nullable=True),
        sa.Column('market_cap', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create stock_prices table
    op.create_table(
        'stock_prices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('stock_id', sa.String(36), sa.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('open', sa.Float(), nullable=False),
        sa.Column('high', sa.Float(), nullable=False),
        sa.Column('low', sa.Float(), nullable=False),
        sa.Column('close', sa.Float(), nullable=False),
        sa.Column('adjusted_close', sa.Float(), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('stock_id', 'date', name='uq_stock_date')
    )
    
    # Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_portfolio_name')
    )
    
    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portfolio_id', sa.String(36), sa.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stock_id', sa.String(36), sa.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('portfolio_id', 'stock_id', name='uq_portfolio_stock')
    )
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portfolio_id', sa.String(36), sa.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stock_id', sa.String(36), sa.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transaction_type', sa.String(10), nullable=False),  # BUY, SELL
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('fees', sa.Float(), nullable=False, default=0.0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create strategies table
    op.create_table(
        'strategies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('strategy_type', sa.String(50), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_strategy_name')
    )
    
    # Create signals table
    op.create_table(
        'signals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stock_id', sa.String(36), sa.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('signal_type', sa.String(10), nullable=False),  # BUY, SELL, HOLD
        sa.Column('strength', sa.Float(), nullable=False),  # 0.0 to 1.0
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_stocks_symbol', 'stocks', ['symbol'])
    op.create_index('ix_stock_prices_date', 'stock_prices', ['date'])
    op.create_index('ix_stock_prices_stock_id_date', 'stock_prices', ['stock_id', 'date'])
    op.create_index('ix_transactions_portfolio_id', 'transactions', ['portfolio_id'])
    op.create_index('ix_transactions_stock_id', 'transactions', ['stock_id'])
    op.create_index('ix_transactions_transaction_date', 'transactions', ['transaction_date'])
    op.create_index('ix_signals_strategy_id', 'signals', ['strategy_id'])
    op.create_index('ix_signals_stock_id', 'signals', ['stock_id'])
    op.create_index('ix_signals_generated_at', 'signals', ['generated_at'])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('signals')
    op.drop_table('strategies')
    op.drop_table('transactions')
    op.drop_table('positions')
    op.drop_table('portfolios')
    op.drop_table('stock_prices')
    op.drop_table('stocks')
    op.drop_table('user_roles')
    op.drop_table('users')
