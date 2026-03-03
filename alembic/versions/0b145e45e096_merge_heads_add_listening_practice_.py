"""merge heads: add_listening_practice_tables and 018_add_competition_tables

Revision ID: 0b145e45e096
Revises: add_listening_practice_tables, 018_add_competition_tables
Create Date: 2026-03-03 15:10:40.078905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b145e45e096'
down_revision: Union[str, Sequence[str], None] = ('add_listening_practice_tables', '018_add_competition_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
