import stripe
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.core.database import get_db
from app.modules.pagos.models import SuscripcionTaller, PagoEmergencia
from app.modules.pagos.schemas import (
    CheckoutRequest, 
    CheckoutResponse, 
    PlanPago, 
    PortalResponse, 
    SuscripcionResponse,
    PagoEmergenciaCreate,
    PagoEmergenciaResponse,
    EmergenciaCheckoutRequest
)
from app.modules.pagos.services import (
    crear_checkout_session,
    crear_checkout_emergencia,
    crear_portal_cliente,
    listar_planes,
    upsert_desde_subscription,
    actualizar_factura,
    extraer_valor
)
from datetime import datetime
from app.modules.usuarios.models import Taller, UserRole, Usuario, CalificacionTaller, PersonalTaller
from app.modules.usuarios.routes import get_current_user
from app.modules.emergencias.models import Emergencia, EstadoEmergencia

router = APIRouter(prefix="/pagos", tags=["Pagos y suscripciones"])


def exigir_admin_taller(current_user: Usuario) -> Taller:
    if current_user.rol != UserRole.ADMIN_TALLER:
        raise HTTPException(status_code=403, detail="Solo administradores de taller")
    return current_user


@router.get("/planes", response_model=list[PlanPago])
def planes_disponibles():
    return listar_planes()


@router.get("/mi-suscripcion", response_model=SuscripcionResponse)
def mi_suscripcion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Resolver taller_id (soporta Admin y Personal)
    taller_id = current_user.id
    if current_user.rol == UserRole.PERSONAL_TALLER:
        personal = db.query(PersonalTaller).filter(PersonalTaller.id == current_user.id).first()
        taller_id = personal.taller_id if personal else None

    if not taller_id:
        return SuscripcionResponse(estado="sin_suscripcion")

    suscripcion = db.query(SuscripcionTaller).filter(SuscripcionTaller.taller_id == taller_id).first()
    if not suscripcion:
        return SuscripcionResponse(estado="sin_suscripcion")
    return suscripcion


@router.post("/checkout-session", response_model=CheckoutResponse)
def nueva_checkout_session(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Solo el admin del taller puede iniciar el pago
    if current_user.rol != UserRole.ADMIN_TALLER:
         raise HTTPException(status_code=403, detail="Solo administradores de taller")
    
    taller = db.query(Taller).filter(Taller.id == current_user.id).first()
    session = crear_checkout_session(db, taller, payload.plan_codigo)
    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/portal-session", response_model=PortalResponse)
def portal_facturacion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller_id = current_user.id
    if current_user.rol == UserRole.PERSONAL_TALLER:
        personal = db.query(PersonalTaller).filter(PersonalTaller.id == current_user.id).first()
        taller_id = personal.taller_id if personal else None
        
    taller = db.query(Taller).filter(Taller.id == taller_id).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    portal = crear_portal_cliente(taller)
    return {"portal_url": portal.url}


@router.get("/admin/stats")
def stats_administrador(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol != UserRole.ADMIN_SISTEMA:
        raise HTTPException(status_code=403, detail="Acceso exclusivo para administradores del sistema")

    talleres = db.query(Taller).all()
    resultado = []

    for t in talleres:
        suscripcion = db.query(SuscripcionTaller).filter(SuscripcionTaller.taller_id == t.id).first()
        
        # Conteo de servicios (Emergencias terminadas o atendiendo)
        servicios = db.query(Emergencia).filter(
            Emergencia.id_taller == t.id,
            Emergencia.estado.in_([EstadoEmergencia.atendiendo, EstadoEmergencia.terminado])
        ).count()

        # Conteo de personal + el propio admin del taller
        personal_count = len(t.personal) if t.personal else 0
        total_usuarios_taller = personal_count + 1

        # Calificación promedio
        stats_calif = db.query(
            func.avg(CalificacionTaller.puntuacion).label("promedio")
        ).filter(CalificacionTaller.taller_id == t.id).first()

        resultado.append({
            "taller_id": t.id,
            "nombre_taller": t.nombre_taller,
            "admin_email": t.email,
            "foto_perfil": t.foto_perfil,
            "suscripcion_activa": t.suscripcion_activa,
            "estado_pago": suscripcion.estado if suscripcion else "sin_registro",
            "plan": suscripcion.plan_codigo if suscripcion else "ninguno",
            "monto_centavos": suscripcion.monto_centavos if suscripcion else 0,
            "moneda": (suscripcion.moneda or "USD").upper() if suscripcion else "USD",
            "periodo_inicio": suscripcion.periodo_inicio.isoformat() if suscripcion and suscripcion.periodo_inicio else None,
            "periodo_fin": suscripcion.periodo_fin.isoformat() if suscripcion and suscripcion.periodo_fin else None,
            "servicios_atendidos": servicios,
            "personal_registrado": personal_count,
            "total_usuarios": total_usuarios_taller,
            "calificacion_promedio": round(stats_calif.promedio or 0.0, 1) if stats_calif else 0.0,
            "especialidades": [e.nombre for e in t.especialidades],
            "ultima_factura": suscripcion.ultima_factura_url if suscripcion else None
        })

    return resultado


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    try:
        if settings.STRIPE_WEBHOOK_SECRET:
            # MÉTODO SEGURO: Verificación de firma
            event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
        else:
            # MÉTODO DESARROLLO: Fallback si no hay secret configurado
            print("⚠️ ADVERTENCIA: STRIPE_WEBHOOK_SECRET no está en el .env. Usando modo inseguro.")
            data = json.loads(payload)
            event = stripe.Event.construct_from(data, stripe.api_key)
            
    except Exception as exc:
        print(f"❌ Error crítico en Webhook: {str(exc)}")
        # Si falla aquí es porque la firma de Stripe no coincide con tu STRIPE_WEBHOOK_SECRET
        raise HTTPException(status_code=400, detail=f"Webhook inválido: {str(exc)}")

    event_type = event.type
    print(f"🔔 Evento Stripe recibido: {event_type}")
    data_object = event.data.object

    if event_type == "checkout.session.completed":
        # USAMOS extraer_valor QUE ES INMUNE A ESTOS ERRORES DE STRIPE
        metadata = extraer_valor(data_object, "metadata") or {}
        
        # Extraemos con seguridad
        tipo_pago = extraer_valor(metadata, "tipo_pago")
        print(f"🔍 [DEBUG WEBHOOK] Tipo detectado: '{tipo_pago}' | Metadata: {metadata}")
        
        if tipo_pago == "emergencia":
            nro_emergencia = extraer_valor(metadata, "nro_emergencia")
            if nro_emergencia:
                nro = int(nro_emergencia)
                print(f"✅ Intentando procesar pago de emergencia {nro}...")
                pago = db.query(PagoEmergencia).filter(PagoEmergencia.nro_emergencia == nro).first()
                if pago:
                    pago.pagado = True
                    pago.fecha_pago = datetime.utcnow()
                    pago.stripe_payment_intent_id = extraer_valor(data_object, "payment_intent")
                    db.commit()
                    print(f"✅ ¡ÉXITO! Emergencia {nro} actualizada a PAGADO en BD.")
                else:
                    print(f"❌ [ERROR] No se encontró el pago con nro_emergencia {nro} en BD.")
        else:
            # LÓGICA DE SUSCRIPCIONES INTACTA
            subscription_id = extraer_valor(data_object, "subscription")
            taller_id_str = extraer_valor(data_object, "client_reference_id") or extraer_valor(metadata, "taller_id")
            taller_id = int(taller_id_str) if taller_id_str else 0
            
            if subscription_id and taller_id:
                print(f"✅ Checkout completado para taller {taller_id}. Sincronizando suscripción {subscription_id}...")
                stripe.api_key = settings.STRIPE_SECRET_KEY
                subscription = stripe.Subscription.retrieve(subscription_id, expand=["items.data.price", "latest_invoice"])
                upsert_desde_subscription(db, subscription, taller_id=taller_id)
                
    elif event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
        print(f"🔄 Actualizando suscripción desde evento {event_type}...")
        upsert_desde_subscription(db, data_object)

    elif event_type in {"invoice.paid", "invoice.payment_succeeded", "invoice.payment_failed"}:
        print(f"📝 Actualizando factura desde evento {event_type}...")
        actualizar_factura(db, data_object)

    return {"received": True}

# --- NUEVAS RUTAS PARA PAGOS DE EMERGENCIA ---

@router.post("/emergencia/set-precio", response_model=PagoEmergenciaResponse)
def set_emergencia_precio(
    payload: PagoEmergenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Solo el taller puede fijar precios")

    emergencia = db.query(Emergencia).filter(Emergencia.nro == payload.nro_emergencia).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    # Verificar taller
    taller_id = current_user.id
    if current_user.rol.value == "personal_taller":
        personal = db.query(PersonalTaller).filter(PersonalTaller.id == current_user.id).first()
        taller_id = personal.taller_id if personal else None
    
    if emergencia.id_taller != taller_id:
         raise HTTPException(status_code=403, detail="Esta emergencia no pertenece a tu taller")

    pago = db.query(PagoEmergencia).filter(PagoEmergencia.nro_emergencia == payload.nro_emergencia).first()
    monto_centavos = int(payload.monto * 100)
    
    if not pago:
        pago = PagoEmergencia(nro_emergencia=payload.nro_emergencia, monto=monto_centavos, moneda=payload.moneda)
        db.add(pago)
    else:
        if pago.pagado:
            raise HTTPException(status_code=400, detail="Esta emergencia ya ha sido pagada")
        pago.monto = monto_centavos
        pago.moneda = payload.moneda
    
    db.commit()
    db.refresh(pago)
    return pago

@router.post("/emergencia/pagar", response_model=CheckoutResponse)
def pagar_emergencia(
    payload: EmergenciaCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol.value != "cliente":
        raise HTTPException(status_code=403, detail="Solo los clientes pueden realizar pagos")

    pago = db.query(PagoEmergencia).filter(PagoEmergencia.nro_emergencia == payload.nro_emergencia).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Aún no se ha fijado un precio para esta emergencia")
    
    if pago.pagado:
        raise HTTPException(status_code=400, detail="Esta emergencia ya ha sido pagada")

    session = crear_checkout_emergencia(db, payload.nro_emergencia, pago.monto / 100.0)
    pago.stripe_session_id = session.id
    db.commit()
    
    return {"checkout_url": session.url, "session_id": session.id}

@router.get("/emergencia/{nro}", response_model=PagoEmergenciaResponse)
def get_pago_emergencia(nro: int, db: Session = Depends(get_db)):
    pago = db.query(PagoEmergencia).filter(PagoEmergencia.nro_emergencia == nro).first()
    if not pago:
         raise HTTPException(status_code=404, detail="No hay información de pago")
    return pago

@router.get("/emergencia/taller/historial", response_model=list[dict])
def historial_pagos_taller(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    taller_id = current_user.id
    if current_user.rol.value == "personal_taller":
        personal = db.query(PersonalTaller).filter(PersonalTaller.id == current_user.id).first()
        taller_id = personal.taller_id if personal else None

    # Obtenemos los pagos unidos a las emergencias de este taller
    pagos = db.query(PagoEmergencia).join(Emergencia).filter(Emergencia.id_taller == taller_id).order_by(PagoEmergencia.id.desc()).all()

    resultado = []
    for p in pagos:
        resultado.append({
            "nro_emergencia": p.nro_emergencia,
            "monto_centavos": p.monto,
            "moneda": p.moneda,
            "pagado": p.pagado,
            "fecha_pago": p.fecha_pago.isoformat() if p.fecha_pago else None,
            "cliente": p.emergencia.vehiculo.dueno.nombre if p.emergencia.vehiculo and getattr(p.emergencia.vehiculo, 'dueno', None) else "Cliente",
            "vehiculo": f"{p.emergencia.vehiculo.marca} {p.emergencia.vehiculo.modelo}" if p.emergencia.vehiculo else "Vehículo Desconocido",
            "diagnostico_ia": p.emergencia.diagnostico_ia
        })
    return resultado