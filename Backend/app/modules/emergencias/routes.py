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

@router.post("/pre-analizar", response_model=schemas.PreAnalisisResponse)
async def pre_analizar_emergencia(req: schemas.PreAnalisisRequest, db: Session = Depends(get_db)):
    """
    Endpoint para que la App móvil obtenga un diagnóstico inicial y talleres cercanos
    ANTES de crear la emergencia formalmente.
    """
    # 1. Análisis de IA
    diagnostico, prioridad, especialidad = await analizar_emergencia_con_ia(req.descripcion, req.fotos)
    
    # 2. Parsear ubicación del cliente
    try:
        parts = req.ubicacion_cliente.split(",")
        lat_c = float(parts[0].strip())
        lon_c = float(parts[1].strip())
    except:
        raise HTTPException(status_code=400, detail="Ubicación de cliente inválida. Formato: 'lat,lng'")

    # 3. Buscar talleres que coincidan con la especialidad
    # Usamos la relación 'especialidades' del modelo Taller
    talleres_db = db.query(Taller).all()
    
    sugeridos = []
    for t in talleres_db:
        if t.latitud and t.longitud:
            dist = calculate_distance(lat_c, lon_c, t.latitud, t.longitud)
            
            # Filtro por Radio y Especialidad
            if dist <= req.radio_km:
                # Verificar si el taller tiene la especialidad detectada por IA
                nombres_esp = [e.nombre.lower() for e in t.especialidades]
                if especialidad.lower() in nombres_esp or not t.especialidades:
                    sugeridos.append(schemas.TallerCercano(
                        id=t.id,
                        nombre_taller=t.nombre_taller,
                        distancia_km=round(dist, 2),
                        direccion=t.direccion,
                        foto_perfil=t.foto_perfil,
                        especialidades=[e.nombre for e in t.especialidades],
                        latitud=t.latitud,
                        longitud=t.longitud
                    ))

    # Ordenar por cercanía
    sugeridos.sort(key=lambda x: x.distancia_km)

    return schemas.PreAnalisisResponse(
        diagnostico=diagnostico,
        prioridad=prioridad,
        especialidad_ia=especialidad,
        talleres_sugeridos=sugeridos
    )

@router.post("/buscar-talleres", response_model=List[schemas.TallerCercano])
async def buscar_talleres_cercanos(req: schemas.BuscarTalleresRequest, db: Session = Depends(get_db)):
    """
    Busca talleres por especialidad y radio dinámicamente.
    """
    try:
        parts = req.ubicacion_cliente.split(",")
        lat_c = float(parts[0].strip())
        lon_c = float(parts[1].strip())
    except:
        raise HTTPException(status_code=400, detail="Ubicación inválida")

    talleres_db = db.query(Taller).all()
    sugeridos = []
    
    for t in talleres_db:
        if t.latitud and t.longitud:
            dist = calculate_distance(lat_c, lon_c, t.latitud, t.longitud)
            if dist <= req.radio_km:
                nombres_esp = [e.nombre.lower() for e in t.especialidades]
                # Filtro por especialidad
                if req.especialidad.lower() in nombres_esp or not t.especialidades:
                    sugeridos.append(schemas.TallerCercano(
                        id=t.id,
                        nombre_taller=t.nombre_taller,
                        distancia_km=round(dist, 2),
                        direccion=t.direccion,
                        foto_perfil=t.foto_perfil,
                        especialidades=[e.nombre for e in t.especialidades]
                    ))

    sugeridos.sort(key=lambda x: x.distancia_km)
    return sugeridos

@router.post("/", response_model=schemas.EmergenciaResponse)
async def create_emergencia(emergencia: schemas.EmergenciaCreate, fastapi_request: Request, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value != "cliente":
        raise HTTPException(status_code=403, detail="Solo clientes pueden solicitar emergencias")
        
    # Validar que el vehiculo le pertenece
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo, Vehiculo.cliente_id == current_user.id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado o no pertenece al cliente")

    # 1. Crear y guardar la emergencia
    db_emergencia = models.Emergencia(
        id_vehiculo=emergencia.id_vehiculo,
        ubicacion_real=emergencia.ubicacion_real,
        descripcion=emergencia.descripcion,
        prioridad=emergencia.prioridad,
        fotos=emergencia.fotos,
        id_taller=emergencia.id_taller # Puede ser None si aún no elige
    )
    db.add(db_emergencia)
    db.commit()
    db.refresh(db_emergencia)
    
    # 2. Registrar en bitácora
    registrar_evento(db, fastapi_request, "Solicitud de Emergencia", f"Cliente {current_user.email} solicitó ayuda para vehículo {vehiculo.placa}", usuario=current_user)

    # --- LLAMADA A LA IA (Para el diagnóstico definitivo en la DB) ---
    diagnostico, prioridad_sugerida, especialidad_ia = await analizar_emergencia_con_ia(db_emergencia.descripcion, db_emergencia.fotos)
    
    db_emergencia.diagnostico_ia = diagnostico
    db_emergencia.especialidad_ia = especialidad_ia
    
    if prioridad_sugerida in [p.value for p in models.PrioridadEmergencia]:
        db_emergencia.prioridad = prioridad_sugerida

    db.commit()
    db.refresh(db_emergencia)

    # 3. Notificación WebSocket
    payload = {
        "type": "NEW_EMERGENCY",
        "data": {
            "nro": db_emergencia.nro,
            "ubicacion_real": db_emergencia.ubicacion_real,
            "descripcion": db_emergencia.descripcion,
            "fotos": db_emergencia.fotos,
            "vehiculo": f"{vehiculo.marca} {vehiculo.modelo} ({vehiculo.placa})",
            "diagnostico_ia": db_emergencia.diagnostico_ia,
            "especialidad_ia": db_emergencia.especialidad_ia,
            "prioridad": db_emergencia.prioridad.value if hasattr(db_emergencia.prioridad, 'value') else db_emergencia.prioridad
        }
    }

    if db_emergencia.id_taller:
        payload["data"]["id_taller_destino"] = db_emergencia.id_taller
        await manager.broadcast_to_talleres(payload)
    else:
        # Broadcast a todos (comportamiento antiguo/offline)
        await manager.broadcast_to_talleres(payload)
    
    return db_emergencia

@router.websocket("/ws/taller")
async def websocket_taller(websocket: WebSocket):
    await manager.connect_taller(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_taller(websocket)

@router.websocket("/ws/cliente/{client_id}")
async def websocket_cliente(websocket: WebSocket, client_id: int):
    await manager.connect_client(websocket, client_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_client(client_id)

@router.get("/espera", response_model=List[schemas.EmergenciaResponse])
def get_emergencias_espera(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """
    Los talleres consultan las emergencias que están esperando.
    FILTRO: Solo ver emergencias asignadas específicamente a este taller (id_taller)
    o aquellas que no tienen taller asignado aún (broadcast/fallback).
    """
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Solo talleres pueden ver emergencias en espera")

    # Descubrir de qué taller es el usuario actual
    taller_id = current_user.id
    if current_user.rol.value == "personal_taller":
        personal = db.query(PersonalTaller).filter(PersonalTaller.id == current_user.id).first()
        if personal:
            taller_id = personal.taller_id

    # Filtrar: En espera Y (Sin taller O Mi taller)
    query = db.query(models.Emergencia).filter(models.Emergencia.estado == models.EstadoEmergencia.espera)
    query = query.filter((models.Emergencia.id_taller == None) | (models.Emergencia.id_taller == taller_id))
    
    return query.order_by(models.Emergencia.fecha_creacion.desc()).all()

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

@router.post("/{nro}/aceptar", response_model=schemas.EmergenciaResponse)
async def aceptar_emergencia(fastapi_request: Request, nro: int, req: schemas.AceptarEmergenciaRequest, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value not in ["admin_taller", "personal_taller"]:
        raise HTTPException(status_code=403, detail="Solo taller puede aceptar")

    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")
    if emergencia.estado != models.EstadoEmergencia.espera:
        raise HTTPException(status_code=400, detail="Emergencia ya no está en espera")

    taller_id = current_user.id
    if current_user.rol.value == "personal_taller":
        personal = db.query(PersonalTaller).filter(PersonalTaller.id == current_user.id).first()
        if personal:
            taller_id = personal.taller_id
            
    emergencia.id_taller = taller_id 
    emergencia.id_personal = req.id_personal
    emergencia.estado = models.EstadoEmergencia.atendiendo
    
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
                minutos = int(distancia_km * 2.5 + 5)
                tiempo_estimado = f"{minutos} min"
        except Exception as e:
            print(f"Error calculando distancia: {e}")

    detalle = db.query(models.DetalleEmergencia).filter(models.DetalleEmergencia.nro_emergencia == nro).first()
    if not detalle:
        detalle = models.DetalleEmergencia(nro_emergencia=nro)
        db.add(detalle)
    detalle.tiempo_llegada_estimado = tiempo_estimado

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

    db.commit()
    db.refresh(emergencia)

    registrar_evento(db, fastapi_request, "Emergencia Aceptada", f"Taller {nombre_taller} aceptó la emergencia Nro {nro}. Mecánico asignado: {nombre_mecanico}", usuario=current_user, id_taller=taller_id)

    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo).first()
    if vehiculo:
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

    taller_id = emergencia.id_taller
    registrar_evento(db, fastapi_request, "Emergencia Finalizada", f"Servicio completado para emergencia Nro {nro}", usuario=current_user, id_taller=taller_id)

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

    db.commit()
    db.refresh(emergencia)

    registrar_evento(db, fastapi_request, "Cambio de Estado", f"Emergencia Nro {nro} cambió de {estado_anterior} a {req.estado}", usuario=current_user, id_taller=taller_id)

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
def obtener_mis_emergencias_cliente(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    vehiculos_ids = [v.id for v in db.query(Vehiculo).filter(Vehiculo.cliente_id == current_user.id).all()]
    emergencias = db.query(models.Emergencia).filter(models.Emergencia.id_vehiculo.in_(vehiculos_ids)).order_by(models.Emergencia.fecha_creacion.desc()).all()
    return emergencias


@router.post("/{nro}/mensajes", response_model=schemas.MensajeResponse)
async def enviar_mensaje(nro: int, req: schemas.MensajeCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    nuevo_mensaje = models.Mensajeria(nro_emergencia=nro, id_remitente=current_user.id, mensaje=req.mensaje)
    db.add(nuevo_mensaje)
    db.commit()
    db.refresh(nuevo_mensaje)

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

    if current_user.rol.value == "cliente":
        await manager.broadcast_to_talleres(ws_payload)
    else:
        vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo).first()
        if vehiculo:
            await manager.send_to_client(vehiculo.cliente_id, ws_payload)

    return nuevo_mensaje


@router.get("/{nro}/mensajes", response_model=List[schemas.MensajeResponse])
def obtener_historial_chat(nro: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(models.Mensajeria).filter(models.Mensajeria.nro_emergencia == nro).order_by(models.Mensajeria.fecha_hora.asc()).all()


@router.put("/{nro}/mensajes/leer")
async def marcar_mensajes_como_leidos(nro: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    mensajes_no_leidos = db.query(models.Mensajeria).filter(models.Mensajeria.nro_emergencia == nro, models.Mensajeria.id_remitente != current_user.id, models.Mensajeria.leido == False).all()

    if not mensajes_no_leidos:
        return {"mensaje": "No hay mensajes nuevos por leer"}

    for msg in mensajes_no_leidos:
        msg.leido = True
    db.commit()

    ws_payload = {"type": "MESSAGES_READ", "data": {"nro_emergencia": nro, "leido_por": current_user.id}}

    if current_user.rol.value == "cliente":
        await manager.broadcast_to_talleres(ws_payload)
    else:
        emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
        vehiculo = db.query(Vehiculo).filter(Vehiculo.id == emergencia.id_vehiculo).first()
        if vehiculo:
            await manager.send_to_client(vehiculo.cliente_id, ws_payload)

    return {"mensaje": f"{len(mensajes_no_leidos)} mensajes marcados como leídos"}

@router.get("/chats/activos", response_model=List[dict])
def obtener_lista_chats_activos(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value != "admin_taller":
        raise HTTPException(status_code=403, detail="Solo el administrador del taller puede gestionar los chats")

    emergencias = db.query(models.Emergencia).filter(models.Emergencia.estado == models.EstadoEmergencia.atendiendo, models.Emergencia.id_taller == current_user.id).all()
    
    resultado = []
    for e in emergencias:
        no_leidos = db.query(models.Mensajeria).filter(models.Mensajeria.nro_emergencia == e.nro, models.Mensajeria.id_remitente != current_user.id, models.Mensajeria.leido == False).count()
        ultimo_msg = db.query(models.Mensajeria).filter(models.Mensajeria.nro_emergencia == e.nro).order_by(models.Mensajeria.fecha_hora.desc()).first()

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

@router.post("/{nro}/calificar")
def calificar_emergencia(nro: int, req: schemas.CalificarEmergenciaRequest, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol.value != "cliente":
        raise HTTPException(status_code=403, detail="Solo el cliente puede calificar")

    emergencia = db.query(models.Emergencia).filter(models.Emergencia.nro == nro).first()
    if not emergencia:
        raise HTTPException(status_code=404, detail="Emergencia no encontrada")

    if emergencia.vehiculo.cliente_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes calificar una emergencia que no es tuya")

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
