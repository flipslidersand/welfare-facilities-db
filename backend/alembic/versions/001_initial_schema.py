"""Initial schema - Create corporations, facilities, and corporation_financials tables

Revision ID: 001
Revises:
Create Date: 2026-04-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create corporations table
    op.create_table(
        'corporations',
        sa.Column('corporation_id', sa.String(13), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('type', sa.String(20)),
        sa.Column('postal_code', sa.String(7)),
        sa.Column('prefecture', sa.String(10)),
        sa.Column('city', sa.String(50)),
        sa.Column('address', sa.String(200)),
        sa.Column('established_date', sa.Date),
        sa.Column('updated_at', sa.DateTime),
        sa.PrimaryKeyConstraint('corporation_id')
    )
    op.create_index('idx_corporation_prefecture', 'corporations', ['prefecture'])
    op.create_index('idx_corporation_type', 'corporations', ['type'])

    # Create facilities table
    op.create_table(
        'facilities',
        sa.Column('facility_id', sa.String(20), nullable=False),
        sa.Column('corporation_id', sa.String(13)),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('service_type', sa.String(50)),
        sa.Column('service_detail', sa.String(100)),
        sa.Column('capacity', sa.Integer),
        sa.Column('opened_date', sa.Date),
        sa.Column('postal_code', sa.String(7)),
        sa.Column('prefecture', sa.String(10)),
        sa.Column('city', sa.String(50)),
        sa.Column('address', sa.String(200)),
        sa.Column('management_type', sa.String(30)),
        sa.Column('match_status', sa.String(20), server_default='matched'),
        sa.Column('updated_at', sa.DateTime),
        sa.PrimaryKeyConstraint('facility_id'),
        sa.ForeignKeyConstraint(['corporation_id'], ['corporations.corporation_id'])
    )
    op.create_index('idx_facility_corporation', 'facilities', ['corporation_id'])
    op.create_index('idx_facility_prefecture', 'facilities', ['prefecture'])
    op.create_index('idx_facility_service_type', 'facilities', ['service_type'])

    # Create corporation_financials table
    op.create_table(
        'corporation_financials',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('corporation_id', sa.String(13), nullable=False),
        sa.Column('fiscal_year', sa.Integer, nullable=False),
        sa.Column('revenue', sa.BigInteger),
        sa.Column('ordinary_profit', sa.BigInteger),
        sa.Column('net_assets', sa.BigInteger),
        sa.Column('total_assets', sa.BigInteger),
        sa.Column('employees', sa.Integer),
        sa.Column('report_url', sa.String(500)),
        sa.Column('collected_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.ForeignKeyConstraint(['corporation_id'], ['corporations.corporation_id'])
    )
    op.create_index('idx_financial_corporation_year', 'corporation_financials', ['corporation_id', 'fiscal_year'])
    op.create_index('idx_financial_corporation', 'corporation_financials', ['corporation_id'])
    op.create_index('idx_financial_year', 'corporation_financials', ['fiscal_year'])


def downgrade() -> None:
    op.drop_index('idx_financial_year', 'corporation_financials')
    op.drop_index('idx_financial_corporation', 'corporation_financials')
    op.drop_index('idx_financial_corporation_year', 'corporation_financials')
    op.drop_table('corporation_financials')

    op.drop_index('idx_facility_service_type', 'facilities')
    op.drop_index('idx_facility_prefecture', 'facilities')
    op.drop_index('idx_facility_corporation', 'facilities')
    op.drop_table('facilities')

    op.drop_index('idx_corporation_type', 'corporations')
    op.drop_index('idx_corporation_prefecture', 'corporations')
    op.drop_table('corporations')
