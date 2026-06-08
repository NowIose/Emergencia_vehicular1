from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlanPago(BaseModel):
    codigo: str
    nombre: str
    descripcion: str
    intervalo: str
    descuento: Optional[str] = None
    price_id_configurado: bool


class CheckoutRequest(BaseModel):
    plan_codigo: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PortalResponse(BaseModel):
    portal_url: str


class SuscripcionResponse(BaseModel):
    estado: str = "sin_suscripcion"
    plan_codigo: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    periodo_inicio: Optional[datetime] = None
    periodo_fin: Optional[datetime] = None
    cancelar_al_final: bool = False
    ultima_factura_url: Optional[str] = None
    ultima_factura_pdf: Optional[str] = None
    monto_centavos: Optional[int] = None
    moneda: Optional[str] = None

    class Config:
        from_attributes = True

class PagoEmergenciaCreate(BaseModel):
    nro_emergencia: int
    monto: float # En unidades (ej. 10.50), lo convertiremos a centavos
    moneda: str = "usd"

class PagoEmergenciaResponse(BaseModel):
    nro_emergencia: int
    monto: int
    moneda: str
    pagado: bool
    fecha_pago: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmergenciaCheckoutRequest(BaseModel):
    nro_emergencia: int
