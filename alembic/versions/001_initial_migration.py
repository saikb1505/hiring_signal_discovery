"""Initial migration - create query_history table

Revision ID: 001
Revises:
Create Date: 2025-12-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create query_history table."""
    op.create_table(
        'query_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('original_query', sa.Text(), nullable=False),
        sa.Column('formatted_query', sa.Text(), nullable=False),
        sa.Column('last_run_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_history_id'), 'query_history', ['id'], unique=False)


def downgrade() -> None:
    """Drop query_history table."""
    op.drop_index(op.f('ix_query_history_id'), table_name='query_history')
    op.drop_table('query_history')
