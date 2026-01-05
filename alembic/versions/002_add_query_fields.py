"""Add query_string, locations, and duration fields

Revision ID: 002
Revises: 001
Create Date: 2025-12-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new fields to query_history table."""
    # Add query_string column
    op.add_column('query_history', sa.Column('query_string', sa.Text(), nullable=True))

    # Add locations column (JSON)
    op.add_column('query_history', sa.Column('locations', sa.JSON(), nullable=True))

    # Add duration_from column
    op.add_column('query_history', sa.Column('duration_from', sa.String(10), nullable=True))

    # Add duration_to column
    op.add_column('query_history', sa.Column('duration_to', sa.String(10), nullable=True))

    # Copy data from formatted_query to query_string for existing records
    op.execute('UPDATE query_history SET query_string = formatted_query WHERE query_string IS NULL')

    # Make query_string NOT NULL after copying data
    op.alter_column('query_history', 'query_string', nullable=False)

    # Make formatted_query nullable for backwards compatibility
    op.alter_column('query_history', 'formatted_query', nullable=True)


def downgrade() -> None:
    """Remove new fields from query_history table."""
    # Make formatted_query NOT NULL again before removing new columns
    op.execute('UPDATE query_history SET formatted_query = query_string WHERE formatted_query IS NULL')
    op.alter_column('query_history', 'formatted_query', nullable=False)

    # Drop new columns
    op.drop_column('query_history', 'duration_to')
    op.drop_column('query_history', 'duration_from')
    op.drop_column('query_history', 'locations')
    op.drop_column('query_history', 'query_string')
