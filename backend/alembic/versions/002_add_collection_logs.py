"""Add data collection logs table

Revision ID: 002
Revises: 001
Create Date: 2026-04-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create data_collection_logs table
    op.create_table(
        'data_collection_logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('script_name', sa.String(100), nullable=False, comment='Script name (import_corporation_csv, import_facility_csv, etc)'),
        sa.Column('status', sa.String(20), nullable=False, comment='Status (running, success, failed)'),
        sa.Column('records_processed', sa.Integer, comment='Number of records processed'),
        sa.Column('error_message', sa.Text, comment='Error message if failed'),
        sa.Column('started_at', sa.DateTime, nullable=False, comment='Start timestamp'),
        sa.Column('completed_at', sa.DateTime, comment='Completion timestamp'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now())
    )

    # Create indexes
    op.create_index('idx_collection_logs_script', 'data_collection_logs', ['script_name'])
    op.create_index('idx_collection_logs_status', 'data_collection_logs', ['status'])
    op.create_index('idx_collection_logs_started', 'data_collection_logs', ['started_at'])


def downgrade() -> None:
    op.drop_index('idx_collection_logs_started', 'data_collection_logs')
    op.drop_index('idx_collection_logs_status', 'data_collection_logs')
    op.drop_index('idx_collection_logs_script', 'data_collection_logs')
    op.drop_table('data_collection_logs')
