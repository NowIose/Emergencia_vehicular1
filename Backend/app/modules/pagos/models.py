from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class SuscripcionTaller(Base):
    __tablename__ = "suscripciones_talleres"

    id = Column(Integer, primary_key=True, index=True)
    taller_id = Column(Integer, ForeignKey("perfil_talleres.id", ondelete="CASCADE"), unique=True, nullable=False)
    stripe_customer_id = Column(String(120), unique=True, nullable=True)
    stripe_subscription_id = Column(String(120), unique=True, nullable=True)
    stripe_price_id = Column(String(120), nullable=True)
    plan_codigo = Column(String(20), nullable=False, default="mensual")
    estado = Column(String(40), nullable=False, default="pending")
    moneda = Column(String(10), nullable=True)
    monto_centavos = Column(Integer, nullable=True)
    periodo_inicio = Column(DateTime, nullable=True)
    periodo_fin = Column(DateTime, nullable=True)
    cancelar_al_final = Column(Boolean, default=False)
    ultima_factura_id = Column(String(120), nullable=True)
    ultima_factura_url = Column(String(500), nullable=True)
    ultima_factura_pdf = Column(String(500), nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    taller = relationship("app.modules.usuarios.models.Taller", backref="suscripcion")

class PagoEmergencia(Base):
    __tablename__ = "pagos_emergencia"

    id = Column(Integer, primary_key=True, index=True)
    nro_emergencia = Column(Integer, ForeignKey("emergencias.nro", ondelete="CASCADE"), unique=True, nullable=False)
    monto = Column(Integer, nullable=False) # Monto en centavos
    moneda = Column(String(10), default="usd")
    pagado = Column(Boolean, default=False)
    fecha_pago = Column(DateTime, nullable=True)
    
    stripe_session_id = Column(String(120), nullable=True)
    stripe_payment_intent_id = Column(String(120), nullable=True)

    # Relaciones
    emergencia = relationship("app.modules.emergencias.models.Emergencia", backref="pago")
