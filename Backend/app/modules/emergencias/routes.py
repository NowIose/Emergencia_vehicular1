from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.modules.usuarios.models import Usuario, UserRole, Cliente, PersonalTaller, PersonalTaller
from app.modules.emergencias import models, schemas
from app.modules.vehiculos.models import Vehiculo
from app.modules.emergencias.websockets import manager

router = APIRouter(prefix="/emergencias", tags=["emergencias"])

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
async def create_emergencia(emergencia: schemas.EmergenciaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
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

@router.get("/espera", response_model=List[schemas.EmergenciaResponse])
def get_emergencias_espera(db: Session = Depends(get_db)):
    # Los talleres consultan las emergencias que están esperando
    return db.query(models.Emergencia).filter(models.Emergencia.estado == models.EstadoEmergencia.espera).all()

@router.post("/{nro}/aceptar", response_model=schemas.EmergenciaResponse)
async def aceptar_emergencia(nro: int, req: schemas.AceptarEmergenciaRequest, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Solo taller puede aceptar")

    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")
    if emergencia.estado != models.EstadoEmergencia.espera:
        raise HTTPException(status_code=400, detail="Emergencia ya no está en espera")

    # --- NUEVO: Descubrir de qué taller es el usuario actual ---
    taller_id = current_user.id
    if current_user.rol.value == "personal_taller":
        personal = db.query(PersonalTaller).filter(PersonalTaller.id == current_user.id).first()
        if personal:
            taller_id = personal.taller_id
            
    # Asignamos la emergencia a este taller
    emergencia.id_taller = taller_id 
    # -----------------------------------------------------------

    emergencia.id_personal = req.id_personal
    emergencia.estado = models.EstadoEmergencia.atendiendo
    
    # --- MENSAJE AUTOMÁTICO ---
    # Buscamos el nombre del personal para el mensaje
    personal = db.query(PersonalTaller).filter(PersonalTaller.id == req.id_personal).first()
    nombre_mecanico = personal.nombre_completo if personal else "un mecánico"
    
    mensaje_auto = models.Mensajeria(
        nro_emergencia=nro,
        id_remitente=personal.id if personal else current_user.id,
        mensaje=f"¡Hola! Soy {nombre_mecanico}. He aceptado tu solicitud y voy en camino a ayudarte."
    )
    db.add(mensaje_auto)
    # ---------------------------

    db.commit()
    db.refresh(emergencia)

    # Notificar al cliente
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo).first()
    if vehiculo:
        await manager.send_to_client(vehiculo.cliente_id, {
            "type": "STATUS_UPDATE",
            "data": {
                "nro": emergencia.nro,
                "estado": "atendiendo"
            }
        })

    return emergencia

@router.post("/{nro}/completar", response_model=schemas.EmergenciaResponse)
async def completar_emergencia(nro: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Solo taller puede completar")

    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    emergencia.estado = models.EstadoEmergencia.terminado
    db.commit()
    db.refresh(emergencia)

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
async def actualizar_estado_generico(nro: int, req: schemas.EstadoUpdateRequest, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Solo el taller puede cambiar el estado")

    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    emergencia.estado = req.estado
    
    # --- NUEVO: Si cambian el estado a atendiendo por aquí, aseguramos que tenga id_taller ---
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
            "id_taller_asignado": emergencia.id_personal  # <--- CRUCIAL
        }
    }

    # 4. Enrutamiento Inteligente
    if current_user.rol.value == "cliente":
        # Seguimos usando broadcast, pero el Frontend del taller 
        # ignorará el mensaje si el id_taller_asignado no es el suyo.
        await manager.broadcast_to_talleres(ws_payload)
    else:
        # Al cliente sí le llega directo porque tenemos su client_id
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
    Lista todas las emergencias 'atendiendo' para el taller 
    con contador de mensajes no leídos.
    """
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="No autorizado")

    # 1. Obtener las emergencias que este taller está atendiendo
    # Nota: Si es admin, quizás quieras que vea todas las 'atendiendo'
    query = db.query(models.Emergencia).filter(
        models.Emergencia.estado == models.EstadoEmergencia.atendiendo
    )
    
    # Si es personal específico, filtramos solo las suyas
    if current_user.rol.value == "personal_taller":
        query = query.filter(models.Emergencia.id_personal == current_user.id)
    
    emergencias = query.all()
    
    resultado = []
    
    for e in emergencias:
        # 2. Contar cuántos mensajes hay de esta emergencia que el taller NO ha leído
        # (Osea, mensajes donde el remitente NO es el taller)
        no_leidos = db.query(models.Mensajeria).filter(
            models.Mensajeria.nro_emergencia == e.nro,
            models.Mensajeria.id_remitente != current_user.id,
            models.Mensajeria.leido == False
        ).count()
        
        # 3. Obtener el texto del último mensaje para la previsualización
        ultimo_msg = db.query(models.Mensajeria).filter(
            models.Mensajeria.nro_emergencia == e.nro
        ).order_by(models.Mensajeria.fecha_hora.desc()).first()

        resultado.append({
            "nro_emergencia": e.nro,
            "descripcion": e.descripcion,
            "mensajes_pendientes": no_leidos,
            "ultimo_mensaje": ultimo_msg.mensaje if ultimo_msg else "",
            "fecha_ultimo_mensaje": ultimo_msg.fecha_hora if ultimo_msg else e.fecha_creacion,
            "id_vehiculo": e.id_vehiculo
        })
        
       
    return resultado