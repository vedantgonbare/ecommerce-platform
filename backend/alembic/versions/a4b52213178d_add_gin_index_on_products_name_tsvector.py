"""add gin index on products name tsvector

Revision ID: a4b52213178d
Revises: 24f9877eac84
Create Date: 2026-11-07 23:28:30.433288

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4b52213178d'
down_revision: Union[str, Sequence[str], None] = '24f9877eac84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "CREATE INDEX ix_products_name_tsvector ON products "
        "USING GIN (to_tsvector('english', name))"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX ix_products_name_tsvector")