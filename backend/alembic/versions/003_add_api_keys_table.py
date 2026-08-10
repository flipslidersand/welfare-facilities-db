"""Add API keys table

Revision ID: 003
Revises: 002
Create Date: 2026-08-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('key_hash', sa.String(256), nullable=False, unique=True, comment='Hashed API key'),
        sa.Column('name', sa.String(100), nullable=False, comment='API key name'),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False, comment='Active/Inactive'),
        sa.Column('expires_at', sa.DateTime, nullable=True, comment='Expiration timestamp'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime, nullable=True, comment='Last used timestamp'),
        sa.Column('usage_count', sa.Integer, default=0, comment='Usage count')
    )

    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('idx_api_keys_is_active', 'api_keys', ['is_active'])


def downgrade() -> None:
    op.drop_index('idx_api_keys_is_active', 'api_keys')
    op.drop_index('idx_api_keys_key_hash', 'api_keys')
    op.drop_table('api_keys')
