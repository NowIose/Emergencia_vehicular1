from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_user
from app.modules.usuarios.models import Usuario, UserRole
from . import models, schemas

router = APIRouter(prefix="/bitacora", tags=["Bitacora"])

@router.get("/", response_model=List[schemas.BitacoraResponse])
def get_bitacora(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """
    Returns the bitacora logs. Only ADMIN_SISTEMA can see everything.
    """
    if current_user.rol != UserRole.ADMIN_SISTEMA:
        raise HTTPException(status_code=403, detail="No tiene permiso para ver la bitácora")

    return db.query(models.Bitacora)\
             .order_by(models.Bitacora.fecha.desc(), models.Bitacora.hora.desc())\
             .all()
