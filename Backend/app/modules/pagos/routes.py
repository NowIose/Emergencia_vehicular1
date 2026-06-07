import stripe
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.core.database import get_db
from app.modules.pagos.models import SuscripcionTaller
from app.modules.pagos.schemas import CheckoutRequest, CheckoutResponse, PlanPago, PortalResponse, SuscripcionResponse
from app.modules.pagos.services import (
    crear_checkout_session,
    crear_portal_cliente,
    listar_planes,
    upsert_desde_subscription,
    actualizar_factura,
)
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
        subscription_id = getattr(data_object, "subscription", None)
        # Buscar el taller_id en los campos client_reference_id o metadata
        taller_id_str = getattr(data_object, "client_reference_id", None) or data_object.metadata.get("taller_id")
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
