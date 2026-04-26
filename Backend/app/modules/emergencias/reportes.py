from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date

# Importaciones de tu proyecto
from app.core.database import get_db
from app.api.auth import get_current_user
from app.modules.usuarios.models import Usuario
from app.modules.emergencias import models, schemas
# IMPORTA EL QUE YA TIENES FUNCIONANDO EN TU ROUTER DE USUARIOS
from app.modules.usuarios.routes import get_current_user 
from app.modules.usuarios.models import Usuario, UserRole
from app.modules.emergencias import models, schemas
# Definimos el router con un prefijo propio para reportes
router = APIRouter(prefix="/reportes", tags=["reportes-admin"])

@router.get("/estadisticas", response_model=List[schemas.ReporteEmergenciaResponse])
def obtener_estadisticas_emergencias(
    fecha_inicio: date,
    fecha_fin: date,
    agrupacion: str = "dia",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user) # Ahora usará la lógica de tu router
):
    if current_user.rol != UserRole.ADMIN_TALLER:
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    # Verificación de Rol (Muy importante para seguridad)
    if current_user.rol.value != "admin_taller":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    query = db.query(models.Emergencia).filter(
        models.Emergencia.fecha_creacion >= fecha_inicio,
        models.Emergencia.fecha_creacion <= fecha_fin,
        models.Emergencia.id_taller == current_user.id
    )

    if agrupacion == "mes":
        agrupador = func.to_char(models.Emergencia.fecha_creacion, 'YYYY-MM').label('etiqueta')
    else:
        agrupador = func.to_char(models.Emergencia.fecha_creacion, 'YYYY-MM-DD').label('etiqueta')

    resultados = query.with_entities(
        agrupador,
        func.count(models.Emergencia.nro).label('total')
    ).group_by('etiqueta').order_by('etiqueta').all()

    return resultados