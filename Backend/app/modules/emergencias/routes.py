from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Request
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.modules.usuarios.models import Usuario, UserRole, Cliente, PersonalTaller, CalificacionTaller, Taller
from app.modules.emergencias import models, schemas
from app.modules.vehiculos.models import Vehiculo
from app.modules.emergencias.websockets import manager
from app.modules.bitacora.utils import registrar_evento

from app.modules.emergencias.ai_service import analizar_emergencia_con_ia
import asyncio
import math

router = APIRouter(prefix="/emergencias", tags=["emergencias"])

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calcula la distancia en km entre dos puntos usando Haversine."""
    R = 6371.0  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.post("/", response_model=schemas.EmergenciaResponse)
async def create_emergencia(emergencia: schemas.EmergenciaCreate, fastapi_request: Request, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value != "cliente":
        raise HTTPException(status_code=403, detail="Solo clientes pueden solicitar emergencias")
        
    # Validar que el vehiculo le pertenece
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo, Vehiculo.cliente_id == current_user.id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado o no pertenece al cliente")

    # 1. Crear y guardar la emergencia BÁSICA inmediatamente
    db_emergencia = models.Emergencia(
        id_vehiculo=emergencia.id_vehiculo,
        ubicacion_real=emergencia.ubicacion_real,
        descripcion=emergencia.descripcion,
        prioridad=emergencia.prioridad,
        fotos=emergencia.fotos
    )
    db.add(db_emergencia)
    db.commit()
    db.refresh(db_emergencia)
    
    # 2. Registrar en bitácora
    registrar_evento(db, fastapi_request, "Solicitud de Emergencia", f"Cliente {current_user.email} solicitó ayuda para vehículo {vehiculo.placa}", usuario=current_user)

    # --- NUEVO: LLAMADA A LA IA ---
    # Llamamos a la IA sin bloquear eternamente. Si tarda mucho, el timeout del servicio saltará.
    diagnostico, prioridad_sugerida = await analizar_emergencia_con_ia(db_emergencia.descripcion, db_emergencia.fotos)
    
    # Actualizamos la base de datos con los resultados de la IA
    db_emergencia.diagnostico_ia = diagnostico
    
    # Validamos que la prioridad devuelta por la IA sea correcta según tu Enum
    if prioridad_sugerida in [p.value for p in models.PrioridadEmergencia]:
        db_emergencia.prioridad = prioridad_sugerida

    db.commit()
    db.refresh(db_emergencia)
    # ------------------------------

    # 3. Broadcast a todos los talleres (Ahora incluye los datos de la IA)
    await manager.broadcast_to_talleres({
        "type": "NEW_EMERGENCY",
        "data": {
            "nro": db_emergencia.nro,
            "ubicacion_real": db_emergencia.ubicacion_real,
            "descripcion": db_emergencia.descripcion,
            "fotos": db_emergencia.fotos,
            "vehiculo": f"{vehiculo.marca} {vehiculo.modelo} ({vehiculo.placa})",
            # Añadimos los campos de la IA al WebSocket del frontend de Angular
            "diagnostico_ia": db_emergencia.diagnostico_ia,
            "prioridad": db_emergencia.prioridad.value if hasattr(db_emergencia.prioridad, 'value') else db_emergencia.prioridad
        }
    })
    
    return db_emergencia


# ---- WEBSOCKETS ----
@router.websocket("/ws/taller")
async def websocket_taller(websocket: WebSocket):
    await manager.connect_taller(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_taller(websocket)

@router.websocket("/ws/cliente/{client_id}")
async def websocket_cliente(websocket: WebSocket, client_id: int):
    await manager.connect_client(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_client(client_id)

@router.get("/espera", response_model=List[schemas.EmergenciaResponse])
def get_emergencias_espera(db: Session = Depends(get_db)):
    # Los talleres consultan las emergencias que están esperando
    return db.query(models.Emergencia).filter(models.Emergencia.estado == models.EstadoEmergencia.espera).all()

@router.get("/taller", response_model=List[schemas.EmergenciaResponse])
def get_emergencias_taller(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Solo taller puede ver su historial")
    
    taller_id = current_user.id
    if current_user.rol.value == "personal_taller":
        personal = db.query(PersonalTaller).filter(PersonalTaller.id == current_user.id).first()
        if personal:
            taller_id = personal.taller_id

    return db.query(models.Emergencia).filter(models.Emergencia.id_taller == taller_id).order_by(models.Emergencia.fecha_creacion.desc()).all()

@router.get("/cliente", response_model=List[schemas.EmergenciaResponse])
def get_emergencias_cliente(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value != "cliente":
        raise HTTPException(status_code=403, detail="Solo clientes pueden ver su historial")
    
    return db.query(models.Emergencia).join(Vehiculo).filter(Vehiculo.cliente_id == current_user.id).order_by(models.Emergencia.fecha_creacion.desc()).all()

# ---- ENDPOINTS ----
@router.post("/", response_model=schemas.EmergenciaResponse)
async def create_emergencia(emergencia: schemas.EmergenciaCreate, fastapi_request: Request, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value != "cliente":
        raise HTTPException(status_code=403, detail="Solo clientes pueden solicitar emergencias")
        
    # Validar que el vehiculo le pertenece
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo, Vehiculo.cliente_id == current_user.id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado o no pertenece al cliente")

    db_emergencia = models.Emergencia(
        id_vehiculo=emergencia.id_vehiculo,
        ubicacion_real=emergencia.ubicacion_real,
        descripcion=emergencia.descripcion,
        prioridad=emergencia.prioridad,
        fotos=emergencia.fotos
    )
    db.add(db_emergencia)
    db.commit()
    db.refresh(db_emergencia)
    
    # Registrar en bitácora
    registrar_evento(db, fastapi_request, "Solicitud de Emergencia", f"Cliente {current_user.email} solicitó ayuda para vehículo {vehiculo.placa}", usuario=current_user)

    # Broadcast a todos los talleres
    await manager.broadcast_to_talleres({
        "type": "NEW_EMERGENCY",
        "data": {
            "nro": db_emergencia.nro,
            "ubicacion_real": db_emergencia.ubicacion_real,
            "descripcion": db_emergencia.descripcion,
            "fotos": db_emergencia.fotos,
            "vehiculo": f"{vehiculo.marca} {vehiculo.modelo} ({vehiculo.placa})"
        }
    })
    
    return db_emergencia

@router.post("/{nro}/aceptar", response_model=schemas.EmergenciaResponse)
async def aceptar_emergencia(fastapi_request: Request, nro: int, req: schemas.AceptarEmergenciaRequest, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Solo taller puede aceptar")

    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")
    if emergencia.estado != models.EstadoEmergencia.espera:
        raise HTTPException(status_code=400, detail="Emergencia ya no está en espera")

    # --- Descubrir de qué taller es el usuario actual ---
    taller_id = current_user.id
    if current_user.rol.value == "personal_taller":
        personal = db.query(PersonalTaller).filter(PersonalTaller.id == current_user.id).first()
        if personal:
            taller_id = personal.taller_id
            
    # Asignamos la emergencia a este taller
    emergencia.id_taller = taller_id 
    emergencia.id_personal = req.id_personal
    emergencia.estado = models.EstadoEmergencia.atendiendo
    
    # --- NUEVO: Obtener datos del Taller para distancia y ETA ---
    taller = db.query(Taller).filter(Taller.id == taller_id).first()
    nombre_taller = taller.nombre_taller if taller else "un taller"
    
    distancia_km = 0.0
    tiempo_estimado = "tiempo desconocido"
    
    if taller and taller.latitud and taller.longitud and emergencia.ubicacion_real:
        try:
            parts = emergencia.ubicacion_real.split(",")
            if len(parts) == 2:
                client_lat = float(parts[0].strip())
                client_lon = float(parts[1].strip())
                distancia_km = calculate_distance(taller.latitud, taller.longitud, client_lat, client_lon)
                # Estimación simple: 2.5 min por km (tráfico) + 5 min base
                minutos = int(distancia_km * 2.5 + 5)
                tiempo_estimado = f"{minutos} min"
        except Exception as e:
            print(f"Error calculando distancia: {e}")

    # Guardamos el tiempo estimado en DetalleEmergencia para persistencia
    detalle = db.query(models.DetalleEmergencia).filter(models.DetalleEmergencia.nro_emergencia == nro).first()
    if not detalle:
        detalle = models.DetalleEmergencia(nro_emergencia=nro)
        db.add(detalle)
    detalle.tiempo_llegada_estimado = tiempo_estimado

    # --- MENSAJE AUTOMÁTICO ---
    personal_obj = db.query(PersonalTaller).filter(PersonalTaller.id == req.id_personal).first()
    nombre_mecanico = personal_obj.nombre_completo if personal_obj else "un mecánico"
    
    msg_texto = f"¡Hola! Soy {nombre_mecanico} de {nombre_taller}. He aceptado tu solicitud. " \
                f"Estoy a {distancia_km:.1f} km de distancia y tardaré aproximadamente {tiempo_estimado} en llegar."
    
    mensaje_auto = models.Mensajeria(
        nro_emergencia=nro,
        id_remitente=taller_id,
        mensaje=msg_texto
    )
    db.add(mensaje_auto)
    # ---------------------------

    db.commit()
    db.refresh(emergencia)

    # Registrar en bitácora
    registrar_evento(db, fastapi_request, "Emergencia Aceptada", f"Taller {nombre_taller} aceptó la emergencia Nro {nro}. Mecánico asignado: {nombre_mecanico}", usuario=current_user, id_taller=taller_id)

    # Notificar al cliente
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo).first()
    if vehiculo:
        # 1. Notificación de cambio de estado con info extra
        await manager.send_to_client(vehiculo.cliente_id, {
            "type": "STATUS_UPDATE",
            "data": {
                "nro": emergencia.nro,
                "estado": "atendiendo",
                "nombre_taller": nombre_taller,
                "distancia": f"{distancia_km:.1f} km",
                "eta": tiempo_estimado
            }
        })
        # 2. Notificación de nuevo mensaje (el mensaje automático) para que aparezca en el chat
        await manager.send_to_client(vehiculo.cliente_id, {
            "type": "NEW_MESSAGE",
            "data": {
                "nro_emergencia": nro,
                "id_remitente": taller_id,
                "mensaje": msg_texto,
                "id_taller": taller_id,
                "id_personal": req.id_personal
            }
        })

    return emergencia

@router.post("/{nro}/completar", response_model=schemas.EmergenciaResponse)
async def completar_emergencia(nro: int, fastapi_request: Request, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Solo taller puede completar")

    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    emergencia.estado = models.EstadoEmergencia.terminado
    db.commit()
    db.refresh(emergencia)

    # Registrar en bitácora
    taller_id = emergencia.id_taller
    registrar_evento(db, fastapi_request, "Emergencia Finalizada", f"Servicio completado para emergencia Nro {nro}", usuario=current_user, id_taller=taller_id)

    # Notificar al cliente
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo).first()
    if vehiculo:
        await manager.send_to_client(vehiculo.cliente_id, {
            "type": "STATUS_UPDATE",
            "data": {
                "nro": emergencia.nro,
                "estado": "terminado"
            }
        })

    return emergencia

@router.patch("/{nro}/estado", response_model=schemas.EmergenciaResponse)
async def actualizar_estado_generico(nro: int, req: schemas.EstadoUpdateRequest, fastapi_request: Request, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Solo el taller puede cambiar el estado")

    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    estado_anterior = emergencia.estado.value if hasattr(emergencia.estado, 'value') else emergencia.estado
    emergencia.estado = req.estado
    
    # --- NUEVO: Si cambian el estado a atendiendo por aquí, aseguramos que tenga id_taller ---
    taller_id = emergencia.id_taller
    if req.estado == "atendiendo" and emergencia.id_taller is None:
        taller_id = current_user.id
        if current_user.rol.value == "personal_taller":
            personal = db.query(PersonalTaller).filter(PersonalTaller.id == current_user.id).first()
            if personal:
                taller_id = personal.taller_id
        
        emergencia.id_taller = taller_id
        if current_user.rol.value == "personal_taller":
            emergencia.id_personal = current_user.id
    # -----------------------------------------------------------------------------------------

    db.commit()
    db.refresh(emergencia)

    # Registrar en bitácora
    registrar_evento(db, fastapi_request, "Cambio de Estado", f"Emergencia Nro {nro} cambió de {estado_anterior} a {req.estado}", usuario=current_user, id_taller=taller_id)

    # Notificar al cliente vía WebSocket que su estado cambió
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo).first()
    if vehiculo:
        await manager.send_to_client(vehiculo.cliente_id, {
            "type": "STATUS_UPDATE",
            "data": {
                "nro": emergencia.nro,
                "estado": req.estado
            }
        })

    return emergencia


@router.get("/cliente/mis-emergencias", response_model=List[schemas.EmergenciaResponse])
def obtener_mis_emergencias_cliente(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """ Devuelve todas las emergencias creadas por el cliente logueado """
    # Buscamos los IDs de los vehículos que pertenecen al cliente
    vehiculos_ids = [v.id for v in db.query(Vehiculo).filter(Vehiculo.cliente_id == current_user.id).all()]
    
    # Buscamos las emergencias de esos vehículos, ordenadas por la más reciente
    emergencias = db.query(models.Emergencia).filter(
        models.Emergencia.id_vehiculo.in_(vehiculos_ids)
    ).order_by(models.Emergencia.fecha_creacion.desc()).all()
    
    return emergencias


# ---- MENSAJERÍA ----
# ==========================================
# ---- ENDPOINTS DE MENSAJERÍA (CHAT) ----
# ==========================================

@router.post("/{nro}/mensajes", response_model=schemas.MensajeResponse)
async def enviar_mensaje(
    nro: int,
    req: schemas.MensajeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # 1. Validar emergencia y obtener el taller asignado
    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    # 2. Guardar en DB
    nuevo_mensaje = models.Mensajeria(
        nro_emergencia=nro,
        id_remitente=current_user.id,
        mensaje=req.mensaje
    )
    db.add(nuevo_mensaje)
    db.commit()
    db.refresh(nuevo_mensaje)

    # 3. Payload con información de filtrado
    ws_payload = {
        "type": "NEW_MESSAGE",
        "data": {
            "nro_emergencia": nro,
            "id_remitente": current_user.id,
            "mensaje": req.mensaje,
            "id_taller": emergencia.id_taller,
            "id_personal": emergencia.id_personal
        }
    }

    # 4. Enrutamiento Inteligente
    if current_user.rol.value == "cliente":
        # Broadcast a los talleres; ellos filtrarán por id_taller en el front
        await manager.broadcast_to_talleres(ws_payload)
    else:
        # Al cliente le llega directo
        vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo).first()
        if vehiculo:
            await manager.send_to_client(vehiculo.cliente_id, ws_payload)

    return nuevo_mensaje


@router.get("/{nro}/mensajes", response_model=List[schemas.MensajeResponse])
def obtener_historial_chat(nro: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """ Devuelve todos los mensajes de una emergencia específica """
    
    mensajes = db.query(models.Mensajeria).filter(
        models.Mensajeria.nro_emergencia == nro
    ).order_by(models.Mensajeria.fecha_hora.asc()).all()
    
    return mensajes


@router.put("/{nro}/mensajes/leer")
async def marcar_mensajes_como_leidos(
    nro: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """ Cuando el usuario entra al chat, marca los mensajes del 'otro' como leídos """
    
    # Buscamos los mensajes de esta emergencia que NO sean míos y que NO estén leídos
    mensajes_no_leidos = db.query(models.Mensajeria).filter(
        models.Mensajeria.nro_emergencia == nro,
        models.Mensajeria.id_remitente != current_user.id,
        models.Mensajeria.leido == False
    ).all()

    if not mensajes_no_leidos:
        return {"mensaje": "No hay mensajes nuevos por leer"}

    # Actualizamos el estado a True (Leído)
    for msg in mensajes_no_leidos:
        msg.leido = True
    
    db.commit()

    # Notificamos por WebSocket que hubo una actualización de lectura 
    # (Ideal para pintar el doble check azul en el Frontend)
    ws_payload = {
        "type": "MESSAGES_READ",
        "data": {
            "nro_emergencia": nro,
            "leido_por": current_user.id
        }
    }

    if current_user.rol.value == "cliente":
        await manager.broadcast_to_talleres(ws_payload)
    else:
        emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
        vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo).first()
        if vehiculo:
            await manager.send_to_client(vehiculo.cliente_id, ws_payload)

    return {"mensaje": f"{len(mensajes_no_leidos)} mensajes marcados como leídos"}
@router.get("/chats/activos", response_model=List[dict])
def obtener_lista_chats_activos(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """ 
    Lista todas las emergencias 'atendiendo' para el taller (Admin)
    con contador de mensajes no leídos del cliente.
    """
    if current_user.rol.value != "admin_taller":
        raise HTTPException(status_code=403, detail="Solo el administrador del taller puede gestionar los chats")

    # 1. Obtener las emergencias que este taller (Admin) está atendiendo
    # Filtramos por id_taller para que el admin solo vea las suyas
    emergencias = db.query(models.Emergencia).filter(
        models.Emergencia.estado == models.EstadoEmergencia.atendiendo,
        models.Emergencia.id_taller == current_user.id
    ).all()
    
    resultado = []
    
    for e in emergencias:
        # 2. Contar mensajes del cliente que el taller NO ha leído
        no_leidos = db.query(models.Mensajeria).filter(
            models.Mensajeria.nro_emergencia == e.nro,
            models.Mensajeria.id_remitente != current_user.id, # El remitente NO es el taller
            models.Mensajeria.leido == False
        ).count()
        
        # 3. Obtener el último mensaje para previsualizar
        ultimo_msg = db.query(models.Mensajeria).filter(
            models.Mensajeria.nro_emergencia == e.nro
        ).order_by(models.Mensajeria.fecha_hora.desc()).first()

        resultado.append({
            "nro_emergencia": e.nro,
            "descripcion": e.descripcion,
            "mensajes_pendientes": no_leidos,
            "ultimo_mensaje": ultimo_msg.mensaje if ultimo_msg else "",
            "fecha_ultimo_mensaje": ultimo_msg.fecha_hora if ultimo_msg else e.fecha_creacion,
            "id_vehiculo": e.id_vehiculo,
            "id_taller": e.id_taller,
            "nombre_cliente": e.vehiculo.dueno.nombre if e.vehiculo and e.vehiculo.dueno else "Cliente Desconocido"
        })
        
    return resultado
        
       
    return resultado
# --- Endpoint de Calificación ---
from app.modules.usuarios.models import CalificacionTaller
from sqlalchemy import Float

@router.post("/{nro}/calificar")
def calificar_emergencia(
    nro: int, 
    req: schemas.CalificarEmergenciaRequest, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    # 1. Validar que sea cliente
    if current_user.rol.value != "cliente":
        raise HTTPException(status_code=403, detail="Solo el cliente puede calificar")

    # 2. Buscar la emergencia
    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    # 3. Validar que la emergencia pertenezca al usuario
    if emergencia.vehiculo.cliente_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes calificar una emergencia que no es tuya")

    # 4. Registrar la calificación
    nueva_calificacion = CalificacionTaller(
        cliente_id=current_user.id,
        taller_id=emergencia.id_taller,
        emergencia_id=emergencia.nro,
        puntuacion=req.puntuacion,
        comentario=req.comentario
    )
    
    db.add(nueva_calificacion)
    db.commit()
    db.refresh(nueva_calificacion)
    
    return {"message": "Calificación registrada correctamente"}