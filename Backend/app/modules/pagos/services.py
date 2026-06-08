from datetime import datetime, timezone
from typing import Any, Optional

import stripe
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.config import settings
from app.modules.pagos.models import SuscripcionTaller
from app.modules.usuarios.models import Taller


PLANES = {
    "mensual": {
        "nombre": "Plan Profesional Mensual",
        "descripcion": "Acceso completo por un mes",
        "intervalo": "mes",
        "price_id_setting": "STRIPE_MONTHLY_PRICE_ID",
    },
    "anual": {
        "nombre": "Plan Premium Anual",
        "descripcion": "Ahorra 20% con el pago anual",
        "intervalo": "año",
        "descuento": "20%",
        "price_id_setting": "STRIPE_YEARLY_PRICE_ID",
    },
}


def configurar_stripe() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe no esta configurado en el servidor")
    stripe.api_key = settings.STRIPE_SECRET_KEY


def obtener_price_id(plan_codigo: str) -> str:
    plan = PLANES.get(plan_codigo)
    if not plan:
        raise HTTPException(status_code=400, detail="Plan no valido")
    price_id = getattr(settings, plan["price_id_setting"], None)
    if not price_id:
        raise HTTPException(status_code=500, detail=f"Falta configurar el price id del plan {plan_codigo}")
    return price_id


def listar_planes() -> list[dict[str, Any]]:
    planes = []
    for codigo, plan in PLANES.items():
        price_id = getattr(settings, plan["price_id_setting"], None)
        planes.append(
            {
                "codigo": codigo,
                "nombre": plan["nombre"],
                "descripcion": plan["descripcion"],
                "intervalo": plan["intervalo"],
                "descuento": plan.get("descuento"),
                "price_id_configurado": bool(price_id),
            }
        )
    return planes


def get_or_create_suscripcion(db: Session, taller_id: int, plan_codigo: str = "mensual") -> SuscripcionTaller:
    suscripcion = db.query(SuscripcionTaller).filter(SuscripcionTaller.taller_id == taller_id).first()
    if suscripcion:
        return suscripcion

    suscripcion = SuscripcionTaller(taller_id=taller_id, plan_codigo=plan_codigo, estado="pending")
    db.add(suscripcion)
    db.commit()
    db.refresh(suscripcion)
    return suscripcion


def crear_checkout_session(db: Session, taller: Taller, plan_codigo: str) -> Any:
    configurar_stripe()
    price_id = obtener_price_id(plan_codigo)
    suscripcion = get_or_create_suscripcion(db, taller.id, plan_codigo)
    suscripcion.plan_codigo = plan_codigo
    suscripcion.stripe_price_id = price_id
    db.commit()

    success_url = f"{settings.FRONTEND_URL}/home/facturacion?checkout=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.FRONTEND_URL}/home/facturacion?checkout=cancelled"

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=taller.email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(taller.id),
        metadata={"taller_id": str(taller.id), "plan_codigo": plan_codigo},
        subscription_data={"metadata": {"taller_id": str(taller.id), "plan_codigo": plan_codigo}},
    )
    return session


def crear_portal_cliente(taller: Taller) -> Any:
    configurar_stripe()
    suscripcion = db.query(SuscripcionTaller).filter(SuscripcionTaller.taller_id == taller.id).first()
    if not suscripcion or not suscripcion.stripe_customer_id:
        raise HTTPException(status_code=400, detail="El taller aun no tiene cliente de Stripe")

    return stripe.billing_portal.Session.create(
        customer=suscripcion.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/home/facturacion",
    )


def extraer_valor(obj: Any, clave: str, default: Any = None) -> Any:
    """Extrae valores de forma segura sin importar si es dict o StripeObject"""
    if isinstance(obj, dict):
        return obj.get(clave, default)
    return getattr(obj, clave, default)


def dt_from_timestamp(value: Any) -> Optional[datetime]:
    if not value: 
        return None
    try:
        ts = int(float(value))
        return datetime.utcfromtimestamp(ts)
    except Exception as e:
        print(f"⚠️ Error convirtiendo timestamp {value}: {e}")
        return None


def upsert_desde_subscription(db: Session, subscription: Any, taller_id: Optional[int] = None) -> SuscripcionTaller:
    metadata = extraer_valor(subscription, "metadata") or {}
    if not isinstance(metadata, dict):
        metadata = getattr(metadata, "to_dict", lambda: {})()

    taller_id = taller_id or int(metadata.get("taller_id") or 0)
    customer_id = extraer_valor(subscription, "customer")

    if not taller_id:
        s_exist = db.query(SuscripcionTaller).filter(SuscripcionTaller.stripe_customer_id == customer_id).first()
        if s_exist: taller_id = s_exist.taller_id

    if not taller_id:
        raise ValueError("Taller ID no encontrado")

    items = extraer_valor(subscription, "items")
    items_data = extraer_valor(items, "data") if items else []
    price_data = extraer_valor(items_data[0], "price") if items_data else {}
    
    plan_cod = metadata.get("plan_codigo") or "mensual"
    suscripcion = get_or_create_suscripcion(db, taller_id, plan_cod)
    
    suscripcion.stripe_customer_id = customer_id
    suscripcion.stripe_subscription_id = extraer_valor(subscription, "id")
    suscripcion.stripe_price_id = extraer_valor(price_data, "id")
    suscripcion.plan_codigo = plan_cod
    suscripcion.estado = extraer_valor(subscription, "status")
    suscripcion.cancelar_al_final = bool(extraer_valor(subscription, "cancel_at_period_end"))
    
    # 1. Obtenemos el INICIO de la suscripción (start_date)
    raw_inicio = extraer_valor(subscription, "current_period_start") or extraer_valor(subscription, "start_date")
    p_inicio = dt_from_timestamp(raw_inicio)
    if p_inicio: suscripcion.periodo_inicio = p_inicio
    
    suscripcion.moneda = extraer_valor(price_data, "currency")
    suscripcion.monto_centavos = extraer_valor(price_data, "unit_amount")
    
    # 2. Extraemos URLs y la FECHA DE FIN directamente de la factura expandida
    latest_invoice = extraer_valor(subscription, "latest_invoice")
    if latest_invoice:
        if isinstance(latest_invoice, str) and not suscripcion.ultima_factura_id:
            suscripcion.ultima_factura_id = latest_invoice
        else:
            inv_id = extraer_valor(latest_invoice, "id")
            inv_url = extraer_valor(latest_invoice, "hosted_invoice_url")
            inv_pdf = extraer_valor(latest_invoice, "invoice_pdf")
            
            if inv_id: suscripcion.ultima_factura_id = inv_id
            if inv_url: suscripcion.ultima_factura_url = inv_url
            if inv_pdf: suscripcion.ultima_factura_pdf = inv_pdf
            
            # --- AQUÍ LA SOLUCIÓN: Robamos el periodo_fin del recibo de pago ---
            lines = extraer_valor(latest_invoice, "lines")
            lines_data = extraer_valor(lines, "data") if lines else []
            line_period = extraer_valor(lines_data[0], "period") if lines_data else {}
            
            p_end_raw = extraer_valor(latest_invoice, "period_end") or extraer_valor(line_period, "end")
            p_fin = dt_from_timestamp(p_end_raw)
            
            if p_fin and p_fin > (suscripcion.periodo_inicio or p_fin):
                suscripcion.periodo_fin = p_fin
            else:
                # Si Stripe no mandó fecha fin válida o es igual al inicio, forzamos 30 días
                referencia = suscripcion.periodo_inicio or datetime.utcnow()
                suscripcion.periodo_fin = referencia + timedelta(days=30)
            
            # -------------------------------------------------------------------
    
    taller = db.query(Taller).filter(Taller.id == taller_id).first()
    if taller:
        taller.suscripcion_activa = (suscripcion.estado in ["active", "trialing"])
    
    db.commit()
    db.refresh(suscripcion)
    return suscripcion

def actualizar_factura(db: Session, invoice: Any) -> None:
    sub_id = extraer_valor(invoice, "subscription")
    customer_id = extraer_valor(invoice, "customer")
    
    if not sub_id: return

    suscripcion = db.query(SuscripcionTaller).filter(
        (SuscripcionTaller.stripe_subscription_id == sub_id) | 
        (SuscripcionTaller.stripe_customer_id == customer_id)
    ).first()
    
    if not suscripcion: return

    inv_id = extraer_valor(invoice, "id")
    inv_url = extraer_valor(invoice, "hosted_invoice_url")
    inv_pdf = extraer_valor(invoice, "invoice_pdf")
    
    if inv_id: suscripcion.ultima_factura_id = inv_id
    if inv_url: suscripcion.ultima_factura_url = inv_url
    if inv_pdf: suscripcion.ultima_factura_pdf = inv_pdf
    
    # -------- EXTRACCIÓN GARANTIZADA DESDE LA FACTURA --------
    # La factura siempre tiene el inicio y fin exactos del ciclo de cobro
    lines = extraer_valor(invoice, "lines")
    lines_data = extraer_valor(lines, "data") if lines else []
    line_period = extraer_valor(lines_data[0], "period") if lines_data else {}
    
    p_start_raw = extraer_valor(invoice, "period_start") or extraer_valor(line_period, "start")
    p_end_raw = extraer_valor(invoice, "period_end") or extraer_valor(line_period, "end")
    
    p_start = dt_from_timestamp(p_start_raw)
    p_end = dt_from_timestamp(p_end_raw)
    
    if p_start: suscripcion.periodo_inicio = p_start
    if p_end: suscripcion.periodo_fin = p_end
    # ---------------------------------------------------------

    if extraer_valor(invoice, "paid"):
        suscripcion.estado = "active"
        taller = db.query(Taller).filter(Taller.id == suscripcion.taller_id).first()
        if taller: taller.suscripcion_activa = True
        
    db.commit()

def crear_checkout_emergencia(db: Session, emergencia_nro: int, monto_decimal: float) -> Any:
    configurar_stripe()
    
    # Convertir monto a centavos
    monto_centavos = int(monto_decimal * 100)
    
    # URL de retorno
    success_url = f"{settings.FRONTEND_URL}/pago-exitoso?nro={emergencia_nro}&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.FRONTEND_URL}/pago-cancelado?nro={emergencia_nro}"

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"Servicio de Emergencia #{emergencia_nro}",
                    "description": "Pago por servicios de asistencia vehicular",
                },
                "unit_amount": monto_centavos,
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"nro_emergencia": str(emergencia_nro), "tipo_pago": "emergencia"},
    )
    return session
