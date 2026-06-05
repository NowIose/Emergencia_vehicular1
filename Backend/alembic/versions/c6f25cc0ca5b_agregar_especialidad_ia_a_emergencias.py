"""agregar_especialidad_ia_a_emergencias

Revision ID: c6f25cc0ca5b
Revises: 01ac6565a4b7
Create Date: 2026-06-04 19:36:59.047730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6f25cc0ca5b'
down_revision: Union[str, Sequence[str], None] = '01ac6565a4b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('emergencias', sa.Column('especialidad_ia', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('emergencias', 'especialidad_ia')
