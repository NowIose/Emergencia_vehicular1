# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.database import get_db
from app.modules.usuarios.models import Taller, UserRole, Usuario
from app.modules.usuarios.schemas import TallerCreate

# 1. IMPORTA LA CONFIGURACIÓN REAL DE TU PROYECTO
from app.core.config import settings 
from app.core.security import pwd_context

router = APIRouter(prefix="/auth", tags=["auth"])

# 2. USA LAS VARIABLES DE SETTINGS (No inventes textos manuales)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="usuarios/login")

@router.post("/register-taller")
def register_taller(obj_in: TallerCreate, db: Session = Depends(get_db)):
    user_exists = db.query(Usuario).filter(Usuario.email == obj_in.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    nuevo_taller = Taller(
        email=obj_in.email,
        password_hash=pwd_context.hash(obj_in.password),
        rol=UserRole.ADMIN_TALLER,
        nombre_comercial=obj_in.nombre_taller,
        nit=obj_in.nit,
        ciudad=obj_in.ciudad,
        direccion=obj_in.direccion,
        tipo_perfil="taller"
    )

    try:
        db.add(nuevo_taller)
        db.commit()
        db.refresh(nuevo_taller)
        return {"status": "success", "message": "Taller creado", "id": nuevo_taller.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 3. LÓGICA DE USUARIO ACTUAL USANDO SETTINGS
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado - token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # AQUÍ USAMOS settings.SECRET_KEY para que coincida con el Login
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
        
    return user

