"""Create platform_urls table

Revision ID: 003
Revises: 002
Create Date: 2026-01-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create platform_urls table."""
    op.create_table(
        'platform_urls',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('platform', sa.String(255), nullable=False),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('status', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on id
    op.create_index(op.f('ix_platform_urls_id'), 'platform_urls', ['id'], unique=False)


def downgrade() -> None:
    """Drop platform_urls table."""
    op.drop_index(op.f('ix_platform_urls_id'), table_name='platform_urls')
    op.drop_table('platform_urls')
