"""sincronizar_tablas_bitacora_e_ia

Revision ID: 41d30cc8e826
Revises: ddac15928e00
Create Date: 2026-04-27 14:49:50.460089

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '41d30cc8e826'
down_revision: Union[str, Sequence[str], None] = 'ddac15928e00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # COMENTADO: La tabla 'bitacora' ya existe en el historial (revision 5ea595e82268).
    # Se deja vacío para evitar el error 'DuplicateTable' en Render.
    
    # op.create_table('bitacora',
    #     sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    #     sa.Column('ip', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    #     sa.Column('agente', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    #     sa.Column('hora', postgresql.TIME(), autoincrement=False, nullable=True),
    #     sa.Column('fecha', sa.DATE(), autoincrement=False, nullable=True),
    #     sa.Column('accion', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    #     sa.Column('detalle', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    #     sa.Column('id_usuario', sa.INTEGER(), autoincrement=False, nullable=True),
    #     sa.Column('id_taller', sa.INTEGER(), autoincrement=False, nullable=True),
    #     sa.ForeignKeyConstraint(['id_taller'], ['perfil_talleres.id'], name=op.f('bitacora_id_taller_fkey')),
    #     sa.ForeignKeyConstraint(['id_usuario'], ['usuarios.id'], name=op.f('bitacora_id_usuario_fkey')),
    #     sa.PrimaryKeyConstraint('id', name=op.f('bitacora_pkey'))
    # )
    # op.create_index(op.f('ix_bitacora_id'), 'bitacora', ['id'], unique=False)
    pass

def downgrade() -> None:
    """Downgrade schema."""
    # op.drop_index(op.f('ix_bitacora_id'), table_name='bitacora')
    # op.drop_table('bitacora')
    pass