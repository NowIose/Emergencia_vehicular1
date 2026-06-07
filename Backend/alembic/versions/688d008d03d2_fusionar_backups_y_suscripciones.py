"""fusionar_backups_y_suscripciones

Revision ID: 688d008d03d2
Revises: 0721826f375a, 8f4fa7540181
Create Date: 2026-06-07 09:15:07.560147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '688d008d03d2'
down_revision: Union[str, Sequence[str], None] = ('0721826f375a', '8f4fa7540181')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
