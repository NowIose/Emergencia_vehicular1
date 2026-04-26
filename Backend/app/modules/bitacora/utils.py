from sqlalchemy.orm import Session
from fastapi import Request
from .models import Bitacora
from app.modules.usuarios.models import Usuario, PersonalTaller

def registrar_evento(
    db: Session, 
    request: Request = None, 
    accion: str = "Desconocida", 
    detalle: str = None, 
    usuario: Usuario = None,
    id_taller: int = None
):
    """
    Utility to record an event in the bitacora.
    """
    ip = "unknown"
    agente = "unknown"
    
    if request:
        ip = request.client.host if request.client else "unknown"
        agente = request.headers.get("user-agent", "unknown")
    
    id_usuario = None
    
    if usuario:
        id_usuario = usuario.id
        # If id_taller wasn't provided, try to infer it from the user
        if id_taller is None:
            if usuario.rol.value == "admin_taller":
                id_taller = usuario.id
            elif usuario.rol.value == "personal_taller":
                personal = db.query(PersonalTaller).filter(PersonalTaller.id == usuario.id).first()
                if personal:
                    id_taller = personal.taller_id

    nueva_entrada = Bitacora(
        ip=ip,
        agente=agente,
        accion=accion,
        detalle=detalle,
        id_usuario=id_usuario,
        id_taller=id_taller
    )
    
    db.add(nueva_entrada)
    db.commit()
    db.refresh(nueva_entrada)
    return nueva_entrada
