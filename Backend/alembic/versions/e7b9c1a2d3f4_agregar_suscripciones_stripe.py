"""agregar suscripciones stripe

Revision ID: e7b9c1a2d3f4
Revises: c6f25cc0ca5b
Create Date: 2026-06-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7b9c1a2d3f4"
down_revision: Union[str, Sequence[str], None] = "c6f25cc0ca5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suscripciones_talleres",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("taller_id", sa.Integer(), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=120), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=120), nullable=True),
        sa.Column("stripe_price_id", sa.String(length=120), nullable=True),
        sa.Column("plan_codigo", sa.String(length=20), nullable=False, server_default="mensual"),
        sa.Column("estado", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("moneda", sa.String(length=10), nullable=True),
        sa.Column("monto_centavos", sa.Integer(), nullable=True),
        sa.Column("periodo_inicio", sa.DateTime(), nullable=True),
        sa.Column("periodo_fin", sa.DateTime(), nullable=True),
        sa.Column("cancelar_al_final", sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column("ultima_factura_id", sa.String(length=120), nullable=True),
        sa.Column("ultima_factura_url", sa.String(length=500), nullable=True),
        sa.Column("ultima_factura_pdf", sa.String(length=500), nullable=True),
        sa.Column("creado_en", sa.DateTime(), nullable=True),
        sa.Column("actualizado_en", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["taller_id"], ["perfil_talleres.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_customer_id"),
        sa.UniqueConstraint("stripe_subscription_id"),
        sa.UniqueConstraint("taller_id"),
    )
    op.create_index(op.f("ix_suscripciones_talleres_id"), "suscripciones_talleres", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_suscripciones_talleres_id"), table_name="suscripciones_talleres")
    op.drop_table("suscripciones_talleres")
