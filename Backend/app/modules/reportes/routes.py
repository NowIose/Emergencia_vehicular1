from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
# Importamos la seguridad desde tu módulo de usuarios
from app.modules.usuarios.routes import get_current_user
from app.modules.usuarios.models import Usuario, UserRole

# Importamos schemas y services de esta misma carpeta
from . import schemas, services

# 1. CAMBIAMOS EL PREFIJO PARA QUE COINCIDA CON ANGULAR
router = APIRouter(prefix="/admin/reportes", tags=["Reportes Globales"])

@router.get("/usuarios-lista", response_model=List[schemas.ReporteUsuarioDetalle])
def reporte_usuarios_detallado(
    rol: Optional[str] = Query(None),
    orden: Optional[str] = Query(None), 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Pasamos AMBOS parámetros al servicio
    return services.obtener_reporte_usuarios(db, rol_filtro=rol, orden=orden)

from fastapi import File, UploadFile
# ... tus otras importaciones

@router.post("/filtro-voz")
async def filtro_por_voz(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user)
):
    # Le pasamos el archivo de audio al servicio que crearemos
    filtros = await services.procesar_audio_filtros(file)
    print(filtros)
    return filtros

@router.get("/kpis-dashboard")
def kpis_operacionales(
    tenant_id: Optional[int] = Query(None, description="ID del taller para filtrar (opcional)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Si el usuario logueado es un taller, forzamos su propio ID para que solo vea sus datos
    if current_user.tipo_perfil == "taller":
        return services.obtener_kpis_dashboard(db, tenant_id=current_user.id)
    
    # Si es un Admin global, puede ver de todos o filtrar por uno específico
    return services.obtener_kpis_dashboard(db, tenant_id=tenant_id)